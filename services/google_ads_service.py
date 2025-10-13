#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
GOOGLE ADS SERVICE PARA GENERADOR IA 2.0
Servicio completo para integración con Google Ads API
Versión: 2.0
Fecha: 2025-01-13
============================================================================
"""

import logging
import json
import yaml
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
    from google.protobuf import field_mask_pb2
    GOOGLE_ADS_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_AVAILABLE = False
    logging.warning("Google Ads API no disponible. Usando modo simulación.")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdStatus(Enum):
    """Estados de anuncios"""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"

class CampaignStatus(Enum):
    """Estados de campañas"""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"

@dataclass
class AdGroupAd:
    """Representación de un anuncio en Google Ads"""
    resource_name: str
    ad_id: str
    ad_group_id: str
    campaign_id: str
    status: AdStatus
    headlines: List[str]
    descriptions: List[str]
    final_urls: List[str]
    path1: Optional[str] = None
    path2: Optional[str] = None

@dataclass
class Campaign:
    """Representación de una campaña en Google Ads"""
    resource_name: str
    campaign_id: str
    name: str
    status: CampaignStatus
    budget_amount: float
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None

@dataclass
class AdGroup:
    """Representación de un grupo de anuncios"""
    resource_name: str
    ad_group_id: str
    campaign_id: str
    name: str
    status: str
    cpc_bid: Optional[float] = None

@dataclass
class AdCreationRequest:
    """Solicitud para crear un anuncio"""
    customer_id: str
    ad_group_id: str
    headlines: List[str]
    descriptions: List[str]
    final_urls: List[str]
    path1: Optional[str] = None
    path2: Optional[str] = None

@dataclass
class AdPerformanceMetrics:
    """Métricas de rendimiento de anuncio"""
    ad_id: str
    impressions: int
    clicks: int
    conversions: float
    cost: float
    ctr: float
    conversion_rate: float
    cpc: float
    cpa: float
    quality_score: Optional[float] = None

class EsotericGoogleAdsService:
    """
    Servicio completo para integración con Google Ads API
    Especializado en anuncios esotéricos
    """
    
    def __init__(self, config_path: Optional[str] = None, credentials_path: Optional[str] = None):
        """
        Inicializar el servicio de Google Ads
        
        Args:
            config_path: Ruta al archivo de configuración
            credentials_path: Ruta a las credenciales de Google Ads
        """
        self.config_path = config_path or self._get_default_config_path()
        self.credentials_path = credentials_path
        
        # Configuraciones
        self.config = {}
        self.client = None
        self.simulation_mode = not GOOGLE_ADS_AVAILABLE
        
        # Servicios de Google Ads
        self.ad_group_ad_service = None
        self.campaign_service = None
        self.ad_group_service = None
        self.googleads_service = None
        self.keyword_plan_service = None
        
        # Cache para optimizar consultas
        self.cache = {
            'campaigns': {},
            'ad_groups': {},
            'ads': {},
            'performance': {}
        }
        
        # Cargar configuraciones e inicializar cliente
        self._load_config()
        self._initialize_client()
        
        logger.info(f"Google Ads Service inicializado - Modo: {'Simulación' if self.simulation_mode else 'Producción'}")
    
    def _get_default_config_path(self) -> str:
        """Obtener ruta por defecto de configuración"""
        return "config/google_ads_config.yaml"
    
    def _load_config(self) -> None:
        """Cargar configuración del servicio"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                self._create_default_config()
            
            logger.info("Configuración de Google Ads cargada")
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Crear configuración por defecto"""
        self.config = {
            'google_ads': {
                'developer_token': 'YOUR_DEVELOPER_TOKEN',
                'client_id': 'YOUR_CLIENT_ID',
                'client_secret': 'YOUR_CLIENT_SECRET',
                'refresh_token': 'YOUR_REFRESH_TOKEN',
                'login_customer_id': 'YOUR_LOGIN_CUSTOMER_ID'
            },
            'defaults': {
                'campaign_budget': 1000.0,
                'ad_group_cpc': 1.50,
                'max_headlines': 15,
                'max_descriptions': 4,
                'esoteric_categories': [
                    'amarres_amor',
                    'tarot',
                    'limpias_espirituales',
                    'rituales_dinero',
                    'proteccion_espiritual'
                ]
            },
            'performance': {
                'cache_duration_minutes': 30,
                'batch_size': 100,
                'retry_attempts': 3
            }
        }
    
    def _initialize_client(self) -> None:
        """Inicializar cliente de Google Ads"""
        if self.simulation_mode:
            logger.info("Modo simulación activado - Google Ads API no disponible")
            return
        
        try:
            # Configurar cliente de Google Ads
            if self.credentials_path and Path(self.credentials_path).exists():
                self.client = GoogleAdsClient.load_from_storage(self.credentials_path)
            else:
                # Usar configuración del archivo YAML
                config_dict = {
                    'developer_token': self.config['google_ads']['developer_token'],
                    'client_id': self.config['google_ads']['client_id'],
                    'client_secret': self.config['google_ads']['client_secret'],
                    'refresh_token': self.config['google_ads']['refresh_token'],
                    'login_customer_id': self.config['google_ads']['login_customer_id']
                }
                self.client = GoogleAdsClient.load_from_dict(config_dict)
            
            # Inicializar servicios
            self._initialize_services()
            
            logger.info("Cliente de Google Ads inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando cliente de Google Ads: {e}")
            self.simulation_mode = True
    
    def _initialize_services(self) -> None:
        """Inicializar servicios de Google Ads"""
        if not self.client:
            return
        
        try:
            self.ad_group_ad_service = self.client.get_service("AdGroupAdService")
            self.campaign_service = self.client.get_service("CampaignService")
            self.ad_group_service = self.client.get_service("AdGroupService")
            self.googleads_service = self.client.get_service("GoogleAdsService")
            self.keyword_plan_service = self.client.get_service("KeywordPlanService")
            
            logger.info("Servicios de Google Ads inicializados")
            
        except Exception as e:
            logger.error(f"Error inicializando servicios: {e}")
            self.simulation_mode = True
    
    def create_responsive_search_ad(self, request: AdCreationRequest) -> Tuple[bool, str, Optional[str]]:
        """
        Crear un anuncio de búsqueda responsivo
        
        Args:
            request: Solicitud de creación de anuncio
            
        Returns:
            Tupla (éxito, mensaje, resource_name)
        """
        if self.simulation_mode:
            return self._simulate_ad_creation(request)
        
        try:
            # Validar datos de entrada
            validation_result = self._validate_ad_request(request)
            if not validation_result[0]:
                return validation_result
            
            # Construir el anuncio
            ad_group_ad_operation = self._build_responsive_search_ad(request)
            
            # Crear el anuncio
            response = self.ad_group_ad_service.mutate_ad_group_ads(
                customer_id=request.customer_id,
                operations=[ad_group_ad_operation]
            )
            
            resource_name = response.results[0].resource_name
            
            # Actualizar cache
            self._update_ad_cache(request.customer_id, resource_name)
            
            logger.info(f"Anuncio creado exitosamente: {resource_name}")
            return True, "Anuncio creado exitosamente", resource_name
            
        except GoogleAdsException as ex:
            error_msg = f"Error de Google Ads: {ex.error.code().name}"
            logger.error(error_msg)
            return False, error_msg, None
            
        except Exception as e:
            error_msg = f"Error creando anuncio: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def _validate_ad_request(self, request: AdCreationRequest) -> Tuple[bool, str]:
        """Validar solicitud de creación de anuncio"""
        # Validar headlines
        if not request.headlines or len(request.headlines) < 3:
            return False, "Se requieren al menos 3 headlines"
        
        if len(request.headlines) > 15:
            return False, "Máximo 15 headlines permitidos"
        
        # Validar descriptions
        if not request.descriptions or len(request.descriptions) < 2:
            return False, "Se requieren al menos 2 descriptions"
        
        if len(request.descriptions) > 4:
            return False, "Máximo 4 descriptions permitidas"
        
        # Validar URLs
        if not request.final_urls:
            return False, "Se requiere al menos una URL final"
        
        # Validar longitudes
        for headline in request.headlines:
            if len(headline) > 30:
                return False, f"Headline muy largo: '{headline}' (máximo 30 caracteres)"
        
        for description in request.descriptions:
            if len(description) > 90:
                return False, f"Description muy larga: '{description}' (máximo 90 caracteres)"
        
        return True, "Validación exitosa"
    
    def _build_responsive_search_ad(self, request: AdCreationRequest):
        """Construir anuncio de búsqueda responsivo"""
        # Crear headlines
        headlines = []
        for headline_text in request.headlines:
            headline = self.client.get_type("AdTextAsset")
            headline.text = headline_text
            headlines.append(headline)
        
        # Crear descriptions
        descriptions = []
        for description_text in request.descriptions:
            description = self.client.get_type("AdTextAsset")
            description.text = description_text
            descriptions.append(description)
        
        # Crear anuncio responsivo
        responsive_search_ad = self.client.get_type("ResponsiveSearchAdInfo")
        responsive_search_ad.headlines.extend(headlines)
        responsive_search_ad.descriptions.extend(descriptions)
        
        # Configurar paths si están disponibles
        if request.path1:
            responsive_search_ad.path1 = request.path1
        if request.path2:
            responsive_search_ad.path2 = request.path2
        
        # Crear el anuncio
        ad = self.client.get_type("Ad")
        ad.responsive_search_ad.CopyFrom(responsive_search_ad)
        ad.final_urls.extend(request.final_urls)
        
        # Crear operación de grupo de anuncios
        ad_group_ad = self.client.get_type("AdGroupAd")
        ad_group_ad.ad_group = self.client.get_service("AdGroupService").ad_group_path(
            request.customer_id, request.ad_group_id
        )
        ad_group_ad.ad.CopyFrom(ad)
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED
        
        # Crear operación
        operation = self.client.get_type("AdGroupAdOperation")
        operation.create.CopyFrom(ad_group_ad)
        
        return operation
    
    def _simulate_ad_creation(self, request: AdCreationRequest) -> Tuple[bool, str, Optional[str]]:
        """Simular creación de anuncio"""
        # Validar datos
        validation_result = self._validate_ad_request(request)
        if not validation_result[0]:
            return validation_result[0], validation_result[1], None
        
        # Simular resource name
        resource_name = f"customers/{request.customer_id}/adGroupAds/{request.ad_group_id}~{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"[SIMULACIÓN] Anuncio creado: {resource_name}")
        return True, "Anuncio creado exitosamente (simulación)", resource_name
    
    def get_campaigns(self, customer_id: str, force_refresh: bool = False) -> List[Campaign]:
        """
        Obtener campañas del cliente
        
        Args:
            customer_id: ID del cliente
            force_refresh: Forzar actualización del cache
            
        Returns:
            Lista de campañas
        """
        cache_key = f"campaigns_{customer_id}"
        
        # Verificar cache
        if not force_refresh and cache_key in self.cache['campaigns']:
            cached_data = self.cache['campaigns'][cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(minutes=30):
                return cached_data['data']
        
        if self.simulation_mode:
            return self._simulate_get_campaigns(customer_id)
        
        try:
            query = """
                SELECT 
                    campaign.resource_name,
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign_budget.amount_micros
                FROM campaign
                WHERE campaign.status != 'REMOVED'
                ORDER BY campaign.name
            """
            
            response = self.googleads_service.search(
                customer_id=customer_id,
                query=query
            )
            
            campaigns = []
            for row in response:
                campaign = Campaign(
                    resource_name=row.campaign.resource_name,
                    campaign_id=str(row.campaign.id),
                    name=row.campaign.name,
                    status=CampaignStatus(row.campaign.status.name),
                    budget_amount=row.campaign_budget.amount_micros / 1_000_000
                )
                campaigns.append(campaign)
            
            # Actualizar cache
            self.cache['campaigns'][cache_key] = {
                'data': campaigns,
                'timestamp': datetime.now()
            }
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Error obteniendo campañas: {e}")
            return []
    
    def _simulate_get_campaigns(self, customer_id: str) -> List[Campaign]:
        """Simular obtención de campañas"""
        return [
            Campaign(
                resource_name=f"customers/{customer_id}/campaigns/1001",
                campaign_id="1001",
                name="Campaña Esotérica - Amarres de Amor",
                status=CampaignStatus.ENABLED,
                budget_amount=1000.0
            ),
            Campaign(
                resource_name=f"customers/{customer_id}/campaigns/1002",
                campaign_id="1002",
                name="Campaña Esotérica - Tarot y Videncia",
                status=CampaignStatus.ENABLED,
                budget_amount=800.0
            )
        ]
    
    def get_ad_groups(self, customer_id: str, campaign_id: Optional[str] = None) -> List[AdGroup]:
        """
        Obtener grupos de anuncios
        
        Args:
            customer_id: ID del cliente
            campaign_id: ID de campaña específica (opcional)
            
        Returns:
            Lista de grupos de anuncios
        """
        if self.simulation_mode:
            return self._simulate_get_ad_groups(customer_id, campaign_id)
        
        try:
            query = """
                SELECT 
                    ad_group.resource_name,
                    ad_group.id,
                    ad_group.campaign,
                    ad_group.name,
                    ad_group.status,
                    ad_group.cpc_bid_micros
                FROM ad_group
                WHERE ad_group.status != 'REMOVED'
            """
            
            if campaign_id:
                query += f" AND ad_group.campaign = 'customers/{customer_id}/campaigns/{campaign_id}'"
            
            query += " ORDER BY ad_group.name"
            
            response = self.googleads_service.search(
                customer_id=customer_id,
                query=query
            )
            
            ad_groups = []
            for row in response:
                campaign_id_extracted = row.ad_group.campaign.split('/')[-1]
                cpc_bid = row.ad_group.cpc_bid_micros / 1_000_000 if row.ad_group.cpc_bid_micros else None
                
                ad_group = AdGroup(
                    resource_name=row.ad_group.resource_name,
                    ad_group_id=str(row.ad_group.id),
                    campaign_id=campaign_id_extracted,
                    name=row.ad_group.name,
                    status=row.ad_group.status.name,
                    cpc_bid=cpc_bid
                )
                ad_groups.append(ad_group)
            
            return ad_groups
            
        except Exception as e:
            logger.error(f"Error obteniendo grupos de anuncios: {e}")
            return []
    
    def _simulate_get_ad_groups(self, customer_id: str, campaign_id: Optional[str] = None) -> List[AdGroup]:
        """Simular obtención de grupos de anuncios"""
        return [
            AdGroup(
                resource_name=f"customers/{customer_id}/adGroups/2001",
                ad_group_id="2001",
                campaign_id="1001",
                name="Amarres de Amor - México",
                status="ENABLED",
                cpc_bid=1.50
            ),
            AdGroup(
                resource_name=f"customers/{customer_id}/adGroups/2002",
                ad_group_id="2002",
                campaign_id="1002",
                name="Tarot Online - España",
                status="ENABLED",
                cpc_bid=1.80
            )
        ]
    
    def get_ads(self, customer_id: str, ad_group_id: Optional[str] = None) -> List[AdGroupAd]:
        """
        Obtener anuncios
        
        Args:
            customer_id: ID del cliente
            ad_group_id: ID del grupo de anuncios (opcional)
            
        Returns:
            Lista de anuncios
        """
        if self.simulation_mode:
            return self._simulate_get_ads(customer_id, ad_group_id)
        
        try:
            query = """
                SELECT 
                    ad_group_ad.resource_name,
                    ad_group_ad.ad.id,
                    ad_group_ad.ad_group,
                    ad_group_ad.status,
                    ad_group_ad.ad.responsive_search_ad.headlines,
                    ad_group_ad.ad.responsive_search_ad.descriptions,
                    ad_group_ad.ad.final_urls
                FROM ad_group_ad
                WHERE ad_group_ad.status != 'REMOVED'
                AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
            """
            
            if ad_group_id:
                query += f" AND ad_group_ad.ad_group = 'customers/{customer_id}/adGroups/{ad_group_id}'"
            
            response = self.googleads_service.search(
                customer_id=customer_id,
                query=query
            )
            
            ads = []
            for row in response:
                ad_group_resource = row.ad_group_ad.ad_group
                ad_group_id_extracted = ad_group_resource.split('/')[-1]
                campaign_id_extracted = "unknown"  # Necesitaríamos otra consulta para obtener esto
                
                # Extraer headlines
                headlines = [asset.text for asset in row.ad_group_ad.ad.responsive_search_ad.headlines]
                
                # Extraer descriptions
                descriptions = [asset.text for asset in row.ad_group_ad.ad.responsive_search_ad.descriptions]
                
                # Extraer URLs
                final_urls = list(row.ad_group_ad.ad.final_urls)
                
                ad = AdGroupAd(
                    resource_name=row.ad_group_ad.resource_name,
                    ad_id=str(row.ad_group_ad.ad.id),
                    ad_group_id=ad_group_id_extracted,
                    campaign_id=campaign_id_extracted,
                    status=AdStatus(row.ad_group_ad.status.name),
                    headlines=headlines,
                    descriptions=descriptions,
                    final_urls=final_urls
                )
                ads.append(ad)
            
            return ads
            
        except Exception as e:
            logger.error(f"Error obteniendo anuncios: {e}")
            return []
    
    def _simulate_get_ads(self, customer_id: str, ad_group_id: Optional[str] = None) -> List[AdGroupAd]:
        """Simular obtención de anuncios"""
        return [
            AdGroupAd(
                resource_name=f"customers/{customer_id}/adGroupAds/2001~3001",
                ad_id="3001",
                ad_group_id="2001",
                campaign_id="1001",
                status=AdStatus.ENABLED,
                headlines=["Amarres de Amor Efectivos", "Magia Blanca Poderosa", "Resultados en 24 Horas"],
                descriptions=["Maestra con 15 años de experiencia", "Consulta gratis por WhatsApp"],
                final_urls=["https://example.com/amarres-amor"]
            )
        ]
    
    def get_ad_performance(self, customer_id: str, ad_id: str, 
                          date_range: Tuple[str, str] = None) -> Optional[AdPerformanceMetrics]:
        """
        Obtener métricas de rendimiento de un anuncio
        
        Args:
            customer_id: ID del cliente
            ad_id: ID del anuncio
            date_range: Rango de fechas (inicio, fin) en formato YYYY-MM-DD
            
        Returns:
            Métricas de rendimiento
        """
        if self.simulation_mode:
            return self._simulate_get_ad_performance(ad_id)
        
        try:
            # Configurar rango de fechas
            if not date_range:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                date_range = (start_date, end_date)
            
            query = f"""
                SELECT 
                    ad_group_ad.ad.id,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.conversions,
                    metrics.cost_micros,
                    metrics.ctr,
                    metrics.conversions_per_click,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM ad_group_ad
                WHERE ad_group_ad.ad.id = {ad_id}
                AND segments.date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
            """
            
            response = self.googleads_service.search(
                customer_id=customer_id,
                query=query
            )
            
            # Agregar métricas
            total_impressions = 0
            total_clicks = 0
            total_conversions = 0.0
            total_cost = 0.0
            
            for row in response:
                total_impressions += row.metrics.impressions
                total_clicks += row.metrics.clicks
                total_conversions += row.metrics.conversions
                total_cost += row.metrics.cost_micros / 1_000_000
            
            if total_impressions == 0:
                return None
            
            ctr = (total_clicks / total_impressions) * 100
            conversion_rate = (total_conversions / total_clicks) * 100 if total_clicks > 0 else 0
            cpc = total_cost / total_clicks if total_clicks > 0 else 0
            cpa = total_cost / total_conversions if total_conversions > 0 else 0
            
            return AdPerformanceMetrics(
                ad_id=ad_id,
                impressions=total_impressions,
                clicks=total_clicks,
                conversions=total_conversions,
                cost=total_cost,
                ctr=ctr,
                conversion_rate=conversion_rate,
                cpc=cpc,
                cpa=cpa
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de rendimiento: {e}")
            return None
    
    def _simulate_get_ad_performance(self, ad_id: str) -> AdPerformanceMetrics:
        """Simular métricas de rendimiento"""
        import random
        
        impressions = random.randint(1000, 10000)
        clicks = random.randint(20, 300)
        conversions = random.uniform(1, 25)
        cost = random.uniform(50, 500)
        
        return AdPerformanceMetrics(
            ad_id=ad_id,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            cost=cost,
            ctr=(clicks / impressions) * 100,
            conversion_rate=(conversions / clicks) * 100,
            cpc=cost / clicks,
            cpa=cost / conversions
        )
    
    def pause_ad(self, customer_id: str, ad_resource_name: str) -> Tuple[bool, str]:
        """
        Pausar un anuncio
        
        Args:
            customer_id: ID del cliente
            ad_resource_name: Resource name del anuncio
            
        Returns:
            Tupla (éxito, mensaje)
        """
        if self.simulation_mode:
            logger.info(f"[SIMULACIÓN] Anuncio pausado: {ad_resource_name}")
            return True, "Anuncio pausado exitosamente (simulación)"
        
        try:
            # Crear operación de actualización
            operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = operation.update
            ad_group_ad.resource_name = ad_resource_name
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.PAUSED
            
            # Configurar field mask
            operation.update_mask.CopyFrom(
                field_mask_pb2.FieldMask(paths=["status"])
            )
            
            # Ejecutar operación
            response = self.ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=[operation]
            )
            
            logger.info(f"Anuncio pausado exitosamente: {ad_resource_name}")
            return True, "Anuncio pausado exitosamente"
            
        except Exception as e:
            error_msg = f"Error pausando anuncio: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def enable_ad(self, customer_id: str, ad_resource_name: str) -> Tuple[bool, str]:
        """
        Activar un anuncio
        
        Args:
            customer_id: ID del cliente
            ad_resource_name: Resource name del anuncio
            
        Returns:
            Tupla (éxito, mensaje)
        """
        if self.simulation_mode:
            logger.info(f"[SIMULACIÓN] Anuncio activado: {ad_resource_name}")
            return True, "Anuncio activado exitosamente (simulación)"
        
        try:
            # Crear operación de actualización
            operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = operation.update
            ad_group_ad.resource_name = ad_resource_name
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED
            
            # Configurar field mask
            operation.update_mask.CopyFrom(
                field_mask_pb2.FieldMask(paths=["status"])
            )
            
            # Ejecutar operación
            response = self.ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=[operation]
            )
            
            logger.info(f"Anuncio activado exitosamente: {ad_resource_name}")
            return True, "Anuncio activado exitosamente"
            
        except Exception as e:
            error_msg = f"Error activando anuncio: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def batch_create_ads(self, requests: List[AdCreationRequest]) -> Dict[str, Any]:
        """
        Crear múltiples anuncios en lote
        
        Args:
            requests: Lista de solicitudes de creación
            
        Returns:
            Resultados del lote
        """
        results = {
            'successful': [],
            'failed': [],
            'total': len(requests),
            'success_count': 0,
            'error_count': 0
        }
        
        for request in requests:
            success, message, resource_name = self.create_responsive_search_ad(request)
            
            if success:
                results['successful'].append({
                    'ad_group_id': request.ad_group_id,
                    'resource_name': resource_name,
                    'message': message
                })
                results['success_count'] += 1
            else:
                results['failed'].append({
                    'ad_group_id': request.ad_group_id,
                    'error': message
                })
                results['error_count'] += 1
        
        logger.info(f"Lote completado: {results['success_count']} éxitos, {results['error_count']} errores")
        return results
    
    def _update_ad_cache(self, customer_id: str, resource_name: str) -> None:
        """Actualizar cache de anuncios"""
        # Invalidar cache relacionado
        cache_keys_to_remove = [
            key for key in self.cache['ads'].keys() 
            if customer_id in key
        ]
        
        for key in cache_keys_to_remove:
            del self.cache['ads'][key]
    
    def get_account_info(self, customer_id: str) -> Dict[str, Any]:
        """
        Obtener información de la cuenta
        
        Args:
            customer_id: ID del cliente
            
        Returns:
            Información de la cuenta
        """
        if self.simulation_mode:
            return {
                'customer_id': customer_id,
                'descriptive_name': 'Cuenta Esotérica Demo',
                'currency_code': 'USD',
                'time_zone': 'America/Mexico_City',
                'simulation_mode': True
            }
        
        try:
            query = """
                SELECT 
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone
                FROM customer
                LIMIT 1
            """
            
            response = self.googleads_service.search(
                customer_id=customer_id,
                query=query
            )
            
            for row in response:
                return {
                    'customer_id': str(row.customer.id),
                    'descriptive_name': row.customer.descriptive_name,
                    'currency_code': row.customer.currency_code,
                    'time_zone': row.customer.time_zone,
                    'simulation_mode': False
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo información de cuenta: {e}")
            return {}

# Función de utilidad para crear servicio rápidamente
def create_google_ads_service(config_path: Optional[str] = None, 
                             credentials_path: Optional[str] = None) -> EsotericGoogleAdsService:
    """
    Crear servicio de Google Ads
    
    Args:
        config_path: Ruta al archivo de configuración
        credentials_path: Ruta a las credenciales
        
    Returns:
        Servicio de Google Ads
    """
    return EsotericGoogleAdsService(config_path, credentials_path)

if __name__ == "__main__":
    # Ejemplo de uso
    service = EsotericGoogleAdsService()
    
    # Obtener información de cuenta
    account_info = service.get_account_info("1234567890")
    print("=" * 60)
    print("🔗 INFORMACIÓN DE CUENTA")
    print("=" * 60)
    print(f"Customer ID: {account_info.get('customer_id', 'N/A')}")
    print(f"Nombre: {account_info.get('descriptive_name', 'N/A')}")
    print(f"Moneda: {account_info.get('currency_code', 'N/A')}")
    print(f"Zona Horaria: {account_info.get('time_zone', 'N/A')}")
    print(f"Modo Simulación: {account_info.get('simulation_mode', True)}")
    
    # Obtener campañas
    campaigns = service.get_campaigns("1234567890")
    print(f"\n📊 CAMPAÑAS ({len(campaigns)}):")
    for campaign in campaigns:
        print(f"- {campaign.name} (ID: {campaign.campaign_id}) - {campaign.status.value}")
    
    # Ejemplo de creación de anuncio
    ad_request = AdCreationRequest(
        customer_id="1234567890",
        ad_group_id="2001",
        headlines=[
            "Amarres de Amor Efectivos",
            "Magia Blanca Poderosa",
            "Resultados en 24 Horas"
        ],
        descriptions=[
            "Maestra con 15 años de experiencia en amarres de amor",
            "Consulta gratis por WhatsApp. Testimonios reales"
        ],
        final_urls=["https://example.com/amarres-amor"]
    )
    
    success, message, resource_name = service.create_responsive_search_ad(ad_request)
    print(f"\n📝 CREACIÓN DE ANUNCIO:")
    print(f"Éxito: {success}")
    print(f"Mensaje: {message}")
    if resource_name:
        print(f"Resource Name: {resource_name}")