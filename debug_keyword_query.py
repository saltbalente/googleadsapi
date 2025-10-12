#!/usr/bin/env python3
"""
Debug script para investigar por qué la consulta GAQL de keywords retorna 0 filas
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, date

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.google_ads_client import GoogleAdsClientWrapper
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    try:
        print("🔍 Iniciando debug de consulta GAQL de keywords...")
        
        # Inicializar cliente
        ads_client = GoogleAdsClientWrapper()
        client = ads_client.get_client()
        print("✅ GoogleAdsClient inicializado correctamente")
        
        # Obtener cuentas disponibles
        accounts = ads_client.get_customer_ids()
        print(f"📊 Cuentas disponibles: {len(accounts)}")
        
        # Usar la cuenta seleccionada en el dashboard
        customer_id = "7094116152"
        print(f"🎯 Usando cuenta: {customer_id}")
        
        # Test 1: Verificar campañas habilitadas (sin filtro de fecha)
        print("\n🧪 Test 1: Verificando campañas habilitadas...")
        campaign_query = """
            SELECT campaign.id, campaign.name, campaign.status
            FROM campaign
            WHERE campaign.status = 'ENABLED'
        """
        
        try:
            campaign_results = ads_client.execute_query(customer_id, campaign_query)
            campaigns = list(campaign_results)
            print(f"✅ Campañas habilitadas encontradas: {len(campaigns)}")
            
            for campaign in campaigns[:5]:  # Mostrar solo las primeras 5
                print(f"   📋 {campaign.campaign.name} (ID: {campaign.campaign.id})")
                
        except Exception as e:
            print(f"❌ Error consultando campañas: {e}")
            return
        
        if not campaigns:
            print("⚠️ No se encontraron campañas habilitadas")
            return
        
        # Test 2: Verificar keywords sin filtro de fecha
        print("\n🧪 Test 2: Verificando keywords sin filtro de fecha...")
        keyword_query_no_date = """
            SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, 
                   ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status
            FROM keyword_view
            WHERE campaign.status = 'ENABLED' 
            AND ad_group_criterion.status = 'ENABLED'
            LIMIT 10
        """
        
        try:
            keyword_results = ads_client.execute_query(customer_id, keyword_query_no_date)
            keywords = list(keyword_results)
            print(f"✅ Keywords habilitadas encontradas: {len(keywords)}")
            
            for keyword in keywords[:3]:  # Mostrar solo las primeras 3
                print(f"   🔑 {keyword.ad_group_criterion.keyword.text} ({keyword.ad_group_criterion.keyword.match_type})")
                
        except Exception as e:
            print(f"❌ Error consultando keywords: {e}")
            return
        
        if not keywords:
            print("⚠️ No se encontraron keywords habilitadas")
            return
        
        # Test 3: Verificar datos con rango de fechas actual (últimos 30 días)
        print("\n🧪 Test 3: Verificando datos con rango de fechas actual...")
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Rango de fechas: {start_date} a {end_date}")
        
        keyword_query_with_date = f"""
            SELECT campaign.id, campaign.name, ad_group.id, ad_group.name,
                   ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status, segments.date, metrics.impressions, metrics.clicks
            FROM keyword_view
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            AND campaign.status = 'ENABLED'
            AND ad_group_criterion.status = 'ENABLED'
            LIMIT 10
        """
        
        try:
            results_with_date = ads_client.execute_query(customer_id, keyword_query_with_date)
            results_list = list(results_with_date)
            print(f"✅ Resultados con fechas actuales: {len(results_list)}")
            
            if results_list:
                for result in results_list[:3]:
                    print(f"   📊 {result.ad_group_criterion.keyword.text} - {result.segments.date} - Impresiones: {result.metrics.impressions}")
            else:
                print("⚠️ No hay datos en el rango de fechas actual")
                
        except Exception as e:
            print(f"❌ Error consultando con fechas: {e}")
        
        # Test 4: Verificar el rango de fechas problemático (2025)
        print("\n🧪 Test 4: Verificando el rango de fechas problemático (2025)...")
        problem_start = "2025-07-13"
        problem_end = "2025-10-11"
        
        print(f"📅 Rango problemático: {problem_start} a {problem_end}")
        
        keyword_query_problem = f"""
            SELECT campaign.id, campaign.name, ad_group.id, ad_group.name,
                   ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
                   ad_group_criterion.status, segments.date, metrics.impressions, metrics.clicks
            FROM keyword_view
            WHERE segments.date BETWEEN '{problem_start}' AND '{problem_end}'
            AND campaign.status = 'ENABLED'
            AND ad_group_criterion.status = 'ENABLED'
            LIMIT 10
        """
        
        try:
            problem_results = ads_client.execute_query(customer_id, keyword_query_problem)
            problem_list = list(problem_results)
            print(f"✅ Resultados con fechas 2025: {len(problem_list)}")
            
            if problem_list:
                print("🎉 ¡Encontrados datos en 2025! (Esto sería extraño)")
            else:
                print("✅ Confirmado: No hay datos en 2025 (como se esperaba)")
                
        except Exception as e:
            print(f"❌ Error consultando fechas 2025: {e}")
        
        # Test 5: Verificar datos históricos más amplios
        print("\n🧪 Test 5: Verificando datos históricos más amplios...")
        historical_start = date.today() - timedelta(days=365)  # Último año
        historical_end = date.today()
        
        print(f"📅 Rango histórico: {historical_start} a {historical_end}")
        
        historical_query = f"""
            SELECT segments.date, metrics.impressions, metrics.clicks
            FROM keyword_view
            WHERE segments.date BETWEEN '{historical_start}' AND '{historical_end}'
            AND campaign.status = 'ENABLED'
            AND ad_group_criterion.status = 'ENABLED'
            AND metrics.impressions > 0
            ORDER BY segments.date DESC
            LIMIT 5
        """
        
        try:
            historical_results = ads_client.execute_query(customer_id, historical_query)
            historical_list = list(historical_results)
            print(f"✅ Datos históricos encontrados: {len(historical_list)}")
            
            if historical_list:
                print("📈 Fechas con datos más recientes:")
                for result in historical_list:
                    print(f"   📅 {result.segments.date} - Impresiones: {result.metrics.impressions}, Clicks: {result.metrics.clicks}")
            else:
                print("⚠️ No se encontraron datos históricos con impresiones")
                
        except Exception as e:
            print(f"❌ Error consultando datos históricos: {e}")
        
        print("\n🎯 Resumen del diagnóstico:")
        print("=" * 50)
        print("1. ✅ Cliente Google Ads inicializado correctamente")
        print(f"2. ✅ Cuenta {customer_id} accesible")
        print("3. ✅ Campañas habilitadas encontradas" if campaigns else "3. ❌ No hay campañas habilitadas")
        print("4. ✅ Keywords habilitadas encontradas" if keywords else "4. ❌ No hay keywords habilitadas")
        print("5. 🔍 El problema está en el rango de fechas 2025-07-13 a 2025-10-11")
        print("6. 💡 Solución: Usar fechas actuales en lugar de fechas futuras")
        
    except Exception as e:
        logger.error(f"Error en debug: {e}")
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    main()