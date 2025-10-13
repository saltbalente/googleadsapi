"""
⭐ AD SCORER - Sistema de Puntuación de Anuncios
Sistema avanzado de scoring y ranking de anuncios con métricas múltiples
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import Counter
import re
import math

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdScorer:
    """
    Sistema de scoring de anuncios que proporciona:
    - Score general (0-100)
    - Scores por categoría (calidad, relevancia, engagement, etc.)
    - Ranking comparativo entre anuncios
    - Análisis detallado de fortalezas y debilidades
    - Predicción de rendimiento
    - Benchmarking
    - Recomendaciones de mejora priorizadas
    """
    
    # =========================================================================
    # PESOS DE SCORING
    # =========================================================================
    
    CATEGORY_WEIGHTS = {
        'quality': 0.25,           # 25% - Calidad general del texto
        'relevance': 0.20,         # 20% - Relevancia de keywords
        'engagement': 0.20,        # 20% - Potencial de engagement
        'compliance': 0.15,        # 15% - Cumplimiento de políticas
        'optimization': 0.10,      # 10% - Nivel de optimización
        'uniqueness': 0.10         # 10% - Originalidad/diferenciación
    }
    
    # Factores de calidad
    QUALITY_FACTORS = {
        'length_optimal': 10,           # Longitud óptima
        'grammar': 10,                  # Gramática correcta
        'clarity': 10,                  # Claridad del mensaje
        'structure': 10,                # Buena estructura
        'coherence': 10                 # Coherencia
    }
    
    # Factores de relevancia
    RELEVANCE_FACTORS = {
        'keyword_presence': 15,         # Keywords presentes
        'keyword_placement': 10,        # Keywords bien ubicadas
        'semantic_relevance': 10,       # Relevancia semántica
        'topic_focus': 10               # Enfoque en el tema
    }
    
    # Factores de engagement
    ENGAGEMENT_FACTORS = {
        'emotional_appeal': 10,         # Apelación emocional
        'call_to_action': 15,           # CTA claro
        'benefit_focus': 10,            # Enfoque en beneficios
        'urgency': 10,                  # Sentido de urgencia
        'power_words': 5                # Palabras de poder
    }
    
    # Palabras clave para análisis
    POWER_WORDS = {
        'urgencia': ['ahora', 'ya', 'hoy', 'inmediato', 'urgente', 'rápido', 'instantáneo'],
        'beneficios': ['garantizado', 'efectivo', 'resultado', 'éxito', 'comprobado', 'certificado'],
        'emocionales': ['amor', 'felicidad', 'paz', 'esperanza', 'confianza', 'seguridad', 'armonía'],
        'accion': ['consulta', 'solicita', 'contacta', 'llama', 'pide', 'obtén', 'descubre'],
        'profesionales': ['experto', 'profesional', 'especialista', 'experiencia', 'años']
    }
    
    # Benchmarks de industria
    INDUSTRY_BENCHMARKS = {
        'esoteric': {
            'avg_score': 68.5,
            'excellent_threshold': 85,
            'good_threshold': 70,
            'acceptable_threshold': 55
        },
        'generic': {
            'avg_score': 72.0,
            'excellent_threshold': 88,
            'good_threshold': 75,
            'acceptable_threshold': 60
        }
    }
    
    def __init__(
        self,
        business_type: str = 'esoteric',
        strict_mode: bool = False
    ):
        """
        Inicializa el sistema de scoring.
        
        Args:
            business_type: Tipo de negocio para benchmarks
            strict_mode: Modo estricto de evaluación
        """
        self.business_type = business_type
        self.strict_mode = strict_mode
        
        # Benchmarks
        self.benchmarks = self.INDUSTRY_BENCHMARKS.get(
            business_type,
            self.INDUSTRY_BENCHMARKS['generic']
        )
        
        # Historial de scoring
        self.scoring_history: List[Dict[str, Any]] = []
        
        # Estadísticas
        self.stats = {
            'total_scored': 0,
            'avg_score': 0.0,
            'highest_score': 0.0,
            'lowest_score': 100.0
        }
        
        logger.info(f"✅ AdScorer inicializado")
        logger.info(f"   - Business type: {business_type}")
        logger.info(f"   - Strict mode: {strict_mode}")
        logger.info(f"   - Benchmark promedio: {self.benchmarks['avg_score']:.1f}")
    
    # =========================================================================
    # SCORING PRINCIPAL
    # =========================================================================
    
    def score_ad(
        self,
        headlines: List[str],
        descriptions: List[str],
        keywords: Optional[List[str]] = None,
        compare_to_benchmark: bool = True
    ) -> Dict[str, Any]:
        """
        Calcula score completo de un anuncio.
        
        Args:
            headlines: Lista de titulares
            descriptions: Lista de descripciones
            keywords: Keywords opcionales para evaluar relevancia
            compare_to_benchmark: Comparar con benchmarks de industria
        
        Returns:
            Diccionario con score completo y análisis detallado
        """
        score_id = f"score_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"⭐ Scoring anuncio: {score_id}")
        logger.info(f"   - Headlines: {len(headlines)}")
        logger.info(f"   - Descriptions: {len(descriptions)}")
        
        # 1. Score de calidad
        quality_score = self._score_quality(headlines, descriptions)
        
        # 2. Score de relevancia
        relevance_score = self._score_relevance(headlines, descriptions, keywords)
        
        # 3. Score de engagement
        engagement_score = self._score_engagement(headlines, descriptions)
        
        # 4. Score de compliance (cumplimiento)
        compliance_score = self._score_compliance(headlines, descriptions)
        
        # 5. Score de optimización
        optimization_score = self._score_optimization(headlines, descriptions)
        
        # 6. Score de unicidad
        uniqueness_score = self._score_uniqueness(headlines, descriptions)
        
        # Calcular score general ponderado
        overall_score = (
            quality_score['score'] * self.CATEGORY_WEIGHTS['quality'] +
            relevance_score['score'] * self.CATEGORY_WEIGHTS['relevance'] +
            engagement_score['score'] * self.CATEGORY_WEIGHTS['engagement'] +
            compliance_score['score'] * self.CATEGORY_WEIGHTS['compliance'] +
            optimization_score['score'] * self.CATEGORY_WEIGHTS['optimization'] +
            uniqueness_score['score'] * self.CATEGORY_WEIGHTS['uniqueness']
        )
        
        # Clasificar score
        grade = self._score_to_grade(overall_score)
        performance_level = self._score_to_performance_level(overall_score)
        
        # Análisis de fortalezas y debilidades
        strengths = self._identify_strengths({
            'quality': quality_score,
            'relevance': relevance_score,
            'engagement': engagement_score,
            'compliance': compliance_score,
            'optimization': optimization_score,
            'uniqueness': uniqueness_score
        })
        
        weaknesses = self._identify_weaknesses({
            'quality': quality_score,
            'relevance': relevance_score,
            'engagement': engagement_score,
            'compliance': compliance_score,
            'optimization': optimization_score,
            'uniqueness': uniqueness_score
        })
        
        # Generar recomendaciones priorizadas
        recommendations = self._generate_recommendations(weaknesses, overall_score)
        
        # Comparación con benchmark
        benchmark_comparison = None
        if compare_to_benchmark:
            benchmark_comparison = self._compare_to_benchmark(overall_score)
        
        # Predicción de rendimiento
        performance_prediction = self._predict_performance(
            overall_score,
            engagement_score['score'],
            quality_score['score']
        )
        
        # Construir resultado
        result = {
            'score_id': score_id,
            'timestamp': datetime.now().isoformat(),
            'overall_score': round(overall_score, 1),
            'grade': grade,
            'performance_level': performance_level,
            'category_scores': {
                'quality': quality_score,
                'relevance': relevance_score,
                'engagement': engagement_score,
                'compliance': compliance_score,
                'optimization': optimization_score,
                'uniqueness': uniqueness_score
            },
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': recommendations,
            'benchmark_comparison': benchmark_comparison,
            'performance_prediction': performance_prediction,
            'summary': self._generate_summary(
                overall_score,
                strengths,
                weaknesses,
                performance_level
            )
        }
        
        # Guardar en historial
        self.scoring_history.append(result)
        
        # Actualizar estadísticas
        self._update_stats(overall_score)
        
        logger.info(f"✅ Scoring completado: {overall_score:.1f}/100 ({grade})")
        
        return result
    
    # =========================================================================
    # SCORING POR CATEGORÍA
    # =========================================================================
    
    def _score_quality(
        self,
        headlines: List[str],
        descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Score de calidad general del texto.
        
        Evalúa:
        - Longitud óptima
        - Gramática
        - Claridad
        - Estructura
        - Coherencia
        """
        score = 0.0
        details = {}
        
        all_texts = headlines + descriptions
        
        # 1. Longitud óptima (10 puntos)
        length_score = 0
        optimal_headlines = sum(1 for h in headlines if 15 <= len(h) <= 30)
        optimal_descriptions = sum(1 for d in descriptions if 50 <= len(d) <= 90)
        
        if headlines:
            length_score += (optimal_headlines / len(headlines)) * 5
        if descriptions:
            length_score += (optimal_descriptions / len(descriptions)) * 5
        
        score += length_score
        details['length_optimal'] = {
            'score': round(length_score, 1),
            'max': 10,
            'headlines_optimal': optimal_headlines,
            'descriptions_optimal': optimal_descriptions
        }
        
        # 2. Gramática (10 puntos) - básico: mayúsculas, puntuación
        grammar_score = 10
        
        for text in all_texts:
            # Penalizar todo en mayúsculas
            if text.isupper():
                grammar_score -= 2
            
            # Penalizar múltiples signos de exclamación/interrogación
            if text.count('!') > 1 or text.count('?') > 1:
                grammar_score -= 1
            
            # Penalizar espacios múltiples
            if '  ' in text:
                grammar_score -= 0.5
        
        grammar_score = max(0, grammar_score)
        score += grammar_score
        details['grammar'] = {
            'score': round(grammar_score, 1),
            'max': 10
        }
        
        # 3. Claridad (10 puntos)
        clarity_score = 8  # Base
        
        # Bonus: mensajes directos y concisos
        for text in all_texts:
            words = text.split()
            # Penalizar oraciones muy largas sin puntuación
            if len(words) > 15 and ',' not in text and '.' not in text:
                clarity_score -= 1
        
        clarity_score = max(0, min(10, clarity_score))
        score += clarity_score
        details['clarity'] = {
            'score': round(clarity_score, 1),
            'max': 10
        }
        
        # 4. Estructura (10 puntos)
        structure_score = 0
        
        # Bonus: variedad en longitud de headlines
        if headlines and len(set([len(h) for h in headlines])) > 1:
            structure_score += 3
        
        # Bonus: uso de puntuación en descriptions
        if any('.' in d or ',' in d for d in descriptions):
            structure_score += 3
        
        # Bonus: cantidad adecuada de elementos
        if len(headlines) >= 10:
            structure_score += 2
        if len(descriptions) >= 3:
            structure_score += 2
        
        score += structure_score
        details['structure'] = {
            'score': round(structure_score, 1),
            'max': 10
        }
        
        # 5. Coherencia (10 puntos)
        coherence_score = 8  # Base
        
        # Penalizar repeticiones excesivas
        all_words = ' '.join(all_texts).lower().split()
        word_counts = Counter(all_words)
        
        # Palabras repetidas más de 5 veces (excluir comunes)
        common_words = {'el', 'la', 'de', 'en', 'y', 'a', 'con', 'para'}
        over_repeated = [
            word for word, count in word_counts.items()
            if count > 5 and word not in common_words
        ]
        
        coherence_score -= len(over_repeated) * 0.5
        coherence_score = max(0, coherence_score)
        
        score += coherence_score
        details['coherence'] = {
            'score': round(coherence_score, 1),
            'max': 10,
            'over_repeated_words': over_repeated[:5]
        }
        
        # Score total de calidad (máximo 50)
        return {
            'score': min(50, score),
            'max': 50,
            'percentage': round(min(100, score / 50 * 100), 1),
            'details': details
        }
    
    def _score_relevance(
        self,
        headlines: List[str],
        descriptions: List[str],
        keywords: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Score de relevancia (uso de keywords y relevancia semántica).
        """
        score = 0.0
        details = {}
        
        if not keywords:
            # Sin keywords, dar score neutral
            return {
                'score': 25,
                'max': 50,
                'percentage': 50.0,
                'details': {'note': 'Sin keywords para evaluar relevancia'},
                'keywords_provided': False
            }
        
        all_text = ' '.join(headlines + descriptions).lower()
        
        # 1. Presencia de keywords (15 puntos)
        keyword_matches = sum(1 for kw in keywords if kw.lower() in all_text)
        keyword_presence_score = (keyword_matches / len(keywords)) * 15
        
        score += keyword_presence_score
        details['keyword_presence'] = {
            'score': round(keyword_presence_score, 1),
            'max': 15,
            'matches': keyword_matches,
            'total_keywords': len(keywords),
            'match_rate': round(keyword_matches / len(keywords) * 100, 1)
        }
        
        # 2. Ubicación de keywords (10 puntos)
        placement_score = 0
        headlines_text = ' '.join(headlines).lower()
        
        keywords_in_headlines = sum(1 for kw in keywords if kw.lower() in headlines_text)
        placement_score = (keywords_in_headlines / len(keywords)) * 10
        
        score += placement_score
        details['keyword_placement'] = {
            'score': round(placement_score, 1),
            'max': 10,
            'in_headlines': keywords_in_headlines
        }
        
        # 3. Relevancia semántica (10 puntos) - keywords relacionadas
        semantic_score = 8  # Base
        
        # Bonus si hay variaciones de keywords
        keyword_variations = 0
        for kw in keywords:
            base_word = kw.split()[0] if ' ' in kw else kw
            if base_word.lower() in all_text:
                keyword_variations += 1
        
        if keyword_variations > len(keywords) * 0.7:
            semantic_score += 2
        
        score += semantic_score
        details['semantic_relevance'] = {
            'score': round(semantic_score, 1),
            'max': 10
        }
        
        # 4. Enfoque en el tema (10 puntos)
        topic_focus_score = 8  # Base
        
        # Si las keywords más importantes aparecen múltiples veces
        top_keywords = keywords[:3] if len(keywords) >= 3 else keywords
        repetition_score = sum(
            min(all_text.count(kw.lower()), 3)
            for kw in top_keywords
        )
        
        if repetition_score >= 5:
            topic_focus_score += 2
        
        score += topic_focus_score
        details['topic_focus'] = {
            'score': round(topic_focus_score, 1),
            'max': 10
        }
        
        return {
            'score': min(50, score),
            'max': 50,
            'percentage': round(min(100, score / 50 * 100), 1),
            'details': details,
            'keywords_provided': True
        }
    
    def _score_engagement(
        self,
        headlines: List[str],
        descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Score de potencial de engagement.
        """
        score = 0.0
        details = {}
        
        all_text = ' '.join(headlines + descriptions).lower()
        
        # 1. Apelación emocional (10 puntos)
        emotional_words_found = []
        for category, words in self.POWER_WORDS.items():
            if category == 'emocionales':
                for word in words:
                    if word in all_text:
                        emotional_words_found.append(word)
        
        emotional_score = min(len(emotional_words_found) * 2, 10)
        score += emotional_score
        details['emotional_appeal'] = {
            'score': round(emotional_score, 1),
            'max': 10,
            'words_found': emotional_words_found
        }
        
        # 2. Call to Action (15 puntos)
        cta_words_found = []
        for word in self.POWER_WORDS['accion']:
            if word in all_text:
                cta_words_found.append(word)
        
        cta_score = min(len(cta_words_found) * 5, 15)
        score += cta_score
        details['call_to_action'] = {
            'score': round(cta_score, 1),
            'max': 15,
            'ctas_found': cta_words_found,
            'has_strong_cta': len(cta_words_found) >= 2
        }
        
        # 3. Enfoque en beneficios (10 puntos)
        benefit_words_found = []
        for word in self.POWER_WORDS['beneficios']:
            if word in all_text:
                benefit_words_found.append(word)
        
        benefit_score = min(len(benefit_words_found) * 3, 10)
        score += benefit_score
        details['benefit_focus'] = {
            'score': round(benefit_score, 1),
            'max': 10,
            'benefits_found': benefit_words_found
        }
        
        # 4. Urgencia (10 puntos)
        urgency_words_found = []
        for word in self.POWER_WORDS['urgencia']:
            if word in all_text:
                urgency_words_found.append(word)
        
        urgency_score = min(len(urgency_words_found) * 3, 10)
        score += urgency_score
        details['urgency'] = {
            'score': round(urgency_score, 1),
            'max': 10,
            'urgency_words': urgency_words_found
        }
        
        # 5. Palabras de poder (5 puntos)
        professional_words_found = []
        for word in self.POWER_WORDS['profesionales']:
            if word in all_text:
                professional_words_found.append(word)
        
        power_score = min(len(professional_words_found) * 1.5, 5)
        score += power_score
        details['power_words'] = {
            'score': round(power_score, 1),
            'max': 5,
            'words_found': professional_words_found
        }
        
        return {
            'score': min(50, score),
            'max': 50,
            'percentage': round(min(100, score / 50 * 100), 1),
            'details': details
        }
    
    def _score_compliance(
        self,
        headlines: List[str],
        descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Score de cumplimiento de políticas de Google Ads.
        """
        score = 50.0  # Comenzar con puntuación perfecta
        violations = []
        warnings = []
        
        # Palabras prohibidas
        forbidden_words = [
            '100% garantizado', 'gratis siempre', 'milagro',
            'infalible', 'nunca falla', 'totalmente gratis'
        ]
        
        all_text = ' '.join(headlines + descriptions).lower()
        
        for forbidden in forbidden_words:
            if forbidden in all_text:
                score -= 10
                violations.append(f"Palabra prohibida: '{forbidden}'")
        
        # Validar headlines
        for i, headline in enumerate(headlines):
            # Longitud
            if len(headline) > 30:
                score -= 5
                violations.append(f"Headline {i+1} excede 30 caracteres")
            
            # Todo mayúsculas
            if headline.isupper():
                score -= 3
                violations.append(f"Headline {i+1} en mayúsculas")
            
            # Caracteres prohibidos
            if any(char in headline for char in ['!', '?', '¡', '¿']):
                score -= 2
                warnings.append(f"Headline {i+1} con signos prohibidos")
        
        # Validar descriptions
        for i, desc in enumerate(descriptions):
            if len(desc) > 90:
                score -= 5
                violations.append(f"Description {i+1} excede 90 caracteres")
            
            if desc.isupper():
                score -= 3
                violations.append(f"Description {i+1} en mayúsculas")
        
        score = max(0, score)
        
        return {
            'score': round(score, 1),
            'max': 50,
            'percentage': round(score / 50 * 100, 1),
            'violations': violations,
            'warnings': warnings,
            'is_compliant': len(violations) == 0
        }
    
    def _score_optimization(
        self,
        headlines: List[str],
        descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Score de nivel de optimización.
        """
        score = 0.0
        details = {}
        
        # 1. Cantidad adecuada (20 puntos)
        quantity_score = 0
        
        if len(headlines) >= 15:
            quantity_score += 10
        elif len(headlines) >= 10:
            quantity_score += 7
        elif len(headlines) >= 5:
            quantity_score += 4
        
        if len(descriptions) >= 4:
            quantity_score += 10
        elif len(descriptions) >= 2:
            quantity_score += 5
        
        score += quantity_score
        details['quantity'] = {
            'score': round(quantity_score, 1),
            'max': 20,
            'headlines': len(headlines),
            'descriptions': len(descriptions)
        }
        
        # 2. Variedad (15 puntos)
        variety_score = 0
        
        # Variedad en longitud de headlines
        if headlines:
            lengths = [len(h) for h in headlines]
            if len(set(lengths)) > len(headlines) * 0.5:
                variety_score += 5
        
        # Variedad en contenido (unicidad)
        unique_headlines = len(set(headlines))
        if headlines and unique_headlines == len(headlines):
            variety_score += 5
        
        unique_descriptions = len(set(descriptions))
        if descriptions and unique_descriptions == len(descriptions):
            variety_score += 5
        
        score += variety_score
        details['variety'] = {
            'score': round(variety_score, 1),
            'max': 15,
            'unique_headlines': unique_headlines,
            'unique_descriptions': unique_descriptions
        }
        
        # 3. Uso de números (10 puntos)
        all_text = ' '.join(headlines + descriptions)
        has_numbers = any(char.isdigit() for char in all_text)
        
        number_score = 10 if has_numbers else 5
        score += number_score
        details['numbers'] = {
            'score': round(number_score, 1),
            'max': 10,
            'has_numbers': has_numbers
        }
        
        # 4. Optimización móvil (5 puntos) - headlines cortos
        mobile_friendly = sum(1 for h in headlines if len(h) <= 25)
        mobile_score = (mobile_friendly / len(headlines) * 5) if headlines else 0
        
        score += mobile_score
        details['mobile_optimization'] = {
            'score': round(mobile_score, 1),
            'max': 5,
            'mobile_friendly_headlines': mobile_friendly
        }
        
        return {
            'score': min(50, score),
            'max': 50,
            'percentage': round(min(100, score / 50 * 100), 1),
            'details': details
        }
    
    def _score_uniqueness(
        self,
        headlines: List[str],
        descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Score de originalidad y diferenciación.
        """
        score = 30.0  # Base
        details = {}
        
        all_text = ' '.join(headlines + descriptions).lower()
        
        # 1. Uso de palabras únicas (no comunes)
        common_words = {
            'el', 'la', 'de', 'en', 'y', 'a', 'con', 'para', 'por',
            'más', 'su', 'que', 'no', 'un', 'una', 'es', 'como'
        }
        
        words = [w for w in all_text.split() if len(w) > 3]
        unique_words = [w for w in words if w not in common_words]
        
        uniqueness_ratio = len(set(unique_words)) / len(unique_words) if unique_words else 0
        unique_score = uniqueness_ratio * 10
        
        score += unique_score
        details['unique_vocabulary'] = {
            'score': round(unique_score, 1),
            'max': 10,
            'ratio': round(uniqueness_ratio * 100, 1)
        }
        
        # 2. Diferenciación de templates comunes
        template_phrases = [
            'haz clic aquí', 'más información', 'contacta ahora',
            'llama ya', 'visita nuestra web'
        ]
        
        template_count = sum(1 for phrase in template_phrases if phrase in all_text)
        
        # Penalizar uso excesivo de frases template
        if template_count > 2:
            score -= 5
            details['template_usage'] = {
                'penalty': -5,
                'template_phrases_found': template_count
            }
        
        # 3. Bonus por creatividad (detectar elementos únicos)
        creative_elements = []
        
        # Metáforas o lenguaje figurativo (palabras asociadas)
        creative_words = ['camino', 'puerta', 'luz', 'poder', 'energía', 'vibración']
        for word in creative_words:
            if word in all_text:
                creative_elements.append(word)
        
        if len(creative_elements) > 2:
            score += 5
            details['creative_elements'] = {
                'bonus': 5,
                'elements_found': creative_elements
            }
        
        score = max(0, min(50, score))
        
        return {
            'score': round(score, 1),
            'max': 50,
            'percentage': round(score / 50 * 100, 1),
            'details': details
        }
    
    # =========================================================================
    # ANÁLISIS Y COMPARACIÓN
    # =========================================================================
    
    def _identify_strengths(self, category_scores: Dict[str, Dict]) -> List[Dict[str, str]]:
        """Identifica fortalezas del anuncio."""
        strengths = []
        
        for category, score_data in category_scores.items():
            percentage = score_data.get('percentage', 0)
            
            if percentage >= 80:
                strengths.append({
                    'category': category,
                    'score': score_data['score'],
                    'description': f"Excelente {category} ({percentage:.1f}%)"
                })
        
        # Ordenar por score
        strengths.sort(key=lambda x: x['score'], reverse=True)
        
        return strengths
    
    def _identify_weaknesses(self, category_scores: Dict[str, Dict]) -> List[Dict[str, str]]:
        """Identifica debilidades del anuncio."""
        weaknesses = []
        
        for category, score_data in category_scores.items():
            percentage = score_data.get('percentage', 0)
            
            if percentage < 60:
                weaknesses.append({
                    'category': category,
                    'score': score_data['score'],
                    'percentage': percentage,
                    'description': f"{category.capitalize()} necesita mejoras ({percentage:.1f}%)"
                })
        
        # Ordenar por score (peores primero)
        weaknesses.sort(key=lambda x: x['score'])
        
        return weaknesses
    
    def _generate_recommendations(
        self,
        weaknesses: List[Dict],
        overall_score: float
    ) -> List[Dict[str, Any]]:
        """Genera recomendaciones priorizadas."""
        recommendations = []
        
        # Recomendaciones basadas en debilidades
        for weakness in weaknesses:
            category = weakness['category']
            
            if category == 'quality':
                recommendations.append({
                    'priority': 'high',
                    'category': 'Calidad',
                    'recommendation': 'Revisa longitud de textos y gramática',
                    'expected_impact': '+10-15 puntos'
                })
            
            elif category == 'relevance':
                recommendations.append({
                    'priority': 'high',
                    'category': 'Relevancia',
                    'recommendation': 'Incluye más keywords en headlines',
                    'expected_impact': '+8-12 puntos'
                })
            
            elif category == 'engagement':
                recommendations.append({
                    'priority': 'high',
                    'category': 'Engagement',
                    'recommendation': 'Agrega CTAs claros y urgencia',
                    'expected_impact': '+12-18 puntos'
                })
            
            elif category == 'compliance':
                recommendations.append({
                    'priority': 'critical',
                    'category': 'Cumplimiento',
                    'recommendation': 'Corrige violaciones de políticas inmediatamente',
                    'expected_impact': 'Evitar rechazo del anuncio'
                })
            
            elif category == 'optimization':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'Optimización',
                    'recommendation': 'Agrega más variaciones de headlines',
                    'expected_impact': '+5-8 puntos'
                })
            
            elif category == 'uniqueness':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'Diferenciación',
                    'recommendation': 'Usa lenguaje más único y creativo',
                    'expected_impact': '+3-5 puntos'
                })
        
        # Recomendación general si el score es bajo
        if overall_score < 60:
            recommendations.insert(0, {
                'priority': 'critical',
                'category': 'General',
                'recommendation': 'Score bajo: Considera regenerar el anuncio con IA',
                'expected_impact': '+20-30 puntos potenciales'
            })
        
        # Limitar a top 5
        return recommendations[:5]
    
    def _compare_to_benchmark(self, score: float) -> Dict[str, Any]:
        """Compara score con benchmarks de industria."""
        avg_score = self.benchmarks['avg_score']
        diff = score - avg_score
        
        if score >= self.benchmarks['excellent_threshold']:
            level = 'Excelente'
            description = 'Muy por encima del promedio de industria'
        elif score >= self.benchmarks['good_threshold']:
            level = 'Bueno'
            description = 'Por encima del promedio de industria'
        elif score >= self.benchmarks['acceptable_threshold']:
            level = 'Aceptable'
            description = 'Cerca del promedio de industria'
        else:
            level = 'Bajo'
            description = 'Por debajo del promedio de industria'
        
        return {
            'industry_average': avg_score,
            'your_score': round(score, 1),
            'difference': round(diff, 1),
            'percentage_vs_avg': round((score / avg_score * 100) - 100, 1),
            'level': level,
            'description': description,
            'percentile': self._estimate_percentile(score)
        }
    
    def _estimate_percentile(self, score: float) -> int:
        """Estima percentil basado en score."""
        if score >= 90:
            return 95
        elif score >= 85:
            return 90
        elif score >= 80:
            return 85
        elif score >= 75:
            return 75
        elif score >= 70:
            return 65
        elif score >= 65:
            return 55
        elif score >= 60:
            return 45
        elif score >= 55:
            return 35
        else:
            return 25
    
    def _predict_performance(
        self,
        overall_score: float,
        engagement_score: float,
        quality_score: float
    ) -> Dict[str, Any]:
        """Predice rendimiento esperado basado en score."""
        # CTR estimado
        base_ctr = 3.0  # CTR base
        ctr_multiplier = overall_score / 70  # 70 es score "normal"
        estimated_ctr = base_ctr * ctr_multiplier
        
        # Quality Score de Google
        estimated_quality_score = (overall_score / 10) * 0.7 + 3  # Entre 3-10
        
        # Tasa de conversión estimada
        base_conversion = 4.0
        conversion_multiplier = engagement_score / 40
        estimated_conversion = base_conversion * conversion_multiplier
        
        return {
            'estimated_ctr': round(estimated_ctr, 2),
            'estimated_quality_score': round(estimated_quality_score, 1),
            'estimated_conversion_rate': round(estimated_conversion, 2),
            'confidence': 'medium',
            'note': 'Predicciones basadas en score y benchmarks históricos'
        }
    
    # =========================================================================
    # RANKING COMPARATIVO
    # =========================================================================
    
    def rank_ads(
        self,
        ads: List[Dict[str, Any]],
        keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Rankea múltiples anuncios comparativamente.
        
        Args:
            ads: Lista de anuncios con headlines y descriptions
            keywords: Keywords opcionales
        
        Returns:
            Lista de anuncios rankeados con scores
        """
        logger.info(f"📊 Rankeando {len(ads)} anuncios...")
        
        ranked_ads = []
        
        for i, ad in enumerate(ads):
            # Score del anuncio
            score_result = self.score_ad(
                headlines=ad.get('headlines', []),
                descriptions=ad.get('descriptions', []),
                keywords=keywords,
                compare_to_benchmark=False
            )
            
            ranked_ad = {
                'rank': 0,  # Se asignará después de ordenar
                'ad_index': i,
                'original_ad': ad,
                'score': score_result['overall_score'],
                'grade': score_result['grade'],
                'category_scores': score_result['category_scores'],
                'strengths_count': len(score_result['strengths']),
                'weaknesses_count': len(score_result['weaknesses'])
            }
            
            ranked_ads.append(ranked_ad)
        
        # Ordenar por score
        ranked_ads.sort(key=lambda x: x['score'], reverse=True)
        
        # Asignar ranks
        for i, ad in enumerate(ranked_ads, 1):
            ad['rank'] = i
        
        logger.info(f"✅ Ranking completado")
        logger.info(f"   Mejor score: {ranked_ads[0]['score']:.1f}")
        logger.info(f"   Peor score: {ranked_ads[-1]['score']:.1f}")
        
        return ranked_ads
    
    def compare_ads(
        self,
        ad1: Dict[str, Any],
        ad2: Dict[str, Any],
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compara dos anuncios lado a lado.
        
        Args:
            ad1: Primer anuncio
            ad2: Segundo anuncio
            keywords: Keywords opcionales
        
        Returns:
            Comparación detallada
        """
        # Score de ambos anuncios
        score1 = self.score_ad(
            headlines=ad1.get('headlines', []),
            descriptions=ad1.get('descriptions', []),
            keywords=keywords,
            compare_to_benchmark=False
        )
        
        score2 = self.score_ad(
            headlines=ad2.get('headlines', []),
            descriptions=ad2.get('descriptions', []),
            keywords=keywords,
            compare_to_benchmark=False
        )
        
        # Determinar ganador
        winner = 'ad1' if score1['overall_score'] > score2['overall_score'] else 'ad2'
        difference = abs(score1['overall_score'] - score2['overall_score'])
        
        # Comparación por categoría
        category_comparison = {}
        for category in self.CATEGORY_WEIGHTS.keys():
            score1_cat = score1['category_scores'][category]['score']
            score2_cat = score2['category_scores'][category]['score']
            
            category_comparison[category] = {
                'ad1_score': score1_cat,
                'ad2_score': score2_cat,
                'difference': round(score1_cat - score2_cat, 1),
                'winner': 'ad1' if score1_cat > score2_cat else 'ad2'
            }
        
        comparison = {
            'winner': winner,
            'score_difference': round(difference, 1),
            'ad1_score': score1['overall_score'],
            'ad2_score': score2['overall_score'],
            'ad1_grade': score1['grade'],
            'ad2_grade': score2['grade'],
            'category_comparison': category_comparison,
            'recommendation': self._generate_comparison_recommendation(
                winner,
                difference,
                category_comparison
            )
        }
        
        return comparison
    
    def _generate_comparison_recommendation(
        self,
        winner: str,
        difference: float,
        category_comparison: Dict
    ) -> str:
        """Genera recomendación basada en comparación."""
        if difference > 15:
            return f"Usar {winner} - diferencia significativa de {difference:.1f} puntos"
        elif difference > 5:
            return f"Preferir {winner} - diferencia moderada de {difference:.1f} puntos"
        else:
            return f"Scores similares ({difference:.1f} pts) - considera hacer A/B testing"
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _score_to_grade(self, score: float) -> str:
        """Convierte score a calificación letra."""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
    
    def _score_to_performance_level(self, score: float) -> str:
        """Convierte score a nivel de rendimiento."""
        if score >= 85:
            return 'Excepcional'
        elif score >= 75:
            return 'Excelente'
        elif score >= 65:
            return 'Muy Bueno'
        elif score >= 55:
            return 'Bueno'
        elif score >= 45:
            return 'Aceptable'
        else:
            return 'Necesita Mejoras'
    
    def _generate_summary(
        self,
        score: float,
        strengths: List[Dict],
        weaknesses: List[Dict],
        performance_level: str
    ) -> str:
        """Genera resumen del análisis."""
        summary = f"**Score General:** {score:.1f}/100 ({performance_level})\n\n"
        
        if strengths:
            summary += f"**Fortalezas:** {len(strengths)} áreas destacadas\n"
        
        if weaknesses:
            summary += f"**Áreas de mejora:** {len(weaknesses)} detectadas\n"
        
        if score >= 80:
            summary += "\n✅ Anuncio de alta calidad, listo para publicar"
        elif score >= 65:
            summary += "\n👍 Buen anuncio, con mejoras menores podría ser excelente"
        elif score >= 50:
            summary += "\n⚠️ Anuncio aceptable, requiere optimizaciones"
        else:
            summary += "\n❌ Anuncio necesita mejoras importantes antes de publicar"
        
        return summary
    
    def _update_stats(self, score: float) -> None:
        """Actualiza estadísticas internas."""
        self.stats['total_scored'] += 1
        
        # Actualizar promedio
        total = self.stats['total_scored']
        current_avg = self.stats['avg_score']
        self.stats['avg_score'] = round(
            (current_avg * (total - 1) + score) / total,
            2
        )
        
        # Actualizar mejor/peor
        if score > self.stats['highest_score']:
            self.stats['highest_score'] = score
        
        if score < self.stats['lowest_score']:
            self.stats['lowest_score'] = score
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del scorer."""
        return {
            **self.stats,
            'scoring_history_size': len(self.scoring_history)
        }
    
    def get_scoring_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene historial de scoring."""
        history = self.scoring_history.copy()
        
        if limit:
            history = history[-limit:]
        
        return history


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_ad_scorer(
    business_type: str = 'esoteric',
    strict_mode: bool = False
) -> AdScorer:
    """
    Factory function para crear scorer.
    
    Args:
        business_type: Tipo de negocio
        strict_mode: Modo estricto
    
    Returns:
        Instancia de AdScorer
    """
    return AdScorer(
        business_type=business_type,
        strict_mode=strict_mode
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("⭐ AD SCORER - Ejemplo de Uso")
    print("="*60)
    
    # Crear scorer
    scorer = AdScorer(business_type='esoteric')
    
    # Anuncio de ejemplo
    headlines = [
        'Amarres de Amor Efectivos',
        'Recupera a Tu Pareja Ya',
        'Brujería Profesional Certificada',
        'Resultados Garantizados en 24h',
        'Consulta Gratis Ahora'
    ]
    
    descriptions = [
        'Amarres de amor con magia blanca efectiva. Resultados rápidos garantizados.',
        'Bruja profesional con 15 años de experiencia. Consulta inicial sin costo.',
        'Recupera a tu pareja con rituales poderosos. Discreto y seguro.',
        'Garantía total de satisfacción. Contacta ahora para más información.'
    ]
    
    keywords = ['amarres de amor', 'hechizos', 'brujería profesional']
    
    print(f"\n📊 Evaluando anuncio...")
    print(f"   Headlines: {len(headlines)}")
    print(f"   Descriptions: {len(descriptions)}")
    print(f"   Keywords: {', '.join(keywords)}")
    
    # Score del anuncio
    result = scorer.score_ad(
        headlines=headlines,
        descriptions=descriptions,
        keywords=keywords,
        compare_to_benchmark=True
    )
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("✅ RESULTADO DEL SCORING")
    print("="*60)
    
    print(f"\n⭐ Score General: {result['overall_score']:.1f}/100")
    print(f"   Calificación: {result['grade']}")
    print(f"   Nivel: {result['performance_level']}")
    
    print(f"\n📊 Scores por Categoría:")
    for category, score_data in result['category_scores'].items():
        print(f"   • {category.capitalize()}: {score_data['score']:.1f}/{score_data['max']} ({score_data['percentage']:.1f}%)")
    
    print(f"\n✅ Fortalezas ({len(result['strengths'])}):")
    for strength in result['strengths']:
        print(f"   • {strength['description']}")
    
    if result['weaknesses']:
        print(f"\n⚠️ Áreas de Mejora ({len(result['weaknesses'])}):")
        for weakness in result['weaknesses']:
            print(f"   • {weakness['description']}")
    
    print(f"\n💡 Recomendaciones:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"   {i}. [{rec['priority'].upper()}] {rec['category']}")
        print(f"      {rec['recommendation']}")
        print(f"      Impacto: {rec['expected_impact']}")
    
    # Benchmark
    if result['benchmark_comparison']:
        bench = result['benchmark_comparison']
        print(f"\n📈 Comparación con Industria:")
        print(f"   Promedio industria: {bench['industry_average']:.1f}")
        print(f"   Tu score: {bench['your_score']:.1f}")
        print(f"   Diferencia: {bench['difference']:+.1f} ({bench['percentage_vs_avg']:+.1f}%)")
        print(f"   Nivel: {bench['level']}")
        print(f"   Percentil estimado: Top {100 - bench['percentile']}%")
    
    # Predicción
    pred = result['performance_prediction']
    print(f"\n🔮 Predicción de Rendimiento:")
    print(f"   CTR estimado: {pred['estimated_ctr']:.2f}%")
    print(f"   Quality Score: {pred['estimated_quality_score']:.1f}/10")
    print(f"   Tasa de conversión: {pred['estimated_conversion_rate']:.2f}%")
    
    print(f"\n📝 Resumen:")
    print(result['summary'])
    
    # Estadísticas
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DEL SCORER")
    print("="*60)
    
    stats = scorer.get_statistics()
    print(f"   Total evaluados: {stats['total_scored']}")
    print(f"   Score promedio: {stats['avg_score']:.1f}")
    print(f"   Mejor score: {stats['highest_score']:.1f}")
    
    print("\n" + "="*60)