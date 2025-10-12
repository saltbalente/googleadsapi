"""
Ad Group Service
Servicio para gestionar grupos de anuncios en Google Ads
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date, timedelta

logger = logging.getLogger(__name__)

class AdGroupService:
    """Servicio para gestionar grupos de anuncios"""
    
    def __init__(self, google_ads_client):
        """
        Inicializa el servicio de grupos de anuncios
        
        Args:
            google_ads_client: Cliente de Google Ads (wrapper)
        """
        self.client = google_ads_client.get_client()
        self.wrapper = google_ads_client
    
    def get_ad_groups_by_campaign(
        self, 
        customer_id: str, 
        campaign_id: str,
        include_metrics: bool = True,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los grupos de anuncios de una campaña
        
        Args:
            customer_id: ID del cliente
            campaign_id: ID de la campaña
            include_metrics: Si incluir métricas de rendimiento
            start_date: Fecha de inicio para métricas (default: últimos 30 días)
            end_date: Fecha de fin para métricas (default: hoy)
        
        Returns:
            Lista de grupos de anuncios con sus datos
        """
        try:
            # Configurar fechas por defecto
            if end_date is None:
                end_date = date.today()
            if start_date is None:
                start_date = end_date - timedelta(days=30)
            
            # Construir query base
            query = """
                SELECT
                    ad_group.id,
                    ad_group.name,
                    ad_group.status,
                    ad_group.type,
                    ad_group.cpc_bid_micros,
                    ad_group.target_cpa_micros,
                    ad_group.target_roas,
                    campaign.id,
                    campaign.name
            """
            
            # Agregar métricas si se solicitan
            if include_metrics:
                query += """,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value,
                    metrics.average_cpc,
                    metrics.ctr
                """
            
            query += f"""
                FROM ad_group
                WHERE campaign.id = {campaign_id}
                AND ad_group.status != 'REMOVED'
            """
            
            # Agregar rango de fechas si incluimos métricas
            if include_metrics:
                query += f"""
                AND segments.date BETWEEN '{start_date.strftime('%Y-%m-%d')}' 
                AND '{end_date.strftime('%Y-%m-%d')}'
                """
            
            query += " ORDER BY ad_group.name"
            
            logger.info(f"🔍 Ejecutando query para obtener grupos de campaña {campaign_id}")
            logger.debug(f"Query: {query}")
            
            # Ejecutar query
            ga_service = self.client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=customer_id, query=query)
            
            # Procesar resultados
            ad_groups = []
            ad_groups_dict = {}  # Para agrupar métricas por ad_group_id
            
            for row in response:
                ad_group_id = str(row.ad_group.id)
                
                # Si el grupo ya existe, acumular métricas
                if ad_group_id in ad_groups_dict:
                    if include_metrics:
                        ad_groups_dict[ad_group_id]['metrics']['impressions'] += row.metrics.impressions
                        ad_groups_dict[ad_group_id]['metrics']['clicks'] += row.metrics.clicks
                        ad_groups_dict[ad_group_id]['metrics']['cost_micros'] += row.metrics.cost_micros
                        ad_groups_dict[ad_group_id]['metrics']['conversions'] += row.metrics.conversions
                        ad_groups_dict[ad_group_id]['metrics']['conversions_value'] += row.metrics.conversions_value
                else:
                    # Crear nuevo grupo
                    ad_group_data = {
                        'id': ad_group_id,
                        'name': row.ad_group.name,
                        'status': row.ad_group.status.name,
                        'type': row.ad_group.type_.name,
                        'cpc_bid_micros': row.ad_group.cpc_bid_micros,
                        'target_cpa_micros': row.ad_group.target_cpa_micros,
                        'target_roas': row.ad_group.target_roas,
                        'campaign_id': str(row.campaign.id),
                        'campaign_name': row.campaign.name
                    }
                    
                    # Agregar métricas si se solicitan
                    if include_metrics:
                        ad_group_data['metrics'] = {
                            'impressions': row.metrics.impressions,
                            'clicks': row.metrics.clicks,
                            'cost_micros': row.metrics.cost_micros,
                            'conversions': row.metrics.conversions,
                            'conversions_value': row.metrics.conversions_value,
                            'average_cpc': row.metrics.average_cpc,
                            'ctr': row.metrics.ctr
                        }
                    
                    ad_groups_dict[ad_group_id] = ad_group_data
            
            # Convertir dict a lista
            ad_groups = list(ad_groups_dict.values())
            
            logger.info(f"✅ {len(ad_groups)} grupos de anuncios obtenidos para campaña {campaign_id}")
            return ad_groups
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo grupos de anuncios: {e}", exc_info=True)
            return []
    
    def get_ads_by_ad_group(
        self, 
        customer_id: str, 
        ad_group_id: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los anuncios de un grupo
        
        Args:
            customer_id: ID del cliente
            ad_group_id: ID del grupo de anuncios
        
        Returns:
            Lista de anuncios con sus datos
        """
        try:
            query = f"""
                SELECT
                    ad_group_ad.ad.id,
                    ad_group_ad.ad.name,
                    ad_group_ad.status,
                    ad_group_ad.ad.type,
                    ad_group_ad.ad.final_urls,
                    ad_group_ad.ad.responsive_search_ad.headlines,
                    ad_group_ad.ad.responsive_search_ad.descriptions,
                    ad_group_ad.ad.responsive_search_ad.path1,
                    ad_group_ad.ad.responsive_search_ad.path2,
                    ad_group_ad.policy_summary.approval_status
                FROM ad_group_ad
                WHERE ad_group.id = {ad_group_id}
                AND ad_group_ad.status != 'REMOVED'
            """
            
            logger.info(f"🔍 Obteniendo anuncios del grupo {ad_group_id}")
            
            ga_service = self.client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=customer_id, query=query)
            
            ads = []
            
            for row in response:
                ad = row.ad_group_ad.ad
                
                # Procesar headlines
                headlines = []
                if ad.responsive_search_ad.headlines:
                    headlines = [h.text for h in ad.responsive_search_ad.headlines]
                
                # Procesar descriptions
                descriptions = []
                if ad.responsive_search_ad.descriptions:
                    descriptions = [d.text for d in ad.responsive_search_ad.descriptions]
                
                # Procesar URLs
                final_urls = []
                if ad.final_urls:
                    final_urls = list(ad.final_urls)
                
                ad_data = {
                    'id': str(ad.id),
                    'name': ad.name if ad.name else f"Anuncio {ad.id}",
                    'status': row.ad_group_ad.status.name,
                    'type': ad.type_.name,
                    'final_urls': final_urls,
                    'headlines': headlines,
                    'descriptions': descriptions,
                    'path1': ad.responsive_search_ad.path1,
                    'path2': ad.responsive_search_ad.path2,
                    'approval_status': row.ad_group_ad.policy_summary.approval_status.name if row.ad_group_ad.policy_summary else 'UNKNOWN'
                }
                
                ads.append(ad_data)
            
            logger.info(f"✅ {len(ads)} anuncios obtenidos del grupo {ad_group_id}")
            return ads
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo anuncios del grupo: {e}", exc_info=True)
            return []
    
    def get_keywords_by_ad_group(
        self, 
        customer_id: str, 
        ad_group_id: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las keywords de un grupo
        
        Args:
            customer_id: ID del cliente
            ad_group_id: ID del grupo de anuncios
        
        Returns:
            Lista de keywords con sus datos
        """
        try:
            query = f"""
                SELECT
                    ad_group_criterion.criterion_id,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status,
                    ad_group_criterion.quality_info.quality_score,
                    ad_group_criterion.cpc_bid_micros
                FROM ad_group_criterion
                WHERE ad_group.id = {ad_group_id}
                AND ad_group_criterion.type = 'KEYWORD'
                AND ad_group_criterion.status != 'REMOVED'
            """
            
            logger.info(f"🔍 Obteniendo keywords del grupo {ad_group_id}")
            
            ga_service = self.client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=customer_id, query=query)
            
            keywords = []
            
            for row in response:
                keyword_data = {
                    'id': str(row.ad_group_criterion.criterion_id),
                    'text': row.ad_group_criterion.keyword.text,
                    'match_type': row.ad_group_criterion.keyword.match_type.name,
                    'status': row.ad_group_criterion.status.name,
                    'quality_score': row.ad_group_criterion.quality_info.quality_score if row.ad_group_criterion.quality_info else None,
                    'cpc_bid_micros': row.ad_group_criterion.cpc_bid_micros
                }
                
                keywords.append(keyword_data)
            
            logger.info(f"✅ {len(keywords)} keywords obtenidas del grupo {ad_group_id}")
            return keywords
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo keywords del grupo {ad_group_id}: {e}", exc_info=True)
            return []
    
    def create_ad_in_ad_group(
        self,
        customer_id: str,
        ad_group_id: str,
        headlines: List[str],
        descriptions: List[str],
        final_url: str,
        path1: str = "",
        path2: str = ""
    ) -> Dict[str, Any]:
        """
        Crea un nuevo anuncio en un grupo existente
        
        Args:
            customer_id: ID del cliente
            ad_group_id: ID del grupo donde crear el anuncio
            headlines: Lista de títulos (mínimo 3, máximo 15)
            descriptions: Lista de descripciones (mínimo 2, máximo 4)
            final_url: URL de destino
            path1: Ruta 1 de visualización (opcional)
            path2: Ruta 2 de visualización (opcional)
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            logger.info(f"🚀 Creando anuncio en grupo {ad_group_id}")
            
            # Validaciones
            if len(headlines) < 3:
                return {
                    'success': False,
                    'error': 'Se requieren al menos 3 títulos'
                }
            
            if len(descriptions) < 2:
                return {
                    'success': False,
                    'error': 'Se requieren al menos 2 descripciones'
                }
            
            if not final_url:
                return {
                    'success': False,
                    'error': 'Se requiere una URL de destino'
                }
            
            # Obtener servicio
            ad_group_ad_service = self.client.get_service("AdGroupAdService")
            ad_group_service = self.client.get_service("AdGroupService")
            
            # Crear operación
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.create
            
            # Configurar grupo
            ad_group_ad.ad_group = ad_group_service.ad_group_path(customer_id, ad_group_id)
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED
            
            # Configurar anuncio
            ad = ad_group_ad.ad
            ad.final_urls.append(final_url)
            
            # Agregar títulos
            for headline_text in headlines[:15]:  # Máximo 15
                if headline_text.strip():
                    headline = self.client.get_type("AdTextAsset")
                    headline.text = headline_text.strip()
                    ad.responsive_search_ad.headlines.append(headline)
            
            # Agregar descripciones
            for description_text in descriptions[:4]:  # Máximo 4
                if description_text.strip():
                    description = self.client.get_type("AdTextAsset")
                    description.text = description_text.strip()
                    ad.responsive_search_ad.descriptions.append(description)
            
            # Agregar rutas
            if path1:
                ad.responsive_search_ad.path1 = path1
            if path2:
                ad.responsive_search_ad.path2 = path2
            
            # Ejecutar creación
            logger.info("📤 Enviando anuncio a Google Ads...")
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=[ad_group_ad_operation]
            )
            
            ad_resource_name = response.results[0].resource_name
            ad_id = ad_resource_name.split('/')[-1]
            
            logger.info(f"✅ Anuncio creado exitosamente: {ad_id}")
            
            return {
                'success': True,
                'ad_id': ad_id,
                'resource_name': ad_resource_name,
                'message': f'Anuncio creado exitosamente (ID: {ad_id})'
            }
        
        except Exception as e:
            logger.error(f"❌ Error creando anuncio: {e}", exc_info=True)
            
            error_msg = str(e)
            error_details = [error_msg]
            
            # Capturar detalles adicionales si existen
            if hasattr(e, 'failure'):
                try:
                    for error in e.failure.errors:
                        error_details.append(f"  → {error.message}")
                except:
                    pass
            
            return {
                'success': False,
                'error': error_msg,
                'details': error_details
            }