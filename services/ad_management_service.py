"""
Ad Management Service - Gestiona acciones sobre anuncios (pausar, activar, etc.)
Compatible con Google Ads API v21
"""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2
from typing import List, Dict, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AdAction:
    """Representa una acción sobre un anuncio"""
    customer_id: str
    ad_group_id: str
    ad_id: str
    ad_headlines: str
    campaign_name: str
    ad_group_name: str
    current_status: str
    reason: str

class AdManagementService:
    """Servicio para gestionar acciones sobre anuncios"""
    
    def __init__(self, google_ads_client):
        """
        Inicializa el servicio
        
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
            self.ad_group_ad_service = self.client.get_service("AdGroupAdService")
            self.googleads_service = self.client.get_service("GoogleAdsService")
            logger.info("✅ AdManagementService inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando servicios: {e}")
            raise
    
    def pause_ad(
        self,
        customer_id: str,
        ad_group_id: str,
        ad_id: str,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Pausa un anuncio
        
        Args:
            customer_id: ID del cliente (sin guiones)
            ad_group_id: ID del ad group
            ad_id: ID del anuncio
            dry_run: Si es True, solo simula
            
        Returns:
            (success: bool, message: str)
        """
        try:
            # Construir resource name
            ad_resource_name = self.ad_group_ad_service.ad_group_ad_path(
                customer_id, ad_group_id, ad_id
            )
            
            if dry_run:
                logger.info(f"[DRY RUN] Pausaría anuncio {ad_id} en ad group {ad_group_id}")
                return True, "[DRY RUN] Anuncio se pausaría"
            
            # Crear operación de actualización
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.update
            
            # Establecer resource name
            ad_group_ad.resource_name = ad_resource_name
            
            # Establecer status a PAUSED
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.PAUSED
            
            # Field mask para v21
            field_mask = field_mask_pb2.FieldMask(paths=["status"])
            ad_group_ad_operation.update_mask.CopyFrom(field_mask)
            
            # Ejecutar cambio
            response = self.ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=[ad_group_ad_operation]
            )
            
            logger.info(f"✅ Anuncio pausado: ad_id {ad_id}")
            return True, "Anuncio pausado exitosamente"
            
        except GoogleAdsException as e:
            error_msg = f"Error API: {e.failure.errors[0].message}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg
    
    def enable_ad(
        self,
        customer_id: str,
        ad_group_id: str,
        ad_id: str,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Activa un anuncio pausado
        
        Args:
            customer_id: ID del cliente
            ad_group_id: ID del ad group
            ad_id: ID del anuncio
            dry_run: Si es True, solo simula
            
        Returns:
            (success: bool, message: str)
        """
        try:
            ad_resource_name = self.ad_group_ad_service.ad_group_ad_path(
                customer_id, ad_group_id, ad_id
            )
            
            if dry_run:
                logger.info(f"[DRY RUN] Activaría anuncio {ad_id}")
                return True, "[DRY RUN] Anuncio se activaría"
            
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.update
            
            ad_group_ad.resource_name = ad_resource_name
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED
            
            field_mask = field_mask_pb2.FieldMask(paths=["status"])
            ad_group_ad_operation.update_mask.CopyFrom(field_mask)
            
            response = self.ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=[ad_group_ad_operation]
            )
            
            logger.info(f"✅ Anuncio activado: ad_id {ad_id}")
            return True, "Anuncio activado exitosamente"
            
        except GoogleAdsException as e:
            error_msg = f"Error API: {e.failure.errors[0].message}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg
    
    def bulk_pause_ads(
        self,
        actions: List[AdAction],
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        Pausa múltiples anuncios en lote
        
        Args:
            actions: Lista de AdAction
            dry_run: Si es True, solo simula
            
        Returns:
            Diccionario con resultados
        """
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }
        
        for action in actions:
            success, message = self.pause_ad(
                customer_id=action.customer_id,
                ad_group_id=action.ad_group_id,
                ad_id=action.ad_id,
                dry_run=dry_run
            )
            
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'ad_id': action.ad_id,
                    'headlines': action.ad_headlines,
                    'error': message
                })
            
            results['details'].append({
                'ad_id': action.ad_id,
                'headlines': action.ad_headlines,
                'campaign': action.campaign_name,
                'ad_group': action.ad_group_name,
                'previous_status': action.current_status,
                'reason': action.reason,
                'success': success,
                'message': message
            })
        
        logger.info(f"📊 Pausado de anuncios completado: {results['successful']} exitosos, {results['failed']} fallidos")
        return results
    
    def bulk_enable_ads(
        self,
        actions: List[AdAction],
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        Activa múltiples anuncios en lote
        
        Args:
            actions: Lista de AdAction
            dry_run: Si es True, solo simula
            
        Returns:
            Diccionario con resultados
        """
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }
        
        for action in actions:
            success, message = self.enable_ad(
                customer_id=action.customer_id,
                ad_group_id=action.ad_group_id,
                ad_id=action.ad_id,
                dry_run=dry_run
            )
            
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'ad_id': action.ad_id,
                    'headlines': action.ad_headlines,
                    'error': message
                })
            
            results['details'].append({
                'ad_id': action.ad_id,
                'headlines': action.ad_headlines,
                'campaign': action.campaign_name,
                'ad_group': action.ad_group_name,
                'previous_status': action.current_status,
                'reason': action.reason,
                'success': success,
                'message': message
            })
        
        logger.info(f"📊 Activación de anuncios completado: {results['successful']} exitosos, {results['failed']} fallidos")
        return results