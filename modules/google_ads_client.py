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
                # Use top-level keys from YAML and overlay environment variables if present
                config.update(loaded)
            
            # Overlay environment variables regardless of file existence
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
            
            # Sanitize login customer ID format (remove dashes)
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
            # Treat placeholders and empty values as missing
            if not dev_token or dev_token.upper().startswith('YOUR_'):
                logger.error("Developer token not found or invalid in configuration")
                return None
            
            client_id = config.get('client_id')
            client_secret = config.get('client_secret')
            refresh_token = config.get('refresh_token')
            if not all([client_id, client_secret, refresh_token]):
                logger.error("Missing OAuth credentials (client_id, client_secret, refresh_token)")
                return None
            
            # Build config dict expected by google-ads client
            client_config = {
                'developer_token': dev_token,
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'use_proto_plus': config.get('use_proto_plus', True)
            }
            
            # Add login customer ID if available
            if config.get('login_customer_id'):
                client_config['login_customer_id'] = config['login_customer_id']
            
            # Initialize client from dict (compatible across versions)
            self._client = GoogleAdsClient.load_from_dict(client_config)
            
            # ✅ SOLUCIÓN: Agregar atributo .client para compatibilidad
            self.client = self._client
            
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
                        # Remove inline comments after '#'
                        if '#' in line:
                            line = line.split('#', 1)[0].strip()
                        # Keep only digits (remove dashes, spaces and any non-digit)
                        digits_only = ''.join(ch for ch in line if ch.isdigit())
                        if not digits_only:
                            continue
                        if len(digits_only) == 10:
                            customer_ids.append(digits_only)
                        else:
                            logger.warning(f"Skipping invalid customer ID in accounts.txt: '{raw_line.strip()}' -> '{digits_only}'")
                    # Deduplicate while preserving order
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
    
    def execute_query(self, customer_id: str, query: str) -> List[Any]:
        """Execute GAQL query and return results as protobuf objects"""
        client = self.get_client()
        if not client:
            return []
            
        try:
            ga_service = client.get_service("GoogleAdsService")
            
            # Execute search request
            search_request = client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            # Return rows directly as protobuf objects
            # The service layer expects protobuf objects with attributes like row.campaign, row.metrics, etc.
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
        """
        Get account information including currency code from customer resource
        
        Args:
            customer_id: Google Ads customer ID
            
        Returns:
            Dictionary with account information
        """
        try:
            client = self.get_client()
            if not client:
                return {}
            
            # Query customer resource for account information
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
        
        # Aggregate results
        total_spend = sum(row.get('metrics', {}).get('cost_micros', 0) for row in results)
        
        return {
            'customer_id': customer_id,
            'total_spend_micros': total_spend,
            'total_spend': total_spend / 1_000_000,  # Convert from micros
            'currency': 'USD'  # Default, should be fetched from account info
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
            
            # Execute a minimal GAQL query directly to validate connectivity
            ga_service = client.get_service("GoogleAdsService")
            query = "SELECT customer.id FROM customer LIMIT 1"
            test_customer = customer_ids[0]
            try:
                response = ga_service.search(customer_id=test_customer, query=query)
                for _ in response:
                    logger.info("Connection test query returned rows.")
                    return True
                logger.warning("Connection test query returned no rows.")
                return False
            except GoogleAdsException as ex:
                logger.error(f"Google Ads API error during connection test: {ex}")
                for error in ex.failure.errors:
                    logger.error(f"Error: {error.message}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error during connection test: {e}")
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    # Add a getter to match expected interface used elsewhere
    def get_customer_ids(self) -> List[str]:
        """Get customer IDs from accounts.txt file (simple and reliable)"""
        # Use static file - it's more reliable and doesn't require complex API calls
        customer_ids = self.load_customer_ids()
        if customer_ids:
            logger.info(f"Loaded {len(customer_ids)} customer accounts from accounts.txt")
            return customer_ids
        
        logger.warning("No customer IDs found in accounts.txt")
        return []
    
    def _validate_customer_accounts(self, customer_ids: List[str]) -> List[str]:
        """Validate that customer accounts are accessible and active"""
        if not customer_ids:
            return []
            
        client = self.get_client()
        if not client:
            logger.error("Cannot validate accounts - client not initialized")
            return customer_ids  # Return unvalidated if client fails
            
        validated_accounts = []
        
        for customer_id in customer_ids:
            try:
                # Try to get basic account info to validate access
                account_info = self.get_account_info(customer_id)
                if account_info and account_info.get('name'):
                    validated_accounts.append(customer_id)
                    logger.info(f"✓ Account {customer_id} validated: {account_info.get('name', 'Unknown')}")
                else:
                    logger.warning(f"✗ Account {customer_id} validation failed - no account info")
                    
            except Exception as e:
                logger.warning(f"✗ Account {customer_id} validation failed: {e}")
                # Don't include accounts that fail validation
                continue
        
        logger.info(f"Account validation complete: {len(validated_accounts)}/{len(customer_ids)} accounts accessible")
        return validated_accounts
    
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
        
        # Aggregate results
        total_spend = sum(row.get('metrics', {}).get('cost_micros', 0) for row in results)
        
        return {
            'customer_id': customer_id,
            'total_spend_micros': total_spend,
            'total_spend': total_spend / 1_000_000,  # Convert from micros
            'currency': 'USD'  # Default, should be fetched from account info
        }
    
    def list_accessible_customers(self) -> List[str]:
        """Return a list of customer IDs accessible with current credentials.
        Filters out the manager account and returns only child accounts."""
        client = self.get_client()
        if not client:
            logger.error("Google Ads client not initialized; cannot list accessible customers.")
            return []
        
        try:
            # Get configuration to identify manager account
            config = self._load_config()
            manager_account_id = config.get('login_customer_id', '').replace('-', '')
            logger.info(f"Manager account ID: {manager_account_id}")
            
            # First, get all accessible customers
            customer_service = client.get_service("CustomerService")
            response = customer_service.list_accessible_customers()
            resource_names = list(response.resource_names)
            
            all_customer_ids: List[str] = []
            for rn in resource_names:
                # rn format: "customers/1234567890"
                parts = str(rn).split('/')
                if len(parts) == 2 and parts[1].isdigit():
                    all_customer_ids.append(parts[1])
                else:
                    logger.warning(f"Unexpected resource name format: {rn}")
            
            logger.info(f"Total accessible customers found: {len(all_customer_ids)}")
            logger.info(f"All accessible customer IDs: {all_customer_ids}")
            
            # Now get child accounts specifically from the manager account
            child_accounts = self._get_child_accounts(manager_account_id)
            if child_accounts:
                logger.info(f"Child accounts from manager: {child_accounts}")
                # Filter to only include child accounts that are also in accessible list
                valid_child_accounts = [cid for cid in child_accounts if cid in all_customer_ids]
                logger.info(f"Valid child accounts (accessible): {valid_child_accounts}")
                return valid_child_accounts
            
            # Fallback: filter out manager account from accessible customers
            filtered_customers = [cid for cid in all_customer_ids if cid != manager_account_id]
            logger.info(f"Filtered customers (excluding manager): {filtered_customers}")
            
            return filtered_customers
            
        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error listing accessible customers: {ex}")
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing accessible customers: {e}")
            return []
    
    def _get_child_accounts(self, manager_customer_id: str) -> List[str]:
        """Get child accounts from a manager account using CustomerClientService."""
        if not manager_customer_id:
            logger.warning("No manager customer ID provided")
            return []
            
        client = self.get_client()
        if not client:
            return []
            
        try:
            logger.info(f"Querying child accounts for manager: {manager_customer_id}")
            
            # Query to get customer clients (child accounts)
            query = """
                SELECT 
                    customer_client.client_customer,
                    customer_client.level,
                    customer_client.manager,
                    customer_client.descriptive_name,
                    customer_client.currency_code,
                    customer_client.time_zone,
                    customer_client.status
                FROM customer_client 
                WHERE customer_client.level <= 1
            """
            
            ga_service = client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=manager_customer_id, query=query)
            
            child_customer_ids = []
            for row in response:
                client_info = row.customer_client
                client_id = str(client_info.client_customer).replace('customers/', '')
                
                logger.info(f"Found client: {client_id}, Name: {client_info.descriptive_name}, "
                           f"Level: {client_info.level}, Manager: {client_info.manager}, "
                           f"Status: {client_info.status}")
                
                # Only include non-manager accounts (level 1 = child accounts)
                if not client_info.manager and client_info.level == 1:
                    child_customer_ids.append(client_id)
            
            logger.info(f"Child customer IDs found: {child_customer_ids}")
            return child_customer_ids
            
        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error getting child accounts: {ex}")
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            return []
    
    # ✅ MÉTODOS ADICIONALES PARA COMPATIBILIDAD CON BidAdjustmentService
    def get_service(self, service_name: str, version: str = "v17"):
        """
        Proxy para obtener servicios de Google Ads
        
        Args:
            service_name: Nombre del servicio (ej: "GoogleAdsService")
            version: Versión de la API (default: v17)
            
        Returns:
            Servicio de Google Ads
        """
        if not self._client:
            self.get_client()
        return self._client.get_service(service_name, version=version)
    
    def get_type(self, type_name: str, version: str = "v17"):
        """
        Proxy para obtener tipos de Google Ads
        
        Args:
            type_name: Nombre del tipo (ej: "AdGroupCriterionOperation")
            version: Versión de la API
            
        Returns:
            Tipo de Google Ads
        """
        if not self._client:
            self.get_client()
        return self._client.get_type(type_name, version=version)
    
    @property
    def enums(self):
        """Acceso a enums de Google Ads"""
        if not self._client:
            self.get_client()
        return self._client.enums
    
    def copy_from(self, *args, **kwargs):
        """Proxy para copy_from"""
        if not self._client:
            self.get_client()
        return self._client.copy_from(*args, **kwargs)
    
    def __getattr__(self, name):
        """
        Fallback: Delega cualquier método/atributo no encontrado al cliente real
        
        Esto hace que el wrapper sea transparente para cualquier uso
        """
        if not self._client:
            self.get_client()
        return getattr(self._client, name)
    
    def __repr__(self):
        return f"<GoogleAdsClientWrapper(client={type(self._client).__name__ if self._client else 'None'})>"