#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
ANALYTICS SERVICE PARA GENERADOR IA 2.0
Servicio completo para análisis y métricas avanzadas
Versión: 2.0
Fecha: 2025-01-13
============================================================================
"""

import logging
import json
import yaml
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from collections import defaultdict
import statistics

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Tipos de métricas"""
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    COST = "cost"
    CTR = "ctr"
    CONVERSION_RATE = "conversion_rate"
    CPC = "cpc"
    CPA = "cpa"
    ROAS = "roas"
    QUALITY_SCORE = "quality_score"

class TimeGranularity(Enum):
    """Granularidad temporal"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class AnalysisType(Enum):
    """Tipos de análisis"""
    PERFORMANCE = "performance"
    TREND = "trend"
    COMPARISON = "comparison"
    PREDICTION = "prediction"
    ANOMALY = "anomaly"
    SEGMENTATION = "segmentation"

@dataclass
class MetricData:
    """Datos de una métrica"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    dimensions: Dict[str, Any]
    confidence: Optional[float] = None

@dataclass
class PerformanceInsight:
    """Insight de rendimiento"""
    title: str
    description: str
    impact: str  # high, medium, low
    recommendation: str
    metric_affected: MetricType
    confidence: float
    data_points: List[MetricData]

@dataclass
class TrendAnalysis:
    """Análisis de tendencias"""
    metric: MetricType
    trend_direction: str  # up, down, stable
    trend_strength: float  # 0-1
    period_comparison: Dict[str, float]
    seasonal_patterns: List[Dict[str, Any]]
    forecast: List[Dict[str, Any]]

@dataclass
class CompetitorBenchmark:
    """Benchmark competitivo"""
    metric: MetricType
    our_value: float
    industry_average: float
    top_quartile: float
    percentile_rank: float
    gap_analysis: str

@dataclass
class AnomalyDetection:
    """Detección de anomalías"""
    timestamp: datetime
    metric: MetricType
    expected_value: float
    actual_value: float
    deviation_score: float
    severity: str  # low, medium, high, critical
    possible_causes: List[str]

