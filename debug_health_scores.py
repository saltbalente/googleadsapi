#!/usr/bin/env python3
"""
Script para debuggear los health scores en la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService
from datetime import datetime, timedelta

def debug_health_scores():
    """Debuggea los health scores en la base de datos"""
    
    db_service = DatabaseService()
    
    print("=== DEBUG HEALTH SCORES ===")
    
    # 1. Verificar cuentas activas
    print("\n1. Verificando cuentas activas...")
    accounts = db_service.get_all_accounts(active_only=True)
    print(f"Cuentas activas encontradas: {len(accounts)}")
    
    for account in accounts[:5]:  # Mostrar solo las primeras 5
        print(f"  - {account.customer_id}: {account.account_name}")
    
    # 2. Verificar health scores existentes
    print("\n2. Verificando health scores existentes...")
    
    # Verificar para cada cuenta
    for account in accounts[:3]:  # Solo las primeras 3 para no saturar
        print(f"\n--- Cuenta: {account.customer_id} ({account.account_name}) ---")
        
        # Obtener health scores
        health_scores = db_service.get_health_scores(account.customer_id)
        print(f"Health scores encontrados: {len(health_scores)}")
        
        if health_scores:
            # Mostrar algunos ejemplos
            for i, score in enumerate(health_scores[:3]):
                print(f"  Score {i+1}: Keyword='{score.get('keyword', 'N/A')}', "
                      f"Health Score={score.get('health_score', 'N/A')}, "
                      f"Status='{score.get('status', 'N/A')}'")
        
        # Obtener latest health scores
        latest_scores = db_service.get_latest_health_scores(account.customer_id)
        print(f"Latest health scores: {len(latest_scores)}")
        
        # Verificar keyword metrics
        keyword_metrics = db_service.get_keyword_metrics(account.customer_id)
        print(f"Keyword metrics encontrados: {len(keyword_metrics)}")
    
    # 3. Verificar tabla directamente
    print("\n3. Verificando tabla keyword_health_scores directamente...")
    
    try:
        # Contar registros totales
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM keyword_health_scores")
            total_count = cursor.fetchone()[0]
            print(f"Total registros en keyword_health_scores: {total_count}")
            
            # Verificar registros recientes (últimos 7 días)
            cursor.execute("""
                SELECT COUNT(*) FROM keyword_health_scores 
                WHERE created_at >= %s
            """, (datetime.now() - timedelta(days=7),))
            recent_count = cursor.fetchone()[0]
            print(f"Registros de los últimos 7 días: {recent_count}")
            
            # Mostrar algunos registros de ejemplo
            cursor.execute("""
                SELECT customer_id, keyword, health_score, status, created_at 
                FROM keyword_health_scores 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            sample_records = cursor.fetchall()
            print(f"\nEjemplos de registros (útimos 5):")
            for record in sample_records:
                print(f"  Customer: {record[0]}, Keyword: '{record[1]}', "
                      f"Score: {record[2]}, Status: '{record[3]}', "
                      f"Created: {record[4]}")
                      
    except Exception as e:
        print(f"Error al verificar tabla: {e}")
    
    print("\n=== FIN DEBUG ===")

if __name__ == "__main__":
    debug_health_scores()