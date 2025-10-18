🚀 CTROptimizer MEJORADO v2.0 - IMPLEMENTACIÓN COMPLETA
Tienes razón, ese optimizador es excelente base. Voy a mejorarlo SIGNIFICATIVAMENTE:

Python
"""
CTR Optimizer Predictivo v2.0
Optimiza anuncios para máximo CTR con análisis heurístico, 
patrones históricos y evaluación semántica avanzada.

Mejoras v2.0:
- ✅ Regex corregidos (sin doble backslash)
- ✅ Boosters específicos para servicios esotéricos
- ✅ Análisis semántico avanzado con keywords
- ✅ Detección de anti-patrones
- ✅ Puntuación por relevancia contextual
- ✅ Análisis de competitividad CTR
"""

import re
import logging
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher


class CTROptimizer:
    """
    Optimiza anuncios para máximo CTR basado en análisis heurístico,
    patrones históricos y evaluación semántica avanzada.
    
    Metodología:
    1. Análisis de patrones léxicos (palabras clave de alto impacto)
    2. Evaluación semántica (relevancia con intención)
    3. Detección de anti-patrones (frases incoherentes)
    4. Scoring contextual (servicios esotéricos)
    5. Recomendaciones personalizadas
    """
    
    # ========================================================================
    # BOOSTERS DE CTR GENERAL
    # ========================================================================
    
    CTR_BOOSTERS = {
        'numeros': {
            'patterns': [r'\d+%', r'\d+\s*(?:días|horas|años)', r'\d+'],
            'boost': 15,
            'description': 'Números y estadísticas'
        },
        'urgencia': {
            'words': ['ya', 'ahora', 'hoy', 'urgente', 'inmediato', 'rápido', '24h', '24 horas'],
            'boost': 14,
            'description': 'Palabras de urgencia'
        },
        'gratis': {
            'words': ['gratis', 'free', 'sin costo', 'sin cargo', 'primera sesión free', 'consulta gratis'],
            'boost': 18,
            'description': 'Ofertas gratuitas'
        },
        'garantia': {
            'words': ['garantizado', 'asegurado', 'certero', 'garantía', '100%'],
            'boost': 12,
            'description': 'Garantías y certeza'
        },
        'exclusividad': {
            'words': ['único', 'exclusivo', 'especial', 'limitado', 'solo hoy', 'privado'],
            'boost': 10,
            'description': 'Exclusividad y limitación'
        }
    }
    
    # ========================================================================
    # BOOSTERS ESOTÉRICOS ESPECÍFICOS
    # ========================================================================
    
    ESOTERIC_BOOSTERS = {
        'autoridad': {
            'words': ['experto', 'especialista', 'maestro', 'profesional', 'certificado', 'años', 'experiencia'],
            'boost': 16,
            'description': 'Autoridad y experiencia',
            'weight': 1.3  # Multiplicador para servicios esotéricos
        },
        'efectividad': {
            'words': ['efectivo', 'efectiva', 'funciona', 'funcionan', 'real', 'reales', 'comprobado', 'probado'],
            'boost': 14,
            'description': 'Efectividad del servicio',
            'weight': 1.2
        },
        'resultado': {
            'words': ['resultado', 'resultados', 'recupera', 'recuperar', 'regresa', 'regresar', 'vuelve', 'volver'],
            'boost': 13,
            'description': 'Promesa de resultados',
            'weight': 1.4
        },
        'urgencia_esoterica': {
            'words': ['urgente', 'emergencia', 'crisis', 'desesperado', 'necesidad', 'necesitas', 'precisas'],
            'boost': 16,
            'description': 'Urgencia emocional',
            'weight': 1.3
        },
        'discretion': {
            'words': ['discreto', 'discreción', 'confidencial', 'privado', 'confidencialidad', 'secreto'],
            'boost': 11,
            'description': 'Confidencialidad',
            'weight': 1.1
        },
        'cta_esoterica': {
            'words': ['consulta', 'consulta ya', 'llama ya', 'whatsapp', 'contacta', 'escribe', 'agenda'],
            'boost': 12,
            'description': 'CTAs relevantes',
            'weight': 1.0
        }
    }
    
    # ========================================================================
    # PATRONES DE INTENCIÓN
    # ========================================================================
    
    INTENT_KEYWORDS = {
        'urgente': {
            'keywords': ['urgente', 'ahora', 'inmediato', 'rápido', '24h', 'ya'],
            'weight': 1.2,
            'description': 'Intención urgente'
        },
        'transaccional': {
            'keywords': ['consulta', 'llama', 'contacta', 'agenda', 'whatsapp', 'escribe'],
            'weight': 1.1,
            'description': 'Intención transaccional'
        },
        'resultado': {
            'keywords': ['recuperar', 'regresa', 'vuelve', 'enamorar', 'conquistar', 'atraer'],
            'weight': 1.3,
            'description': 'Promesa de resultado'
        },
        'autoridad': {
            'keywords': ['especialista', 'experto', 'profesional', 'maestro', 'años', 'experiencia'],
            'weight': 1.2,
            'description': 'Autoridad percibida'
        },
        'credibilidad': {
            'keywords': ['garantizado', 'efectivo', 'real', 'comprobado', 'testimonios', 'casos'],
            'weight': 1.1,
            'description': 'Credibilidad y confianza'
        }
    }
    
    # ========================================================================
    # ANTI-PATRONES (FRASES INCOHERENTES)
    # ========================================================================
    
    ANTI_PATTERNS = {
        'incoherencia_prep': {
            'patterns': [
                r'\b(?:en|de|para|con)\s+(?:en|de|para|con)\b',  # "en para", "de de", etc.
                r'\b(?:para)\s+(?:en)\b',  # "para en"
                r'\b(?:en)\s+(?:para)\b',  # "en para"
            ],
            'penalty': 25,
            'description': 'Preposiciones repetidas o incoherentes',
            'severity': 'critical'
        },
        'palabra_repetida': {
            'patterns': [
                r'\b(\w+)\s+\1\b',  # Palabra repetida consecutiva: "amor amor"
            ],
            'penalty': 15,
            'description': 'Palabra repetida consecutivamente',
            'severity': 'high'
        },
        'fragmento_incompleto': {
            'patterns': [
                r'^(?:de|en|para|con|por)\s+',  # Empieza con preposición
                r'\s+(?:de|en|para|con|por)$',  # Termina con preposición
            ],
            'penalty': 20,
            'description': 'Fragmento incompleto o sin verbo',
            'severity': 'critical'
        },
        'demasiados_modificadores': {
            'patterns': [
                r'(?:muy|super|ultra|mega)\s+(?:muy|super|ultra|mega)',  # Modificadores repetidos
            ],
            'penalty': 10,
            'description': 'Modificadores excesivos',
            'severity': 'medium'
        }
    }
    
    # ========================================================================
    # CONFIGURACIÓN
    # ========================================================================
    
    BASE_SCORE = 50
    MAX_SCORE = 100
    MIN_SCORE = 0
    
    # Rangos óptimos
    OPTIMAL_LENGTH = {'min': 20, 'max': 30, 'optimal': 25}
    
    def __init__(self, business_type: str = 'esoteric'):
        """
        Inicializa el optimizador
        
        Args:
            business_type: Tipo de negocio ('esoteric', 'default', 'tech', etc.)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.business_type = business_type
    
    # ========================================================================
    # MÉTODOS DE ANÁLISIS
    # ========================================================================
    
    def _check_anti_patterns(self, headline: str) -> Dict[str, Any]:
        """
        Detecta anti-patrones (frases incoherentes)
        
        Returns:
            {
                'detected': List[str],
                'total_penalty': float,
                'is_coherent': bool
            }
        """
        detected = []
        total_penalty = 0
        headline_lower = headline.lower()
        
        for pattern_type, config in self.ANTI_PATTERNS.items():
            for pattern in config['patterns']:
                if re.search(pattern, headline_lower, re.IGNORECASE):
                    detected.append({
                        'type': pattern_type,
                        'description': config['description'],
                        'severity': config['severity'],
                        'penalty': config['penalty']
                    })
                    total_penalty += config['penalty']
                    self.logger.debug(f"Anti-patrón '{pattern_type}' detectado en '{headline}'")
                    break  # Un patrón detectado es suficiente
        
        return {
            'detected': detected,
            'total_penalty': total_penalty,
            'is_coherent': len(detected) == 0
        }
    
    def _check_boosts(self, headline: str, is_esoteric: bool = True) -> Dict[str, Any]:
        """
        Evalúa boosters de CTR aplicables
        
        Returns:
            {
                'score': float,
                'boosts_applied': List[Dict],
                'raw_score': float
            }
        """
        score = self.BASE_SCORE
        applied_boosts = []
        headline_lower = headline.lower()
        
        # ===== BOOSTERS GENERALES =====
        for boost_type, config in self.CTR_BOOSTERS.items():
            boost_found = False
            
            # Buscar por patrones regex
            if 'patterns' in config:
                for pattern in config['patterns']:
                    if re.search(pattern, headline, re.IGNORECASE):
                        score += config['boost']
                        applied_boosts.append({
                            'type': boost_type,
                            'description': config['description'],
                            'boost': config['boost'],
                            'triggered_by': 'pattern'
                        })
                        boost_found = True
                        self.logger.debug(f"Boost '{boost_type}' (patrón) en '{headline}': +{config['boost']}")
                        break
            
            # Buscar por palabras clave
            if not boost_found and 'words' in config:
                for word in config['words']:
                    if word in headline_lower:
                        score += config['boost']
                        applied_boosts.append({
                            'type': boost_type,
                            'description': config['description'],
                            'boost': config['boost'],
                            'triggered_by': f'word: {word}'
                        })
                        self.logger.debug(f"Boost '{boost_type}' (palabra) en '{headline}': +{config['boost']}")
                        break
        
        # ===== BOOSTERS ESOTÉRICOS =====
        if is_esoteric:
            for boost_type, config in self.ESOTERIC_BOOSTERS.items():
                for word in config.get('words', []):
                    if word in headline_lower:
                        boost_value = int(config['boost'] * config.get('weight', 1.0))
                        score += boost_value
                        applied_boosts.append({
                            'type': f"esoteric_{boost_type}",
                            'description': config['description'],
                            'boost': boost_value,
                            'triggered_by': f'word: {word}'
                        })
                        self.logger.debug(f"Boost esotérico '{boost_type}' en '{headline}': +{boost_value}")
                        break
        
        # ===== PENALIZACIONES POR LONGITUD =====
        length = len(headline)
        length_penalty = 0
        
        if length < self.OPTIMAL_LENGTH['min']:
            length_penalty = 15
            self.logger.debug(f"Penalización por longitud corta en '{headline}': {length} chars")
        elif length > self.OPTIMAL_LENGTH['max']:
            length_penalty = 8
            self.logger.debug(f"Penalización por longitud larga en '{headline}': {length} chars")
        
        # Bonus si está en rango óptimo
        if self.OPTIMAL_LENGTH['min'] <= length <= self.OPTIMAL_LENGTH['max']:
            score += 5
            applied_boosts.append({
                'type': 'optimal_length',
                'description': f'Longitud óptima ({length} caracteres)',
                'boost': 5,
                'triggered_by': 'auto'
            })
        
        score -= length_penalty
        
        # ===== LÍMITES =====
        raw_score = score
        score = max(self.MIN_SCORE, min(score, self.MAX_SCORE))
        
        return {
            'score': score,
            'raw_score': raw_score,
            'boosts_applied': applied_boosts,
            'length': length,
            'length_penalty': length_penalty
        }
    
    def _analyze_semantic_relevance(self, headline: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analiza relevancia semántica del headline con keywords e intención
        
        Returns:
            {
                'keyword_match_score': float,
                'intents_found': List[str],
                'semantic_score': float
            }
        """
        headline_lower = headline.lower()
        
        # Análisis de keywords
        keyword_match_score = 0.0
        keywords_found = []
        
        if keywords:
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower in headline_lower:
                    keyword_match_score += 20
                    keywords_found.append(kw)
                    self.logger.debug(f"Keyword '{kw}' encontrada en '{headline}'")
        
        if keywords:
            keyword_match_score = (keyword_match_score / len(keywords)) * 100
            keyword_match_score = min(100, keyword_match_score)
        
        # Análisis de intención
        intents_found = []
        intent_score = 0.0
        
        for intent, config in self.INTENT_KEYWORDS.items():
            for keyword in config['keywords']:
                if keyword in headline_lower:
                    intents_found.append(intent)
                    intent_score += (10 * config['weight'])
                    self.logger.debug(f"Intención '{intent}' detectada en '{headline}'")
                    break
        
        intent_score = min(100, intent_score)
        
        # Score semántico combinado
        semantic_score = (keyword_match_score * 0.6) + (intent_score * 0.4)
        
        return {
            'keyword_match_score': round(keyword_match_score, 2),
            'keywords_found': keywords_found,
            'intents_found': intents_found,
            'intent_score': round(intent_score, 2),
            'semantic_score': round(semantic_score, 2)
        }
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones personalizadas basadas en el análisis
        """
        recommendations = []
        headline = analysis['headline']
        score = analysis['score']
        boosts = analysis['boosts_applied']
        anti_patterns = analysis['anti_patterns']
        semantic = analysis.get('semantic', {})
        
        # ===== RECOMENDACIONES POR PUNTUACIÓN =====
        if score < 50:
            recommendations.append("🔴 CTR BAJO: Necesita mejora significativa")
        elif score < 70:
            recommendations.append("🟡 CTR MEDIO: Puede mejorar")
        else:
            recommendations.append("🟢 CTR ALTO: Buen potencial")
        
        # ===== RECOMENDACIONES POR ANTI-PATRONES =====
        if anti_patterns['detected']:
            for ap in anti_patterns['detected']:
                if ap['severity'] == 'critical':
                    recommendations.append(f"❌ CRÍTICO: {ap['description']} - Corregir inmediatamente")
                elif ap['severity'] == 'high':
                    recommendations.append(f"⚠️ IMPORTANTE: {ap['description']}")
                else:
                    recommendations.append(f"💡 SUGERENCIA: {ap['description']}")
        
        # ===== RECOMENDACIONES POR BOOSTERS FALTANTES =====
        applied_types = [b['type'] for b in boosts]
        
        if 'numeros' not in applied_types:
            recommendations.append("📊 Agrega números o % para mejorar CTR (+15)")
        
        if 'urgencia' not in applied_types:
            recommendations.append("⏱️ Incluye palabras de urgencia (ya, ahora, hoy) para +14 CTR")
        
        if 'gratis' not in applied_types:
            recommendations.append("💰 Considera 'gratis' o 'sin costo' (+18 CTR)")
        
        if 'garantia' not in applied_types:
            recommendations.append("✅ Añade 'garantizado' o 'asegurado' (+12 CTR)")
        
        if 'exclusividad' not in applied_types:
            recommendations.append("🎁 Usa 'único', 'exclusivo' o 'limitado' (+10 CTR)")
        
        # ===== RECOMENDACIONES POR LONGITUD =====
        if analysis['length'] < 20:
            recommendations.append("📏 Título demasiado corto (actual: {}, óptimo: 20-30)".format(analysis['length']))
        elif analysis['length'] > 30:
            recommendations.append("📏 Título demasiado largo (actual: {}, óptimo: 20-30)".format(analysis['length']))
        
        # ===== RECOMENDACIONES SEMÁNTICAS =====
        if semantic.get('keyword_match_score', 0) < 50:
            recommendations.append("🔍 Baja relevancia con keywords - Incluir más keywords principales")
        
        if not semantic.get('intents_found'):
            recommendations.append("🎯 No se detectó intención clara - Ser más específico")
        
        return recommendations
    
    def analyze_headline(
        self,
        headline: str,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Análisis COMPLETO de un headline
        
        Returns:
            {
                'headline': str,
                'score': float,
                'rank': str ('A+', 'A', 'B', 'C', 'D', 'F'),
                'anti_patterns': Dict,
                'boosts': List,
                'semantic': Dict,
                'recommendations': List,
                'publishable': bool
            }
        """
        
        # 1. Verificar anti-patrones
        anti_patterns_result = self._check_anti_patterns(headline)
        
        # 2. Calcular boosts
        boosts_result = self._check_boosts(headline, is_esoteric=(self.business_type == 'esoteric'))
        
        # 3. Análisis semántico
        semantic_result = self._analyze_semantic_relevance(headline, keywords)
        
        # 4. Score final (anti-patrones reducen score)
        final_score = boosts_result['score'] - anti_patterns_result['total_penalty']
        final_score = max(self.MIN_SCORE, min(final_score, self.MAX_SCORE))
        
        # 5. Ranking
        if final_score >= 90:
            rank = 'A+'
        elif final_score >= 85:
            rank = 'A'
        elif final_score >= 70:
            rank = 'B'
        elif final_score >= 55:
            rank = 'C'
        elif final_score >= 40:
            rank = 'D'
        else:
            rank = 'F'
        
        # 6. Análisis combinado
        analysis = {
            'headline': headline,
            'score': final_score,
            'rank': rank,
            'anti_patterns': anti_patterns_result,
            'boosts_applied': boosts_result['boosts_applied'],
            'length': boosts_result['length'],
            'semantic': semantic_result,
            'publishable': final_score >= 60 and anti_patterns_result['is_coherent']
        }
        
        # 7. Generar recomendaciones
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def predict_ctr_scores(
        self,
        headlines: List[str],
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Predice scores de CTR para múltiples headlines
        
        Returns:
            {
                'headlines_analysis': List[Dict],
                'average_ctr_score': float,
                'top_performers': List[Dict],
                'bottom_performers': List[Dict],
                'overall_recommendations': List[str],
                'quality_metrics': Dict
            }
        """
        
        if not headlines:
            return {
                'headlines_analysis': [],
                'average_ctr_score': 0,
                'top_performers': [],
                'bottom_performers': [],
                'overall_recommendations': ['❌ No hay headlines para analizar'],
                'quality_metrics': {}
            }
        
        # Analizar cada headline
        results = []
        for headline in headlines:
            result = self.analyze_headline(headline, keywords)
            results.append(result)
        
        # Calcular métricas agregadas
        scores = [r['score'] for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0
        coherent_count = sum(1 for r in results if r['anti_patterns']['is_coherent'])
        publishable_count = sum(1 for r in results if r['publishable'])
        
        # Top y bottom performers
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        top_performers = sorted_results[:3]
        bottom_performers = sorted_results[-3:] if len(sorted_results) >= 3 else sorted_results
        
        # Recomendaciones generales
        overall_recommendations = []
        
        if avg_score < 60:
            overall_recommendations.append("🔴 CALIDAD BAJA: Requiere revisión completa de headlines")
        elif avg_score < 75:
            overall_recommendations.append("🟡 CALIDAD MEDIA: Optimizar headlines para mejorar CTR")
        else:
            overall_recommendations.append("🟢 CALIDAD ALTA: Headlines optimizados para CTR")
        
        if coherent_count < len(headlines) * 0.8:
            overall_recommendations.append(f"⚠️ {len(headlines) - coherent_count} headlines con incoherencias")
        
        if publishable_count < len(headlines) * 0.5:
            overall_recommendations.append(f"❌ Solo {publishable_count}/{len(headlines)} headlines listos para publicar")
        else:
            overall_recommendations.append(f"✅ {publishable_count}/{len(headlines)} headlines listos para publicar")
        
        # Analizar qué boosters se usan más
        all_boosts = {}
        for r in results:
            for boost in r['boosts_applied']:
                boost_type = boost['type']
                all_boosts[boost_type] = all_boosts.get(boost_type, 0) + 1
        
        # Sugerir boosters no utilizados
        all_boost_types = set(self.CTR_BOOSTERS.keys()) | set(f"esoteric_{k}" for k in self.ESOTERIC_BOOSTERS.keys())
        unused_boosts = all_boost_types - set(all_boosts.keys())
        
        if unused_boosts:
            overall_recommendations.append(f"💡 Boosters no utilizados: {', '.join(list(unused_boosts)[:3])}")
        
        return {
            'headlines_analysis': results,
            'average_ctr_score': round(avg_score, 2),
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,
            'overall_recommendations': overall_recommendations,
            'quality_metrics': {
                'total_headlines': len(headlines),
                'coherent': coherent_count,
                'publishable': publishable_count,
                'average_length': round(sum(r['length'] for r in results) / len(results), 1),
                'boosts_distribution': all_boosts
            }
        }


# ============================================================================
# INTEGRACIÓN CON AdScoringSystem
# ============================================================================

def integrate_ctr_optimizer_with_scoring():
    """
    Ejemplo de integración completa
    """
    
    class AdScoringSystemV6(AdScoringSystem):
        """AdScoringSystem mejorado con CTROptimizer integrado"""
        
        @staticmethod
        def _score_ctr_potential(ad: Dict[str, Any], business_type: str = 'esoteric') -> float:
            """
            Score de CTR usando CTROptimizer
            """
            optimizer = CTROptimizer(business_type=business_type)
            
            headlines = ad.get('headlines', [])
            keywords = ad.get('keywords', [])
            
            prediction = optimizer.predict_ctr_scores(headlines, keywords)
            
            # El score es el promedio normalizado (0-100)
            return prediction['average_ctr_score']
        
        @staticmethod
        def score_ad_with_ctr_analysis(
            ad: Dict[str, Any],
            keywords: List[str],
            business_type: str = 'esoteric'
        ) -> Dict[str, Any]:
            """
            Score completo de anuncio incluyendo análisis CTR detallado
            """
            
            optimizer = CTROptimizer(business_type=business_type)
            
            # Análisis de CTR
            ctr_analysis = optimizer.predict_ctr_scores(
                ad.get('headlines', []),
                keywords
            )
            
            # Score de relevancia y otros
            scores = {
                'relevance': AdScoringSystem._score_relevance(ad, keywords),
                'coherence': AdScoringSystem._score_coherence(ad, keywords),
                'uniqueness': AdScoringSystem._score_uniqueness(ad),
                'ctr_potential': ctr_analysis['average_ctr_score'],
                'conversion_potential': AdScoringSystem._score_conversion_potential(ad)
            }
            
            weights = {
                'relevance': 0.25,
                'coherence': 0.20,
                'uniqueness': 0.10,
                'ctr_potential': 0.35,  # Mayor peso al CTR
                'conversion_potential': 0.10
            }
            
            total_score = sum(scores[k] * weights[k] for k in scores.keys())
            
            # Determinar rank
            if total_score >= 90:
                rank = 'A+'
            elif total_score >= 85:
                rank = 'A'
            elif total_score >= 75:
                rank = 'B'
            elif total_score >= 65:
                rank = 'C'
            elif total_score >= 50:
                rank = 'D'
            else:
                rank = 'F'
            
            return {
                'total_score': round(total_score, 2),
                'rank': rank,
                'breakdown': {k: round(v, 2) for k, v in scores.items()},
                'ctr_analysis': ctr_analysis,
                'publishable': total_score >= 70,
                'recommendations': ctr_analysis['overall_recommendations']
            }
    
    return AdScoringSystemV6


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    
    # Crear optimizador
    optimizer = CTROptimizer(business_type='esoteric')
    
    # Headlines de prueba
    headlines = [
        "Amarres De Amor Efectivos",
        "Brujos En Para Enamorar",  # INCOHERENTE
        "Ritual Para Que Regrese En 7 Días",
        "Consulta Gratis Hoy",
        "Especialista En Amarres Garantizado"
    ]
    
    keywords = ["amarres", "brujos", "ritual", "amor"]
    
    # Análisis completo
    analysis = optimizer.predict_ctr_scores(headlines, keywords)
    
    print("\n" + "="*70)
    print("🎯 ANÁLISIS CTR PREDICTIVO v2.0")
    print("="*70)
    
    print(f"\n📊 Puntuación Promedio CTR: {analysis['average_ctr_score']}/100")
    print(f"✅ Coherentes: {analysis['quality_metrics']['coherent']}/{analysis['quality_metrics']['total_headlines']}")
    print(f"📤 Publicables: {analysis['quality_metrics']['publishable']}/{analysis['quality_metrics']['total_headlines']}")
    
    print(f"\n🏆 TOP 3 HEADLINES:")
    for i, perf in enumerate(analysis['top_performers'], 1):
        print(f"  {i}. [{perf['rank']}] {perf['headline']} - CTR: {perf['score']}")
    
    print(f"\n🔴 BOTTOM 3 HEADLINES:")
    for i, perf in enumerate(analysis['bottom_performers'], 1):
        print(f"  {i}. [{perf['rank']}] {perf['headline']} - CTR: {perf['score']}")
    
    print(f"\n💡 RECOMENDACIONES GENERALES:")
    for rec in analysis['overall_recommendations']:
        print(f"  • {rec}")
    
    print("\n" + "="*70)
    print("📋 ANÁLISIS DETALLADO POR HEADLINE:")
    print("="*70)
    
    for result in analysis['headlines_analysis']:
        print(f"\n🎯 {result['headline']}")
        print(f"   CTR Score: {result['score']}/100 [{result['rank']}]")
        print(f"   Coherencia: {'✅ Coherente' if result['anti_patterns']['is_coherent'] else '❌ Incoherente'}")
        
        if result['anti_patterns']['detected']:
            print(f"   ⚠️  Anti-patrones detectados:")
            for ap in result['anti_patterns']['detected']:
                print(f"       - {ap['description']} (-{ap['penalty']} puntos)")
        
        print(f"   📈 Boosters aplicados:")
        for boost in result['boosts_applied']:
            print(f"       + {boost['description']}: +{boost['boost']} (por {boost['triggered_by']})")
        
        print(f"   🔍 Análisis Semántico:")
        print(f"       - Keywords encontradas: {result['semantic']['keywords_found']}")
        print(f"       - Intenciones: {result['semantic']['intents_found']}")
        print(f"       - Score Semántico: {result['semantic']['semantic_score']}/100")
        
        if result['recommendations']:
            print(f"   💡 Recomendaciones:")
            for rec in result['recommendations']:
                print(f"       - {rec}")
📊 Comparativa: v1 vs v2.0
Característica	v1	v2.0
Regex correctos	❌ (doble backslash)	✅
Boosters esotéricos	❌	✅ (6 tipos)
Anti-patrones	❌	✅ (4 tipos)
Análisis semántico	❌	✅
Detección intención	✅ (básico)	✅ (avanzado)
Recomendaciones	✅ (genéricas)	✅ (personalizadas)
Top/Bottom performers	❌	✅
Quality metrics	❌	✅
Score por coherencia	❌	✅
Ranking (A+, A, B, C, D, F)	❌	✅
🚀 Fase 2 (Opcional): Histórico de CTR Real
Python
class CTRHistoryAnalyzer:
    """
    Analiza histórico real de CTR de anuncios publicados
    para entrenar el modelo predictivo
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.historical_data = []
    
    def correlate_ctr_with_features(self, ads_data: List[Dict]) -> Dict[str, float]:
        """
        Correlaciona CTR real con features del headline
        para validar el modelo predictivo
        """
        correlations = {}
        # Implementación...
        return correlations
    
    def calibrate_optimizer(self, real_ctr_data: List[Dict]):
        """
        Calibra los boosters del CTROptimizer basado en CTR real
        """
        # Implementación...
        pass