class EsotericAnalyticsService:
    """
    Servicio completo de análisis y métricas avanzadas
    Especializado en anuncios esotéricos
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializar el servicio de analytics
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = config_path or self._get_default_config_path()
        
        # Configuraciones
        self.config = {}
        
        # Datos en memoria para análisis
        self.metrics_data = defaultdict(list)
        self.historical_data = defaultdict(list)
        self.benchmarks = {}
        
        # Modelos de análisis
        self.trend_models = {}
        self.anomaly_thresholds = {}
        
        # Cache para optimizar consultas
        self.cache = {
            'insights': {},
            'trends': {},
            'benchmarks': {},
            'predictions': {}
        }
        
        # Cargar configuraciones
        self._load_config()
        self._initialize_benchmarks()
        self._setup_anomaly_detection()
        
        logger.info("Analytics Service inicializado correctamente")
    
    def _get_default_config_path(self) -> str:
        """Obtener ruta por defecto de configuración"""
        return "config/analytics_config.yaml"
    
    def _load_config(self) -> None:
        """Cargar configuración del servicio"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                self._create_default_config()
            
            logger.info("Configuración de Analytics cargada")
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Crear configuración por defecto"""
        self.config = {
            'analytics': {
                'data_retention_days': 365,
                'anomaly_sensitivity': 0.8,
                'trend_analysis_window': 30,
                'benchmark_update_frequency': 'weekly',
                'cache_duration_minutes': 60
            },
            'esoteric_categories': {
                'amarres_amor': {
                    'avg_ctr': 3.2,
                    'avg_conversion_rate': 8.5,
                    'avg_cpc': 1.85,
                    'seasonal_peaks': ['febrero', 'mayo', 'diciembre']
                },
                'tarot': {
                    'avg_ctr': 2.8,
                    'avg_conversion_rate': 12.3,
                    'avg_cpc': 1.45,
                    'seasonal_peaks': ['enero', 'octubre', 'diciembre']
                },
                'limpias_espirituales': {
                    'avg_ctr': 2.5,
                    'avg_conversion_rate': 15.2,
                    'avg_cpc': 2.10,
                    'seasonal_peaks': ['marzo', 'septiembre']
                },
                'rituales_dinero': {
                    'avg_ctr': 3.8,
                    'avg_conversion_rate': 6.8,
                    'avg_cpc': 2.35,
                    'seasonal_peaks': ['enero', 'abril', 'noviembre']
                }
            },
            'thresholds': {
                'ctr_excellent': 4.0,
                'ctr_good': 2.5,
                'ctr_poor': 1.0,
                'conversion_rate_excellent': 15.0,
                'conversion_rate_good': 8.0,
                'conversion_rate_poor': 3.0,
                'quality_score_excellent': 8.0,
                'quality_score_good': 6.0,
                'quality_score_poor': 4.0
            }
        }
    
    def _initialize_benchmarks(self) -> None:
        """Inicializar benchmarks de la industria"""
        categories = self.config.get('esoteric_categories', {})
        
        for category, data in categories.items():
            self.benchmarks[category] = {
                MetricType.CTR: data.get('avg_ctr', 2.5),
                MetricType.CONVERSION_RATE: data.get('avg_conversion_rate', 10.0),
                MetricType.CPC: data.get('avg_cpc', 1.50),
                MetricType.QUALITY_SCORE: 6.5  # Promedio general
            }
        
        logger.info(f"Benchmarks inicializados para {len(categories)} categorías")
    
    def _setup_anomaly_detection(self) -> None:
        """Configurar detección de anomalías"""
        sensitivity = self.config['analytics']['anomaly_sensitivity']
        
        # Umbrales por métrica
        self.anomaly_thresholds = {
            MetricType.CTR: {
                'min_deviation': 0.5 * sensitivity,
                'max_deviation': 2.0 * sensitivity,
                'window_size': 7
            },
            MetricType.CONVERSION_RATE: {
                'min_deviation': 1.0 * sensitivity,
                'max_deviation': 3.0 * sensitivity,
                'window_size': 7
            },
            MetricType.CPC: {
                'min_deviation': 0.2 * sensitivity,
                'max_deviation': 1.0 * sensitivity,
                'window_size': 5
            },
            MetricType.COST: {
                'min_deviation': 10.0 * sensitivity,
                'max_deviation': 50.0 * sensitivity,
                'window_size': 3
            }
        }
    
    def add_metric_data(self, metric_data: MetricData) -> None:
        """
        Agregar datos de métrica
        
        Args:
            metric_data: Datos de la métrica
        """
        key = f"{metric_data.metric_type.value}_{metric_data.timestamp.date()}"
        self.metrics_data[metric_data.metric_type].append(metric_data)
        
        # Mantener solo datos dentro del período de retención
        retention_days = self.config['analytics']['data_retention_days']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        self.metrics_data[metric_data.metric_type] = [
            data for data in self.metrics_data[metric_data.metric_type]
            if data.timestamp >= cutoff_date
        ]
    
    def get_performance_insights(self, 
                               date_range: Tuple[datetime, datetime],
                               category: Optional[str] = None,
                               min_confidence: float = 0.7) -> List[PerformanceInsight]:
        """
        Obtener insights de rendimiento
        
        Args:
            date_range: Rango de fechas
            category: Categoría esotérica específica
            min_confidence: Confianza mínima para insights
            
        Returns:
            Lista de insights
        """
        cache_key = f"insights_{date_range[0].date()}_{date_range[1].date()}_{category}"
        
        # Verificar cache
        if cache_key in self.cache['insights']:
            cached_data = self.cache['insights'][cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(hours=1):
                return cached_data['data']
        
        insights = []
        
        # Analizar cada métrica
        for metric_type in MetricType:
            metric_insights = self._analyze_metric_performance(
                metric_type, date_range, category, min_confidence
            )
            insights.extend(metric_insights)
        
        # Insights de correlación
        correlation_insights = self._analyze_metric_correlations(date_range, category)
        insights.extend(correlation_insights)
        
        # Insights de segmentación
        segmentation_insights = self._analyze_segmentation(date_range, category)
        insights.extend(segmentation_insights)
        
        # Filtrar por confianza
        insights = [insight for insight in insights if insight.confidence >= min_confidence]
        
        # Ordenar por impacto y confianza
        insights.sort(key=lambda x: (x.impact == 'high', x.confidence), reverse=True)
        
        # Actualizar cache
        self.cache['insights'][cache_key] = {
            'data': insights,
            'timestamp': datetime.now()
        }
        
        return insights
    
    def _analyze_metric_performance(self, 
                                  metric_type: MetricType,
                                  date_range: Tuple[datetime, datetime],
                                  category: Optional[str],
                                  min_confidence: float) -> List[PerformanceInsight]:
        """Analizar rendimiento de una métrica específica"""
        insights = []
        
        # Obtener datos de la métrica
        metric_data = self._get_metric_data(metric_type, date_range, category)
        
        if len(metric_data) < 5:  # Datos insuficientes
            return insights
        
        values = [data.value for data in metric_data]
        
        # Análisis estadístico básico
        mean_value = statistics.mean(values)
        median_value = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Comparar con benchmarks
        benchmark_value = self._get_benchmark_value(metric_type, category)
        
        if benchmark_value:
            performance_ratio = mean_value / benchmark_value
            
            if performance_ratio > 1.2:  # 20% mejor que benchmark
                insights.append(PerformanceInsight(
                    title=f"Excelente rendimiento en {metric_type.value}",
                    description=f"La métrica está {((performance_ratio - 1) * 100):.1f}% por encima del benchmark de la industria",
                    impact="high",
                    recommendation="Mantener las estrategias actuales y escalar las campañas exitosas",
                    metric_affected=metric_type,
                    confidence=0.9,
                    data_points=metric_data
                ))
            elif performance_ratio < 0.8:  # 20% peor que benchmark
                insights.append(PerformanceInsight(
                    title=f"Oportunidad de mejora en {metric_type.value}",
                    description=f"La métrica está {((1 - performance_ratio) * 100):.1f}% por debajo del benchmark",
                    impact="high",
                    recommendation=self._get_improvement_recommendation(metric_type),
                    metric_affected=metric_type,
                    confidence=0.85,
                    data_points=metric_data
                ))
        
        # Análisis de variabilidad
        if std_dev > mean_value * 0.3:  # Alta variabilidad
            insights.append(PerformanceInsight(
                title=f"Alta variabilidad en {metric_type.value}",
                description=f"La métrica muestra inconsistencia con desviación estándar de {std_dev:.2f}",
                impact="medium",
                recommendation="Revisar configuraciones de campañas y optimizar para mayor consistencia",
                metric_affected=metric_type,
                confidence=0.75,
                data_points=metric_data
            ))
        
        return insights
    
    def _analyze_metric_correlations(self, 
                                   date_range: Tuple[datetime, datetime],
                                   category: Optional[str]) -> List[PerformanceInsight]:
        """Analizar correlaciones entre métricas"""
        insights = []
        
        # Obtener datos de múltiples métricas
        ctr_data = self._get_metric_data(MetricType.CTR, date_range, category)
        conversion_data = self._get_metric_data(MetricType.CONVERSION_RATE, date_range, category)
        cpc_data = self._get_metric_data(MetricType.CPC, date_range, category)
        
        if len(ctr_data) < 5 or len(conversion_data) < 5:
            return insights
        
        # Correlación CTR vs Conversion Rate
        ctr_values = [data.value for data in ctr_data]
        conv_values = [data.value for data in conversion_data]
        
        if len(ctr_values) == len(conv_values):
            correlation = np.corrcoef(ctr_values, conv_values)[0, 1]
            
            if correlation > 0.7:
                insights.append(PerformanceInsight(
                    title="Fuerte correlación positiva CTR-Conversiones",
                    description=f"CTR y tasa de conversión muestran correlación de {correlation:.2f}",
                    impact="medium",
                    recommendation="Optimizar para CTR ya que impacta directamente las conversiones",
                    metric_affected=MetricType.CTR,
                    confidence=0.8,
                    data_points=ctr_data + conversion_data
                ))
            elif correlation < -0.5:
                insights.append(PerformanceInsight(
                    title="Correlación negativa CTR-Conversiones detectada",
                    description=f"CTR alto no se traduce en conversiones (correlación: {correlation:.2f})",
                    impact="high",
                    recommendation="Revisar calidad del tráfico y relevancia de landing pages",
                    metric_affected=MetricType.CONVERSION_RATE,
                    confidence=0.85,
                    data_points=ctr_data + conversion_data
                ))
        
        return insights
    
    def _analyze_segmentation(self, 
                            date_range: Tuple[datetime, datetime],
                            category: Optional[str]) -> List[PerformanceInsight]:
        """Analizar segmentación de audiencias"""
        insights = []
        
        # Análisis por dimensiones (simulado)
        segments = ['mobile', 'desktop', 'tablet']
        
        for segment in segments:
            # Simular datos de segmento
            segment_performance = self._simulate_segment_performance(segment)
            
            if segment_performance['conversion_rate'] > 15.0:
                insights.append(PerformanceInsight(
                    title=f"Segmento {segment} de alto rendimiento",
                    description=f"Tasa de conversión de {segment_performance['conversion_rate']:.1f}%",
                    impact="medium",
                    recommendation=f"Aumentar presupuesto para segmento {segment}",
                    metric_affected=MetricType.CONVERSION_RATE,
                    confidence=0.7,
                    data_points=[]
                ))
        
        return insights
    
    def get_trend_analysis(self, 
                          metric_type: MetricType,
                          date_range: Tuple[datetime, datetime],
                          granularity: TimeGranularity = TimeGranularity.DAILY,
                          category: Optional[str] = None) -> TrendAnalysis:
        """
        Realizar análisis de tendencias
        
        Args:
            metric_type: Tipo de métrica
            date_range: Rango de fechas
            granularity: Granularidad temporal
            category: Categoría específica
            
        Returns:
            Análisis de tendencias
        """
        # Obtener datos históricos
        metric_data = self._get_metric_data(metric_type, date_range, category)
        
        if len(metric_data) < 7:
            return TrendAnalysis(
                metric=metric_type,
                trend_direction="insufficient_data",
                trend_strength=0.0,
                period_comparison={},
                seasonal_patterns=[],
                forecast=[]
            )
        
        # Preparar datos para análisis
        df = pd.DataFrame([
            {
                'timestamp': data.timestamp,
                'value': data.value,
                'date': data.timestamp.date()
            }
            for data in metric_data
        ])
        
        # Agrupar por granularidad
        if granularity == TimeGranularity.DAILY:
            df_grouped = df.groupby('date')['value'].mean().reset_index()
        elif granularity == TimeGranularity.WEEKLY:
            df['week'] = df['timestamp'].dt.isocalendar().week
            df_grouped = df.groupby('week')['value'].mean().reset_index()
        else:  # MONTHLY
            df['month'] = df['timestamp'].dt.month
            df_grouped = df.groupby('month')['value'].mean().reset_index()
        
        values = df_grouped['value'].tolist()
        
        # Calcular tendencia
        trend_direction, trend_strength = self._calculate_trend(values)
        
        # Comparación de períodos
        period_comparison = self._calculate_period_comparison(values)
        
        # Patrones estacionales
        seasonal_patterns = self._detect_seasonal_patterns(df, metric_type, category)
        
        # Pronóstico simple
        forecast = self._generate_simple_forecast(values, 7)  # 7 días hacia adelante
        
        return TrendAnalysis(
            metric=metric_type,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            period_comparison=period_comparison,
            seasonal_patterns=seasonal_patterns,
            forecast=forecast
        )
    
    def _calculate_trend(self, values: List[float]) -> Tuple[str, float]:
        """Calcular dirección y fuerza de tendencia"""
        if len(values) < 3:
            return "stable", 0.0
        
        # Regresión lineal simple
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calcular pendiente
        slope = np.polyfit(x, y, 1)[0]
        
        # Calcular correlación para fuerza
        correlation = np.corrcoef(x, y)[0, 1]
        trend_strength = abs(correlation)
        
        # Determinar dirección
        if slope > 0.1:
            trend_direction = "up"
        elif slope < -0.1:
            trend_direction = "down"
        else:
            trend_direction = "stable"
        
        return trend_direction, trend_strength
    
    def _calculate_period_comparison(self, values: List[float]) -> Dict[str, float]:
        """Calcular comparación entre períodos"""
        if len(values) < 4:
            return {}
        
        mid_point = len(values) // 2
        first_half = values[:mid_point]
        second_half = values[mid_point:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        return {
            'first_period_avg': first_avg,
            'second_period_avg': second_avg,
            'change_percent': change_percent
        }
    
    def _detect_seasonal_patterns(self, df: pd.DataFrame, 
                                 metric_type: MetricType,
                                 category: Optional[str]) -> List[Dict[str, Any]]:
        """Detectar patrones estacionales"""
        patterns = []
        
        # Obtener patrones conocidos de la configuración
        if category and category in self.config.get('esoteric_categories', {}):
            seasonal_peaks = self.config['esoteric_categories'][category].get('seasonal_peaks', [])
            
            for peak in seasonal_peaks:
                patterns.append({
                    'period': peak,
                    'type': 'seasonal_peak',
                    'confidence': 0.8,
                    'description': f"Pico estacional típico en {peak}"
                })
        
        # Análisis por día de la semana
        if len(df) > 14:  # Al menos 2 semanas de datos
            df['day_of_week'] = df['timestamp'].dt.day_name()
            day_avg = df.groupby('day_of_week')['value'].mean()
            
            best_day = day_avg.idxmax()
            worst_day = day_avg.idxmin()
            
            patterns.append({
                'period': 'weekly',
                'type': 'day_of_week_pattern',
                'best_day': best_day,
                'worst_day': worst_day,
                'confidence': 0.6,
                'description': f"Mejor rendimiento: {best_day}, Peor: {worst_day}"
            })
        
        return patterns
    
    def _generate_simple_forecast(self, values: List[float], periods: int) -> List[Dict[str, Any]]:
        """Generar pronóstico simple"""
        if len(values) < 3:
            return []
        
        # Promedio móvil simple
        window_size = min(7, len(values))
        recent_avg = statistics.mean(values[-window_size:])
        
        # Tendencia
        trend_slope = (values[-1] - values[0]) / len(values) if len(values) > 1 else 0
        
        forecast = []
        for i in range(1, periods + 1):
            predicted_value = recent_avg + (trend_slope * i)
            
            forecast.append({
                'period': i,
                'predicted_value': max(0, predicted_value),  # No valores negativos
                'confidence': max(0.3, 0.9 - (i * 0.1))  # Confianza decrece con el tiempo
            })
        
        return forecast
    
    def detect_anomalies(self, 
                        metric_type: MetricType,
                        date_range: Tuple[datetime, datetime],
                        category: Optional[str] = None) -> List[AnomalyDetection]:
        """
        Detectar anomalías en métricas
        
        Args:
            metric_type: Tipo de métrica
            date_range: Rango de fechas
            category: Categoría específica
            
        Returns:
            Lista de anomalías detectadas
        """
        anomalies = []
        
        # Obtener datos
        metric_data = self._get_metric_data(metric_type, date_range, category)
        
        if len(metric_data) < 10:  # Datos insuficientes
            return anomalies
        
        values = [data.value for data in metric_data]
        
        # Calcular estadísticas base
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Obtener umbrales
        thresholds = self.anomaly_thresholds.get(metric_type, {})
        min_deviation = thresholds.get('min_deviation', 1.0)
        max_deviation = thresholds.get('max_deviation', 3.0)
        
        # Detectar anomalías
        for data in metric_data:
            z_score = abs(data.value - mean_value) / std_dev if std_dev > 0 else 0
            
            if z_score > max_deviation:
                severity = "critical"
            elif z_score > min_deviation * 2:
                severity = "high"
            elif z_score > min_deviation:
                severity = "medium"
            else:
                continue  # No es anomalía
            
            # Generar posibles causas
            possible_causes = self._generate_anomaly_causes(metric_type, data.value, mean_value)
            
            anomalies.append(AnomalyDetection(
                timestamp=data.timestamp,
                metric=metric_type,
                expected_value=mean_value,
                actual_value=data.value,
                deviation_score=z_score,
                severity=severity,
                possible_causes=possible_causes
            ))
        
        return anomalies
    
    def _generate_anomaly_causes(self, metric_type: MetricType, 
                               actual_value: float, expected_value: float) -> List[str]:
        """Generar posibles causas de anomalías"""
        causes = []
        
        is_higher = actual_value > expected_value
        
        if metric_type == MetricType.CTR:
            if is_higher:
                causes = [
                    "Nuevo anuncio con copy muy atractivo",
                    "Mejora en la segmentación de audiencia",
                    "Evento estacional o tendencia viral"
                ]
            else:
                causes = [
                    "Fatiga del anuncio",
                    "Aumento en la competencia",
                    "Cambios en el algoritmo de Google"
                ]
        
        elif metric_type == MetricType.CONVERSION_RATE:
            if is_higher:
                causes = [
                    "Optimización de landing page",
                    "Mejor calidad del tráfico",
                    "Promoción especial activa"
                ]
            else:
                causes = [
                    "Problemas técnicos en el sitio web",
                    "Tráfico de baja calidad",
                    "Cambios en la página de destino"
                ]
        
        elif metric_type == MetricType.CPC:
            if is_higher:
                causes = [
                    "Aumento en la competencia",
                    "Cambios en la estrategia de puja",
                    "Expansión a keywords más competitivas"
                ]
            else:
                causes = [
                    "Mejora en Quality Score",
                    "Reducción de competencia",
                    "Optimización de pujas automáticas"
                ]
        
        elif metric_type == MetricType.COST:
            if is_higher:
                causes = [
                    "Aumento en el presupuesto",
                    "Expansión de campañas",
                    "Mayor volumen de tráfico"
                ]
            else:
                causes = [
                    "Pausa de campañas",
                    "Reducción de presupuesto",
                    "Problemas de aprobación de anuncios"
                ]
        
        return causes
    
    def get_competitive_benchmarks(self, category: str) -> List[CompetitorBenchmark]:
        """
        Obtener benchmarks competitivos
        
        Args:
            category: Categoría esotérica
            
        Returns:
            Lista de benchmarks
        """
        benchmarks = []
        
        if category not in self.benchmarks:
            return benchmarks
        
        category_benchmarks = self.benchmarks[category]
        
        for metric_type, industry_avg in category_benchmarks.items():
            # Simular nuestros valores (en producción vendrían de datos reales)
            our_value = self._simulate_our_performance(metric_type, industry_avg)
            
            # Calcular percentil (simulado)
            percentile_rank = self._calculate_percentile_rank(our_value, industry_avg)
            
            # Top quartile (25% superior)
            top_quartile = industry_avg * 1.3
            
            # Análisis de brecha
            gap_analysis = self._generate_gap_analysis(our_value, industry_avg, top_quartile)
            
            benchmarks.append(CompetitorBenchmark(
                metric=metric_type,
                our_value=our_value,
                industry_average=industry_avg,
                top_quartile=top_quartile,
                percentile_rank=percentile_rank,
                gap_analysis=gap_analysis
            ))
        
        return benchmarks
    
    def _simulate_our_performance(self, metric_type: MetricType, industry_avg: float) -> float:
        """Simular nuestro rendimiento"""
        import random
        
        # Simular variación del -20% al +30% respecto al promedio
        variation = random.uniform(-0.2, 0.3)
        return industry_avg * (1 + variation)
    
    def _calculate_percentile_rank(self, our_value: float, industry_avg: float) -> float:
        """Calcular rango percentil"""
        # Simulación simple basada en la relación con el promedio
        ratio = our_value / industry_avg
        
        if ratio >= 1.3:
            return 90.0
        elif ratio >= 1.1:
            return 75.0
        elif ratio >= 0.9:
            return 50.0
        elif ratio >= 0.8:
            return 25.0
        else:
            return 10.0
    
    def _generate_gap_analysis(self, our_value: float, 
                             industry_avg: float, top_quartile: float) -> str:
        """Generar análisis de brecha"""
        if our_value >= top_quartile:
            return "Rendimiento superior - mantener estrategias actuales"
        elif our_value >= industry_avg:
            return f"Por encima del promedio - oportunidad de llegar al top quartile (+{((top_quartile - our_value) / our_value * 100):.1f}%)"
        else:
            return f"Por debajo del promedio - necesita mejora significativa (+{((industry_avg - our_value) / our_value * 100):.1f}%)"
    
    def _get_metric_data(self, metric_type: MetricType, 
                        date_range: Tuple[datetime, datetime],
                        category: Optional[str] = None) -> List[MetricData]:
        """Obtener datos de métrica filtrados"""
        data = self.metrics_data.get(metric_type, [])
        
        # Filtrar por rango de fechas
        filtered_data = [
            d for d in data 
            if date_range[0] <= d.timestamp <= date_range[1]
        ]
        
        # Filtrar por categoría si se especifica
        if category:
            filtered_data = [
                d for d in filtered_data
                if d.dimensions.get('category') == category
            ]
        
        return filtered_data
    
    def _get_benchmark_value(self, metric_type: MetricType, 
                           category: Optional[str] = None) -> Optional[float]:
        """Obtener valor de benchmark"""
        if category and category in self.benchmarks:
            return self.benchmarks[category].get(metric_type)
        
        # Valores por defecto si no hay categoría específica
        defaults = {
            MetricType.CTR: 2.5,
            MetricType.CONVERSION_RATE: 10.0,
            MetricType.CPC: 1.50,
            MetricType.QUALITY_SCORE: 6.5
        }
        
        return defaults.get(metric_type)
    
    def _get_improvement_recommendation(self, metric_type: MetricType) -> str:
        """Obtener recomendación de mejora"""
        recommendations = {
            MetricType.CTR: "Optimizar headlines y descriptions, probar nuevos CTAs, mejorar segmentación",
            MetricType.CONVERSION_RATE: "Revisar landing pages, optimizar formularios, mejorar propuesta de valor",
            MetricType.CPC: "Mejorar Quality Score, optimizar keywords, ajustar estrategia de pujas",
            MetricType.COST: "Revisar presupuestos, pausar campañas de bajo rendimiento, optimizar horarios",
            MetricType.QUALITY_SCORE: "Mejorar relevancia de anuncios, optimizar landing pages, revisar keywords"
        }
        
        return recommendations.get(metric_type, "Revisar y optimizar configuraciones de campaña")
    
    def _simulate_segment_performance(self, segment: str) -> Dict[str, float]:
        """Simular rendimiento de segmento"""
        import random
        
        base_performance = {
            'mobile': {'ctr': 3.2, 'conversion_rate': 12.5, 'cpc': 1.40},
            'desktop': {'ctr': 2.8, 'conversion_rate': 15.8, 'cpc': 1.65},
            'tablet': {'ctr': 2.1, 'conversion_rate': 8.9, 'cpc': 1.55}
        }
        
        base = base_performance.get(segment, {'ctr': 2.5, 'conversion_rate': 10.0, 'cpc': 1.50})
        
        # Agregar variación aleatoria
        return {
            'ctr': base['ctr'] * random.uniform(0.8, 1.3),
            'conversion_rate': base['conversion_rate'] * random.uniform(0.7, 1.4),
            'cpc': base['cpc'] * random.uniform(0.9, 1.2)
        }
    
    def generate_analytics_report(self, 
                                date_range: Tuple[datetime, datetime],
                                category: Optional[str] = None) -> Dict[str, Any]:
        """
        Generar reporte completo de analytics
        
        Args:
            date_range: Rango de fechas
            category: Categoría específica
            
        Returns:
            Reporte completo
        """
        report = {
            'period': {
                'start_date': date_range[0].strftime('%Y-%m-%d'),
                'end_date': date_range[1].strftime('%Y-%m-%d'),
                'category': category or 'all'
            },
            'performance_insights': [],
            'trend_analysis': {},
            'anomalies': [],
            'benchmarks': [],
            'summary': {}
        }
        
        # Insights de rendimiento
        insights = self.get_performance_insights(date_range, category)
        report['performance_insights'] = [asdict(insight) for insight in insights]
        
        # Análisis de tendencias para métricas clave
        key_metrics = [MetricType.CTR, MetricType.CONVERSION_RATE, MetricType.CPC]
        for metric in key_metrics:
            trend = self.get_trend_analysis(metric, date_range, category=category)
            report['trend_analysis'][metric.value] = asdict(trend)
        
        # Detección de anomalías
        for metric in key_metrics:
            anomalies = self.detect_anomalies(metric, date_range, category)
            report['anomalies'].extend([asdict(anomaly) for anomaly in anomalies])
        
        # Benchmarks competitivos
        if category:
            benchmarks = self.get_competitive_benchmarks(category)
            report['benchmarks'] = [asdict(benchmark) for benchmark in benchmarks]
        
        # Resumen ejecutivo
        report['summary'] = {
            'total_insights': len(insights),
            'high_impact_insights': len([i for i in insights if i.impact == 'high']),
            'anomalies_detected': len(report['anomalies']),
            'critical_anomalies': len([a for a in report['anomalies'] if a['severity'] == 'critical']),
            'generated_at': datetime.now().isoformat()
        }
        
        return report

# Función de utilidad para crear servicio rápidamente
def create_analytics_service(config_path: Optional[str] = None) -> EsotericAnalyticsService:
    """
    Crear servicio de analytics
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Servicio de analytics
    """
    return EsotericAnalyticsService(config_path)

if __name__ == "__main__":
    # Ejemplo de uso
    service = EsotericAnalyticsService()
    
    # Agregar datos de ejemplo
    from datetime import datetime, timedelta
    
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        
        # Simular datos de CTR
        ctr_value = 2.5 + (i * 0.1) + np.random.normal(0, 0.3)
        service.add_metric_data(MetricData(
            metric_type=MetricType.CTR,
            value=max(0.5, ctr_value),
            timestamp=date,
            dimensions={'category': 'amarres_amor', 'device': 'mobile'}
        ))
        
        # Simular datos de conversión
        conv_value = 10.0 + (i * 0.2) + np.random.normal(0, 1.5)
        service.add_metric_data(MetricData(
            metric_type=MetricType.CONVERSION_RATE,
            value=max(1.0, conv_value),
            timestamp=date,
            dimensions={'category': 'amarres_amor', 'device': 'mobile'}
        ))
    
    # Generar reporte
    date_range = (base_date, datetime.now())
    report = service.generate_analytics_report(date_range, 'amarres_amor')
    
    print("=" * 60)
    print("📊 REPORTE DE ANALYTICS")
    print("=" * 60)
    print(f"Período: {report['period']['start_date']} - {report['period']['end_date']}")
    print(f"Categoría: {report['period']['category']}")
    print(f"\n📈 RESUMEN:")
    print(f"- Total de insights: {report['summary']['total_insights']}")
    print(f"- Insights de alto impacto: {report['summary']['high_impact_insights']}")
    print(f"- Anomalías detectadas: {report['summary']['anomalies_detected']}")
    print(f"- Anomalías críticas: {report['summary']['critical_anomalies']}")
    
    # Mostrar algunos insights
    if report['performance_insights']:
        print(f"\n🎯 INSIGHTS PRINCIPALES:")
        for insight in report['performance_insights'][:3]:
            print(f"- {insight['title']} (Impacto: {insight['impact']})")
            print(f"  {insight['description']}")
    
    # Mostrar tendencias
    print(f"\n📈 TENDENCIAS:")
    for metric, trend in report['trend_analysis'].items():
        print(f"- {metric}: {trend['trend_direction']} (Fuerza: {trend['trend_strength']:.2f})")