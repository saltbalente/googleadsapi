#!/usr/bin/env python3
"""
Script para iniciar el scheduler de forma independiente
"""

import os
import sys
import signal
import time
import logging
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scheduler_service import SchedulerService
from modules.google_ads_client import GoogleAdsClientWrapper
from utils.logger import get_logger

logger = get_logger(__name__)

class SchedulerManager:
    """Gestor del scheduler para ejecución independiente"""
    
    def __init__(self):
        self.scheduler_service = None
        self.running = False
        logger.info("SchedulerManager inicializado")
    
    def start(self):
        """Iniciar el scheduler"""
        try:
            logger.info("🚀 Iniciando scheduler...")
            
            # Inicializar cliente de Google Ads
            google_ads_client = GoogleAdsClientWrapper()
            
            # Crear e iniciar scheduler service
            self.scheduler_service = SchedulerService(google_ads_client)
            self.scheduler_service.start()
            
            self.running = True
            logger.info("✅ Scheduler iniciado exitosamente")
            
            # Mostrar estado de trabajos programados
            self._show_job_status()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando scheduler: {e}")
            return False
    
    def stop(self):
        """Detener el scheduler"""
        try:
            if self.scheduler_service and self.running:
                logger.info("🛑 Deteniendo scheduler...")
                self.scheduler_service.shutdown()
                self.running = False
                logger.info("✅ Scheduler detenido exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo scheduler: {e}")
    
    def _show_job_status(self):
        """Mostrar estado de trabajos programados"""
        try:
            if self.scheduler_service:
                status = self.scheduler_service.get_job_status()
                
                logger.info("📋 Estado del scheduler:")
                logger.info(f"   - Scheduler activo: {status.get('scheduler_running', False)}")
                logger.info(f"   - Total trabajos: {status.get('total_jobs', 0)}")
                
                jobs = status.get('jobs', [])
                if jobs:
                    logger.info("   - Trabajos programados:")
                    for job in jobs:
                        next_run = job.get('next_run', 'No programado')
                        logger.info(f"     • {job.get('name', job.get('id'))}: {next_run}")
                
        except Exception as e:
            logger.error(f"Error mostrando estado de trabajos: {e}")
    
    def run_forever(self):
        """Ejecutar el scheduler de forma continua"""
        try:
            logger.info("🔄 Scheduler ejecutándose en modo continuo...")
            logger.info("   Presiona Ctrl+C para detener")
            
            # Configurar manejador de señales para shutdown limpio
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Mantener el proceso vivo
            while self.running:
                time.sleep(60)  # Verificar cada minuto
                
                # Mostrar estado cada 30 minutos
                if datetime.now().minute % 30 == 0:
                    self._show_job_status()
            
        except KeyboardInterrupt:
            logger.info("⚠️ Interrupción recibida, deteniendo scheduler...")
        except Exception as e:
            logger.error(f"❌ Error en ejecución continua: {e}")
        finally:
            self.stop()
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales para shutdown limpio"""
        logger.info(f"Señal {signum} recibida, iniciando shutdown...")
        self.running = False

def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando Scheduler Manager...")
        
        manager = SchedulerManager()
        
        # Iniciar scheduler
        if manager.start():
            # Ejecutar de forma continua
            manager.run_forever()
        else:
            logger.error("❌ No se pudo iniciar el scheduler")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en Scheduler Manager: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)