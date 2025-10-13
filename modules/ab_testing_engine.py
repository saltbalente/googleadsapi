"""
🧪 AB TESTING ENGINE - Motor de Pruebas A/B para Anuncios
Sistema avanzado de testing A/B con variaciones automáticas y predicción de rendimiento
Versión: 2.0
Fecha: 2025-01-13
Autor: saltbalente
"""

import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict
import statistics
import json
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABTestingEngine:
    """
    Motor de pruebas A/B para anuncios que proporciona:
    - Creación de variaciones automáticas (A, B, C)
    - Variaciones por tono (emocional, racional, urgente)
    - Análisis comparativo detallado
    - Predicción de CTR basado en benchmarks
    - Recomendaciones de ganador
    - Métricas de confianza estadística
    - Historial de tests
    """
    
    # Benchmarks de industria (CTR promedio por tipo)
    INDUSTRY_BENCHMARKS = {
        'esoteric': {
            'emocional': 4.2,
            'urgente': 5.1,
            'profesional': 3.8,
            'místico': 4.5,
            'esperanzador': 3.9,
            'poderoso': 4.7,
            'tranquilizador': 3.5
        },
        'generic': {
            'emocional': 2.8,
            'urgente': 3.5,
            'profesional': 3.2,
            'informativo': 2.9
        }
    }
    
    # Factores de ajuste por características
    FEATURE_IMPACT = {
        'power_words': 0.3,        # +0.3% CTR
        'action_cta': 0.5,          # +0.5% CTR
        'numbers': 0.2,             # +0.2% CTR
        'benefits': 0.4,            # +0.4% CTR
        'urgency': 0.6,             # +0.6% CTR
        'emotional_words': 0.3,     # +0.3% CTR
        'length_optimal': 0.2       # +0.2% CTR
    }
    
    def __init__(
        self,
        ai_generator=None,
        save_results: bool = True,
        results_dir: Optional[str] = None
    ):
        """
        Inicializa el motor de pruebas A/B.
        
        Args:
            ai_generator: Generador de IA para crear variaciones
            save_results: Guardar resultados de tests
            results_dir: Directorio para guardar resultados
        """
        self.ai_generator = ai_generator
        self.save_results = save_results
        
        # Configurar directorio de resultados
        if results_dir:
            self.results_dir = Path(results_dir)
        else:
            self.results_dir = Path(__file__).parent.parent / "data" / "ab_tests"
        
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Historial de tests
        self.test_history: List[Dict[str, Any]] = []
        
        # Estadísticas
        self.stats = {
            'total_tests': 0,
            'total_variations': 0,
            'avg_improvement': 0.0,
            'best_performing_tone': None
        }
        
        logger.info(f"✅ ABTestingEngine inicializado")
        logger.info(f"   - Resultados dir: {self.results_dir}")
        logger.info(f"   - Guardar resultados: {save_results}")
    
    # =========================================================================
    # CREACIÓN DE VARIACIONES
    # =========================================================================
    
    def create_variations(
        self,
        base_ad: Dict[str, Any],
        variation_types: List[str] = ['emocional', 'racional', 'urgente'],
        num_headlines: int = 15,
        num_descriptions: int = 4,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Crea variaciones A/B/C de un anuncio base.
        
        Args:
            base_ad: Anuncio base (puede contener headlines/descriptions o solo keywords)
            variation_types: Tipos de variaciones a crear
            num_headlines: Número de títulos por variación
            num_descriptions: Número de descripciones por variación
            keywords: Keywords base
        
        Returns:
            Diccionario con test A/B creado
        """
        test_id = f"abtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🧪 Creando test A/B: {test_id}")
        logger.info(f"   - Variaciones: {', '.join(variation_types)}")
        
        # Extraer keywords
        if not keywords:
            keywords = base_ad.get('keywords', [])
        
        if not keywords:
            logger.error("❌ No se proporcionaron keywords para el test")
            return {
                'success': False,
                'error': 'Se requieren keywords para crear variaciones'
            }
        
        # Mapear tipos a tonos del sistema
        tone_mapping = {
            'emocional': 'emocional',
            'racional': 'profesional',
            'urgente': 'urgente'
        }
        
        variations = []
        variation_labels = ['A', 'B', 'C', 'D', 'E']
        
        for i, var_type in enumerate(variation_types):
            label = variation_labels[i] if i < len(variation_labels) else f"V{i+1}"
            tone = tone_mapping.get(var_type, var_type)
            
            logger.info(f"   Generando variación {label} ({var_type})...")
            
            # Si tenemos generador de IA, generar con IA
            if self.ai_generator:
                try:
                    generated = self.ai_generator.generate_ad(
                        keywords=keywords,
                        num_ads=1,
                        num_headlines=num_headlines,
                        num_descriptions=num_descriptions,
                        tone=tone,
                        user='saltbalente',
                        validate=True
                    )
                    
                    if generated and len(generated) > 0:
                        ad_data = generated[0]
                        
                        variation = {
                            'label': label,
                            'type': var_type,
                            'tone': tone,
                            'headlines': ad_data.get('headlines', []),
                            'descriptions': ad_data.get('descriptions', []),
                            'validation': ad_data.get('validation_result', {}),
                            'generated_at': datetime.now().isoformat()
                        }
                        
                        variations.append(variation)
                        logger.info(f"   ✅ Variación {label} generada")
                    else:
                        logger.warning(f"   ⚠️ No se pudo generar variación {label}")
                        
                except Exception as e:
                    logger.error(f"   ❌ Error generando variación {label}: {e}")
            
            else:
                # Sin IA: crear variación placeholder
                variation = {
                    'label': label,
                    'type': var_type,
                    'tone': tone,
                    'headlines': base_ad.get('headlines', [])[:num_headlines],
                    'descriptions': base_ad.get('descriptions', [])[:num_descriptions],
                    'note': 'Variación creada sin IA - usar como template'
                }
                variations.append(variation)
        
        # Crear test
        test = {
            'test_id': test_id,
            'status': 'draft',
            'created_at': datetime.now().isoformat(),
            'created_by': 'saltbalente',
            'base_ad': base_ad,
            'keywords': keywords,
            'variations': variations,
            'variation_count': len(variations),
            'analysis': self._analyze_variations(variations, keywords),
            'predictions': self._predict_performance(variations),
            'recommendations': self._generate_recommendations(variations)
        }
        
        # Guardar en historial
        self.test_history.append(test)
        
        # Guardar en disco
        if self.save_results:
            self._save_test(test)
        
        # Actualizar estadísticas
        self.stats['total_tests'] += 1
        self.stats['total_variations'] += len(variations)
        
        logger.info(f"✅ Test A/B creado: {test_id}")
        logger.info(f"   - Variaciones creadas: {len(variations)}")
        
        return test
    
    def create_tone_based_test(
        self,
        keywords: List[str],
        tones: List[str] = ['emocional', 'urgente', 'profesional'],
        num_headlines: int = 15,
        num_descriptions: int = 4
    ) -> Dict[str, Any]:
        """
        Crea test A/B basado en diferentes tonos.
        
        Args:
            keywords: Keywords base
            tones: Tonos a probar
            num_headlines: Títulos por variación
            num_descriptions: Descripciones por variación
        
        Returns:
            Test A/B creado
        """
        logger.info(f"🎨 Creando test basado en tonos: {', '.join(tones)}")
        
        base_ad = {'keywords': keywords}
        
        return self.create_variations(
            base_ad=base_ad,
            variation_types=tones,
            num_headlines=num_headlines,
            num_descriptions=num_descriptions,
            keywords=keywords
        )
    
    # =========================================================================
    # ANÁLISIS DE VARIACIONES
    # =========================================================================
    
    def _analyze_variations(
        self,
        variations: List[Dict[str, Any]],
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Analiza las diferencias entre variaciones.
        
        Args:
            variations: Lista de variaciones
            keywords: Keywords de referencia
        
        Returns:
            Diccionario con análisis comparativo
        """
        if not variations:
            return {}
        
        analysis = {
            'total_variations': len(variations),
            'by_variation': {},
            'comparison': {
                'headline_lengths': {},
                'description_lengths': {},
                'keyword_usage': {},
                'unique_elements': {}
            }
        }
        
        all_headlines = []
        all_descriptions = []
        
        for variation in variations:
            label = variation['label']
            headlines = variation.get('headlines', [])
            descriptions = variation.get('descriptions', [])
            
            all_headlines.extend(headlines)
            all_descriptions.extend(descriptions)
            
            # Análisis por variación
            analysis['by_variation'][label] = {
                'type': variation.get('type', 'unknown'),
                'tone': variation.get('tone', 'unknown'),
                'num_headlines': len(headlines),
                'num_descriptions': len(descriptions),
                'avg_headline_length': round(
                    statistics.mean([len(h) for h in headlines]) if headlines else 0, 
                    1
                ),
                'avg_description_length': round(
                    statistics.mean([len(d) for d in descriptions]) if descriptions else 0,
                    1
                ),
                'keyword_matches': self._count_keyword_matches(
                    headlines + descriptions, 
                    keywords
                )
            }
        
        # Análisis de unicidad
        unique_headlines = len(set(all_headlines))
        unique_descriptions = len(set(all_descriptions))
        
        analysis['comparison']['unique_elements'] = {
            'total_headlines': len(all_headlines),
            'unique_headlines': unique_headlines,
            'uniqueness_rate_headlines': round(
                unique_headlines / len(all_headlines) * 100 if all_headlines else 0,
                1
            ),
            'total_descriptions': len(all_descriptions),
            'unique_descriptions': unique_descriptions,
            'uniqueness_rate_descriptions': round(
                unique_descriptions / len(all_descriptions) * 100 if all_descriptions else 0,
                1
            )
        }
        
        return analysis
    
    def _count_keyword_matches(
        self,
        texts: List[str],
        keywords: List[str]
    ) -> int:
        """Cuenta cuántas keywords aparecen en los textos."""
        all_text = ' '.join(texts).lower()
        matches = 0
        
        for keyword in keywords:
            if keyword.lower() in all_text:
                matches += 1
        
        return matches
    
    # =========================================================================
    # PREDICCIÓN DE RENDIMIENTO
    # =========================================================================
    
    def _predict_performance(
        self,
        variations: List[Dict[str, Any]],
        business_type: str = 'esoteric'
    ) -> Dict[str, Any]:
        """
        Predice métricas de rendimiento basándose en benchmarks.
        
        Args:
            variations: Lista de variaciones
            business_type: Tipo de negocio ('esoteric' o 'generic')
        
        Returns:
            Diccionario con predicciones
        """
        predictions = {
            'business_type': business_type,
            'by_variation': {},
            'best_predicted': None,
            'confidence_level': 'medium'
        }
        
        best_ctr = 0
        best_variation = None
        
        for variation in variations:
            label = variation['label']
            tone = variation.get('tone', 'profesional')
            headlines = variation.get('headlines', [])
            descriptions = variation.get('descriptions', [])
            
            # CTR base según tono y tipo de negocio
            benchmarks = self.INDUSTRY_BENCHMARKS.get(business_type, {})
            base_ctr = benchmarks.get(tone, 3.0)
            
            # Calcular ajustes por características
            adjustments = 0.0
            features_detected = []
            
            # Analizar características
            all_text = ' '.join(headlines + descriptions).lower()
            
            # Palabras de poder
            power_words = ['garantizado', 'efectivo', 'profesional', 'poderoso']
            if any(word in all_text for word in power_words):
                adjustments += self.FEATURE_IMPACT['power_words']
                features_detected.append('power_words')
            
            # CTAs
            action_words = ['consulta', 'solicita', 'obtén', 'descubre']
            if any(word in all_text for word in action_words):
                adjustments += self.FEATURE_IMPACT['action_cta']
                features_detected.append('action_cta')
            
            # Números
            if any(char.isdigit() for char in all_text):
                adjustments += self.FEATURE_IMPACT['numbers']
                features_detected.append('numbers')
            
            # Beneficios
            benefit_words = ['resultado', 'garantía', 'éxito', 'efectivo']
            if any(word in all_text for word in benefit_words):
                adjustments += self.FEATURE_IMPACT['benefits']
                features_detected.append('benefits')
            
            # Urgencia
            urgency_words = ['ahora', 'ya', 'hoy', 'inmediato', 'rápido']
            if any(word in all_text for word in urgency_words):
                adjustments += self.FEATURE_IMPACT['urgency']
                features_detected.append('urgency')
            
            # Longitud óptima de headlines
            if headlines:
                avg_length = statistics.mean([len(h) for h in headlines])
                if 20 <= avg_length <= 28:
                    adjustments += self.FEATURE_IMPACT['length_optimal']
                    features_detected.append('length_optimal')
            
            # CTR predicho
            predicted_ctr = round(base_ctr + adjustments, 2)
            
            # Quality Score predicho (basado en características)
            quality_score = min(10, 6 + len(features_detected) * 0.5)
            
            # CPC estimado (inversamente proporcional a quality score)
            base_cpc = 1.50  # USD base para esotérico
            estimated_cpc = round(base_cpc * (10 / quality_score), 2)
            
            # Conversiones proyectadas (CTR * conversion_rate)
            conversion_rate = 0.05  # 5% tasa de conversión promedio
            estimated_conversions_per_100_clicks = round(predicted_ctr * conversion_rate, 2)
            
            predictions['by_variation'][label] = {
                'tone': tone,
                'predicted_ctr': predicted_ctr,
                'base_ctr': base_ctr,
                'adjustments': round(adjustments, 2),
                'features_detected': features_detected,
                'quality_score': round(quality_score, 1),
                'estimated_cpc': estimated_cpc,
                'estimated_conversions_per_100_clicks': estimated_conversions_per_100_clicks,
                'confidence': self._calculate_confidence(features_detected)
            }
            
            # Tracking del mejor
            if predicted_ctr > best_ctr:
                best_ctr = predicted_ctr
                best_variation = label
        
        predictions['best_predicted'] = {
            'variation': best_variation,
            'predicted_ctr': best_ctr,
            'reason': f"Mejor CTR predicho basado en {len(predictions['by_variation'][best_variation]['features_detected'])} características detectadas"
        }
        
        # Nivel de confianza general
        avg_confidence = statistics.mean([
            v['confidence'] for v in predictions['by_variation'].values()
        ])
        
        if avg_confidence >= 0.8:
            predictions['confidence_level'] = 'high'
        elif avg_confidence >= 0.6:
            predictions['confidence_level'] = 'medium'
        else:
            predictions['confidence_level'] = 'low'
        
        return predictions
    
    def _calculate_confidence(self, features: List[str]) -> float:
        """
        Calcula nivel de confianza de la predicción.
        
        Args:
            features: Lista de características detectadas
        
        Returns:
            Nivel de confianza (0-1)
        """
        # Más características = mayor confianza
        base_confidence = 0.5
        
        feature_confidence = len(features) * 0.08
        
        total_confidence = min(1.0, base_confidence + feature_confidence)
        
        return round(total_confidence, 2)
    
    # =========================================================================
    # RECOMENDACIONES
    # =========================================================================
    
    def _generate_recommendations(
        self,
        variations: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Genera recomendaciones para el test A/B.
        
        Args:
            variations: Lista de variaciones
        
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        if not variations:
            return ["No hay variaciones para analizar"]
        
        # Recomendación: diversidad
        all_headlines = []
        for v in variations:
            all_headlines.extend(v.get('headlines', []))
        
        unique_rate = len(set(all_headlines)) / len(all_headlines) if all_headlines else 0
        
        if unique_rate < 0.7:
            recommendations.append(
                "Aumenta la diversidad entre variaciones para resultados más concluyentes"
            )
        
        # Recomendación: duración del test
        recommendations.append(
            "Ejecuta el test durante al menos 7 días para obtener datos estadísticamente significativos"
        )
        
        # Recomendación: volumen mínimo
        recommendations.append(
            "Asegúrate de tener al menos 100 clics por variación antes de tomar decisiones"
        )
        
        # Recomendación: distribución de tráfico
        recommendations.append(
            "Distribuye el tráfico equitativamente (33.3% por variación para test A/B/C)"
        )
        
        # Recomendación: métricas a monitorear
        recommendations.append(
            "Monitorea CTR, Quality Score y tasa de conversión, no solo clics"
        )
        
        return recommendations
    
    def recommend_winner(
        self,
        test_results: Dict[str, Any],
        min_clicks: int = 100,
        min_confidence: float = 0.95
    ) -> Dict[str, Any]:
        """
        Recomienda el ganador de un test A/B basado en resultados reales.
        
        Args:
            test_results: Diccionario con métricas reales por variación
            min_clicks: Mínimo de clics requeridos por variación
            min_confidence: Nivel de confianza mínimo requerido
        
        Returns:
            Diccionario con recomendación de ganador
        """
        logger.info("🏆 Analizando test A/B para recomendar ganador...")
        
        variations = test_results.get('variations', {})
        
        if not variations:
            return {
                'success': False,
                'error': 'No hay datos de variaciones'
            }
        
        # Validar que todas tengan suficientes datos
        valid_variations = {}
        insufficient_data = []
        
        for label, metrics in variations.items():
            clicks = metrics.get('clicks', 0)
            
            if clicks >= min_clicks:
                valid_variations[label] = metrics
            else:
                insufficient_data.append({
                    'variation': label,
                    'clicks': clicks,
                    'needed': min_clicks
                })
        
        if not valid_variations:
            return {
                'success': False,
                'error': 'Ninguna variación tiene suficientes datos',
                'insufficient_data': insufficient_data,
                'recommendation': f'Continúa el test hasta alcanzar {min_clicks} clics por variación'
            }
        
        # Calcular métricas por variación
        variation_scores = {}
        
        for label, metrics in valid_variations.items():
            impressions = metrics.get('impressions', 0)
            clicks = metrics.get('clicks', 0)
            conversions = metrics.get('conversions', 0)
            cost = metrics.get('cost', 0)
            
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
            cpc = cost / clicks if clicks > 0 else 0
            cost_per_conversion = cost / conversions if conversions > 0 else float('inf')
            
            # Score compuesto (ponderado)
            # CTR: 30%, Conversion Rate: 40%, Cost Efficiency: 30%
            ctr_score = min(ctr / 10, 1.0)  # Normalizado a 0-1
            conv_score = min(conversion_rate / 10, 1.0)  # Normalizado a 0-1
            cost_score = max(0, 1 - (cost_per_conversion / 100))  # Menor costo = mejor
            
            composite_score = (
                ctr_score * 0.3 +
                conv_score * 0.4 +
                cost_score * 0.3
            ) * 100
            
            variation_scores[label] = {
                'ctr': round(ctr, 2),
                'conversion_rate': round(conversion_rate, 2),
                'cpc': round(cpc, 2),
                'cost_per_conversion': round(cost_per_conversion, 2) if cost_per_conversion != float('inf') else None,
                'composite_score': round(composite_score, 2),
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'cost': round(cost, 2)
            }
        
        # Determinar ganador
        winner = max(variation_scores.items(), key=lambda x: x[1]['composite_score'])
        winner_label = winner[0]
        winner_data = winner[1]
        
        # Calcular significancia estadística (simplificado)
        # En producción, usar test chi-cuadrado o test z
        statistical_confidence = self._calculate_statistical_confidence(
            variation_scores,
            winner_label
        )
        
        # Resultado
        result = {
            'success': True,
            'winner': {
                'variation': winner_label,
                'metrics': winner_data,
                'statistical_confidence': statistical_confidence,
                'is_significant': statistical_confidence >= min_confidence
            },
            'all_variations': variation_scores,
            'analysis': {
                'total_variations_tested': len(variation_scores),
                'test_duration_recommendation': 'Continúa monitoreando' if statistical_confidence < min_confidence else 'Test completo',
                'next_steps': self._generate_next_steps(winner_label, winner_data, statistical_confidence, min_confidence)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Ganador recomendado: Variación {winner_label}")
        logger.info(f"   - Score: {winner_data['composite_score']:.2f}")
        logger.info(f"   - Confianza: {statistical_confidence:.1%}")
        
        return result
    
    def _calculate_statistical_confidence(
        self,
        variation_scores: Dict[str, Dict],
        winner_label: str
    ) -> float:
        """
        Calcula confianza estadística del ganador (simplificado).
        
        En producción real, usar pruebas estadísticas apropiadas.
        
        Args:
            variation_scores: Scores de todas las variaciones
            winner_label: Label del ganador
        
        Returns:
            Nivel de confianza (0-1)
        """
        if len(variation_scores) < 2:
            return 0.5
        
        winner_score = variation_scores[winner_label]['composite_score']
        
        other_scores = [
            data['composite_score'] 
            for label, data in variation_scores.items() 
            if label != winner_label
        ]
        
        if not other_scores:
            return 0.5
        
        avg_other_score = statistics.mean(other_scores)
        
        # Diferencia relativa
        if avg_other_score == 0:
            return 0.9
        
        difference = (winner_score - avg_other_score) / avg_other_score
        
        # Convertir diferencia a confianza
        # 10% diferencia = 0.75 confianza
        # 20% diferencia = 0.90 confianza
        # 30%+ diferencia = 0.95+ confianza
        
        if difference >= 0.30:
            confidence = 0.95
        elif difference >= 0.20:
            confidence = 0.90
        elif difference >= 0.10:
            confidence = 0.75
        elif difference >= 0.05:
            confidence = 0.60
        else:
            confidence = 0.50
        
        return round(confidence, 2)
    
    def _generate_next_steps(
        self,
        winner_label: str,
        winner_data: Dict,
        confidence: float,
        min_confidence: float
    ) -> List[str]:
        """Genera recomendaciones de próximos pasos."""
        steps = []
        
        if confidence >= min_confidence:
            steps.append(f"✅ Implementa la variación {winner_label} como anuncio principal")
            steps.append("🔄 Considera crear nuevas variaciones basadas en el ganador")
            steps.append("📊 Monitorea el rendimiento durante 30 días")
        else:
            steps.append(f"⏳ Continúa el test - confianza actual: {confidence:.1%}")
            steps.append(f"🎯 Objetivo: alcanzar {min_confidence:.1%} de confianza")
            steps.append("📈 Aumenta el presupuesto para obtener más datos rápidamente")
        
        # Recomendaciones basadas en métricas
        if winner_data['ctr'] < 3.0:
            steps.append("💡 CTR bajo - considera mejorar los titulares")
        
        if winner_data['conversion_rate'] < 3.0:
            steps.append("💡 Tasa de conversión baja - revisa landing page")
        
        return steps
    
    # =========================================================================
    # GESTIÓN DE TESTS
    # =========================================================================
    
    def get_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un test específico del historial.
        
        Args:
            test_id: ID del test
        
        Returns:
            Diccionario con datos del test o None
        """
        for test in self.test_history:
            if test['test_id'] == test_id:
                return test
        
        # Buscar en disco
        test_file = self.results_dir / f"{test_id}.json"
        if test_file.exists():
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ Error cargando test {test_id}: {e}")
        
        return None
    
    def list_tests(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista tests del historial.
        
        Args:
            status: Filtrar por estado ('draft', 'running', 'completed')
            limit: Número máximo de tests a retornar
        
        Returns:
            Lista de tests
        """
        tests = self.test_history.copy()
        
        # Filtrar por estado
        if status:
            tests = [t for t in tests if t.get('status') == status]
        
        # Ordenar por fecha (más recientes primero)
        tests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Limitar cantidad
        if limit:
            tests = tests[:limit]
        
        return tests
    
    def update_test_status(
        self,
        test_id: str,
        status: str,
        results: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Actualiza el estado de un test.
        
        Args:
            test_id: ID del test
            status: Nuevo estado
            results: Resultados opcionales
        
        Returns:
            True si se actualizó exitosamente
        """
        test = self.get_test(test_id)
        
        if not test:
            logger.error(f"❌ Test {test_id} no encontrado")
            return False
        
        test['status'] = status
        test['updated_at'] = datetime.now().isoformat()
        
        if results:
            test['results'] = results
        
        # Guardar cambios
        if self.save_results:
            self._save_test(test)
        
        logger.info(f"✅ Test {test_id} actualizado a estado: {status}")
        
        return True
    
    def _save_test(self, test: Dict[str, Any]) -> None:
        """Guarda test en disco."""
        test_id = test['test_id']
        test_file = self.results_dir / f"{test_id}.json"
        
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Test guardado: {test_file}")
        except Exception as e:
            logger.error(f"❌ Error guardando test: {e}")
    
    def delete_test(self, test_id: str) -> bool:
        """
        Elimina un test del historial y disco.
        
        Args:
            test_id: ID del test
        
        Returns:
            True si se eliminó exitosamente
        """
        # Eliminar de historial
        self.test_history = [t for t in self.test_history if t['test_id'] != test_id]
        
        # Eliminar de disco
        test_file = self.results_dir / f"{test_id}.json"
        
        if test_file.exists():
            try:
                test_file.unlink()
                logger.info(f"✅ Test {test_id} eliminado")
                return True
            except Exception as e:
                logger.error(f"❌ Error eliminando test: {e}")
                return False
        
        return True
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del motor A/B."""
        # Analizar historial para encontrar mejor tono
        tone_performance = defaultdict(list)
        
        for test in self.test_history:
            predictions = test.get('predictions', {})
            
            for var_label, var_pred in predictions.get('by_variation', {}).items():
                tone = var_pred.get('tone')
                ctr = var_pred.get('predicted_ctr', 0)
                
                if tone:
                    tone_performance[tone].append(ctr)
        
        # Calcular promedio por tono
        best_tone = None
        best_avg_ctr = 0
        
        for tone, ctrs in tone_performance.items():
            avg_ctr = statistics.mean(ctrs)
            if avg_ctr > best_avg_ctr:
                best_avg_ctr = avg_ctr
                best_tone = tone
        
        self.stats['best_performing_tone'] = best_tone
        
        return {
            **self.stats,
            'history_size': len(self.test_history),
            'tone_performance': {
                tone: round(statistics.mean(ctrs), 2)
                for tone, ctrs in tone_performance.items()
            }
        }
    
    def export_test_results(
        self,
        test_id: str,
        format: str = 'json'
    ) -> Optional[str]:
        """
        Exporta resultados de un test.
        
        Args:
            test_id: ID del test
            format: Formato ('json' o 'csv')
        
        Returns:
            Path del archivo exportado o None
        """
        test = self.get_test(test_id)
        
        if not test:
            logger.error(f"❌ Test {test_id} no encontrado")
            return None
        
        export_dir = self.results_dir / "exports"
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            export_file = export_dir / f"{test_id}_export_{timestamp}.json"
            
            try:
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(test, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ Test exportado: {export_file}")
                return str(export_file)
            except Exception as e:
                logger.error(f"❌ Error exportando test: {e}")
                return None
        
        elif format == 'csv':
            import csv
            
            export_file = export_dir / f"{test_id}_export_{timestamp}.csv"
            
            try:
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Header
                    writer.writerow([
                        'Variation', 'Type', 'Tone', 'Predicted CTR',
                        'Quality Score', 'Estimated CPC'
                    ])
                    
                    # Rows
                    predictions = test.get('predictions', {})
                    for var_label, var_pred in predictions.get('by_variation', {}).items():
                        writer.writerow([
                            var_label,
                            var_pred.get('tone', ''),
                            var_pred.get('tone', ''),
                            var_pred.get('predicted_ctr', ''),
                            var_pred.get('quality_score', ''),
                            var_pred.get('estimated_cpc', '')
                        ])
                
                logger.info(f"✅ Test exportado: {export_file}")
                return str(export_file)
            except Exception as e:
                logger.error(f"❌ Error exportando test: {e}")
                return None
        
        return None


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_ab_testing_engine(
    ai_generator=None,
    save_results: bool = True
) -> ABTestingEngine:
    """
    Factory function para crear una instancia de ABTestingEngine.
    
    Args:
        ai_generator: Generador de IA
        save_results: Guardar resultados
    
    Returns:
        Instancia de ABTestingEngine
    """
    return ABTestingEngine(
        ai_generator=ai_generator,
        save_results=save_results
    )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🧪 AB TESTING ENGINE - Ejemplo de Uso")
    print("="*60)
    
    # Crear motor A/B
    ab_engine = ABTestingEngine(save_results=False)
    
    # Crear test con keywords
    keywords = ["amarres de amor", "hechizos efectivos", "brujería profesional"]
    
    print("\n📋 Creando test A/B/C con 3 variaciones de tono...")
    
    test = ab_engine.create_tone_based_test(
        keywords=keywords,
        tones=['emocional', 'urgente', 'profesional'],
        num_headlines=10,
        num_descriptions=3
    )
    
    print(f"\n✅ Test creado: {test['test_id']}")
    print(f"   - Variaciones: {test['variation_count']}")
    print(f"   - Estado: {test['status']}")
    
    # Mostrar predicciones
    print("\n📊 PREDICCIONES DE RENDIMIENTO:")
    print("-"*60)
    
    predictions = test['predictions']
    
    for var_label, var_pred in predictions['by_variation'].items():
        print(f"\n🔹 Variación {var_label} ({var_pred['tone']}):")
        print(f"   CTR Predicho: {var_pred['predicted_ctr']}%")
        print(f"   Quality Score: {var_pred['quality_score']}/10")
        print(f"   CPC Estimado: ${var_pred['estimated_cpc']}")
        print(f"   Características: {', '.join(var_pred['features_detected'])}")
        print(f"   Confianza: {var_pred['confidence']:.0%}")
    
    best = predictions['best_predicted']
    print(f"\n🏆 GANADOR PREDICHO: Variación {best['variation']}")
    print(f"   CTR: {best['predicted_ctr']}%")
    print(f"   Razón: {best['reason']}")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    print("-"*60)
    for i, rec in enumerate(test['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # Estadísticas
    print("\n📈 ESTADÍSTICAS DEL MOTOR:")
    print("-"*60)
    stats = ab_engine.get_statistics()
    print(f"Total tests: {stats['total_tests']}")
    print(f"Total variaciones: {stats['total_variations']}")