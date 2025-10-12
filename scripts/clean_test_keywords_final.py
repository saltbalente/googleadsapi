#!/usr/bin/env python3
"""
Script final para limpiar completamente los datos de prueba y sincronizar solo keywords reales
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

class FinalKeywordCleaner:
    """Limpiador final de datos de prueba de keywords"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.ads_client = GoogleAdsClientWrapper()
        self.report_service = ReportService(self.ads_client)
        self.health_service = KeywordHealthService(
            db_service=self.db_service,
            ads_client=self.ads_client,
            report_service=self.report_service
        )
        logger.info("FinalKeywordCleaner inicializado")

    def clean_all_test_data(self):
        """Limpiar completamente todos los datos de prueba"""
        try:
            logger.info("🧹 Iniciando limpieza completa de datos de prueba...")
            
            # Palabras clave de prueba conocidas
            test_keywords = {
                'zapatos deportivos', 'ropa casual', 'accesorios moda',
                'software empresarial', 'herramientas productividad', 'servicios cloud',
                'consultoría marketing', 'diseño web', 'desarrollo apps'
            }
            
            # Obtener todas las cuentas
            accounts = self.db_service.get_all_accounts(active_only=True)
            logger.info(f"Procesando {len(accounts)} cuentas...")
            
            total_deleted = 0
            
            for account in accounts:
                customer_id = account.customer_id
                logger.info(f"Limpiando datos de prueba para cuenta {customer_id}...")
                
                # Eliminar métricas de keywords de prueba
                deleted_metrics = self._delete_test_keyword_metrics(customer_id, test_keywords)
                
                # Eliminar health scores de keywords de prueba
                deleted_scores = self._delete_test_health_scores(customer_id, test_keywords)
                
                total_deleted += deleted_metrics + deleted_scores
                logger.info(f"  Eliminados {deleted_metrics} métricas y {deleted_scores} health scores")
            
            logger.info(f"✅ Limpieza completa: {total_deleted} registros eliminados")
            return True
            
        except Exception as e:
            logger.error(f"Error en limpieza completa: {e}")
            return False

    def _delete_test_keyword_metrics(self, customer_id: str, test_keywords: set) -> int:
        """Eliminar métricas de keywords de prueba"""
        try:
            # Obtener todas las métricas de la cuenta
            metrics = self.db_service.get_keyword_metrics(customer_id, days_back=365)
            
            deleted_count = 0
            for metric in metrics:
                if metric.keyword_text.lower() in test_keywords:
                    # Eliminar esta métrica
                    success = self.db_service.delete_keyword_metric(
                        customer_id, 
                        metric.keyword_text, 
                        metric.campaign_id, 
                        metric.date
                    )
                    if success:
                        deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error eliminando métricas de prueba: {e}")
            return 0

    def _delete_test_health_scores(self, customer_id: str, test_keywords: set) -> int:
        """Eliminar health scores de keywords de prueba"""
        try:
            # Obtener todos los health scores de la cuenta
            health_scores = self.db_service.get_health_scores(customer_id)
            
            deleted_count = 0
            for score in health_scores:
                if score.keyword_text.lower() in test_keywords:
                    # Eliminar este health score
                    success = self.db_service.delete_health_score(
                        customer_id,
                        score.keyword_text,
                        score.campaign_id
                    )
                    if success:
                        deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error eliminando health scores de prueba: {e}")
            return 0

    def sync_real_keywords_only(self):
        """Sincronizar solo keywords reales desde la API"""
        try:
            logger.info("🔄 Sincronizando solo keywords reales...")
            
            accounts = self.db_service.get_all_accounts(active_only=True)
            successful_accounts = 0
            
            for account in accounts:
                customer_id = account.customer_id
                logger.info(f"Sincronizando keywords reales para cuenta {customer_id}...")
                
                # Usar el método mejorado del KeywordHealthService
                success = self.health_service.sync_keyword_data_to_database(customer_id, days_back=30)
                
                if success:
                    successful_accounts += 1
                    logger.info(f"  ✅ Sincronización exitosa para {customer_id}")
                else:
                    logger.warning(f"  ❌ Falló sincronización para {customer_id}")
            
            logger.info(f"✅ Sincronización completa: {successful_accounts}/{len(accounts)} cuentas exitosas")
            return successful_accounts > 0
            
        except Exception as e:
            logger.error(f"Error sincronizando keywords reales: {e}")
            return False

    def calculate_health_scores(self):
        """Calcular health scores para las keywords reales"""
        try:
            logger.info("📊 Calculando health scores para keywords reales...")
            
            accounts = self.db_service.get_all_accounts(active_only=True)
            successful_accounts = 0
            
            for account in accounts:
                customer_id = account.customer_id
                logger.info(f"Calculando health scores para cuenta {customer_id}...")
                
                try:
                    # Calcular health scores
                    health_scores = self.health_service.calculate_health_scores_for_account(customer_id)
                    
                    if health_scores:
                        logger.info(f"  ✅ Calculados {len(health_scores)} health scores para {customer_id}")
                        successful_accounts += 1
                    else:
                        logger.warning(f"  ⚠️ No se calcularon health scores para {customer_id}")
                        
                except Exception as e:
                    logger.error(f"  ❌ Error calculando health scores para {customer_id}: {e}")
            
            logger.info(f"✅ Cálculo completo: {successful_accounts}/{len(accounts)} cuentas exitosas")
            return successful_accounts > 0
            
        except Exception as e:
            logger.error(f"Error calculando health scores: {e}")
            return False

    def run_complete_cleanup(self):
        """Ejecutar limpieza completa y sincronización"""
        try:
            logger.info("🚀 Iniciando proceso completo de limpieza y sincronización...")
            
            # Paso 1: Limpiar datos de prueba
            if not self.clean_all_test_data():
                logger.error("❌ Falló la limpieza de datos de prueba")
                return False
            
            # Paso 2: Sincronizar keywords reales
            if not self.sync_real_keywords_only():
                logger.error("❌ Falló la sincronización de keywords reales")
                return False
            
            # Paso 3: Calcular health scores
            if not self.calculate_health_scores():
                logger.error("❌ Falló el cálculo de health scores")
                return False
            
            logger.info("🎉 Proceso completo exitoso: datos de prueba eliminados y keywords reales sincronizadas")
            return True
            
        except Exception as e:
            logger.error(f"Error en proceso completo: {e}")
            return False

def main():
    """Función principal"""
    cleaner = FinalKeywordCleaner()
    
    try:
        success = cleaner.run_complete_cleanup()
        
        if success:
            logger.info("✅ Limpieza y sincronización completada exitosamente")
            print("✅ El dashboard ahora debería mostrar solo keywords reales")
            sys.exit(0)
        else:
            logger.error("❌ Falló el proceso de limpieza y sincronización")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()