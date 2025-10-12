#!/usr/bin/env python3
"""
Script para reemplazar datos de prueba con datos reales de Google Ads API
"""

import os
import sys
import logging
from datetime import datetime, date

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from services.keyword_health_service import KeywordHealthService
from modules.google_ads_client import GoogleAdsClientWrapper
from services.report_service import ReportService
from utils.logger import get_logger

logger = get_logger(__name__)

class RealDataReplacer:
    """Reemplazador de datos de prueba con datos reales"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.ads_client = GoogleAdsClientWrapper()
        self.report_service = ReportService(self.ads_client)
        self.health_service = KeywordHealthService(
            db_service=self.db_service,
            ads_client=self.ads_client,
            report_service=self.report_service
        )
        logger.info("RealDataReplacer inicializado")
    
    def replace_all_test_data(self, days_back: int = 30) -> bool:
        """Reemplazar todos los datos de prueba con datos reales"""
        try:
            logger.info("🧹 Iniciando reemplazo de datos de prueba con datos reales...")
            
            # 1. Limpiar datos de prueba existentes
            self._clean_test_data()
            
            # 2. Obtener todas las cuentas activas
            accounts = self.db_service.get_all_accounts(active_only=True)
            
            if not accounts:
                logger.warning("No se encontraron cuentas activas")
                return False
            
            total_success = 0
            total_failed = 0
            
            # 3. Procesar cada cuenta
            for account in accounts:
                try:
                    logger.info(f"📊 Procesando cuenta {account.customer_id} - {account.account_name}")
                    
                    # Sincronizar datos reales de keywords
                    success = self.health_service.sync_keyword_data_to_database(
                        account.customer_id, 
                        days_back
                    )
                    
                    if success:
                        # Calcular health scores basados en datos reales
                        health_scores = self.health_service.calculate_health_scores_for_account(
                            account.customer_id,
                            days_back
                        )
                        
                        logger.info(f"✅ Cuenta {account.customer_id}: {len(health_scores)} health scores calculados")
                        total_success += 1
                    else:
                        logger.error(f"❌ Error procesando cuenta {account.customer_id}")
                        total_failed += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando cuenta {account.customer_id}: {e}")
                    total_failed += 1
                    continue
            
            logger.info(f"🎉 Reemplazo completado: {total_success} cuentas exitosas, {total_failed} fallidas")
            return total_success > 0
            
        except Exception as e:
            logger.error(f"Error en reemplazo de datos: {e}")
            return False
    
    def _clean_test_data(self):
        """Limpiar datos de prueba genéricos"""
        try:
            logger.info("🧹 Limpiando datos de prueba genéricos...")
            
            # Keywords de prueba conocidas que deben eliminarse
            test_keywords = [
                "zapatos deportivos",
                "ropa casual", 
                "accesorios moda",
                "software empresarial",
                "herramientas productividad",
                "servicios cloud",
                "consultoría marketing",
                "diseño web",
                "desarrollo apps"
            ]
            
            # Eliminar métricas de keywords de prueba
            for keyword in test_keywords:
                deleted_metrics = self.db_service.delete_keyword_metrics_by_text(keyword)
                if deleted_metrics > 0:
                    logger.info(f"🗑️ Eliminadas {deleted_metrics} métricas para keyword de prueba: {keyword}")
            
            # Eliminar health scores asociados a keywords de prueba
            for keyword in test_keywords:
                deleted_scores = self.db_service.delete_health_scores_by_keyword(keyword)
                if deleted_scores > 0:
                    logger.info(f"🗑️ Eliminados {deleted_scores} health scores para keyword de prueba: {keyword}")
            
            logger.info("✅ Limpieza de datos de prueba completada")
            
        except Exception as e:
            logger.error(f"Error limpiando datos de prueba: {e}")
    
    def verify_real_data(self) -> bool:
        """Verificar que ahora tenemos datos reales"""
        try:
            logger.info("🔍 Verificando datos reales...")
            
            accounts = self.db_service.get_all_accounts(active_only=True)
            
            for account in accounts:
                # Verificar métricas de keywords
                metrics = self.db_service.get_keyword_metrics(account.customer_id, days_back=7)
                
                if metrics:
                    # Mostrar algunas keywords reales encontradas
                    real_keywords = [m.keyword_text for m in metrics[:5]]
                    logger.info(f"✅ Cuenta {account.customer_id}: {len(metrics)} métricas reales encontradas")
                    logger.info(f"   Ejemplos de keywords reales: {real_keywords}")
                else:
                    logger.warning(f"⚠️ Cuenta {account.customer_id}: No se encontraron métricas reales")
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando datos reales: {e}")
            return False

def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando reemplazo de datos de prueba con datos reales")
        
        replacer = RealDataReplacer()
        
        # Reemplazar datos de prueba con datos reales
        success = replacer.replace_all_test_data(days_back=30)
        
        if success:
            # Verificar que tenemos datos reales
            replacer.verify_real_data()
            logger.info("🎉 ¡Reemplazo de datos completado exitosamente!")
            return True
        else:
            logger.error("❌ Error en el reemplazo de datos")
            return False
            
    except Exception as e:
        logger.error(f"Error en main: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)