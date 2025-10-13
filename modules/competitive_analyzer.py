"""
🔍 COMPETITIVE ANALYZER - Analizador de Competencia
Sistema avanzado de análisis competitivo para anuncios y keywords
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import re
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import Counter, defaultdict
import statistics
import hashlib
from pathlib import Path
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompetitiveAnalyzer:
    """
    Analizador de competencia que proporciona:
    - Análisis de keywords competitivas
    - Estimación de nivel de competencia
    - Análisis de anuncios de competidores
    - Identificación de gaps de mercado
    - Sugerencias de diferenciación
    - Análisis de tendencias
    - Benchmarking competitivo
    - Estrategias de posicionamiento
    """
    
    # =========================================================================
    # DATOS DE COMPETENCIA (Simulados - En producción usar APIs reales)
    # =========================================================================
    
    # Keywords altamente competitivas en el nicho esotérico
    HIGH_COMPETITION_KEYWORDS = {
        'amarres de amor': {'difficulty': 85, 'volume': 12000, 'cpc': 2.50},
        'hechizos de amor': {'difficulty': 80, 'volume': 8500, 'cpc': 2.20},
        'tarot': {'difficulty': 90, 'volume': 45000, 'cpc': 1.80},
        'videncia': {'difficulty': 75, 'volume': 15000, 'cpc': 1.90},
        'brujería': {'difficulty': 70, 'volume': 9000, 'cpc': 1.60},
        'magia blanca': {'difficulty': 65, 'volume': 7500, 'cpc': 1.70},
        'rituales de amor': {'difficulty': 60, 'volume': 5000, 'cpc': 2.00},
        'amarres efectivos': {'difficulty': 75, 'volume': 3500, 'cpc': 2.30},
        'lectura de tarot': {'difficulty': 82, 'volume': 18000, 'cpc': 1.75},
        'consulta espiritual': {'difficulty': 55, 'volume': 4000, 'cpc': 1.85}
    }
    
    # Competidores conocidos (simulado)
    KNOWN_COMPETITORS = [
        {
            'name': 'Competidor A',
            'domain': 'competitor-a.com',
            'strength': 'high',
            'focus': ['amarres', 'hechizos', 'tarot'],
            'estimated_budget': 5000,
            'ad_count': 25
        },
        {
            'name': 'Competidor B',
            'domain': 'competitor-b.com',
            'strength': 'medium',
            'focus': ['videncia', 'tarot', 'consultas'],
            'estimated_budget': 2000,
            'ad_count': 15
        },
        {
            'name': 'Competidor C',
            'domain': 'competitor-c.com',
            'strength': 'low',
            'focus': ['brujería', 'rituales'],
            'estimated_budget': 500,
            'ad_count': 8
        }
    ]
    
    # Patrones comunes en anuncios de competidores
    COMPETITOR_AD_PATTERNS = {
        'urgency': ['ahora', 'hoy', 'inmediato', 'ya', 'urgente', 'rápido'],
        'guarantees': ['garantizado', 'garantía', '100%', 'efectivo', 'seguro'],
        'experience': ['experto', 'profesional', 'años', 'experiencia', 'certificado'],
        'price': ['gratis', 'consulta gratis', 'económico', 'precio', 'oferta'],
        'results': ['resultados', 'funciona', 'efectivo', 'éxito', 'comprobado'],
        'emotion': ['amor', 'felicidad', 'paz', 'armonía', 'bienestar']
    }
    
    # Niveles de dificultad
    DIFFICULTY_LEVELS = {
        'very_easy': (0, 30),
        'easy': (31, 50),
        'medium': (51, 70),
        'hard': (71, 85),
        'very_hard': (86, 100)
    }
    
    def __init__(
        self,
        business_type: str = 'esoteric',
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Inicializa el analizador competitivo.
        
        Args:
            business_type: Tipo de negocio
            cache_enabled: Habilitar caché
            cache_dir: Directorio de caché
        """
        self.business_type = business_type
        self.cache_enabled = cache_enabled
        
        # Configurar caché
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / "data" / "competitive_cache"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado
        self.analysis_history: List[Dict[str, Any]] = []
        self.cache: Dict[str, Any] = {}
        
        # Estadísticas
        self.stats = {
            'total_analyses': 0,
            'keywords_analyzed': 0,
            'competitors_identified': 0,
            'gaps_found': 0
        }
        
        logger.info(f"✅ CompetitiveAnalyzer inicializado")
        logger.info(f"   - Business type: {business_type}")
        logger.info(f"   - Cache: {'enabled' if cache_enabled else 'disabled'}")
    
    # =========================================================================
    # ANÁLISIS PRINCIPAL
    # =========================================================================
    
    def analyze(
        self,
        keywords: List[str],
        your_ad: Optional[Dict[str, Any]] = None,
        deep_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Realiza análisis competitivo completo.
        
        Args:
            keywords: Lista de keywords a analizar
            your_ad: Tu anuncio (opcional para comparación)
            deep_analysis: Análisis profundo (más lento pero más completo)
        
        Returns:
            Diccionario con análisis competitivo completo
        """
        analysis_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🔍 Iniciando análisis competitivo: {analysis_id}")
        logger.info(f"   - Keywords: {len(keywords)}")
        logger.info(f"   - Deep analysis: {deep_analysis}")
        
        # 1. Analizar keywords
        keyword_analysis = self._analyze_keywords(keywords)
        
        # 2. Identificar competidores
        competitor_analysis = self._identify_competitors(keywords)
        
        # 3. Analizar anuncios de competidores
        competitor_ads = self._analyze_competitor_ads(keywords) if deep_analysis else {}
        
        # 4. Identificar gaps de mercado
        market_gaps = self._identify_market_gaps(keywords, competitor_ads)
        
        # 5. Generar estrategia de diferenciación
        differentiation_strategy = self._generate_differentiation_strategy(
            keywords,
            competitor_analysis,
            market_gaps
        )
        
        # 6. Comparar con tu anuncio (si se proporciona)
        your_position = None
        if your_ad:
            your_position = self._analyze_your_position(
                your_ad,
                competitor_ads,
                keyword_analysis
            )
        
        # 7. Generar recomendaciones
        recommendations = self._generate_competitive_recommendations(
            keyword_analysis,
            competitor_analysis,
            market_gaps,
            your_position
        )
        
        # 8. Calcular score competitivo
        competitive_score = self._calculate_competitive_score(
            keyword_analysis,
            market_gaps,
            your_position
        )
        
        # Construir resultado
        result = {
            'analysis_id': analysis_id,
            'timestamp': datetime.now().isoformat(),
            'keywords': keywords,
            'keyword_analysis': keyword_analysis,
            'competitor_analysis': competitor_analysis,
            'competitor_ads': competitor_ads,
            'market_gaps': market_gaps,
            'differentiation_strategy': differentiation_strategy,
            'your_position': your_position,
            'competitive_score': competitive_score,
            'recommendations': recommendations,
            'summary': self._generate_summary(
                keyword_analysis,
                competitor_analysis,
                market_gaps
            )
        }
        
        # Guardar en historial
        self.analysis_history.append(result)
        
        # Actualizar estadísticas
        self.stats['total_analyses'] += 1
        self.stats['keywords_analyzed'] += len(keywords)
        self.stats['competitors_identified'] += len(competitor_analysis.get('competitors', []))
        self.stats['gaps_found'] += len(market_gaps.get('opportunities', []))
        
        logger.info(f"✅ Análisis competitivo completado: {analysis_id}")
        logger.info(f"   - Nivel de competencia: {keyword_analysis['overall_difficulty']}")
        logger.info(f"   - Competidores identificados: {len(competitor_analysis.get('competitors', []))}")
        logger.info(f"   - Gaps encontrados: {len(market_gaps.get('opportunities', []))}")
        
        return result
    
    # =========================================================================
    # ANÁLISIS DE KEYWORDS
    # =========================================================================
    
    def _analyze_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Analiza nivel de competencia de keywords.
        
        Args:
            keywords: Lista de keywords
        
        Returns:
            Análisis de competencia por keyword
        """
        keyword_data = []
        total_difficulty = 0
        total_volume = 0
        total_cpc = 0
        
        for keyword in keywords:
            kw_lower = keyword.lower()
            
            # Buscar en base de datos de competencia
            if kw_lower in self.HIGH_COMPETITION_KEYWORDS:
                data = self.HIGH_COMPETITION_KEYWORDS[kw_lower]
                difficulty = data['difficulty']
                volume = data['volume']
                cpc = data['cpc']
            else:
                # Estimar competencia basándose en palabras
                difficulty = self._estimate_keyword_difficulty(keyword)
                volume = self._estimate_search_volume(keyword)
                cpc = self._estimate_cpc_for_keyword(keyword)
            
            # Calcular oportunidad
            opportunity_score = self._calculate_opportunity_score(
                difficulty,
                volume,
                cpc
            )
            
            keyword_info = {
                'keyword': keyword,
                'difficulty': difficulty,
                'difficulty_level': self._difficulty_to_level(difficulty),
                'search_volume': volume,
                'estimated_cpc': round(cpc, 2),
                'opportunity_score': round(opportunity_score, 1),
                'recommendation': self._get_keyword_recommendation(
                    difficulty,
                    volume,
                    opportunity_score
                )
            }
            
            keyword_data.append(keyword_info)
            
            total_difficulty += difficulty
            total_volume += volume
            total_cpc += cpc
        
        # Calcular promedios
        count = len(keywords)
        avg_difficulty = total_difficulty / count if count > 0 else 0
        avg_volume = total_volume / count if count > 0 else 0
        avg_cpc = total_cpc / count if count > 0 else 0
        
        # Clasificar keywords por dificultad
        easy_keywords = [k for k in keyword_data if k['difficulty'] < 50]
        medium_keywords = [k for k in keyword_data if 50 <= k['difficulty'] < 70]
        hard_keywords = [k for k in keyword_data if k['difficulty'] >= 70]
        
        # Identificar mejores oportunidades
        best_opportunities = sorted(
            keyword_data,
            key=lambda x: x['opportunity_score'],
            reverse=True
        )[:5]
        
        analysis = {
            'total_keywords': count,
            'keyword_details': keyword_data,
            'overall_difficulty': round(avg_difficulty, 1),
            'overall_difficulty_level': self._difficulty_to_level(avg_difficulty),
            'avg_search_volume': int(avg_volume),
            'avg_cpc': round(avg_cpc, 2),
            'distribution': {
                'easy': len(easy_keywords),
                'medium': len(medium_keywords),
                'hard': len(hard_keywords)
            },
            'best_opportunities': best_opportunities,
            'recommendations': self._get_keyword_strategy_recommendations(
                avg_difficulty,
                easy_keywords,
                hard_keywords
            )
        }
        
        return analysis
    
    def _estimate_keyword_difficulty(self, keyword: str) -> int:
        """Estima dificultad de keyword basándose en características."""
        difficulty = 50  # Base
        
        keyword_lower = keyword.lower()
        
        # Keywords muy competitivas
        high_comp_words = ['amor', 'dinero', 'trabajo', 'suerte', 'tarot', 'videncia']
        if any(word in keyword_lower for word in high_comp_words):
            difficulty += 20
        
        # Long-tail keywords (menos competitivas)
        word_count = len(keyword.split())
        if word_count >= 4:
            difficulty -= 15
        elif word_count >= 3:
            difficulty -= 10
        
        # Keywords con calificadores (menos competitivas)
        qualifiers = ['profesional', 'efectivo', 'rápido', 'garantizado', 'certificado']
        if any(qual in keyword_lower for qual in qualifiers):
            difficulty -= 5
        
        # Limitar rango
        difficulty = max(10, min(95, difficulty))
        
        return difficulty
    
    def _estimate_search_volume(self, keyword: str) -> int:
        """Estima volumen de búsqueda."""
        base_volume = 1000
        
        keyword_lower = keyword.lower()
        
        # Keywords populares
        popular_words = ['amor', 'tarot', 'videncia']
        if any(word in keyword_lower for word in popular_words):
            base_volume *= 5
        
        # Long-tail (menor volumen)
        word_count = len(keyword.split())
        if word_count >= 4:
            base_volume = int(base_volume * 0.3)
        elif word_count >= 3:
            base_volume = int(base_volume * 0.5)
        
        return base_volume
    
    def _estimate_cpc_for_keyword(self, keyword: str) -> float:
        """Estima CPC de keyword."""
        base_cpc = 1.50
        
        keyword_lower = keyword.lower()
        
        # Keywords de alto valor
        high_value = ['consulta', 'servicio', 'profesional']
        if any(word in keyword_lower for word in high_value):
            base_cpc *= 1.3
        
        # Long-tail (menor CPC)
        word_count = len(keyword.split())
        if word_count >= 3:
            base_cpc *= 0.8
        
        return base_cpc
    
    def _calculate_opportunity_score(
        self,
        difficulty: int,
        volume: int,
        cpc: float
    ) -> float:
        """
        Calcula score de oportunidad (0-100).
        
        Alta oportunidad = Alto volumen, baja dificultad, CPC razonable
        """
        # Normalizar valores
        difficulty_score = (100 - difficulty) / 100  # Invertir: baja dificultad = mejor
        volume_score = min(volume / 10000, 1.0)  # Normalizar a 0-1
        cpc_score = min(cpc / 3.0, 1.0)  # CPC moderado es mejor
        
        # Ponderación
        opportunity = (
            difficulty_score * 0.4 +  # 40% peso en dificultad
            volume_score * 0.4 +       # 40% peso en volumen
            cpc_score * 0.2            # 20% peso en CPC
        ) * 100
        
        return opportunity
    
    def _difficulty_to_level(self, difficulty: float) -> str:
        """Convierte dificultad a nivel textual."""
        for level, (min_val, max_val) in self.DIFFICULTY_LEVELS.items():
            if min_val <= difficulty <= max_val:
                return level.replace('_', ' ').title()
        return 'Unknown'
    
    def _get_keyword_recommendation(
        self,
        difficulty: int,
        volume: int,
        opportunity_score: float
    ) -> str:
        """Genera recomendación para keyword."""
        if opportunity_score >= 70:
            return "Excelente oportunidad - Alta prioridad"
        elif opportunity_score >= 50:
            return "Buena oportunidad - Considerar"
        elif difficulty > 80:
            return "Muy competitiva - Requiere alto presupuesto"
        elif volume < 500:
            return "Bajo volumen - Nicho específico"
        else:
            return "Oportunidad moderada - Evaluar"
    
    def _get_keyword_strategy_recommendations(
        self,
        avg_difficulty: float,
        easy_keywords: List[Dict],
        hard_keywords: List[Dict]
    ) -> List[str]:
        """Genera recomendaciones estratégicas de keywords."""
        recommendations = []
        
        if avg_difficulty > 75:
            recommendations.append(
                "🎯 Competencia muy alta: Considera usar long-tail keywords más específicas"
            )
            recommendations.append(
                "💰 Prepara presupuesto mayor para competir efectivamente"
            )
        
        if len(easy_keywords) > 0:
            recommendations.append(
                f"✅ Enfócate primero en las {len(easy_keywords)} keywords de baja competencia"
            )
        
        if len(hard_keywords) > len(easy_keywords):
            recommendations.append(
                "⚠️ Mayoría de keywords son competitivas: Diferénciate con propuesta única"
            )
        
        if avg_difficulty < 50:
            recommendations.append(
                "🚀 Oportunidad: Baja competencia general, puedes dominar rápidamente"
            )
        
        return recommendations
    
    # =========================================================================
    # IDENTIFICACIÓN DE COMPETIDORES
    # =========================================================================
    
    def _identify_competitors(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Identifica competidores principales.
        
        Args:
            keywords: Lista de keywords
        
        Returns:
            Análisis de competidores
        """
        # En producción, esto consultaría APIs reales (Google Ads, SEMrush, etc.)
        # Por ahora, usar datos simulados
        
        relevant_competitors = []
        
        for competitor in self.KNOWN_COMPETITORS:
            # Calcular relevancia basándose en keywords
            relevance_score = 0
            matching_keywords = []
            
            for keyword in keywords:
                kw_lower = keyword.lower()
                for focus_area in competitor['focus']:
                    if focus_area in kw_lower or kw_lower in focus_area:
                        relevance_score += 1
                        matching_keywords.append(keyword)
                        break
            
            if relevance_score > 0:
                competitor_info = {
                    **competitor,
                    'relevance_score': relevance_score,
                    'matching_keywords': list(set(matching_keywords)),
                    'threat_level': self._calculate_threat_level(
                        competitor['strength'],
                        relevance_score,
                        competitor['estimated_budget']
                    )
                }
                relevant_competitors.append(competitor_info)
        
        # Ordenar por relevancia
        relevant_competitors.sort(
            key=lambda x: x['relevance_score'],
            reverse=True
        )
        
        # Calcular competencia total
        total_budget = sum(c['estimated_budget'] for c in relevant_competitors)
        total_ads = sum(c['ad_count'] for c in relevant_competitors)
        
        # Análisis de fortalezas competitivas
        strength_distribution = Counter([c['strength'] for c in relevant_competitors])
        
        analysis = {
            'total_competitors': len(relevant_competitors),
            'competitors': relevant_competitors,
            'total_estimated_budget': total_budget,
            'total_ads': total_ads,
            'strength_distribution': dict(strength_distribution),
            'average_budget': round(total_budget / len(relevant_competitors)) if relevant_competitors else 0,
            'top_competitor': relevant_competitors[0] if relevant_competitors else None,
            'market_saturation': self._calculate_market_saturation(
                len(relevant_competitors),
                total_budget
            )
        }
        
        return analysis
    
    def _calculate_threat_level(
        self,
        strength: str,
        relevance: int,
        budget: int
    ) -> str:
        """Calcula nivel de amenaza de competidor."""
        threat_score = 0
        
        # Peso por fortaleza
        strength_weights = {'high': 3, 'medium': 2, 'low': 1}
        threat_score += strength_weights.get(strength, 1)
        
        # Peso por relevancia
        threat_score += min(relevance, 3)
        
        # Peso por presupuesto
        if budget > 3000:
            threat_score += 3
        elif budget > 1000:
            threat_score += 2
        else:
            threat_score += 1
        
        # Clasificar
        if threat_score >= 8:
            return 'Very High'
        elif threat_score >= 6:
            return 'High'
        elif threat_score >= 4:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_market_saturation(
        self,
        competitor_count: int,
        total_budget: int
    ) -> Dict[str, Any]:
        """Calcula nivel de saturación del mercado."""
        # Clasificar saturación
        if competitor_count >= 10 or total_budget >= 20000:
            level = 'Very High'
            description = "Mercado altamente saturado, difícil entrar"
        elif competitor_count >= 5 or total_budget >= 10000:
            level = 'High'
            description = "Mercado competitivo, requiere estrategia sólida"
        elif competitor_count >= 3 or total_budget >= 5000:
            level = 'Medium'
            description = "Competencia moderada, oportunidades disponibles"
        else:
            level = 'Low'
            description = "Mercado poco saturado, excelente oportunidad"
        
        return {
            'level': level,
            'description': description,
            'competitor_count': competitor_count,
            'estimated_total_spend': total_budget
        }
    
    # =========================================================================
    # ANÁLISIS DE ANUNCIOS DE COMPETIDORES
    # =========================================================================
    
    def _analyze_competitor_ads(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Analiza anuncios de competidores (simulado).
        
        En producción, esto scrapearía anuncios reales de Google.
        """
        # Simular análisis de anuncios
        pattern_frequency = defaultdict(int)
        
        # Contar frecuencia de patrones
        for keyword in keywords:
            kw_lower = keyword.lower()
            
            for pattern_type, words in self.COMPETITOR_AD_PATTERNS.items():
                if any(word in kw_lower for word in words):
                    pattern_frequency[pattern_type] += 1
        
        # Identificar patrones más usados
        most_common_patterns = sorted(
            pattern_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Generar insights
        insights = []
        
        if pattern_frequency['urgency'] > len(keywords) * 0.5:
            insights.append(
                "Los competidores usan mucho lenguaje de urgencia"
            )
        
        if pattern_frequency['guarantees'] > len(keywords) * 0.4:
            insights.append(
                "Mayoría de competidores ofrecen garantías"
            )
        
        if pattern_frequency['price'] > 2:
            insights.append(
                "Competidores compiten en precio (consultas gratis)"
            )
        
        analysis = {
            'patterns_detected': dict(pattern_frequency),
            'most_common_patterns': [
                {'pattern': p, 'frequency': f}
                for p, f in most_common_patterns
            ],
            'insights': insights,
            'estimated_ad_count': len(keywords) * 3,  # Simular
            'common_themes': self._extract_common_themes(pattern_frequency)
        }
        
        return analysis
    
    def _extract_common_themes(
        self,
        pattern_frequency: Dict[str, int]
    ) -> List[str]:
        """Extrae temas comunes de patrones."""
        themes = []
        
        if pattern_frequency.get('urgency', 0) > 3:
            themes.append("Urgencia y rapidez")
        
        if pattern_frequency.get('guarantees', 0) > 2:
            themes.append("Garantías y efectividad")
        
        if pattern_frequency.get('experience', 0) > 2:
            themes.append("Experiencia y profesionalismo")
        
        if pattern_frequency.get('emotion', 0) > 3:
            themes.append("Conexión emocional")
        
        return themes
    
    # =========================================================================
    # IDENTIFICACIÓN DE GAPS DE MERCADO
    # =========================================================================
    
    def _identify_market_gaps(
        self,
        keywords: List[str],
        competitor_ads: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identifica oportunidades no explotadas en el mercado.
        
        Args:
            keywords: Keywords analizadas
            competitor_ads: Análisis de anuncios de competidores
        
        Returns:
            Gaps y oportunidades identificadas
        """
        opportunities = []
        underserved_areas = []
        
        # Analizar patrones menos usados
        if competitor_ads:
            patterns = competitor_ads.get('patterns_detected', {})
            total = sum(patterns.values()) if patterns else 1
            
            for pattern_type, words in self.COMPETITOR_AD_PATTERNS.items():
                frequency = patterns.get(pattern_type, 0)
                usage_rate = (frequency / total * 100) if total > 0 else 0
                
                if usage_rate < 20:  # Menos del 20% de uso
                    opportunities.append({
                        'type': 'underused_pattern',
                        'pattern': pattern_type,
                        'current_usage': round(usage_rate, 1),
                        'recommendation': f"Pocos competidores usan {pattern_type}, oportunidad para destacar",
                        'priority': 'high' if usage_rate < 10 else 'medium'
                    })
        
        # Buscar keywords no cubiertas
        # Long-tail keywords específicas
        long_tail_opportunities = [
            kw for kw in keywords
            if len(kw.split()) >= 3
        ]
        
        if long_tail_opportunities:
            opportunities.append({
                'type': 'long_tail_keywords',
                'keywords': long_tail_opportunities,
                'count': len(long_tail_opportunities),
                'recommendation': "Keywords específicas con baja competencia",
                'priority': 'high'
            })
        
        # Identificar áreas sub-atendidas
        esoteric_services = [
            'limpieza espiritual',
            'amarres de pareja',
            'rituales de prosperidad',
            'lectura de cartas',
            'consulta astrológica'
        ]
        
        for service in esoteric_services:
            if not any(service.lower() in kw.lower() for kw in keywords):
                underserved_areas.append({
                    'service': service,
                    'recommendation': f"Considera expandir a {service}"
                })
        
        # Calcular potencial de cada gap
        for opp in opportunities:
            opp['potential_score'] = self._calculate_gap_potential(opp)
        
        # Ordenar por potencial
        opportunities.sort(
            key=lambda x: x.get('potential_score', 0),
            reverse=True
        )
        
        gaps = {
            'total_opportunities': len(opportunities),
            'opportunities': opportunities,
            'underserved_areas': underserved_areas[:5],  # Top 5
            'market_potential': self._assess_market_potential(
                len(opportunities),
                len(underserved_areas)
            )
        }
        
        return gaps
    
    def _calculate_gap_potential(self, opportunity: Dict[str, Any]) -> float:
        """Calcula potencial de un gap de mercado."""
        score = 50.0  # Base
        
        opp_type = opportunity.get('type')
        priority = opportunity.get('priority', 'medium')
        
        # Bonus por prioridad
        if priority == 'high':
            score += 30
        elif priority == 'medium':
            score += 15
        
        # Bonus por tipo
        if opp_type == 'underused_pattern':
            usage = opportunity.get('current_usage', 50)
            score += (100 - usage) * 0.2
        elif opp_type == 'long_tail_keywords':
            count = opportunity.get('count', 0)
            score += min(count * 5, 30)
        
        return min(100, score)
    
    def _assess_market_potential(
        self,
        opportunity_count: int,
        underserved_count: int
    ) -> Dict[str, Any]:
        """Evalúa potencial general del mercado."""
        total_potential = opportunity_count + underserved_count
        
        if total_potential >= 10:
            level = 'Very High'
            description = "Excelente potencial, muchas oportunidades sin explotar"
        elif total_potential >= 5:
            level = 'High'
            description = "Buen potencial, varias oportunidades disponibles"
        elif total_potential >= 3:
            level = 'Medium'
            description = "Potencial moderado, algunas oportunidades"
        else:
            level = 'Low'
            description = "Mercado saturado, pocas oportunidades nuevas"
        
        return {
            'level': level,
            'description': description,
            'opportunity_count': opportunity_count,
            'underserved_areas': underserved_count
        }
    
    # =========================================================================
    # ESTRATEGIA DE DIFERENCIACIÓN
    # =========================================================================
    
    def _generate_differentiation_strategy(
        self,
        keywords: List[str],
        competitor_analysis: Dict[str, Any],
        market_gaps: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera estrategia para diferenciarse de competidores.
        
        Args:
            keywords: Keywords analizadas
            competitor_analysis: Análisis de competidores
            market_gaps: Gaps identificados
        
        Returns:
            Estrategia de diferenciación
        """
        strategies = []
        
        # Estrategia basada en gaps
        opportunities = market_gaps.get('opportunities', [])
        if opportunities:
            top_opportunity = opportunities[0]
            strategies.append({
                'strategy': 'Explotar gap de mercado',
                'description': top_opportunity.get('recommendation', ''),
                'action': f"Enfócate en {top_opportunity.get('type', 'oportunidad identificada')}",
                'priority': top_opportunity.get('priority', 'medium')
            })
        
        # Estrategia basada en competencia
        market_saturation = competitor_analysis.get('market_saturation', {})
        saturation_level = market_saturation.get('level', 'Medium')
        
        if saturation_level in ['Very High', 'High']:
            strategies.append({
                'strategy': 'Nicho específico',
                'description': 'Mercado saturado, especializarse es clave',
                'action': 'Enfócate en un sub-nicho muy específico (ej: solo amarres de pareja)',
                'priority': 'high'
            })
        else:
            strategies.append({
                'strategy': 'Expansión agresiva',
                'description': 'Baja saturación, oportunidad para capturar mercado',
                'action': 'Aumenta presupuesto y cubre múltiples keywords',
                'priority': 'high'
            })
        
        # Estrategia de propuesta de valor
        strategies.append({
            'strategy': 'Propuesta única de valor',
            'description': 'Diferénciate con algo que competidores no ofrecen',
            'action': 'Ej: "Primera consulta gratis + garantía 30 días"',
            'priority': 'high'
        })
        
        # Estrategia de contenido
        strategies.append({
            'strategy': 'Marketing de contenido',
            'description': 'Construye autoridad con contenido de valor',
            'action': 'Blog, videos, testimonios, casos de éxito',
            'priority': 'medium'
        })
        
        differentiation = {
            'strategies': strategies,
            'quick_wins': self._identify_quick_wins(market_gaps),
            'long_term_plays': self._identify_long_term_strategies(
                competitor_analysis
            ),
            'key_message': self._generate_key_differentiation_message(
                strategies
            )
        }
        
        return differentiation
    
    def _identify_quick_wins(self, market_gaps: Dict[str, Any]) -> List[str]:
        """Identifica victorias rápidas."""
        quick_wins = []
        
        opportunities = market_gaps.get('opportunities', [])
        
        for opp in opportunities[:3]:
            if opp.get('priority') == 'high':
                quick_wins.append(
                    f"✅ {opp.get('recommendation', 'Implementar oportunidad detectada')}"
                )
        
        if not quick_wins:
            quick_wins = [
                "✅ Optimiza anuncios con keywords long-tail",
                "✅ Agrega garantías si competidores no las tienen",
                "✅ Destaca experiencia/certificaciones"
            ]
        
        return quick_wins
    
    def _identify_long_term_strategies(
        self,
        competitor_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identifica estrategias a largo plazo."""
        strategies = [
            "🎯 Construir marca reconocible en el nicho",
            "📈 Desarrollar base de clientes leales con programa de referidos",
            "🌐 Expandir presencia digital (SEO, redes sociales)"
        ]
        
        top_competitor = competitor_analysis.get('top_competitor')
        if top_competitor:
            strategies.append(
                f"🏆 Superar a {top_competitor['name']} en Quality Score y CTR"
            )
        
        return strategies
    
    def _generate_key_differentiation_message(
        self,
        strategies: List[Dict[str, Any]]
    ) -> str:
        """Genera mensaje clave de diferenciación."""
        if not strategies:
            return "Enfócate en lo que te hace único"
        
        top_strategy = strategies[0]
        
        return f"Tu ventaja competitiva: {top_strategy['description']}"
    
    # =========================================================================
    # ANÁLISIS DE TU POSICIÓN
    # =========================================================================
    
    def _analyze_your_position(
        self,
        your_ad: Dict[str, Any],
        competitor_ads: Dict[str, Any],
        keyword_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analiza tu posición frente a competidores.
        
        Args:
            your_ad: Tu anuncio
            competitor_ads: Anuncios de competidores
            keyword_analysis: Análisis de keywords
        
        Returns:
            Análisis de tu posición competitiva
        """
        # Analizar tu anuncio
        your_headlines = your_ad.get('headlines', [])
        your_descriptions = your_ad.get('descriptions', [])
        your_text = ' '.join(your_headlines + your_descriptions).lower()
        
        # Detectar patrones en tu anuncio
        your_patterns = {}
        for pattern_type, words in self.COMPETITOR_AD_PATTERNS.items():
            count = sum(1 for word in words if word in your_text)
            your_patterns[pattern_type] = count
        
        # Comparar con competidores
        competitor_patterns = competitor_ads.get('patterns_detected', {})
        
        strengths = []
        weaknesses = []
        
        for pattern_type in self.COMPETITOR_AD_PATTERNS.keys():
            your_count = your_patterns.get(pattern_type, 0)
            comp_count = competitor_patterns.get(pattern_type, 0)
            
            if your_count > comp_count:
                strengths.append(f"Más {pattern_type} que competidores")
            elif your_count < comp_count and comp_count > 2:
                weaknesses.append(f"Menos {pattern_type} que competidores")
        
        # Calcular score de posicionamiento
        positioning_score = self._calculate_positioning_score(
            your_patterns,
            competitor_patterns,
            len(strengths),
            len(weaknesses)
        )
        
        position = {
            'positioning_score': round(positioning_score, 1),
            'positioning_level': self._score_to_positioning_level(positioning_score),
            'your_patterns': your_patterns,
            'competitor_average': competitor_patterns,
            'strengths': strengths[:5],
            'weaknesses': weaknesses[:5],
            'improvement_suggestions': self._generate_improvement_suggestions(
                weaknesses,
                your_patterns
            )
        }
        
        return position
    
    def _calculate_positioning_score(
        self,
        your_patterns: Dict[str, int],
        competitor_patterns: Dict[str, int],
        strength_count: int,
        weakness_count: int
    ) -> float:
        """Calcula score de posicionamiento (0-100)."""
        score = 50.0  # Base
        
        # Bonus por fortalezas
        score += strength_count * 8
        
        # Penalización por debilidades
        score -= weakness_count * 5
        
        # Normalizar
        score = max(0, min(100, score))
        
        return score
    
    def _score_to_positioning_level(self, score: float) -> str:
        """Convierte score a nivel de posicionamiento."""
        if score >= 80:
            return 'Líder del mercado'
        elif score >= 65:
            return 'Fuerte posición'
        elif score >= 50:
            return 'Posición competitiva'
        elif score >= 35:
            return 'Necesita mejoras'
        else:
            return 'Posición débil'
    
    def _generate_improvement_suggestions(
        self,
        weaknesses: List[str],
        your_patterns: Dict[str, int]
    ) -> List[str]:
        """Genera sugerencias de mejora."""
        suggestions = []
        
        for weakness in weaknesses[:3]:
            pattern_type = weakness.split()[1]  # Extraer tipo
            suggestions.append(
                f"Agrega más elementos de {pattern_type} a tu anuncio"
            )
        
        if not suggestions:
            suggestions = [
                "Mantén tu estrategia actual, está funcionando bien"
            ]
        
        return suggestions
    
    # =========================================================================
    # RECOMENDACIONES
    # =========================================================================
    
    def _generate_competitive_recommendations(
        self,
        keyword_analysis: Dict[str, Any],
        competitor_analysis: Dict[str, Any],
        market_gaps: Dict[str, Any],
        your_position: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Genera recomendaciones competitivas."""
        recommendations = []
        
        # Basadas en keywords
        difficulty = keyword_analysis.get('overall_difficulty', 50)
        if difficulty > 75:
            recommendations.append({
                'category': 'Keywords',
                'priority': 'high',
                'recommendation': 'Competencia muy alta: Usa long-tail keywords',
                'expected_impact': 'Reducción de CPC hasta 40%'
            })
        
        # Basadas en competidores
        market_sat = competitor_analysis.get('market_saturation', {})
        if market_sat.get('level') in ['Very High', 'High']:
            recommendations.append({
                'category': 'Estrategia',
                'priority': 'high',
                'recommendation': 'Mercado saturado: Diferénciate con propuesta única',
                'expected_impact': 'Mayor tasa de conversión'
            })
        
        # Basadas en gaps
        gap_count = len(market_gaps.get('opportunities', []))
        if gap_count > 0:
            recommendations.append({
                'category': 'Oportunidades',
                'priority': 'medium',
                'recommendation': f'Explota {gap_count} gap(s) de mercado identificado(s)',
                'expected_impact': 'Ventaja competitiva temprana'
            })
        
        # Basadas en tu posición
        if your_position:
            pos_score = your_position.get('positioning_score', 50)
            if pos_score < 50:
                recommendations.append({
                    'category': 'Posicionamiento',
                    'priority': 'high',
                    'recommendation': 'Mejora tu anuncio según debilidades detectadas',
                    'expected_impact': '+20-30 puntos en positioning score'
                })
        
        return recommendations
    
    def _calculate_competitive_score(
        self,
        keyword_analysis: Dict[str, Any],
        market_gaps: Dict[str, Any],
        your_position: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calcula score competitivo general."""
        score = 50.0  # Base
        
        # Factor keyword difficulty (invertido)
        difficulty = keyword_analysis.get('overall_difficulty', 50)
        score += (100 - difficulty) * 0.2
        
        # Factor gaps
        gap_potential = market_gaps.get('market_potential', {})
        if gap_potential.get('level') == 'Very High':
            score += 20
        elif gap_potential.get('level') == 'High':
            score += 10
        
        # Factor posicionamiento
        if your_position:
            pos_score = your_position.get('positioning_score', 50)
            score = (score * 0.6) + (pos_score * 0.4)
        
        # Normalizar
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 1),
            'level': self._score_to_competitive_level(score),
            'interpretation': self._interpret_competitive_score(score)
        }
    
    def _score_to_competitive_level(self, score: float) -> str:
        """Convierte score a nivel competitivo."""
        if score >= 80:
            return 'Dominante'
        elif score >= 65:
            return 'Fuerte'
        elif score >= 50:
            return 'Competitivo'
        elif score >= 35:
            return 'Emergente'
        else:
            return 'Desafiante'
    
    def _interpret_competitive_score(self, score: float) -> str:
        """Interpreta el score competitivo."""
        if score >= 80:
            return "Posición dominante en el mercado, mantén la ventaja"
        elif score >= 65:
            return "Fuerte posición competitiva, sigue optimizando"
        elif score >= 50:
            return "Posición sólida, busca diferenciarte más"
        elif score >= 35:
            return "Necesitas mejorar para ser más competitivo"
        else:
            return "Posición desafiante, requiere estrategia agresiva"
    
    def _generate_summary(
        self,
        keyword_analysis: Dict[str, Any],
        competitor_analysis: Dict[str, Any],
        market_gaps: Dict[str, Any]
    ) -> str:
        """Genera resumen ejecutivo del análisis."""
        difficulty_level = keyword_analysis.get('overall_difficulty_level', 'Medium')
        competitor_count = competitor_analysis.get('total_competitors', 0)
        gap_count = len(market_gaps.get('opportunities', []))
        
        summary = f"""**Resumen Ejecutivo:**

🎯 **Competencia:** {difficulty_level} ({keyword_analysis.get('overall_difficulty', 0):.1f}/100)
👥 **Competidores activos:** {competitor_count}
💡 **Oportunidades identificadas:** {gap_count}

**Veredicto:** {market_gaps.get('market_potential', {}).get('description', 'Evaluar oportunidades')}"""
        
        return summary
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del analizador."""
        return {
            **self.stats,
            'analysis_history_size': len(self.analysis_history)
        }
    
    def get_analysis_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene historial de análisis."""
        history = self.analysis_history.copy()
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def export_analysis(
        self,
        analysis: Dict[str, Any],
        format: str = 'json'
    ) -> str:
        """Exporta análisis."""
        if format == 'json':
            return json.dumps(analysis, indent=2, ensure_ascii=False)
        
        return str(analysis)


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_competitive_analyzer(
    business_type: str = 'esoteric',
    cache_enabled: bool = True
) -> CompetitiveAnalyzer:
    """
    Factory function para crear analizador.
    
    Args:
        business_type: Tipo de negocio
        cache_enabled: Habilitar caché
    
    Returns:
        Instancia de CompetitiveAnalyzer
    """
    return CompetitiveAnalyzer(
        business_type=business_type,
        cache_enabled=cache_enabled
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🔍 COMPETITIVE ANALYZER - Ejemplo de Uso")
    print("="*60)
    
    # Crear analizador
    analyzer = CompetitiveAnalyzer(business_type='esoteric')
    
    # Keywords de ejemplo
    keywords = [
        'amarres de amor',
        'hechizos efectivos',
        'tarot profesional',
        'limpieza espiritual',
        'brujería blanca'
    ]
    
    # Tu anuncio (opcional)
    your_ad = {
        'headlines': [
            'Amarres de Amor Garantizados',
            'Brujería Profesional Certificada',
            'Resultados en 24 Horas'
        ],
        'descriptions': [
            'Amarres efectivos con garantía total. Consulta gratis.',
            'Bruja experta con 15 años de experiencia.'
        ]
    }
    
    print(f"\n📊 Analizando {len(keywords)} keywords...")
    print(f"Keywords: {', '.join(keywords)}")
    
    # Realizar análisis
    result = analyzer.analyze(
        keywords=keywords,
        your_ad=your_ad,
        deep_analysis=True
    )
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*60)
    
    print(f"\n{result['summary']}")
    
    # Keywords
    print("\n📊 ANÁLISIS DE KEYWORDS:")
    kw_analysis = result['keyword_analysis']
    print(f"   Dificultad promedio: {kw_analysis['overall_difficulty']:.1f}/100")
    print(f"   Nivel: {kw_analysis['overall_difficulty_level']}")
    print(f"   Volumen promedio: {kw_analysis['avg_search_volume']:,}")
    print(f"   CPC promedio: ${kw_analysis['avg_cpc']:.2f}")
    
    print(f"\n🎯 Mejores oportunidades:")
    for i, opp in enumerate(kw_analysis['best_opportunities'][:3], 1):
        print(f"   {i}. {opp['keyword']}")
        print(f"      - Oportunidad: {opp['opportunity_score']:.1f}/100")
        print(f"      - Dificultad: {opp['difficulty_level']}")
    
    # Competidores
    print("\n👥 COMPETIDORES:")
    comp_analysis = result['competitor_analysis']
    print(f"   Total identificados: {comp_analysis['total_competitors']}")
    print(f"   Presupuesto total estimado: ${comp_analysis['total_estimated_budget']:,}")
    print(f"   Saturación: {comp_analysis['market_saturation']['level']}")
    
    if comp_analysis['top_competitor']:
        top = comp_analysis['top_competitor']
        print(f"\n   🏆 Competidor principal:")
        print(f"      {top['name']} - Nivel de amenaza: {top['threat_level']}")
    
    # Gaps
    print("\n💡 OPORTUNIDADES DE MERCADO:")
    gaps = result['market_gaps']
    print(f"   Total oportunidades: {gaps['total_opportunities']}")
    print(f"   Potencial: {gaps['market_potential']['level']}")
    
    if gaps['opportunities']:
        print(f"\n   Top oportunidades:")
        for i, opp in enumerate(gaps['opportunities'][:3], 1):
            print(f"   {i}. {opp['recommendation']}")
            print(f"      Prioridad: {opp['priority']}")
    
    # Tu posición
    if result['your_position']:
        print("\n📍 TU POSICIÓN:")
        pos = result['your_position']
        print(f"   Score: {pos['positioning_score']:.1f}/100")
        print(f"   Nivel: {pos['positioning_level']}")
        
        if pos['strengths']:
            print(f"\n   ✅ Fortalezas:")
            for strength in pos['strengths'][:3]:
                print(f"      • {strength}")
        
        if pos['weaknesses']:
            print(f"\n   ⚠️ Áreas de mejora:")
            for weakness in pos['weaknesses'][:3]:
                print(f"      • {weakness}")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"\n   {i}. [{rec['priority'].upper()}] {rec['category']}")
        print(f"      {rec['recommendation']}")
        print(f"      Impacto: {rec['expected_impact']}")
    
    # Score competitivo
    print("\n🏆 SCORE COMPETITIVO:")
    score = result['competitive_score']
    print(f"   Score: {score['score']:.1f}/100")
    print(f"   Nivel: {score['level']}")
    print(f"   {score['interpretation']}")
    
    # Estrategia
    print("\n🎯 ESTRATEGIA DE DIFERENCIACIÓN:")
    strategy = result['differentiation_strategy']
    print(f"\n   Mensaje clave: {strategy['key_message']}")
    
    print(f"\n   🚀 Quick Wins:")
    for qw in strategy['quick_wins']:
        print(f"      {qw}")
    
    print("\n" + "="*60)