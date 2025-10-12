#!/usr/bin/env python3
"""
Script para analizar los valores específicos de health scores y identificar por qué aparecen como 0 o None
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService
from services.keyword_health_service import KeywordHealthService
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Analizar valores específicos de health scores"""
    try:
        print("🔍 Analizando valores específicos de health scores...")
        
        # Inicializar servicios
        db_service = DatabaseService()
        
        # Usar cuentas que sabemos tienen datos
        test_accounts = ['1803044752', '9759913462', '1919262845', '7004285893']
        
        for customer_id in test_accounts:
            print(f"\n📊 Analizando cuenta: {customer_id}")
            
            # Obtener health scores
            health_scores = db_service.get_latest_health_scores(customer_id, limit=50)
            print(f"Health scores encontrados: {len(health_scores)}")
            
            if not health_scores:
                continue
            
            # Analizar distribución de valores
            values = [hs.health_score for hs in health_scores if hs.health_score is not None]
            zero_values = [hs for hs in health_scores if hs.health_score == 0]
            none_values = [hs for hs in health_scores if hs.health_score is None]
            positive_values = [hs for hs in health_scores if hs.health_score and hs.health_score > 0]
            
            print(f"  📈 Distribución de valores:")
            print(f"    - Health scores = 0: {len(zero_values)}")
            print(f"    - Health scores = None: {len(none_values)}")
            print(f"    - Health scores > 0: {len(positive_values)}")
            
            if values:
                print(f"    - Valor mínimo: {min(values):.3f}")
                print(f"    - Valor máximo: {max(values):.3f}")
                print(f"    - Valor promedio: {sum(values)/len(values):.3f}")
            
            # Analizar ejemplos de cada tipo
            print(f"\n  🔍 Análisis detallado:")
            
            # Ejemplo de health score = 0
            if zero_values:
                example = zero_values[0]
                print(f"    📉 Ejemplo health_score = 0:")
                print(f"      - Keyword: {example.keyword_text}")
                print(f"      - Health score: {example.health_score}")
                print(f"      - Conv rate score: {example.conv_rate_score}")
                print(f"      - CPA score: {example.cpa_score}")
                print(f"      - CTR score: {example.ctr_score}")
                print(f"      - Quality score points: {example.quality_score_points}")
                print(f"      - Confidence score: {example.confidence_score}")
                print(f"      - Total spend: {example.total_spend}")
                print(f"      - Total conversions: {example.total_conversions}")
                print(f"      - Total clicks: {example.total_clicks}")
                
                # Calcular manualmente el health score
                if all(x is not None for x in [example.conv_rate_score, example.cpa_score, example.ctr_score, example.quality_score_points, example.confidence_score]):
                    manual_calc = (
                        example.conv_rate_score * 0.3 +  # conv_rate_weight
                        example.cpa_score * 0.25 +       # cpa_weight
                        example.ctr_score * 0.2 +        # ctr_weight
                        0 * 0.15 +                       # volume_score (calculado aparte)
                        example.quality_score_points * 0.1  # quality_score_weight
                    ) * example.confidence_score
                    print(f"      - Cálculo manual (sin volume): {manual_calc:.3f}")
            
            # Ejemplo de health score = None
            if none_values:
                example = none_values[0]
                print(f"    ❓ Ejemplo health_score = None:")
                print(f"      - Keyword: {example.keyword_text}")
                print(f"      - Health score: {example.health_score}")
                print(f"      - Conv rate score: {example.conv_rate_score}")
                print(f"      - CPA score: {example.cpa_score}")
                print(f"      - CTR score: {example.ctr_score}")
                print(f"      - Quality score points: {example.quality_score_points}")
                print(f"      - Confidence score: {example.confidence_score}")
            
            # Ejemplo de health score válido
            if positive_values:
                example = positive_values[0]
                print(f"    ✅ Ejemplo health_score válido:")
                print(f"      - Keyword: {example.keyword_text}")
                print(f"      - Health score: {example.health_score}")
                print(f"      - Conv rate score: {example.conv_rate_score}")
                print(f"      - CPA score: {example.cpa_score}")
                print(f"      - CTR score: {example.ctr_score}")
                print(f"      - Quality score points: {example.quality_score_points}")
                print(f"      - Confidence score: {example.confidence_score}")
                print(f"      - Total spend: {example.total_spend}")
                print(f"      - Total conversions: {example.total_conversions}")
                print(f"      - Total clicks: {example.total_clicks}")
            
            # Verificar métricas originales para entender el problema
            print(f"\n  📊 Verificando métricas originales:")
            metrics = db_service.get_keyword_metrics(customer_id, days_back=30)
            if metrics:
                # Buscar métricas para keywords problemáticas
                if zero_values:
                    problem_keyword = zero_values[0].keyword_text
                    matching_metrics = [m for m in metrics if m.keyword_text == problem_keyword]
                    if matching_metrics:
                        metric = matching_metrics[0]
                        print(f"    📈 Métricas para '{problem_keyword}':")
                        print(f"      - Clicks: {metric.clicks}")
                        print(f"      - Conversiones: {metric.conversions}")
                        print(f"      - Costo (micros): {metric.cost_micros}")
                        print(f"      - CTR: {metric.ctr}")
                        print(f"      - Average CPC (micros): {metric.average_cpc}")
                        print(f"      - Quality Score: {metric.quality_score}")
                        
                        # Calcular métricas derivadas
                        conv_rate = metric.conversions / metric.clicks if metric.clicks > 0 else 0
                        cpa = (metric.cost_micros / 1_000_000) / metric.conversions if metric.conversions > 0 else float('inf')
                        print(f"      - Conv rate calculada: {conv_rate:.4f}")
                        print(f"      - CPA calculado: {cpa:.2f}")
            
            print(f"\n" + "="*50)
        
        print("\n✅ Análisis completado")
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()