#!/usr/bin/env python3
"""
Script para probar health scores en cuentas específicas que tienen datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService
from datetime import datetime, timedelta

def test_specific_accounts():
    """Probar health scores en cuentas específicas"""
    
    db_service = DatabaseService()
    
    print("=== PRUEBA DE CUENTAS ESPECÍFICAS ===")
    
    # Cuentas que sabemos tienen health scores calculados
    test_accounts = [
        '1803044752',
        '9759913462', 
        '1919262845',
        '7004285893'
    ]
    
    for customer_id in test_accounts:
        print(f"\n--- Probando cuenta: {customer_id} ---")
        
        # Obtener health scores
        health_scores = db_service.get_health_scores(customer_id, days_back=30)
        print(f"Health scores (30 días): {len(health_scores)}")
        
        # Obtener latest health scores
        latest_scores = db_service.get_latest_health_scores(customer_id)
        print(f"Latest health scores: {len(latest_scores)}")
        
        # Obtener keyword metrics
        keyword_metrics = db_service.get_keyword_metrics(customer_id)
        print(f"Keyword metrics: {len(keyword_metrics)}")
        
        if health_scores:
            print("✅ Esta cuenta tiene health scores!")
            # Mostrar algunos ejemplos
            for i, score in enumerate(health_scores[:3]):
                print(f"  {i+1}. Keyword: '{score.get('keyword_text', 'N/A')}', "
                      f"Score: {score.get('health_score', 'N/A')}, "
                      f"Category: '{score.get('health_category', 'N/A')}'")
        else:
            print("❌ No hay health scores para esta cuenta")
    
    print("\n=== FIN PRUEBA ===")

if __name__ == "__main__":
    test_specific_accounts()