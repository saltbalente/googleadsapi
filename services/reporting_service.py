#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
REPORTING SERVICE PARA GENERADOR IA 2.0
Servicio completo para generación de reportes avanzados
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
import base64
from io import BytesIO

# Importaciones para generación de gráficos
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logging.warning("Matplotlib/Seaborn no disponibles. Gráficos deshabilitados.")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Tipos de reportes"""
    PERFORMANCE = "performance"
    CAMPAIGN_ANALYSIS = "campaign_analysis"
    AD_COMPARISON = "ad_comparison"
    TREND_ANALYSIS = "trend_analysis"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    ROI_ANALYSIS = "roi_analysis"
    AUDIENCE_INSIGHTS = "audience_insights"
    KEYWORD_PERFORMANCE = "keyword_performance"

class ReportFormat(Enum):
    """Formatos de reporte"""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"

class ChartType(Enum):
    """Tipos de gráficos"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"

@dataclass
class ReportConfig:
    """Configuración de reporte"""
    report_type: ReportType
    format: ReportFormat
    date_range: Tuple[datetime, datetime]
    categories: List[str]
    metrics: List[str]
    include_charts: bool = True
    include_insights: bool = True
    include_recommendations: bool = True
    custom_filters: Dict[str, Any] = None

@dataclass
class ChartConfig:
    """Configuración de gráfico"""
    chart_type: ChartType
    title: str
    data: Dict[str, Any]
    x_axis: str
    y_axis: str
    color_scheme: str = "viridis"
    width: int = 800
    height: int = 600

@dataclass
class ReportSection:
    """Sección de reporte"""
    title: str
    content: str
    charts: List[str] = None  # Base64 encoded charts
    data_tables: List[Dict[str, Any]] = None
    insights: List[str] = None
    recommendations: List[str] = None

@dataclass
class GeneratedReport:
    """Reporte generado"""
    report_id: str
    title: str
    generated_at: datetime
    config: ReportConfig
    sections: List[ReportSection]
    summary: Dict[str, Any]
    file_path: Optional[str] = None

