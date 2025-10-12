#!/usr/bin/env python3
"""
Script para depurar por qué no se obtienen datos de keywords reales
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from modules.google_ads_client import GoogleAdsClientWrapper
from services.report_service import ReportService
from modules.models import ReportConfig
from utils.logger import get_logger

logger = get_logger(__name__)

class KeywordDataDebugger:
    """Depurador de datos de keywords"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.ads_client = GoogleAdsClientWrapper()
        self.report_service = ReportService(self.ads_client)
        logger.info("KeywordDataDebugger inicializado")
    
    def debug_all_accounts(self):
        """Depurar todas las cuentas para encontrar datos de keywords"""
        try:
            logger.info("🔍 Iniciando depuración de datos de keywords...")
            
            # Obtener todas las cuentas activas
            accounts = self.db_service.get_all_accounts(active_only=True)
            
            if not accounts:
                logger.warning("No se encontraron cuentas activas")
                return
            
            for account in accounts:
                logger.info(f"\n📊 Depurando cuenta {account.customer_id} - {account.account_name}")
                self._debug_account(account.customer_id)
                
        except Exception as e:
            logger.error(f"Error en depuración: {e}")
    
    def _debug_account(self, customer_id: str):
        """Depurar una cuenta específica"""
        try:
            # 1. Verificar si hay campañas activas
            self._check_campaigns(customer_id)
            
            # 2. Verificar si hay ad groups activos
            self._check_ad_groups(customer_id)
            
            # 3. Verificar si hay keywords
            self._check_keywords(customer_id)
            
            # 4. Probar diferentes queries de keywords
            self._test_keyword_queries(customer_id)
            
        except Exception as e:
            logger.error(f"Error depurando cuenta {customer_id}: {e}")
    
    def _check_campaigns(self, customer_id: str):
        """Verificar campañas activas"""
        try:
            query = """
                SELECT 
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign.advertising_channel_type
                FROM campaign 
                WHERE campaign.status = 'ENABLED'
                LIMIT 10
            """
            
            results = self.ads_client.execute_query(customer_id, query)
            
            if results:
                logger.info(f"✅ Encontradas {len(results)} campañas activas:")
                for i, row in enumerate(results[:3]):  # Mostrar solo las primeras 3
                    logger.info(f"   - {row.campaign.name} (ID: {row.campaign.id})")
            else:
                logger.warning("❌ No se encontraron campañas activas")
                
        except Exception as e:
            logger.error(f"Error verificando campañas: {e}")
    
    def _check_ad_groups(self, customer_id: str):
        """Verificar ad groups activos"""
        try:
            query = """
                SELECT 
                    ad_group.id,
                    ad_group.name,
                    ad_group.status,
                    campaign.name
                FROM ad_group 
                WHERE ad_group.status = 'ENABLED'
                    AND campaign.status = 'ENABLED'
                LIMIT 10
            """
            
            results = self.ads_client.execute_query(customer_id, query)
            
            if results:
                logger.info(f"✅ Encontrados {len(results)} ad groups activos:")
                for i, row in enumerate(results[:3]):  # Mostrar solo los primeros 3
                    logger.info(f"   - {row.ad_group.name} (ID: {row.ad_group.id}) en {row.campaign.name}")
            else:
                logger.warning("❌ No se encontraron ad groups activos")
                
        except Exception as e:
            logger.error(f"Error verificando ad groups: {e}")
    
    def _check_keywords(self, customer_id: str):
        """Verificar keywords activas"""
        try:
            query = """
                SELECT 
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status,
                    ad_group.name,
                    campaign.name
                FROM ad_group_criterion 
                WHERE ad_group_criterion.type = 'KEYWORD'
                    AND ad_group_criterion.status = 'ENABLED'
                    AND ad_group.status = 'ENABLED'
                    AND campaign.status = 'ENABLED'
                LIMIT 10
            """
            
            results = self.ads_client.execute_query(customer_id, query)
            
            if results:
                logger.info(f"✅ Encontradas {len(results)} keywords activas:")
                for i, row in enumerate(results[:5]):  # Mostrar solo las primeras 5
                    logger.info(f"   - '{row.ad_group_criterion.keyword.text}' ({row.ad_group_criterion.keyword.match_type}) en {row.ad_group.name}")
            else:
                logger.warning("❌ No se encontraron keywords activas")
                
        except Exception as e:
            logger.error(f"Error verificando keywords: {e}")
    
    def _test_keyword_queries(self, customer_id: str):
        """Probar diferentes queries de keywords con métricas"""
        try:
            # Query 1: Keyword view con métricas de los últimos 30 días
            logger.info("🧪 Probando query 1: keyword_view con métricas...")
            query1 = """
                SELECT 
                    ad_group_criterion.keyword.text,
                    campaign.name,
                    ad_group.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros
                FROM keyword_view 
                WHERE segments.date DURING LAST_30_DAYS
                    AND ad_group_criterion.status = 'ENABLED'
                    AND campaign.status = 'ENABLED'
                LIMIT 5
            """
            
            results1 = self.ads_client.execute_query(customer_id, query1)
            if results1:
                logger.info(f"✅ Query 1: {len(results1)} resultados con métricas")
                for row in results1[:2]:
                    logger.info(f"   - '{row.ad_group_criterion.keyword.text}': {row.metrics.impressions} impresiones, {row.metrics.clicks} clics")
            else:
                logger.warning("❌ Query 1: Sin resultados con métricas")
            
            # Query 2: Keyword view sin filtro de fecha
            logger.info("🧪 Probando query 2: keyword_view sin filtro de fecha...")
            query2 = """
                SELECT 
                    ad_group_criterion.keyword.text,
                    campaign.name,
                    ad_group.name
                FROM keyword_view 
                WHERE ad_group_criterion.status = 'ENABLED'
                    AND campaign.status = 'ENABLED'
                LIMIT 5
            """
            
            results2 = self.ads_client.execute_query(customer_id, query2)
            if results2:
                logger.info(f"✅ Query 2: {len(results2)} keywords sin métricas")
                for row in results2[:2]:
                    logger.info(f"   - '{row.ad_group_criterion.keyword.text}' en {row.campaign.name}")
            else:
                logger.warning("❌ Query 2: Sin keywords encontradas")
            
            # Query 3: Usar ReportService como en campaigns
            logger.info("🧪 Probando query 3: ReportService como en campaigns...")
            try:
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                
                report_config = ReportConfig(
                    report_name='Debug Keyword Report',
                    customer_ids=[customer_id],
                    metrics=[
                        'metrics.impressions',
                        'metrics.clicks',
                        'metrics.cost_micros'
                    ],
                    dimensions=[
                        'campaign.name',
                        'ad_group.name',
                        'ad_group_criterion.keyword.text',
                        'ad_group_criterion.keyword.match_type'
                    ],
                    date_range=f"{start_date.strftime('%Y-%m-%d')} AND {end_date.strftime('%Y-%m-%d')}",
                    from_resource='keyword_view'
                )
                
                report_result = self.report_service.generate_custom_report(report_config)
                
                if report_result.get('success') and report_result.get('data'):
                    data = report_result.get('data', [])
                    logger.info(f"✅ Query 3 (ReportService): {len(data)} resultados")
                    for i, row in enumerate(data[:2]):
                        keyword = row.get('ad_group_criterion.keyword.text', 'N/A')
                        impressions = row.get('metrics.impressions', 0)
                        logger.info(f"   - '{keyword}': {impressions} impresiones")
                else:
                    logger.warning(f"❌ Query 3 (ReportService): {report_result.get('error', 'Sin datos')}")
                    
            except Exception as e:
                logger.error(f"Error en query 3: {e}")
                
        except Exception as e:
            logger.error(f"Error probando queries: {e}")

def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando depuración de datos de keywords")
        
        debugger = KeywordDataDebugger()
        debugger.debug_all_accounts()
        
        logger.info("🎉 Depuración completada")
        return True
        
    except Exception as e:
        logger.error(f"Error en main: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)