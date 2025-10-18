"""
Google Ads API Client Wrapper
Provides simplified interface for Google Ads API operations
"""

import os
import yaml
import logging
from typing import List, Dict, Any, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from modules.auth import GoogleAdsAuth
import streamlit as st

logger = logging.getLogger(__name__)

class GoogleAdsClientWrapper:
    """Wrapper for Google Ads API client with error handling and caching"""
    
    def __init__(self, config_file: str = "config/google-ads.yaml"):
        self.config_file = config_file
        self.auth = GoogleAdsAuth()
        self._client = None
        self._customer_ids = []
        
    def _load_config(self) -> Dict[str, Any]:
        """Load Google Ads API configuration"""
        try:
            config: Dict[str, Any] = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded = yaml.safe_load(f) or {}
                config.update(loaded)
            
            def getenv_nonempty(key: str) -> Optional[str]:
                val = os.getenv(key)
                if val is None:
                    return None
                val = val.strip()
                return val if val else None
            
            env_overrides = {
                'developer_token': getenv_nonempty('GOOGLE_ADS_DEVELOPER_TOKEN'),
                'client_id': getenv_nonempty('GOOGLE_ADS_CLIENT_ID'),
                'client_secret': getenv_nonempty('GOOGLE_ADS_CLIENT_SECRET'),
                'refresh_token': getenv_nonempty('GOOGLE_ADS_REFRESH_TOKEN'),
                'login_customer_id': getenv_nonempty('GOOGLE_ADS_LOGIN_CUSTOMER_ID'),
                'use_proto_plus': True if getenv_nonempty('GOOGLE_ADS_USE_PROTO_PLUS') in ('1', 'true', 'True') else None,
            }
            for k, v in env_overrides.items():
                if v is not None:
                    config[k] = v
            
            if config.get('login_customer_id'):
                config['login_customer_id'] = str(config['login_customer_id']).replace('-', '').strip()
            
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def get_client(self) -> Optional[GoogleAdsClient]:
        """Get authenticated Google Ads client"""
        if self._client:
            return self._client
        
        try:
            config = self._load_config()
            dev_token = str(config.get('developer_token', '')).strip()
            if not dev_token or dev_token.upper().startswith('YOUR_'):
                logger.error("Developer token not found or invalid in configuration")
                return None
            
            client_id = config.get('client_id')
            client_secret = config.get('client_secret')
            refresh_token = config.get('refresh_token')
            if not all([client_id, client_secret, refresh_token]):
                logger.error("Missing OAuth credentials (client_id, client_secret, refresh_token)")
                return None
            
            client_config = {
                'developer_token': dev_token,
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'use_proto_plus': config.get('use_proto_plus', True)
            }
            
            if config.get('login_customer_id'):
                client_config['login_customer_id'] = config['login_customer_id']
            
            self._client = GoogleAdsClient.load_from_dict(client_config)
            self.client = self._client  # Compatibilidad
            
            logger.info("Google Ads client initialized successfully")
            return self._client
            
        except Exception as e:
            logger.error(f"Error creating Google Ads client: {e}")
            return None

    def load_customer_ids(self) -> List[str]:
        """Load customer IDs from accounts.txt file"""
        if self._customer_ids:
            return self._customer_ids
            
        try:
            accounts_file = "config/accounts.txt"
            if os.path.exists(accounts_file):
                with open(accounts_file, 'r') as f:
                    customer_ids: List[str] = []
                    for raw_line in f:
                        line = raw_line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '#' in line:
                            line = line.split('#', 1)[0].strip()
                        digits_only = ''.join(ch for ch in line if ch.isdigit())
                        if not digits_only:
                            continue
                        if len(digits_only) == 10:
                            customer_ids.append(digits_only)
                        else:
                            logger.warning(f"Skipping invalid customer ID: '{raw_line.strip()}'")
                    seen = set()
                    deduped_ids = []
                    for cid in customer_ids:
                        if cid not in seen:
                            seen.add(cid)
                            deduped_ids.append(cid)
                    self._customer_ids = deduped_ids
                    logger.info(f"Loaded {len(deduped_ids)} customer IDs from accounts.txt")
            else:
                logger.warning("accounts.txt file not found")
                self._customer_ids = []
                
        except Exception as e:
            logger.error(f"Error loading customer IDs: {e}")
            self._customer_ids = []
            
        return self._customer_ids
    
    def get_customer_ids(self) -> list:
        """Get accessible customer IDs - Optimizado para cuentas MCC"""
        try:
            client = self.get_client()
            if not client:
                logger.error("❌ Cliente no disponible")
                return []
            
            customer_service = client.get_service("CustomerService")
            
            # Obtener todas las cuentas accesibles
            accessible_customers = customer_service.list_accessible_customers()
            resource_names = accessible_customers.resource_names
            
            logger.info(f"📋 Encontradas {len(resource_names)} cuentas totales")
            
            # Extraer IDs
            all_customer_ids = [
                name.split('/')[-1] 
                for name in resource_names
            ]
            
            # Verificar si tenemos una cuenta MCC como login_customer_id
            is_mcc = False
            mcc_id = self.login_customer_id
            
            if mcc_id in all_customer_ids:
                # Verificar si es MCC
                try:
                    ga_service = client.get_service("GoogleAdsService")
                    query = """
                        SELECT
                            customer.manager
                        FROM customer
                        LIMIT 1
                    """
                    response = ga_service.search(customer_id=mcc_id, query=query)
                    for row in response:
                        is_mcc = row.customer.manager
                        logger.info(f"🔍 Cuenta {mcc_id} - Es MCC: {is_mcc}")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo verificar si {mcc_id} es MCC: {e}")
            
            if is_mcc:
                logger.info(f"✅ Cuenta MCC detectada: {mcc_id}")
                
                # Para cuentas MCC, obtener todas las sub-cuentas
                try:
                    ga_service = client.get_service("GoogleAdsService")
                    
                    query = """
                        SELECT
                            customer_client.client_customer,
                            customer_client.descriptive_name,
                            customer_client.manager,
                            customer_client.status,
                            customer_client.hidden
                        FROM customer_client
                        WHERE customer_client.status = 'ENABLED'
                        AND customer_client.hidden = FALSE
                    """
                    
                    response = ga_service.search(customer_id=mcc_id, query=query)
                    
                    sub_account_ids = []
                    for row in response:
                        client_customer = row.customer_client.client_customer
                        customer_id = client_customer.split('/')[-1]
                        is_manager = row.customer_client.manager
                        name = row.customer_client.descriptive_name
                        
                        # Incluir todas las sub-cuentas (tanto normales como sub-MCCs)
                        sub_account_ids.append(customer_id)
                        
                        logger.info(f"✅ Sub-cuenta: {customer_id} - {name} {'(MCC)' if is_manager else ''}")
                    
                    # También incluir la MCC principal
                    sub_account_ids.append(mcc_id)
                    logger.info(f"✅ Agregada MCC principal: {mcc_id}")
                    
                    # Eliminar duplicados y ordenar
                    unique_ids = sorted(set(sub_account_ids))
                    
                    logger.info(f"✅ Total de cuentas accesibles: {len(unique_ids)}")
                    
                    return unique_ids
                    
                except Exception as e:
                    logger.error(f"❌ Error obteniendo sub-cuentas de MCC: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Fallback: devolver solo las cuentas accesibles directamente
                    logger.warning("⚠️ Usando fallback: solo cuentas con acceso directo")
            
            # Si no es MCC o hubo error, filtrar cuentas con acceso directo
            valid_customer_ids = []
            ga_service = client.get_service("GoogleAdsService")
            
            for customer_id in all_customer_ids:
                try:
                    query = """
                        SELECT
                            customer.id,
                            customer.descriptive_name
                        FROM customer
                        LIMIT 1
                    """
                    
                    response = ga_service.search(customer_id=customer_id, query=query)
                    
                    for row in response:
                        valid_customer_ids.append(customer_id)
                        logger.info(f"✅ Cuenta accesible: {customer_id} - {row.customer.descriptive_name}")
                        break
                        
                except Exception as e:
                    error_msg = str(e)
                    if "PERMISSION_DENIED" in error_msg:
                        logger.warning(f"⚠️ Sin permisos para {customer_id}")
                    elif "CUSTOMER_NOT_ENABLED" in error_msg:
                        logger.warning(f"⚠️ Cuenta deshabilitada {customer_id}")
                    else:
                        logger.warning(f"⚠️ Error en {customer_id}: {str(e)[:100]}")
                    continue
            
            if not valid_customer_ids:
                logger.error("❌ No se encontraron cuentas válidas")
            else:
                logger.info(f"✅ {len(valid_customer_ids)} cuentas válidas")
            
            return valid_customer_ids
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo customer IDs: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def execute_query(self, customer_id: str, query: str) -> List[Any]:
        """Execute GAQL query and return results as protobuf objects"""
        client = self.get_client()
        if not client:
            return []
            
        try:
            ga_service = client.get_service("GoogleAdsService")
            search_request = client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            results = list(ga_service.search(request=search_request))
            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return results
            
        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex}")
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            return []
    
    def get_account_info(self, customer_id: str) -> Dict[str, Any]:
        """Get account information including currency code"""
        try:
            client = self.get_client()
            if not client:
                return {}
            
            query = """
                SELECT
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.status,
                    customer.manager,
                    customer.test_account
                FROM customer
                LIMIT 1
            """
            
            results = self.execute_query(customer_id, query)
            
            if results and len(results) > 0:
                row = results[0]
                return {
                    'customer_id': row.customer.id,
                    'name': row.customer.descriptive_name,
                    'currency_code': row.customer.currency_code,
                    'time_zone': row.customer.time_zone,
                    'status': row.customer.status.name if hasattr(row.customer.status, 'name') else str(row.customer.status),
                    'is_manager': row.customer.manager,
                    'is_test_account': row.customer.test_account
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting account info for {customer_id}: {e}")
            return {}
    
    def get_campaign_metrics(self, customer_id: str, date_range: str = "LAST_30_DAYS") -> List[Dict[str, Any]]:
        """Get campaign performance metrics"""
        query = f"""
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc,
            metrics.conversion_rate,
            metrics.cost_per_conversion
        FROM campaign 
        WHERE segments.date DURING {date_range}
        AND campaign.status = 'ENABLED'
        ORDER BY metrics.cost_micros DESC
        """
        
        return self.execute_query(customer_id, query)
    
    def get_billing_summary(self, customer_id: str, month: Optional[str] = None) -> Dict[str, Any]:
        """Get billing and spend information"""
        date_condition = f"segments.month = '{month}'" if month else "segments.date DURING THIS_MONTH"
        
        query = f"""
        SELECT 
            customer.id,
            metrics.cost_micros,
            segments.date
        FROM customer 
        WHERE {date_condition}
        """
        
        results = self.execute_query(customer_id, query)
        total_spend = sum(row.get('metrics', {}).get('cost_micros', 0) for row in results)
        
        return {
            'customer_id': customer_id,
            'total_spend_micros': total_spend,
            'total_spend': total_spend / 1_000_000,
            'currency': 'USD'
        }
    
    def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            client = self.get_client()
            if not client:
                return False
            
            customer_ids = self.load_customer_ids()
            if not customer_ids:
                logger.warning("No customer IDs available for testing")
                return False
            
            ga_service = client.get_service("GoogleAdsService")
            query = "SELECT customer.id FROM customer LIMIT 1"
            test_customer = customer_ids[0]
            
            try:
                response = ga_service.search(customer_id=test_customer, query=query)
                for _ in response:
                    logger.info("Connection test successful")
                    return True
                logger.warning("Connection test returned no rows")
                return False
            except GoogleAdsException as ex:
                logger.error(f"Google Ads API error during test: {ex}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def list_accessible_customers(self) -> List[str]:
        """List all accessible customer accounts"""
        client = self.get_client()
        if not client:
            return []
        
        try:
            config = self._load_config()
            manager_account_id = config.get('login_customer_id', '').replace('-', '')
            
            customer_service = client.get_service("CustomerService")
            response = customer_service.list_accessible_customers()
            
            all_customer_ids = []
            for rn in response.resource_names:
                parts = str(rn).split('/')
                if len(parts) == 2 and parts[1].isdigit():
                    all_customer_ids.append(parts[1])
            
            return [cid for cid in all_customer_ids if cid != manager_account_id]
            
        except Exception as e:
            logger.error(f"Error listing customers: {e}")
            return []
    
    # ✅ Métodos proxy para compatibilidad
    def get_service(self, service_name: str, version: str = "v17"):
        """Proxy para obtener servicios"""
        if not self._client:
            self.get_client()
        return self._client.get_service(service_name, version=version)
    
    def get_type(self, type_name: str, version: str = "v17"):
        """Proxy para obtener tipos"""
        if not self._client:
            self.get_client()
        return self._client.get_type(type_name, version=version)
    
    @property
    def enums(self):
        """Acceso a enums"""
        if not self._client:
            self.get_client()
        return self._client.enums
    
    def copy_from(self, *args, **kwargs):
        """Proxy para copy_from"""
        if not self._client:
            self.get_client()
        return self._client.copy_from(*args, **kwargs)
    
    def __getattr__(self, name):
        """Delega métodos no encontrados al cliente real"""
        if not self._client:
            self.get_client()
        return getattr(self._client, name)
    
    def __repr__(self):
        return f"<GoogleAdsClientWrapper(client={type(self._client).__name__ if self._client else 'None'})>"