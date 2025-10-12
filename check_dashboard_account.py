#!/usr/bin/env python3
"""
Script para verificar qué cuenta está seleccionada en el dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService

def check_dashboard_account():
    """Verificar las cuentas disponibles y sus health scores"""
    
    db_service = DatabaseService()
    
    print("=== VERIFICACIÓN DE CUENTAS PARA DASHBOARD ===")
    
    # Obtener todas las cuentas
    accounts = db_service.get_all_accounts(active_only=True)
    
    print(f"\n📊 Cuentas disponibles ({len(accounts)}):")
    
    accounts_with_scores = []
    accounts_without_scores = []
    
    for account in accounts:
        customer_id = account.customer_id
        account_name = account.account_name
        
        # Verificar health scores
        health_scores = db_service.get_health_scores(customer_id, days_back=30)
        score_count = len(health_scores)
        
        print(f"\n  🏢 {account_name}")
        print(f"     ID: {customer_id}")
        print(f"     Health Scores: {score_count}")
        
        if score_count > 0:
            accounts_with_scores.append({
                'customer_id': customer_id,
                'account_name': account_name,
                'score_count': score_count
            })
            print(f"     ✅ TIENE DATOS")
        else:
            accounts_without_scores.append({
                'customer_id': customer_id,
                'account_name': account_name
            })
            print(f"     ❌ SIN DATOS")
    
    print(f"\n📈 RESUMEN:")
    print(f"  ✅ Cuentas CON health scores: {len(accounts_with_scores)}")
    for acc in accounts_with_scores:
        print(f"     - {acc['account_name']} ({acc['customer_id']}): {acc['score_count']} scores")
    
    print(f"\n  ❌ Cuentas SIN health scores: {len(accounts_without_scores)}")
    for acc in accounts_without_scores:
        print(f"     - {acc['account_name']} ({acc['customer_id']})")
    
    print(f"\n💡 RECOMENDACIÓN:")
    if accounts_with_scores:
        best_account = max(accounts_with_scores, key=lambda x: x['score_count'])
        print(f"   Para ver datos en el dashboard, selecciona la cuenta:")
        print(f"   🎯 {best_account['account_name']} ({best_account['customer_id']})")
        print(f"   Esta cuenta tiene {best_account['score_count']} health scores")
    else:
        print("   ⚠️ Ninguna cuenta tiene health scores calculados")
        print("   Ejecuta el script de cálculo de health scores primero")
    
    print("\n=== FIN VERIFICACIÓN ===")

if __name__ == "__main__":
    check_dashboard_account()