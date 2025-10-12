"""
Scheduler Service para automatizar la ingesta diaria de datos y procesamiento de keywords
Utiliza APScheduler para ejecutar tareas programadas
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import atexit

from services.database_service import DatabaseService
from services.keyword_health_service import KeywordHealthService
from services.mcc_management_service import MCCManagementService
from services.action_execution_service import ActionExecutionService
from services.report_service import ReportService
from modules.google_ads_client import GoogleAdsClientWrapper
from utils.logger import get_logger

logger = get_logger(__name__)

class SchedulerService:
    """Servicio para automatizar tareas de optimización de keywords"""
    
    def __init__(self, google_ads_client: GoogleAdsClientWrapper):
        self.scheduler = BackgroundScheduler()
        self.db_service = DatabaseService()
        self.mcc_service = MCCManagementService()
        self.action_service = ActionExecutionService()
        self.report_service = ReportService(google_ads_client)
        self.health_service = KeywordHealthService(db_service=self.db_service, ads_client=google_ads_client, report_service=self.report_service)
        
        # Configurar listeners de eventos
        self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
        
        # Registrar shutdown handler
        atexit.register(self.shutdown)
        
        logger.info("SchedulerService inicializado")

    def start(self):
        """Iniciar el scheduler y configurar trabajos"""
        try:
            # Configurar trabajos programados
            self._setup_scheduled_jobs()
            
            # Iniciar scheduler
            self.scheduler.start()
            logger.info("Scheduler iniciado exitosamente")
            
        except Exception as e:
            logger.error(f"Error iniciando scheduler: {e}")
            raise

    def shutdown(self):
        """Detener el scheduler de forma segura"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("Scheduler detenido exitosamente")
        except Exception as e:
            logger.error(f"Error deteniendo scheduler: {e}")

    def _setup_scheduled_jobs(self):
        """Configurar todos los trabajos programados"""
        
        # 1. Ingesta diaria de datos a las 6:00 AM
        self.scheduler.add_job(
            func=self.daily_data_ingestion,
            trigger=CronTrigger(hour=6, minute=0),
            id='daily_data_ingestion',
            name='Ingesta Diaria de Datos',
            replace_existing=True,
            max_instances=1
        )
        
        # 2. Cálculo de health scores a las 7:00 AM (después de la ingesta)
        self.scheduler.add_job(
            func=self.calculate_health_scores,
            trigger=CronTrigger(hour=7, minute=0),
            id='calculate_health_scores',
            name='Cálculo de Health Scores',
            replace_existing=True,
            max_instances=1
        )
        
        # 3. Detección de nuevas cuentas cada 4 horas
        self.scheduler.add_job(
            func=self.discover_new_accounts,
            trigger=IntervalTrigger(hours=4),
            id='discover_new_accounts',
            name='Descubrimiento de Nuevas Cuentas',
            replace_existing=True,
            max_instances=1
        )
        
        # 4. Limpieza de datos antiguos cada domingo a las 2:00 AM
        self.scheduler.add_job(
            func=self.cleanup_old_data,
            trigger=CronTrigger(day_of_week=6, hour=2, minute=0),
            id='cleanup_old_data',
            name='Limpieza de Datos Antiguos',
            replace_existing=True,
            max_instances=1
        )
        
        # 5. Generación de reportes semanales los lunes a las 8:00 AM
        self.scheduler.add_job(
            func=self.generate_weekly_reports,
            trigger=CronTrigger(day_of_week=0, hour=8, minute=0),
            id='generate_weekly_reports',
            name='Reportes Semanales',
            replace_existing=True,
            max_instances=1
        )
        
        # 6. Verificación de salud del sistema cada hora
        self.scheduler.add_job(
            func=self.system_health_check,
            trigger=IntervalTrigger(hours=1),
            id='system_health_check',
            name='Verificación de Salud del Sistema',
            replace_existing=True,
            max_instances=1
        )
        
        logger.info("Trabajos programados configurados exitosamente")

    def daily_data_ingestion(self):
        """Ingesta diaria de datos de todas las cuentas MCC"""
        try:
            start_time = datetime.now()
            logger.info("Iniciando ingesta diaria de datos")
            
            # Obtener todas las cuentas activas
            accounts = self.db_service.get_all_mcc_accounts()
            active_accounts = [acc for acc in accounts if acc.get('status') == 'active']
            
            results = {
                'total_accounts': len(active_accounts),
                'successful': 0,
                'failed': 0,
                'total_keywords': 0,
                'errors': []
            }
            
            # Procesar cada cuenta
            for account in active_accounts:
                try:
                    customer_id = account['customer_id']
                    logger.info(f"Procesando cuenta: {customer_id}")
                    
                    # Obtener datos de los últimos 30 días
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=30)
                    
                    # Sincronizar datos reales de keywords usando KeywordHealthService
                    success = self.health_service.sync_keyword_data_to_database(customer_id, days_back=30)
                    
                    if success:
                        results['successful'] += 1
                        logger.info(f"Cuenta {customer_id}: métricas de keywords sincronizadas")
                    else:
                        logger.warning(f"No se obtuvieron datos para cuenta {customer_id}")
                        
                except Exception as e:
                    logger.error(f"Error procesando cuenta {account.get('customer_id')}: {e}")
                    results['failed'] += 1
                    results['errors'].append({
                        'customer_id': account.get('customer_id'),
                        'error': str(e)
                    })
            
            # Registrar resultado de la ingesta
            duration = (datetime.now() - start_time).total_seconds()
            
            self._log_job_result('daily_data_ingestion', {
                'duration_seconds': duration,
                'accounts_processed': results['successful'],
                'accounts_failed': results['failed'],
                'total_keywords': results['total_keywords'],
                'errors': results['errors']
            })
            
            logger.info(f"Ingesta diaria completada en {duration:.1f}s: {results['successful']} cuentas exitosas, {results['failed']} fallidas")
            
        except Exception as e:
            logger.error(f"Error en ingesta diaria: {e}")
            self._log_job_result('daily_data_ingestion', {'error': str(e)})

    def calculate_health_scores(self):
        """Calcular health scores para todas las keywords"""
        try:
            start_time = datetime.now()
            logger.info("Iniciando cálculo de health scores")
            
            # Obtener todas las cuentas activas
            accounts = self.db_service.get_all_mcc_accounts()
            active_accounts = [acc for acc in accounts if acc.get('status') == 'active']
            
            results = {
                'total_accounts': len(active_accounts),
                'successful': 0,
                'failed': 0,
                'total_scores': 0,
                'errors': []
            }
            
            # Procesar cada cuenta
            for account in active_accounts:
                try:
                    customer_id = account['customer_id']
                    logger.info(f"Calculando health scores para cuenta: {customer_id}")
                    
                    # Obtener métricas recientes
                    metrics = self.db_service.get_keyword_metrics(customer_id, days_back=30)
                    
                    if metrics:
                        # Calcular health scores agregados para la cuenta
                        health_scores = self.health_service.calculate_health_scores_for_account(customer_id, days_back=30)
                        
                        # Guardar health scores
                        if health_scores:
                            success = self.db_service.bulk_insert_health_scores(health_scores)
                            if success:
                                results['successful'] += 1
                                results['total_scores'] += len(health_scores)
                                logger.info(f"Cuenta {customer_id}: {len(health_scores)} health scores calculados")
                    else:
                        logger.warning(f"No se encontraron métricas para cuenta {customer_id}")
                        
                except Exception as e:
                    logger.error(f"Error calculando health scores para cuenta {account.get('customer_id')}: {e}")
                    results['failed'] += 1
                    results['errors'].append({
                        'customer_id': account.get('customer_id'),
                        'error': str(e)
                    })
            
            # Registrar resultado
            duration = (datetime.now() - start_time).total_seconds()
            
            self._log_job_result('calculate_health_scores', {
                'duration_seconds': duration,
                'accounts_processed': results['successful'],
                'accounts_failed': results['failed'],
                'total_scores': results['total_scores'],
                'errors': results['errors']
            })
            
            logger.info(f"Cálculo de health scores completado en {duration:.1f}s: {results['total_scores']} scores calculados")
            
        except Exception as e:
            logger.error(f"Error calculando health scores: {e}")
            self._log_job_result('calculate_health_scores', {'error': str(e)})

    def discover_new_accounts(self):
        """Descubrir y sincronizar nuevas cuentas MCC"""
        try:
            start_time = datetime.now()
            logger.info("Iniciando descubrimiento de nuevas cuentas")
            
            # Usar MCCManagementService para descubrir cuentas
            discovery_result = self.mcc_service.discover_and_sync_accounts()
            
            # Registrar resultado
            duration = (datetime.now() - start_time).total_seconds()
            
            self._log_job_result('discover_new_accounts', {
                'duration_seconds': duration,
                'new_accounts': discovery_result.get('new_accounts', 0),
                'updated_accounts': discovery_result.get('updated_accounts', 0),
                'errors': discovery_result.get('errors', [])
            })
            
            logger.info(f"Descubrimiento completado en {duration:.1f}s: {discovery_result.get('new_accounts', 0)} nuevas cuentas")
            
        except Exception as e:
            logger.error(f"Error en descubrimiento de cuentas: {e}")
            self._log_job_result('discover_new_accounts', {'error': str(e)})

    def cleanup_old_data(self):
        """Limpiar datos antiguos para mantener performance"""
        try:
            start_time = datetime.now()
            logger.info("Iniciando limpieza de datos antiguos")
            
            # Definir períodos de retención
            retention_periods = {
                'keyword_metrics_history': 90,  # 90 días
                'keyword_health_scores': 60,    # 60 días
                'optimization_actions': 180,    # 180 días (6 meses)
                'action_results': 180           # 180 días
            }
            
            cleanup_results = {}
            
            # Limpiar cada tabla
            for table, days in retention_periods.items():
                try:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    deleted_count = self.db_service.cleanup_old_data(table, cutoff_date)
                    cleanup_results[table] = deleted_count
                    logger.info(f"Limpieza {table}: {deleted_count} registros eliminados")
                    
                except Exception as e:
                    logger.error(f"Error limpiando tabla {table}: {e}")
                    cleanup_results[table] = f"Error: {str(e)}"
            
            # Registrar resultado
            duration = (datetime.now() - start_time).total_seconds()
            
            self._log_job_result('cleanup_old_data', {
                'duration_seconds': duration,
                'cleanup_results': cleanup_results
            })
            
            total_deleted = sum(v for v in cleanup_results.values() if isinstance(v, int))
            logger.info(f"Limpieza completada en {duration:.1f}s: {total_deleted} registros eliminados")
            
        except Exception as e:
            logger.error(f"Error en limpieza de datos: {e}")
            self._log_job_result('cleanup_old_data', {'error': str(e)})

    def generate_weekly_reports(self):
        """Generar reportes semanales de performance"""
        try:
            start_time = datetime.now()
            logger.info("Iniciando generación de reportes semanales")
            
            # Obtener todas las cuentas activas
            accounts = self.db_service.get_all_mcc_accounts()
            active_accounts = [acc for acc in accounts if acc.get('status') == 'active']
            
            reports_generated = 0
            errors = []
            
            # Generar reporte por cuenta
            for account in active_accounts:
                try:
                    customer_id = account['customer_id']
                    
                    # Generar reporte semanal
                    report_data = self._generate_account_weekly_report(customer_id)
                    
                    if report_data:
                        # Guardar reporte (en implementación real, enviar por email o guardar en storage)
                        logger.info(f"Reporte semanal generado para cuenta {customer_id}")
                        reports_generated += 1
                    
                except Exception as e:
                    logger.error(f"Error generando reporte para cuenta {account.get('customer_id')}: {e}")
                    errors.append({
                        'customer_id': account.get('customer_id'),
                        'error': str(e)
                    })
            
            # Registrar resultado
            duration = (datetime.now() - start_time).total_seconds()
            
            self._log_job_result('generate_weekly_reports', {
                'duration_seconds': duration,
                'reports_generated': reports_generated,
                'errors': errors
            })
            
            logger.info(f"Generación de reportes completada en {duration:.1f}s: {reports_generated} reportes generados")
            
        except Exception as e:
            logger.error(f"Error generando reportes semanales: {e}")
            self._log_job_result('generate_weekly_reports', {'error': str(e)})

    def system_health_check(self):
        """Verificar salud del sistema"""
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'database_connection': False,
                'scheduler_running': False,
                'recent_data_ingestion': False,
                'errors': []
            }
            
            # Verificar conexión a base de datos
            try:
                test_accounts = self.db_service.get_all_mcc_accounts()
                health_status['database_connection'] = True
            except Exception as e:
                health_status['errors'].append(f"Database error: {str(e)}")
            
            # Verificar que el scheduler esté corriendo
            health_status['scheduler_running'] = self.scheduler.running
            
            # Verificar ingesta reciente de datos
            try:
                # Verificar si hay datos de las últimas 24 horas
                recent_metrics = self.db_service.get_keyword_metrics('', days_back=1)
                health_status['recent_data_ingestion'] = len(recent_metrics) > 0
            except Exception as e:
                health_status['errors'].append(f"Data ingestion check error: {str(e)}")
            
            # Log del estado de salud
            if health_status['errors']:
                logger.warning(f"System health check - Issues found: {health_status['errors']}")
            else:
                logger.info("System health check - All systems operational")
            
            # En implementación real, enviar alertas si hay problemas críticos
            
        except Exception as e:
            logger.error(f"Error en verificación de salud del sistema: {e}")

    def _fetch_keyword_data(self, customer_id: str, start_date, end_date) -> List[Dict]:
        """Obtener datos de keywords usando ReportService existente"""
        try:
            # En implementación real, usar ReportService para obtener datos
            # Por ahora, simular datos
            logger.info(f"Obteniendo datos de keywords para {customer_id} desde {start_date} hasta {end_date}")
            
            # Simular datos de keywords
            sample_data = []
            for i in range(10):  # Simular 10 keywords por cuenta
                sample_data.append({
                    'customer_id': customer_id,
                    'campaign_id': f'campaign_{i}',
                    'ad_group_id': f'adgroup_{i}',
                    'keyword_text': f'keyword {i}',
                    'match_type': 'EXACT',
                    'date': end_date,
                    'impressions': 1000 + i * 100,
                    'clicks': 50 + i * 5,
                    'cost': 100.0 + i * 10,
                    'conversions': 2 + i,
                    'conversion_value': 200.0 + i * 20,
                    'quality_score': 7 + (i % 4),
                    'cpc_bid': 2.0 + i * 0.1
                })
            
            return sample_data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de keywords para {customer_id}: {e}")
            return []

    def _generate_account_weekly_report(self, customer_id: str) -> Optional[Dict]:
        """Generar reporte semanal para una cuenta"""
        try:
            # Obtener métricas de la semana pasada
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            
            # Obtener health scores y métricas
            health_scores = self.db_service.get_health_scores(customer_id, days_back=7)
            metrics = self.db_service.get_keyword_metrics(customer_id, days_back=7)
            
            # Calcular estadísticas del reporte
            report_data = {
                'customer_id': customer_id,
                'period': f"{start_date} to {end_date}",
                'total_keywords': len(set(m.get('keyword_text') for m in metrics)),
                'avg_health_score': sum(h.get('health_score', 0) for h in health_scores) / len(health_scores) if health_scores else 0,
                'total_cost': sum(m.get('cost', 0) for m in metrics),
                'total_conversions': sum(m.get('conversions', 0) for m in metrics),
                'generated_at': datetime.now().isoformat()
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generando reporte semanal para {customer_id}: {e}")
            return None

    def _log_job_result(self, job_id: str, result_data: Dict):
        """Registrar resultado de trabajo programado"""
        try:
            log_entry = {
                'job_id': job_id,
                'executed_at': datetime.now().isoformat(),
                'result': result_data
            }
            
            # En implementación real, guardar en base de datos o sistema de logs
            logger.info(f"Job {job_id} result logged: {result_data}")
            
        except Exception as e:
            logger.error(f"Error registrando resultado de job {job_id}: {e}")

    def _job_executed_listener(self, event):
        """Listener para trabajos ejecutados exitosamente"""
        logger.info(f"Job {event.job_id} ejecutado exitosamente")

    def _job_error_listener(self, event):
        """Listener para errores en trabajos"""
        logger.error(f"Job {event.job_id} falló: {event.exception}")

    def get_job_status(self) -> Dict[str, any]:
        """Obtener estado de todos los trabajos programados"""
        try:
            jobs_info = []
            
            for job in self.scheduler.get_jobs():
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'max_instances': job.max_instances
                }
                jobs_info.append(job_info)
            
            return {
                'scheduler_running': self.scheduler.running,
                'total_jobs': len(jobs_info),
                'jobs': jobs_info
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de trabajos: {e}")
            return {'error': str(e)}

    def trigger_job_manually(self, job_id: str) -> bool:
        """Ejecutar un trabajo manualmente"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"Job {job_id} programado para ejecución inmediata")
                return True
            else:
                logger.error(f"Job {job_id} no encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando job {job_id} manualmente: {e}")
            return False