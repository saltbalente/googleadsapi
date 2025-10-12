"""
MCCManagementService para gestión de cuentas MCC
Auto-detección de nuevas cuentas y gestión de benchmarks personalizados
"""

import logging
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from services.database_service import DatabaseService, MCCAccount, KeywordBenchmark
from modules.google_ads_client import GoogleAdsClientWrapper
from utils.logger import get_logger

logger = get_logger(__name__)

from modules.google_ads_client import GoogleAdsClientWrapper

class MCCManagementService:
    """Servicio para gestión automática de cuentas MCC y benchmarks"""
    
    def __init__(self, db_service: DatabaseService = None, ads_client: GoogleAdsClientWrapper = None):
        self.db_service = db_service or DatabaseService()
        self.ads_client = ads_client or GoogleAdsClientWrapper()
        logger.info("MCCManagementService inicializado")

    def discover_and_sync_accounts(self, manager_customer_id: str = None) -> Dict[str, int]:
        """Descubrir y sincronizar todas las cuentas bajo un MCC"""
        try:
            results = {
                'discovered': 0,
                'updated': 0,
                'errors': 0,
                'new_accounts': []
            }
            
            # Obtener cuentas existentes en la base de datos
            existing_accounts = {acc.customer_id for acc in self.db_service.get_all_accounts(active_only=False)}
            
            # Descubrir cuentas desde Google Ads API
            discovered_accounts = self._discover_accounts_from_api(manager_customer_id)
            
            for account_info in discovered_accounts:
                try:
                    customer_id = account_info['customer_id']
                    
                    # Crear objeto MCCAccount
                    account = MCCAccount(
                        customer_id=customer_id,
                        account_name=account_info.get('account_name', f'Account {customer_id}'),
                        currency_code=account_info.get('currency_code', 'USD'),
                        time_zone=account_info.get('time_zone', 'America/New_York'),
                        is_active=account_info.get('is_active', True),
                        account_type=account_info.get('account_type', 'child'),
                        parent_customer_id=account_info.get('parent_customer_id'),
                        discovered_at=datetime.now() if customer_id not in existing_accounts else None
                    )
                    
                    # Insertar o actualizar cuenta
                    if self.db_service.upsert_account(account):
                        if customer_id not in existing_accounts:
                            results['discovered'] += 1
                            results['new_accounts'].append(customer_id)
                            logger.info(f"Nueva cuenta descubierta: {customer_id}")
                            
                            # Crear benchmarks por defecto para nueva cuenta
                            self._create_default_benchmarks(customer_id, account_info)
                        else:
                            results['updated'] += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando cuenta {account_info.get('customer_id', 'unknown')}: {e}")
                    results['errors'] += 1
            
            logger.info(f"Sincronización completada: {results['discovered']} nuevas, {results['updated']} actualizadas, {results['errors']} errores")
            return results
            
        except Exception as e:
            logger.error(f"Error en descubrimiento de cuentas: {e}")
            return {'discovered': 0, 'updated': 0, 'errors': 1, 'new_accounts': []}

    def _discover_accounts_from_api(self, manager_customer_id: str = None) -> List[Dict]:
        """Descubrir cuentas desde Google Ads API"""
        try:
            discovered_accounts = []
            
            # Si no se especifica manager, usar todas las cuentas accesibles
            if not manager_customer_id:
                accessible_customers = self.ads_client.get_accessible_customers()
                customer_ids = [customer.id for customer in accessible_customers]
            else:
                # Obtener cuentas hijas del manager específico
                customer_ids = self._get_child_accounts(manager_customer_id)
            
            for customer_id in customer_ids:
                try:
                    # Obtener información detallada de la cuenta
                    account_info = self._get_account_details(customer_id)
                    if account_info:
                        discovered_accounts.append(account_info)
                        
                except Exception as e:
                    logger.warning(f"No se pudo obtener información de la cuenta {customer_id}: {e}")
                    continue
            
            logger.info(f"Descubiertas {len(discovered_accounts)} cuentas desde API")
            return discovered_accounts
            
        except Exception as e:
            logger.error(f"Error descubriendo cuentas desde API: {e}")
            return []

    def _get_child_accounts(self, manager_customer_id: str) -> List[str]:
        """Obtener cuentas hijas de un manager account"""
        try:
            query = """
                SELECT 
                    customer_client.id,
                    customer_client.descriptive_name,
                    customer_client.currency_code,
                    customer_client.time_zone,
                    customer_client.status
                FROM customer_client
                WHERE customer_client.manager = FALSE
            """
            
            response = self.ads_client.search(manager_customer_id, query)
            child_accounts = []
            
            for row in response:
                customer_client = row.customer_client
                if customer_client.status.name == 'ENABLED':
                    child_accounts.append(str(customer_client.id))
            
            logger.info(f"Encontradas {len(child_accounts)} cuentas hijas para manager {manager_customer_id}")
            return child_accounts
            
        except Exception as e:
            logger.error(f"Error obteniendo cuentas hijas para {manager_customer_id}: {e}")
            return []

    def _get_account_details(self, customer_id: str) -> Optional[Dict]:
        """Obtener detalles de una cuenta específica"""
        try:
            query = """
                SELECT 
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.status,
                    customer.manager
                FROM customer
                LIMIT 1
            """
            
            response = self.ads_client.search(customer_id, query)
            
            for row in response:
                customer = row.customer
                return {
                    'customer_id': str(customer.id),
                    'account_name': customer.descriptive_name or f'Account {customer.id}',
                    'currency_code': customer.currency_code or 'USD',
                    'time_zone': customer.time_zone or 'America/New_York',
                    'is_active': customer.status.name == 'ENABLED',
                    'account_type': 'manager' if customer.manager else 'child'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles de cuenta {customer_id}: {e}")
            return None

    def _create_default_benchmarks(self, customer_id: str, account_info: Dict):
        """Crear benchmarks por defecto para una nueva cuenta"""
        try:
            # Determinar vertical de industria basado en el nombre de la cuenta
            industry_vertical = self._detect_industry_vertical(account_info.get('account_name', ''))
            
            # Obtener benchmarks base según la industria
            base_benchmarks = self._get_industry_benchmarks(industry_vertical)
            
            # Ajustar por moneda si no es USD
            currency_code = account_info.get('currency_code', 'USD')
            if currency_code != 'USD':
                base_benchmarks = self._adjust_benchmarks_for_currency(base_benchmarks, currency_code)
            
            # Crear benchmarks personalizados
            benchmarks = KeywordBenchmark(
                customer_id=customer_id,
                target_conv_rate=base_benchmarks['target_conv_rate'],
                target_cpa=base_benchmarks['target_cpa'],
                benchmark_ctr=base_benchmarks['benchmark_ctr'],
                min_quality_score=base_benchmarks['min_quality_score'],
                industry_vertical=industry_vertical,
                seasonality_factor=1.0,
                risk_tolerance='moderate',
                created_by='auto_discovery'
            )
            
            # Guardar en base de datos
            if self.db_service.update_benchmarks(customer_id, benchmarks):
                logger.info(f"Benchmarks por defecto creados para {customer_id} (industria: {industry_vertical})")
            else:
                logger.error(f"Error creando benchmarks para {customer_id}")
                
        except Exception as e:
            logger.error(f"Error creando benchmarks por defecto para {customer_id}: {e}")

    def _detect_industry_vertical(self, account_name: str) -> str:
        """Detectar vertical de industria basado en el nombre de la cuenta"""
        try:
            account_name_lower = account_name.lower()
            
            # Mapeo de palabras clave a verticales
            industry_keywords = {
                'ecommerce': ['shop', 'store', 'retail', 'ecommerce', 'commerce', 'tienda'],
                'saas': ['software', 'saas', 'app', 'platform', 'tech', 'cloud'],
                'healthcare': ['health', 'medical', 'clinic', 'hospital', 'pharma', 'salud'],
                'finance': ['bank', 'finance', 'insurance', 'loan', 'credit', 'fintech'],
                'education': ['school', 'university', 'education', 'course', 'learning'],
                'real_estate': ['real estate', 'property', 'homes', 'realty', 'inmobiliaria'],
                'automotive': ['auto', 'car', 'vehicle', 'automotive', 'dealer'],
                'travel': ['travel', 'hotel', 'tourism', 'vacation', 'viajes'],
                'food': ['restaurant', 'food', 'delivery', 'catering', 'comida'],
                'fitness': ['gym', 'fitness', 'health', 'workout', 'sport']
            }
            
            for vertical, keywords in industry_keywords.items():
                if any(keyword in account_name_lower for keyword in keywords):
                    return vertical
            
            return 'general'  # Por defecto
            
        except Exception as e:
            logger.error(f"Error detectando vertical de industria: {e}")
            return 'general'

    def _get_industry_benchmarks(self, industry_vertical: str) -> Dict:
        """Obtener benchmarks base por industria"""
        industry_benchmarks = {
            'ecommerce': {
                'target_conv_rate': 0.025,  # 2.5%
                'target_cpa': 150000.00,    # $150 USD en micros
                'benchmark_ctr': 0.035,     # 3.5%
                'min_quality_score': 6
            },
            'saas': {
                'target_conv_rate': 0.015,  # 1.5%
                'target_cpa': 300000.00,    # $300 USD en micros
                'benchmark_ctr': 0.025,     # 2.5%
                'min_quality_score': 7
            },
            'healthcare': {
                'target_conv_rate': 0.030,  # 3.0%
                'target_cpa': 200000.00,    # $200 USD en micros
                'benchmark_ctr': 0.040,     # 4.0%
                'min_quality_score': 6
            },
            'finance': {
                'target_conv_rate': 0.020,  # 2.0%
                'target_cpa': 250000.00,    # $250 USD en micros
                'benchmark_ctr': 0.030,     # 3.0%
                'min_quality_score': 7
            },
            'education': {
                'target_conv_rate': 0.035,  # 3.5%
                'target_cpa': 100000.00,    # $100 USD en micros
                'benchmark_ctr': 0.045,     # 4.5%
                'min_quality_score': 6
            },
            'real_estate': {
                'target_conv_rate': 0.040,  # 4.0%
                'target_cpa': 180000.00,    # $180 USD en micros
                'benchmark_ctr': 0.050,     # 5.0%
                'min_quality_score': 6
            },
            'automotive': {
                'target_conv_rate': 0.025,  # 2.5%
                'target_cpa': 220000.00,    # $220 USD en micros
                'benchmark_ctr': 0.035,     # 3.5%
                'min_quality_score': 6
            },
            'travel': {
                'target_conv_rate': 0.020,  # 2.0%
                'target_cpa': 120000.00,    # $120 USD en micros
                'benchmark_ctr': 0.040,     # 4.0%
                'min_quality_score': 6
            },
            'food': {
                'target_conv_rate': 0.030,  # 3.0%
                'target_cpa': 80000.00,     # $80 USD en micros
                'benchmark_ctr': 0.045,     # 4.5%
                'min_quality_score': 5
            },
            'fitness': {
                'target_conv_rate': 0.025,  # 2.5%
                'target_cpa': 150000.00,    # $150 USD en micros
                'benchmark_ctr': 0.040,     # 4.0%
                'min_quality_score': 6
            }
        }
        
        return industry_benchmarks.get(industry_vertical, {
            'target_conv_rate': 0.020,  # 2.0% por defecto
            'target_cpa': 200000.00,    # $200 USD en micros
            'benchmark_ctr': 0.030,     # 3.0%
            'min_quality_score': 5
        })

    def _adjust_benchmarks_for_currency(self, benchmarks: Dict, currency_code: str) -> Dict:
        """Ajustar benchmarks por moneda"""
        try:
            # Factores de conversión aproximados (en la práctica, usar API de cambio)
            currency_factors = {
                'EUR': 0.85,    # 1 USD = 0.85 EUR aproximadamente
                'GBP': 0.75,    # 1 USD = 0.75 GBP aproximadamente
                'CAD': 1.25,    # 1 USD = 1.25 CAD aproximadamente
                'AUD': 1.35,    # 1 USD = 1.35 AUD aproximadamente
                'MXN': 18.0,    # 1 USD = 18 MXN aproximadamente
                'BRL': 5.0,     # 1 USD = 5 BRL aproximadamente
                'JPY': 110.0,   # 1 USD = 110 JPY aproximadamente
            }
            
            factor = currency_factors.get(currency_code, 1.0)
            
            # Ajustar solo el CPA target (en micros)
            adjusted_benchmarks = benchmarks.copy()
            adjusted_benchmarks['target_cpa'] = benchmarks['target_cpa'] * factor
            
            return adjusted_benchmarks
            
        except Exception as e:
            logger.error(f"Error ajustando benchmarks por moneda {currency_code}: {e}")
            return benchmarks

    def update_account_benchmarks(self, customer_id: str, benchmarks_data: Dict) -> bool:
        """Actualizar benchmarks de una cuenta específica"""
        try:
            # Validar datos de entrada
            required_fields = ['target_conv_rate', 'target_cpa', 'benchmark_ctr', 'min_quality_score']
            for field in required_fields:
                if field not in benchmarks_data:
                    logger.error(f"Campo requerido faltante: {field}")
                    return False
            
            # Crear objeto KeywordBenchmark
            benchmarks = KeywordBenchmark(
                customer_id=customer_id,
                target_conv_rate=float(benchmarks_data['target_conv_rate']),
                target_cpa=float(benchmarks_data['target_cpa']),
                benchmark_ctr=float(benchmarks_data['benchmark_ctr']),
                min_quality_score=int(benchmarks_data['min_quality_score']),
                industry_vertical=benchmarks_data.get('industry_vertical', 'general'),
                seasonality_factor=float(benchmarks_data.get('seasonality_factor', 1.0)),
                risk_tolerance=benchmarks_data.get('risk_tolerance', 'moderate'),
                created_by=benchmarks_data.get('created_by', 'manual_update')
            )
            
            # Actualizar en base de datos
            success = self.db_service.update_benchmarks(customer_id, benchmarks)
            
            if success:
                logger.info(f"Benchmarks actualizados para cuenta {customer_id}")
            else:
                logger.error(f"Error actualizando benchmarks para cuenta {customer_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error actualizando benchmarks para {customer_id}: {e}")
            return False

    def get_account_performance_summary(self, customer_id: str, days_back: int = 30) -> Dict:
        """Obtener resumen de rendimiento de una cuenta"""
        try:
            # Obtener métricas recientes
            metrics = self.db_service.get_keyword_metrics(customer_id, days_back)
            
            if not metrics:
                return {
                    'total_keywords': 0,
                    'total_spend': 0,
                    'total_conversions': 0,
                    'avg_conv_rate': 0,
                    'avg_cpa': 0,
                    'avg_ctr': 0,
                    'active_campaigns': 0,
                    'last_sync': None
                }
            
            # Calcular métricas agregadas
            total_spend = sum(m.cost_micros / 1_000_000 for m in metrics)
            total_conversions = sum(m.conversions for m in metrics)
            total_clicks = sum(m.clicks for m in metrics)
            total_impressions = sum(m.impressions for m in metrics)
            
            avg_conv_rate = (total_conversions / total_clicks) if total_clicks > 0 else 0
            avg_cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
            avg_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0
            
            # Contar keywords y campañas únicas
            unique_keywords = set((m.campaign_id, m.ad_group_id, m.keyword_text) for m in metrics)
            unique_campaigns = set(m.campaign_id for m in metrics)
            
            # Obtener información de la cuenta
            accounts = self.db_service.get_all_accounts(active_only=False)
            account_info = next((acc for acc in accounts if acc.customer_id == customer_id), None)
            
            return {
                'total_keywords': len(unique_keywords),
                'total_spend': round(total_spend, 2),
                'total_conversions': round(total_conversions, 2),
                'avg_conv_rate': round(avg_conv_rate * 100, 2),  # Porcentaje
                'avg_cpa': round(avg_cpa, 2),
                'avg_ctr': round(avg_ctr * 100, 2),  # Porcentaje
                'active_campaigns': len(unique_campaigns),
                'last_sync': account_info.last_sync if account_info else None,
                'currency_code': account_info.currency_code if account_info else 'USD'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de rendimiento para {customer_id}: {e}")
            return {}

    def get_all_accounts_summary(self) -> List[Dict]:
        """Obtener resumen de todas las cuentas activas"""
        try:
            accounts = self.db_service.get_all_accounts(active_only=True)
            summaries = []
            
            for account in accounts:
                try:
                    performance = self.get_account_performance_summary(account.customer_id)
                    health_summary = self.db_service.get_health_score_summary(account.customer_id)
                    
                    summary = {
                        'customer_id': account.customer_id,
                        'account_name': account.account_name,
                        'currency_code': account.currency_code,
                        'account_type': account.account_type,
                        'last_sync': account.last_sync,
                        'performance': performance,
                        'health_summary': health_summary
                    }
                    
                    summaries.append(summary)
                    
                except Exception as e:
                    logger.error(f"Error obteniendo resumen para cuenta {account.customer_id}: {e}")
                    continue
            
            logger.info(f"Generados resúmenes para {len(summaries)} cuentas")
            return summaries
            
        except Exception as e:
            logger.error(f"Error obteniendo resúmenes de cuentas: {e}")
            return []

    def cleanup_inactive_accounts(self, days_inactive: int = 90) -> int:
        """Marcar como inactivas las cuentas sin sincronización reciente"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_inactive)
            accounts = self.db_service.get_all_accounts(active_only=False)
            
            deactivated_count = 0
            
            for account in accounts:
                if (account.last_sync and account.last_sync < cutoff_date and account.is_active):
                    # Marcar como inactiva
                    account.is_active = False
                    if self.db_service.upsert_account(account):
                        deactivated_count += 1
                        logger.info(f"Cuenta {account.customer_id} marcada como inactiva")
            
            logger.info(f"Desactivadas {deactivated_count} cuentas inactivas")
            return deactivated_count
            
        except Exception as e:
            logger.error(f"Error limpiando cuentas inactivas: {e}")
            return 0

    def validate_account_access(self, customer_id: str) -> bool:
        """Validar que tenemos acceso a una cuenta específica"""
        try:
            # Intentar hacer una consulta simple a la cuenta
            query = "SELECT customer.id FROM customer LIMIT 1"
            response = self.ads_client.search(customer_id, query)
            
            # Si no hay excepción, tenemos acceso
            for row in response:
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"No se pudo validar acceso a cuenta {customer_id}: {e}")
            return False

    def discover_and_sync_accounts(self) -> Dict[str, Any]:
        """
        Descubrir y sincronizar cuentas MCC desde Google Ads API
        
        Returns:
            Resultado de la sincronización con estadísticas
        """
        try:
            logger.info("Iniciando descubrimiento y sincronización de cuentas MCC")
            
            # Obtener cliente de Google Ads
            client = self.ads_client.get_client()
            if not client:
                logger.error("No se pudo obtener cliente de Google Ads")
                return {
                    'success': False,
                    'error': 'No se pudo conectar a Google Ads API',
                    'accounts_discovered': 0,
                    'accounts_synced': 0
                }
            
            # Cargar customer IDs desde configuración
            customer_ids = self.ads_client.load_customer_ids()
            
            if not customer_ids:
                logger.warning("No se encontraron customer IDs en la configuración")
                return {
                    'success': True,
                    'message': 'No hay customer IDs configurados',
                    'accounts_discovered': 0,
                    'accounts_synced': 0
                }
            
            accounts_discovered = 0
            accounts_synced = 0
            errors = []
            
            # Procesar cada customer ID
            for customer_id in customer_ids:
                try:
                    # Obtener información de la cuenta
                    account_info = self.ads_client.get_account_info(customer_id)
                    
                    if account_info:
                        accounts_discovered += 1
                        
                        # Crear objeto MCCAccount
                        mcc_account = MCCAccount(
                            customer_id=customer_id,
                            account_name=account_info.get('descriptive_name', f'Account {customer_id}'),
                            currency_code=account_info.get('currency_code', 'USD'),
                            time_zone=account_info.get('time_zone', 'America/New_York'),
                            is_active=True,
                            account_type='child',
                            last_sync=datetime.now()
                        )
                        
                        # Verificar si la cuenta ya existe
                        existing_account = self.db_service.get_mcc_account(customer_id)
                        
                        if existing_account:
                            # Actualizar cuenta existente
                            if self.db_service.update_mcc_account(mcc_account):
                                accounts_synced += 1
                                logger.info(f"Cuenta actualizada: {mcc_account.account_name} ({customer_id})")
                            else:
                                logger.warning(f"No se pudo actualizar cuenta: {customer_id}")
                        else:
                            # Insertar nueva cuenta
                            if self.db_service.insert_mcc_account(mcc_account):
                                accounts_synced += 1
                                logger.info(f"Nueva cuenta sincronizada: {mcc_account.account_name} ({customer_id})")
                                
                                # Crear benchmarks por defecto para nueva cuenta
                                self._create_default_benchmarks_for_account(mcc_account)
                            else:
                                logger.warning(f"No se pudo insertar nueva cuenta: {customer_id}")
                    else:
                        logger.warning(f"No se pudo obtener información para customer ID: {customer_id}")
                        
                except Exception as e:
                    error_msg = f"Error procesando customer ID {customer_id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            result = {
                'success': True,
                'accounts_discovered': accounts_discovered,
                'accounts_synced': accounts_synced,
                'total_customer_ids': len(customer_ids),
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Sincronización completada: {accounts_synced}/{accounts_discovered} cuentas sincronizadas")
            return result
            
        except Exception as e:
            logger.error(f"Error en descubrimiento y sincronización de cuentas: {e}")
            return {
                'success': False,
                'error': str(e),
                'accounts_discovered': 0,
                'accounts_synced': 0
            }
    
    def _detect_industry_vertical(self, account_info: Dict[str, Any]) -> str:
        """
        Detectar vertical de industria basado en información de la cuenta
        
        Args:
            account_info: Información de la cuenta de Google Ads
            
        Returns:
            Vertical de industria detectado
        """
        try:
            account_name = account_info.get('descriptive_name', '').lower()
            
            # Mapeo de palabras clave a verticales
            industry_keywords = {
                'retail': ['store', 'shop', 'retail', 'ecommerce', 'fashion', 'clothing', 'shoes'],
                'technology': ['tech', 'software', 'saas', 'app', 'digital', 'cloud', 'ai'],
                'services': ['service', 'consulting', 'agency', 'professional', 'legal', 'medical'],
                'finance': ['bank', 'finance', 'insurance', 'loan', 'credit', 'investment'],
                'healthcare': ['health', 'medical', 'clinic', 'hospital', 'dental', 'pharmacy'],
                'education': ['school', 'university', 'education', 'learning', 'course', 'training'],
                'travel': ['travel', 'hotel', 'tourism', 'vacation', 'flight', 'booking'],
                'automotive': ['car', 'auto', 'vehicle', 'dealership', 'automotive', 'garage'],
                'real_estate': ['real estate', 'property', 'home', 'house', 'apartment', 'realty']
            }
            
            # Buscar coincidencias
            for vertical, keywords in industry_keywords.items():
                if any(keyword in account_name for keyword in keywords):
                    return vertical
            
            # Por defecto, asignar 'retail'
            return 'retail'
            
        except Exception as e:
            logger.error(f"Error detectando vertical de industria: {e}")
            return 'retail'
    
    def _create_default_benchmarks_for_account(self, account: MCCAccount):
        """
        Crear benchmarks por defecto para una nueva cuenta
        
        Args:
            account: Cuenta MCC para la cual crear benchmarks
        """
        try:
            # Obtener benchmarks por defecto para la industria
            default_benchmarks = self.get_default_benchmarks_by_industry(
                account.industry_vertical, 
                account.currency
            )
            
            # Crear benchmark en la base de datos
            benchmark = KeywordBenchmark(
                customer_id=account.customer_id,
                benchmark_name=f"{account.industry_vertical.title()} Industry Standard",
                target_ctr=default_benchmarks['target_ctr'],
                target_conversion_rate=default_benchmarks['target_conversion_rate'],
                max_cpa=default_benchmarks['max_cpa'],
                min_quality_score=default_benchmarks['min_quality_score'],
                target_impression_share=default_benchmarks['target_impression_share'],
                is_default=True,
                created_at=datetime.now()
            )
            
            if self.db_service.insert_keyword_benchmark(benchmark):
                logger.info(f"Benchmarks por defecto creados para {account.account_name}")
            else:
                logger.warning(f"No se pudieron crear benchmarks para {account.account_name}")
                
        except Exception as e:
            logger.error(f"Error creando benchmarks por defecto para {account.account_name}: {e}")