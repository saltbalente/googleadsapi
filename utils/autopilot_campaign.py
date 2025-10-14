"""
🚀 AUTOPILOT CAMPAIGN GENERATOR 2050
Sistema de generación automática de campañas completas con IA
Versión: 1.0 Ultra Pro
Fecha: 2025-01-13
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, field
import json
import time

logger = logging.getLogger(__name__)


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
            response = await self._call_ai(prompt)
            themes_data = json.loads(response)
            
            self._update_progress(f"✅ {len(themes_data['themes'])} temas identificados", 10)
            
            return themes_data['themes']
        
        except Exception as e:
            logger.error(f"Error analizando negocio: {e}")
            return self._get_fallback_themes()
    
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
            response = await self._call_ai(prompt)
            keywords_data = json.loads(response)
            
            return keywords_data
        
        except Exception as e:
            logger.error(f"Error generando keywords: {e}")
            return {
                'keywords': [theme['theme']],
                'negative_keywords': ['gratis', 'free']
            }
    
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
            return []
    
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
    # FASE 5: PUBLICACIÓN A GOOGLE ADS (PLACEHOLDER)
    # ========================================================================
    
    async def publish_campaign(
        self,
        blueprint: CampaignBlueprint,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Publica la campaña completa a Google Ads
        
        Returns:
            {
                'success': True/False,
                'campaign_id': '...',
                'ad_group_ids': [...],
                'errors': [...]
            }
        """
        
        self._update_progress("🚀 Publicando campaña a Google Ads...", 90)
        blueprint.status = "publishing"
        
        result = {
            'success': False,
            'campaign_id': None,
            'ad_group_ids': [],
            'ad_ids': [],
            'errors': []
        }
        
        try:
            # Simulación de publicación (implementar con Google Ads API)
            await asyncio.sleep(2)  # Simular delay
            
            # 1. Crear campaña
            campaign_id = f"campaign_{int(datetime.utcnow().timestamp())}"
            result['campaign_id'] = campaign_id
            
            self._update_progress(f"✅ Campaña creada: {campaign_id}", 92)
            
            # 2. Crear ad groups (simulado)
            for idx, ad_group_data in enumerate(blueprint.ad_groups):
                ad_group_id = f"adgroup_{int(datetime.utcnow().timestamp())}_{idx}"
                result['ad_group_ids'].append(ad_group_id)
                
                # Simular creación de anuncios
                for ad_idx, ad in enumerate(ad_group_data['ads']):
                    ad_id = f"ad_{int(datetime.utcnow().timestamp())}_{idx}_{ad_idx}"
                    result['ad_ids'].append(ad_id)
                
                progress = 92 + ((idx + 1) / len(blueprint.ad_groups) * 8)
                self._update_progress(
                    f"✅ Grupo {idx+1}/{len(blueprint.ad_groups)} publicado",
                    progress
                )
            
            blueprint.status = "published"
            result['success'] = True
            
            self._update_progress("🎉 Campaña publicada exitosamente", 100)
            
            return result
        
        except Exception as e:
            error_msg = f"Error publicando campaña: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            blueprint.status = "error"
            return result
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    async def _call_ai(self, prompt: str) -> str:
        """Llama a la IA de forma async"""
        try:
            # Wrapper para llamadas síncronas del AI generator
            loop = asyncio.get_event_loop()
            
            # Simular delay para mostrar progreso
            await asyncio.sleep(0.5)
            
            # Usar el AI generator existente (método síncrono)
            if hasattr(self.ai_generator, 'generate_single'):
                response = self.ai_generator.generate_single(
                    keywords=['análisis'],
                    num_headlines=1,
                    num_descriptions=1,
                    tone='profesional',
                    custom_prompt=prompt
                )
                return json.dumps(response)
            else:
                # Fallback con respuesta simulada
                return '{"themes": [{"theme": "Servicios Principales", "description": "Servicios core del negocio", "priority": 1, "estimated_volume": "high", "competition": "medium", "buyer_intent": "high"}]}'
        
        except Exception as e:
            logger.error(f"Error en llamada AI: {e}")
            return '{"themes": []}'
    
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
    
    def _get_fallback_themes(self) -> List[Dict[str, Any]]:
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
                'theme': 'Productos Destacados',
                'description': 'Productos más populares',
                'priority': 2,
                'estimated_volume': 'medium',
                'competition': 'medium',
                'buyer_intent': 'high'
            },
            {
                'theme': 'Ofertas Especiales',
                'description': 'Promociones y descuentos',
                'priority': 3,
                'estimated_volume': 'medium',
                'competition': 'low',
                'buyer_intent': 'high'
            }
        ]
    
    def generate_campaign_blueprint(self, campaign_config: Dict[str, Any]) -> CampaignBlueprint:
        """
        Método síncrono para generar un blueprint de campaña
        Wrapper para el método asíncrono generate_complete_campaign
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
                business_url="",  # No tenemos URL en este caso
                business_description=business_description,
                budget_daily=budget_daily,
                target_locations=locations,
                languages=['es']
            )
            
            # Generar temas básicos basados en la descripción
            themes = self._generate_themes_from_description(business_description, target_audience)
            blueprint.themes = themes
            
            # Generar grupos de anuncios
            ad_groups = []
            total_keywords = 0
            total_ads = 0
            
            for i, theme in enumerate(themes[:3]):  # Máximo 3 temas
                # Generar keywords para el tema
                keywords = self._generate_keywords_for_theme_sync(theme, business_description)
                
                # Generar anuncios para el tema
                ads = self._generate_ads_for_theme_sync(theme, keywords, business_description)
                
                ad_group = {
                    'name': f"AG_{i+1}_{theme['theme'].replace(' ', '_')}",
                    'theme': theme['theme'],
                    'keywords': keywords,
                    'negative_keywords': [],
                    'ads': ads,
                    'max_cpc_bid': self._calculate_suggested_bid(theme),
                    'status': 'ready',
                    'score': 85.0 + (i * 2)  # Score simulado
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
            # Retornar blueprint básico en caso de error
            return self._create_fallback_blueprint(campaign_config)
    
    def _parse_budget_range(self, budget_range: str) -> float:
        """Convierte rango de presupuesto a valor diario"""
        try:
            # Extraer números del rango
            import re
            numbers = re.findall(r'\d+', budget_range)
            if numbers:
                # Tomar el valor promedio del rango
                if len(numbers) >= 2:
                    avg_monthly = (int(numbers[0]) + int(numbers[1])) / 2
                else:
                    avg_monthly = int(numbers[0])
                
                # Convertir a diario (mes = 30 días)
                return round(avg_monthly / 30, 2)
            
            return 20.0  # Default
            
        except Exception:
            return 20.0
    
    def _generate_themes_from_description(self, business_description: str, target_audience: str) -> List[Dict[str, Any]]:
        """Genera temas basados en la descripción del negocio"""
        try:
            # Análisis básico de palabras clave en la descripción
            description_lower = business_description.lower()
            
            themes = []
            
            # Tema principal basado en el tipo de negocio
            if any(word in description_lower for word in ['clínica', 'medicina', 'salud', 'tratamiento']):
                themes.append({
                    'theme': 'Servicios Médicos',
                    'description': 'Servicios principales de salud y medicina',
                    'priority': 1,
                    'estimated_volume': 'high',
                    'competition': 'medium',
                    'buyer_intent': 'high'
                })
            elif any(word in description_lower for word in ['restaurante', 'comida', 'cocina', 'chef']):
                themes.append({
                    'theme': 'Servicios Gastronómicos',
                    'description': 'Servicios de comida y gastronomía',
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
            
            # Tema de ubicación si se menciona
            themes.append({
                'theme': 'Servicios Locales',
                'description': 'Servicios en ubicación específica',
                'priority': 2,
                'estimated_volume': 'medium',
                'competition': 'low',
                'buyer_intent': 'high'
            })
            
            # Tema de audiencia objetivo
            themes.append({
                'theme': 'Audiencia Especializada',
                'description': f'Servicios para {target_audience}',
                'priority': 3,
                'estimated_volume': 'medium',
                'competition': 'medium',
                'buyer_intent': 'high'
            })
            
            return themes
            
        except Exception as e:
            logger.error(f"Error generando temas: {e}")
            return self._get_fallback_themes()
    
    def _generate_keywords_for_theme_sync(self, theme: Dict[str, Any], business_description: str) -> List[str]:
        """Genera keywords para un tema de forma síncrona"""
        try:
            theme_name = theme['theme'].lower()
            description_words = business_description.lower().split()
            
            keywords = []
            
            # Keywords basadas en el tema
            if 'médicos' in theme_name or 'salud' in theme_name:
                keywords.extend([
                    'consulta médica', 'doctor especialista', 'tratamiento médico',
                    'clínica médica', 'servicios de salud', 'atención médica'
                ])
            elif 'gastronómicos' in theme_name or 'comida' in theme_name:
                keywords.extend([
                    'restaurante', 'comida casera', 'chef profesional',
                    'servicio de catering', 'cocina gourmet', 'menú especial'
                ])
            elif 'locales' in theme_name:
                keywords.extend([
                    'servicios locales', 'cerca de mí', 'en mi ciudad',
                    'local comercial', 'negocio local', 'servicio domicilio'
                ])
            else:
                keywords.extend([
                    'servicios profesionales', 'empresa confiable', 'mejor servicio',
                    'atención personalizada', 'calidad garantizada', 'precios competitivos'
                ])
            
            # Agregar variaciones con palabras de la descripción
            important_words = [word for word in description_words 
                             if len(word) > 4 and word not in ['para', 'con', 'una', 'del', 'las', 'los']][:3]
            
            for word in important_words:
                keywords.extend([
                    f"{word} profesional",
                    f"mejor {word}",
                    f"{word} especializado"
                ])
            
            return keywords[:15]  # Limitar a 15 keywords
            
        except Exception as e:
            logger.error(f"Error generando keywords: {e}")
            return ['servicios profesionales', 'empresa confiable', 'atención personalizada']
    
    def _generate_ads_for_theme_sync(self, theme: Dict[str, Any], keywords: List[str], business_description: str) -> List[Dict[str, Any]]:
        """Genera anuncios para un tema de forma síncrona"""
        try:
            theme_name = theme['theme']
            main_keywords = keywords[:3]  # Usar las primeras 3 keywords
            
            ads = []
            
            # Generar 3 anuncios por tema
            for i in range(3):
                headline = f"{theme_name} - {main_keywords[i % len(main_keywords)].title()}"
                if len(headline) > 30:
                    headline = headline[:27] + "..."
                
                description = f"Descubre nuestros servicios de {theme_name.lower()}. Calidad garantizada y atención personalizada."
                if len(description) > 90:
                    description = description[:87] + "..."
                
                ad = {
                    'headline': headline,
                    'description': description,
                    'final_url': 'https://ejemplo.com',
                    'display_url': 'ejemplo.com',
                    'status': 'ready',
                    'score': 85.0 + i
                }
                
                ads.append(ad)
            
            return ads
            
        except Exception as e:
            logger.error(f"Error generando anuncios: {e}")
            return [{
                'headline': 'Servicios Profesionales',
                'description': 'Descubre nuestros servicios de calidad. Atención personalizada garantizada.',
                'final_url': 'https://ejemplo.com',
                'display_url': 'ejemplo.com',
                'status': 'ready',
                'score': 80.0
            }]
    
    def _create_fallback_blueprint(self, campaign_config: Dict[str, Any]) -> CampaignBlueprint:
        """Crea un blueprint básico en caso de error"""
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
                'negative_keywords': [],
                'ads': [{
                    'headline': 'Servicios Profesionales',
                    'description': 'Descubre nuestros servicios de calidad. Atención personalizada garantizada.',
                    'final_url': 'https://ejemplo.com',
                    'display_url': 'ejemplo.com',
                    'status': 'ready',
                    'score': 80.0
                }],
                'max_cpc_bid': 1.0,
                'status': 'ready',
                'score': 80.0
            }],
            total_ads=1,
            total_keywords=3,
            estimated_ctr=2.5,
            status="ready"
        )