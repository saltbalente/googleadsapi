"""
📈 PERFORMANCE PREDICTOR - Predictor de Métricas de Rendimiento
Sistema avanzado de predicción de métricas de anuncios basado en IA y machine learning
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
from collections import defaultdict
import math

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformancePredictor:
    """
    Predictor de rendimiento de anuncios que proporciona:
    - Predicción de CTR (Click-Through Rate)
    - Predicción de Quality Score
    - Estimación de CPC (Cost Per Click)
    - Proyección de conversiones
    - Estimación de presupuesto necesario
    - ROI esperado
    - Análisis de competitividad
    - Recomendaciones de optimización
    """
    
    # =========================================================================
    # BENCHMARKS DE INDUSTRIA
    # =========================================================================
    
    INDUSTRY_BENCHMARKS = {
        'esoteric': {
            'avg_ctr': 4.2,
            'avg_conversion_rate': 5.5,
            'avg_cpc': 1.50,
            'avg_quality_score': 6.5,
            'avg_impression_share': 45.0,
            'competitive_level': 'medium'
        },
        'generic': {
            'avg_ctr': 3.17,
            'avg_conversion_rate': 3.75,
            'avg_cpc': 2.69,
            'avg_quality_score': 5.0,
            'avg_impression_share': 35.0,
            'competitive_level': 'high'
        }
    }
    
    # CTR base por tono (%)
    TONE_CTR_MULTIPLIERS = {
        'emocional': 1.15,      # +15%
        'urgente': 1.25,         # +25%
        'profesional': 1.05,     # +5%
        'místico': 1.18,         # +18%
        'esperanzador': 1.10,    # +10%
        'poderoso': 1.22,        # +22%
        'tranquilizador': 1.00,  # base
        'informativo': 1.03      # +3%
    }
    
    # Factores de impacto en CTR (puntos porcentuales)
    CTR_IMPACT_FACTORS = {
        'power_words': 0.4,
        'action_cta': 0.6,
        'numbers': 0.3,
        'benefits_mentioned': 0.5,
        'urgency_words': 0.7,
        'emotional_words': 0.4,
        'length_optimal': 0.3,
        'keyword_relevance': 0.8,
        'ad_extensions': 0.5,
        'mobile_optimized': 0.4
    }
    
    # Factores de Quality Score
    QUALITY_SCORE_FACTORS = {
        'expected_ctr': 0.40,         # 40% del peso
        'ad_relevance': 0.35,         # 35% del peso
        'landing_page_experience': 0.25  # 25% del peso
    }
    
    # Niveles de competencia por keyword
    COMPETITION_LEVELS = {
        'low': {'cpc_multiplier': 0.7, 'impression_share': 65},
        'medium': {'cpc_multiplier': 1.0, 'impression_share': 45},
        'high': {'cpc_multiplier': 1.4, 'impression_share': 30},
        'very_high': {'cpc_multiplier': 1.8, 'impression_share': 20}
    }
    
    def __init__(
        self,
        business_type: str = 'esoteric',
        historical_data: Optional[Dict[str, Any]] = None,
        confidence_threshold: float = 0.7
    ):
        """
        Inicializa el predictor de rendimiento.
        
        Args:
            business_type: Tipo de negocio ('esoteric' o 'generic')
            historical_data: Datos históricos opcionales para mejorar predicciones
            confidence_threshold: Umbral de confianza para predicciones
        """
        self.business_type = business_type
        self.historical_data = historical_data or {}
        self.confidence_threshold = confidence_threshold
        
        # Benchmarks del negocio
        self.benchmarks = self.INDUSTRY_BENCHMARKS.get(
            business_type,
            self.INDUSTRY_BENCHMARKS['generic']
        )
        
        # Historial de predicciones
        self.prediction_history: List[Dict[str, Any]] = []
        
        # Métricas de precisión (si tenemos datos históricos)
        self.accuracy_metrics = {
            'ctr_mae': 0.0,  # Mean Absolute Error
            'cpc_mae': 0.0,
            'total_predictions': 0,
            'accurate_predictions': 0
        }
        
        logger.info(f"✅ PerformancePredictor inicializado")
        logger.info(f"   - Tipo de negocio: {business_type}")
        logger.info(f"   - CTR promedio industria: {self.benchmarks['avg_ctr']}%")
        logger.info(f"   - CPC promedio: ${self.benchmarks['avg_cpc']}")
    
    # =========================================================================
    # PREDICCIÓN COMPLETA
    # =========================================================================
    
    def predict_performance(
        self,
        ad_data: Dict[str, Any],
        keywords: List[str],
        budget: float,
        duration_days: int = 30,
        target_locations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Realiza predicción completa de rendimiento de un anuncio.
        
        Args:
            ad_data: Datos del anuncio (headlines, descriptions, tone, etc.)
            keywords: Lista de palabras clave
            budget: Presupuesto diario (USD)
            duration_days: Duración de la campaña en días
            target_locations: Ubicaciones objetivo (opcional)
        
        Returns:
            Diccionario con predicciones completas
        """
        prediction_id = f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"📈 Iniciando predicción de rendimiento: {prediction_id}")
        logger.info(f"   - Keywords: {len(keywords)}")
        logger.info(f"   - Presupuesto diario: ${budget}")
        logger.info(f"   - Duración: {duration_days} días")
        
        # 1. Analizar características del anuncio
        ad_features = self._analyze_ad_features(ad_data, keywords)
        
        # 2. Predecir CTR
        ctr_prediction = self.predict_ctr(ad_data, keywords)
        
        # 3. Predecir Quality Score
        quality_score = self.predict_quality_score(ad_data, keywords)
        
        # 4. Estimar CPC
        cpc_estimate = self.estimate_cpc(keywords, quality_score)
        
        # 5. Proyectar métricas
        metrics_projection = self._project_metrics(
            ctr=ctr_prediction['predicted_ctr'],
            cpc=cpc_estimate['estimated_cpc'],
            quality_score=quality_score['predicted_score'],
            budget=budget,
            duration_days=duration_days
        )
        
        # 6. Estimar conversiones
        conversion_estimate = self._estimate_conversions(
            clicks=metrics_projection['estimated_clicks'],
            ad_features=ad_features
        )
        
        # 7. Calcular ROI esperado
        roi_calculation = self._calculate_expected_roi(
            total_cost=metrics_projection['total_budget'],
            estimated_conversions=conversion_estimate['estimated_conversions'],
            avg_conversion_value=conversion_estimate['avg_conversion_value']
        )
        
        # 8. Analizar competitividad
        competition_analysis = self._analyze_competition(keywords)
        
        # 9. Generar recomendaciones
        recommendations = self._generate_recommendations(
            ctr_prediction=ctr_prediction,
            quality_score=quality_score,
            cpc_estimate=cpc_estimate,
            competition_analysis=competition_analysis,
            ad_features=ad_features
        )
        
        # Construir resultado completo
        prediction = {
            'prediction_id': prediction_id,
            'timestamp': datetime.now().isoformat(),
            'business_type': self.business_type,
            'input': {
                'keywords': keywords,
                'budget_daily': budget,
                'duration_days': duration_days,
                'target_locations': target_locations or ['Global']
            },
            'ad_analysis': ad_features,
            'ctr_prediction': ctr_prediction,
            'quality_score': quality_score,
            'cpc_estimate': cpc_estimate,
            'metrics_projection': metrics_projection,
            'conversion_estimate': conversion_estimate,
            'roi_calculation': roi_calculation,
            'competition_analysis': competition_analysis,
            'recommendations': recommendations,
            'confidence_summary': self._calculate_overall_confidence([
                ctr_prediction['confidence'],
                quality_score['confidence'],
                cpc_estimate['confidence']
            ]),
            'benchmark_comparison': self._compare_to_benchmarks(
                ctr_prediction['predicted_ctr'],
                quality_score['predicted_score'],
                cpc_estimate['estimated_cpc']
            )
        }
        
        # Guardar en historial
        self.prediction_history.append(prediction)
        
        logger.info(f"✅ Predicción completada: {prediction_id}")
        logger.info(f"   - CTR estimado: {ctr_prediction['predicted_ctr']:.2f}%")
        logger.info(f"   - Quality Score: {quality_score['predicted_score']:.1f}/10")
        logger.info(f"   - CPC estimado: ${cpc_estimate['estimated_cpc']:.2f}")
        logger.info(f"   - Conversiones estimadas: {conversion_estimate['estimated_conversions']}")
        
        return prediction
    
    # =========================================================================
    # PREDICCIÓN DE CTR
    # =========================================================================
    
    def predict_ctr(
        self,
        ad_data: Dict[str, Any],
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Predice el Click-Through Rate (CTR) del anuncio.
        
        Args:
            ad_data: Datos del anuncio
            keywords: Lista de keywords
        
        Returns:
            Diccionario con predicción de CTR
        """
        # CTR base de la industria
        base_ctr = self.benchmarks['avg_ctr']
        
        # Multiplicador por tono
        tone = ad_data.get('tone', 'profesional')
        tone_multiplier = self.TONE_CTR_MULTIPLIERS.get(tone, 1.0)
        
        adjusted_ctr = base_ctr * tone_multiplier
        
        # Analizar características del anuncio
        headlines = ad_data.get('headlines', [])
        descriptions = ad_data.get('descriptions', [])
        all_text = ' '.join(headlines + descriptions).lower()
        
        # Aplicar factores de impacto
        adjustments = 0.0
        detected_features = []
        
        # Palabras de poder
        power_words = ['garantizado', 'efectivo', 'profesional', 'poderoso', 'certificado']
        if any(word in all_text for word in power_words):
            adjustments += self.CTR_IMPACT_FACTORS['power_words']
            detected_features.append('power_words')
        
        # CTAs
        action_words = ['consulta', 'solicita', 'obtén', 'descubre', 'contacta']
        if any(word in all_text for word in action_words):
            adjustments += self.CTR_IMPACT_FACTORS['action_cta']
            detected_features.append('action_cta')
        
        # Números
        if any(char.isdigit() for char in all_text):
            adjustments += self.CTR_IMPACT_FACTORS['numbers']
            detected_features.append('numbers')
        
        # Beneficios
        benefit_words = ['resultado', 'garantía', 'éxito', 'efectivo', 'rápido']
        if any(word in all_text for word in benefit_words):
            adjustments += self.CTR_IMPACT_FACTORS['benefits_mentioned']
            detected_features.append('benefits_mentioned')
        
        # Urgencia
        urgency_words = ['ahora', 'ya', 'hoy', 'inmediato', 'urgente']
        if any(word in all_text for word in urgency_words):
            adjustments += self.CTR_IMPACT_FACTORS['urgency_words']
            detected_features.append('urgency_words')
        
        # Emocionales
        emotional_words = ['amor', 'felicidad', 'paz', 'esperanza', 'confianza']
        if any(word in all_text for word in emotional_words):
            adjustments += self.CTR_IMPACT_FACTORS['emotional_words']
            detected_features.append('emotional_words')
        
        # Longitud óptima
        if headlines:
            avg_headline_length = statistics.mean([len(h) for h in headlines])
            if 20 <= avg_headline_length <= 28:
                adjustments += self.CTR_IMPACT_FACTORS['length_optimal']
                detected_features.append('length_optimal')
        
        # Relevancia de keywords
        keyword_matches = sum(1 for kw in keywords if kw.lower() in all_text)
        keyword_relevance = keyword_matches / len(keywords) if keywords else 0
        
        if keyword_relevance > 0.5:
            adjustments += self.CTR_IMPACT_FACTORS['keyword_relevance'] * keyword_relevance
            detected_features.append('keyword_relevance')
        
        # CTR predicho
        predicted_ctr = adjusted_ctr + adjustments
        
        # Calcular confianza
        confidence = self._calculate_ctr_confidence(
            len(detected_features),
            keyword_relevance,
            tone_multiplier
        )
        
        # Rango de predicción (min/max)
        ctr_range = self._calculate_prediction_range(predicted_ctr, confidence)
        
        result = {
            'predicted_ctr': round(predicted_ctr, 2),
            'base_ctr': base_ctr,
            'tone_multiplier': tone_multiplier,
            'adjustments': round(adjustments, 2),
            'detected_features': detected_features,
            'feature_count': len(detected_features),
            'keyword_relevance': round(keyword_relevance * 100, 1),
            'confidence': confidence,
            'confidence_level': self._confidence_to_level(confidence),
            'range': {
                'min': round(ctr_range[0], 2),
                'max': round(ctr_range[1], 2)
            },
            'comparison_to_benchmark': {
                'industry_avg': base_ctr,
                'predicted_vs_industry': round(
                    ((predicted_ctr - base_ctr) / base_ctr * 100), 1
                )
            }
        }
        
        return result
    
    def _calculate_ctr_confidence(
        self,
        feature_count: int,
        keyword_relevance: float,
        tone_multiplier: float
    ) -> float:
        """Calcula nivel de confianza de la predicción de CTR."""
        base_confidence = 0.6
        
        # Más características = mayor confianza
        feature_bonus = min(feature_count * 0.05, 0.2)
        
        # Alta relevancia de keywords = mayor confianza
        keyword_bonus = keyword_relevance * 0.1
        
        # Tono con multiplicador alto = mayor certeza
        tone_bonus = (tone_multiplier - 1.0) * 0.05
        
        total_confidence = base_confidence + feature_bonus + keyword_bonus + tone_bonus
        
        return round(min(0.95, total_confidence), 2)
    
    # =========================================================================
    # PREDICCIÓN DE QUALITY SCORE
    # =========================================================================
    
    def predict_quality_score(
        self,
        ad_data: Dict[str, Any],
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Predice el Quality Score del anuncio (1-10).
        
        Args:
            ad_data: Datos del anuncio
            keywords: Lista de keywords
        
        Returns:
            Diccionario con predicción de Quality Score
        """
        # Componentes del Quality Score
        
        # 1. Expected CTR (40% del peso)
        ctr_prediction = self.predict_ctr(ad_data, keywords)
        expected_ctr = ctr_prediction['predicted_ctr']
        
        # Convertir CTR a score 1-10
        ctr_score = self._ctr_to_score(expected_ctr)
        
        # 2. Ad Relevance (35% del peso)
        ad_relevance_score = self._calculate_ad_relevance(ad_data, keywords)
        
        # 3. Landing Page Experience (25% del peso) - estimado
        landing_page_score = self._estimate_landing_page_score(ad_data)
        
        # Quality Score ponderado
        quality_score = (
            ctr_score * self.QUALITY_SCORE_FACTORS['expected_ctr'] +
            ad_relevance_score * self.QUALITY_SCORE_FACTORS['ad_relevance'] +
            landing_page_score * self.QUALITY_SCORE_FACTORS['landing_page_experience']
        )
        
        # Ajustes por datos históricos si existen
        if self.historical_data.get('avg_quality_score'):
            historical_avg = self.historical_data['avg_quality_score']
            quality_score = (quality_score * 0.7) + (historical_avg * 0.3)
        
        # Calcular confianza
        confidence = self._calculate_quality_score_confidence(
            ctr_prediction['confidence'],
            ad_relevance_score,
            landing_page_score
        )
        
        result = {
            'predicted_score': round(quality_score, 1),
            'grade': self._quality_score_to_grade(quality_score),
            'components': {
                'expected_ctr': {
                    'score': round(ctr_score, 1),
                    'weight': self.QUALITY_SCORE_FACTORS['expected_ctr'],
                    'contribution': round(ctr_score * self.QUALITY_SCORE_FACTORS['expected_ctr'], 1)
                },
                'ad_relevance': {
                    'score': round(ad_relevance_score, 1),
                    'weight': self.QUALITY_SCORE_FACTORS['ad_relevance'],
                    'contribution': round(ad_relevance_score * self.QUALITY_SCORE_FACTORS['ad_relevance'], 1)
                },
                'landing_page': {
                    'score': round(landing_page_score, 1),
                    'weight': self.QUALITY_SCORE_FACTORS['landing_page_experience'],
                    'contribution': round(landing_page_score * self.QUALITY_SCORE_FACTORS['landing_page_experience'], 1)
                }
            },
            'confidence': confidence,
            'confidence_level': self._confidence_to_level(confidence),
            'impact_on_cpc': self._quality_score_cpc_impact(quality_score),
            'recommendations': self._quality_score_recommendations(
                ctr_score, 
                ad_relevance_score, 
                landing_page_score
            )
        }
        
        return result
    
    def _ctr_to_score(self, ctr: float) -> float:
        """Convierte CTR a score 1-10."""
        # CTR promedio de industria = 5
        # CTR alto (>6%) = 10
        # CTR bajo (<2%) = 1
        
        if ctr >= 6.0:
            return 10.0
        elif ctr >= 5.0:
            return 8.0 + (ctr - 5.0) * 2
        elif ctr >= 4.0:
            return 6.0 + (ctr - 4.0) * 2
        elif ctr >= 3.0:
            return 4.0 + (ctr - 3.0) * 2
        elif ctr >= 2.0:
            return 2.0 + (ctr - 2.0) * 2
        else:
            return max(1.0, ctr)
    
    def _calculate_ad_relevance(
        self,
        ad_data: Dict[str, Any],
        keywords: List[str]
    ) -> float:
        """Calcula score de relevancia del anuncio (1-10)."""
        headlines = ad_data.get('headlines', [])
        descriptions = ad_data.get('descriptions', [])
        all_text = ' '.join(headlines + descriptions).lower()
        
        # Contar matches de keywords
        keyword_matches = 0
        for keyword in keywords:
            if keyword.lower() in all_text:
                keyword_matches += 1
        
        # Ratio de keywords usadas
        keyword_ratio = keyword_matches / len(keywords) if keywords else 0
        
        # Score base por ratio
        base_score = keyword_ratio * 10
        
        # Bonus: keywords en títulos (más importante)
        headlines_text = ' '.join(headlines).lower()
        keywords_in_headlines = sum(
            1 for kw in keywords if kw.lower() in headlines_text
        )
        headline_bonus = (keywords_in_headlines / len(keywords)) * 2 if keywords else 0
        
        relevance_score = min(10.0, base_score + headline_bonus)
        
        return relevance_score
    
    def _estimate_landing_page_score(self, ad_data: Dict[str, Any]) -> float:
        """Estima score de landing page (1-10) basado en datos disponibles."""
        # En ausencia de datos reales de landing page, usar heurísticas
        
        base_score = 6.0  # Asumimos página decente por defecto
        
        # Ajustes basados en consistencia del anuncio
        headlines = ad_data.get('headlines', [])
        descriptions = ad_data.get('descriptions', [])
        
        # Si el anuncio es coherente, asumimos landing page alineada
        if len(headlines) >= 10 and len(descriptions) >= 3:
            base_score += 1.0
        
        # Si tiene CTA clara, asumimos landing page optimizada
        all_text = ' '.join(headlines + descriptions).lower()
        if any(word in all_text for word in ['consulta', 'solicita', 'contacta']):
            base_score += 0.5
        
        # Si menciona beneficios, asumimos landing page persuasiva
        if any(word in all_text for word in ['resultado', 'garantía', 'efectivo']):
            base_score += 0.5
        
        return min(10.0, base_score)
    
    def _calculate_quality_score_confidence(
        self,
        ctr_confidence: float,
        ad_relevance: float,
        landing_page_score: float
    ) -> float:
        """Calcula confianza de la predicción de Quality Score."""
        # Promedio ponderado de confianzas
        
        # CTR confidence ya calculada
        ctr_weight = 0.5
        
        # Confianza en ad relevance (basado en score)
        relevance_confidence = ad_relevance / 10 * 0.3
        
        # Landing page tiene baja confianza (estimado)
        landing_confidence = 0.2
        
        total_confidence = (
            ctr_confidence * ctr_weight +
            relevance_confidence +
            landing_confidence
        )
        
        return round(total_confidence, 2)
    
    def _quality_score_to_grade(self, score: float) -> str:
        """Convierte Quality Score a grado."""
        if score >= 9:
            return 'Excelente'
        elif score >= 7:
            return 'Bueno'
        elif score >= 5:
            return 'Promedio'
        elif score >= 3:
            return 'Bajo'
        else:
            return 'Muy Bajo'
    
    def _quality_score_cpc_impact(self, quality_score: float) -> Dict[str, Any]:
        """Calcula impacto del Quality Score en el CPC."""
        # Quality Score afecta inversamente al CPC
        # QS 10 = hasta 50% descuento
        # QS 1 = hasta 400% incremento
        
        if quality_score >= 9:
            discount = 0.40  # 40% descuento
        elif quality_score >= 7:
            discount = 0.20  # 20% descuento
        elif quality_score >= 5:
            discount = 0.0   # Sin cambio
        elif quality_score >= 3:
            discount = -0.50  # 50% incremento
        else:
            discount = -1.00  # 100% incremento
        
        return {
            'multiplier': round(1 + discount, 2),
            'expected_change': f"{discount * 100:+.0f}%",
            'explanation': self._get_cpc_impact_explanation(discount)
        }
    
    def _get_cpc_impact_explanation(self, discount: float) -> str:
        """Genera explicación del impacto en CPC."""
        if discount > 0:
            return f"Quality Score alto: pagarás menos por clic ({discount*100:.0f}% descuento)"
        elif discount == 0:
            return "Quality Score promedio: CPC estándar"
        else:
            return f"Quality Score bajo: pagarás más por clic ({abs(discount)*100:.0f}% incremento)"
    
    def _quality_score_recommendations(
        self,
        ctr_score: float,
        relevance_score: float,
        landing_score: float
    ) -> List[str]:
        """Genera recomendaciones para mejorar Quality Score."""
        recommendations = []
        
        if ctr_score < 6:
            recommendations.append(
                "Mejora CTR: Usa titulares más atractivos y llamadas a la acción claras"
            )
        
        if relevance_score < 7:
            recommendations.append(
                "Aumenta relevancia: Incluye más keywords en títulos y descripciones"
            )
        
        if landing_score < 7:
            recommendations.append(
                "Optimiza landing page: Asegura que el contenido coincida con el anuncio"
            )
        
        if not recommendations:
            recommendations.append(
                "Mantén el buen trabajo: Quality Score está en buen nivel"
            )
        
        return recommendations
    
    # =========================================================================
    # ESTIMACIÓN DE CPC
    # =========================================================================
    
    def estimate_cpc(
        self,
        keywords: List[str],
        quality_score_data: Dict[str, Any],
        competition_level: str = 'medium'
    ) -> Dict[str, Any]:
        """
        Estima el Cost Per Click (CPC).
        
        Args:
            keywords: Lista de keywords
            quality_score_data: Datos de Quality Score predicho
            competition_level: Nivel de competencia ('low', 'medium', 'high', 'very_high')
        
        Returns:
            Diccionario con estimación de CPC
        """
        # CPC base de la industria
        base_cpc = self.benchmarks['avg_cpc']
        
        # Ajuste por competencia
        competition_data = self.COMPETITION_LEVELS.get(
            competition_level,
            self.COMPETITION_LEVELS['medium']
        )
        cpc_with_competition = base_cpc * competition_data['cpc_multiplier']
        
        # Ajuste por Quality Score
        quality_score = quality_score_data.get('predicted_score', 5.0)
        quality_multiplier = quality_score_data['impact_on_cpc']['multiplier']
        
        estimated_cpc = cpc_with_competition * quality_multiplier
        
        # Ajuste por número de keywords (más keywords = más competencia)
        keyword_count_factor = 1.0
        if len(keywords) > 20:
            keyword_count_factor = 1.1
        elif len(keywords) > 50:
            keyword_count_factor = 1.2
        
        estimated_cpc *= keyword_count_factor
        
        # Calcular rango de CPC
        confidence = 0.75  # Confianza moderada en estimación de CPC
        cpc_range = self._calculate_prediction_range(estimated_cpc, confidence)
        
        result = {
            'estimated_cpc': round(estimated_cpc, 2),
            'base_cpc': base_cpc,
            'competition_multiplier': competition_data['cpc_multiplier'],
            'quality_score_multiplier': quality_multiplier,
            'keyword_count_factor': keyword_count_factor,
            'range': {
                'min': round(cpc_range[0], 2),
                'max': round(cpc_range[1], 2)
            },
            'confidence': confidence,
            'confidence_level': self._confidence_to_level(confidence),
            'factors': {
                'competition': competition_level,
                'quality_score': quality_score,
                'keyword_count': len(keywords)
            },
            'comparison_to_benchmark': {
                'industry_avg': base_cpc,
                'predicted_vs_industry': round(
                    ((estimated_cpc - base_cpc) / base_cpc * 100), 1
                )
            }
        }
        
        return result
    
    # =========================================================================
    # PROYECCIÓN DE MÉTRICAS
    # =========================================================================
    
    def _project_metrics(
        self,
        ctr: float,
        cpc: float,
        quality_score: float,
        budget: float,
        duration_days: int
    ) -> Dict[str, Any]:
        """
        Proyecta métricas basándose en CTR, CPC y presupuesto.
        
        Args:
            ctr: Click-through rate (%)
            cpc: Cost per click (USD)
            quality_score: Quality Score (1-10)
            budget: Presupuesto diario (USD)
            duration_days: Duración en días
        
        Returns:
            Diccionario con métricas proyectadas
        """
        # Presupuesto total
        total_budget = budget * duration_days
        
        # Clics estimados
        estimated_clicks = int(total_budget / cpc)
        
        # Impresiones estimadas (basado en CTR)
        estimated_impressions = int(estimated_clicks / (ctr / 100))
        
        # Impression Share estimado (basado en Quality Score y presupuesto)
        impression_share = self._estimate_impression_share(
            quality_score,
            budget
        )
        
        # Métricas diarias
        daily_clicks = int(estimated_clicks / duration_days)
        daily_impressions = int(estimated_impressions / duration_days)
        
        projection = {
            'duration_days': duration_days,
            'total_budget': round(total_budget, 2),
            'budget_daily': budget,
            'estimated_impressions': estimated_impressions,
            'estimated_clicks': estimated_clicks,
            'estimated_ctr': ctr,
            'estimated_cpc': cpc,
            'impression_share': round(impression_share, 1),
            'daily_metrics': {
                'impressions': daily_impressions,
                'clicks': daily_clicks,
                'cost': budget
            },
            'weekly_metrics': {
                'impressions': daily_impressions * 7,
                'clicks': daily_clicks * 7,
                'cost': budget * 7
            },
            'monthly_metrics': {
                'impressions': daily_impressions * 30,
                'clicks': daily_clicks * 30,
                'cost': budget * 30
            }
        }
        
        return projection
    
    def _estimate_impression_share(
        self,
        quality_score: float,
        budget: float
    ) -> float:
        """Estima impression share basado en Quality Score y presupuesto."""
        # Base: quality score alto = más impresiones
        base_share = (quality_score / 10) * 50  # Max 50%
        
        # Ajuste por presupuesto (presupuesto alto = más share)
        if budget >= 50:
            budget_bonus = 15
        elif budget >= 20:
            budget_bonus = 10
        elif budget >= 10:
            budget_bonus = 5
        else:
            budget_bonus = 0
        
        estimated_share = min(85, base_share + budget_bonus)
        
        return estimated_share
    
    # =========================================================================
    # ESTIMACIÓN DE CONVERSIONES
    # =========================================================================
    
    def _estimate_conversions(
        self,
        clicks: int,
        ad_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estima conversiones basándose en clics y características del anuncio.
        
        Args:
            clicks: Número de clics estimados
            ad_features: Características del anuncio
        
        Returns:
            Diccionario con estimación de conversiones
        """
        # Tasa de conversión base de la industria
        base_conversion_rate = self.benchmarks['avg_conversion_rate']
        
        # Ajustes por características del anuncio
        adjustments = 0.0
        
        # Si tiene CTA fuerte
        if ad_features.get('has_strong_cta'):
            adjustments += 0.5
        
        # Si menciona beneficios
        if ad_features.get('mentions_benefits'):
            adjustments += 0.3
        
        # Si tiene urgencia
        if ad_features.get('has_urgency'):
            adjustments += 0.4
        
        # Si es emocional
        if ad_features.get('is_emotional'):
            adjustments += 0.3
        
        estimated_conversion_rate = base_conversion_rate + adjustments
        
        # Conversiones estimadas
        estimated_conversions = int(clicks * (estimated_conversion_rate / 100))
        
        # Valor promedio de conversión (esotérico: consultas de $50-200)
        avg_conversion_value = 75.0  # USD promedio
        
        # Valor total de conversiones
        total_conversion_value = estimated_conversions * avg_conversion_value
        
        result = {
            'estimated_conversions': estimated_conversions,
            'conversion_rate': round(estimated_conversion_rate, 2),
            'base_conversion_rate': base_conversion_rate,
            'adjustments': round(adjustments, 2),
            'avg_conversion_value': avg_conversion_value,
            'total_conversion_value': round(total_conversion_value, 2),
            'conversions_per_day': round(estimated_conversions / 30, 1),  # Asumiendo 30 días
            'confidence': 0.65  # Confianza moderada
        }
        
        return result
    
    # =========================================================================
    # CÁLCULO DE ROI
    # =========================================================================
    
    def _calculate_expected_roi(
        self,
        total_cost: float,
        estimated_conversions: int,
        avg_conversion_value: float
    ) -> Dict[str, Any]:
        """
        Calcula ROI esperado.
        
        Args:
            total_cost: Costo total de la campaña
            estimated_conversions: Conversiones estimadas
            avg_conversion_value: Valor promedio por conversión
        
        Returns:
            Diccionario con cálculo de ROI
        """
        total_revenue = estimated_conversions * avg_conversion_value
        profit = total_revenue - total_cost
        
        roi_percentage = (profit / total_cost * 100) if total_cost > 0 else 0
        roas = (total_revenue / total_cost) if total_cost > 0 else 0
        
        # Cost per acquisition
        cpa = (total_cost / estimated_conversions) if estimated_conversions > 0 else 0
        
        result = {
            'total_cost': round(total_cost, 2),
            'total_revenue': round(total_revenue, 2),
            'profit': round(profit, 2),
            'roi_percentage': round(roi_percentage, 1),
            'roas': round(roas, 2),
            'cpa': round(cpa, 2),
            'breakeven_conversions': int(total_cost / avg_conversion_value) if avg_conversion_value > 0 else 0,
            'is_profitable': profit > 0,
            'profitability_level': self._classify_profitability(roi_percentage)
        }
        
        return result
    
    def _classify_profitability(self, roi: float) -> str:
        """Clasifica nivel de rentabilidad."""
        if roi >= 200:
            return 'Excelente'
        elif roi >= 100:
            return 'Muy Bueno'
        elif roi >= 50:
            return 'Bueno'
        elif roi >= 0:
            return 'Marginal'
        else:
            return 'No Rentable'
    
    # =========================================================================
    # ANÁLISIS DE COMPETENCIA
    # =========================================================================
    
    def _analyze_competition(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Analiza nivel de competencia basándose en keywords.
        
        Args:
            keywords: Lista de keywords
        
        Returns:
            Análisis de competencia
        """
        # Heurísticas simples para competencia
        # En producción, usar datos reales de Google Keyword Planner
        
        competitive_keywords = [
            'amor', 'dinero', 'trabajo', 'suerte', 'éxito',
            'salud', 'negocio', 'pareja', 'matrimonio'
        ]
        
        # Contar keywords competitivas
        competitive_count = sum(
            1 for kw in keywords 
            if any(comp in kw.lower() for comp in competitive_keywords)
        )
        
        competition_ratio = competitive_count / len(keywords) if keywords else 0
        
        # Clasificar nivel
        if competition_ratio >= 0.7:
            level = 'very_high'
        elif competition_ratio >= 0.5:
            level = 'high'
        elif competition_ratio >= 0.3:
            level = 'medium'
        else:
            level = 'low'
        
        competition_data = self.COMPETITION_LEVELS[level]
        
        analysis = {
            'level': level,
            'level_label': level.replace('_', ' ').title(),
            'competitive_keywords': competitive_count,
            'total_keywords': len(keywords),
            'competition_ratio': round(competition_ratio * 100, 1),
            'cpc_multiplier': competition_data['cpc_multiplier'],
            'expected_impression_share': competition_data['impression_share'],
            'recommendations': self._get_competition_recommendations(level)
        }
        
        return analysis
    
    def _get_competition_recommendations(self, level: str) -> List[str]:
        """Genera recomendaciones basadas en nivel de competencia."""
        recommendations = {
            'low': [
                "Aprovecha la baja competencia para posicionarte",
                "Considera aumentar presupuesto para capturar más mercado"
            ],
            'medium': [
                "Optimiza Quality Score para reducir CPC",
                "Usa long-tail keywords para nichos específicos"
            ],
            'high': [
                "Enfócate en keywords específicas menos competidas",
                "Mejora landing page para aumentar conversiones",
                "Considera remarketing para maximizar ROI"
            ],
            'very_high': [
                "Busca keywords de nicho con menor competencia",
                "Invierte en Quality Score alto para reducir costos",
                "Considera canales alternativos (Display, YouTube)",
                "Usa audiencias personalizadas para segmentar mejor"
            ]
        }
        
        return recommendations.get(level, [])
    
    # =========================================================================
    # ANÁLISIS DE CARACTERÍSTICAS DEL ANUNCIO
    # =========================================================================
    
    def _analyze_ad_features(
        self,
        ad_data: Dict[str, Any],
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Analiza características del anuncio."""
        headlines = ad_data.get('headlines', [])
        descriptions = ad_data.get('descriptions', [])
        all_text = ' '.join(headlines + descriptions).lower()
        
        features = {
            'has_strong_cta': any(
                word in all_text 
                for word in ['consulta', 'solicita', 'contacta', 'llama']
            ),
            'mentions_benefits': any(
                word in all_text 
                for word in ['resultado', 'garantía', 'éxito', 'efectivo']
            ),
            'has_urgency': any(
                word in all_text 
                for word in ['ahora', 'ya', 'hoy', 'inmediato', 'urgente']
            ),
            'is_emotional': any(
                word in all_text 
                for word in ['amor', 'felicidad', 'paz', 'esperanza']
            ),
            'uses_numbers': any(char.isdigit() for char in all_text),
            'keyword_count': len(keywords),
            'headline_count': len(headlines),
            'description_count': len(descriptions),
            'avg_headline_length': round(
                statistics.mean([len(h) for h in headlines]) if headlines else 0,
                1
            ),
            'avg_description_length': round(
                statistics.mean([len(d) for d in descriptions]) if descriptions else 0,
                1
            )
        }
        
        return features
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _calculate_prediction_range(
        self,
        predicted_value: float,
        confidence: float
    ) -> Tuple[float, float]:
        """
        Calcula rango de predicción (min/max) basado en confianza.
        
        Args:
            predicted_value: Valor predicho
            confidence: Nivel de confianza (0-1)
        
        Returns:
            Tupla (min, max)
        """
        # Mayor confianza = rango más estrecho
        variance_factor = 1 - confidence
        
        min_value = predicted_value * (1 - variance_factor * 0.3)
        max_value = predicted_value * (1 + variance_factor * 0.3)
        
        return (min_value, max_value)
    
    def _confidence_to_level(self, confidence: float) -> str:
        """Convierte confianza numérica a nivel textual."""
        if confidence >= 0.85:
            return 'Very High'
        elif confidence >= 0.70:
            return 'High'
        elif confidence >= 0.55:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_overall_confidence(self, confidences: List[float]) -> Dict[str, Any]:
        """Calcula confianza general de la predicción."""
        if not confidences:
            return {'score': 0.5, 'level': 'Low'}
        
        avg_confidence = statistics.mean(confidences)
        
        return {
            'score': round(avg_confidence, 2),
            'level': self._confidence_to_level(avg_confidence),
            'components': {
                'ctr': confidences[0] if len(confidences) > 0 else 0,
                'quality_score': confidences[1] if len(confidences) > 1 else 0,
                'cpc': confidences[2] if len(confidences) > 2 else 0
            }
        }
    
    def _compare_to_benchmarks(
        self,
        ctr: float,
        quality_score: float,
        cpc: float
    ) -> Dict[str, Any]:
        """Compara predicciones con benchmarks de industria."""
        return {
            'ctr': {
                'predicted': ctr,
                'benchmark': self.benchmarks['avg_ctr'],
                'vs_benchmark': round(
                    ((ctr - self.benchmarks['avg_ctr']) / self.benchmarks['avg_ctr'] * 100),
                    1
                ),
                'performance': 'above' if ctr > self.benchmarks['avg_ctr'] else 'below'
            },
            'quality_score': {
                'predicted': quality_score,
                'benchmark': self.benchmarks['avg_quality_score'],
                'vs_benchmark': round(quality_score - self.benchmarks['avg_quality_score'], 1),
                'performance': 'above' if quality_score > self.benchmarks['avg_quality_score'] else 'below'
            },
            'cpc': {
                'predicted': cpc,
                'benchmark': self.benchmarks['avg_cpc'],
                'vs_benchmark': round(
                    ((cpc - self.benchmarks['avg_cpc']) / self.benchmarks['avg_cpc'] * 100),
                    1
                ),
                'performance': 'below' if cpc < self.benchmarks['avg_cpc'] else 'above'  # Invertido: menos CPC es mejor
            }
        }
    
    def _generate_recommendations(
        self,
        ctr_prediction: Dict,
        quality_score: Dict,
        cpc_estimate: Dict,
        competition_analysis: Dict,
        ad_features: Dict
    ) -> List[Dict[str, str]]:
        """Genera recomendaciones estratégicas."""
        recommendations = []
        
        # CTR bajo
        if ctr_prediction['predicted_ctr'] < self.benchmarks['avg_ctr']:
            recommendations.append({
                'category': 'CTR',
                'priority': 'high',
                'recommendation': 'Mejora titulares con palabras de poder y urgencia',
                'expected_impact': f"+{(self.benchmarks['avg_ctr'] - ctr_prediction['predicted_ctr']):.1f}% CTR"
            })
        
        # Quality Score bajo
        if quality_score['predicted_score'] < 7:
            recommendations.append({
                'category': 'Quality Score',
                'priority': 'high',
                'recommendation': quality_score['recommendations'][0],
                'expected_impact': 'Reducción de CPC hasta 20%'
            })
        
        # CPC alto
        if cpc_estimate['estimated_cpc'] > self.benchmarks['avg_cpc'] * 1.2:
            recommendations.append({
                'category': 'CPC',
                'priority': 'medium',
                'recommendation': 'Optimiza Quality Score para reducir costos',
                'expected_impact': f"-${(cpc_estimate['estimated_cpc'] - self.benchmarks['avg_cpc']):.2f} por clic"
            })
        
        # Competencia alta
        if competition_analysis['level'] in ['high', 'very_high']:
            recommendations.append({
                'category': 'Competencia',
                'priority': 'medium',
                'recommendation': competition_analysis['recommendations'][0],
                'expected_impact': 'Mayor visibilidad en nicho específico'
            })
        
        # Sin CTA
        if not ad_features.get('has_strong_cta'):
            recommendations.append({
                'category': 'Conversión',
                'priority': 'high',
                'recommendation': 'Agrega llamada a la acción clara en descripciones',
                'expected_impact': '+0.5-1% tasa de conversión'
            })
        
        return recommendations
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del predictor."""
        return {
            'business_type': self.business_type,
            'total_predictions': len(self.prediction_history),
            'accuracy_metrics': self.accuracy_metrics,
            'benchmarks': self.benchmarks
        }
    
    def get_prediction_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene historial de predicciones."""
        history = self.prediction_history.copy()
        
        if limit:
            history = history[-limit:]
        
        return history


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_performance_predictor(
    business_type: str = 'esoteric',
    historical_data: Optional[Dict] = None
) -> PerformancePredictor:
    """
    Factory function para crear predictor.
    
    Args:
        business_type: Tipo de negocio
        historical_data: Datos históricos opcionales
    
    Returns:
        Instancia de PerformancePredictor
    """
    return PerformancePredictor(
        business_type=business_type,
        historical_data=historical_data
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("📈 PERFORMANCE PREDICTOR - Ejemplo de Uso")
    print("="*60)
    
    # Crear predictor
    predictor = PerformancePredictor(business_type='esoteric')
    
    # Datos de ejemplo
    ad_data = {
        'headlines': [
            'Amarres de Amor Efectivos',
            'Recupera a Tu Pareja Ya',
            'Brujería Profesional Certificada',
            'Resultados Garantizados en 24h'
        ],
        'descriptions': [
            'Amarres de amor con magia blanca efectiva. Resultados rápidos garantizados.',
            'Bruja profesional con experiencia. Consulta gratis.',
            'Recupera a tu pareja ahora. Discreto y seguro.'
        ],
        'tone': 'emocional'
    }
    
    keywords = [
        'amarres de amor',
        'hechizos efectivos',
        'brujería profesional',
        'magia blanca',
        'recuperar pareja'
    ]
    
    budget = 20.0  # USD diarios
    duration = 30  # días
    
    print(f"\n📊 DATOS DE ENTRADA:")
    print(f"   - Keywords: {len(keywords)}")
    print(f"   - Presupuesto diario: ${budget}")
    print(f"   - Duración: {duration} días")
    print(f"   - Tono: {ad_data['tone']}")
    
    # Realizar predicción completa
    print("\n🔮 Realizando predicción de rendimiento...")
    
    prediction = predictor.predict_performance(
        ad_data=ad_data,
        keywords=keywords,
        budget=budget,
        duration_days=duration
    )
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("✅ PREDICCIÓN COMPLETADA")
    print("="*60)
    
    # CTR
    ctr = prediction['ctr_prediction']
    print(f"\n📊 CTR (Click-Through Rate):")
    print(f"   Predicho: {ctr['predicted_ctr']:.2f}%")
    print(f"   Rango: {ctr['range']['min']:.2f}% - {ctr['range']['max']:.2f}%")
    print(f"   vs Industria: {ctr['comparison_to_benchmark']['predicted_vs_industry']:+.1f}%")
    print(f"   Confianza: {ctr['confidence_level']} ({ctr['confidence']:.0%})")
    print(f"   Características detectadas: {', '.join(ctr['detected_features'][:3])}")
    
    # Quality Score
    qs = prediction['quality_score']
    print(f"\n⭐ Quality Score:")
    print(f"   Predicho: {qs['predicted_score']:.1f}/10 ({qs['grade']})")
    print(f"   Componentes:")
    print(f"      - Expected CTR: {qs['components']['expected_ctr']['score']:.1f}/10")
    print(f"      - Ad Relevance: {qs['components']['ad_relevance']['score']:.1f}/10")
    print(f"      - Landing Page: {qs['components']['landing_page']['score']:.1f}/10")
    print(f"   Impacto en CPC: {qs['impact_on_cpc']['expected_change']}")
    print(f"   Confianza: {qs['confidence_level']} ({qs['confidence']:.0%})")
    
    # CPC
    cpc = prediction['cpc_estimate']
    print(f"\n💰 CPC (Cost Per Click):")
    print(f"   Estimado: ${cpc['estimated_cpc']:.2f}")
    print(f"   Rango: ${cpc['range']['min']:.2f} - ${cpc['range']['max']:.2f}")
    print(f"   vs Industria: {cpc['comparison_to_benchmark']['predicted_vs_industry']:+.1f}%")
    print(f"   Factores:")
    print(f"      - Competencia: {cpc['factors']['competition']}")
    print(f"      - Quality Score: {cpc['factors']['quality_score']:.1f}/10")
    
    # Métricas proyectadas
    metrics = prediction['metrics_projection']
    print(f"\n📈 PROYECCIÓN DE MÉTRICAS ({duration} días):")
    print(f"   Presupuesto total: ${metrics['total_budget']:,.2f}")
    print(f"   Impresiones estimadas: {metrics['estimated_impressions']:,}")
    print(f"   Clics estimados: {metrics['estimated_clicks']:,}")
    print(f"   Impression Share: {metrics['impression_share']:.1f}%")
    print(f"\n   Métricas diarias:")
    print(f"      - Impresiones: {metrics['daily_metrics']['impressions']:,}")
    print(f"      - Clics: {metrics['daily_metrics']['clicks']:,}")
    print(f"      - Costo: ${metrics['daily_metrics']['cost']:.2f}")
    
    # Conversiones
    conv = prediction['conversion_estimate']
    print(f"\n🎯 CONVERSIONES ESTIMADAS:")
    print(f"   Total: {conv['estimated_conversions']}")
    print(f"   Tasa de conversión: {conv['conversion_rate']:.2f}%")
    print(f"   Por día: {conv['conversions_per_day']:.1f}")
    print(f"   Valor promedio: ${conv['avg_conversion_value']:.2f}")
    print(f"   Valor total: ${conv['total_conversion_value']:,.2f}")
    
    # ROI
    roi = prediction['roi_calculation']
    print(f"\n💹 ROI (Return on Investment):")
    print(f"   Costo total: ${roi['total_cost']:,.2f}")
    print(f"   Revenue estimado: ${roi['total_revenue']:,.2f}")
    print(f"   Ganancia: ${roi['profit']:,.2f}")
    print(f"   ROI: {roi['roi_percentage']:,.1f}%")
    print(f"   ROAS: {roi['roas']:.2f}x")
    print(f"   CPA: ${roi['cpa']:.2f}")
    print(f"   Nivel: {roi['profitability_level']}")
    print(f"   ¿Rentable?: {'✅ Sí' if roi['is_profitable'] else '❌ No'}")
    
    # Competencia
    comp = prediction['competition_analysis']
    print(f"\n🔍 ANÁLISIS DE COMPETENCIA:")
    print(f"   Nivel: {comp['level_label']}")
    print(f"   Keywords competitivas: {comp['competitive_keywords']}/{comp['total_keywords']}")
    print(f"   Ratio: {comp['competition_ratio']:.1f}%")
    print(f"   CPC multiplier: {comp['cpc_multiplier']}x")
    print(f"   Impression Share esperado: {comp['expected_impression_share']}%")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES ESTRATÉGICAS:")
    recs = prediction['recommendations']
    for i, rec in enumerate(recs, 1):
        print(f"\n   {i}. [{rec['priority'].upper()}] {rec['category']}")
        print(f"      Acción: {rec['recommendation']}")
        print(f"      Impacto: {rec['expected_impact']}")
    
    # Comparación con benchmarks
    print(f"\n📊 COMPARACIÓN CON BENCHMARKS:")
    benchmark = prediction['benchmark_comparison']
    
    print(f"\n   CTR:")
    print(f"      Tu predicción: {benchmark['ctr']['predicted']:.2f}%")
    print(f"      Promedio industria: {benchmark['ctr']['benchmark']:.2f}%")
    print(f"      Diferencia: {benchmark['ctr']['vs_benchmark']:+.1f}%")
    print(f"      Rendimiento: {'📈 Superior' if benchmark['ctr']['performance'] == 'above' else '📉 Inferior'}")
    
    print(f"\n   Quality Score:")
    print(f"      Tu predicción: {benchmark['quality_score']['predicted']:.1f}/10")
    print(f"      Promedio industria: {benchmark['quality_score']['benchmark']:.1f}/10")
    print(f"      Diferencia: {benchmark['quality_score']['vs_benchmark']:+.1f}")
    print(f"      Rendimiento: {'📈 Superior' if benchmark['quality_score']['performance'] == 'above' else '📉 Inferior'}")
    
    print(f"\n   CPC:")
    print(f"      Tu predicción: ${benchmark['cpc']['predicted']:.2f}")
    print(f"      Promedio industria: ${benchmark['cpc']['benchmark']:.2f}")
    print(f"      Diferencia: {benchmark['cpc']['vs_benchmark']:+.1f}%")
    print(f"      Rendimiento: {'📈 Mejor (más bajo)' if benchmark['cpc']['performance'] == 'below' else '📉 Peor (más alto)'}")
    
    # Confianza general
    confidence = prediction['confidence_summary']
    print(f"\n🎯 CONFIANZA GENERAL DE LA PREDICCIÓN:")
    print(f"   Score: {confidence['score']:.0%}")
    print(f"   Nivel: {confidence['level']}")
    print(f"   Componentes:")
    print(f"      - CTR: {confidence['components']['ctr']:.0%}")
    print(f"      - Quality Score: {confidence['components']['quality_score']:.0%}")
    print(f"      - CPC: {confidence['components']['cpc']:.0%}")
    
    # Resumen ejecutivo
    print("\n" + "="*60)
    print("📋 RESUMEN EJECUTIVO")
    print("="*60)
    
    print(f"""
🎯 PREDICCIÓN DE RENDIMIENTO - {duration} DÍAS

💰 INVERSIÓN:
   • Presupuesto total: ${metrics['total_budget']:,.2f}
   • Presupuesto diario: ${budget:.2f}

📊 RESULTADOS ESPERADOS:
   • Impresiones: {metrics['estimated_impressions']:,}
   • Clics: {metrics['estimated_clicks']:,}
   • Conversiones: {conv['estimated_conversions']}
   • CTR: {ctr['predicted_ctr']:.2f}%
   • CPC: ${cpc['estimated_cpc']:.2f}

💹 RENTABILIDAD:
   • Revenue: ${roi['total_revenue']:,.2f}
   • Ganancia: ${roi['profit']:,.2f}
   • ROI: {roi['roi_percentage']:,.1f}%
   • ROAS: {roi['roas']:.2f}x
   • Nivel: {roi['profitability_level']}

⭐ CALIDAD:
   • Quality Score: {qs['predicted_score']:.1f}/10 ({qs['grade']})
   • Nivel de competencia: {comp['level_label']}
   • Confianza: {confidence['level']} ({confidence['score']:.0%})

✅ VEREDICTO: {'CAMPAÑA RENTABLE - PROCEDER' if roi['is_profitable'] else 'REVISAR ESTRATEGIA'}
    """)
    
    # Guardar predicción (opcional)
    print("\n💾 Predicción guardada en historial")
    print(f"   ID: {prediction['prediction_id']}")
    print(f"   Timestamp: {prediction['timestamp']}")
    
    # Estadísticas del predictor
    print("\n📈 ESTADÍSTICAS DEL PREDICTOR:")
    stats = predictor.get_statistics()
    print(f"   Total predicciones: {stats['total_predictions']}")
    print(f"   Tipo de negocio: {stats['business_type']}")
    
    print("\n" + "="*60)
    print("✅ Ejemplo completado exitosamente")
    print("="*60)
    