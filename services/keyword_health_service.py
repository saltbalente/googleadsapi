"""
KeywordHealthService para el cálculo de health scores
Implementa el algoritmo de 5 componentes con pesos específicos
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from services.database_service import DatabaseService, KeywordMetric, KeywordBenchmark, KeywordHealthScore
from utils.logger import get_logger
from modules.google_ads_client import GoogleAdsClientWrapper
from services.report_service import ReportService

logger = get_logger(__name__)

@dataclass
class HealthScoreComponents:
    """Componentes del health score con sus pesos"""
    conv_rate_weight: float = 0.30  # 30%
    cpa_weight: float = 0.30        # 30%
    ctr_weight: float = 0.20        # 20%
    volume_weight: float = 0.10     # 10%
    quality_score_weight: float = 0.10  # 10%

@dataclass
class KeywordAnalytics:
    """Analytics agregados de una keyword"""
    keyword_text: str
    campaign_id: str
    ad_group_id: str
    total_impressions: int
    total_clicks: int
    total_cost: float
    total_conversions: float
    total_conv_value: float
    avg_ctr: float
    avg_cpc: float
    conv_rate: float
    cpa: float
    avg_quality_score: Optional[float]
    data_confidence: float
    days_active: int

class KeywordHealthService:
    """Servicio para calcular health scores de keywords usando algoritmo de 5 componentes"""
    
    def __init__(self, db_service: DatabaseService = None, ads_client: GoogleAdsClientWrapper = None, report_service: ReportService = None):
        self.db_service = db_service or DatabaseService()
        self.ads_client = ads_client
        self.report_service = report_service
        self.components = HealthScoreComponents()  # Inicializar componentes de health score
        logger.info("KeywordHealthService inicializado")

    def calculate_health_scores_for_account(self, customer_id: str, days_back: int = 30) -> List[KeywordHealthScore]:
        """Calcular health scores para todas las keywords de una cuenta"""
        try:
            # Obtener métricas y benchmarks
            metrics = self.db_service.get_keyword_metrics(customer_id, days_back)
            benchmarks = self.db_service.get_account_benchmarks(customer_id)
            
            if not metrics:
                logger.warning(f"No se encontraron métricas para la cuenta {customer_id}")
                return []
            
            # Fallback: usar benchmarks por defecto si no hay específicos de la cuenta
            if benchmarks is None:
                logger.warning(f"No hay benchmarks configurados para {customer_id}, usando valores por defecto")
                benchmarks = self.db_service.get_default_benchmarks()
                if benchmarks:
                    benchmarks.customer_id = customer_id
            
            # Agregar métricas por keyword
            keyword_analytics = self._aggregate_keyword_metrics(metrics)
            
            # Calcular health scores
            health_scores = []
            for analytics in keyword_analytics:
                score = self._calculate_keyword_health_score(analytics, benchmarks, days_back)
                if score:
                    health_scores.append(score)
            
            logger.info(f"Calculados {len(health_scores)} health scores para {customer_id}")
            return health_scores
            
        except Exception as e:
            logger.error(f"Error calculando health scores para {customer_id}: {e}")
            return []

    def _aggregate_keyword_metrics(self, metrics: List[KeywordMetric]) -> List[KeywordAnalytics]:
        """Agregar métricas por keyword para el período especificado"""
        try:
            # Convertir a DataFrame para facilitar agregaciones
            df = pd.DataFrame([{
                'keyword_text': m.keyword_text,
                'campaign_id': m.campaign_id,
                'ad_group_id': m.ad_group_id,
                'impressions': m.impressions,
                'clicks': m.clicks,
                'cost': m.cost_micros / 1_000_000,  # Convertir de micros
                'conversions': m.conversions,
                'conversions_value': m.conversions_value,
                'ctr': m.ctr or 0,
                'average_cpc': (m.average_cpc / 1_000_000) if m.average_cpc else 0,
                'quality_score': m.quality_score,
                'date': m.date
            } for m in metrics])
            
            if df.empty:
                return []
            
            # Agregar por keyword
            aggregated = df.groupby(['keyword_text', 'campaign_id', 'ad_group_id']).agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'cost': 'sum',
                'conversions': 'sum',
                'conversions_value': 'sum',
                'ctr': 'mean',
                'average_cpc': 'mean',
                'quality_score': 'mean',
                'date': ['count', 'nunique']
            }).reset_index()
            
            # Aplanar columnas multi-nivel
            aggregated.columns = [
                'keyword_text', 'campaign_id', 'ad_group_id',
                'total_impressions', 'total_clicks', 'total_cost', 
                'total_conversions', 'total_conv_value',
                'avg_ctr', 'avg_cpc', 'avg_quality_score',
                'total_records', 'days_active'
            ]
            
            # Calcular métricas derivadas
            analytics = []
            for _, row in aggregated.iterrows():
                # Calcular conversion rate y CPA
                conv_rate = row['total_conversions'] / row['total_clicks'] if row['total_clicks'] > 0 else 0
                cpa = row['total_cost'] / row['total_conversions'] if row['total_conversions'] > 0 else float('inf')
                
                # Calcular confianza de datos basada en volumen y días
                data_confidence = self._calculate_data_confidence(
                    row['total_clicks'], 
                    row['days_active'], 
                    row['total_impressions']
                )
                
                analytics.append(KeywordAnalytics(
                    keyword_text=row['keyword_text'],
                    campaign_id=row['campaign_id'],
                    ad_group_id=row['ad_group_id'],
                    total_impressions=int(row['total_impressions']),
                    total_clicks=int(row['total_clicks']),
                    total_cost=float(row['total_cost']),
                    total_conversions=float(row['total_conversions']),
                    total_conv_value=float(row['total_conv_value']),
                    avg_ctr=float(row['avg_ctr']),
                    avg_cpc=float(row['avg_cpc']),
                    conv_rate=conv_rate,
                    cpa=cpa,
                    avg_quality_score=float(row['avg_quality_score']) if pd.notna(row['avg_quality_score']) else None,
                    data_confidence=data_confidence,
                    days_active=int(row['days_active'])
                ))
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error agregando métricas de keywords: {e}")
            return []

    def _calculate_data_confidence(self, clicks: int, days_active: int, impressions: int) -> float:
        """Calcular confianza estadística de los datos"""
        try:
            # Factores de confianza
            click_confidence = min(clicks / 50, 1.0)  # Máxima confianza con 50+ clicks
            time_confidence = min(days_active / 14, 1.0)  # Máxima confianza con 14+ días
            volume_confidence = min(impressions / 1000, 1.0)  # Máxima confianza con 1000+ impresiones
            
            # Promedio ponderado
            confidence = (click_confidence * 0.5 + time_confidence * 0.3 + volume_confidence * 0.2)
            return round(confidence, 3)
            
        except Exception as e:
            logger.error(f"Error calculando confianza de datos: {e}")
            return 0.0

    def _calculate_keyword_health_score(self, analytics: KeywordAnalytics, 
                                      benchmarks: KeywordBenchmark, 
                                      days_back: int) -> Optional[KeywordHealthScore]:
        """Calcular health score para una keyword específica"""
        try:
            # Calcular cada componente del score
            conv_rate_score = self._calculate_conversion_rate_score(analytics.conv_rate, benchmarks.target_conv_rate)
            cpa_score = self._calculate_cpa_score(analytics.cpa, benchmarks.target_cpa)
            ctr_score = self._calculate_ctr_score(analytics.avg_ctr, benchmarks.benchmark_ctr)
            volume_score = self._calculate_volume_score(analytics.total_clicks, analytics.total_impressions)
            quality_score_points = self._calculate_quality_score_points(analytics.avg_quality_score, benchmarks.min_quality_score)
            
            # Calcular health score final ponderado
            health_score = (
                conv_rate_score * self.components.conv_rate_weight +
                cpa_score * self.components.cpa_weight +
                ctr_score * self.components.ctr_weight +
                volume_score * self.components.volume_weight +
                quality_score_points * self.components.quality_score_weight
            )
            
            # Ajustar por confianza de datos
            adjusted_health_score = health_score * analytics.data_confidence
            
            # Determinar categoría y acción recomendada
            health_category, recommended_action, action_priority = self._determine_health_category(
                adjusted_health_score, analytics, benchmarks
            )
            
            # Calcular período de datos
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            return KeywordHealthScore(
                customer_id=benchmarks.customer_id,
                campaign_id=analytics.campaign_id,
                ad_group_id=analytics.ad_group_id,
                keyword_text=analytics.keyword_text,
                health_score=round(adjusted_health_score, 3),
                conv_rate_score=round(conv_rate_score, 3),
                cpa_score=round(cpa_score, 3),
                ctr_score=round(ctr_score, 3),
                confidence_score=round(analytics.data_confidence, 3),
                quality_score_points=round(quality_score_points, 3),
                health_category=health_category,
                recommended_action=recommended_action,
                action_priority=action_priority,
                data_period_start=start_date,
                data_period_end=end_date,
                total_spend=analytics.total_cost,
                total_conversions=analytics.total_conversions,
                total_clicks=analytics.total_clicks,
                calculated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculando health score para {analytics.keyword_text}: {e}")
            return None

    def _calculate_conversion_rate_score(self, actual_conv_rate: float, target_conv_rate: float) -> float:
        """Calcular score de conversion rate (0-100)"""
        if target_conv_rate <= 0:
            return 50.0  # Score neutro si no hay target
        
        # Score basado en ratio vs target
        ratio = actual_conv_rate / target_conv_rate
        
        if ratio >= 1.5:  # 150% o más del target
            return 100.0
        elif ratio >= 1.0:  # Entre 100% y 150%
            return 70 + (ratio - 1.0) * 60  # 70-100
        elif ratio >= 0.5:  # Entre 50% y 100%
            return 30 + (ratio - 0.5) * 80  # 30-70
        else:  # Menos del 50%
            return ratio * 60  # 0-30

    def _calculate_cpa_score(self, actual_cpa: float, target_cpa: float) -> float:
        """Calcular score de CPA (0-100) - menor CPA es mejor"""
        if target_cpa <= 0 or actual_cpa == float('inf'):
            return 0.0  # Sin conversiones
        
        # Score basado en ratio vs target (invertido porque menor es mejor)
        ratio = actual_cpa / target_cpa
        
        if ratio <= 0.5:  # 50% o menos del target (muy bueno)
            return 100.0
        elif ratio <= 1.0:  # Entre 50% y 100% del target
            return 70 + (1.0 - ratio) * 60  # 70-100
        elif ratio <= 2.0:  # Entre 100% y 200% del target
            return 30 + (2.0 - ratio) * 40  # 30-70
        else:  # Más del 200% del target
            return max(0, 30 - (ratio - 2.0) * 15)  # 0-30

    def _calculate_ctr_score(self, actual_ctr: float, benchmark_ctr: float) -> float:
        """Calcular score de CTR (0-100)"""
        if benchmark_ctr <= 0:
            return 50.0  # Score neutro
        
        # Score basado en ratio vs benchmark
        ratio = actual_ctr / benchmark_ctr
        
        if ratio >= 2.0:  # 200% o más del benchmark
            return 100.0
        elif ratio >= 1.0:  # Entre 100% y 200%
            return 60 + (ratio - 1.0) * 40  # 60-100
        elif ratio >= 0.5:  # Entre 50% y 100%
            return 20 + (ratio - 0.5) * 80  # 20-60
        else:  # Menos del 50%
            return ratio * 40  # 0-20

    def _calculate_volume_score(self, clicks: int, impressions: int) -> float:
        """Calcular score de volumen basado en clicks e impressions"""
        # Score basado en clicks (actividad)
        click_score = min(clicks / 100, 1.0) * 50  # Máximo 50 puntos por clicks
        
        # Score basado en impressions (visibilidad)
        impression_score = min(impressions / 5000, 1.0) * 50  # Máximo 50 puntos por impressions
        
        return click_score + impression_score

    def _calculate_quality_score_points(self, quality_score: Optional[float], min_quality_score: int) -> float:
        """Calcular puntos de Quality Score (0-100)"""
        if quality_score is None or quality_score <= 0:
            return 0.0
        
        # Score basado en Quality Score de Google (1-10)
        if quality_score >= 8:
            return 100.0
        elif quality_score >= 6:
            return 60 + (quality_score - 6) * 20  # 60-100
        elif quality_score >= 4:
            return 20 + (quality_score - 4) * 20  # 20-60
        else:
            return quality_score * 5  # 0-20

    def _determine_health_category(self, health_score: float, analytics: KeywordAnalytics, 
                                 benchmarks: KeywordBenchmark) -> Tuple[str, str, int]:
        """Determinar categoría de salud y acción recomendada"""
        try:
            # Categorías basadas en health score
            if health_score >= 80:
                category = 'excellent'
                action = 'increase_bid'
                priority = 1
            elif health_score >= 60:
                category = 'good'
                action = 'monitor'
                priority = 3
            elif health_score >= 40:
                category = 'warning'
                action = 'optimize'
                priority = 2
            else:
                category = 'critical'
                action = 'decrease_bid'
                priority = 1
            
            # Ajustes específicos basados en métricas
            if analytics.total_conversions == 0 and analytics.total_cost > benchmarks.target_cpa:
                category = 'critical'
                action = 'pause_keyword'
                priority = 1
            elif analytics.conv_rate > benchmarks.target_conv_rate * 1.5 and analytics.cpa < benchmarks.target_cpa * 0.7:
                category = 'excellent'
                action = 'increase_bid'
                priority = 1
            elif analytics.avg_quality_score and analytics.avg_quality_score < benchmarks.min_quality_score:
                if category in ['excellent', 'good']:
                    category = 'warning'
                action = 'improve_quality'
                priority = 2
            
            return category, action, priority
            
        except Exception as e:
            logger.error(f"Error determinando categoría de salud: {e}")
            return 'warning', 'monitor', 5

    def get_quick_wins(self, customer_id: str, limit: int = 20) -> List[KeywordHealthScore]:
        """Obtener keywords con mayor potencial de mejora rápida"""
        try:
            # Obtener health scores más recientes
            all_scores = self.db_service.get_latest_health_scores(customer_id, limit=1000)
            
            if not all_scores:
                return []
            
            # Filtrar quick wins: health score medio-alto pero con acciones de alta prioridad
            quick_wins = [
                score for score in all_scores
                if (score.health_score >= 40 and score.health_score < 80 and 
                    score.action_priority <= 2 and
                    score.recommended_action in ['increase_bid', 'optimize', 'improve_quality'])
            ]
            
            # Ordenar por potencial de impacto (health score * spend)
            quick_wins.sort(
                key=lambda x: (x.health_score * (x.total_spend or 0)), 
                reverse=True
            )
            
            return quick_wins[:limit]
            
        except Exception as e:
            logger.error(f"Error obteniendo quick wins para {customer_id}: {e}")
            return []

    def get_vampire_keywords(self, customer_id: str, min_spend: float = 200.0, 
                           min_clicks: int = 20) -> List[KeywordHealthScore]:
        """Obtener keywords vampiro (alto gasto, cero conversiones)"""
        try:
            # Obtener health scores más recientes
            all_scores = self.db_service.get_latest_health_scores(customer_id, limit=1000)
            
            # Filtrar vampiros
            vampires = [
                score for score in all_scores
                if (score.total_conversions == 0 and 
                    (score.total_spend or 0) >= min_spend and
                    (score.total_clicks or 0) >= min_clicks)
            ]
            
            # Ordenar por gasto descendente
            vampires.sort(key=lambda x: x.total_spend or 0, reverse=True)
            
            return vampires
            
        except Exception as e:
            logger.error(f"Error obteniendo keywords vampiro para {customer_id}: {e}")
            return []

    def get_saturation_alerts(self, customer_id: str, percentile: float = 90) -> List[KeywordHealthScore]:
        """Obtener keywords con alertas de saturación (alto volumen, bajo CTR)"""
        try:
            # Obtener health scores más recientes
            all_scores = self.db_service.get_latest_health_scores(customer_id, limit=1000)
            
            if not all_scores:
                return []
            
            # Calcular percentil de clicks para determinar alto volumen
            clicks_values = [score.total_clicks or 0 for score in all_scores]
            high_volume_threshold = np.percentile(clicks_values, percentile)
            
            # Filtrar keywords con alto volumen pero CTR bajo
            saturation_alerts = [
                score for score in all_scores
                if ((score.total_clicks or 0) >= high_volume_threshold and
                    score.ctr_score < 40 and  # CTR score bajo
                    score.health_category in ['warning', 'critical'])
            ]
            
            # Ordenar por volumen de clicks descendente
            saturation_alerts.sort(key=lambda x: x.total_clicks or 0, reverse=True)
            
            return saturation_alerts
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas de saturación para {customer_id}: {e}")
            return []

    def get_bid_recommendations(self, customer_id: str, days_back: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener recomendaciones de cambio de puja listas para el UI.
        
        - Carga los últimos health scores de la cuenta
        - Obtiene pujas actuales (preferencia: cpc_bid cuando esté disponible, si no average_cpc)
        - Calcula recomendaciones y las enriquece con metadatos necesarios para ejecutar acciones
        """
        try:
            # 1) Obtener health scores más recientes
            health_scores = self.db_service.get_latest_health_scores(customer_id) or []
            if not health_scores:
                logger.info(f"No hay health scores recientes para {customer_id}")
                return []
            
            # 2) Obtener datos recientes de keywords para estimar pujas actuales
            keyword_rows = self.fetch_real_keyword_data(customer_id, days_back)
            current_bids: Dict[str, float] = {}
            info_by_key: Dict[str, Dict[str, Any]] = {}
            
            for row in keyword_rows:
                campaign_id = str(row.get('campaign_id', '') or '')
                ad_group_id = str(row.get('ad_group_id', '') or '')
                keyword_text = str(row.get('keyword_text', '') or '')
                if not campaign_id or not ad_group_id or not keyword_text:
                    continue
                
                keyword_key = f"{campaign_id}_{ad_group_id}_{keyword_text}"
                
                # Preferir cpc_bid si está disponible, si no average_cpc
                bid_val = 0.0
                if row.get('cpc_bid'):
                    try:
                        bid_val = float(row.get('cpc_bid', 0) or 0)
                    except Exception:
                        bid_val = 0.0
                elif row.get('cpc_bid_micros'):
                    try:
                        bid_val = float(row.get('cpc_bid_micros', 0) or 0) / 1_000_000.0
                    except Exception:
                        bid_val = 0.0
                elif row.get('average_cpc'):
                    try:
                        bid_val = float(row.get('average_cpc', 0) or 0)
                    except Exception:
                        bid_val = 0.0
                
                if bid_val and bid_val > 0:
                    current_bids[keyword_key] = bid_val
                    info_by_key[keyword_key] = {
                        'customer_id': customer_id,
                        'campaign_id': campaign_id,
                        'ad_group_id': ad_group_id,
                        'keyword_text': keyword_text
                    }
            
            if not current_bids:
                logger.info(f"No se encontraron pujas actuales para {customer_id}")
                return []
            
            # 3) Calcular recomendaciones crudas
            raw_recs = self.calculate_bid_recommendations(health_scores, current_bids)
            if not raw_recs:
                return []
            
            # 4) Convertir a lista enriquecida para UI/ejecución
            enriched: List[Dict[str, Any]] = []
            for k, rec in raw_recs.items():
                info = info_by_key.get(k)
                if not info:
                    # Evitar mapeos incorrectos cuando la clave no coincide
                    continue
                enriched.append({
                    'customer_id': info['customer_id'],
                    'campaign_id': info['campaign_id'],
                    'ad_group_id': info['ad_group_id'],
                    'keyword_text': info['keyword_text'],
                    'current_bid': rec.get('current_bid', 0),
                    'recommended_bid': rec.get('recommended_bid', None),
                    # UI espera 'bid_change_percent'
                    'bid_change_percent': rec.get('change_percent', 0),
                    'justification': rec.get('justification', ''),
                    'risk_level': rec.get('risk_level', 'medium'),
                    'health_score': rec.get('health_score', 0)
                })
            
            # 5) Ordenar por mayor impacto de cambio y limitar
            enriched.sort(key=lambda r: abs(r.get('bid_change_percent', 0)), reverse=True)
            if limit and len(enriched) > limit:
                enriched = enriched[:limit]
            
            logger.info(f"Generadas {len(enriched)} recomendaciones de puja para {customer_id}")
            return enriched
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones de puja: {e}")
            return []

    def calculate_bid_recommendations(self, health_scores: List[KeywordHealthScore], 
                                    current_bids: Dict[str, float]) -> Dict[str, Dict]:
        """Calcular recomendaciones de puja basadas en health scores"""
        try:
            recommendations = {}
            
            for score in health_scores:
                keyword_key = f"{score.campaign_id}_{score.ad_group_id}_{score.keyword_text}"
                current_bid = current_bids.get(keyword_key, 0)
                
                if current_bid <= 0:
                    continue
                
                # Calcular cambio de puja basado en health score y acción recomendada
                if score.recommended_action == 'increase_bid' and score.health_score >= 70:
                    # Aumentar puja para keywords con buen rendimiento
                    multiplier = 1.1 + (score.health_score - 70) * 0.01  # 1.1 a 1.3
                    multiplier = min(multiplier, 1.3)  # Máximo 30% de aumento
                elif score.recommended_action == 'decrease_bid' and score.health_score < 40:
                    # Disminuir puja para keywords con mal rendimiento
                    multiplier = 0.9 - (40 - score.health_score) * 0.01  # 0.9 a 0.7
                    multiplier = max(multiplier, 0.7)  # Máximo 30% de disminución
                else:
                    multiplier = 1.0  # Sin cambio
                
                new_bid = current_bid * multiplier
                change_percent = (multiplier - 1.0) * 100
                
                # Solo recomendar si el cambio es significativo (>5%)
                if abs(change_percent) >= 5:
                    recommendations[keyword_key] = {
                        'current_bid': current_bid,
                        'recommended_bid': round(new_bid, 2),
                        'change_percent': round(change_percent, 1),
                        'health_score': score.health_score,
                        'justification': self._generate_bid_justification(score, change_percent),
                        'risk_level': self._assess_bid_risk(score, change_percent)
                    }
            
            logger.info(f"Generadas {len(recommendations)} recomendaciones de puja")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error calculando recomendaciones de puja: {e}")
            return {}

    def _generate_bid_justification(self, score: KeywordHealthScore, change_percent: float) -> str:
        """Generar justificación para cambio de puja"""
        try:
            if change_percent > 0:
                return f"Aumentar puja {abs(change_percent):.1f}% - Health Score: {score.health_score:.1f}, Conv Rate: {score.conv_rate_score:.1f}, CPA: {score.cpa_score:.1f}"
            else:
                return f"Disminuir puja {abs(change_percent):.1f}% - Health Score: {score.health_score:.1f}, bajo rendimiento detectado"
        except:
            return f"Ajuste de puja recomendado basado en health score {score.health_score:.1f}"

    def _assess_bid_risk(self, score: KeywordHealthScore, change_percent: float) -> str:
        """Evaluar riesgo del cambio de puja"""
        try:
            # Factores de riesgo
            high_spend = (score.total_spend or 0) > 500  # Alto gasto
            low_confidence = score.confidence_score < 0.7  # Baja confianza en datos
            large_change = abs(change_percent) > 20  # Cambio grande
            
            risk_factors = sum([high_spend, low_confidence, large_change])
            
            if risk_factors >= 2:
                return 'high'
            elif risk_factors == 1:
                return 'medium'
            else:
                return 'low'
        except:
            return 'medium'

    def _convert_db_metrics_to_dict(self, customer_id: str, days_back: int) -> List[Dict[str, Any]]:
        """
        Convertir métricas de base de datos al formato de diccionario esperado
        
        Args:
            customer_id: ID del cliente
            days_back: Días hacia atrás
            
        Returns:
            Lista de métricas en formato diccionario
        """
        try:
            # Obtener métricas de base de datos
            db_metrics = self.db_service.get_keyword_metrics(customer_id, days_back)
            
            keyword_data = []
            for metric in db_metrics:
                keyword_data.append({
                    'customer_id': metric.customer_id,
                    'campaign_id': metric.campaign_id,
                    'campaign_name': metric.campaign_name,
                    'ad_group_id': metric.ad_group_id,
                    'ad_group_name': metric.ad_group_name,
                    'keyword_text': metric.keyword_text,
                    'match_type': metric.match_type,
                    'status': metric.status,
                    'date': metric.date.isoformat() if metric.date else '',
                    'impressions': metric.impressions,
                    'clicks': metric.clicks,
                    'cost_micros': metric.cost_micros,
                    'cost': metric.cost_micros / 1_000_000 if metric.cost_micros else 0,
                    'conversions': metric.conversions,
                    'ctr': metric.ctr * 100 if metric.ctr else 0,  # Convertir a porcentaje
                    'average_cpc': metric.average_cpc / 1_000_000 if metric.average_cpc else 0,
                    'quality_score': metric.quality_score
                })
            
            logger.info(f"Convertidas {len(keyword_data)} métricas de base de datos para cuenta {customer_id}")
            return keyword_data
            
        except Exception as e:
            logger.error(f"Error convirtiendo métricas de base de datos: {e}")
            return []

    def fetch_real_keyword_data(self, customer_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Obtener datos reales de keywords desde Google Ads API usando la misma lógica que campaigns
        
        Args:
            customer_id: ID del cliente de Google Ads
            days_back: Días hacia atrás para obtener datos
            
        Returns:
            Lista de métricas de keywords
        """
        try:
            if not self.ads_client:
                logger.warning("GoogleAdsClient no disponible, usando datos de base de datos")
                return self._convert_db_metrics_to_dict(customer_id, days_back)
            
            # Usar ReportService para obtener datos de keywords (misma lógica que campaigns)
            if self.report_service:
                from modules.models import ReportConfig
                from datetime import date, timedelta
                
                # Calcular fechas
                end_date = date.today()
                start_date = end_date - timedelta(days=days_back)
                
                # Configurar reporte de keywords (igual que en campaigns)
                report_config = ReportConfig(
                    report_name='Keyword Health Data',
                    customer_ids=[customer_id],
                    metrics=[
                        'metrics.impressions',
                        'metrics.clicks',
                        'metrics.cost_micros',
                        'metrics.conversions',
                        'metrics.ctr',
                        'metrics.average_cpc'
                    ],
                    dimensions=[
                        'campaign.id',
                        'campaign.name',
                        'ad_group.id',
                        'ad_group.name',
                        'ad_group_criterion.keyword.text',
                        'ad_group_criterion.keyword.match_type',
                        'ad_group_criterion.status',
                        'segments.date'
                    ],
                    date_range=f"{start_date.strftime('%Y-%m-%d')} AND {end_date.strftime('%Y-%m-%d')}",
                    from_resource='keyword_view'
                )
                
                # Generar reporte
                report_result = self.report_service.generate_custom_report(report_config)
                
                if report_result.get('success') and report_result.get('data'):
                    # Convertir datos del reporte al formato esperado
                    keyword_data = []
                    for row in report_result.get('data', []):
                        keyword_data.append({
                            'customer_id': customer_id,
                            'campaign_id': str(row.get('campaign.id', '')),
                            'campaign_name': row.get('campaign.name', ''),
                            'ad_group_id': str(row.get('ad_group.id', '')),
                            'ad_group_name': row.get('ad_group.name', ''),
                            'keyword_text': row.get('ad_group_criterion.keyword.text', ''),
                            'match_type': row.get('ad_group_criterion.keyword.match_type', ''),
                            'status': row.get('ad_group_criterion.status', ''),
                            'date': row.get('segments.date', ''),
                            'impressions': int(row.get('metrics.impressions', 0)),
                            'clicks': int(row.get('metrics.clicks', 0)),
                            'cost_micros': int(row.get('metrics.cost_micros', 0)),
                            'cost': float(row.get('metrics.cost_micros', 0)) / 1_000_000,  # Convertir de micros
                            'conversions': float(row.get('metrics.conversions', 0)),
                            'ctr': float(row.get('metrics.ctr', 0)) * 100,  # Convertir a porcentaje
                            'average_cpc': float(row.get('metrics.average_cpc', 0)) / 1_000_000,
                            'quality_score': row.get('ad_group_criterion.quality_info.quality_score', None)
                        })
                    
                    logger.info(f"Obtenidos {len(keyword_data)} registros de keywords reales desde Google Ads API para cuenta {customer_id}")
                    return keyword_data
                else:
                    logger.warning(f"No se obtuvieron datos de keywords desde API para cuenta {customer_id}: {report_result.get('error', 'Sin datos')}")
            
            # Fallback: usar query directo si ReportService no está disponible
            return self._fetch_keywords_direct_query(customer_id, days_back)
            
        except Exception as e:
            logger.error(f"Error obteniendo datos reales de keywords: {e}")
            # Fallback a datos de base de datos
            return self._convert_db_metrics_to_dict(customer_id, days_back)
    
    def _fetch_keywords_direct_query(self, customer_id: str, days_back: int) -> List[Dict[str, Any]]:
        """
        Obtener datos de keywords usando query directo a Google Ads API
        
        Args:
            customer_id: ID del cliente
            days_back: Días hacia atrás
            
        Returns:
            Lista de métricas de keywords
        """
        try:
            # Query GAQL para obtener datos de keywords (usando la misma lógica que campaigns)
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    ad_group.id,
                    ad_group.name,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status,
                    segments.date,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc
                FROM keyword_view
                WHERE segments.date DURING LAST_{days_back}_DAYS
                    AND ad_group_criterion.status = 'ENABLED'
                    AND ad_group.status = 'ENABLED'
                    AND campaign.status = 'ENABLED'
                ORDER BY metrics.impressions DESC
                LIMIT 1000
            """
            
            # Ejecutar query
            results = self.ads_client.execute_query(customer_id, query)
            
            # Procesar resultados
            keyword_data = []
            for row in results:
                keyword_data.append({
                    'customer_id': customer_id,
                    'campaign_id': str(row.campaign.id),
                    'campaign_name': row.campaign.name,
                    'ad_group_id': str(row.ad_group.id),
                    'ad_group_name': row.ad_group.name,
                    'keyword_text': row.ad_group_criterion.keyword.text,
                    'match_type': row.ad_group_criterion.keyword.match_type.name,
                    'date': str(row.segments.date),
                    'impressions': row.metrics.impressions,
                    'clicks': row.metrics.clicks,
                    'cost': row.metrics.cost_micros / 1_000_000,
                    'conversions': row.metrics.conversions,
                    'conversion_value': row.metrics.conversion_value_micros / 1_000_000,
                    'ctr': row.metrics.ctr * 100,
                    'cpc_bid': row.metrics.average_cpc / 1_000_000,
                    'quality_score': getattr(row.ad_group_criterion.quality_info, 'quality_score', 0)
                })
            
            logger.info(f"Obtenidos {len(keyword_data)} registros usando query directo")
            return keyword_data
            
        except Exception as e:
            logger.error(f"Error en query directo de keywords: {e}")
            return []
    
    def sync_keyword_data_to_database(self, customer_id: str, days_back: int = 30) -> bool:
        """
        Sincronizar datos de keywords reales a la base de datos
        
        Args:
            customer_id: ID del cliente de Google Ads
            days_back: Días hacia atrás para obtener datos
            
        Returns:
            True si la sincronización fue exitosa
        """
        try:
            logger.info(f"Sincronizando datos de keywords para cuenta {customer_id}")
            
            # Obtener datos reales de keywords
            keyword_data = self.fetch_real_keyword_data(customer_id, days_back)
            
            if not keyword_data:
                logger.warning(f"No se obtuvieron datos de keywords para sincronizar en cuenta {customer_id}")
                # Intentar obtener keywords sin métricas (solo estructura)
                return self._sync_keywords_without_metrics(customer_id)
            
            # Convertir a objetos KeywordMetric
            keyword_metrics = []
            for data in keyword_data:
                # Validar campos requeridos
                if not data.get('keyword_text') or not data.get('campaign_id'):
                    continue
                
                # Crear objeto KeywordMetric con valores por defecto
                metric = KeywordMetric(
                    customer_id=customer_id,
                    campaign_id=str(data.get('campaign_id', '')),
                    campaign_name=data.get('campaign_name', ''),
                    ad_group_id=str(data.get('ad_group_id', '')),
                    ad_group_name=data.get('ad_group_name', ''),
                    keyword_text=data.get('keyword_text', ''),
                    match_type=data.get('match_type', 'UNKNOWN'),
                    status=data.get('status', 'UNKNOWN'),
                    quality_score=data.get('quality_score'),
                    impressions=int(data.get('impressions', 0)),
                    clicks=int(data.get('clicks', 0)),
                    cost_micros=int(data.get('cost_micros', 0)),
                    conversions=float(data.get('conversions', 0)),
                    conversions_value=float(data.get('conversion_value', 0)),
                    ctr=float(data.get('ctr', 0)) / 100 if data.get('ctr') else 0,  # Convertir de porcentaje a decimal
                    average_cpc=float(data.get('average_cpc', 0)) * 1_000_000 if data.get('average_cpc') else 0,  # Convertir a micros
                    date=datetime.strptime(data.get('date', date.today().isoformat()), '%Y-%m-%d').date(),
                    extracted_at=datetime.now()
                )
                keyword_metrics.append(metric)
            
            if not keyword_metrics:
                logger.warning(f"No se generaron métricas válidas para cuenta {customer_id}")
                # Intentar obtener keywords sin métricas
                return self._sync_keywords_without_metrics(customer_id)
            
            # Insertar en base de datos
            success = self.db_service.bulk_insert_keyword_metrics(keyword_metrics)
            
            if success:
                logger.info(f"Sincronizados {len(keyword_metrics)} registros de keywords para cuenta {customer_id}")
                return True
            else:
                logger.error(f"Error insertando métricas de keywords en base de datos para cuenta {customer_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error sincronizando datos de keywords: {e}")
            return False
    
    def _sync_keywords_without_metrics(self, customer_id: str) -> bool:
        """
        Sincronizar keywords sin métricas (solo estructura) para cuentas con keywords inactivas
        """
        try:
            logger.info(f"Intentando sincronizar keywords sin métricas para cuenta {customer_id}")
            
            # Query para obtener keywords sin filtro de métricas
            query = """
                SELECT 
                    campaign.id,
                    campaign.name,
                    ad_group.id,
                    ad_group.name,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status
                FROM ad_group_criterion 
                WHERE ad_group_criterion.type = 'KEYWORD'
                    AND ad_group_criterion.status = 'ENABLED'
                    AND ad_group.status = 'ENABLED'
                    AND campaign.status = 'ENABLED'
                LIMIT 100
            """
            
            results = self.ads_client.execute_query(customer_id, query)
            
            if not results:
                logger.warning(f"No se encontraron keywords para cuenta {customer_id}")
                return False
            
            # Crear métricas con valores por defecto para keywords sin actividad
            keyword_metrics = []
            today = date.today()
            
            for row in results:
                metric = KeywordMetric(
                    customer_id=customer_id,
                    campaign_id=str(row.campaign.id),
                    campaign_name=row.campaign.name,
                    ad_group_id=str(row.ad_group.id),
                    ad_group_name=row.ad_group.name,
                    keyword_text=row.ad_group_criterion.keyword.text,
                    match_type=row.ad_group_criterion.keyword.match_type.name,
                    status=row.ad_group_criterion.status.name,
                    quality_score=None,
                    impressions=0,  # Sin actividad reciente
                    clicks=0,
                    cost_micros=0,
                    conversions=0.0,
                    conversions_value=0.0,
                    ctr=0.0,
                    average_cpc=0,
                    date=today,
                    extracted_at=datetime.now()
                )
                keyword_metrics.append(metric)
            
            if keyword_metrics:
                success = self.db_service.bulk_insert_keyword_metrics(keyword_metrics)
                if success:
                    logger.info(f"Sincronizadas {len(keyword_metrics)} keywords sin métricas para cuenta {customer_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sincronizando keywords sin métricas: {e}")
            return False
    
    def get_account_currency(self, customer_id: str) -> str:
        """
        Obtener la moneda de la cuenta usando GoogleAdsClient
        
        Args:
            customer_id: ID del cliente
            
        Returns:
            Código de moneda (ej: 'USD', 'EUR')
        """
        try:
            if self.ads_client:
                account_info = self.ads_client.get_account_info(customer_id)
                return account_info.get('currency_code', 'USD')
            else:
                # Fallback: obtener de base de datos
                account = self.db_service.get_mcc_account(customer_id)
                return account.get('currency', 'USD') if account else 'USD'
                
        except Exception as e:
            logger.error(f"Error obteniendo moneda de cuenta: {e}")
            return 'USD'