class EsotericReportingService:
    """
    Servicio completo para generación de reportes avanzados
    Especializado en anuncios esotéricos
    """
    
    def __init__(self, config_path: Optional[str] = None, output_dir: Optional[str] = None):
        """
        Inicializar el servicio de reportes
        
        Args:
            config_path: Ruta al archivo de configuración
            output_dir: Directorio de salida para reportes
        """
        self.config_path = config_path or self._get_default_config_path()
        self.output_dir = Path(output_dir or "reports")
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuraciones
        self.config = {}
        
        # Templates de reportes
        self.report_templates = {}
        
        # Cache para datos y gráficos
        self.cache = {
            'data': {},
            'charts': {},
            'reports': {}
        }
        
        # Configurar matplotlib si está disponible
        if PLOTTING_AVAILABLE:
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
        
        # Cargar configuraciones
        self._load_config()
        self._load_templates()
        
        logger.info("Reporting Service inicializado correctamente")
    
    def _get_default_config_path(self) -> str:
        """Obtener ruta por defecto de configuración"""
        return "config/reporting_config.yaml"
    
    def _load_config(self) -> None:
        """Cargar configuración del servicio"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                self._create_default_config()
            
            logger.info("Configuración de Reporting cargada")
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Crear configuración por defecto"""
        self.config = {
            'reporting': {
                'default_format': 'html',
                'include_charts': True,
                'chart_quality': 'high',
                'max_data_points': 1000,
                'cache_duration_hours': 24
            },
            'styling': {
                'primary_color': '#2E86AB',
                'secondary_color': '#A23B72',
                'accent_color': '#F18F01',
                'background_color': '#F8F9FA',
                'text_color': '#212529',
                'font_family': 'Arial, sans-serif'
            },
            'esoteric_categories': {
                'amarres_amor': {
                    'display_name': 'Amarres de Amor',
                    'color': '#E91E63',
                    'icon': '💕'
                },
                'tarot': {
                    'display_name': 'Tarot y Videncia',
                    'color': '#9C27B0',
                    'icon': '🔮'
                },
                'limpias_espirituales': {
                    'display_name': 'Limpias Espirituales',
                    'color': '#00BCD4',
                    'icon': '✨'
                },
                'rituales_dinero': {
                    'display_name': 'Rituales de Dinero',
                    'color': '#4CAF50',
                    'icon': '💰'
                }
            },
            'metrics': {
                'primary': ['impressions', 'clicks', 'conversions', 'cost'],
                'secondary': ['ctr', 'conversion_rate', 'cpc', 'cpa', 'roas'],
                'advanced': ['quality_score', 'search_impression_share', 'top_impression_share']
            }
        }
    
    def _load_templates(self) -> None:
        """Cargar templates de reportes"""
        self.report_templates = {
            ReportType.PERFORMANCE: {
                'title': 'Reporte de Rendimiento',
                'sections': [
                    'executive_summary',
                    'key_metrics',
                    'performance_trends',
                    'top_performing_ads',
                    'recommendations'
                ]
            },
            ReportType.CAMPAIGN_ANALYSIS: {
                'title': 'Análisis de Campañas',
                'sections': [
                    'campaign_overview',
                    'budget_analysis',
                    'audience_performance',
                    'geographic_analysis',
                    'optimization_opportunities'
                ]
            },
            ReportType.AD_COMPARISON: {
                'title': 'Comparación de Anuncios',
                'sections': [
                    'ad_performance_comparison',
                    'creative_analysis',
                    'a_b_test_results',
                    'winning_elements',
                    'next_steps'
                ]
            },
            ReportType.TREND_ANALYSIS: {
                'title': 'Análisis de Tendencias',
                'sections': [
                    'trend_overview',
                    'seasonal_patterns',
                    'performance_evolution',
                    'forecast',
                    'strategic_recommendations'
                ]
            }
        }
    
    def generate_report(self, config: ReportConfig) -> GeneratedReport:
        """
        Generar reporte completo
        
        Args:
            config: Configuración del reporte
            
        Returns:
            Reporte generado
        """
        report_id = self._generate_report_id()
        
        logger.info(f"Generando reporte {config.report_type.value} - ID: {report_id}")
        
        # Obtener template
        template = self.report_templates.get(config.report_type, {})
        title = template.get('title', f'Reporte {config.report_type.value}')
        
        # Generar secciones
        sections = []
        for section_name in template.get('sections', []):
            section = self._generate_section(section_name, config)
            if section:
                sections.append(section)
        
        # Generar resumen
        summary = self._generate_summary(sections, config)
        
        # Crear reporte
        report = GeneratedReport(
            report_id=report_id,
            title=title,
            generated_at=datetime.now(),
            config=config,
            sections=sections,
            summary=summary
        )
        
        # Exportar según formato
        if config.format != ReportFormat.JSON:
            file_path = self._export_report(report, config.format)
            report.file_path = file_path
        
        logger.info(f"Reporte generado exitosamente: {report_id}")
        return report
    
    def _generate_report_id(self) -> str:
        """Generar ID único para reporte"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"report_{timestamp}"
    
    def _generate_section(self, section_name: str, config: ReportConfig) -> Optional[ReportSection]:
        """Generar sección específica del reporte"""
        try:
            if section_name == 'executive_summary':
                return self._generate_executive_summary(config)
            elif section_name == 'key_metrics':
                return self._generate_key_metrics_section(config)
            elif section_name == 'performance_trends':
                return self._generate_performance_trends_section(config)
            elif section_name == 'top_performing_ads':
                return self._generate_top_performing_ads_section(config)
            elif section_name == 'recommendations':
                return self._generate_recommendations_section(config)
            elif section_name == 'campaign_overview':
                return self._generate_campaign_overview_section(config)
            elif section_name == 'ad_performance_comparison':
                return self._generate_ad_comparison_section(config)
            elif section_name == 'trend_overview':
                return self._generate_trend_overview_section(config)
            else:
                return self._generate_generic_section(section_name, config)
                
        except Exception as e:
            logger.error(f"Error generando sección {section_name}: {e}")
            return None
    
    def _generate_executive_summary(self, config: ReportConfig) -> ReportSection:
        """Generar resumen ejecutivo"""
        # Simular datos de resumen
        period_days = (config.date_range[1] - config.date_range[0]).days
        
        # Datos simulados
        total_impressions = np.random.randint(50000, 200000)
        total_clicks = np.random.randint(1000, 5000)
        total_conversions = np.random.randint(50, 300)
        total_cost = np.random.uniform(500, 3000)
        
        ctr = (total_clicks / total_impressions) * 100
        conversion_rate = (total_conversions / total_clicks) * 100
        cpc = total_cost / total_clicks
        cpa = total_cost / total_conversions
        
        content = f"""
        <div class="executive-summary">
            <h3>📊 Resumen Ejecutivo</h3>
            <p><strong>Período de análisis:</strong> {config.date_range[0].strftime('%d/%m/%Y')} - {config.date_range[1].strftime('%d/%m/%Y')} ({period_days} días)</p>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <h4>👁️ Impresiones</h4>
                    <p class="metric-value">{total_impressions:,}</p>
                </div>
                <div class="metric-card">
                    <h4>👆 Clics</h4>
                    <p class="metric-value">{total_clicks:,}</p>
                </div>
                <div class="metric-card">
                    <h4>🎯 Conversiones</h4>
                    <p class="metric-value">{total_conversions}</p>
                </div>
                <div class="metric-card">
                    <h4>💰 Costo Total</h4>
                    <p class="metric-value">${total_cost:,.2f}</p>
                </div>
            </div>
            
            <div class="kpi-summary">
                <p><strong>CTR:</strong> {ctr:.2f}% | <strong>Tasa de Conversión:</strong> {conversion_rate:.2f}% | <strong>CPC:</strong> ${cpc:.2f} | <strong>CPA:</strong> ${cpa:.2f}</p>
            </div>
        </div>
        """
        
        # Generar gráfico de resumen si está habilitado
        charts = []
        if config.include_charts and PLOTTING_AVAILABLE:
            chart_data = {
                'metrics': ['Impresiones', 'Clics', 'Conversiones'],
                'values': [total_impressions/1000, total_clicks, total_conversions]
            }
            chart = self._create_bar_chart(
                data=chart_data,
                title="Métricas Principales",
                x_axis='metrics',
                y_axis='values'
            )
            if chart:
                charts.append(chart)
        
        return ReportSection(
            title="Resumen Ejecutivo",
            content=content,
            charts=charts,
            insights=[
                f"Se generaron {total_impressions:,} impresiones en {period_days} días",
                f"CTR de {ctr:.2f}% {'por encima' if ctr > 2.5 else 'por debajo'} del promedio de la industria",
                f"Costo por conversión de ${cpa:.2f}"
            ]
        )
    
    def _generate_key_metrics_section(self, config: ReportConfig) -> ReportSection:
        """Generar sección de métricas clave"""
        # Simular datos de métricas por categoría
        metrics_data = {}
        
        for category in config.categories:
            category_info = self.config['esoteric_categories'].get(category, {})
            display_name = category_info.get('display_name', category)
            
            metrics_data[display_name] = {
                'impressions': np.random.randint(10000, 50000),
                'clicks': np.random.randint(200, 1500),
                'conversions': np.random.randint(10, 100),
                'cost': np.random.uniform(100, 800),
                'ctr': np.random.uniform(1.5, 4.5),
                'conversion_rate': np.random.uniform(5.0, 20.0)
            }
        
        # Crear tabla HTML
        table_html = "<table class='metrics-table'><thead><tr><th>Categoría</th><th>Impresiones</th><th>Clics</th><th>Conversiones</th><th>CTR</th><th>Tasa Conv.</th><th>Costo</th></tr></thead><tbody>"
        
        for category, data in metrics_data.items():
            table_html += f"""
            <tr>
                <td>{category}</td>
                <td>{data['impressions']:,}</td>
                <td>{data['clicks']:,}</td>
                <td>{data['conversions']}</td>
                <td>{data['ctr']:.2f}%</td>
                <td>{data['conversion_rate']:.2f}%</td>
                <td>${data['cost']:.2f}</td>
            </tr>
            """
        
        table_html += "</tbody></table>"
        
        content = f"""
        <div class="key-metrics">
            <h3>📈 Métricas Clave por Categoría</h3>
            {table_html}
        </div>
        """
        
        # Generar gráfico de comparación
        charts = []
        if config.include_charts and PLOTTING_AVAILABLE:
            chart_data = {
                'categories': list(metrics_data.keys()),
                'conversions': [data['conversions'] for data in metrics_data.values()]
            }
            chart = self._create_bar_chart(
                data=chart_data,
                title="Conversiones por Categoría",
                x_axis='categories',
                y_axis='conversions'
            )
            if chart:
                charts.append(chart)
        
        return ReportSection(
            title="Métricas Clave",
            content=content,
            charts=charts,
            data_tables=[{'name': 'metrics_by_category', 'data': metrics_data}]
        )
    
    def _generate_performance_trends_section(self, config: ReportConfig) -> ReportSection:
        """Generar sección de tendencias de rendimiento"""
        # Simular datos de tendencias diarias
        days = (config.date_range[1] - config.date_range[0]).days
        dates = [config.date_range[0] + timedelta(days=i) for i in range(days)]
        
        # Generar datos con tendencia
        base_ctr = 2.5
        trend_data = []
        
        for i, date in enumerate(dates):
            # Simular tendencia con ruido
            trend_factor = 1 + (i / days) * 0.3  # Tendencia creciente
            noise = np.random.normal(0, 0.2)
            ctr_value = base_ctr * trend_factor + noise
            
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'ctr': max(0.5, ctr_value),
                'conversions': np.random.randint(5, 25),
                'cost': np.random.uniform(20, 100)
            })
        
        # Crear contenido HTML
        content = f"""
        <div class="performance-trends">
            <h3>📊 Tendencias de Rendimiento</h3>
            <p>Análisis de la evolución de métricas clave durante el período seleccionado.</p>
            
            <div class="trend-summary">
                <h4>Observaciones Principales:</h4>
                <ul>
                    <li>CTR muestra tendencia {'creciente' if trend_data[-1]['ctr'] > trend_data[0]['ctr'] else 'decreciente'}</li>
                    <li>Variabilidad en conversiones diarias</li>
                    <li>Costo promedio diario: ${np.mean([d['cost'] for d in trend_data]):.2f}</li>
                </ul>
            </div>
        </div>
        """
        
        # Generar gráfico de líneas
        charts = []
        if config.include_charts and PLOTTING_AVAILABLE:
            chart_data = {
                'dates': [d['date'] for d in trend_data],
                'ctr': [d['ctr'] for d in trend_data]
            }
            chart = self._create_line_chart(
                data=chart_data,
                title="Evolución del CTR",
                x_axis='dates',
                y_axis='ctr'
            )
            if chart:
                charts.append(chart)
        
        return ReportSection(
            title="Tendencias de Rendimiento",
            content=content,
            charts=charts,
            data_tables=[{'name': 'daily_trends', 'data': trend_data}]
        )
    
    def _generate_top_performing_ads_section(self, config: ReportConfig) -> ReportSection:
        """Generar sección de anuncios top"""
        # Simular datos de anuncios top
        top_ads = []
        
        esoteric_headlines = [
            "Amarres de Amor Efectivos - Resultados en 24h",
            "Tarot Certero - Consulta Gratis por WhatsApp",
            "Limpia Espiritual Poderosa - Maestra Experta",
            "Ritual de Dinero - Abundancia Garantizada",
            "Videncia Real - 15 Años de Experiencia"
        ]
        
        for i, headline in enumerate(esoteric_headlines):
            top_ads.append({
                'ad_id': f'ad_{i+1:03d}',
                'headline': headline,
                'impressions': np.random.randint(5000, 20000),
                'clicks': np.random.randint(100, 800),
                'conversions': np.random.randint(10, 50),
                'ctr': np.random.uniform(2.0, 5.0),
                'conversion_rate': np.random.uniform(8.0, 25.0),
                'cost': np.random.uniform(50, 300)
            })
        
        # Ordenar por conversiones
        top_ads.sort(key=lambda x: x['conversions'], reverse=True)
        top_ads = top_ads[:3]  # Top 3
        
        # Crear contenido HTML
        content = """
        <div class="top-performing-ads">
            <h3>🏆 Top 3 Anuncios con Mejor Rendimiento</h3>
        """
        
        for i, ad in enumerate(top_ads, 1):
            content += f"""
            <div class="ad-card">
                <h4>#{i} - {ad['headline']}</h4>
                <div class="ad-metrics">
                    <span>📊 {ad['conversions']} conversiones</span>
                    <span>👆 CTR: {ad['ctr']:.2f}%</span>
                    <span>🎯 Conv. Rate: {ad['conversion_rate']:.2f}%</span>
                    <span>💰 Costo: ${ad['cost']:.2f}</span>
                </div>
            </div>
            """
        
        content += "</div>"
        
        return ReportSection(
            title="Anuncios Top",
            content=content,
            data_tables=[{'name': 'top_ads', 'data': top_ads}],
            insights=[
                f"El anuncio top generó {top_ads[0]['conversions']} conversiones",
                f"CTR promedio de top 3: {np.mean([ad['ctr'] for ad in top_ads]):.2f}%",
                "Anuncios esotéricos muestran alta tasa de conversión"
            ]
        )
    
    def _generate_recommendations_section(self, config: ReportConfig) -> ReportSection:
        """Generar sección de recomendaciones"""
        recommendations = [
            {
                'priority': 'Alta',
                'category': 'Optimización de CTR',
                'recommendation': 'Probar headlines más emocionales con urgencia temporal',
                'impact': 'Incremento estimado del 15-25% en CTR',
                'effort': 'Bajo'
            },
            {
                'priority': 'Alta',
                'category': 'Segmentación',
                'recommendation': 'Crear audiencias específicas por tipo de consulta esotérica',
                'impact': 'Mejora del 20-30% en tasa de conversión',
                'effort': 'Medio'
            },
            {
                'priority': 'Media',
                'category': 'Landing Pages',
                'recommendation': 'Optimizar formularios de contacto con menos campos',
                'impact': 'Reducción del 10-15% en CPA',
                'effort': 'Medio'
            },
            {
                'priority': 'Media',
                'category': 'Horarios',
                'recommendation': 'Ajustar horarios de publicación según picos de conversión',
                'impact': 'Optimización del 5-10% en costo',
                'effort': 'Bajo'
            }
        ]
        
        content = """
        <div class="recommendations">
            <h3>💡 Recomendaciones Estratégicas</h3>
            <p>Acciones prioritarias para optimizar el rendimiento de las campañas:</p>
        """
        
        for rec in recommendations:
            priority_class = rec['priority'].lower()
            content += f"""
            <div class="recommendation-card priority-{priority_class}">
                <div class="rec-header">
                    <span class="priority-badge">{rec['priority']}</span>
                    <h4>{rec['category']}</h4>
                </div>
                <p class="rec-description">{rec['recommendation']}</p>
                <div class="rec-details">
                    <span class="impact">📈 {rec['impact']}</span>
                    <span class="effort">⚡ Esfuerzo: {rec['effort']}</span>
                </div>
            </div>
            """
        
        content += "</div>"
        
        return ReportSection(
            title="Recomendaciones",
            content=content,
            recommendations=[rec['recommendation'] for rec in recommendations]
        )
    
    def _generate_campaign_overview_section(self, config: ReportConfig) -> ReportSection:
        """Generar sección de overview de campañas"""
        # Simular datos de campañas
        campaigns = [
            {
                'name': 'Amarres de Amor - México',
                'status': 'Activa',
                'budget': 500.0,
                'spent': 387.50,
                'impressions': 25000,
                'clicks': 750,
                'conversions': 45
            },
            {
                'name': 'Tarot Online - España',
                'status': 'Activa',
                'budget': 300.0,
                'spent': 245.80,
                'impressions': 18000,
                'clicks': 540,
                'conversions': 38
            }
        ]
        
        content = """
        <div class="campaign-overview">
            <h3>🎯 Resumen de Campañas</h3>
            <div class="campaigns-grid">
        """
        
        for campaign in campaigns:
            budget_usage = (campaign['spent'] / campaign['budget']) * 100
            ctr = (campaign['clicks'] / campaign['impressions']) * 100
            
            content += f"""
            <div class="campaign-card">
                <h4>{campaign['name']}</h4>
                <div class="campaign-status">{campaign['status']}</div>
                <div class="campaign-metrics">
                    <p>💰 Presupuesto: ${campaign['budget']:.2f} (Usado: {budget_usage:.1f}%)</p>
                    <p>👁️ Impresiones: {campaign['impressions']:,}</p>
                    <p>👆 CTR: {ctr:.2f}%</p>
                    <p>🎯 Conversiones: {campaign['conversions']}</p>
                </div>
            </div>
            """
        
        content += "</div></div>"
        
        return ReportSection(
            title="Resumen de Campañas",
            content=content,
            data_tables=[{'name': 'campaigns', 'data': campaigns}]
        )
    
    def _generate_ad_comparison_section(self, config: ReportConfig) -> ReportSection:
        """Generar sección de comparación de anuncios"""
        content = """
        <div class="ad-comparison">
            <h3>⚖️ Comparación de Anuncios</h3>
            <p>Análisis comparativo de rendimiento entre diferentes variaciones de anuncios.</p>
            
            <div class="comparison-insights">
                <h4>Insights Clave:</h4>
                <ul>
                    <li>Anuncios con testimonios tienen 23% más conversiones</li>
                    <li>Headlines con urgencia temporal mejoran CTR en 18%</li>
                    <li>Mencionar "gratis" en description aumenta clics en 15%</li>
                </ul>
            </div>
        </div>
        """
        
        return ReportSection(
            title="Comparación de Anuncios",
            content=content
        )
    
    def _generate_trend_overview_section(self, config: ReportConfig) -> ReportSection:
        """Generar sección de overview de tendencias"""
        content = """
        <div class="trend-overview">
            <h3>📈 Análisis de Tendencias</h3>
            <p>Identificación de patrones y tendencias en el rendimiento de campañas esotéricas.</p>
            
            <div class="trend-highlights">
                <h4>Tendencias Identificadas:</h4>
                <ul>
                    <li>📅 Picos de conversión los fines de semana (+35%)</li>
                    <li>🌙 Mayor actividad en horarios nocturnos (8PM-12AM)</li>
                    <li>📱 Dispositivos móviles representan 78% del tráfico</li>
                    <li>🎯 Audiencias femeninas 25-45 años más receptivas</li>
                </ul>
            </div>
        </div>
        """
        
        return ReportSection(
            title="Análisis de Tendencias",
            content=content
        )
    
    def _generate_generic_section(self, section_name: str, config: ReportConfig) -> ReportSection:
        """Generar sección genérica"""
        content = f"""
        <div class="generic-section">
            <h3>{section_name.replace('_', ' ').title()}</h3>
            <p>Sección en desarrollo para {section_name}</p>
        </div>
        """
        
        return ReportSection(
            title=section_name.replace('_', ' ').title(),
            content=content
        )
    
    def _generate_summary(self, sections: List[ReportSection], config: ReportConfig) -> Dict[str, Any]:
        """Generar resumen del reporte"""
        total_insights = sum(len(section.insights or []) for section in sections)
        total_recommendations = sum(len(section.recommendations or []) for section in sections)
        total_charts = sum(len(section.charts or []) for section in sections)
        
        return {
            'total_sections': len(sections),
            'total_insights': total_insights,
            'total_recommendations': total_recommendations,
            'total_charts': total_charts,
            'report_type': config.report_type.value,
            'format': config.format.value,
            'period_days': (config.date_range[1] - config.date_range[0]).days,
            'categories_analyzed': len(config.categories)
        }
    
    def _create_bar_chart(self, data: Dict[str, Any], title: str, 
                         x_axis: str, y_axis: str) -> Optional[str]:
        """Crear gráfico de barras"""
        if not PLOTTING_AVAILABLE:
            return None
        
        try:
            plt.figure(figsize=(10, 6))
            plt.bar(data[x_axis], data[y_axis], color=self.config['styling']['primary_color'])
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(x_axis.replace('_', ' ').title())
            plt.ylabel(y_axis.replace('_', ' ').title())
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico de barras: {e}")
            return None
    
    def _create_line_chart(self, data: Dict[str, Any], title: str, 
                          x_axis: str, y_axis: str) -> Optional[str]:
        """Crear gráfico de líneas"""
        if not PLOTTING_AVAILABLE:
            return None
        
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(data[x_axis], data[y_axis], 
                    color=self.config['styling']['primary_color'], 
                    linewidth=2, marker='o')
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(x_axis.replace('_', ' ').title())
            plt.ylabel(y_axis.replace('_', ' ').title())
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico de líneas: {e}")
            return None
    
    def _export_report(self, report: GeneratedReport, format: ReportFormat) -> str:
        """Exportar reporte en formato específico"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report.report_id}_{timestamp}"
        
        if format == ReportFormat.HTML:
            return self._export_html(report, filename)
        elif format == ReportFormat.JSON:
            return self._export_json(report, filename)
        elif format == ReportFormat.CSV:
            return self._export_csv(report, filename)
        else:
            logger.warning(f"Formato {format.value} no implementado, usando HTML")
            return self._export_html(report, filename)
    
    def _export_html(self, report: GeneratedReport, filename: str) -> str:
        """Exportar reporte como HTML"""
        file_path = self.output_dir / f"{filename}.html"
        
        # CSS básico
        css = """
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
            .header { background: linear-gradient(135deg, #2E86AB, #A23B72); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .section { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
            .metric-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2E86AB; }
            .metric-value { font-size: 24px; font-weight: bold; color: #2E86AB; margin: 10px 0; }
            .metrics-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            .metrics-table th, .metrics-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            .metrics-table th { background-color: #2E86AB; color: white; }
            .ad-card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #F18F01; }
            .ad-metrics span { display: inline-block; margin-right: 20px; padding: 5px 10px; background: white; border-radius: 4px; font-size: 12px; }
            .recommendation-card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .priority-alta { border-left: 4px solid #dc3545; }
            .priority-media { border-left: 4px solid #ffc107; }
            .priority-baja { border-left: 4px solid #28a745; }
            .priority-badge { background: #2E86AB; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
            .chart-container { text-align: center; margin: 20px 0; }
            .chart-container img { max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        </style>
        """
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{report.title}</title>
            {css}
        </head>
        <body>
            <div class="header">
                <h1>🔮 {report.title}</h1>
                <p>Generado el {report.generated_at.strftime('%d/%m/%Y a las %H:%M')}</p>
                <p>ID del Reporte: {report.report_id}</p>
            </div>
        """
        
        # Agregar secciones
        for section in report.sections:
            html_content += f'<div class="section">{section.content}'
            
            # Agregar gráficos
            if section.charts:
                for chart in section.charts:
                    html_content += f'<div class="chart-container"><img src="data:image/png;base64,{chart}" alt="Gráfico"></div>'
            
            html_content += '</div>'
        
        # Footer con resumen
        html_content += f"""
            <div class="section">
                <h3>📋 Resumen del Reporte</h3>
                <ul>
                    <li>Secciones: {report.summary['total_sections']}</li>
                    <li>Insights: {report.summary['total_insights']}</li>
                    <li>Recomendaciones: {report.summary['total_recommendations']}</li>
                    <li>Gráficos: {report.summary['total_charts']}</li>
                    <li>Período analizado: {report.summary['period_days']} días</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        # Guardar archivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)
    
    def _export_json(self, report: GeneratedReport, filename: str) -> str:
        """Exportar reporte como JSON"""
        file_path = self.output_dir / f"{filename}.json"
        
        # Convertir a diccionario serializable
        report_dict = {
            'report_id': report.report_id,
            'title': report.title,
            'generated_at': report.generated_at.isoformat(),
            'config': {
                'report_type': report.config.report_type.value,
                'format': report.config.format.value,
                'date_range': [
                    report.config.date_range[0].isoformat(),
                    report.config.date_range[1].isoformat()
                ],
                'categories': report.config.categories,
                'metrics': report.config.metrics
            },
            'sections': [asdict(section) for section in report.sections],
            'summary': report.summary
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        return str(file_path)
    
    def _export_csv(self, report: GeneratedReport, filename: str) -> str:
        """Exportar datos del reporte como CSV"""
        file_path = self.output_dir / f"{filename}.csv"
        
        # Recopilar todos los datos tabulares
        all_data = []
        
        for section in report.sections:
            if section.data_tables:
                for table in section.data_tables:
                    table_data = table['data']
                    if isinstance(table_data, list) and table_data:
                        df = pd.DataFrame(table_data)
                        df['section'] = section.title
                        df['table_name'] = table['name']
                        all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df.to_csv(file_path, index=False, encoding='utf-8')
        else:
            # Crear CSV básico con resumen
            summary_df = pd.DataFrame([report.summary])
            summary_df.to_csv(file_path, index=False, encoding='utf-8')
        
        return str(file_path)
    
    def get_available_templates(self) -> Dict[str, Any]:
        """Obtener templates disponibles"""
        return {
            report_type.value: {
                'title': template['title'],
                'sections': template['sections']
            }
            for report_type, template in self.report_templates.items()
        }
    
    def schedule_report(self, config: ReportConfig, 
                       schedule: str, email: Optional[str] = None) -> str:
        """
        Programar generación automática de reporte
        
        Args:
            config: Configuración del reporte
            schedule: Programación (daily, weekly, monthly)
            email: Email para envío automático
            
        Returns:
            ID de la programación
        """
        schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # En una implementación real, esto se guardaría en base de datos
        # y se configuraría un cron job o scheduler
        
        logger.info(f"Reporte programado: {schedule_id} - Frecuencia: {schedule}")
        
        return schedule_id

# Función de utilidad para crear servicio rápidamente
def create_reporting_service(config_path: Optional[str] = None, 
                           output_dir: Optional[str] = None) -> EsotericReportingService:
    """
    Crear servicio de reportes
    
    Args:
        config_path: Ruta al archivo de configuración
        output_dir: Directorio de salida
        
    Returns:
        Servicio de reportes
    """
    return EsotericReportingService(config_path, output_dir)

if __name__ == "__main__":
    # Ejemplo de uso
    service = EsotericReportingService()
    
    # Configurar reporte
    config = ReportConfig(
        report_type=ReportType.PERFORMANCE,
        format=ReportFormat.HTML,
        date_range=(datetime.now() - timedelta(days=30), datetime.now()),
        categories=['amarres_amor', 'tarot'],
        metrics=['impressions', 'clicks', 'conversions', 'ctr', 'conversion_rate'],
        include_charts=True,
        include_insights=True,
        include_recommendations=True
    )
    
    # Generar reporte
    report = service.generate_report(config)
    
    print("=" * 60)
    print("📊 REPORTE GENERADO")
    print("=" * 60)
    print(f"ID: {report.report_id}")
    print(f"Título: {report.title}")
    print(f"Formato: {report.config.format.value}")
    print(f"Secciones: {len(report.sections)}")
    print(f"Archivo: {report.file_path}")
    
    print(f"\n📋 RESUMEN:")
    for key, value in report.summary.items():
        print(f"- {key}: {value}")
    
    print(f"\n📑 SECCIONES:")
    for section in report.sections:
        print(f"- {section.title}")
        if section.insights:
            print(f"  Insights: {len(section.insights)}")
        if section.recommendations:
            print(f"  Recomendaciones: {len(section.recommendations)}")
    
    # Mostrar templates disponibles
    templates = service.get_available_templates()
    print(f"\n📋 TEMPLATES DISPONIBLES:")
    for template_type, template_info in templates.items():
        print(f"- {template_type}: {template_info['title']}")
        print(f"  Secciones: {', '.join(template_info['sections'])}")