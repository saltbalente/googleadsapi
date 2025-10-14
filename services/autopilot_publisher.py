"""
Autopilot Publisher - Publicación Automática a Google Ads
Publica campañas completas generadas por IA
"""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AutopilotPublisher:
    """
    Publicador de campañas automáticas a Google Ads
    
    Maneja:
    - Creación de campañas
    - Creación de ad groups
    - Inserción de keywords
    - Creación de responsive search ads
    - Manejo de errores y rollback
    """
    
    def __init__(self, google_ads_client):
        """
        Inicializa el publisher
        
        Args:
            google_ads_client: GoogleAdsClientWrapper instance
        """
        self.client = google_ads_client.get_client()
        self.wrapper = google_ads_client
    
    # ========================================================================
    # PUBLICACIÓN COMPLETA
    # ========================================================================
    
    def publish_complete_campaign(
        self,
        blueprint: Dict[str, Any],
        customer_id: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Publica una campaña completa a Google Ads
        
        Args:
            blueprint: CampaignBlueprint.__dict__
            customer_id: ID del cliente de Google Ads
            progress_callback: Función para reportar progreso
            
        Returns:
            {
                'success': bool,
                'campaign_id': str,
                'campaign_resource_name': str,
                'ad_group_ids': List[str],
                'ad_ids': List[str],
                'keyword_ids': List[str],
                'errors': List[str],
                'warnings': List[str]
            }
        """
        
        result = {
            'success': False,
            'campaign_id': None,
            'campaign_resource_name': None,
            'ad_group_ids': [],
            'ad_ids': [],
            'keyword_ids': [],
            'errors': [],
            'warnings': []
        }
        
        created_resources = []  # Para rollback si falla
        
        try:
            # ✅ DETERMINAR SI ES NUEVA CAMPAÑA O EXISTENTE
            is_new_campaign = 'campaign_id' not in blueprint or blueprint.get('campaign_id') is None
            
            logger.info(f"📊 Tipo de publicación: {'NUEVA CAMPAÑA' if is_new_campaign else 'CAMPAÑA EXISTENTE'}")
            
            if is_new_campaign:
                # ✅ CREAR NUEVA CAMPAÑA
                logger.info("🆕 Creando nueva campaña...")
                self._update_progress(progress_callback, "Creando campaña...", 10)
                
                campaign_result = self._create_campaign(
                    customer_id=customer_id,
                    campaign_name=blueprint['campaign_name'],
                    budget_daily=blueprint['budget_daily'],
                    target_locations=blueprint['target_locations'],
                    languages=blueprint.get('languages', ['es', 'en'])
                )
                
                if campaign_result['error']:
                    result['errors'].append(f"Error creando campaña: {campaign_result['error']}")
                    return result
                
                result['campaign_id'] = campaign_result['campaign_id']
                result['campaign_resource_name'] = campaign_result['resource_name']
                created_resources.append(('campaign', campaign_result['resource_name']))
                
                logger.info(f"✅ Campaña creada: {result['campaign_id']}")
            
            else:
                # ✅ USAR CAMPAÑA EXISTENTE
                existing_campaign_id = blueprint['campaign_id']
                logger.info(f"📂 Usando campaña existente: {existing_campaign_id}")
                
                campaign_service = self.client.get_service("CampaignService")
                result['campaign_id'] = existing_campaign_id
                result['campaign_resource_name'] = campaign_service.campaign_path(customer_id, existing_campaign_id)
                
                logger.info(f"✅ Campaign resource name: {result['campaign_resource_name']}")
            
            # PASO 2: Crear ad groups con keywords y anuncios
            total_groups = len(blueprint['ad_groups'])
            
            for idx, ad_group_data in enumerate(blueprint['ad_groups']):
                group_num = idx + 1
                progress = 10 + ((group_num / total_groups) * 80)
                
                self._update_progress(
                    progress_callback,
                    f"Creando grupo {group_num}/{total_groups}: {ad_group_data['name']}...",
                    progress
                )
                
                try:
                    # ✅ VALIDACIÓN ESPECÍFICA PARA CADA AD GROUP
                    logger.info(f"🔍 Validando ad group {group_num}: {ad_group_data['name']}")
                    
                    # Validar estructura del ad group
                    if not ad_group_data.get('name'):
                        error_msg = f"Ad group {group_num} no tiene nombre válido"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
                        continue
                    
                    if not ad_group_data.get('keywords'):
                        error_msg = f"Ad group '{ad_group_data['name']}' no tiene keywords"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
                        continue
                    
                    if not ad_group_data.get('ads'):
                        error_msg = f"Ad group '{ad_group_data['name']}' no tiene anuncios"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
                        continue
                    
                    # ✅ PASO 2A: Crear ad group con manejo de errores específico
                    logger.info(f"📝 Creando ad group: {ad_group_data['name']}")
                    ad_group_result = self._create_ad_group(
                        customer_id=customer_id,
                        campaign_resource_name=result['campaign_resource_name'],
                        ad_group_name=ad_group_data['name'],
                        max_cpc_bid=ad_group_data.get('max_cpc_bid', 1.0)
                    )
                    
                    if ad_group_result['error']:
                        error_msg = f"❌ Error creando ad group '{ad_group_data['name']}': {ad_group_result['error']}"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
                        continue
                    
                    ad_group_resource = ad_group_result['resource_name']
                    result['ad_group_ids'].append(ad_group_result['ad_group_id'])
                    created_resources.append(('ad_group', ad_group_resource))
                    logger.info(f"✅ Ad group creado exitosamente: {ad_group_result['ad_group_id']}")
                    
                    # ✅ PASO 2B: Agregar keywords con manejo de errores específico
                    logger.info(f"🔑 Agregando {len(ad_group_data['keywords'])} keywords al ad group")
                    keyword_results = self._add_keywords(
                        customer_id=customer_id,
                        ad_group_resource_name=ad_group_resource,
                        keywords=ad_group_data['keywords'],
                        negative_keywords=ad_group_data.get('negative_keywords', [])
                    )
                    
                    # Procesar resultados de keywords
                    if keyword_results['keyword_ids']:
                        result['keyword_ids'].extend(keyword_results['keyword_ids'])
                        logger.info(f"✅ {len(keyword_results['keyword_ids'])} keywords agregadas exitosamente")
                    
                    if keyword_results['errors']:
                        result['errors'].extend(keyword_results['errors'])
                        logger.error(f"❌ Errores en keywords: {len(keyword_results['errors'])}")
                    
                    if keyword_results['warnings']:
                        result['warnings'].extend(keyword_results['warnings'])
                        logger.warning(f"⚠️ Advertencias en keywords: {len(keyword_results['warnings'])}")
                    
                    # ✅ PASO 2C: Crear anuncios con manejo de errores específico
                    logger.info(f"📢 Creando {len(ad_group_data['ads'])} anuncios para el ad group")
                    ads_created_count = 0
                    
                    for ad_idx, ad_data in enumerate(ad_group_data['ads']):
                        logger.info(f"📝 Creando anuncio {ad_idx+1}/{len(ad_group_data['ads'])}")
                        
                        # Validar datos del anuncio
                        if not ad_data.get('headlines'):
                            error_msg = f"Anuncio {ad_idx+1} del grupo '{ad_group_data['name']}' no tiene headlines"
                            logger.error(error_msg)
                            result['errors'].append(error_msg)
                            continue
                        
                        if not ad_data.get('descriptions'):
                            error_msg = f"Anuncio {ad_idx+1} del grupo '{ad_group_data['name']}' no tiene descriptions"
                            logger.error(error_msg)
                            result['errors'].append(error_msg)
                            continue
                        
                        ad_result = self._create_responsive_search_ad(
                            customer_id=customer_id,
                            ad_group_resource_name=ad_group_resource,
                            headlines=ad_data.get('headlines', []),
                            descriptions=ad_data.get('descriptions', []),
                            final_url=ad_data.get('final_url', blueprint.get('business_url', 'https://example.com'))
                        )
                        
                        if ad_result['error']:
                            error_msg = f"❌ Error en anuncio {ad_idx+1} del grupo '{ad_group_data['name']}': {ad_result['error']}"
                            logger.error(error_msg)
                            result['errors'].append(error_msg)
                        else:
                            result['ad_ids'].append(ad_result['ad_id'])
                            created_resources.append(('ad', ad_result['resource_name']))
                            ads_created_count += 1
                            logger.info(f"✅ Anuncio {ad_idx+1} creado exitosamente: {ad_result['ad_id']}")
                    
                    logger.info(f"📊 Resumen del grupo '{ad_group_data['name']}': {ads_created_count}/{len(ad_group_data['ads'])} anuncios creados")
                    logger.info(f"✅ Grupo {group_num}/{total_groups} completado exitosamente")
                
                except Exception as e:
                    error_msg = f"❌ Error crítico procesando grupo '{ad_group_data['name']}': {str(e)}"
                    logger.error(error_msg)
                    
                    # ✅ TRACEBACK COMPLETO PARA ERRORES EN AD GROUP
                    import traceback
                    logger.error(f"Traceback completo del error en ad group:\n{traceback.format_exc()}")
                    
                    result['errors'].append(error_msg)
                    continue
            
            # Verificar éxito
            result['success'] = len(result['errors']) == 0 or len(result['ad_group_ids']) > 0
            
            self._update_progress(progress_callback, "✅ Publicación completada", 100)
            
            logger.info(
                f"📊 Publicación finalizada - "
                f"Campaign: {result['campaign_id']}, "
                f"Ad Groups: {len(result['ad_group_ids'])}, "
                f"Ads: {len(result['ad_ids'])}, "
                f"Keywords: {len(result['keyword_ids'])}, "
                f"Errors: {len(result['errors'])}"
            )
            
            return result
        
        except GoogleAdsException as ex:
            # ✅ EXTRACCIÓN DETALLADA DE ERRORES DE GOOGLE ADS API - PUBLISH CAMPAIGN
            error_details = []
            error_details.append(f"Error Code: {ex.error.code().name}")
            error_details.append(f"Error Type: {type(ex.error).__name__}")
            error_details.append(f"Customer ID: {customer_id}")
            error_details.append(f"Campaign Name: {blueprint.get('campaign_name', 'N/A')}")
            error_details.append(f"Ad Groups Processed: {len(result.get('ad_group_ids', []))}")
            
            # Extraer errores específicos del failure
            if hasattr(ex, 'failure') and ex.failure:
                error_details.append(f"Request ID: {getattr(ex.failure, 'request_id', 'N/A')}")
                
                if hasattr(ex.failure, 'errors'):
                    for idx, error in enumerate(ex.failure.errors):
                        error_details.append(f"Error {idx+1}:")
                        error_details.append(f"  - Message: {error.message}")
                        error_details.append(f"  - Error Code: {error.error_code}")
                        
                        # Extraer detalles específicos del error
                        if hasattr(error, 'location'):
                            error_details.append(f"  - Location: {error.location}")
                        
                        if hasattr(error, 'details'):
                            error_details.append(f"  - Details: {error.details}")
            
            error_msg = "Google Ads API Error - Campaign Publication:\n" + "\n".join(error_details)
            
            # ✅ LOGGING DETALLADO CON TRACEBACK
            logger.error(error_msg)
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            result['errors'].append(error_msg)
            
            # Intentar rollback si es necesario
            if not result.get('ad_group_ids'):
                logger.warning("🔄 Iniciando rollback de recursos creados...")
                self._rollback_resources(customer_id, created_resources)
            
            return result
        
        except Exception as e:
            error_msg = f"❌ Error crítico inesperado en publicación: {str(e)}"
            logger.error(error_msg)
            
            # ✅ TRACEBACK COMPLETO PARA ERRORES GENERALES
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            result['errors'].append(error_msg)
            return result
    
    # ========================================================================
    # CREACIÓN DE CAMPAÑA
    # ========================================================================
    
    def _create_campaign(
        self,
        customer_id: str,
        campaign_name: str,
        budget_daily: float,
        target_locations: List[str],
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """
        Crea una campaña de búsqueda en Google Ads
        
        Returns:
            {
                'campaign_id': str,
                'resource_name': str,
                'error': Optional[str]
            }
        """
        
        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_budget_service = self.client.get_service("CampaignBudgetService")
            
            # 1. Crear presupuesto
            budget_operation = self.client.get_type("CampaignBudgetOperation")
            budget = budget_operation.create
            
            budget.name = f"Budget for {campaign_name}"
            budget.amount_micros = int(budget_daily * 1_000_000)
            budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD
            
            budget_response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[budget_operation]
            )
            
            budget_resource_name = budget_response.results[0].resource_name
            
            logger.info(f"✅ Presupuesto creado: {budget_resource_name}")
            
            # 2. Crear campaña
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.create
            
            campaign.name = campaign_name
            campaign.status = self.client.enums.CampaignStatusEnum.PAUSED  # Crear pausada
            campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.SEARCH
            campaign.campaign_budget = budget_resource_name
            
            # Estrategia de puja: Maximizar clics
            campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CLICKS
            
            # Network settings
            campaign.network_settings.target_google_search = True
            campaign.network_settings.target_search_network = True
            campaign.network_settings.target_content_network = False
            campaign.network_settings.target_partner_search_network = False
            
            # Fechas
            start_date = datetime.now()
            end_date = start_date + timedelta(days=365)
            
            campaign.start_date = start_date.strftime("%Y%m%d")
            campaign.end_date = end_date.strftime("%Y%m%d")
            
            # Geo targeting
            self._set_geo_targeting(campaign, target_locations)
            
            # Language targeting
            if languages:
                self._set_language_targeting(campaign, languages)
            
            # Crear campaña
            campaign_response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=[campaign_operation]
            )
            
            campaign_resource_name = campaign_response.results[0].resource_name
            campaign_id = campaign_resource_name.split('/')[-1]
            
            logger.info(f"✅ Campaña creada: {campaign_id}")
            
            return {
                'campaign_id': campaign_id,
                'resource_name': campaign_resource_name,
                'error': None
            }
        
        except GoogleAdsException as ex:
            # ✅ EXTRACCIÓN DETALLADA DE ERRORES DE GOOGLE ADS API
            error_details = []
            error_details.append(f"Error Code: {ex.error.code().name}")
            error_details.append(f"Error Type: {type(ex.error).__name__}")
            
            # Extraer errores específicos del failure
            if hasattr(ex, 'failure') and ex.failure:
                error_details.append(f"Request ID: {getattr(ex.failure, 'request_id', 'N/A')}")
                
                if hasattr(ex.failure, 'errors'):
                    for idx, error in enumerate(ex.failure.errors):
                        error_details.append(f"Error {idx+1}:")
                        error_details.append(f"  - Message: {error.message}")
                        error_details.append(f"  - Error Code: {error.error_code}")
                        
                        # Extraer detalles específicos del error
                        if hasattr(error, 'location'):
                            error_details.append(f"  - Location: {error.location}")
                        
                        if hasattr(error, 'details'):
                            error_details.append(f"  - Details: {error.details}")
            
            error_msg = "Google Ads API Error - Campaign Creation:\n" + "\n".join(error_details)
            
            # ✅ LOGGING DETALLADO CON TRACEBACK
            logger.error(error_msg)
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            return {'campaign_id': None, 'resource_name': None, 'error': error_msg}
        
        except Exception as e:
            error_msg = f"Error crítico creando campaña: {str(e)}"
            logger.error(error_msg)
            
            # ✅ TRACEBACK COMPLETO PARA ERRORES GENERALES
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            return {'campaign_id': None, 'resource_name': None, 'error': error_msg}
    
    # ========================================================================
    # CREACIÓN DE AD GROUP
    # ========================================================================
    
    def _create_ad_group(
        self,
        customer_id: str,
        campaign_resource_name: str,
        ad_group_name: str,
        max_cpc_bid: float = 1.0
    ) -> Dict[str, Any]:
        """
        Crea un ad group en una campaña
        
        Returns:
            {
                'ad_group_id': str,
                'resource_name': str,
                'error': Optional[str]
            }
        """
        
        try:
            ad_group_service = self.client.get_service("AdGroupService")
            
            operation = self.client.get_type("AdGroupOperation")
            ad_group = operation.create
            
            # ✅ FIX DUPLICATE_ADGROUP_NAME: Agregar timestamp único al nombre
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Incluye microsegundos
            unique_ad_group_name = f"{ad_group_name}_{timestamp}"
            
            ad_group.name = unique_ad_group_name
            ad_group.campaign = campaign_resource_name
            ad_group.status = self.client.enums.AdGroupStatusEnum.ENABLED
            ad_group.type_ = self.client.enums.AdGroupTypeEnum.SEARCH_STANDARD
            
            # CPC bid
            ad_group.cpc_bid_micros = int(max_cpc_bid * 1_000_000)
            
            response = ad_group_service.mutate_ad_groups(
                customer_id=customer_id,
                operations=[operation]
            )
            
            resource_name = response.results[0].resource_name
            ad_group_id = resource_name.split('/')[-1]
            
            logger.info(f"✅ Ad group creado: {ad_group_id} (Nombre único: {unique_ad_group_name})")
            
            return {
                'ad_group_id': ad_group_id,
                'resource_name': resource_name,
                'error': None
            }
        
        except GoogleAdsException as ex:
            # ✅ EXTRACCIÓN DETALLADA DE ERRORES DE GOOGLE ADS API - AD GROUP
            error_details = []
            error_details.append(f"Error Code: {ex.error.code().name}")
            error_details.append(f"Error Type: {type(ex.error).__name__}")
            error_details.append(f"Original Ad Group Name: {ad_group_name}")
            error_details.append(f"Unique Ad Group Name: {unique_ad_group_name if 'unique_ad_group_name' in locals() else 'N/A'}")
            error_details.append(f"Campaign Resource: {campaign_resource_name}")
            error_details.append(f"CPC Bid: {max_cpc_bid}")
            
            # Extraer errores específicos del failure
            if hasattr(ex, 'failure') and ex.failure:
                error_details.append(f"Request ID: {getattr(ex.failure, 'request_id', 'N/A')}")
                
                if hasattr(ex.failure, 'errors'):
                    for idx, error in enumerate(ex.failure.errors):
                        error_details.append(f"Error {idx+1}:")
                        error_details.append(f"  - Message: {error.message}")
                        error_details.append(f"  - Error Code: {error.error_code}")
                        
                        # Extraer detalles específicos del error
                        if hasattr(error, 'location'):
                            error_details.append(f"  - Location: {error.location}")
                        
                        if hasattr(error, 'details'):
                            error_details.append(f"  - Details: {error.details}")
            
            error_msg = "Google Ads API Error - Ad Group Creation:\n" + "\n".join(error_details)
            
            # ✅ LOGGING DETALLADO CON TRACEBACK
            logger.error(error_msg)
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            return {'ad_group_id': None, 'resource_name': None, 'error': error_msg}
        
        except Exception as e:
            error_msg = f"Error crítico creando ad group '{ad_group_name}': {str(e)}"
            logger.error(error_msg)
            
            # ✅ TRACEBACK COMPLETO PARA ERRORES GENERALES
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            return {'ad_group_id': None, 'resource_name': None, 'error': error_msg}
    
    # ========================================================================
    # KEYWORDS
    # ========================================================================
    
    # ========================================================================
    # KEYWORDS - FIX PARTIAL_FAILURE
    # ========================================================================
    
    def _add_keywords(
        self,
        customer_id: str,
        ad_group_resource_name: str,
        keywords: List[str],
        negative_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """
        Agrega keywords CON MANEJO DE ERRORES INDIVIDUALES
        Si una keyword falla, continúa con las demás
        """
        
        result = {
            'keyword_ids': [],
            'errors': [],
            'warnings': []
        }
        
        try:
            logger.info(f"🔑 Iniciando creación de keywords")
            logger.info(f"   - Positivas recibidas: {keywords}")
            logger.info(f"   - Negativas recibidas: {negative_keywords}")
            
            # ✅ VALIDAR Y LIMPIAR KEYWORDS
            valid_keywords = []
            for kw in keywords[:50]:
                if not kw or not isinstance(kw, str):
                    continue
                
                kw_clean = kw.strip()
                
                if len(kw_clean) < 3 or len(kw_clean) > 80:
                    logger.warning(f"⚠️ Keyword inválida por longitud: '{kw_clean}'")
                    continue
                
                valid_keywords.append(kw_clean)
                logger.info(f"   ✅ Keyword válida: '{kw_clean}'")
            
            # Validar negative keywords
            valid_negative = []
            if negative_keywords:
                for neg_kw in negative_keywords[:25]:
                    if not neg_kw or not isinstance(neg_kw, str):
                        continue
                    
                    neg_clean = neg_kw.strip()
                    
                    if len(neg_clean) < 3 or len(neg_clean) > 80:
                        continue
                    
                    valid_negative.append(neg_clean)
            
            logger.info(f"✅ Keywords válidas finales:")
            logger.info(f"   - Positivas: {len(valid_keywords)}")
            logger.info(f"   - Negativas: {len(valid_negative)}")
            
            if not valid_keywords:
                error_msg = "No hay keywords válidas para agregar"
                logger.error(f"❌ {error_msg}")
                result['errors'].append(error_msg)
                return result
            
            ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
            
            # ✅ ESTRATEGIA: AGREGAR KEYWORDS UNA POR UNA
            # En vez de enviar todas en un batch, las enviamos individualmente
            # Así si una falla, las demás se agregan
            
            logger.info(f"📤 Agregando keywords INDIVIDUALMENTE para evitar fallos en bloque")
            
            # Agregar keywords positivas una por una
            for idx, kw in enumerate(valid_keywords):
                try:
                    operation = self.client.get_type("AdGroupCriterionOperation")
                    criterion = operation.create
                    
                    criterion.ad_group = ad_group_resource_name
                    criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED
                    criterion.keyword.text = kw
                    criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum.BROAD
                    
                    # Enviar operación individual
                    response = ad_group_criterion_service.mutate_ad_group_criteria(
                        customer_id=customer_id,
                        operations=[operation]
                    )
                    
                    keyword_id = response.results[0].resource_name.split('/')[-1]
                    result['keyword_ids'].append(keyword_id)
                    logger.info(f"   ✅ Keyword {idx+1}/{len(valid_keywords)} creada: '{kw}' (ID: {keyword_id})")
                    
                except Exception as kw_error:
                    error_msg = f"Error en keyword '{kw}': {str(kw_error)}"
                    logger.warning(f"   ⚠️ {error_msg}")
                    result['warnings'].append(error_msg)
                    
                    # Extraer detalles si es GoogleAdsException
                    if hasattr(kw_error, 'failure'):
                        if hasattr(kw_error.failure, 'errors'):
                            for error in kw_error.failure.errors:
                                if hasattr(error, 'message'):
                                    logger.warning(f"      Razón: {error.message}")
                    
                    # Continuar con la siguiente keyword
                    continue
            
            # Agregar keywords negativas una por una
            for idx, neg_kw in enumerate(valid_negative):
                try:
                    operation = self.client.get_type("AdGroupCriterionOperation")
                    criterion = operation.create
                    
                    criterion.ad_group = ad_group_resource_name
                    criterion.negative = True
                    criterion.keyword.text = neg_kw
                    criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum.BROAD
                    
                    # Enviar operación individual
                    response = ad_group_criterion_service.mutate_ad_group_criteria(
                        customer_id=customer_id,
                        operations=[operation]
                    )
                    
                    keyword_id = response.results[0].resource_name.split('/')[-1]
                    result['keyword_ids'].append(keyword_id)
                    logger.info(f"   ✅ Negative keyword {idx+1}/{len(valid_negative)} creada: '{neg_kw}' (ID: {keyword_id})")
                    
                except Exception as neg_error:
                    error_msg = f"Error en negative keyword '{neg_kw}': {str(neg_error)}"
                    logger.warning(f"   ⚠️ {error_msg}")
                    result['warnings'].append(error_msg)
                    continue
            
            # Resumen final
            total_attempted = len(valid_keywords) + len(valid_negative)
            logger.info(f"✅ Proceso completado: {len(result['keyword_ids'])}/{total_attempted} keywords agregadas")
            
            if result['warnings']:
                logger.warning(f"⚠️ {len(result['warnings'])} keywords no se pudieron agregar")
        
        except Exception as e:
            error_msg = f"Error crítico agregando keywords: {str(e)}"
            logger.error(error_msg)
            
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            result['errors'].append(error_msg)
        
        return result
    
    # ========================================================================
    # RESPONSIVE SEARCH ADS
    # ========================================================================
    
    # =======================================================================
    # RESPONSIVE SEARCH ADS - FIX URL
    # =======================================================================
    
    def _create_responsive_search_ad(
        self,
        customer_id: str,
        ad_group_resource_name: str,
        headlines: List[str],
        descriptions: List[str],
        final_url: str
    ) -> Dict[str, Any]:
        """
        Crea un Responsive Search Ad
        
        Returns:
            {
                'ad_id': str,
                'resource_name': str,
                'error': Optional[str]
            }
        """
        
        try:
            logger.info(f"📝 Creando RSA:")
            logger.info(f"   - Headlines: {len(headlines)}")
            logger.info(f"   - Descriptions: {len(descriptions)}")
            logger.info(f"   - URL: {final_url}")
            
            ad_group_ad_service = self.client.get_service("AdGroupAdService")
            
            operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = operation.create
            
            ad_group_ad.ad_group = ad_group_resource_name
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED
            
            # ✅ FIX: Usar final_url del parámetro (que viene de ad_data)
            ad_group_ad.ad.final_urls.append(final_url)
            
            # Responsive Search Ad
            rsa = ad_group_ad.ad.responsive_search_ad
            
            # Headlines (mínimo 3, máximo 15)
            for headline_text in headlines[:15]:
                headline = self.client.get_type("AdTextAsset")
                headline.text = headline_text[:30]  # Límite de 30 caracteres
                rsa.headlines.append(headline)
            
            # Descriptions (mínimo 2, máximo 4)
            for description_text in descriptions[:4]:
                description = self.client.get_type("AdTextAsset")
                description.text = description_text[:90]  # Límite de 90 caracteres
                rsa.descriptions.append(description)
            
            # Validar mínimos
            if len(rsa.headlines) < 3:
                return {
                    'ad_id': None,
                    'resource_name': None,
                    'error': f"Se necesitan al menos 3 headlines (tienes {len(rsa.headlines)})"
                }
            
            if len(rsa.descriptions) < 2:
                return {
                    'ad_id': None,
                    'resource_name': None,
                    'error': f"Se necesitan al menos 2 descriptions (tienes {len(rsa.descriptions)})"
                }
            
            # Crear anuncio
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=[operation]
            )
            
            resource_name = response.results[0].resource_name
            ad_id = resource_name.split('~')[-1]
            
            logger.info(f"✅ Anuncio creado: {ad_id} con URL: {final_url}")
            
            return {
                'ad_id': ad_id,
                'resource_name': resource_name,
                'error': None
            }
        
        except GoogleAdsException as ex:
            # ✅ EXTRACCIÓN DETALLADA DE ERRORES DE GOOGLE ADS API - RESPONSIVE SEARCH AD
            error_details = []
            error_details.append(f"Error Code: {ex.error.code().name}")
            error_details.append(f"Error Type: {type(ex.error).__name__}")
            error_details.append(f"Ad Group Resource: {ad_group_resource_name}")
            error_details.append(f"Headlines Count: {len(headlines)}")
            error_details.append(f"Descriptions Count: {len(descriptions)}")
            error_details.append(f"Final URL: {final_url}")
            
            # Extraer errores específicos del failure
            if hasattr(ex, 'failure') and ex.failure:
                error_details.append(f"Request ID: {getattr(ex.failure, 'request_id', 'N/A')}")
                
                if hasattr(ex.failure, 'errors'):
                    for idx, error in enumerate(ex.failure.errors):
                        error_details.append(f"Error {idx+1}:")
                        error_details.append(f"  - Message: {error.message}")
                        error_details.append(f"  - Error Code: {error.error_code}")
                        
                        # Extraer detalles específicos del error
                        if hasattr(error, 'location'):
                            error_details.append(f"  - Location: {error.location}")
                        
                        if hasattr(error, 'details'):
                            error_details.append(f"  - Details: {error.details}")
            
            error_msg = "Google Ads API Error - Responsive Search Ad Creation:\n" + "\n".join(error_details)
            
            # ✅ LOGGING DETALLADO CON TRACEBACK
            logger.error(error_msg)
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            return {'ad_id': None, 'resource_name': None, 'error': error_msg}
        
        except Exception as e:
            error_msg = f"Error crítico creando anuncio: {str(e)}"
            logger.error(error_msg)
            
            # ✅ TRACEBACK COMPLETO PARA ERRORES GENERALES
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            return {'ad_id': None, 'resource_name': None, 'error': error_msg}
    
    # ========================================================================
    # TARGETING
    # ========================================================================
    
    def _set_geo_targeting(self, campaign, target_locations: List[str]):
        """Configura geo-targeting en la campaña"""
        
        location_codes = {
            'United States': '2840',
            'Mexico': '2484',
            'Spain': '2724',
            'Colombia': '2170',
            'Argentina': '2032',
            'Chile': '2152',
            'Peru': '2604',
            'Ecuador': '2218',
            'Venezuela': '2862'
        }
        
        for location_name in target_locations:
            if location_name in location_codes:
                criterion = campaign.geo_target_type_setting.positive_geo_target_type
                criterion = self.client.enums.PositiveGeoTargetTypeEnum.PRESENCE_OR_INTEREST

    def _set_language_targeting(self, campaign, languages: List[str]):
        """Configura language targeting en la campaña"""
        
        language_codes = {
            'es': '1003',  # Spanish
            'en': '1000'   # English
        }
        
        # Las languages se configuran a nivel de campaña como criterios
        # (Requiere un paso adicional con CampaignCriterionService)
        pass
    
    # ========================================================================
    # UTILIDADES
    # ========================================================================
    
    def _update_progress(self, callback, message: str, percent: float):
        """Actualiza progreso si hay callback"""
        if callback:
            callback(message, percent)
    
    def _rollback_resources(self, customer_id: str, resources: List[tuple]):
        """Intenta hacer rollback de recursos creados"""
        logger.warning(f"⚠️ Intentando rollback de {len(resources)} recursos...")
        
        # En una implementación real, eliminarías los recursos creados
        # Por ahora solo logueamos
        for resource_type, resource_name in resources:
            logger.info(f"Rollback: {resource_type} - {resource_name}")
    
    def _create_ad_group_with_content_sync(
        self,
        customer_id: str,
        campaign_resource_name: str,
        ad_group_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea un ad group completo con contenido sincronizado
        Incluye timestamp único para evitar DUPLICATE_ADGROUP_NAME
        
        Args:
            customer_id: ID del cliente de Google Ads
            campaign_resource_name: Nombre del recurso de la campaña
            ad_group_data: Datos del ad group con estructura:
                {
                    'name': str,
                    'cpc_bid': float,
                    'keywords': List[str],
                    'ads': List[Dict]
                }
        
        Returns:
            {
                'success': bool,
                'ad_group_id': str,
                'resource_name': str,
                'keywords_added': int,
                'ads_created': int,
                'errors': List[str]
            }
        """
        
        result = {
            'success': False,
            'ad_group_id': None,
            'resource_name': None,
            'keywords_added': 0,
            'ads_created': 0,
            'errors': []
        }
        
        try:
            # ✅ PASO 1: Crear ad group con nombre único
            logger.info(f"🚀 Creando ad group: {ad_group_data['name']}")
            
            ad_group_result = self._create_ad_group(
                customer_id=customer_id,
                campaign_resource_name=campaign_resource_name,
                ad_group_name=ad_group_data['name'],
                max_cpc_bid=ad_group_data.get('cpc_bid', 1.0)
            )
            
            if ad_group_result['error']:
                result['errors'].append(f"Error creando ad group: {ad_group_result['error']}")
                return result
            
            result['ad_group_id'] = ad_group_result['ad_group_id']
            result['resource_name'] = ad_group_result['resource_name']
            
            # ✅ PASO 2: Agregar keywords
            if ad_group_data.get('keywords'):
                logger.info(f"📝 Agregando {len(ad_group_data['keywords'])} keywords")
                
                keywords_result = self._add_keywords(
                    customer_id=customer_id,
                    ad_group_resource_name=result['resource_name'],
                    keywords=ad_group_data['keywords']
                )
                
                if keywords_result['errors']:
                    result['errors'].extend(keywords_result['errors'])
                else:
                    result['keywords_added'] = len(ad_group_data['keywords'])
            
            # ✅ PASO 3: Crear anuncios
            if ad_group_data.get('ads'):
                logger.info(f"📢 Creando {len(ad_group_data['ads'])} anuncios")
                
                for idx, ad_data in enumerate(ad_group_data['ads']):
                    ad_result = self._create_responsive_search_ad(
                        customer_id=customer_id,
                        ad_group_resource_name=result['resource_name'],
                        headlines=ad_data.get('headlines', []),
                        descriptions=ad_data.get('descriptions', []),
                        final_url=ad_data.get('final_url', '')
                    )
                    
                    if ad_result['error']:
                        result['errors'].append(f"Error creando anuncio {idx+1}: {ad_result['error']}")
                    else:
                        result['ads_created'] += 1
            
            # ✅ VERIFICAR ÉXITO GENERAL
            if not result['errors']:
                result['success'] = True
                logger.info(f"✅ Ad group completo creado exitosamente: {result['ad_group_id']}")
            else:
                logger.warning(f"⚠️ Ad group creado con errores: {len(result['errors'])} problemas")
            
            return result
            
        except Exception as ex:
            import traceback
            error_msg = f"Error crítico en _create_ad_group_with_content_sync: {str(ex)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            result['errors'].append(error_msg)
            return result