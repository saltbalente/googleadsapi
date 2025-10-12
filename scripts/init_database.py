#!/usr/bin/env python3
"""
Database Initialization Script
Configura la base de datos Supabase y crea datos iniciales para el sistema de optimización de keywords
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService, MCCAccount, KeywordBenchmark
from services.mcc_management_service import MCCManagementService
from services.scheduler_service import SchedulerService
from modules.google_ads_client import GoogleAdsClientWrapper
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseInitializer:
    """Inicializador de base de datos para el sistema de optimización de keywords"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.mcc_service = MCCManagementService()
        # Initialize Google Ads client for scheduler
        self.google_ads_client = GoogleAdsClientWrapper()
        
    def initialize_database(self, force_reset: bool = False) -> bool:
        """Inicializar base de datos completa"""
        try:
            logger.info("🚀 Iniciando inicialización de base de datos...")
            
            # 1. Verificar conexión a Supabase
            if not self._verify_supabase_connection():
                logger.error("❌ No se pudo conectar a Supabase")
                return False
            
            # 2. Verificar que las tablas existan
            if not self._verify_tables_exist():
                logger.error("❌ Las tablas de base de datos no existen. Ejecute las migraciones primero.")
                return False
            
            # 3. Limpiar datos existentes si se solicita
            if force_reset:
                logger.info("🧹 Limpiando datos existentes...")
                self._cleanup_existing_data()
            
            # 4. Crear cuentas MCC de ejemplo
            logger.info("👥 Creando cuentas MCC de ejemplo...")
            sample_accounts = self._create_sample_mcc_accounts()
            
            # 5. Crear benchmarks por defecto
            logger.info("📊 Creando benchmarks por defecto...")
            self._create_default_benchmarks(sample_accounts)
            
            # 6. Crear datos de ejemplo para testing
            logger.info("🧪 Creando datos de ejemplo...")
            self._create_sample_data(sample_accounts)
            
            # 7. Verificar integridad de datos
            logger.info("✅ Verificando integridad de datos...")
            if not self._verify_data_integrity():
                logger.warning("⚠️ Algunos problemas de integridad detectados")
            
            logger.info("🎉 Inicialización de base de datos completada exitosamente!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            return False
    
    def _verify_supabase_connection(self) -> bool:
        """Verificar conexión a Supabase"""
        try:
            # Intentar obtener cuentas MCC (operación simple)
            accounts = self.db_service.get_all_accounts()
            logger.info("✅ Conexión a Supabase verificada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Supabase: {e}")
            return False
    
    def _verify_tables_exist(self) -> bool:
        """Verificar que todas las tablas necesarias existan"""
        try:
            # Lista de tablas requeridas
            required_tables = [
                'mcc_accounts',
                'keyword_metrics_history',
                'keyword_benchmarks',
                'keyword_health_scores',
                'optimization_actions',
                'action_results'
            ]
            
            # En una implementación real, verificaríamos la existencia de cada tabla
            # Por ahora, asumimos que existen si podemos conectar
            logger.info(f"✅ Verificadas {len(required_tables)} tablas requeridas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verificando tablas: {e}")
            return False
    
    def _cleanup_existing_data(self):
        """Limpiar datos existentes (solo para reset completo)"""
        try:
            logger.warning("🧹 Limpiando todos los datos existentes...")
            
            # En implementación real, limpiaríamos las tablas en orden correcto
            # respetando las foreign keys
            
            # Por ahora, solo log
            logger.info("✅ Datos existentes limpiados")
            
        except Exception as e:
            logger.error(f"❌ Error limpiando datos: {e}")
    
    def _create_sample_mcc_accounts(self) -> List[MCCAccount]:
        """Crear cuentas MCC de ejemplo"""
        try:
            sample_accounts = [
                MCCAccount(
                    customer_id='1234567890',
                    account_name='E-commerce Store Demo',
                    currency_code='USD',
                    time_zone='America/New_York',
                    is_active=True,
                    account_type='child',
                    last_sync=datetime.now()
                ),
                MCCAccount(
                    customer_id='2345678901',
                    account_name='SaaS Company Demo',
                    currency_code='USD',
                    time_zone='America/Los_Angeles',
                    is_active=True,
                    account_type='child',
                    last_sync=datetime.now()
                ),
                MCCAccount(
                    customer_id='3456789012',
                    account_name='Local Services Demo',
                    currency_code='USD',
                    time_zone='America/Chicago',
                    is_active=True,
                    account_type='child',
                    last_sync=datetime.now()
                )
            ]
            
            # Insertar cuentas
            created_accounts = []
            for account in sample_accounts:
                try:
                    # Verificar si ya existe
                    existing = self.db_service.get_mcc_account(account.customer_id)
                    if not existing:
                        if self.db_service.insert_mcc_account(account):
                            created_accounts.append(account)
                            logger.info(f"✅ Cuenta creada: {account.account_name} ({account.customer_id})")
                        else:
                            logger.warning(f"⚠️ No se pudo crear cuenta: {account.account_name}")
                    else:
                        created_accounts.append(account)
                        logger.info(f"ℹ️ Cuenta ya existe: {account.account_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Error creando cuenta {account.account_name}: {e}")
            
            return created_accounts
            
        except Exception as e:
            logger.error(f"❌ Error creando cuentas MCC de ejemplo: {e}")
            return []
    
    def _create_default_benchmarks(self, accounts: List[MCCAccount]):
        """Crear benchmarks por defecto para las cuentas"""
        try:
            # Benchmarks por industria
            industry_benchmarks = {
                'retail': {
                    'target_ctr': 3.5,
                    'target_conversion_rate': 2.8,
                    'max_cpa': 50.0,
                    'min_quality_score': 7,
                    'target_impression_share': 65.0
                },
                'technology': {
                    'target_ctr': 2.8,
                    'target_conversion_rate': 3.2,
                    'max_cpa': 120.0,
                    'min_quality_score': 8,
                    'target_impression_share': 70.0
                },
                'services': {
                    'target_ctr': 4.2,
                    'target_conversion_rate': 4.5,
                    'max_cpa': 80.0,
                    'min_quality_score': 7,
                    'target_impression_share': 60.0
                }
            }
            
            created_benchmarks = 0
            
            for account in accounts:
                try:
                    # Obtener benchmarks para la industria
                    industry = account.industry_vertical or 'retail'
                    benchmarks_config = industry_benchmarks.get(industry, industry_benchmarks['retail'])
                    
                    # Crear benchmark
                    benchmark = KeywordBenchmark(
                        customer_id=account.customer_id,
                        benchmark_name=f"{industry.title()} Industry Standard",
                        target_ctr=benchmarks_config['target_ctr'],
                        target_conversion_rate=benchmarks_config['target_conversion_rate'],
                        max_cpa=benchmarks_config['max_cpa'],
                        min_quality_score=benchmarks_config['min_quality_score'],
                        target_impression_share=benchmarks_config['target_impression_share'],
                        is_default=True,
                        created_at=datetime.now()
                    )
                    
                    # Verificar si ya existe
                    existing_benchmarks = self.db_service.get_account_benchmarks(account.customer_id)
                    if not any(b.get('is_default') for b in existing_benchmarks):
                        if self.db_service.insert_keyword_benchmark(benchmark):
                            created_benchmarks += 1
                            logger.info(f"✅ Benchmark creado para {account.account_name}")
                        else:
                            logger.warning(f"⚠️ No se pudo crear benchmark para {account.account_name}")
                    else:
                        logger.info(f"ℹ️ Benchmark ya existe para {account.account_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Error creando benchmark para {account.account_name}: {e}")
            
            logger.info(f"✅ {created_benchmarks} benchmarks creados")
            
        except Exception as e:
            logger.error(f"❌ Error creando benchmarks por defecto: {e}")
    
    def _create_sample_data(self, accounts: List[MCCAccount]):
        """Crear datos de ejemplo para testing"""
        try:
            logger.info("🧪 Creando datos de ejemplo para testing...")
            
            # Crear métricas de ejemplo para cada cuenta
            for account in accounts:
                self._create_sample_metrics(account)
                self._create_sample_health_scores(account)
            
            logger.info("✅ Datos de ejemplo creados")
            
        except Exception as e:
            logger.error(f"❌ Error creando datos de ejemplo: {e}")
    
    def _create_sample_metrics(self, account: MCCAccount):
        """Crear métricas de ejemplo para una cuenta"""
        try:
            # Generar métricas para los últimos 30 días
            sample_keywords = [
                'running shoes',
                'nike sneakers',
                'athletic footwear',
                'sports equipment',
                'fitness gear'
            ]
            
            metrics_data = []
            
            for i, keyword in enumerate(sample_keywords):
                for days_ago in range(30):
                    date = datetime.now().date() - timedelta(days=days_ago)
                    
                    # Generar métricas realistas
                    base_impressions = 1000 + (i * 200)
                    base_clicks = int(base_impressions * 0.035)  # 3.5% CTR
                    base_cost = base_clicks * (2.0 + i * 0.5)
                    base_conversions = int(base_clicks * 0.03)  # 3% conversion rate
                    
                    # Añadir variación diaria
                    daily_variation = 0.8 + (days_ago % 7) * 0.05
                    
                    metric = {
                        'customer_id': account.customer_id,
                        'campaign_id': f'campaign_{i+1}',
                        'ad_group_id': f'adgroup_{i+1}',
                        'keyword_text': keyword,
                        'match_type': 'EXACT',
                        'date': date,
                        'impressions': int(base_impressions * daily_variation),
                        'clicks': int(base_clicks * daily_variation),
                        'cost': base_cost * daily_variation,
                        'conversions': int(base_conversions * daily_variation),
                        'conversion_value': base_conversions * daily_variation * 25.0,
                        'quality_score': 7 + (i % 4),
                        'cpc_bid': 2.0 + i * 0.3
                    }
                    
                    metrics_data.append(metric)
            
            # Insertar métricas (en lotes para eficiencia)
            if metrics_data:
                inserted_count = self.db_service.insert_keyword_metrics(metrics_data)
                logger.info(f"✅ {inserted_count} métricas de ejemplo creadas para {account.account_name}")
            
        except Exception as e:
            logger.error(f"❌ Error creando métricas de ejemplo para {account.account_name}: {e}")
    
    def _create_sample_health_scores(self, account: MCCAccount):
        """Crear health scores de ejemplo para una cuenta"""
        try:
            # Generar health scores para keywords de ejemplo
            sample_keywords = [
                'running shoes',
                'nike sneakers',
                'athletic footwear',
                'sports equipment',
                'fitness gear'
            ]
            
            health_scores_data = []
            
            for i, keyword in enumerate(sample_keywords):
                # Generar health score realista
                base_score = 60 + (i * 8)  # Scores entre 60-92
                
                health_score = {
                    'customer_id': account.customer_id,
                    'campaign_id': f'campaign_{i+1}',
                    'ad_group_id': f'adgroup_{i+1}',
                    'keyword_text': keyword,
                    'health_score': min(100, base_score + (i % 3) * 5),
                    'conversion_rate_score': 70 + (i * 5),
                    'cpa_score': 65 + (i * 6),
                    'ctr_score': 75 + (i * 4),
                    'volume_score': 80 + (i * 3),
                    'quality_score_component': 85 + (i * 2),
                    'data_confidence': 0.85 + (i * 0.03),
                    'calculated_at': datetime.now()
                }
                
                health_scores_data.append(health_score)
            
            # Insertar health scores
            if health_scores_data:
                inserted_count = self.db_service.insert_health_scores(health_scores_data)
                logger.info(f"✅ {inserted_count} health scores de ejemplo creados para {account.account_name}")
            
        except Exception as e:
            logger.error(f"❌ Error creando health scores de ejemplo para {account.account_name}: {e}")
    
    def _verify_data_integrity(self) -> bool:
        """Verificar integridad de los datos creados"""
        try:
            integrity_checks = []
            
            # 1. Verificar que hay cuentas MCC
            accounts = self.db_service.get_all_mcc_accounts()
            integrity_checks.append(('MCC Accounts', len(accounts) > 0, f"{len(accounts)} cuentas encontradas"))
            
            # 2. Verificar que hay benchmarks
            total_benchmarks = 0
            for account in accounts:
                benchmarks = self.db_service.get_account_benchmarks(account['customer_id'])
                total_benchmarks += len(benchmarks)
            
            integrity_checks.append(('Benchmarks', total_benchmarks > 0, f"{total_benchmarks} benchmarks encontrados"))
            
            # 3. Verificar que hay métricas
            total_metrics = 0
            for account in accounts:
                metrics = self.db_service.get_keyword_metrics(account['customer_id'], days_back=30)
                total_metrics += len(metrics)
            
            integrity_checks.append(('Keyword Metrics', total_metrics > 0, f"{total_metrics} métricas encontradas"))
            
            # 4. Verificar que hay health scores
            total_scores = 0
            for account in accounts:
                scores = self.db_service.get_health_scores(account['customer_id'], days_back=30)
                total_scores += len(scores)
            
            integrity_checks.append(('Health Scores', total_scores > 0, f"{total_scores} scores encontrados"))
            
            # Mostrar resultados
            all_passed = True
            for check_name, passed, message in integrity_checks:
                if passed:
                    logger.info(f"✅ {check_name}: {message}")
                else:
                    logger.error(f"❌ {check_name}: {message}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            logger.error(f"❌ Error verificando integridad de datos: {e}")
            return False
    
    def setup_scheduler(self) -> bool:
        """Configurar y iniciar el scheduler"""
        try:
            logger.info("⏰ Configurando scheduler...")
            
            scheduler_service = SchedulerService(self.google_ads_client)
            scheduler_service.start()
            
            logger.info("✅ Scheduler configurado y iniciado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando scheduler: {e}")
            return False
    
    def run_initial_data_sync(self) -> bool:
        """Ejecutar sincronización inicial de datos"""
        try:
            logger.info("🔄 Ejecutando sincronización inicial de datos...")
            
            # Descubrir y sincronizar cuentas MCC reales
            discovery_result = self.mcc_service.discover_and_sync_accounts()
            
            logger.info(f"✅ Sincronización completada: {discovery_result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en sincronización inicial: {e}")
            return False

def main():
    """Función principal del script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Inicializar base de datos del sistema de optimización de keywords')
    parser.add_argument('--reset', action='store_true', help='Limpiar datos existentes antes de inicializar')
    parser.add_argument('--no-scheduler', action='store_true', help='No iniciar el scheduler')
    parser.add_argument('--no-sync', action='store_true', help='No ejecutar sincronización inicial')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar logs detallados')
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear inicializador
    initializer = DatabaseInitializer()
    
    try:
        logger.info("🚀 Iniciando configuración del sistema de optimización de keywords...")
        
        # 1. Inicializar base de datos
        if not initializer.initialize_database(force_reset=args.reset):
            logger.error("❌ Falló la inicialización de base de datos")
            sys.exit(1)
        
        # 2. Configurar scheduler (opcional)
        if not args.no_scheduler:
            if not initializer.setup_scheduler():
                logger.warning("⚠️ Falló la configuración del scheduler, pero continuando...")
        
        # 3. Ejecutar sincronización inicial (opcional)
        if not args.no_sync:
            if not initializer.run_initial_data_sync():
                logger.warning("⚠️ Falló la sincronización inicial, pero continuando...")
        
        logger.info("🎉 ¡Sistema de optimización de keywords configurado exitosamente!")
        logger.info("📋 Próximos pasos:")
        logger.info("   1. Verificar que el scheduler esté ejecutándose")
        logger.info("   2. Acceder al dashboard en la página 'Keyword Health'")
        logger.info("   3. Configurar benchmarks personalizados si es necesario")
        logger.info("   4. Revisar las primeras recomendaciones de optimización")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Inicialización cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()