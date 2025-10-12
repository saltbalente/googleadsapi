#!/usr/bin/env python3
"""
Script para calcular y guardar health scores en la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService
from services.keyword_health_service import KeywordHealthService
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """Calcular y guardar health scores para todas las cuentas activas"""
    try:
        # Inicializar servicios
        db_service = DatabaseService()
        health_service = KeywordHealthService(db_service=db_service)
        
        # Obtener cuentas activas
        accounts = db_service.get_all_accounts(active_only=True)
        active_accounts = [{'customer_id': acc.customer_id, 'account_name': acc.account_name} for acc in accounts]
        
        print(f"Encontradas {len(active_accounts)} cuentas activas")
        
        total_scores_saved = 0
        
        for account in active_accounts:
            customer_id = account['customer_id']
            print(f"\nProcesando cuenta: {customer_id}")
            
            # Verificar si hay métricas
            metrics = db_service.get_keyword_metrics(customer_id, days_back=30)
            if not metrics:
                print(f"  No hay métricas para la cuenta {customer_id}")
                continue
                
            print(f"  Encontradas {len(metrics)} métricas")
            
            # Calcular health scores
            health_scores = health_service.calculate_health_scores_for_account(customer_id, days_back=30)
            
            if health_scores:
                # Guardar en base de datos
                success = db_service.bulk_insert_health_scores(health_scores)
                
                if success:
                    print(f"  ✅ Guardados {len(health_scores)} health scores")
                    total_scores_saved += len(health_scores)
                else:
                    print(f"  ❌ Error guardando health scores")
            else:
                print(f"  No se pudieron calcular health scores")
        
        print(f"\n🎉 Total de health scores guardados: {total_scores_saved}")
        
        # Verificar datos guardados
        print("\n📊 Verificando datos guardados:")
        for account in active_accounts[:3]:  # Solo verificar las primeras 3 cuentas
            customer_id = account['customer_id']
            saved_scores = db_service.get_health_scores(customer_id, days_back=30)
            print(f"  Cuenta {customer_id}: {len(saved_scores)} health scores en BD")
            
            if saved_scores:
                # Mostrar ejemplo
                example = saved_scores[0]
                print(f"    Ejemplo: {example['keyword_text']} - Score: {example['health_score']:.2f}")
        
    except Exception as e:
        logger.error(f"Error en el script principal: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()