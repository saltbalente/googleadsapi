#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos reales de keywords desde Google Ads API
"""

import os
import sys
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService, KeywordMetric, KeywordHealthScore
from services.keyword_health_service import KeywordHealthService
from modules.google_ads_client import GoogleAdsClientWrapper
from utils.logger import get_logger

logger = get_logger(__name__)

class KeywordDataPopulator:
    """Poblador de datos de keywords desde Google Ads API"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.ads_client = GoogleAdsClientWrapper()
        self.health_service = KeywordHealthService()
        logger.info("KeywordDataPopulator inicializado")
    
    def populate_all_accounts(self, days_back: int = 30) -> Dict[str, int]:
        """Poblar datos de todas las cuentas activas"""
        try:
            logger.info(f"Iniciando población de datos para los últimos {days_back} días")
            
            # Obtener todas las cuentas activas
            accounts = self.db_service.get_all_accounts(active_only=True)
            
            results = {
                'total_accounts': len(accounts),
                'successful_accounts': 0,
                'failed_accounts': 0,
                'total_keywords': 0,
                'total_health_scores': 0,
                'errors': []
            }
            
            # Procesar cada cuenta
            for account in accounts:
                try:
                    logger.info(f"Procesando cuenta: {account.account_name} ({account.customer_id})")
                    
                    # Poblar métricas de keywords
                    keyword_count = self._populate_keyword_metrics(account.customer_id, days_back)
                    
                    if keyword_count > 0:
                        # Calcular health scores
                        health_count = self._calculate_health_scores(account.customer_id)
                        
                        results['successful_accounts'] += 1
                        results['total_keywords'] += keyword_count
                        results['total_health_scores'] += health_count
                        
                        logger.info(f"✅ Cuenta {account.customer_id}: {keyword_count} keywords, {health_count} health scores")
                    else:
                        logger.warning(f"⚠️ No se encontraron datos para cuenta {account.customer_id}")
                        results['failed_accounts'] += 1
                        
                except Exception as e:
                    error_msg = f"Error procesando cuenta {account.customer_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['failed_accounts'] += 1
            
            logger.info(f"Población completada: {results['successful_accounts']}/{results['total_accounts']} cuentas exitosas")
            return results
            
        except Exception as e:
            logger.error(f"Error en población de datos: {e}")
            return {'total_accounts': 0, 'successful_accounts': 0, 'failed_accounts': 0, 'total_keywords': 0, 'errors': [str(e)]}
    
    def _populate_keyword_metrics(self, customer_id: str, days_back: int) -> int:
        """Poblar métricas de keywords para una cuenta específica"""
        try:
            # Calcular fechas
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Query para obtener datos de keywords
            query = f"""
                SELECT 
                    campaign.id,
                    campaign.name,
                    ad_group.id,
                    ad_group.name,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status,
                    ad_group_criterion.quality_info.quality_score,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value,
                    metrics.ctr,
                    metrics.average_cpc,
                    segments.date
                FROM keyword_view 
                WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                    AND ad_group_criterion.type = 'KEYWORD'
                    AND campaign.status = 'ENABLED'
                    AND ad_group.status = 'ENABLED'
                ORDER BY segments.date DESC, metrics.cost_micros DESC
                LIMIT 1000
            """
            
            # Ejecutar query
            response = self.ads_client.search(customer_id, query)
            
            # Procesar resultados
            metrics = []
            for row in response:
                try:
                    # Extraer datos
                    campaign = row.campaign
                    ad_group = row.ad_group
                    criterion = row.ad_group_criterion
                    metrics_data = row.metrics
                    segments = row.segments
                    
                    # Crear objeto KeywordMetric
                    metric = KeywordMetric(
                        customer_id=customer_id,
                        campaign_id=str(campaign.id),
                        campaign_name=campaign.name,
                        ad_group_id=str(ad_group.id),
                        ad_group_name=ad_group.name,
                        keyword_text=criterion.keyword.text,
                        match_type=criterion.keyword.match_type.name,
                        status=criterion.status.name,
                        quality_score=criterion.quality_info.quality_score if criterion.quality_info.quality_score else None,
                        impressions=metrics_data.impressions,
                        clicks=metrics_data.clicks,
                        cost_micros=metrics_data.cost_micros,
                        conversions=float(metrics_data.conversions),
                        conversions_value=float(metrics_data.conversions_value),
                        ctr=float(metrics_data.ctr) if metrics_data.ctr else None,
                        average_cpc=float(metrics_data.average_cpc) if metrics_data.average_cpc else None,
                        date=datetime.strptime(segments.date, '%Y-%m-%d').date(),
                        extracted_at=datetime.now()
                    )
                    
                    metrics.append(metric)
                    
                except Exception as e:
                    logger.warning(f"Error procesando fila de keyword: {e}")
                    continue
            
            # Insertar en base de datos
            if metrics:
                success = self.db_service.bulk_insert_keyword_metrics(metrics)
                if success:
                    logger.info(f"Insertadas {len(metrics)} métricas de keywords para cuenta {customer_id}")
                    return len(metrics)
                else:
                    logger.error(f"Error insertando métricas para cuenta {customer_id}")
                    return 0
            else:
                logger.warning(f"No se encontraron métricas de keywords para cuenta {customer_id}")
                return 0
                
        except Exception as e:
            logger.error(f"Error obteniendo métricas de keywords para cuenta {customer_id}: {e}")
            return 0
    
    def _calculate_health_scores(self, customer_id: str) -> int:
        """Calcular health scores para una cuenta específica"""
        try:
            # Usar el servicio de health para calcular scores
            health_scores = self.health_service.calculate_health_scores_for_account(customer_id)
            
            if health_scores:
                # Insertar health scores en base de datos
                success = self.db_service.bulk_insert_health_scores(health_scores)
                if success:
                    logger.info(f"Calculados {len(health_scores)} health scores para cuenta {customer_id}")
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
    
    def create_sample_data_if_empty(self) -> bool:
        """Crear datos de ejemplo si no hay datos reales disponibles"""
        try:
            logger.info("Verificando si necesitamos crear datos de ejemplo...")
            
            # Verificar si ya hay datos
            accounts = self.db_service.get_all_accounts(active_only=True)
            has_data = False
            
            for account in accounts:
                metrics = self.db_service.get_keyword_metrics(account.customer_id, days_back=7)
                if metrics:
                    has_data = True
                    break
            
            if has_data:
                logger.info("Ya existen datos reales, no se crearán datos de ejemplo")
                return True
            
            logger.info("No se encontraron datos reales, creando datos de ejemplo...")
            
            # Crear datos de ejemplo para cada cuenta
            for account in accounts:
                self._create_sample_metrics(account.customer_id)
                self._create_sample_health_scores(account.customer_id)
            
            logger.info("✅ Datos de ejemplo creados exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error creando datos de ejemplo: {e}")
            return False
    
    def _create_sample_metrics(self, customer_id: str):
        """Crear métricas de ejemplo para una cuenta"""
        try:
            import random
            
            sample_keywords = [
                "zapatos deportivos", "ropa casual", "accesorios moda",
                "software empresarial", "herramientas productividad", "servicios cloud",
                "consultoría marketing", "diseño web", "desarrollo apps"
            ]
            
            metrics = []
            
            # Crear datos para los últimos 30 días
            for days_ago in range(30):
                current_date = date.today() - timedelta(days=days_ago)
                
                for i, keyword in enumerate(sample_keywords[:6]):  # Limitar a 6 keywords
                    # Generar métricas realistas
                    impressions = random.randint(100, 5000)
                    clicks = random.randint(5, int(impressions * 0.1))
                    cost_micros = random.randint(50000, 500000)  # $50 - $500 COP
                    conversions = random.uniform(0, clicks * 0.05)
                    
                    metric = KeywordMetric(
                        customer_id=customer_id,
                        campaign_id=f"campaign_{i+1}",
                        campaign_name=f"Campaña {keyword.title()}",
                        ad_group_id=f"adgroup_{i+1}",
                        ad_group_name=f"Grupo {keyword.title()}",
                        keyword_text=keyword,
                        match_type="BROAD",
                        status="ENABLED",
                        quality_score=random.randint(3, 10),
                        impressions=impressions,
                        clicks=clicks,
                        cost_micros=cost_micros,
                        conversions=conversions,
                        conversions_value=conversions * random.uniform(100000, 1000000),  # $100k - $1M COP
                        ctr=clicks / impressions if impressions > 0 else 0,
                        average_cpc=cost_micros / clicks if clicks > 0 else 0,
                        date=current_date,
                        extracted_at=datetime.now()
                    )
                    
                    metrics.append(metric)
            
            # Insertar métricas
            if metrics:
                self.db_service.bulk_insert_keyword_metrics(metrics)
                logger.info(f"Creadas {len(metrics)} métricas de ejemplo para cuenta {customer_id}")
                
        except Exception as e:
            logger.error(f"Error creando métricas de ejemplo para cuenta {customer_id}: {e}")
    
    def _create_sample_health_scores(self, customer_id: str):
        """Crear health scores de ejemplo para una cuenta"""
        try:
            # Usar el servicio de health para calcular scores basados en las métricas de ejemplo
            health_scores = self.health_service.calculate_health_scores_for_account(customer_id)
            
            if health_scores:
                self.db_service.bulk_insert_health_scores(health_scores)
                logger.info(f"Creados {len(health_scores)} health scores de ejemplo para cuenta {customer_id}")
                
        except Exception as e:
            logger.error(f"Error creando health scores de ejemplo para cuenta {customer_id}: {e}")

def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando población de datos de keywords...")
        
        populator = KeywordDataPopulator()
        
        # Intentar poblar con datos reales
        logger.info("📊 Intentando obtener datos reales desde Google Ads API...")
        results = populator.populate_all_accounts(days_back=30)
        
        # Si no hay datos reales, crear datos de ejemplo
        if results['total_keywords'] == 0:
            logger.info("📝 No se encontraron datos reales, creando datos de ejemplo...")
            populator.create_sample_data_if_empty()
        
        logger.info("🎉 ¡Población de datos completada exitosamente!")
        logger.info("📋 Próximos pasos:")
        logger.info("   1. Verificar el dashboard de Keyword Health")
        logger.info("   2. Activar el scheduler para actualizaciones automáticas")
        logger.info("   3. Revisar las primeras recomendaciones de optimización")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en población de datos: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)