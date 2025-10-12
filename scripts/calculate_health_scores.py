#!/usr/bin/env python3
"""
Script para calcular health scores basados en las métricas existentes en la base de datos
"""

import os
import sys
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService, KeywordHealthScore
from services.keyword_health_service import KeywordHealthService
from utils.logger import get_logger

logger = get_logger(__name__)

class HealthScoreCalculator:
    """Calculador de health scores basado en métricas existentes"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.health_service = KeywordHealthService()
        logger.info("HealthScoreCalculator inicializado")
    
    def calculate_all_accounts(self) -> Dict[str, int]:
        """Calcular health scores para todas las cuentas con métricas"""
        try:
            logger.info("Iniciando cálculo de health scores para todas las cuentas")
            
            # Obtener todas las cuentas activas
            accounts = self.db_service.get_all_accounts(active_only=True)
            
            results = {
                'total_accounts': len(accounts),
                'successful_accounts': 0,
                'failed_accounts': 0,
                'total_health_scores': 0,
                'errors': []
            }
            
            # Procesar cada cuenta
            for account in accounts:
                try:
                    logger.info(f"Calculando health scores para cuenta: {account.account_name} ({account.customer_id})")
                    
                    # Verificar si hay métricas para esta cuenta
                    metrics = self.db_service.get_keyword_metrics(account.customer_id, days_back=30)
                    
                    if not metrics:
                        logger.warning(f"No se encontraron métricas para cuenta {account.customer_id}")
                        results['failed_accounts'] += 1
                        continue
                    
                    # Calcular health scores
                    health_scores = self.health_service.calculate_health_scores_for_account(account.customer_id)
                    
                    if health_scores:
                        # Insertar health scores en base de datos
                        success = self.db_service.bulk_insert_health_scores(health_scores)
                        if success:
                            results['successful_accounts'] += 1
                            results['total_health_scores'] += len(health_scores)
                            logger.info(f"✅ Calculados {len(health_scores)} health scores para cuenta {account.customer_id}")
                        else:
                            logger.error(f"Error insertando health scores para cuenta {account.customer_id}")
                            results['failed_accounts'] += 1
                    else:
                        logger.warning(f"No se pudieron calcular health scores para cuenta {account.customer_id}")
                        results['failed_accounts'] += 1
                        
                except Exception as e:
                    error_msg = f"Error procesando cuenta {account.customer_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['failed_accounts'] += 1
            
            logger.info(f"Cálculo completado: {results['successful_accounts']}/{results['total_accounts']} cuentas exitosas")
            logger.info(f"Total health scores calculados: {results['total_health_scores']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en cálculo de health scores: {e}")
            return {'total_accounts': 0, 'successful_accounts': 0, 'failed_accounts': 0, 'total_health_scores': 0, 'errors': [str(e)]}
    
    def calculate_for_account(self, customer_id: str) -> int:
        """Calcular health scores para una cuenta específica"""
        try:
            logger.info(f"Calculando health scores para cuenta: {customer_id}")
            
            # Verificar si hay métricas para esta cuenta
            metrics = self.db_service.get_keyword_metrics(customer_id, days_back=30)
            
            if not metrics:
                logger.warning(f"No se encontraron métricas para cuenta {customer_id}")
                return 0
            
            # Calcular health scores
            health_scores = self.health_service.calculate_health_scores_for_account(customer_id)
            
            if health_scores:
                # Insertar health scores en base de datos
                success = self.db_service.bulk_insert_health_scores(health_scores)
                if success:
                    logger.info(f"✅ Calculados {len(health_scores)} health scores para cuenta {customer_id}")
                    return len(health_scores)
                else:
                    logger.error(f"Error insertando health scores para cuenta {customer_id}")
                    return 0
            else:
                logger.warning(f"No se pudieron calcular health scores para cuenta {customer_id}")
                return 0
                
        except Exception as e:
            logger.error(f"Error calculando health scores para cuenta {customer_id}: {e}")
            return 0

def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando cálculo de health scores...")
        
        calculator = HealthScoreCalculator()
        
        # Calcular health scores para todas las cuentas
        results = calculator.calculate_all_accounts()
        
        if results['total_health_scores'] > 0:
            logger.info("🎉 ¡Cálculo de health scores completado exitosamente!")
            logger.info(f"📊 Resumen:")
            logger.info(f"   - Cuentas procesadas: {results['successful_accounts']}/{results['total_accounts']}")
            logger.info(f"   - Health scores calculados: {results['total_health_scores']}")
            logger.info(f"   - Errores: {len(results['errors'])}")
        else:
            logger.warning("⚠️ No se calcularon health scores. Verifica que existan métricas en la base de datos.")
        
        logger.info("📋 Próximos pasos:")
        logger.info("   1. Verificar el dashboard de Keyword Health")
        logger.info("   2. Activar el scheduler para actualizaciones automáticas")
        logger.info("   3. Revisar las recomendaciones de optimización")
        
        return results['total_health_scores'] > 0
        
    except Exception as e:
        logger.error(f"❌ Error en cálculo de health scores: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)