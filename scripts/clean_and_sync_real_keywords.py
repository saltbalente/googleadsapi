#!/usr/bin/env python3
"""
Script para limpiar completamente los datos de prueba y sincronizar solo keywords reales
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from services.keyword_health_service import KeywordHealthService
from modules.google_ads_client import GoogleAdsClientWrapper
from services.report_service import ReportService
from utils.logger import get_logger

logger = get_logger(__name__)

class RealKeywordSyncer:
    """Sincronizador de keywords reales"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.ads_client = GoogleAdsClientWrapper()
        self.report_service = ReportService(self.ads_client)
        self.health_service = KeywordHealthService(
            db_service=self.db_service,
            ads_client=self.ads_client,
            report_service=self.report_service
        )
        logger.info("RealKeywordSyncer inicializado")
    
    def clean_and_sync_all(self) -> bool:
        """Limpiar todos los datos y sincronizar solo keywords reales"""
        try:
            logger.info("🧹 Iniciando limpieza completa y sincronización de keywords reales...")
            
            # 1. Limpiar TODOS los datos de keywords y health scores
            self._clean_all_keyword_data()
            
            # 2. Obtener cuentas activas
            accounts = self.db_service.get_all_accounts(active_only=True)
            
            if not accounts:
                logger.warning("No se encontraron cuentas activas")
                return False
            
            total_success = 0
            total_failed = 0
            
            # 3. Sincronizar solo keywords reales para cada cuenta
            for account in accounts:
                try:
                    logger.info(f"📊 Procesando cuenta {account.customer_id} - {account.account_name}")
                    
                    # Sincronizar keywords reales específicamente
                    success = self._sync_real_keywords_for_account(account.customer_id)
                    
                    if success:
                        total_success += 1
                        logger.info(f"✅ Cuenta {account.customer_id}: Keywords reales sincronizadas")
                    else:
                        total_failed += 1
                        logger.error(f"❌ Error procesando cuenta {account.customer_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando cuenta {account.customer_id}: {e}")
                    total_failed += 1
                    continue
            
            logger.info(f"🎉 Sincronización completada: {total_success} cuentas exitosas, {total_failed} fallidas")
            
            # 4. Verificar resultados
            if total_success > 0:
                self._verify_real_keywords()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error en limpieza y sincronización: {e}")
            return False
    
    def _clean_all_keyword_data(self):
        """Limpiar TODOS los datos de keywords y health scores"""
        try:
            logger.info("🗑️ Limpiando TODOS los datos de keywords y health scores...")
            
            # Eliminar todas las métricas de keywords
            deleted_metrics = self.db_service.delete_all_keyword_metrics()
            logger.info(f"🗑️ Eliminadas {deleted_metrics} métricas de keywords")
            
            # Eliminar todos los health scores
            deleted_scores = self.db_service.delete_all_health_scores()
            logger.info(f"🗑️ Eliminados {deleted_scores} health scores")
            
            logger.info("✅ Limpieza completa de datos completada")
            
        except Exception as e:
            logger.error(f"Error limpiando todos los datos: {e}")
    
    def _sync_real_keywords_for_account(self, customer_id: str) -> bool:
        """Sincronizar solo keywords reales para una cuenta específica"""
        try:
            # Obtener keywords reales directamente de Google Ads API
            real_keywords = self._get_real_keywords_from_api(customer_id)
            
            if not real_keywords:
                logger.warning(f"No se encontraron keywords reales para cuenta {customer_id}")
                return False
            
            # Crear métricas con datos reales
            keyword_metrics = []
            today = date.today()
            
            for keyword_data in real_keywords:
                from services.database_service import KeywordMetric
                
                metric = KeywordMetric(
                    customer_id=customer_id,
                    campaign_id=str(keyword_data['campaign_id']),
                    campaign_name=keyword_data['campaign_name'],
                    ad_group_id=str(keyword_data['ad_group_id']),
                    ad_group_name=keyword_data['ad_group_name'],
                    keyword_text=keyword_data['keyword_text'],
                    match_type=keyword_data['match_type'],
                    status=keyword_data['status'],
                    quality_score=None,
                    impressions=0,  # Inicializar con 0, se actualizará con métricas reales
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
            
            # Insertar en base de datos
            if keyword_metrics:
                success = self.db_service.bulk_insert_keyword_metrics(keyword_metrics)
                if success:
                    logger.info(f"Sincronizadas {len(keyword_metrics)} keywords reales para cuenta {customer_id}")
                    
                    # Calcular health scores para las keywords reales
                    health_scores = self.health_service.calculate_health_scores_for_account(customer_id, 30)
                    logger.info(f"Calculados {len(health_scores)} health scores para cuenta {customer_id}")
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sincronizando keywords reales para cuenta {customer_id}: {e}")
            return False
    
    def _get_real_keywords_from_api(self, customer_id: str) -> list:
        """Obtener keywords reales directamente de Google Ads API"""
        try:
            # Query para obtener solo keywords reales (sin datos de prueba)
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
                return []
            
            # Filtrar keywords de prueba conocidas
            test_keywords = {
                "zapatos deportivos", "ropa casual", "accesorios moda",
                "software empresarial", "herramientas productividad", "servicios cloud",
                "consultoría marketing", "diseño web", "desarrollo apps"
            }
            
            real_keywords = []
            for row in results:
                keyword_text = row.ad_group_criterion.keyword.text.lower()
                
                # Solo incluir keywords que NO sean de prueba
                if keyword_text not in test_keywords:
                    real_keywords.append({
                        'campaign_id': row.campaign.id,
                        'campaign_name': row.campaign.name,
                        'ad_group_id': row.ad_group.id,
                        'ad_group_name': row.ad_group.name,
                        'keyword_text': row.ad_group_criterion.keyword.text,
                        'match_type': row.ad_group_criterion.keyword.match_type.name,
                        'status': row.ad_group_criterion.status.name
                    })
            
            logger.info(f"Encontradas {len(real_keywords)} keywords reales (filtradas de {len(results)} totales) para cuenta {customer_id}")
            
            # Mostrar ejemplos de keywords reales encontradas
            if real_keywords:
                examples = [kw['keyword_text'] for kw in real_keywords[:5]]
                logger.info(f"Ejemplos de keywords reales: {examples}")
            
            return real_keywords
            
        except Exception as e:
            logger.error(f"Error obteniendo keywords reales de API: {e}")
            return []
    
    def _verify_real_keywords(self):
        """Verificar que ahora tenemos keywords reales"""
        try:
            logger.info("🔍 Verificando keywords reales sincronizadas...")
            
            accounts = self.db_service.get_all_accounts(active_only=True)
            
            for account in accounts:
                # Verificar métricas de keywords
                metrics = self.db_service.get_keyword_metrics(account.customer_id, days_back=7)
                
                if metrics:
                    # Mostrar keywords reales encontradas
                    real_keywords = [m.keyword_text for m in metrics[:5]]
                    logger.info(f"✅ Cuenta {account.customer_id}: {len(metrics)} keywords reales")
                    logger.info(f"   Keywords: {real_keywords}")
                else:
                    logger.warning(f"⚠️ Cuenta {account.customer_id}: No se encontraron keywords")
            
        except Exception as e:
            logger.error(f"Error verificando keywords reales: {e}")

def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando limpieza completa y sincronización de keywords reales")
        
        syncer = RealKeywordSyncer()
        
        # Limpiar y sincronizar keywords reales
        success = syncer.clean_and_sync_all()
        
        if success:
            logger.info("🎉 ¡Limpieza y sincronización completada exitosamente!")
            return True
        else:
            logger.error("❌ Error en la limpieza y sincronización")
            return False
            
    except Exception as e:
        logger.error(f"Error en main: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)