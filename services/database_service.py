"""
DatabaseService para el sistema de optimización de keywords
Maneja todas las operaciones CRUD con Supabase
"""

import os
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import pandas as pd
from supabase import create_client, Client
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class MCCAccount:
    customer_id: str
    account_name: str
    currency_code: str
    time_zone: str
    is_active: bool = True
    account_type: str = 'child'
    parent_customer_id: Optional[str] = None
    discovered_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None

@dataclass
class KeywordMetric:
    customer_id: str
    campaign_id: str
    campaign_name: str
    ad_group_id: str
    ad_group_name: str
    keyword_text: str
    match_type: str
    status: str
    quality_score: Optional[int]
    impressions: int
    clicks: int
    cost_micros: int
    conversions: float
    conversions_value: float
    ctr: Optional[float]
    average_cpc: Optional[float]
    date: date
    extracted_at: Optional[datetime] = None

@dataclass
class KeywordBenchmark:
    customer_id: str
    target_conv_rate: float = 0.02
    target_cpa: float = 200000.00
    benchmark_ctr: float = 0.03
    min_quality_score: int = 5
    industry_vertical: Optional[str] = 'general'
    seasonality_factor: float = 1.00
    risk_tolerance: str = 'moderate'
    created_by: Optional[str] = None

@dataclass
class KeywordHealthScore:
    customer_id: str
    campaign_id: str
    ad_group_id: str
    keyword_text: str
    health_score: float
    conv_rate_score: float = 0
    cpa_score: float = 0
    ctr_score: float = 0
    confidence_score: float = 0
    quality_score_points: float = 0
    health_category: str = 'warning'
    recommended_action: str = 'monitor'
    action_priority: int = 5
    data_period_start: date = None
    data_period_end: date = None
    total_spend: Optional[float] = None
    total_conversions: Optional[float] = None
    total_clicks: Optional[int] = None
    calculated_at: Optional[datetime] = None

@dataclass
class OptimizationAction:
    customer_id: str
    execution_id: str
    campaign_id: str
    ad_group_id: str
    keyword_text: str
    action_type: str
    old_bid: Optional[float] = None
    new_bid: Optional[float] = None
    bid_change_percent: Optional[float] = None
    justification: Optional[str] = None
    health_score_before: Optional[float] = None
    risk_level: str = 'medium'
    status: str = 'pending'
    executed_by: Optional[str] = None
    google_ads_operation_id: Optional[str] = None
    api_response: Optional[str] = None
    error_message: Optional[str] = None

