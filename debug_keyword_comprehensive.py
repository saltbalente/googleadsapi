#!/usr/bin/env python3
"""
Script de diagnóstico completo para investigar por qué la consulta GAQL
de keywords retorna 0 filas y por qué la tabla no se renderiza.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from services.google_ads_service import GoogleAdsService
from modules.models import ReportConfig

def main():
    print("🔍 DIAGNÓSTICO COMPLETO - KEYWORD HEALTH")
    print("=" * 60)
    
    try:
        # Inicializar servicio
        ads_service = GoogleAdsService()
        print(f"✅ Servicio Google Ads inicializado correctamente")
        
        # Obtener customer IDs
        customer_ids = ads_service.get_customer_ids()
        print(f"✅ Customer IDs disponibles: {customer_ids}")
        
        # Usar el customer ID seleccionado (7094116152)
        selected_customer = "7094116152"
        print(f"🎯 Customer seleccionado: {selected_customer}")
        
        # Verificar fecha actual del sistema
        current_date = datetime.now().date()
        print(f"📅 Fecha actual del sistema: {current_date}")
        
        # Test 1: Verificar datos en un rango muy amplio (últimos 365 días)
        print("\n" + "="*50)
        print("TEST 1: Datos en rango amplio (últimos 365 días)")
        print("="*50)
        
        end_date_broad = current_date
        start_date_broad = end_date_broad - timedelta(days=365)
        
        query_broad = f"""
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
            metrics.clicks
        FROM keyword_view 
        WHERE segments.date BETWEEN '{start_date_broad}' AND '{end_date_broad}'
        AND campaign.status = 'ENABLED'
        AND ad_group_criterion.status = 'ENABLED'
        LIMIT 10
        """
        
        print(f"Consulta: {query_broad}")
        result_broad = ads_service.execute_query(selected_customer, query_broad)
        print(f"Resultado: {len(result_broad)} filas encontradas")
        
        if result_broad:
            print("Primeras 3 filas:")
            for i, row in enumerate(result_broad[:3]):
                print(f"  Fila {i+1}: {row}")
        
        # Test 2: Verificar datos sin filtro de estado
        print("\n" + "="*50)
        print("TEST 2: Datos sin filtros de estado (últimos 30 días)")
        print("="*50)
        
        end_date_30 = current_date
        start_date_30 = end_date_30 - timedelta(days=30)
        
        query_no_filter = f"""
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            ad_group.id,
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.status,
            segments.date,
            metrics.impressions
        FROM keyword_view 
        WHERE segments.date BETWEEN '{start_date_30}' AND '{end_date_30}'
        LIMIT 10
        """
        
        print(f"Consulta: {query_no_filter}")
        result_no_filter = ads_service.execute_query(selected_customer, query_no_filter)
        print(f"Resultado: {len(result_no_filter)} filas encontradas")
        
        if result_no_filter:
            print("Estados encontrados:")
            campaign_statuses = set()
            criterion_statuses = set()
            for row in result_no_filter:
                campaign_statuses.add(row.get('campaign.status'))
                criterion_statuses.add(row.get('ad_group_criterion.status'))
            print(f"  Estados de campaña: {campaign_statuses}")
            print(f"  Estados de criterio: {criterion_statuses}")
        
        # Test 3: Verificar la consulta exacta del dashboard
        print("\n" + "="*50)
        print("TEST 3: Consulta exacta del dashboard (2025-09-11 a 2025-10-11)")
        print("="*50)
        
        dashboard_query = """
        SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.status, ad_group_criterion.quality_info.quality_score, segments.date, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.conversions_value, metrics.ctr, metrics.average_cpc 
        FROM keyword_view 
        WHERE segments.date BETWEEN '2025-09-11' AND '2025-10-11' 
        AND campaign.status = 'ENABLED' 
        AND ad_group_criterion.status = 'ENABLED'
        """
        
        print(f"Consulta: {dashboard_query}")
        result_dashboard = ads_service.execute_query(selected_customer, dashboard_query)
        print(f"Resultado: {len(result_dashboard)} filas encontradas")
        
        # Test 4: Usar ReportConfig como en el dashboard
        print("\n" + "="*50)
        print("TEST 4: Usando ReportConfig como en el dashboard")
        print("="*50)
        
        from services.report_service import ReportService
        report_service = ReportService(ads_service)
        
        # Simular las fechas del dashboard
        start_date_str = "2025-09-11"
        end_date_str = "2025-10-11"
        
        kw_config = ReportConfig(
            report_name='Keyword Performance Report RT',
            metrics=[
                'metrics.impressions',
                'metrics.clicks',
                'metrics.cost_micros',
                'metrics.conversions',
                'metrics.conversions_value',
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
                'ad_group_criterion.quality_info.quality_score',
                'segments.date'
            ],
            date_range=f"'{start_date_str}' AND '{end_date_str}'",
            from_resource='keyword_view',
            filters={
                'campaign.status': 'ENABLED',
                'ad_group_criterion.status': 'ENABLED'
            }
        )
        
        print(f"GAQL generado: {kw_config.to_gaql_query()}")
        kw_report = report_service.generate_custom_report(kw_config)
        
        print(f"Resultado ReportService:")
        print(f"  Éxito: {kw_report.get('success')}")
        print(f"  Filas: {kw_report.get('total_rows')}")
        print(f"  Errores: {kw_report.get('errors')}")
        print(f"  Datos disponibles: {bool(kw_report.get('data'))}")
        
        # Test 5: Verificar datos con fechas actuales (últimos 7 días)
        print("\n" + "="*50)
        print("TEST 5: Datos con fechas recientes (últimos 7 días)")
        print("="*50)
        
        end_date_recent = current_date
        start_date_recent = end_date_recent - timedelta(days=7)
        
        kw_config_recent = ReportConfig(
            report_name='Keyword Performance Report Recent',
            metrics=[
                'metrics.impressions',
                'metrics.clicks'
            ],
            dimensions=[
                'campaign.name',
                'ad_group_criterion.keyword.text',
                'segments.date'
            ],
            date_range=f"'{start_date_recent}' AND '{end_date_recent}'",
            from_resource='keyword_view',
            filters={
                'campaign.status': 'ENABLED',
                'ad_group_criterion.status': 'ENABLED'
            }
        )
        
        print(f"GAQL reciente: {kw_config_recent.to_gaql_query()}")
        kw_report_recent = report_service.generate_custom_report(kw_config_recent)
        
        print(f"Resultado fechas recientes:")
        print(f"  Éxito: {kw_report_recent.get('success')}")
        print(f"  Filas: {kw_report_recent.get('total_rows')}")
        print(f"  Errores: {kw_report_recent.get('errors')}")
        
        if kw_report_recent.get('data'):
            print("Primeras 3 filas de datos recientes:")
            for i, row in enumerate(kw_report_recent['data'][:3]):
                print(f"  Fila {i+1}: {row}")
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DEL DIAGNÓSTICO")
        print("="*60)
        print(f"1. Rango amplio (365 días): {len(result_broad)} filas")
        print(f"2. Sin filtros (30 días): {len(result_no_filter)} filas")
        print(f"3. Consulta dashboard exacta: {len(result_dashboard)} filas")
        print(f"4. ReportConfig dashboard: {kw_report.get('total_rows', 0)} filas")
        print(f"5. Fechas recientes (7 días): {kw_report_recent.get('total_rows', 0)} filas")
        
        if len(result_broad) == 0:
            print("\n❌ PROBLEMA CRÍTICO: No hay datos de keywords en absoluto")
            print("   Posibles causas:")
            print("   - La cuenta no tiene keywords configuradas")
            print("   - La cuenta no tiene historial de datos")
            print("   - Problema de permisos en la cuenta")
        elif kw_report.get('total_rows', 0) == 0:
            print("\n⚠️  PROBLEMA ESPECÍFICO: Hay datos pero no en el rango 2025-09-11 a 2025-10-11")
            print("   Posibles causas:")
            print("   - El rango de fechas no tiene actividad")
            print("   - Los filtros son demasiado restrictivos")
            print("   - Problema en el procesamiento de ReportService")
        else:
            print("\n✅ Los datos están disponibles, el problema puede ser en la renderización")
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()