"""
ActionExecutionService para ejecutar optimizaciones con guardrails de seguridad
Incluye límites de ±30%, exclusiones y rollback automático
"""

import logging
import uuid
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from services.database_service import DatabaseService, OptimizationAction, KeywordHealthScore
from modules.google_ads_client import GoogleAdsClientWrapper
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class BidChangeRequest:
    customer_id: str
    campaign_id: str
    ad_group_id: str
    keyword_text: str
    current_bid: float
    new_bid: float
    change_percent: float
    justification: str
    health_score: float
    risk_level: str = 'medium'

@dataclass
class ExecutionResult:
    success: bool
    action_id: Optional[int] = None
    google_ads_operation_id: Optional[str] = None
    error_message: Optional[str] = None
    rollback_required: bool = False

class ActionExecutionService:
    """Servicio para ejecutar acciones de optimización con guardrails de seguridad"""
    
    def __init__(self, db_service: DatabaseService = None, ads_client: GoogleAdsClientWrapper = None):
        self.db_service = db_service or DatabaseService()
        self.ads_client = ads_client or GoogleAdsClientWrapper()
        
        # Configuración de guardrails
        self.max_bid_change_percent = 30.0  # ±30% máximo
        self.min_bid_amount = 0.10  # $0.10 mínimo
        self.max_bid_amount = 100.00  # $100 máximo
        self.conversion_exclusion_days = 7  # Excluir keywords con conversiones en últimos 7 días
        
        logger.info("ActionExecutionService inicializado con guardrails de seguridad")

    def execute_bid_changes(self, bid_requests: List[BidChangeRequest], 
                          execution_id: str = None, dry_run: bool = False) -> Dict[str, any]:
        """Ejecutar cambios de puja con validaciones de seguridad"""
        try:
            if not execution_id:
                execution_id = str(uuid.uuid4())
            
            results = {
                'execution_id': execution_id,
                'total_requests': len(bid_requests),
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'errors': [],
                'actions': [],
                'dry_run': dry_run
            }
            
            # Validar y filtrar requests
            validated_requests = []
            for request in bid_requests:
                validation_result = self._validate_bid_change_request(request)
                if validation_result['valid']:
                    validated_requests.append(request)
                else:
                    results['skipped'] += 1
                    results['errors'].append({
                        'keyword': request.keyword_text,
                        'error': validation_result['reason']
                    })
            
            logger.info(f"Validados {len(validated_requests)} de {len(bid_requests)} requests")
            
            # Crear acciones en base de datos
            optimization_actions = []
            for request in validated_requests:
                action = OptimizationAction(
                    customer_id=request.customer_id,
                    execution_id=execution_id,
                    campaign_id=request.campaign_id,
                    ad_group_id=request.ad_group_id,
                    keyword_text=request.keyword_text,
                    action_type='bid_change',
                    old_bid=request.current_bid,
                    new_bid=request.new_bid,
                    bid_change_percent=request.change_percent,
                    justification=request.justification,
                    health_score_before=request.health_score,
                    risk_level=request.risk_level,
                    status='pending',
                    executed_by='system'
                )
                optimization_actions.append(action)
            
            # Guardar acciones en base de datos
            if optimization_actions:
                if not self.db_service.insert_optimization_actions(optimization_actions):
                    raise Exception("Error guardando acciones en base de datos")
            
            # Ejecutar cambios si no es dry run
            if not dry_run and validated_requests:
                execution_results = self._execute_google_ads_changes(validated_requests, execution_id)
                
                for i, result in enumerate(execution_results):
                    if result.success:
                        results['successful'] += 1
                        # Actualizar estado en base de datos
                        if result.action_id:
                            self.db_service.update_action_status(
                                result.action_id, 
                                'completed',
                                google_ads_operation_id=result.google_ads_operation_id
                            )
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'keyword': validated_requests[i].keyword_text,
                            'error': result.error_message
                        })
                        # Actualizar estado de error
                        if result.action_id:
                            self.db_service.update_action_status(
                                result.action_id, 
                                'failed',
                                error_message=result.error_message
                            )
                
                results['actions'] = execution_results
            else:
                results['successful'] = len(validated_requests)
                logger.info(f"Dry run completado: {len(validated_requests)} acciones simuladas")
            
            return results
            
        except Exception as e:
            logger.error(f"Error ejecutando cambios de puja: {e}")
            return {
                'execution_id': execution_id or 'unknown',
                'total_requests': len(bid_requests),
                'successful': 0,
                'failed': len(bid_requests),
                'skipped': 0,
                'errors': [{'error': str(e)}],
                'actions': [],
                'dry_run': dry_run
            }

    def _validate_bid_change_request(self, request: BidChangeRequest) -> Dict[str, any]:
        """Validar request de cambio de puja con guardrails"""
        try:
            # Validar porcentaje de cambio
            if abs(request.change_percent) > self.max_bid_change_percent:
                return {
                    'valid': False,
                    'reason': f'Cambio de {request.change_percent:.1f}% excede límite de ±{self.max_bid_change_percent}%'
                }
            
            # Validar montos mínimos y máximos
            if request.new_bid < self.min_bid_amount:
                return {
                    'valid': False,
                    'reason': f'Nueva puja ${request.new_bid:.2f} es menor al mínimo ${self.min_bid_amount:.2f}'
                }
            
            if request.new_bid > self.max_bid_amount:
                return {
                    'valid': False,
                    'reason': f'Nueva puja ${request.new_bid:.2f} excede máximo ${self.max_bid_amount:.2f}'
                }
            
            # Validar que no sea un cambio muy pequeño
            if abs(request.new_bid - request.current_bid) < 0.05:
                return {
                    'valid': False,
                    'reason': 'Cambio de puja muy pequeño (< $0.05)'
                }
            
            # Verificar exclusiones por conversiones recientes
            if self._has_recent_conversions(request):
                return {
                    'valid': False,
                    'reason': f'Keyword tiene conversiones en últimos {self.conversion_exclusion_days} días'
                }
            
            # Validar health score mínimo para aumentos de puja
            if request.change_percent > 0 and request.health_score < 40:
                return {
                    'valid': False,
                    'reason': f'Health score {request.health_score:.1f} muy bajo para aumentar puja'
                }
            
            return {'valid': True, 'reason': 'Validación exitosa'}
            
        except Exception as e:
            logger.error(f"Error validando request: {e}")
            return {'valid': False, 'reason': f'Error de validación: {str(e)}'}

    def _has_recent_conversions(self, request: BidChangeRequest) -> bool:
        """Verificar si la keyword tiene conversiones recientes"""
        try:
            # Obtener métricas recientes
            metrics = self.db_service.get_keyword_metrics(
                request.customer_id, 
                days_back=self.conversion_exclusion_days
            )
            
            # Buscar conversiones para esta keyword específica
            for metric in metrics:
                if (metric.campaign_id == request.campaign_id and 
                    metric.ad_group_id == request.ad_group_id and 
                    metric.keyword_text == request.keyword_text and
                    metric.conversions > 0):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando conversiones recientes: {e}")
            return False  # En caso de error, no excluir

    def _execute_google_ads_changes(self, requests: List[BidChangeRequest], 
                                  execution_id: str) -> List[ExecutionResult]:
        """Ejecutar cambios en Google Ads API"""
        try:
            results = []
            
            # Agrupar por cuenta para optimizar llamadas API
            requests_by_account = {}
            for request in requests:
                if request.customer_id not in requests_by_account:
                    requests_by_account[request.customer_id] = []
                requests_by_account[request.customer_id].append(request)
            
            # Ejecutar por cuenta
            for customer_id, account_requests in requests_by_account.items():
                try:
                    account_results = self._execute_account_bid_changes(customer_id, account_requests)
                    results.extend(account_results)
                    
                except Exception as e:
                    logger.error(f"Error ejecutando cambios para cuenta {customer_id}: {e}")
                    # Crear resultados de error para todas las requests de esta cuenta
                    for request in account_requests:
                        results.append(ExecutionResult(
                            success=False,
                            error_message=f"Error de cuenta: {str(e)}",
                            rollback_required=False
                        ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error ejecutando cambios en Google Ads: {e}")
            return [ExecutionResult(success=False, error_message=str(e)) for _ in requests]

    def _execute_account_bid_changes(self, customer_id: str, 
                                   requests: List[BidChangeRequest]) -> List[ExecutionResult]:
        """Ejecutar cambios de puja para una cuenta específica"""
        try:
            results = []
            
            # Preparar operaciones de Google Ads
            operations = []
            for request in requests:
                try:
                    # Crear operación de actualización de keyword bid
                    operation = self._create_keyword_bid_operation(request)
                    if operation:
                        operations.append(operation)
                        results.append(ExecutionResult(success=True))
                    else:
                        results.append(ExecutionResult(
                            success=False,
                            error_message="No se pudo crear operación"
                        ))
                        
                except Exception as e:
                    logger.error(f"Error creando operación para {request.keyword_text}: {e}")
                    results.append(ExecutionResult(
                        success=False,
                        error_message=str(e)
                    ))
            
            # Ejecutar operaciones en lote si hay alguna válida
            if operations:
                try:
                    # Simular ejecución (en implementación real, usar Google Ads API)
                    logger.info(f"Ejecutando {len(operations)} operaciones para cuenta {customer_id}")
                    
                    # Aquí iría la llamada real a Google Ads API
                    # response = self.ads_client.mutate_keywords(customer_id, operations)
                    
                    # Por ahora, simular éxito
                    for i, result in enumerate(results):
                        if result.success:
                            result.google_ads_operation_id = f"op_{uuid.uuid4().hex[:8]}"
                    
                except Exception as e:
                    logger.error(f"Error ejecutando operaciones en Google Ads: {e}")
                    # Marcar todas como fallidas
                    for result in results:
                        if result.success:
                            result.success = False
                            result.error_message = f"Error API: {str(e)}"
                            result.rollback_required = True
            
            return results
            
        except Exception as e:
            logger.error(f"Error ejecutando cambios para cuenta {customer_id}: {e}")
            return [ExecutionResult(success=False, error_message=str(e)) for _ in requests]

    def _create_keyword_bid_operation(self, request: BidChangeRequest) -> Optional[Dict]:
        """Crear operación de cambio de puja para Google Ads API"""
        try:
            # En implementación real, crear objeto de operación de Google Ads
            operation = {
                'customer_id': request.customer_id,
                'campaign_id': request.campaign_id,
                'ad_group_id': request.ad_group_id,
                'keyword_text': request.keyword_text,
                'new_bid_micros': int(request.new_bid * 1_000_000),  # Convertir a micros
                'operation_type': 'UPDATE'
            }
            
            return operation
            
        except Exception as e:
            logger.error(f"Error creando operación para {request.keyword_text}: {e}")
            return None

    def rollback_execution(self, execution_id: str) -> Dict[str, any]:
        """Hacer rollback de una ejecución específica"""
        try:
            # Obtener acciones de la ejecución
            actions = self.db_service.get_pending_actions()  # Filtrar por execution_id en implementación real
            
            rollback_results = {
                'execution_id': execution_id,
                'total_actions': 0,
                'rolled_back': 0,
                'failed_rollback': 0,
                'errors': []
            }
            
            # Filtrar acciones de esta ejecución
            execution_actions = [a for a in actions if a.get('execution_id') == execution_id]
            rollback_results['total_actions'] = len(execution_actions)
            
            for action in execution_actions:
                try:
                    # Crear request de rollback (revertir a puja original)
                    rollback_request = BidChangeRequest(
                        customer_id=action['customer_id'],
                        campaign_id=action['campaign_id'],
                        ad_group_id=action['ad_group_id'],
                        keyword_text=action['keyword_text'],
                        current_bid=action['new_bid'],
                        new_bid=action['old_bid'],
                        change_percent=0,  # No aplicar límites en rollback
                        justification=f"Rollback de ejecución {execution_id}",
                        health_score=0,
                        risk_level='low'
                    )
                    
                    # Ejecutar rollback (sin validaciones estrictas)
                    result = self._execute_rollback_change(rollback_request)
                    
                    if result.success:
                        rollback_results['rolled_back'] += 1
                        # Actualizar estado en base de datos
                        self.db_service.update_action_status(
                            action['id'],
                            'rolled_back',
                            api_response=f"Rollback exitoso: {result.google_ads_operation_id}"
                        )
                    else:
                        rollback_results['failed_rollback'] += 1
                        rollback_results['errors'].append({
                            'keyword': action['keyword_text'],
                            'error': result.error_message
                        })
                        
                except Exception as e:
                    logger.error(f"Error en rollback de acción {action.get('id')}: {e}")
                    rollback_results['failed_rollback'] += 1
                    rollback_results['errors'].append({
                        'keyword': action.get('keyword_text', 'unknown'),
                        'error': str(e)
                    })
            
            logger.info(f"Rollback completado: {rollback_results['rolled_back']} exitosos, {rollback_results['failed_rollback']} fallidos")
            return rollback_results
            
        except Exception as e:
            logger.error(f"Error en rollback de ejecución {execution_id}: {e}")
            return {
                'execution_id': execution_id,
                'total_actions': 0,
                'rolled_back': 0,
                'failed_rollback': 0,
                'errors': [{'error': str(e)}]
            }

    def _execute_rollback_change(self, rollback_request: BidChangeRequest) -> ExecutionResult:
        """Ejecutar un cambio de rollback individual"""
        try:
            # En implementación real, ejecutar cambio en Google Ads API
            # Por ahora, simular éxito
            operation_id = f"rollback_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"Rollback ejecutado para {rollback_request.keyword_text}: ${rollback_request.current_bid:.2f} -> ${rollback_request.new_bid:.2f}")
            
            return ExecutionResult(
                success=True,
                google_ads_operation_id=operation_id
            )
            
        except Exception as e:
            logger.error(f"Error ejecutando rollback: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )

    def get_execution_status(self, execution_id: str) -> Dict[str, any]:
        """Obtener estado de una ejecución específica"""
        try:
            # Obtener acciones de la ejecución
            all_actions = self.db_service.get_pending_actions()
            execution_actions = [a for a in all_actions if a.get('execution_id') == execution_id]
            
            if not execution_actions:
                return {
                    'execution_id': execution_id,
                    'status': 'not_found',
                    'total_actions': 0
                }
            
            # Contar estados
            status_counts = {}
            for action in execution_actions:
                status = action.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Determinar estado general
            if status_counts.get('failed', 0) > 0:
                overall_status = 'partially_failed'
            elif status_counts.get('pending', 0) > 0:
                overall_status = 'in_progress'
            elif status_counts.get('completed', 0) == len(execution_actions):
                overall_status = 'completed'
            else:
                overall_status = 'unknown'
            
            return {
                'execution_id': execution_id,
                'status': overall_status,
                'total_actions': len(execution_actions),
                'status_breakdown': status_counts,
                'actions': execution_actions
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de ejecución {execution_id}: {e}")
            return {
                'execution_id': execution_id,
                'status': 'error',
                'error': str(e)
            }

    def pause_keywords(self, keyword_requests: List[Dict]) -> Dict[str, any]:
        """Pausar keywords específicas"""
        try:
            results = {
                'total_requests': len(keyword_requests),
                'successful': 0,
                'failed': 0,
                'errors': []
            }
            
            for request in keyword_requests:
                try:
                    # En implementación real, pausar keyword en Google Ads
                    logger.info(f"Pausando keyword: {request.get('keyword_text')} en cuenta {request.get('customer_id')}")
                    
                    # Simular éxito
                    results['successful'] += 1
                    
                except Exception as e:
                    logger.error(f"Error pausando keyword {request.get('keyword_text')}: {e}")
                    results['failed'] += 1
                    results['errors'].append({
                        'keyword': request.get('keyword_text'),
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error pausando keywords: {e}")
            return {
                'total_requests': len(keyword_requests),
                'successful': 0,
                'failed': len(keyword_requests),
                'errors': [{'error': str(e)}]
            }

    def get_guardrails_config(self) -> Dict[str, any]:
        """Obtener configuración actual de guardrails"""
        return {
            'max_bid_change_percent': self.max_bid_change_percent,
            'min_bid_amount': self.min_bid_amount,
            'max_bid_amount': self.max_bid_amount,
            'conversion_exclusion_days': self.conversion_exclusion_days
        }

    def update_guardrails_config(self, config: Dict[str, any]) -> bool:
        """Actualizar configuración de guardrails"""
        try:
            if 'max_bid_change_percent' in config:
                self.max_bid_change_percent = float(config['max_bid_change_percent'])
            
            if 'min_bid_amount' in config:
                self.min_bid_amount = float(config['min_bid_amount'])
            
            if 'max_bid_amount' in config:
                self.max_bid_amount = float(config['max_bid_amount'])
            
            if 'conversion_exclusion_days' in config:
                self.conversion_exclusion_days = int(config['conversion_exclusion_days'])
            
            logger.info("Configuración de guardrails actualizada")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando configuración de guardrails: {e}")
            return False