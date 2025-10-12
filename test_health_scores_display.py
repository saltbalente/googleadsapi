#!/usr/bin/env python3
"""
Script para probar que los health scores se muestren correctamente en el dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """Probar la obtención de health scores para el dashboard"""
    try:
        # Inicializar servicio
        db_service = DatabaseService()
        
        # Obtener cuentas activas
        accounts = db_service.get_all_accounts(active_only=True)
        
        print(f"Encontradas {len(accounts)} cuentas activas")
        
        for account in accounts:
            customer_id = account.customer_id
            print(f"\n🔍 Probando cuenta: {customer_id} ({account.account_name})")
            
            # Probar get_health_scores (método usado en el dashboard)
            health_scores = db_service.get_health_scores(customer_id, days_back=30)
            
            print(f"  📊 Health scores encontrados: {len(health_scores)}")
            
            if health_scores:
                # Mostrar estructura de datos
                example = health_scores[0]
                print(f"  📋 Estructura de datos:")
                for key, value in example.items():
                    print(f"    {key}: {value} ({type(value).__name__})")
                
                # Mostrar algunos ejemplos
                print(f"\n  📝 Primeros 3 health scores:")
                for i, score in enumerate(health_scores[:3]):
                    print(f"    {i+1}. {score['keyword_text']} - Score: {score['health_score']:.2f} - Categoría: {score['health_category']}")
                
                # Verificar que tengan todos los campos necesarios para la tabla
                required_fields = ['keyword_text', 'health_score', 'health_category', 'recommended_action', 
                                 'total_spend', 'total_conversions', 'total_clicks']
                
                missing_fields = []
                for field in required_fields:
                    if field not in example:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"  ❌ Campos faltantes: {missing_fields}")
                else:
                    print(f"  ✅ Todos los campos requeridos están presentes")
            else:
                print(f"  ❌ No se encontraron health scores")
        
        # Probar con un customer_id específico que sabemos que tiene datos
        print(f"\n🎯 Probando con customer_id específico que tiene datos:")
        test_customer_ids = ['1803044752', '9759913462', '1919262845', '7004285893']
        
        for customer_id in test_customer_ids:
            health_scores = db_service.get_health_scores(customer_id, days_back=30)
            print(f"  Customer {customer_id}: {len(health_scores)} health scores")
            
            if health_scores:
                example = health_scores[0]
                print(f"    Ejemplo: {example['keyword_text']} - Score: {example['health_score']:.2f}")
                break
        
    except Exception as e:
        logger.error(f"Error en el script de prueba: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()