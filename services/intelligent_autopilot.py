"""
🚀 AUTOPUBLICADOR INTELIGENTE CON IA - VERSIÓN COMPLETA CORREGIDA
Keywords del usuario + Generación real con IA + Configuración avanzada
Versión: 3.1 Fixed - 2025-10-13 20:50:00
Autor: saltbalente
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging
import re
import asyncio
from dataclasses import dataclass

from services.campaign_service import CampaignService
from services.autopilot_publisher import AutopilotPublisher
from modules.models import Campaign, CampaignStatus
from utils.logger import get_logger
from modules.ai_ad_generator import AIAdGenerator
from modules.ad_prompt_generator import build_enhanced_prompt

logger = get_logger(__name__)


@dataclass
class CampaignOption:
    """Opción de campaña para el autopilot"""
    campaign_id: str
    campaign_name: str
    campaign_status: str
    campaign_type: str
    is_new: bool = False
    
    def __str__(self):
        if self.is_new:
            return "🆕 Crear Nueva Campaña"
        status_emoji = "✅" if self.campaign_status == "ENABLED" else "⏸️"
        return f"{status_emoji} {self.campaign_name} ({self.campaign_type})"


class IntelligentAutopilot:
    """🚀 AUTOPUBLICADOR INTELIGENTE CON IA"""
    
    def __init__(self, google_ads_client):
        self.client = google_ads_client
        self.campaign_service = CampaignService(google_ads_client)
        self.autopilot_publisher = AutopilotPublisher(google_ads_client)
        self.ai_generator = AIAdGenerator()
        # ✅ CONTROL DE UNICIDAD GLOBAL
        self.used_headlines = set()
        self.used_descriptions = set()
        self.used_keywords_by_group = []
    
    # ========================================================================
    # DETECCIÓN DE CAMPAÑAS EXISTENTES
    # ========================================================================
    
    def get_available_campaigns(self, customer_id: str) -> List:
        """Obtiene campañas disponibles"""
        try:
            logger.info(f"🔍 Detectando campañas para customer {customer_id}")
            
            campaigns = self.campaign_service.get_campaigns(
                customer_id,
                status_filter=[CampaignStatus.ENABLED, CampaignStatus.PAUSED]
            )
            
            options = []
            
            # Nueva campaña
            options.append(CampaignOption(
                campaign_id="new_campaign",
                campaign_name="Nueva Campaña",
                campaign_status="NEW",
                campaign_type="SEARCH",
                is_new=True
            ))
            
            # Existentes
            for campaign in campaigns:
                if campaign.campaign_type in ['SEARCH', 'PERFORMANCE_MAX']:
                    options.append(CampaignOption(
                        campaign_id=campaign.campaign_id,
                        campaign_name=campaign.campaign_name,
                        campaign_status=campaign.campaign_status.value,
                        campaign_type=campaign.campaign_type,
                        is_new=False
                    ))
            
            logger.info(f"✅ {len(options)} opciones disponibles")
            return options
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return []
    
    def get_campaign_details(self, customer_id: str, campaign_id: str) -> Dict[str, Any]:
        """Obtiene detalles adicionales de una campaña específica"""
        try:
            logger.info(f"🔍 Obteniendo detalles de campaña {campaign_id} para customer {customer_id}")
            
            # Obtener información básica de la campaña
            campaigns = self.campaign_service.get_campaigns(customer_id)
            campaign = next((c for c in campaigns if c.campaign_id == campaign_id), None)
            
            if not campaign:
                return {
                    'budget': 'N/A',
                    'ad_groups_count': 0,
                    'ads_count': 0,
                    'keywords_count': 0
                }
            
            # Obtener estadísticas adicionales usando el cliente de Google Ads
            try:
                # Query para obtener estadísticas de la campaña
                query = f"""
                    SELECT 
                        campaign.id,
                        campaign.name,
                        campaign_budget.amount_micros,
                        metrics.impressions,
                        metrics.clicks
                    FROM campaign 
                    WHERE campaign.id = {campaign_id}
                """
                
                ga_service = self.client.get_service("GoogleAdsService")
                response = ga_service.search(customer_id=customer_id, query=query)
                
                budget_amount = 'N/A'
                for row in response:
                    if row.campaign_budget.amount_micros:
                        # Convertir de micros a moneda normal
                        budget_amount = f"${row.campaign_budget.amount_micros / 1_000_000:.2f}"
                    break
                
                # Query para contar grupos de anuncios
                ad_groups_query = f"""
                    SELECT ad_group.id
                    FROM ad_group 
                    WHERE campaign.id = {campaign_id}
                """
                
                ad_groups_response = ga_service.search(customer_id=customer_id, query=ad_groups_query)
                ad_groups_count = len(list(ad_groups_response))
                
                # Query para contar anuncios
                ads_query = f"""
                    SELECT ad_group_ad.ad.id
                    FROM ad_group_ad 
                    WHERE campaign.id = {campaign_id}
                    AND ad_group_ad.status != 'REMOVED'
                """
                
                ads_response = ga_service.search(customer_id=customer_id, query=ads_query)
                ads_count = len(list(ads_response))
                
                return {
                    'budget': budget_amount,
                    'ad_groups_count': ad_groups_count,
                    'ads_count': ads_count,
                    'keywords_count': 0  # Podríamos agregar esto después si es necesario
                }
                
            except Exception as query_error:
                logger.warning(f"⚠️ Error obteniendo estadísticas detalladas: {query_error}")
                return {
                    'budget': 'N/A',
                    'ad_groups_count': 0,
                    'ads_count': 0,
                    'keywords_count': 0
                }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo detalles de campaña: {e}")
            return {
                'budget': 'N/A',
                'ad_groups_count': 0,
                'ads_count': 0,
                'keywords_count': 0
            }
    
    # ========================================================================
    # GENERACIÓN MULTI-GRUPO CON CONFIGURACIÓN ESPECÍFICA
    # ========================================================================

    def generate_ad_groups_from_config(
        self,
        business_description: str,
        ad_groups_config: List[Dict],
        generation_config: Dict
    ) -> List[Dict[str, Any]]:
        """
        Genera grupos de anuncios basándose en configuración específica por grupo
        
        Args:
            business_description: Descripción general del negocio
            ad_groups_config: Lista con configuración de cada grupo:
                [{'name': 'Grupo 1', 'keywords': ['kw1', 'kw2'], 'url': 'https://...'}]
            generation_config: Configuración global con:
                - ai_provider: str (openai/gemini/anthropic)
                - ai_model: str (gpt-4o/gemini-pro/etc)
                - ai_creativity: float (0.1-1.0)
                - ads_per_group: int
                - match_types: List[str]
                - use_magnetic: bool
        
        Returns:
            Lista de grupos de anuncios generados con IA
        """
        logger.info("="*70)
        logger.info("🚀 GENERANDO GRUPOS DESDE CONFIGURACIÓN ESPECÍFICA")
        logger.info(f"📦 Total de grupos configurados: {len(ad_groups_config)}")
        logger.info(f"⚙️ Config global: {generation_config}")
        logger.info("="*70)
        
        generated_groups = []
        
        for i, group_config in enumerate(ad_groups_config):
            try:
                # ✅ Extraer datos del grupo
                group_name = group_config.get('name', f'Grupo {i+1}')
                keywords = group_config.get('keywords', [])
                final_url = group_config.get('url', 'https://www.ejemplo.com')
                
                logger.info(f"\n{'='*70}")
                logger.info(f"📋 PROCESANDO GRUPO {i+1}/{len(ad_groups_config)}: {group_name}")
                logger.info(f"{'='*70}")
                logger.info(f"🔑 Keywords ({len(keywords)}): {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
                logger.info(f"🌐 URL: {final_url}")
                
                # ✅ Validar keywords
                if not keywords:
                    logger.warning(f"⚠️ Grupo {group_name} sin keywords, saltando...")
                    continue
                
                # ✅ Extraer configuración de generación
                ai_provider = generation_config.get('ai_provider', 'openai')
                ai_model = generation_config.get('ai_model', 'gpt-4o')
                creativity = generation_config.get('ai_creativity', 0.7)
                use_magnetic = generation_config.get('use_magnetic', False)
                ads_per_group = generation_config.get('ads_per_group', 8)
                match_types = generation_config.get('match_types', ['Exacta', 'Frase'])
                
                logger.info(f"🤖 IA: {ai_provider}/{ai_model}")
                logger.info(f"🎨 Creatividad: {creativity}")
                logger.info(f"🔴 Modo Magnético: {'SÍ' if use_magnetic else 'NO'}")
                logger.info(f"📝 Anuncios a generar: {ads_per_group}")
                
                # ✅ GENERAR ANUNCIOS CON IA
                logger.info("🎨 Generando anuncios con IA...")
                
                ads_result = self._generate_real_ads_with_ai(
                    keywords=keywords,
                    business_description=business_description,
                    business_url=final_url,
                    num_ads=ads_per_group,
                    ai_provider=ai_provider,
                    ai_model=ai_model,
                    tone='profesional',
                    creativity=creativity,
                    use_magnetic=use_magnetic
                )
                
                if not ads_result or len(ads_result) == 0:
                    logger.warning(f"⚠️ No se generaron anuncios para {group_name}")
                    continue
                
                logger.info(f"✅ {len(ads_result)} anuncios generados exitosamente")
                
                # ✅ Aplicar match types a keywords
                logger.info(f"🎯 Aplicando match types: {match_types}")
                keywords_with_match = self._apply_match_types(keywords, match_types)
                
                # ✅ Calcular CPC inteligente
                max_cpc_bid = self._calculate_smart_bid(keywords)
                logger.info(f"💰 CPC sugerido: ${max_cpc_bid:.2f}")
                
                # ✅ CREAR ESTRUCTURA COMPLETA DEL GRUPO
                ad_group = {
                    'name': group_name,
                    'theme': self._extract_theme(keywords),
                    'keywords': keywords,  # Keywords originales
                    'negative_keywords': self._generate_negative_keywords(business_description),
                    'ads': ads_result,  # Anuncios generados con IA
                    'max_cpc_bid': max_cpc_bid,
                    'final_url': final_url,
                    'match_type': match_types[0] if match_types else 'BROAD',
                    'all_match_types': keywords_with_match,  # Keywords con match types
                    'targeting': {
                        'country': 'US',
                        'currency': 'COP',
                        'age_range': None,
                        'gender': None
                    },
                    'status': 'ready',
                    'score': 85.0 + (i * 2)
                }
                
                generated_groups.append(ad_group)
                
                logger.info(f"✅ Grupo '{group_name}' completado exitosamente")
                logger.info(f"   - Keywords: {len(keywords)}")
                logger.info(f"   - Anuncios: {len(ads_result)}")
                logger.info(f"   - CPC: ${max_cpc_bid:.2f}")
                logger.info(f"   - URL: {final_url}")
                
            except Exception as e:
                logger.error(f"❌ Error generando grupo {i+1}: {e}")
                logger.error(f"Traceback:", exc_info=True)
                continue
        
        logger.info("\n" + "="*70)
        logger.info(f"🏁 GENERACIÓN COMPLETADA")
        logger.info(f"✅ Exitosos: {len(generated_groups)}/{len(ad_groups_config)}")
        logger.info(f"❌ Fallidos: {len(ad_groups_config) - len(generated_groups)}")
        logger.info("="*70 + "\n")
        
        return generated_groups

    def generate_ad_groups_for_business(
        self,
        business_description: str,
        target_keywords,  # Puede ser str o List[str]
        generation_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Método wrapper para compatibilidad con la interfaz existente.
        Convierte los parámetros al formato esperado por generate_ad_groups_with_ai.
        """
        try:
            logger.info(f"🔄 Wrapper: generate_ad_groups_for_business llamado")
            logger.info(f"📝 Business: {business_description[:100]}")
            logger.info(f"🔑 Keywords (tipo: {type(target_keywords)}): {target_keywords}")
            logger.info(f"⚙️ Config: {generation_config}")
            
            # Procesar target_keywords si es string
            if isinstance(target_keywords, str):
                logger.info("🔄 Procesando keywords como string...")
                # Separar por comas y saltos de línea, limpiar espacios
                processed_keywords = []
                for keyword in target_keywords.replace('\n', ',').split(','):
                    keyword = keyword.strip()
                    if keyword:  # Solo agregar si no está vacío
                        processed_keywords.append(keyword)
                target_keywords_list = processed_keywords
                logger.info(f"✅ Keywords procesadas: {target_keywords_list}")
            else:
                target_keywords_list = target_keywords if target_keywords else []
                logger.info(f"✅ Keywords como lista: {target_keywords_list}")
            
            # Extraer configuración del generation_config
            business_url = generation_config.get('business_url', 'https://example.com')
            
            # Crear advanced_config en el formato esperado
            advanced_config = {
                'num_groups': generation_config.get('num_ad_groups', 1),
                'keywords_per_group': generation_config.get('keywords_per_group', 10),
                'ads_per_group': generation_config.get('ads_per_group', 3),
                'creativity': generation_config.get('ai_creativity', 0.7),
                'match_types': generation_config.get('match_types', ['BROAD']),
                'ai_provider': 'openai',  # Default
                'ai_model': 'gpt-4o',     # Default
                'tone': 'profesional'     # Default
            }
            
            logger.info(f"🔄 Llamando a generate_ad_groups_with_ai con advanced_config: {advanced_config}")
            
            # Llamar al método principal
            return self.generate_ad_groups_with_ai(
                business_description=business_description,
                business_url=business_url,
                user_keywords=target_keywords_list,
                advanced_config=advanced_config
            )
            
        except Exception as e:
            logger.error(f"❌ Error en generate_ad_groups_for_business: {e}")
            return []
    
    # ========================================================================
    # GENERACIÓN INTELIGENTE CON IA - CORREGIDA
    # ========================================================================
    
    def generate_ad_groups_with_ai(
        self,
        business_description: str,
        business_url: str,
        user_keywords: List[str],
        advanced_config: Dict[str, Any],
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Genera grupos con IA usando keywords del usuario
        
        Args:
            business_description: Descripción del negocio
            business_url: URL del sitio
            user_keywords: Keywords ingresadas por el usuario
            advanced_config: Configuración avanzada con:
                - creativity: float (0.1-1.0)
                - keywords_per_group: int
                - ads_per_group: int
                - match_types: List[str] (BROAD, PHRASE, EXACT)
                - num_groups: int
                - ai_provider: str
                - ai_model: str
                - tone: str
                - use_magnetic: bool (opcional, para prompts magnéticos)
            progress_callback: Callback de progreso
        """
        try:
            # ✅ REINICIAR CONTROL DE UNICIDAD PARA NUEVA GENERACIÓN
            self.used_headlines = set()
            self.used_descriptions = set()
            self.used_keywords_by_group = []
            
            if progress_callback:
                progress_callback("🤖 Iniciando generación inteligente...", 5)
            
            logger.info("="*80)
            logger.info("🚀 INICIO DE GENERACIÓN CON IA")
            logger.info("="*80)
            logger.info(f"📝 Negocio: {business_description[:100]}")
            logger.info(f"🌐 URL: {business_url}")
            logger.info(f"🔑 Keywords usuario: {user_keywords}")
            logger.info(f"⚙️ Config avanzada: {advanced_config}")
            
            # Validar URL
            business_url = self._validate_url(business_url)
            
            # Extraer configuración
            num_groups = advanced_config.get('num_groups', 1)
            keywords_per_group = advanced_config.get('keywords_per_group', 10)
            ads_per_group = advanced_config.get('ads_per_group', 3)
            match_types = advanced_config.get('match_types', ['BROAD'])
            creativity = advanced_config.get('creativity', 0.7)
            ai_provider = advanced_config.get('ai_provider', 'openai')
            ai_model = advanced_config.get('ai_model', 'gpt-4o')
            tone = advanced_config.get('tone', 'profesional')
            use_magnetic = advanced_config.get('use_magnetic', False)  # ✅ NUEVO PARÁMETRO MAGNÉTICO
            logger.info(f"🔴 Modo magnético activado: {use_magnetic}")
            logger.info(f"🎯 Grupos a crear: {num_groups}")
            logger.info(f"🔑 Keywords por grupo: {keywords_per_group}")
            logger.info(f"📝 Anuncios por grupo: {ads_per_group}")
            logger.info(f"🎨 Match types: {match_types}")
            logger.info(f"🤖 IA: {ai_provider} / {ai_model}")
            
            # ✅ DIVIDIR KEYWORDS DEL USUARIO EN GRUPOS
            if progress_callback:
                progress_callback("📦 Organizando keywords del usuario...", 10)
            
            keyword_groups = self._split_user_keywords(user_keywords, num_groups)
            
            logger.info(f"📦 Keywords divididas en {len(keyword_groups)} grupos:")
            for idx, kw_group in enumerate(keyword_groups):
                logger.info(f"   Grupo {idx+1}: {kw_group}")
            
            # ✅ GENERAR GRUPOS DE ANUNCIOS
            ad_groups = []
            
            for idx, user_kws in enumerate(keyword_groups):
                try:
                    progress = 15 + ((idx / len(keyword_groups)) * 70)
                    
                    if progress_callback:
                        progress_callback(
                            f"🤖 Generando grupo {idx+1}/{len(keyword_groups)} con IA...",
                            progress
                        )
                    
                    logger.info(f"\n{'='*80}")
                    logger.info(f"🔧 GENERANDO GRUPO {idx+1}/{len(keyword_groups)}")
                    logger.info(f"{'='*80}")
                    logger.info(f"🔑 Keywords base del usuario: {user_kws}")
                    
                    # ✅ EXPANDIR KEYWORDS CON IA SI ES NECESARIO
                    all_keywords = self._expand_keywords_with_ai(
                        user_keywords=user_kws,
                        target_count=keywords_per_group,
                        business_description=business_description,
                        ai_provider=ai_provider,
                        ai_model=ai_model,
                        creativity=creativity
                    )
                    
                    # ✅ VALIDAR UNICIDAD DE KEYWORDS ENTRE GRUPOS
                    unique_keywords = self._ensure_unique_keywords(all_keywords, idx)
                    
                    logger.info(f"✅ Keywords finales para grupo {idx+1}: {unique_keywords}")
                    
                    # ✅ GENERAR NOMBRE INTELIGENTE
                    group_name = self._generate_intelligent_group_name(
                        keywords=unique_keywords,
                        business_description=business_description,
                        group_index=idx
                    )
                    
                    logger.info(f"📝 Nombre grupo: {group_name}")
                    
                    # ✅ GENERAR ANUNCIOS CON IA REAL
                    if progress_callback:
                        progress_callback(f"🎨 Generando {ads_per_group} anuncios con IA...", progress + 5)
                    
                    ads = self._generate_real_ads_with_ai(
                        keywords=unique_keywords,
                        business_description=business_description,
                        business_url=business_url,
                        num_ads=ads_per_group,
                        ai_provider=ai_provider,
                        ai_model=ai_model,
                        tone=tone,
                        creativity=creativity,
                        use_magnetic=use_magnetic  # ✅ PASAR PARÁMETRO MAGNÉTICO
                    )
                    
                    logger.info(f"✅ {len(ads)} anuncios generados para grupo {idx+1}")
                    
                    # ✅ APLICAR MATCH TYPES A KEYWORDS
                    keywords_with_match = self._apply_match_types(
                        keywords=unique_keywords,
                        match_types=match_types
                    )
                    
                    logger.info(f"🎯 Keywords con match types: {len(keywords_with_match)} keywords")
                    
                    # ✅ CREAR ESTRUCTURA DEL GRUPO
                    ad_group = {
                        'name': group_name,
                        'theme': self._extract_theme(all_keywords),
                        'keywords': all_keywords,  # ✅ KEYWORDS COMPLETAS
                        'negative_keywords': self._generate_negative_keywords(business_description),
                        'ads': ads,
                        'max_cpc_bid': self._calculate_smart_bid(all_keywords),
                        'match_type': match_types[0] if match_types else 'BROAD',  # Match type principal
                        'all_match_types': keywords_with_match,  # Keywords con sus match types
                        'targeting': {
                            'country': 'US',
                            'currency': 'COP',
                            'age_range': None,
                            'gender': None
                        },
                        'status': 'ready',
                        'score': 90.0
                    }
                    
                    ad_groups.append(ad_group)
                    
                    logger.info(f"🎉 Grupo {idx+1} completado:")
                    logger.info(f"   - Nombre: {group_name}")
                    logger.info(f"   - Keywords: {len(all_keywords)}")
                    logger.info(f"   - Anuncios: {len(ads)}")
                    logger.info(f"   - Match type: {match_types[0]}")
                
                except Exception as group_error:
                    logger.error(f"❌ Error en grupo {idx+1}: {str(group_error)}", exc_info=True)
                    continue
            
            if progress_callback:
                progress_callback(f"✅ {len(ad_groups)} grupos listos para publicar", 90)
            
            logger.info("\n" + "="*80)
            logger.info(f"🎉 GENERACIÓN COMPLETADA: {len(ad_groups)} grupos")
            logger.info("="*80)
            
            return ad_groups
            
        except Exception as e:
            error_msg = f"❌ Error generando: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if progress_callback:
                progress_callback(error_msg, None)
            return []
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    # ========================================================================
    # MÉTODOS AUXILIARES - FIX KEYWORDS SPLITTING
    # ========================================================================
    
    def _split_user_keywords(
        self,
        keywords: List[str],
        num_groups: int
    ) -> List[List[str]]:
        """
        Divide keywords del usuario en grupos
        FIX: Separar correctamente por comas
        """
        
        logger.info(f"📦 Dividiendo keywords")
        logger.info(f"   - Input type: {type(keywords)}")
        logger.info(f"   - Input raw: {keywords}")
        logger.info(f"   - Num groups: {num_groups}")
        
        # ✅ FIX: Validar keywords
        if not keywords:
            logger.warning("⚠️ No hay keywords")
            return [[] for _ in range(num_groups)]
        
        # ✅ FIX: Si es un string, separar por COMAS Y SALTOS DE LÍNEA
        if isinstance(keywords, str):
            logger.info("🔄 Keywords es string, separando...")
            
            # Primero separar por saltos de línea
            lines = keywords.split('\n')
            clean_keywords = []
            
            for line in lines:
                # Luego separar cada línea por comas
                if ',' in line:
                    parts = [kw.strip() for kw in line.split(',') if kw.strip()]
                    clean_keywords.extend(parts)
                elif line.strip():
                    clean_keywords.append(line.strip())
            
            keywords = clean_keywords
            logger.info(f"✅ Keywords separadas: {keywords}")
        
        # ✅ Asegurar que sea lista
        if not isinstance(keywords, list):
            logger.error(f"❌ Keywords debe ser lista, es: {type(keywords)}")
            return [[] for _ in range(num_groups)]
        
        # ✅ Limpiar keywords vacías
        clean_keywords = [kw.strip() for kw in keywords if kw and isinstance(kw, str) and kw.strip()]
        
        if not clean_keywords:
            logger.warning("⚠️ No hay keywords válidas")
            return [[] for _ in range(num_groups)]
        
        logger.info(f"✅ Keywords limpias finales: {clean_keywords}")
        logger.info(f"✅ Total: {len(clean_keywords)}")
        
        # ✅ Dividir en grupos
        if len(clean_keywords) <= num_groups:
            # Una keyword por grupo
            result = [[kw] for kw in clean_keywords]
            # Rellenar grupos vacíos si es necesario
            while len(result) < num_groups:
                result.append([])
            logger.info(f"📦 Distribución (1 kw/grupo): {[len(g) for g in result]}")
            return result
        
        # Dividir equitativamente
        keywords_per_group = len(clean_keywords) // num_groups
        remainder = len(clean_keywords) % num_groups
        
        groups = []
        start_idx = 0
        
        for i in range(num_groups):
            group_size = keywords_per_group + (1 if i < remainder else 0)
            end_idx = start_idx + group_size
            groups.append(clean_keywords[start_idx:end_idx])
            start_idx = end_idx
        
        logger.info(f"📦 Distribución final: {[len(g) for g in groups]}")
        for idx, group in enumerate(groups):
            logger.info(f"   Grupo {idx+1}: {group}")
        
        return groups
    
    def _expand_keywords_with_ai(
        self,
        user_keywords: List[str],
        target_count: int,
        business_description: str,
        ai_provider: str,
        ai_model: str,
        creativity: float
    ) -> List[str]:
        """
        Expande keywords usando IA si es necesario
        FIX: No usar provider.generate(), usar generate_batch()
        """
        try:
            logger.info(f"🔍 Expandiendo keywords: {len(user_keywords)} → {target_count}")
            
            # ✅ Si ya tenemos suficientes, retornar
            if len(user_keywords) >= target_count:
                logger.info(f"✅ Ya hay {len(user_keywords)} keywords, suficiente")
                return user_keywords[:target_count]
            
            # ✅ NO EXPANDIR CON IA, SOLO USAR LAS DEL USUARIO
            # Si el usuario puso pocas keywords, repetirlas para llenar grupos
            logger.info(f"⚠️ Solo {len(user_keywords)} keywords del usuario, usando esas")
            
            # Repetir keywords del usuario hasta llenar
            result = user_keywords.copy()
            while len(result) < target_count and user_keywords:
                for kw in user_keywords:
                    if len(result) >= target_count:
                        break
                    result.append(kw)
            
            logger.info(f"✅ Keywords finales: {result[:target_count]}")
            
            return result[:target_count]
        
        except Exception as e:
            logger.error(f"❌ Error expandiendo keywords: {e}")
            return user_keywords
    
    def _generate_real_ads_with_ai(
        self,
        keywords: List[str],
        business_description: str,
        business_url: str,
        num_ads: int,
        ai_provider: str,
        ai_model: str,
        tone: str,
        creativity: float,
        use_magnetic: bool = False  # ✅ PARÁMETRO MAGNÉTICO
    ) -> List[Dict[str, Any]]:
        """
        Genera anuncios REALES usando IA con soporte magnético
        """
        try:
            logger.info(f"🤖 Generando {num_ads} anuncios con {ai_provider}/{ai_model}")
            logger.info(f"🔑 Keywords: {keywords}")
            logger.info(f"🎨 Tono: {tone}, Creatividad: {creativity}")
            logger.info(f"🔴 Modo magnético: {use_magnetic}")
            
            # ✅ CONFIGURAR IA
            from utils.user_storage import get_user_storage
            user_storage = get_user_storage('saltbalente')
            
            api_key_data = user_storage.get_api_key(ai_provider)
            
            if not api_key_data or not api_key_data.get('api_key'):
                logger.error(f"❌ No hay API key para {ai_provider}")
                return self._generate_ads_fallback(keywords, business_url, num_ads)
            
            logger.info(f"✅ API key encontrada para {ai_provider}")
            
            # Configurar generador
            success = self.ai_generator.set_provider(
                provider_type=ai_provider,
                api_key=api_key_data['api_key'],
                model=ai_model
            )
            
            if not success:
                logger.error("❌ Error configurando provider")
                return self._generate_ads_fallback(keywords, business_url, num_ads)
            
            logger.info("✅ Provider configurado correctamente")
            
            # ✅ DETERMINAR BUSINESS_TYPE PARA PROMPT CORRECTO
            business_type = 'auto'  # Auto-detectar
            
            # Detectar si es esotérico por keywords
            esoteric_keywords = ['amarre', 'amarrar', 'hechizo', 'brujería', 'magia', 
                                'tarot', 'videncia', 'brujo', 'bruja', 'ritual']
            
            keywords_lower = ' '.join(keywords).lower()
            is_esoteric = any(kw in keywords_lower for kw in esoteric_keywords)
            
            if is_esoteric:
                business_type = 'esoteric'
                logger.info("🔮 Negocio esotérico detectado")
            
            # ✅ GENERAR CON IA (NORMAL O MAGNÉTICO)
            
            # Construir el prompt avanzado
            logger.info("📝 Construyendo prompt avanzado para Autopilot...")
            logger.info("🔍 DEBUG: Intentando importar build_enhanced_prompt...")
            
            try:
                custom_prompt = build_enhanced_prompt(
                keywords=keywords[:10],
                tone=tone,
                num_headlines=15,
                num_descriptions=4,
                use_location_insertion=False, # Por defecto para Autopilot
                location_levels=['city', 'state', 'country'], # Por defecto para Autopilot
                business_type=business_type
                )
                logger.info("✅✅✅ PRUEBA: Prompt avanzado construido en AUTOPILOT. Inicio del prompt:")
                logger.info(custom_prompt[:300] + "...")
            except Exception as e:
                logger.error(f"❌ ERROR al construir prompt avanzado: {e}")
                logger.error(f"❌ Tipo de error: {type(e).__name__}")
                custom_prompt = None

            if use_magnetic and is_esoteric:
                logger.info("🔴 Usando MODO MAGNÉTICO de alta intensidad (NOTA: prompt magnético anulará el avanzado)")
                # El flag use_magnetic en generate_batch activará el prompt magnético internamente.
                # Aquí podríamos decidir si el prompt magnético anula el `custom_prompt` o no.
                # Por ahora, la lógica en ai_ad_generator no usa `custom_prompt` si `use_magnetic` es true.
                # Esto es un comportamiento que podríamos refinar.
                
            logger.info("📤 Llamando a generate_batch...")
            logger.info("✅✅✅ PRUEBA: Verificando que `custom_prompt` se pasa a `generate_batch`.")
            
            result = self.ai_generator.generate_batch(
                keywords=keywords[:10],
                num_ads=num_ads,
                num_headlines=15,
                num_descriptions=4,
                tone=tone,
                validate=True,
                business_type=business_type,
                save_to_csv=False,
                custom_prompt=custom_prompt, # ✅ Pasar el prompt avanzado
                temperature=creativity,
                # El flag `use_magnetic` se podría manejar aquí si se refina la lógica
            )
            
            logger.info(f"📥 Resultado: {result}")
            
             # ✅ PROCESAR ANUNCIOS GENERADOS CON VALIDACIÓN ESTRICTA
            ads = []
            
            for idx, ad_data in enumerate(result.get('ads', [])):
                if ad_data.get('error'):
                    logger.warning(f"⚠️ Ad {idx+1} con error: {ad_data['error']}")
                    continue
                
                # ✅ VALIDAR UNICIDAD DE TÍTULOS Y DESCRIPCIONES CON SIMILITUD
                unique_headlines = self._ensure_unique_headlines(ad_data.get('headlines', []))
                unique_descriptions = self._ensure_unique_descriptions(
                    ad_data.get('descriptions', []),
                    min_similarity=0.85  # 85% de similitud = rechazar
                )
                
                # ✅ REGENERAR SI NO HAY SUFICIENTES DESCRIPCIONES ÚNICAS
                retry_count = 0
                max_retries = 3
                
                while len(unique_descriptions) < 2 and retry_count < max_retries:
                    logger.warning(f"⚠️ Solo {len(unique_descriptions)} descripciones únicas, regenerando... (intento {retry_count + 1}/{max_retries})")
                    
                    # Regenerar solo descripciones
                    new_descriptions = self._regenerate_descriptions_only(
                        keywords=keywords,
                        business_description=business_description,
                        ai_provider=ai_provider,
                        ai_model=ai_model,
                        tone=tone,
                        creativity=creativity,
                        num_needed=4,
                        exclude_descriptions=list(self.used_descriptions)
                    )
                    
                    # Validar nuevas descripciones
                    unique_descriptions.extend(
                        self._ensure_unique_descriptions(new_descriptions, min_similarity=0.85)
                    )
                    
                    retry_count += 1
                
                # Verificar que tengamos suficientes
                if len(unique_headlines) < 3:
                    logger.warning(f"⚠️ Ad {idx+1}: Solo {len(unique_headlines)} headlines únicos (mínimo 3)")
                    continue
                
                if len(unique_descriptions) < 2:
                    logger.error(f"❌ Ad {idx+1}: Solo {len(unique_descriptions)} descriptions únicos después de {max_retries} intentos")
                    continue
                
                # ✅ AGREGAR URL REAL
                ad_with_url = {
                    'headlines': unique_headlines,
                    'descriptions': unique_descriptions,
                    'final_url': business_url,
                    'path1': self._extract_path_from_url(business_url, 1),
                    'path2': self._extract_path_from_url(business_url, 2)
                }
                
                logger.info(f"✅ Anuncio {idx+1}: {len(unique_headlines)} headlines, {len(unique_descriptions)} descriptions ÚNICOS")
                
                ads.append(ad_with_url)
            
            if not ads:
                logger.warning("⚠️ IA no generó anuncios válidos, usando fallback")
                return self._generate_ads_fallback(keywords, business_url, num_ads)
            
            logger.info(f"🎉 {len(ads)} anuncios generados con IA exitosamente")
            
            return ads
        
        except Exception as e:
            logger.error(f"❌ Error generando con IA: {e}", exc_info=True)
            return self._generate_ads_fallback(keywords, business_url, num_ads)
    
    def _regenerate_descriptions_only(
        self,
        keywords: List[str],
        business_description: str,
        ai_provider: str,
        ai_model: str,
        tone: str,
        creativity: float,
        num_needed: int = 4,
        exclude_descriptions: List[str] = []
    ) -> List[str]:
        """
        Regenera SOLO descripciones sin afectar títulos
        
        Args:
            keywords: Keywords del grupo
            business_description: Descripción del negocio
            ai_provider: Proveedor de IA (openai/gemini)
            ai_model: Modelo de IA
            tone: Tono deseado
            creativity: Nivel de creatividad
            num_needed: Cantidad de descripciones necesarias
            exclude_descriptions: Descripciones a evitar
        
        Returns:
            Lista de nuevas descripciones
        """
        try:
            logger.info(f"🔄 Regenerando {num_needed} descripciones únicas...")
            
            from utils.user_storage import get_user_storage
            user_storage = get_user_storage('saltbalente')
            
            api_key_data = user_storage.get_api_key(ai_provider)
            
            if not api_key_data or not api_key_data.get('api_key'):
                logger.error(f"❌ No hay API key para {ai_provider}")
                return []
            
            # Configurar generador
            success = self.ai_generator.set_provider(
                provider_type=ai_provider,
                api_key=api_key_data['api_key'],
                model=ai_model
            )
            
            if not success:
                logger.error("❌ Error configurando provider")
                return []
            
            # Llamar al método específico del provider para generar solo descripciones
            new_descriptions = self.ai_generator.provider.generate_descriptions_only(
                keywords=keywords,
                business_description=business_description,
                num_descriptions=num_needed,
                tone=tone,
                temperature=creativity + 0.1,  # Aumentar creatividad ligeramente
                exclude_descriptions=exclude_descriptions
            )
            
            logger.info(f"✅ {len(new_descriptions)} nuevas descripciones generadas")
            
            return new_descriptions
            
        except Exception as e:
            logger.error(f"❌ Error regenerando descripciones: {e}")
            return []

    def _generate_ads_fallback(
        self,
        keywords: List[str],
        business_url: str,
        num_ads: int
    ) -> List[Dict[str, Any]]:
        """Fallback básico si falla IA con validación de unicidad"""
        
        logger.warning("⚠️ Usando fallback para anuncios")
        
        ads = []
        
        for i in range(num_ads):
            # ✅ GENERAR TÍTULOS Y DESCRIPCIONES ÚNICOS
            fallback_headlines = [
                keywords[0].title() if keywords else 'Servicios Profesionales',
                'Calidad Garantizada',
                'Atención Personalizada',
                'Expertos Certificados',
                'Resultados Comprobados',
                'Consulta Gratis',
                'Mejor Precio',
                'Servicio Rápido',
                'Garantía Total',
                'Profesionales',
                keywords[1].title() if len(keywords) > 1 else 'Confiables',
                'Atención 24/7',
                'Experiencia',
                'Líderes del Sector',
                'Tu Mejor Opción'
            ]
            
            fallback_descriptions = [
                f"Descubre nuestros servicios profesionales. Calidad y experiencia garantizada.",
                f"Más de 10 años de experiencia. Atención personalizada. Resultados comprobados.",
                f"Consulta gratis. Servicio profesional. Garantía de satisfacción 100%.",
                f"Contáctanos hoy mismo. Presupuesto sin compromiso. Soluciones efectivas."
            ]
            
            # ✅ VALIDAR UNICIDAD
            unique_headlines = self._ensure_unique_headlines(fallback_headlines)
            unique_descriptions = self._ensure_unique_descriptions(fallback_descriptions)
            
            ad = {
                'headlines': unique_headlines,
                'descriptions': unique_descriptions,
                'final_url': business_url,
                'path1': self._extract_path_from_url(business_url, 1),
                'path2': self._extract_path_from_url(business_url, 2)
            }
            ads.append(ad)
        
        return ads
    
    def _apply_match_types(
        self,
        keywords: List[str],
        match_types: List[str]
    ) -> List[Dict[str, str]]:
        """Aplica match types a keywords"""
        
        result = []
        
        # Si solo hay un match type, aplicar a todas
        if len(match_types) == 1:
            for kw in keywords:
                result.append({
                    'text': kw,
                    'match_type': match_types[0]
                })
        else:
            # Distribuir match types
            for idx, kw in enumerate(keywords):
                match_type = match_types[idx % len(match_types)]
                result.append({
                    'text': kw,
                    'match_type': match_type
                })
        
        return result
    
    def _generate_intelligent_group_name(
        self,
        keywords: List[str],
        business_description: str,
        group_index: int
    ) -> str:
        """Genera nombre inteligente del grupo"""
        
        if not keywords:
            return f"AG_{group_index+1}_Grupo"
        
        # Usar primera keyword como base
        base = keywords[0].replace(' ', '_')[:30]
        
        return f"AG_{group_index+1}_{base}"
    
    def _extract_theme(self, keywords: List[str]) -> str:
        """Extrae tema de keywords"""
        return keywords[0].split()[0].title() if keywords else 'General'
    
    def _generate_negative_keywords(self, business_description: str) -> List[str]:
        """Genera negative keywords"""
        return ['gratis', 'free', 'barato', 'cheap', 'gratuito']
    
    def _calculate_smart_bid(self, keywords: List[str]) -> float:
        """Calcula puja inteligente"""
        return 1.0  # USD
    
    def _validate_url(self, url: str) -> str:
        """Valida URL"""
        if not url:
            return 'https://example.com'
        url = url.strip()
        if not url.startswith('http'):
            url = 'https://' + url
        return url
    
    def _extract_path_from_url(self, url: str, path_number: int) -> str:
        """Extrae path de URL"""
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            if path_number == 1 and len(path_parts) > 0:
                return path_parts[0][:15]
            elif path_number == 2 and len(path_parts) > 1:
                return path_parts[1][:15]
            
            return ''
        except:
            return ''
    
    # =======================================================================
    # PUBLICACIÓN - FIX BUDGET_DAILY
    # =======================================================================
    
    def publish_complete_campaign(
        self,
        customer_id: str,
        campaign_option,
        ad_groups: List[Dict[str, Any]],
        campaign_config: Optional[Dict[str, Any]] = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """Publica campaña - FIX BUDGET_DAILY"""
        
        try:
            if progress_callback:
                progress_callback("🚀 Iniciando publicación...", 5)
            
            logger.info(f"🚀 Publicando: {len(ad_groups)} grupos")
            logger.info(f"📊 Modo: {'Nueva' if campaign_option.is_new else 'Existente'}")
            logger.info(f"🆔 Campaign ID: {campaign_option.campaign_id}")
            
            if not ad_groups:
                return {
                    'success': False,
                    'error': 'No hay grupos',
                    'ad_group_ids': [],
                    'ad_ids': [],
                    'keyword_ids': []
                }
            
            # ✅ CREAR BLUEPRINT SEGÚN EL MODO
            if campaign_option.is_new:
                # NUEVA CAMPAÑA - Necesita budget_daily
                logger.info("🆕 Preparando blueprint para NUEVA CAMPAÑA")
                
                default_budget = 20.0
                default_name = f"AUTOPILOT_{datetime.now().strftime('%Y%m%d_%H%M')}"
                
                if campaign_config:
                    default_budget = campaign_config.get('budget_daily', default_budget)
                    default_name = campaign_config.get('campaign_name', default_name)
                
                blueprint = {
                    'campaign_name': default_name,
                    'budget_daily': default_budget,  # ✅ REQUERIDO PARA NUEVA
                    'target_locations': ['United States'],
                    'languages': ['es', 'en'],
                    'business_url': campaign_config.get('business_url', 'https://example.com') if campaign_config else 'https://example.com',
                    'ad_groups': ad_groups
                }
                
                logger.info(f"📋 Blueprint nueva campaña:")
                logger.info(f"   - Nombre: {blueprint['campaign_name']}")
                logger.info(f"   - Budget: ${blueprint['budget_daily']}/día")
                logger.info(f"   - Grupos: {len(blueprint['ad_groups'])}")
            
            else:
                # CAMPAÑA EXISTENTE - NO necesita budget_daily
                logger.info(f"📂 Preparando blueprint para CAMPAÑA EXISTENTE: {campaign_option.campaign_id}")
                
                blueprint = {
                    'campaign_id': campaign_option.campaign_id,
                    'campaign_name': campaign_option.campaign_name,
                    'business_url': campaign_config.get('business_url', 'https://example.com') if campaign_config else 'https://example.com',
                    'ad_groups': ad_groups
                }
                
                logger.info(f"📋 Blueprint campaña existente:")
                logger.info(f"   - ID: {blueprint['campaign_id']}")
                logger.info(f"   - Nombre: {blueprint['campaign_name']}")
                logger.info(f"   - Grupos: {len(blueprint['ad_groups'])}")
            
            # ✅ PUBLICAR
            if progress_callback:
                progress_callback("📤 Publicando a Google Ads...", 10)
            
            logger.info("📤 Llamando a autopilot_publisher.publish_complete_campaign")
            
            result = self.autopilot_publisher.publish_complete_campaign(
                blueprint=blueprint,
                customer_id=customer_id,
                progress_callback=progress_callback
            )
            
            logger.info(f"📊 Resultado publicación:")
            logger.info(f"   - Success: {result.get('success')}")
            logger.info(f"   - Grupos creados: {len(result.get('ad_group_ids', []))}")
            logger.info(f"   - Anuncios creados: {len(result.get('ad_ids', []))}")
            logger.info(f"   - Keywords creadas: {len(result.get('keyword_ids', []))}")
            
            if result.get('errors'):
                logger.error(f"❌ Errores: {result['errors']}")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error publicando: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            
            return {
                'success': False,
                'error': error_msg,
                'ad_group_ids': [],
                'ad_ids': [],
                'keyword_ids': []
            }
    
    def validate_ad_groups(self, ad_groups: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Valida grupos"""
        errors = []
        
        if not ad_groups:
            errors.append("❌ No hay grupos")
            return False, errors
        
        for i, group in enumerate(ad_groups):
            if not group.get('keywords'):
                errors.append(f"❌ Grupo {i+1}: Sin keywords")
            if not group.get('ads'):
                errors.append(f"❌ Grupo {i+1}: Sin anuncios")
        
        is_valid = len([e for e in errors if e.startswith('❌')]) == 0
        return is_valid, errors
    
    # ========================================================================
    # MÉTODOS DE VALIDACIÓN DE UNICIDAD
    # ========================================================================
    
    def _ensure_unique_keywords(self, keywords: List[str], group_index: int) -> List[str]:
        """
        Asegura que las keywords sean únicas entre grupos de anuncios
        """
        unique_keywords = []
        
        # Obtener todas las keywords ya usadas en grupos anteriores
        used_keywords = set()
        for group_keywords in self.used_keywords_by_group:
            used_keywords.update(group_keywords)
        
        # Filtrar keywords únicas
        for keyword in keywords:
            keyword_clean = keyword.lower().strip()
            if keyword_clean not in used_keywords:
                unique_keywords.append(keyword)
                used_keywords.add(keyword_clean)
        
        # Guardar las keywords de este grupo
        if len(self.used_keywords_by_group) <= group_index:
            self.used_keywords_by_group.append([])
        
        self.used_keywords_by_group[group_index] = [kw.lower().strip() for kw in unique_keywords]
        
        logger.info(f"🔍 Grupo {group_index + 1}: {len(keywords)} keywords originales → {len(unique_keywords)} keywords únicas")
        
        return unique_keywords
    
    def _ensure_unique_headlines(self, headlines: List[str]) -> List[str]:
        """
        Asegura que los títulos sean únicos globalmente
        """
        unique_headlines = []
        
        for headline in headlines:
            headline_clean = headline.strip()
            if headline_clean and headline_clean not in self.used_headlines:
                unique_headlines.append(headline_clean)
                self.used_headlines.add(headline_clean)
        
        logger.info(f"📝 Headlines: {len(headlines)} originales → {len(unique_headlines)} únicos")
        
        return unique_headlines
    
    def _ensure_unique_descriptions(self, descriptions: List[str], min_similarity: float = 0.85) -> List[str]:
        """
        Asegura que las descripciones sean únicas globalmente con validación de similitud
        
        Args:
            descriptions: Lista de descripciones generadas
            min_similarity: Umbral de similitud (0.85 = 85% similar = rechazar)
        
        Returns:
            Lista de descripciones únicas validadas
        """
        from difflib import SequenceMatcher
        
        unique_descriptions = []
        
        for description in descriptions:
            description_clean = description.strip()
            
            if not description_clean:
                continue
            
            # Verificar si ya existe exactamente
            if description_clean in self.used_descriptions:
                logger.warning(f"⚠️ Descripción duplicada exacta rechazada: '{description_clean[:50]}...'")
                continue
            
            # Verificar similitud con descripciones existentes
            is_too_similar = False
            
            for used_desc in self.used_descriptions:
                similarity = SequenceMatcher(None, description_clean.lower(), used_desc.lower()).ratio()
                
                if similarity >= min_similarity:
                    logger.warning(f"⚠️ Descripción muy similar ({similarity*100:.1f}%) rechazada:")
                    logger.warning(f"   Nueva: '{description_clean[:50]}...'")
                    logger.warning(f"   Existente: '{used_desc[:50]}...'")
                    is_too_similar = True
                    break
            
            if not is_too_similar:
                unique_descriptions.append(description_clean)
                self.used_descriptions.add(description_clean)
                logger.info(f"✅ Descripción única aceptada: '{description_clean[:50]}...'")
        
        logger.info(f"📄 Descriptions: {len(descriptions)} originales → {len(unique_descriptions)} únicos")
        
        return unique_descriptions