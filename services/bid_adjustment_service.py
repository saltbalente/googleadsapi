"""
Bid Adjustment Service - Modifica pujas en Google Ads usando la API v21
Compatible con múltiples monedas
"""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ✅ NUEVO: Configuración de límites mínimos por moneda
CURRENCY_MIN_BIDS = {
    'USD': 100_000,        # $0.10
    'EUR': 100_000,        # €0.10
    'GBP': 100_000,        # £0.10
    'COP': 400_000_000,    # $400 COP
    'MXN': 2_000_000,      # $2.00 MXN
    'BRL': 500_000,        # R$0.50
    'ARS': 100_000_000,    # $100 ARS
    'CLP': 100_000_000,    # $100 CLP
    'PEN': 500_000,        # S/0.50
}

@dataclass
class BidAdjustment:
    """Representa un ajuste de puja"""
    customer_id: str
    ad_group_id: str
    criterion_id: str
    keyword_text: str
    current_bid_micros: int
    new_bid_micros: int
    adjustment_percent: float
    reason: str

class BidAdjustmentService:
    """Servicio para ajustar pujas en Google Ads API v21"""
    
    def __init__(self, google_ads_client):
        """
        Inicializa el servicio de ajuste de pujas
        
        Args:
            google_ads_client: GoogleAdsClient o GoogleAdsClientWrapper
        """
        # Detectar si es wrapper y extraer cliente real
        if hasattr(google_ads_client, 'client'):
            self.client = google_ads_client.client
            logger.info("Usando cliente real extraído de GoogleAdsClientWrapper")
        else:
            self.client = google_ads_client
            logger.info("Usando GoogleAdsClient directo")
        
        # Inicializar servicios
        try:
            self.ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
            self.googleads_service = self.client.get_service("GoogleAdsService")
            logger.info("✅ Servicios de Google Ads inicializados correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando servicios: {e}")
            raise
        
        # ✅ NUEVO: Cache de moneda por customer_id
        self._currency_cache = {}
    
    def get_account_currency(self, customer_id: str) -> str:
        """
        Obtiene el código de moneda de la cuenta de Google Ads
        
        Args:
            customer_id: ID del cliente
            
        Returns:
            Código de moneda (ej: 'COP', 'USD', 'MXN')
        """
        # Verificar cache
        if customer_id in self._currency_cache:
            return self._currency_cache[customer_id]
        
        query = f"""
            SELECT
                customer.currency_code
            FROM customer
            WHERE customer.id = {customer_id}
        """
        
        try:
            response = self.googleads_service.search(
                customer_id=customer_id, 
                query=query
            )
            
            for row in response:
                currency = row.customer.currency_code
                self._currency_cache[customer_id] = currency
                logger.info(f"✅ Moneda detectada para {customer_id}: {currency}")
                return currency
            
            # Fallback a USD si no se puede detectar
            logger.warning(f"⚠️ No se pudo detectar moneda para {customer_id}, usando USD")
            return 'USD'
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo moneda: {e}")
            return 'USD'
    
    def get_min_bid_for_currency(self, currency_code: str) -> int:
        """
        Obtiene el mínimo de puja en micros para una moneda
        
        Args:
            currency_code: Código de moneda (ej: 'COP', 'USD')
            
        Returns:
            Mínimo de puja en micros
        """
        min_bid = CURRENCY_MIN_BIDS.get(currency_code, 100_000)
        logger.info(f"Mínimo de puja para {currency_code}: {min_bid/1_000_000:,.2f}")
        return min_bid
    
    def get_keyword_criterion_ids(self, customer_id: str, keyword_texts: List[str]) -> Dict[str, Dict]:
        """
        Obtiene los criterion IDs de keywords por texto
        
        Args:
            customer_id: ID del cliente (sin guiones)
            keyword_texts: Lista de textos de keywords
            
        Returns:
            Dict mapping keyword_text → {criterion_id, ad_group_id, campaign_id, current_bid_micros}
        """
        if not keyword_texts:
            return {}
        
        # Escapar comillas simples en keywords
        escaped_keywords = [kw.replace("'", "\\'") for kw in keyword_texts]
        keywords_str = ', '.join([f"'{kw}'" for kw in escaped_keywords])
        
        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.cpc_bid_micros,
                ad_group.id,
                campaign.id
            FROM keyword_view
            WHERE ad_group_criterion.keyword.text IN ({keywords_str})
                AND ad_group_criterion.status = 'ENABLED'
                AND ad_group.status = 'ENABLED'
                AND campaign.status = 'ENABLED'
        """
        
        try:
            response = self.googleads_service.search(customer_id=customer_id, query=query)
            
            keyword_map = {}
            for row in response:
                keyword_text = row.ad_group_criterion.keyword.text
                keyword_map[keyword_text] = {
                    'criterion_id': row.ad_group_criterion.criterion_id,
                    'ad_group_id': row.ad_group.id,
                    'campaign_id': row.campaign.id,
                    'current_bid_micros': row.ad_group_criterion.cpc_bid_micros
                }
            
            logger.info(f"✅ Encontrados {len(keyword_map)} keywords con criterion IDs")
            return keyword_map
            
        except GoogleAdsException as e:
            logger.error(f"❌ Error obteniendo criterion IDs: {e}")
            for error in e.failure.errors:
                logger.error(f"  - {error.message}")
            return {}
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return {}
    
    def adjust_keyword_bid(
        self, 
        customer_id: str, 
        ad_group_id: str, 
        criterion_id: str,
        new_bid_micros: int,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Ajusta la puja de una keyword con detección automática de moneda (Compatible con API v21)
        
        Args:
            customer_id: ID del cliente (sin guiones)
            ad_group_id: ID del ad group
            criterion_id: ID del criterion (keyword)
            new_bid_micros: Nueva puja en micros (1 USD = 1,000,000 micros)
            dry_run: Si es True, solo simula el cambio
            
        Returns:
            (success: bool, message: str)
        """
        try:
            # ✅ NUEVO: Detectar moneda automáticamente
            currency = self.get_account_currency(customer_id)
            min_bid = self.get_min_bid_for_currency(currency)
            
            # ✅ NUEVO: Validar mínimo de puja según moneda
            if new_bid_micros < min_bid:
                error_msg = f"Puja {new_bid_micros/1_000_000:,.2f} {currency} es menor al mínimo {min_bid/1_000_000:,.2f} {currency}"
                logger.warning(f"⚠️ {error_msg}")
                return False, error_msg
            
            # Construir resource name
            criterion_resource_name = self.ad_group_criterion_service.ad_group_criterion_path(
                customer_id, ad_group_id, criterion_id
            )
            
            if dry_run:
                logger.info(f"[DRY RUN] Cambiaría puja de criterion {criterion_id} a {new_bid_micros/1_000_000:,.2f} {currency}")
                return True, f"[DRY RUN] Puja cambiaría a {new_bid_micros/1_000_000:,.2f} {currency}"
            
            # ✅ SINTAXIS CORRECTA PARA API v21
            # Crear operación de actualización
            ad_group_criterion_operation = self.client.get_type("AdGroupCriterionOperation")
            ad_group_criterion = ad_group_criterion_operation.update
            
            # Establecer resource name
            ad_group_criterion.resource_name = criterion_resource_name
            
            # Establecer nueva puja
            ad_group_criterion.cpc_bid_micros = new_bid_micros
            
            # ✅ CORRECCIÓN: FieldMask en v21
            field_mask = field_mask_pb2.FieldMask(paths=["cpc_bid_micros"])
            ad_group_criterion_operation.update_mask.CopyFrom(field_mask)
            
            # Ejecutar cambio real
            response = self.ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=[ad_group_criterion_operation]
            )
            
            logger.info(f"✅ Puja actualizada: criterion {criterion_id} → {new_bid_micros/1_000_000:,.2f} {currency}")
            return True, f"Puja actualizada a {new_bid_micros/1_000_000:,.2f} {currency}"
            
        except GoogleAdsException as e:
            error_msg = f"Error API: {e.failure.errors[0].message}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg
    
    def pause_keyword(
        self,
        customer_id: str,
        ad_group_id: str,
        criterion_id: str,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Pausa una keyword (Compatible con API v21)
        
        Args:
            customer_id: ID del cliente
            ad_group_id: ID del ad group
            criterion_id: ID del criterion
            dry_run: Si es True, solo simula
            
        Returns:
            (success, message)
        """
        try:
            # Construir resource name
            criterion_resource_name = self.ad_group_criterion_service.ad_group_criterion_path(
                customer_id, ad_group_id, criterion_id
            )
            
            if dry_run:
                logger.info(f"[DRY RUN] Pausaría criterion {criterion_id}")
                return True, "[DRY RUN] Keyword se pausaría"
            
            # ✅ SINTAXIS CORRECTA PARA API v21
            ad_group_criterion_operation = self.client.get_type("AdGroupCriterionOperation")
            ad_group_criterion = ad_group_criterion_operation.update
            
            # Resource name
            ad_group_criterion.resource_name = criterion_resource_name
            
            # Establecer status a PAUSED
            ad_group_criterion.status = self.client.enums.AdGroupCriterionStatusEnum.PAUSED
            
            # ✅ CORRECCIÓN: FieldMask en v21
            field_mask = field_mask_pb2.FieldMask(paths=["status"])
            ad_group_criterion_operation.update_mask.CopyFrom(field_mask)
            
            # Ejecutar
            response = self.ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=[ad_group_criterion_operation]
            )
            
            logger.info(f"✅ Keyword pausada: criterion {criterion_id}")
            return True, "Keyword pausada exitosamente"
            
        except GoogleAdsException as e:
            error_msg = f"Error API: {e.failure.errors[0].message}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado pausando: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg
    
    def bulk_adjust_bids(
        self,
        adjustments: List[BidAdjustment],
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        Ajusta múltiples pujas en lote con soporte multi-moneda
        
        Args:
            adjustments: Lista de BidAdjustment
            dry_run: Si es True, solo simula
            
        Returns:
            Diccionario con resultados
        """
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'details': [],
            'currencies_detected': set()  # ✅ NUEVO: Rastrear monedas detectadas
        }
        
        for adj in adjustments:
            # ✅ NUEVO: Detectar moneda para cada ajuste
            currency = self.get_account_currency(adj.customer_id)
            results['currencies_detected'].add(currency)
            
            success, message = self.adjust_keyword_bid(
                customer_id=adj.customer_id,
                ad_group_id=adj.ad_group_id,
                criterion_id=adj.criterion_id,
                new_bid_micros=adj.new_bid_micros,
                dry_run=dry_run
            )
            
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'keyword': adj.keyword_text,
                    'error': message
                })
            
            # ✅ NUEVO: Mostrar moneda en detalles
            results['details'].append({
                'keyword': adj.keyword_text,
                'adjustment': f"{adj.adjustment_percent:+.1f}%",
                'old_bid': f"{adj.current_bid_micros/1_000_000:,.2f} {currency}",
                'new_bid': f"{adj.new_bid_micros/1_000_000:,.2f} {currency}",
                'reason': adj.reason,
                'success': success,
                'message': message,
                'currency': currency  # ✅ NUEVO: Incluir moneda
            })
        
        # ✅ NUEVO: Convertir set a lista para JSON serialization
        results['currencies_detected'] = list(results['currencies_detected'])
        
        logger.info(f"📊 Ajustes completados: {results['successful']} exitosos, {results['failed']} fallidos")
        logger.info(f"💰 Monedas detectadas: {', '.join(results['currencies_detected'])}")
        return results