class DatabaseService:
    """Servicio para todas las operaciones de base de datos del sistema de optimización"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://xpfggzurtzyrwdvybecd.supabase.co')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 
                                     'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhwZmdnenVydHp5cndkdnliZWNkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDEzMzc4MSwiZXhwIjoyMDc1NzA5NzgxfQ.IxW9KSUyS0jSAi4Irfmwf9GKvMqIYrDnt5voPpF4AQQ')
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("DatabaseService inicializado correctamente")

    # ==================== MCC ACCOUNTS ====================
    
    def get_all_accounts(self, active_only: bool = True) -> List[MCCAccount]:
        """Obtener todas las cuentas MCC"""
        try:
            query = self.client.table('mcc_accounts').select('*')
            if active_only:
                query = query.eq('is_active', True)
            
            response = query.execute()
            accounts = []
            
            for row in response.data:
                accounts.append(MCCAccount(
                    customer_id=row['customer_id'],
                    account_name=row['account_name'],
                    currency_code=row['currency_code'],
                    time_zone=row['time_zone'],
                    is_active=row['is_active'],
                    account_type=row.get('account_type', 'child'),
                    parent_customer_id=row.get('parent_customer_id'),
                    discovered_at=datetime.fromisoformat(row['discovered_at'].replace('Z', '+00:00')) if row.get('discovered_at') else None,
                    last_sync=datetime.fromisoformat(row['last_sync'].replace('Z', '+00:00')) if row.get('last_sync') else None
                ))
            
            logger.info(f"Obtenidas {len(accounts)} cuentas MCC")
            return accounts
            
        except Exception as e:
            logger.error(f"Error obteniendo cuentas MCC: {e}")
            return []

    def upsert_account(self, account: MCCAccount) -> bool:
        """Insertar o actualizar una cuenta MCC"""
        try:
            data = {
                'customer_id': account.customer_id,
                'account_name': account.account_name,
                'currency_code': account.currency_code,
                'time_zone': account.time_zone,
                'is_active': account.is_active,
                'account_type': account.account_type,
                'parent_customer_id': account.parent_customer_id,
                'last_sync': datetime.now().isoformat()
            }
            
            response = self.client.table('mcc_accounts').upsert(data).execute()
            logger.info(f"Cuenta {account.customer_id} actualizada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando cuenta {account.customer_id}: {e}")
            return False

    def get_mcc_account(self, customer_id: str) -> Optional[MCCAccount]:
        """Obtener una cuenta MCC específica por customer_id"""
        try:
            response = self.client.table('mcc_accounts').select('*').eq('customer_id', customer_id).execute()
            
            if response.data:
                row = response.data[0]
                return MCCAccount(
                    customer_id=row['customer_id'],
                    account_name=row['account_name'],
                    currency_code=row['currency_code'],
                    time_zone=row['time_zone'],
                    is_active=row['is_active'],
                    account_type=row.get('account_type', 'child'),
                    parent_customer_id=row.get('parent_customer_id'),
                    discovered_at=datetime.fromisoformat(row['discovered_at'].replace('Z', '+00:00')) if row.get('discovered_at') else None,
                    last_sync=datetime.fromisoformat(row['last_sync'].replace('Z', '+00:00')) if row.get('last_sync') else None
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo cuenta MCC {customer_id}: {e}")
            return None

    def insert_mcc_account(self, account: MCCAccount) -> bool:
        """Insertar una nueva cuenta MCC"""
        try:
            data = {
                'customer_id': account.customer_id,
                'account_name': account.account_name,
                'currency_code': account.currency_code,
                'time_zone': account.time_zone,
                'is_active': account.is_active,
                'account_type': account.account_type,
                'parent_customer_id': account.parent_customer_id,
                'discovered_at': account.discovered_at.isoformat() if account.discovered_at else datetime.now().isoformat(),
                'last_sync': account.last_sync.isoformat() if account.last_sync else datetime.now().isoformat()
            }
            
            response = self.client.table('mcc_accounts').insert(data).execute()
            logger.info(f"Cuenta {account.customer_id} insertada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error insertando cuenta {account.customer_id}: {e}")
            return False

    def update_mcc_account(self, account: MCCAccount) -> bool:
        """Actualizar una cuenta MCC existente"""
        try:
            data = {
                'account_name': account.account_name,
                'currency_code': account.currency_code,
                'time_zone': account.time_zone,
                'is_active': account.is_active,
                'account_type': account.account_type,
                'parent_customer_id': account.parent_customer_id,
                'last_sync': datetime.now().isoformat()
            }
            
            response = self.client.table('mcc_accounts').update(data).eq('customer_id', account.customer_id).execute()
            logger.info(f"Cuenta {account.customer_id} actualizada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando cuenta {account.customer_id}: {e}")
            return False

    def get_account_benchmarks(self, customer_id: str) -> Optional[KeywordBenchmark]:
        """Obtener benchmarks de una cuenta específica"""
        try:
            response = self.client.table('keyword_benchmarks').select('*').eq('customer_id', customer_id).execute()
            
            if response.data:
                row = response.data[0]
                return KeywordBenchmark(
                    customer_id=row['customer_id'],
                    target_conv_rate=float(row['target_conv_rate']),
                    target_cpa=float(row['target_cpa']),
                    benchmark_ctr=float(row['benchmark_ctr']),
                    min_quality_score=int(row['min_quality_score']),
                    industry_vertical=row.get('industry_vertical'),
                    seasonality_factor=float(row.get('seasonality_factor', 1.0)),
                    risk_tolerance=row.get('risk_tolerance', 'moderate'),
                    created_by=row.get('created_by')
                )
            else:
                # Usar benchmarks por defecto
                return self.get_default_benchmarks()
                
        except Exception as e:
            logger.error(f"Error obteniendo benchmarks para {customer_id}: {e}")
            return self.get_default_benchmarks()

    def get_default_benchmarks(self) -> KeywordBenchmark:
        """Obtener benchmarks por defecto"""
        return KeywordBenchmark(
            customer_id='default',
            target_conv_rate=0.02,
            target_cpa=200000.00,
            benchmark_ctr=0.03,
            min_quality_score=5,
            industry_vertical='general'
        )

    def update_benchmarks(self, customer_id: str, benchmarks: KeywordBenchmark) -> bool:
        """Actualizar benchmarks de una cuenta"""
        try:
            data = {
                'customer_id': customer_id,
                'target_conv_rate': benchmarks.target_conv_rate,
                'target_cpa': benchmarks.target_cpa,
                'benchmark_ctr': benchmarks.benchmark_ctr,
                'min_quality_score': benchmarks.min_quality_score,
                'industry_vertical': benchmarks.industry_vertical,
                'seasonality_factor': benchmarks.seasonality_factor,
                'risk_tolerance': benchmarks.risk_tolerance,
                'updated_at': datetime.now().isoformat(),
                'created_by': benchmarks.created_by
            }
            
            response = self.client.table('keyword_benchmarks').upsert(data).execute()
            logger.info(f"Benchmarks actualizados para {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando benchmarks para {customer_id}: {e}")
            return False

    # ==================== KEYWORD METRICS ====================
    
    def bulk_insert_keyword_metrics(self, metrics: List[KeywordMetric]) -> bool:
        """Insertar métricas de keywords en lote"""
        try:
            data = []
            for metric in metrics:
                data.append({
                    'customer_id': metric.customer_id,
                    'campaign_id': metric.campaign_id,
                    'campaign_name': metric.campaign_name,
                    'ad_group_id': metric.ad_group_id,
                    'ad_group_name': metric.ad_group_name,
                    'keyword_text': metric.keyword_text,
                    'match_type': metric.match_type,
                    'status': metric.status,
                    'quality_score': metric.quality_score,
                    'impressions': metric.impressions,
                    'clicks': metric.clicks,
                    'cost_micros': metric.cost_micros,
                    'conversions': metric.conversions,
                    'conversions_value': metric.conversions_value,
                    'ctr': metric.ctr,
                    'average_cpc': metric.average_cpc,
                    'date': metric.date.isoformat(),
                    'extracted_at': datetime.now().isoformat()
                })
            
            # Insertar en lotes de 1000 para evitar límites
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                response = self.client.table('keyword_metrics_history').upsert(batch).execute()
            
            logger.info(f"Insertadas {len(metrics)} métricas de keywords")
            return True
            
        except Exception as e:
            logger.error(f"Error insertando métricas de keywords: {e}")
            return False

    def get_keyword_metrics(self, customer_id: str, days_back: int = 30) -> List[KeywordMetric]:
        """Obtener métricas de keywords para una cuenta"""
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).date()
            
            response = (self.client.table('keyword_metrics_history')
                       .select('*')
                       .eq('customer_id', customer_id)
                       .gte('date', start_date.isoformat())
                       .order('date', desc=True)
                       .execute())
            
            metrics = []
            for row in response.data:
                metrics.append(KeywordMetric(
                    customer_id=row['customer_id'],
                    campaign_id=row['campaign_id'],
                    campaign_name=row['campaign_name'],
                    ad_group_id=row['ad_group_id'],
                    ad_group_name=row['ad_group_name'],
                    keyword_text=row['keyword_text'],
                    match_type=row['match_type'],
                    status=row['status'],
                    quality_score=row.get('quality_score'),
                    impressions=row['impressions'],
                    clicks=row['clicks'],
                    cost_micros=row['cost_micros'],
                    conversions=float(row['conversions']),
                    conversions_value=float(row['conversions_value']),
                    ctr=float(row['ctr']) if row.get('ctr') else None,
                    average_cpc=float(row['average_cpc']) if row.get('average_cpc') else None,
                    date=datetime.fromisoformat(row['date']).date(),
                    extracted_at=datetime.fromisoformat(row['extracted_at'].replace('Z', '+00:00')) if row.get('extracted_at') else None
                ))
            
            logger.info(f"Obtenidas {len(metrics)} métricas para {customer_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas para {customer_id}: {e}")
            return []

    # ==================== HEALTH SCORES ====================
    
    def bulk_insert_health_scores(self, scores: List[KeywordHealthScore]) -> bool:
        """Insertar health scores en lote"""
        try:
            data = []
            for score in scores:
                data.append({
                    'customer_id': score.customer_id,
                    'campaign_id': score.campaign_id,
                    'ad_group_id': score.ad_group_id,
                    'keyword_text': score.keyword_text,
                    'health_score': score.health_score,
                    'conv_rate_score': score.conv_rate_score,
                    'cpa_score': score.cpa_score,
                    'ctr_score': score.ctr_score,
                    'confidence_score': score.confidence_score,
                    'quality_score_points': score.quality_score_points,
                    'health_category': score.health_category,
                    'recommended_action': score.recommended_action,
                    'action_priority': score.action_priority,
                    'data_period_start': score.data_period_start.isoformat() if score.data_period_start else None,
                    'data_period_end': score.data_period_end.isoformat() if score.data_period_end else None,
                    'total_spend': score.total_spend,
                    'total_conversions': score.total_conversions,
                    'total_clicks': score.total_clicks,
                    'calculated_at': datetime.now().isoformat()
                })
            
            # Insertar en lotes
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                response = self.client.table('keyword_health_scores').upsert(batch).execute()
            
            logger.info(f"Insertados {len(scores)} health scores")
            return True
            
        except Exception as e:
            logger.error(f"Error insertando health scores: {e}")
            return False

    def get_latest_health_scores(self, customer_id: str, limit: int = 1000) -> List[KeywordHealthScore]:
        """Obtener los health scores más recientes para una cuenta"""
        try:
            response = (self.client.table('keyword_health_scores')
                       .select('*')
                       .eq('customer_id', customer_id)
                       .order('calculated_at', desc=True)
                       .limit(limit)
                       .execute())
            
            scores = []
            for row in response.data:
                scores.append(KeywordHealthScore(
                    customer_id=row['customer_id'],
                    campaign_id=row['campaign_id'],
                    ad_group_id=row['ad_group_id'],
                    keyword_text=row['keyword_text'],
                    health_score=float(row['health_score']),
                    conv_rate_score=float(row['conv_rate_score']),
                    cpa_score=float(row['cpa_score']),
                    ctr_score=float(row['ctr_score']),
                    confidence_score=float(row['confidence_score']),
                    quality_score_points=float(row['quality_score_points']),
                    health_category=row['health_category'],
                    recommended_action=row['recommended_action'],
                    action_priority=int(row['action_priority']),
                    data_period_start=datetime.fromisoformat(row['data_period_start']).date() if row.get('data_period_start') else None,
                    data_period_end=datetime.fromisoformat(row['data_period_end']).date() if row.get('data_period_end') else None,
                    total_spend=float(row['total_spend']) if row.get('total_spend') else None,
                    total_conversions=float(row['total_conversions']) if row.get('total_conversions') else None,
                    total_clicks=int(row['total_clicks']) if row.get('total_clicks') else None,
                    calculated_at=datetime.fromisoformat(row['calculated_at'].replace('Z', '+00:00')) if row.get('calculated_at') else None
                ))
            
            logger.info(f"Obtenidos {len(scores)} health scores para {customer_id}")
            return scores
            
        except Exception as e:
            logger.error(f"Error obteniendo health scores para {customer_id}: {e}")
            return []

    def get_health_scores(self, customer_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Obtener health scores para una cuenta en formato de diccionario
        Compatible con la página de Keyword Health
        """
        try:
            # Calcular ventana basada en fecha de cálculo
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Filtrar por calculated_at para recuperar scores recientes
            response = (self.client.table('keyword_health_scores')
                       .select('*')
                       .eq('customer_id', customer_id)
                       .gte('calculated_at', start_date.isoformat())
                       .order('calculated_at', desc=True)
                       .execute())
            
            # Fallback: si no hay datos recientes, traer los últimos disponibles
            if not response.data:
                logger.warning(f"No health scores encontrados en últimos {days_back} días para {customer_id}, buscando últimos disponibles")
                response = (self.client.table('keyword_health_scores')
                           .select('*')
                           .eq('customer_id', customer_id)
                           .order('calculated_at', desc=True)
                           .limit(1000)
                           .execute())
            
            health_scores = []
            for row in (response.data or []):
                try:
                    health_scores.append({
                        'customer_id': row['customer_id'],
                        'campaign_id': str(row.get('campaign_id', '')),
                        'ad_group_id': str(row.get('ad_group_id', '')),
                        'keyword_text': row.get('keyword_text', ''),
                        'health_score': float(row.get('health_score', 0)),
                        'conv_rate_score': float(row.get('conv_rate_score', 0)),
                        'cpa_score': float(row.get('cpa_score', 0)),
                        'ctr_score': float(row.get('ctr_score', 0)),
                        'confidence_score': float(row.get('confidence_score', 0)),
                        'quality_score_points': float(row.get('quality_score_points', 0)),
                        'health_category': row.get('health_category', 'warning'),
                        'recommended_action': row.get('recommended_action', 'monitor'),
                        'action_priority': int(row.get('action_priority', 5)),
                        'data_period_start': row.get('data_period_start'),
                        'data_period_end': row.get('data_period_end'),
                        'total_spend': float(row.get('total_spend', 0)) if row.get('total_spend') is not None else 0,
                        'total_conversions': float(row.get('total_conversions', 0)) if row.get('total_conversions') is not None else 0,
                        'total_clicks': int(row.get('total_clicks', 0)) if row.get('total_clicks') is not None else 0,
                        'calculated_at': row.get('calculated_at')
                    })
                except Exception as parse_error:
                    logger.error(f"Error parseando fila de health score: {parse_error}")
                    continue
            
            logger.info(f"Obtenidos {len(health_scores)} health scores para {customer_id} (últimos {days_back} días)")
            return health_scores
            
        except Exception as e:
            logger.error(f"Error obteniendo salud scores para {customer_id}: {e}")
            return []

    def get_recent_actions(self, customer_id: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Obtener acciones de optimización recientes para una cuenta
        """
        try:
            # Calcular fecha de inicio
            start_date = datetime.now() - timedelta(days=days_back)
            
            response = (self.client.table('optimization_actions')
                       .select('*')
                       .eq('customer_id', customer_id)
                       .gte('created_at', start_date.isoformat())
                       .order('created_at', desc=True)
                       .execute())
            
            actions = []
            for row in response.data:
                actions.append({
                    'id': row.get('id'),
                    'customer_id': row['customer_id'],
                    'execution_id': row['execution_id'],
                    'campaign_id': row['campaign_id'],
                    'ad_group_id': row['ad_group_id'],
                    'keyword_text': row['keyword_text'],
                    'action_type': row['action_type'],
                    'old_bid': float(row['old_bid']) if row.get('old_bid') else None,
                    'new_bid': float(row['new_bid']) if row.get('new_bid') else None,
                    'bid_change_percent': float(row['bid_change_percent']) if row.get('bid_change_percent') else None,
                    'justification': row.get('justification'),
                    'health_score_before': float(row['health_score_before']) if row.get('health_score_before') else None,
                    'risk_level': row.get('risk_level', 'medium'),
                    'status': row.get('status', 'pending'),
                    'executed_by': row.get('executed_by'),
                    'google_ads_operation_id': row.get('google_ads_operation_id'),
                    'api_response': row.get('api_response'),
                    'error_message': row.get('error_message'),
                    'created_at': row.get('created_at'),
                    'executed_at': row.get('executed_at')
                })
            
            logger.info(f"Obtenidas {len(actions)} acciones recientes para {customer_id} (últimos {days_back} días)")
            return actions
            
        except Exception as e:
            logger.error(f"Error obteniendo acciones recientes para {customer_id}: {e}")
            return []

    # ==================== OPTIMIZATION ACTIONS ====================
    
    def insert_optimization_actions(self, actions: List[OptimizationAction]) -> bool:
        """Insertar acciones de optimización"""
        try:
            data = []
            for action in actions:
                data.append({
                    'customer_id': action.customer_id,
                    'execution_id': action.execution_id,
                    'campaign_id': action.campaign_id,
                    'ad_group_id': action.ad_group_id,
                    'keyword_text': action.keyword_text,
                    'action_type': action.action_type,
                    'old_bid': action.old_bid,
                    'new_bid': action.new_bid,
                    'bid_change_percent': action.bid_change_percent,
                    'justification': action.justification,
                    'health_score_before': action.health_score_before,
                    'risk_level': action.risk_level,
                    'status': action.status,
                    'executed_by': action.executed_by,
                    'google_ads_operation_id': action.google_ads_operation_id,
                    'api_response': action.api_response,
                    'error_message': action.error_message,
                    'scheduled_at': datetime.now().isoformat()
                })
            
            response = self.client.table('optimization_actions').insert(data).execute()
            logger.info(f"Insertadas {len(actions)} acciones de optimización")
            return True
            
        except Exception as e:
            logger.error(f"Error insertando acciones de optimización: {e}")
            return False

    def update_action_status(self, action_id: int, status: str, executed_at: datetime = None, 
                           google_ads_operation_id: str = None, api_response: str = None, 
                           error_message: str = None) -> bool:
        """Actualizar el estado de una acción"""
        try:
            data = {
                'status': status,
                'executed_at': (executed_at or datetime.now()).isoformat(),
                'google_ads_operation_id': google_ads_operation_id,
                'api_response': api_response,
                'error_message': error_message
            }
            
            response = self.client.table('optimization_actions').update(data).eq('id', action_id).execute()
            logger.info(f"Estado de acción {action_id} actualizado a {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando estado de acción {action_id}: {e}")
            return False

    def get_pending_actions(self, customer_id: str = None) -> List[Dict]:
        """Obtener acciones pendientes de ejecución"""
        try:
            query = self.client.table('optimization_actions').select('*').eq('status', 'pending')
            if customer_id:
                query = query.eq('customer_id', customer_id)
            
            response = query.execute()
            logger.info(f"Obtenidas {len(response.data)} acciones pendientes")
            return response.data
            
        except Exception as e:
            logger.error(f"Error obteniendo acciones pendientes: {e}")
            return []

    # ==================== ANALYTICS & REPORTING ====================
    
    def get_health_score_summary(self, customer_id: str) -> Dict[str, Any]:
        """Obtener resumen de health scores por categoría"""
        try:
            response = (self.client.table('keyword_health_scores')
                       .select('health_category, count(*)')
                       .eq('customer_id', customer_id)
                       .execute())
            
            summary = {
                'excellent': 0,
                'good': 0,
                'warning': 0,
                'critical': 0,
                'total': 0
            }
            
            for row in response.data:
                category = row.get('health_category', 'warning')
                count = row.get('count', 0)
                summary[category] = count
                summary['total'] += count
            
            return summary
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de health scores: {e}")
            return {'excellent': 0, 'good': 0, 'warning': 0, 'critical': 0, 'total': 0}

    def get_vampire_keywords(self, customer_id: str, min_spend: float = 200000, 
                           min_clicks: int = 20) -> List[Dict]:
        """Obtener keywords vampiro (alto gasto, cero conversiones)"""
        try:
            # Obtener keywords con alto gasto y cero conversiones
            response = (self.client.table('keyword_health_scores')
                       .select('*')
                       .eq('customer_id', customer_id)
                       .gte('total_spend', min_spend)
                       .gte('total_clicks', min_clicks)
                       .eq('total_conversions', 0)
                       .order('total_spend', desc=True)
                       .execute())
            
            logger.info(f"Encontrados {len(response.data)} keywords vampiro para {customer_id}")
            return response.data
            
        except Exception as e:
            logger.error(f"Error obteniendo keywords vampiro: {e}")
            return []

    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Limpiar datos antiguos para mantener performance"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()
            
            # Limpiar métricas antiguas
            response1 = (self.client.table('keyword_metrics_history')
                        .delete()
                        .lt('date', cutoff_date.isoformat())
                        .execute())
            
            # Limpiar health scores antiguos
            response2 = (self.client.table('keyword_health_scores')
                        .delete()
                        .lt('calculated_at', cutoff_date.isoformat())
                        .execute())
            
            logger.info(f"Limpieza de datos completada. Eliminados datos anteriores a {cutoff_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error en limpieza de datos: {e}")
            return False