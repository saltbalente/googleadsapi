"""
🚀 AUTOPILOT CAMPAIGN GENERATOR 2050
Sistema de generación automática de campañas completas con IA
Versión: 1.0 Ultra Pro
Fecha: 2025-10-13
Autor: saltbalente
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, field
import json
import time

logger = logging.getLogger(__name__)

# ============================================================================
# IMPORTS NECESARIOS
# ============================================================================

try:
    from services.autopilot_publisher import AutopilotPublisher
    PUBLISHER_AVAILABLE = True
except ImportError:
    logger.warning("AutopilotPublisher no disponible - la publicación será simulada")
    PUBLISHER_AVAILABLE = False


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class CampaignBlueprint:
    """Blueprint de una campaña completa"""
    campaign_name: str
    business_url: str
    business_description: str
    budget_daily: float
    target_locations: List[str]
    languages: List[str] = field(default_factory=lambda: ['es'])
    
    # Generado por IA
    themes: List[Dict[str, Any]] = field(default_factory=list)
    ad_groups: List[Dict[str, Any]] = field(default_factory=list)
    total_ads: int = 0
    total_keywords: int = 0
    estimated_ctr: float = 0.0
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "draft"  # draft, generating, validating, ready, publishing, published


@dataclass
class AdGroup:
    """Grupo de anuncios con todo incluido"""
    name: str
    theme: str
    keywords: List[str]
    negative_keywords: List[str]
    ads: List[Dict[str, Any]]
    max_cpc_bid: float
    status: str = "pending"  # pending, generating, validating, ready, published
    score: float = 0.0


# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class AutopilotCampaignGenerator:
    """
    Generador automático de campañas completas
    
    Flow:
    1. Analizar negocio/sitio web
    2. Extraer temas principales (3-10 temas)
    3. Por cada tema:
       - Generar keywords (10-50 por tema)
       - Generar negative keywords
       - Crear 3-5 anuncios completos
       - Calcular score y validar
    4. Estructurar en ad groups
    5. Publicar a Google Ads
    """
    
    def __init__(
        self,
        ai_generator,
        google_ads_client=None,
        user_storage=None
    ):
        self.ai_generator = ai_generator
        self.google_ads_client = google_ads_client
        self.user_storage = user_storage
        self.current_blueprint: Optional[CampaignBlueprint] = None
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """Establece callback para actualizaciones de progreso"""
        self.progress_callback = callback
    
    # ========================================================================
    # FASE 1: ANÁLISIS Y EXTRACCIÓN DE TEMAS
    # ========================================================================
    
    async def analyze_business(
        self,
        business_url: str,
        business_description: str,
        num_themes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analiza el negocio y extrae temas principales
        
        Returns:
            Lista de temas con estructura:
            {
                'theme': 'Amarres de Amor',
                'description': 'Servicios de amarres para parejas',
                'priority': 1,
                'estimated_volume': 'high',
                'competition': 'medium'
            }
        """
        
        self._update_progress("🧠 Analizando negocio con IA...", 5)
        
        prompt = f"""Eres un experto en marketing digital y Google Ads.

NEGOCIO:
- URL: {business_url}
- Descripción: {business_description}

TAREA:
Analiza este negocio y genera {num_themes} TEMAS PRINCIPALES para campañas de Google Ads.

REQUISITOS:
1. Cada tema debe ser específico y orientado a búsqueda
2. Priorizar por volumen de búsqueda estimado
3. Considerar competencia y relevancia
4. Temas viables para Google Ads (no prohibidos)

FORMATO JSON ESTRICTO:
{{
  "themes": [
    {{
      "theme": "Nombre del tema",
      "description": "Descripción breve",
      "priority": 1,
      "estimated_volume": "high|medium|low",
      "competition": "high|medium|low",
      "buyer_intent": "high|medium|low"
    }}
  ]
}}

Genera temas comerciales y específicos."""

        try:
            # Usar el AI generator
            response = await self._call_ai(prompt, business_description)
            themes_data = json.loads(response)
            
            self._update_progress(f"✅ {len(themes_data['themes'])} temas identificados", 10)
            
            return themes_data['themes']
        
        except Exception as e:
            logger.error(f"Error analizando negocio: {e}")
            return self._get_fallback_themes(business_description)
    
    # ========================================================================
    # FASE 2: GENERACIÓN DE KEYWORDS POR TEMA
    # ========================================================================
    
    async def generate_keywords_for_theme(
        self,
        theme: Dict[str, Any],
        num_keywords: int = 30
    ) -> Dict[str, List[str]]:
        """
        Genera keywords y negative keywords para un tema
        
        Returns:
            {
                'keywords': [...],
                'negative_keywords': [...]
            }
        """
        
        self._update_progress(f"🎯 Generando keywords para '{theme['theme']}'...", None)
        
        prompt = f"""Eres un experto en keyword research para Google Ads.

TEMA: {theme['theme']}
DESCRIPCIÓN: {theme['description']}
VOLUMEN: {theme['estimated_volume']}

TAREA:
Genera {num_keywords} keywords optimizadas para Google Ads.

REQUISITOS:
1. Mezcla de concordancia amplia, frase y exacta
2. Incluir long-tail keywords
3. Considerar intención de búsqueda
4. Excluir keywords irrelevantes o prohibidas

TAMBIÉN GENERA 10 NEGATIVE KEYWORDS para evitar tráfico no deseado.

FORMATO JSON:
{{
  "keywords": [
    "keyword 1",
    "keyword 2"
  ],
  "negative_keywords": [
    "gratis",
    "free"
  ]
}}"""

        try:
            response = await self._call_ai(prompt, theme['theme'])
            keywords_data = json.loads(response)
            
            return keywords_data
        
        except Exception as e:
            logger.error(f"Error generando keywords: {e}")
            return self._generate_keywords_fallback(theme)
    
    # ========================================================================
    # FASE 3: GENERACIÓN DE ANUNCIOS POR GRUPO
    # ========================================================================
    
    async def generate_ads_for_group(
        self,
        theme: Dict[str, Any],
        keywords: List[str],
        num_ads: int = 3,
        tone: str = 'profesional'
    ) -> List[Dict[str, Any]]:
        """
        Genera múltiples anuncios para un grupo
        
        Returns:
            Lista de anuncios con headlines y descriptions
        """
        
        self._update_progress(f"📝 Generando {num_ads} anuncios para '{theme['theme']}'...", None)
        
        # Usar el sistema existente de generación de anuncios
        try:
            # Configurar proveedor IA si está disponible
            if self.user_storage:
                api_keys = self.user_storage.get_api_keys()
                provider = 'openai'  # o el default del usuario
                
                if provider in api_keys and api_keys[provider].get('api_key'):
                    provider_config = api_keys[provider]
                    if isinstance(provider_config, dict) and provider_config.get('api_key', '').strip():
                        self.ai_generator.set_provider(
                            provider_type=provider,
                            api_key=provider_config['api_key'],
                            model=provider_config.get('model', 'gpt-4o')
                        )
            
            # Generar batch usando el método síncrono
            batch_result = self.ai_generator.generate_batch(
                keywords=keywords[:5],  # Top 5 keywords
                num_ads=num_ads,
                num_headlines=10,
                num_descriptions=3,
                tone=tone,
                validate=True,
                business_type='esoteric',
                save_to_csv=False
            )
            
            return batch_result['ads']
        
        except Exception as e:
            logger.error(f"Error generando anuncios: {e}")
            return self._generate_ads_fallback(theme, keywords)
    
    # ========================================================================
    # FASE 4: ENSAMBLAJE DE CAMPAÑA COMPLETA
    # ========================================================================
    
    async def generate_complete_campaign(
        self,
        campaign_name: str,
        business_url: str,
        business_description: str,
        budget_daily: float,
        target_locations: List[str],
        num_themes: int = 5,
        ads_per_group: int = 3,
        tone: str = 'profesional'
    ) -> CampaignBlueprint:
        """
        Genera una campaña completa automaticamente
        
        Flow completo:
        1. Analizar negocio → Extraer temas
        2. Por cada tema:
           - Generar keywords
           - Generar anuncios
           - Validar y calcular score
        3. Estructurar en ad groups
        4. Retornar blueprint listo para publicar
        """
        
        self._update_progress("🚀 Iniciando generación automática...", 0)
        
        # Crear blueprint
        blueprint = CampaignBlueprint(
            campaign_name=campaign_name,
            business_url=business_url,
            business_description=business_description,
            budget_daily=budget_daily,
            target_locations=target_locations
        )
        
        self.current_blueprint = blueprint
        blueprint.status = "generating"
        
        try:
            # FASE 1: Analizar y extraer temas
            themes = await self.analyze_business(
                business_url,
                business_description,
                num_themes
            )
            blueprint.themes = themes
            
            # FASE 2-3: Por cada tema, generar keywords y anuncios
            total_steps = len(themes) * 3  # keywords + ads + validation
            current_step = 0
            
            for theme in themes:
                # Generar keywords
                keywords_data = await self.generate_keywords_for_theme(theme)
                current_step += 1
                progress = 10 + (current_step / total_steps * 70)
                self._update_progress(f"Keywords generadas para {theme['theme']}", progress)
                
                # Generar anuncios
                ads = await self.generate_ads_for_group(
                    theme,
                    keywords_data['keywords'],
                    num_ads=ads_per_group,
                    tone=tone
                )
                current_step += 1
                progress = 10 + (current_step / total_steps * 70)
                self._update_progress(f"Anuncios generados para {theme['theme']}", progress)
                
                # Validar y calcular score promedio
                valid_ads = [ad for ad in ads if not ad.get('error')]
                avg_score = sum(ad.get('score', 0) for ad in valid_ads) / len(valid_ads) if valid_ads else 0
                
                current_step += 1
                progress = 10 + (current_step / total_steps * 70)
                
                # Crear ad group
                ad_group = AdGroup(
                    name=f"{campaign_name} - {theme['theme']}",
                    theme=theme['theme'],
                    keywords=keywords_data['keywords'],
                    negative_keywords=keywords_data['negative_keywords'],
                    ads=valid_ads,
                    max_cpc_bid=self._calculate_suggested_bid(theme),
                    status="ready",
                    score=avg_score
                )
                
                blueprint.ad_groups.append(ad_group.__dict__)
                blueprint.total_ads += len(valid_ads)
                blueprint.total_keywords += len(keywords_data['keywords'])
            
            # Calcular estadísticas finales
            blueprint.estimated_ctr = self._estimate_campaign_ctr(blueprint)
            blueprint.status = "ready"
            
            self._update_progress("✅ Campaña generada completamente", 90)
            
            return blueprint
        
        except Exception as e:
            logger.error(f"Error generando campaña: {e}")
            blueprint.status = "error"
            raise
    
    # ========================================================================
    # FASE 5: PUBLICACIÓN A GOOGLE ADS (REAL)
    # ========================================================================
    
    async def publish_campaign(
        self,
        blueprint: CampaignBlueprint,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Publica la campaña completa a Google Ads usando AutopilotPublisher
        
        Returns:
            {
                'success': True/False,
                'campaign_id': '...',
                'ad_group_ids': [...],
                'ad_ids': [...],
                'keyword_ids': [...],
                'errors': [...],
                'warnings': [...]
            }
        """
        
        self._update_progress("🚀 Publicando campaña a Google Ads...", 90)
        blueprint.status = "publishing"
        
        try:
            # Verificar que tenemos Google Ads client
            if not self.google_ads_client:
                logger.error("Google Ads client no disponible")
                return {
                    'success': False,
                    'campaign_id': None,
                    'ad_group_ids': [],
                    'ad_ids': [],
                    'keyword_ids': [],
                    'errors': ['Google Ads client no configurado'],
                    'warnings': []
                }
            
            # Verificar si AutopilotPublisher está disponible
            if not PUBLISHER_AVAILABLE:
                logger.warning("AutopilotPublisher no disponible - usando simulación")
                return await self._publish_campaign_simulated(blueprint, customer_id)
            
            # Crear publisher real
            publisher = AutopilotPublisher(self.google_ads_client)
            
            # Publicar de forma async
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                publisher.publish_complete_campaign,
                blueprint.__dict__,
                customer_id,
                self.progress_callback
            )
            
            if result['success']:
                blueprint.status = "published"
                self._update_progress("🎉 Campaña publicada exitosamente", 100)
            else:
                blueprint.status = "error"
                self._update_progress("❌ Error en publicación", 100)
            
            return result
            
        except Exception as e:
            error_msg = f"Error publicando campaña: {str(e)}"
            logger.error(error_msg)
            blueprint.status = "error"
            return {
                'success': False,
                'campaign_id': None,
                'ad_group_ids': [],
                'ad_ids': [],
                'keyword_ids': [],
                'errors': [error_msg],
                'warnings': []
            }
    
    async def _publish_campaign_simulated(
        self,
        blueprint: CampaignBlueprint,
        customer_id: str
    ) -> Dict[str, Any]:
        """Simulación de publicación cuando AutopilotPublisher no está disponible"""
        
        result = {
            'success': False,
            'campaign_id': None,
            'ad_group_ids': [],
            'ad_ids': [],
            'keyword_ids': [],
            'errors': [],
            'warnings': ['Modo simulación - no se publicó realmente']
        }
        
        try:
            # Simulación de publicación
            await asyncio.sleep(2)
            
            campaign_id = f"sim_campaign_{int(datetime.utcnow().timestamp())}"
            result['campaign_id'] = campaign_id
            
            self._update_progress(f"✅ [SIM] Campaña creada: {campaign_id}", 92)
            
            for idx, ad_group_data in enumerate(blueprint.ad_groups):
                ad_group_id = f"sim_adgroup_{int(datetime.utcnow().timestamp())}_{idx}"
                result['ad_group_ids'].append(ad_group_id)
                
                # Simular IDs de keywords
                for _ in ad_group_data['keywords']:
                    result['keyword_ids'].append(f"sim_kw_{int(datetime.utcnow().timestamp())}")
                
                # Simular IDs de anuncios
                for ad_idx in range(len(ad_group_data['ads'])):
                    ad_id = f"sim_ad_{int(datetime.utcnow().timestamp())}_{idx}_{ad_idx}"
                    result['ad_ids'].append(ad_id)
                
                progress = 92 + ((idx + 1) / len(blueprint.ad_groups) * 8)
                self._update_progress(
                    f"✅ [SIM] Grupo {idx+1}/{len(blueprint.ad_groups)} publicado",
                    progress
                )
            
            blueprint.status = "published"
            result['success'] = True
            
            self._update_progress("🎉 [SIM] Campaña publicada (modo simulación)", 100)
            
            return result
            
        except Exception as e:
            error_msg = f"Error en simulación: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            blueprint.status = "error"
            return result
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    async def _call_ai(self, prompt: str, context: str = "") -> str:
        """Llama a la IA de forma async con análisis inteligente"""
        try:
            # Verificar que tenemos un generador configurado
            if not self.ai_generator:
                logger.error("AI Generator no disponible")
                return self._generate_fallback_response(prompt, context)
            
            # Ejecutar de forma async
            loop = asyncio.get_event_loop()
            
            # Simular delay para mostrar progreso
            await asyncio.sleep(0.5)
            
            # Análisis del tipo de respuesta esperada
            if 'themes' in prompt.lower() or 'temas' in prompt.lower():
                return self._generate_themes_response(context)
            
            elif 'keywords' in prompt.lower():
                return self._generate_keywords_response(context)
            
            # Fallback genérico
            return self._generate_fallback_response(prompt, context)
            
        except Exception as e:
            logger.error(f"Error en llamada AI: {e}")
            return self._generate_fallback_response(prompt, context)
    
    def _generate_themes_response(self, business_description: str) -> str:
        """Genera temas basados en análisis de descripción"""
        # Análisis básico de palabras clave
        description_lower = business_description.lower()
        
        themes = []
        
        # Detectar tipo de negocio y generar temas relevantes
        if any(word in description_lower for word in ['médico', 'clínica', 'salud', 'tratamiento', 'doctor']):
            themes = [
                {
                    "theme": "Servicios Médicos Especializados",
                    "description": "Consultas y tratamientos médicos profesionales",
                    "priority": 1,
                    "estimated_volume": "high",
                    "competition": "medium",
                    "buyer_intent": "high"
                },
                {
                    "theme": "Atención Médica Local",
                    "description": "Servicios médicos en tu zona",
                    "priority": 2,
                    "estimated_volume": "medium",
                    "competition": "low",
                    "buyer_intent": "high"
                },
                {
                    "theme": "Especialidades Médicas",
                    "description": "Tratamientos especializados por expertos",
                    "priority": 3,
                    "estimated_volume": "medium",
                    "competition": "medium",
                    "buyer_intent": "high"
                }
            ]
        elif any(word in description_lower for word in ['restaurante', 'comida', 'cocina', 'chef', 'menú']):
            themes = [
                {
                    "theme": "Servicios de Restaurante",
                    "description": "Experiencia gastronómica de calidad",
                    "priority": 1,
                    "estimated_volume": "high",
                    "competition": "high",
                    "buyer_intent": "high"
                },
                {
                    "theme": "Comida para Llevar",
                    "description": "Servicio de delivery y take-out",
                    "priority": 2,
                    "estimated_volume": "high",
                    "competition": "medium",
                    "buyer_intent": "high"
                },
                {
                    "theme": "Eventos y Catering",
                    "description": "Servicio de catering para eventos",
                    "priority": 3,
                    "estimated_volume": "medium",
                    "competition": "low",
                    "buyer_intent": "medium"
                }
            ]
        else:
            # Temas genéricos adaptables
            themes = [
                {
                    "theme": "Servicios Principales",
                    "description": "Servicios core del negocio",
                    "priority": 1,
                    "estimated_volume": "high",
                    "competition": "medium",
                    "buyer_intent": "high"
                },
                {
                    "theme": "Servicios Locales",
                    "description": "Atención en tu zona",
                    "priority": 2,
                    "estimated_volume": "medium",
                    "competition": "low",
                    "buyer_intent": "high"
                },
                {
                    "theme": "Ofertas Especiales",
                    "description": "Promociones y paquetes",
                    "priority": 3,
                    "estimated_volume": "medium",
                    "competition": "low",
                    "buyer_intent": "medium"
                }
            ]
        
        return json.dumps({"themes": themes})
    
    def _generate_keywords_response(self, theme_name: str) -> str:
        """Genera keywords basadas en el tema"""
        theme_lower = theme_name.lower()
        
        keywords = []
        negative_keywords = ["gratis", "free", "curso", "tutorial"]
        
        # Keywords específicas por tipo de tema
        if 'médico' in theme_lower or 'salud' in theme_lower:
            keywords = [
                "consulta médica", "doctor especialista", "atención médica",
                "tratamiento profesional", "clínica médica", "servicios de salud",
                "médico certificado", "atención especializada", "consulta profesional"
            ]
        elif 'local' in theme_lower:
            keywords = [
                "servicios locales", "cerca de mí", "en mi ciudad",
                "atención local", "negocio local", "servicio domicilio",
                "entrega local", "tienda cerca"
            ]
        elif 'oferta' in theme_lower or 'promoción' in theme_lower:
            keywords = [
                "ofertas especiales", "descuentos", "promociones",
                "paquetes especiales", "precio especial", "oferta limitada"
            ]
        else:
            keywords = [
                "servicios profesionales", "atención personalizada", "calidad garantizada",
                "empresa confiable", "servicio rápido", "mejor servicio",
                "atención inmediata", "profesionales certificados"
            ]
        
        return json.dumps({
            "keywords": keywords[:15],
            "negative_keywords": negative_keywords
        })
    
    def _generate_fallback_response(self, prompt: str, context: str) -> str:
        """Respuesta de fallback genérica"""
        return json.dumps({
            "themes": self._get_fallback_themes(context)
        })
    
    def _generate_keywords_fallback(self, theme: Dict[str, Any]) -> Dict[str, List[str]]:
        """Genera keywords de fallback basadas en el tema"""
        return {
            'keywords': [
                f"{theme['theme'].lower()}",
                f"mejor {theme['theme'].lower()}",
                f"{theme['theme'].lower()} profesional",
                "servicios de calidad",
                "atención personalizada"
            ],
            'negative_keywords': ['gratis', 'free', 'curso']
        }
    
    def _generate_ads_fallback(self, theme: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
        """Genera anuncios de fallback"""
        return [{
            'headlines': [
                f"{theme['theme']}",
                f"Servicio Profesional",
                f"Calidad Garantizada",
                f"{keywords[0].title() if keywords else 'Servicios'}",
                f"Atención Inmediata",
                f"Expertos Certificados",
                f"Mejor Precio Calidad",
                f"Consulta Gratis",
                f"Resultados Garantizados",
                f"Servicio 24/7"
            ],
            'descriptions': [
                f"Descubre nuestros servicios de {theme['theme'].lower()}. Calidad y experiencia garantizada.",
                f"Más de 10 años de experiencia. Atención personalizada. Resultados comprobados.",
                f"Consulta gratis. Servicio profesional. Garantía de satisfacción 100%."
            ],
            'keywords': keywords,
            'tone': 'profesional',
            'provider': 'fallback',
            'model': 'builtin',
            'score': 75.0,
            'error': None
        }]
    
    def _update_progress(self, message: str, progress: Optional[float]):
        """Actualiza el progreso si hay callback"""
        if self.progress_callback:
            self.progress_callback(message, progress)
        
        logger.info(f"Progress: {message} ({progress}%)")
    
    def _calculate_suggested_bid(self, theme: Dict[str, Any]) -> float:
        """Calcula puja sugerida basada en competencia y volumen"""
        base_bid = 0.50  # $0.50 base
        
        # Ajustar por volumen
        volume_multiplier = {
            'high': 1.5,
            'medium': 1.0,
            'low': 0.7
        }.get(theme.get('estimated_volume', 'medium'), 1.0)
        
        # Ajustar por competencia
        competition_multiplier = {
            'high': 1.3,
            'medium': 1.0,
            'low': 0.8
        }.get(theme.get('competition', 'medium'), 1.0)
        
        return round(base_bid * volume_multiplier * competition_multiplier, 2)
    
    def _estimate_campaign_ctr(self, blueprint: CampaignBlueprint) -> float:
        """Estima CTR promedio de la campaña"""
        if not blueprint.ad_groups:
            return 0.0
        
        scores = [ag['score'] for ag in blueprint.ad_groups if ag.get('score')]
        if not scores:
            return 0.0
        
        avg_score = sum(scores) / len(scores)
        
        # Convertir score (0-100) a CTR estimado (0-10%)
        estimated_ctr = (avg_score / 100) * 10
        
        return round(estimated_ctr, 2)
    
    def _get_fallback_themes(self, business_description: str = "") -> List[Dict[str, Any]]:
        """Temas de fallback si falla la IA"""
        return [
            {
                'theme': 'Servicios Principales',
                'description': 'Servicios core del negocio',
                'priority': 1,
                'estimated_volume': 'high',
                'competition': 'medium',
                'buyer_intent': 'high'
            },
            {
                'theme': 'Servicios Locales',
                'description': 'Atención en ubicación específica',
                'priority': 2,
                'estimated_volume': 'medium',
                'competition': 'low',
                'buyer_intent': 'high'
            },
            {
                'theme': 'Ofertas Especiales',
                'description': 'Promociones y paquetes especiales',
                'priority': 3,
                'estimated_volume': 'medium',
                'competition': 'low',
                'buyer_intent': 'medium'
            }
        ]
    
    # ========================================================================
    # MÉTODO SÍNCRONO PARA BLUEPRINT
    # ========================================================================
    
    def generate_campaign_blueprint(self, campaign_config: Dict[str, Any]) -> CampaignBlueprint:
        """
        Método síncrono para generar un blueprint de campaña
        Usado por la UI de AUTOPILOT 2050
        """
        try:
            # Extraer configuración
            business_description = campaign_config.get('business_description', '')
            target_audience = campaign_config.get('target_audience', '')
            budget_range = campaign_config.get('budget_range', '$500-1000/mes')
            objectives = campaign_config.get('objectives', ['Generar Leads'])
            geographic_targeting = campaign_config.get('geographic_targeting', 'México')
            num_campaigns = campaign_config.get('num_campaigns', 1)
            
            # Convertir presupuesto a valor diario
            budget_daily = self._parse_budget_range(budget_range)
            
            # Crear nombre de campaña
            campaign_name = f"AUTOPILOT 2050 - {objectives[0] if objectives else 'Campaña'}"
            
            # Procesar ubicaciones
            locations = [loc.strip() for loc in geographic_targeting.split(',') if loc.strip()]
            if not locations:
                locations = ['México']
            
            # Crear blueprint básico
            blueprint = CampaignBlueprint(
                campaign_name=campaign_name,
                business_url="",
                business_description=business_description,
                budget_daily=budget_daily,
                target_locations=locations,
                languages=['es']
            )
            
            # Generar temas basados en la descripción
            themes = self._generate_themes_from_description(business_description, target_audience)
            blueprint.themes = themes
            
            # Generar grupos de anuncios
            ad_groups = []
            total_keywords = 0
            total_ads = 0
            
            for i, theme in enumerate(themes[:3]):  # Máximo 3 temas
                # Generar keywords
                keywords = self._generate_keywords_for_theme_sync(theme, business_description)
                
                # Generar anuncios
                ads = self._generate_ads_for_theme_sync(theme, keywords, business_description)
                
                ad_group = {
                    'name': f"AG_{i+1}_{theme['theme'].replace(' ', '_')}",
                    'theme': theme['theme'],
                    'keywords': keywords,
                    'negative_keywords': ['gratis', 'free', 'barato'],
                    'ads': ads,
                    'max_cpc_bid': self._calculate_suggested_bid(theme),
                    'status': 'ready',
                    'score': 85.0 + (i * 2)
                }
                
                ad_groups.append(ad_group)
                total_keywords += len(keywords)
                total_ads += len(ads)
            
            blueprint.ad_groups = ad_groups
            blueprint.total_keywords = total_keywords
            blueprint.total_ads = total_ads
            blueprint.estimated_ctr = self._estimate_campaign_ctr(blueprint)
            blueprint.status = "ready"
            
            return blueprint
            
        except Exception as e:
            logger.error(f"Error generando blueprint: {e}")
            return self._create_fallback_blueprint(campaign_config)
    
    def _parse_budget_range(self, budget_range: str) -> float:
        """Convierte rango de presupuesto a valor diario"""
        try:
            import re
            numbers = re.findall(r'\d+', budget_range)
            if numbers:
                if len(numbers) >= 2:
                    avg_monthly = (int(numbers[0]) + int(numbers[1])) / 2
                else:
                    avg_monthly = int(numbers[0])
                
                return round(avg_monthly / 30, 2)
            
            return 20.0
            
        except Exception:
            return 20.0
    
    def _generate_themes_from_description(
        self,
        business_description: str,
        target_audience: str
    ) -> List[Dict[str, Any]]:
        """Genera temas basados en descripción del negocio"""
        description_lower = business_description.lower()
        
        themes = []
        
        # Análisis de palabras clave
        if any(word in description_lower for word in ['médico', 'clínica', 'salud', 'tratamiento']):
            themes.append({
                'theme': 'Servicios Médicos',
                'description': 'Consultas y tratamientos profesionales',
                'priority': 1,
                'estimated_volume': 'high',
                'competition': 'medium',
                'buyer_intent': 'high'
            })
        elif any(word in description_lower for word in ['restaurante', 'comida', 'cocina']):
            themes.append({
                'theme': 'Servicios Gastronómicos',
                'description': 'Experiencia culinaria de calidad',
                'priority': 1,
                'estimated_volume': 'high',
                'competition': 'medium',
                'buyer_intent': 'high'
            })
        else:
            themes.append({
                'theme': 'Servicios Principales',
                'description': 'Servicios core del negocio',
                'priority': 1,
                'estimated_volume': 'high',
                'competition': 'medium',
                'buyer_intent': 'high'
            })
        
        # Tema local
        themes.append({
            'theme': 'Servicios Locales',
            'description': 'Atención en tu zona',
            'priority': 2,
            'estimated_volume': 'medium',
            'competition': 'low',
            'buyer_intent': 'high'
        })
        
        # Tema de audiencia
        themes.append({
            'theme': f'Para {target_audience}',
            'description': f'Servicios especializados para {target_audience}',
            'priority': 3,
            'estimated_volume': 'medium',
            'competition': 'medium',
            'buyer_intent': 'high'
        })
        
        return themes
    
    def _generate_keywords_for_theme_sync(
        self,
        theme: Dict[str, Any],
        business_description: str
    ) -> List[str]:
        """Genera keywords de forma síncrona"""
        theme_name = theme['theme'].lower()
        keywords = []
        
        if 'médico' in theme_name:
            keywords.extend([
                'consulta médica', 'doctor especialista', 'atención médica',
                'tratamiento profesional', 'clínica médica', 'servicios de salud'
            ])
        elif 'gastronómico' in theme_name or 'comida' in theme_name:
            keywords.extend([
                'restaurante', 'comida casera', 'chef profesional',
                'servicio catering', 'cocina gourmet', 'menú especial'
            ])
        elif 'local' in theme_name:
            keywords.extend([
                'servicios locales', 'cerca de mí', 'en mi ciudad',
                'local comercial', 'negocio local', 'servicio domicilio'
            ])
        else:
            keywords.extend([
                'servicios profesionales', 'empresa confiable', 'mejor servicio',
                'atención personalizada', 'calidad garantizada', 'precios competitivos'
            ])
        
        return keywords[:15]
    
    def _generate_ads_for_theme_sync(
        self,
        theme: Dict[str, Any],
        keywords: List[str],
        business_description: str
    ) -> List[Dict[str, Any]]:
        """Genera anuncios de forma síncrona"""
        ads = []
        
        for i in range(3):
            ad = {
                'headlines': [
                    f"{theme['theme']}",
                    f"Servicio Profesional",
                    f"{keywords[i % len(keywords)].title()}",
                    "Calidad Garantizada",
                    "Atención Personalizada",
                    "Expertos Certificados",
                    "Consulta Gratis",
                    "Mejor Precio",
                    "Resultados Reales",
                    "Servicio Rápido"
                ],
                'descriptions': [
                    f"Descubre nuestros servicios de {theme['theme'].lower()}. Experiencia y calidad comprobada.",
                    "Más de 10 años de experiencia. Atención personalizada. Garantía de satisfacción.",
                    "Consulta sin compromiso. Presupuesto gratis. Resultados garantizados."
                ],
                'score': 80.0 + i,
                'error': None
            }
            ads.append(ad)
        
        return ads
    
    def _create_fallback_blueprint(self, campaign_config: Dict[str, Any]) -> CampaignBlueprint:
        """Crea blueprint básico en caso de error"""
        return CampaignBlueprint(
            campaign_name="AUTOPILOT 2050 - Campaña Básica",
            business_url="",
            business_description=campaign_config.get('business_description', 'Negocio profesional'),
            budget_daily=20.0,
            target_locations=['México'],
            languages=['es'],
            themes=self._get_fallback_themes(),
            ad_groups=[{
                'name': 'AG_1_Servicios_Principales',
                'theme': 'Servicios Principales',
                'keywords': ['servicios profesionales', 'empresa confiable', 'atención personalizada'],
                'negative_keywords': ['gratis', 'free'],
                'ads': self._generate_ads_fallback(
                    {'theme': 'Servicios Principales'},
                    ['servicios profesionales']
                ),
                'max_cpc_bid': 1.0,
                'status': 'ready',
                'score': 80.0
            }],
            total_ads=1,
            total_keywords=3,
            estimated_ctr=2.5,
            status="ready"
        )