#!/usr/bin/env python3
"""
Script para investigar por qué los health scores aparecen como 0 o None
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService
from services.keyword_health_service import KeywordHealthService
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Investigar health scores problemáticos"""
    try:
        print("🔍 Investigando health scores problemáticos...")
        
        # Inicializar servicios
        db_service = DatabaseService()
        health_service = KeywordHealthService(db_service=db_service)
        
        # 1. Verificar datos en keyword_health_scores
        print("\n📊 1. Verificando datos en keyword_health_scores...")
        
        # Obtener cuentas activas
        accounts = db_service.get_all_accounts(active_only=True)
        print(f"Cuentas activas encontradas: {len(accounts)}")
        
        for account in accounts[:5]:  # Revisar primeras 5 cuentas
            customer_id = account.customer_id
            print(f"\n--- Cuenta: {customer_id} ({account.account_name}) ---")
            
            # Obtener health scores
            health_scores = db_service.get_latest_health_scores(customer_id, limit=10)
            print(f"Health scores encontrados: {len(health_scores)}")
            
            if health_scores:
                # Analizar valores
                zero_scores = [hs for hs in health_scores if hs.health_score == 0]
                none_scores = [hs for hs in health_scores if hs.health_score is None]
                valid_scores = [hs for hs in health_scores if hs.health_score and hs.health_score > 0]
                
                print(f"  - Health scores = 0: {len(zero_scores)}")
                print(f"  - Health scores = None: {len(none_scores)}")
                print(f"  - Health scores válidos: {len(valid_scores)}")
                
                # Mostrar ejemplos de cada tipo
                if zero_scores:
                    example = zero_scores[0]
                    print(f"  - Ejemplo score=0: {example.keyword_text} | conv_rate_score: {example.conv_rate_score} | cpa_score: {example.cpa_score} | ctr_score: {example.ctr_score}")
                
                if none_scores:
                    example = none_scores[0]
                    print(f"  - Ejemplo score=None: {example.keyword_text} | health_score: {example.health_score}")
                
                if valid_scores:
                    example = valid_scores[0]
                    print(f"  - Ejemplo válido: {example.keyword_text} | health_score: {example.health_score}")
            
            # 2. Verificar métricas base
            print(f"\n📈 2. Verificando métricas base para {customer_id}...")
            metrics = db_service.get_keyword_metrics(customer_id, days_back=30)
            print(f"Métricas encontradas: {len(metrics)}")
            
            if metrics:
                # Analizar métricas problemáticas
                zero_conversions = [m for m in metrics if m.conversions == 0]
                zero_clicks = [m for m in metrics if m.clicks == 0]
                zero_cost = [m for m in metrics if m.cost_micros == 0]
                
                print(f"  - Métricas con 0 conversiones: {len(zero_conversions)}")
                print(f"  - Métricas con 0 clicks: {len(zero_clicks)}")
                print(f"  - Métricas con 0 costo: {len(zero_cost)}")
                
                # Mostrar ejemplo de métrica
                if metrics:
                    example = metrics[0]
                    print(f"  - Ejemplo métrica: {example.keyword_text}")
                    print(f"    * Clicks: {example.clicks}")
                    print(f"    * Conversiones: {example.conversions}")
                    print(f"    * Costo: {example.cost_micros}")
                    print(f"    * CTR: {example.ctr}")
                    print(f"    * Quality Score: {example.quality_score}")
            
            # 3. Verificar benchmarks
            print(f"\n🎯 3. Verificando benchmarks para {customer_id}...")
            benchmarks = db_service.get_account_benchmarks(customer_id)
            if benchmarks:
                print(f"  - Target conv rate: {benchmarks.target_conv_rate}")
                print(f"  - Target CPA: {benchmarks.target_cpa}")
                print(f"  - Benchmark CTR: {benchmarks.benchmark_ctr}")
                print(f"  - Min quality score: {benchmarks.min_quality_score}")
            else:
                print("  - ❌ No se encontraron benchmarks")
        
        # 4. Probar cálculo manual
        print(f"\n🧮 4. Probando cálculo manual...")
        if accounts:
            test_customer = accounts[0].customer_id
            print(f"Probando cálculo para cuenta: {test_customer}")
            
            try:
                calculated_scores = health_service.calculate_health_scores_for_account(test_customer, days_back=30)
                print(f"Health scores calculados: {len(calculated_scores)}")
                
                if calculated_scores:
                    # Analizar resultados del cálculo
                    calc_zero = [hs for hs in calculated_scores if hs.health_score == 0]
                    calc_none = [hs for hs in calculated_scores if hs.health_score is None]
                    calc_valid = [hs for hs in calculated_scores if hs.health_score and hs.health_score > 0]
                    
                    print(f"  - Calculados con score=0: {len(calc_zero)}")
                    print(f"  - Calculados con score=None: {len(calc_none)}")
                    print(f"  - Calculados válidos: {len(calc_valid)}")
                    
                    # Mostrar ejemplo de cálculo problemático
                    if calc_zero:
                        example = calc_zero[0]
                        print(f"  - Ejemplo calculado=0:")
                        print(f"    * Keyword: {example.keyword_text}")
                        print(f"    * Health score: {example.health_score}")
                        print(f"    * Conv rate score: {example.conv_rate_score}")
                        print(f"    * CPA score: {example.cpa_score}")
                        print(f"    * CTR score: {example.ctr_score}")
                        print(f"    * Confidence: {example.confidence_score}")
                
            except Exception as e:
                print(f"❌ Error en cálculo manual: {e}")
        
        print("\n✅ Investigación completada")
        
    except Exception as e:
        print(f"❌ Error en investigación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()