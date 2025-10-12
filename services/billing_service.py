"""
Billing Service for Google Ads Dashboard
Handles billing data retrieval, budget tracking, and spend analysis
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from modules.google_ads_client import GoogleAdsClientWrapper
from modules.models import BillingRecord, BillingSummary, Account
from utils.cache import cache_google_ads_data
from utils.rate_limit import rate_limited
from utils.logger import log_api_call
from utils.formatters import format_currency, format_percentage

logger = logging.getLogger(__name__)

class BillingService:
    """Service for managing billing and budget data"""
    
    def __init__(self, google_ads_client: GoogleAdsClientWrapper):
        """
        Initialize billing service
        
        Args:
            google_ads_client: Google Ads API client wrapper
        """
        self.client = google_ads_client
        self.budgets_config = {}  # Will be loaded from config file

    @rate_limited('search', tokens=2)
    @cache_google_ads_data("", "billing_summary", ttl=1800)  # 30 minutes
    @log_api_call("", "get_billing_summary")
    def get_billing_summary(self, customer_id: str, 
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> Optional[BillingSummary]:
        """
        Get billing summary for a customer using proper Google Ads API billing resources
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for billing period (defaults to current month)
            end_date: End date for billing period (defaults to today)
            
        Returns:
            BillingSummary object or None if error
        """
        try:
            # Set default date range to current month if not provided
            if start_date is None or end_date is None:
                today = date.today()
                start_date = today.replace(day=1)  # First day of current month
                end_date = today
            
            # Get account currency from customer resource
            account_info = self.client.get_account_info(customer_id)
            currency_code = account_info.get('currency_code', 'USD') if account_info else 'USD'
            
            logger.info(f"Getting billing summary for {customer_id} from {start_date} to {end_date}")
            
            # Query campaign metrics for spend data - this is the correct approach for getting spend
            query = f"""
                SELECT
                    customer.id,
                    customer.currency_code,
                    segments.date,
                    metrics.cost_micros
                FROM campaign
                WHERE segments.date >= '{start_date}'
                AND segments.date <= '{end_date}'
            """
            
            results = self.client.execute_query(customer_id, query)
            
            logger.info(f"Billing query returned {len(results) if results else 0} rows for customer {customer_id}")
            
            if not results or len(results) == 0:
                logger.warning(f"No billing data found for {customer_id} between {start_date} and {end_date}")
                return BillingSummary(
                    customer_id=customer_id,
                    current_spend=0.0,
                    monthly_budget=self._get_monthly_budget(customer_id),
                    currency_code=currency_code
                )
            
            # Calculate total spend from campaign metrics
            total_spend_micros = sum(row.metrics.cost_micros for row in results)
            total_spend = total_spend_micros / 1_000_000
            
            logger.info(f"Total spend for {customer_id}: ${total_spend:.2f} ({len(results)} records)")
            
            # Get monthly budget (from account_budget resource or config)
            monthly_budget = self._get_account_budget(customer_id) or self._get_monthly_budget(customer_id)
            
            # Calculate projected spend
            days_in_period = (end_date - start_date).days + 1
            days_in_month = self._get_days_in_month(start_date)
            
            if days_in_period > 0:
                daily_average = total_spend / days_in_period
                projected_spend = daily_average * days_in_month
            else:
                projected_spend = total_spend
            
            # Calculate days remaining in month
            today = date.today()
            last_day_of_month = date(today.year, today.month, days_in_month)
            days_remaining = max(0, (last_day_of_month - today).days)
            
            return BillingSummary(
                customer_id=customer_id,
                current_spend=total_spend,
                monthly_budget=monthly_budget,
                currency_code=currency_code,
                projected_spend=projected_spend,
                days_remaining=days_remaining
            )
            
        except Exception as e:
            logger.error(f"Error getting billing summary for {customer_id}: {e}")
            return None

    def _get_account_budget(self, customer_id: str) -> Optional[float]:
        """
        Get account budget from Google Ads API account_budget resource
        
        Args:
            customer_id: Google Ads customer ID
            
        Returns:
            Account budget amount or None if not found
        """
        try:
            # Query account_budget resource for active budgets
            # Note: Using correct field names for account_budget resource
            query = """
                SELECT
                    account_budget.id,
                    account_budget.name,
                    account_budget.proposed_spending_limit_micros,
                    account_budget.status,
                    account_budget.billing_setup,
                    account_budget.proposed_start_date_time,
                    account_budget.proposed_end_date_time
                FROM account_budget
                WHERE account_budget.status = 'APPROVED'
            """
            
            results = self.client.execute_query(customer_id, query)
            
            if results and len(results) > 0:
                # Get the most recent active budget
                for row in results:
                    if hasattr(row, 'account_budget') and hasattr(row.account_budget, 'proposed_spending_limit_micros'):
                        if row.account_budget.proposed_spending_limit_micros:
                            budget_amount = row.account_budget.proposed_spending_limit_micros / 1_000_000
                            logger.info(f"Found account budget for {customer_id}: ${budget_amount:.2f}")
                            return budget_amount
                        
        except Exception as e:
            logger.warning(f"Could not retrieve account budget for {customer_id}: {e}")
            
        return None

    def get_billing_setups(self, customer_id: str) -> List[Dict]:
        """
        Get billing setups for a customer using billing_setup resource
        
        Args:
            customer_id: Google Ads customer ID
            
        Returns:
            List of billing setup dictionaries
        """
        try:
            # Query billing_setup resource
            query = """
                SELECT
                    billing_setup.id,
                    billing_setup.status,
                    billing_setup.payments_account,
                    billing_setup.payments_account_info.payments_account_id,
                    billing_setup.payments_account_info.payments_account_name,
                    billing_setup.payments_account_info.payments_profile_id,
                    billing_setup.start_date_time,
                    billing_setup.end_date_time
                FROM billing_setup
                WHERE billing_setup.status IN ('APPROVED', 'PENDING')
            """
            
            results = self.client.execute_query(customer_id, query)
            
            billing_setups = []
            if results:
                for row in results:
                    if hasattr(row, 'billing_setup'):
                        setup = {
                            'id': row.billing_setup.id,
                            'status': row.billing_setup.status.name if hasattr(row.billing_setup.status, 'name') else str(row.billing_setup.status),
                            'payments_account': row.billing_setup.payments_account,
                            'start_date': row.billing_setup.start_date_time,
                            'end_date': row.billing_setup.end_date_time
                        }
                        
                        # Add payments account info if available
                        if hasattr(row.billing_setup, 'payments_account_info'):
                            setup['payments_account_info'] = {
                                'account_id': row.billing_setup.payments_account_info.payments_account_id,
                                'account_name': row.billing_setup.payments_account_info.payments_account_name,
                                'profile_id': row.billing_setup.payments_account_info.payments_profile_id
                            }
                        
                        billing_setups.append(setup)
            
            logger.info(f"Found {len(billing_setups)} billing setups for {customer_id}")
            return billing_setups
            
        except Exception as e:
            logger.error(f"Error getting billing setups for {customer_id}: {e}")
            return []

    @rate_limited('search', tokens=3)
    @cache_google_ads_data("", "daily_spend", ttl=3600)  # 1 hour
    @log_api_call("", "get_daily_spend")
    def get_daily_spend(self, customer_id: str, 
                       start_date: date = None, 
                       end_date: date = None,
                       days: int = None) -> List[BillingRecord]:
        """
        Get daily spend data for a customer using campaign metrics
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date (optional if days is provided)
            end_date: End date (optional if days is provided)
            days: Number of days to look back (optional, overrides start_date/end_date)
            
        Returns:
            List of BillingRecord objects
        """
        # If days is provided, calculate start_date and end_date
        if days is not None:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
        elif start_date is None or end_date is None:
            # Default to last 30 days if nothing provided
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        try:
            # Get account currency
            account_info = self.client.get_account_info(customer_id)
            currency_code = account_info.get('currency_code', 'USD') if account_info else 'USD'
            
            logger.info(f"Getting daily spend for {customer_id} from {start_date} to {end_date}, currency: {currency_code}")
            
            # Query for daily spend using campaign metrics - this is the correct approach
            query = f"""
                SELECT
                    customer.id,
                    customer.currency_code,
                    customer.descriptive_name,
                    customer.test_account,
                    segments.date,
                    metrics.cost_micros,
                    campaign.id,
                    campaign.name,
                    campaign.status
                FROM campaign
                WHERE segments.date >= '{start_date}'
                AND segments.date <= '{end_date}'
                ORDER BY segments.date DESC
            """
            
            results = self.client.execute_query(customer_id, query)
            
            logger.info(f"Daily spend query returned {len(results) if results else 0} rows for customer {customer_id}")
            
            if not results or len(results) == 0:
                logger.warning(f"No daily spend data for {customer_id} from {start_date} to {end_date}")
                return []
            
            # Check if this is a test account and log account details
            first_row = results[0]
            is_test_account = getattr(first_row.customer, 'test_account', False)
            account_name = getattr(first_row.customer, 'descriptive_name', 'Unknown')
            api_currency = getattr(first_row.customer, 'currency_code', 'USD')
            
            logger.info(f"Account details - Name: {account_name}, Test Account: {is_test_account}, API Currency: {api_currency}")
            
            # Group by date and sum costs
            daily_spend = {}
            total_cost_micros = 0
            
            for row in results:
                date_str = row.segments.date
                cost_micros = row.metrics.cost_micros
                
                # Log individual campaign costs for debugging
                campaign_cost_usd = cost_micros / 1_000_000
                logger.debug(f"Campaign {row.campaign.name} on {date_str}: {cost_micros} micros = ${campaign_cost_usd:.2f} USD")
                
                if date_str not in daily_spend:
                    daily_spend[date_str] = 0
                daily_spend[date_str] += cost_micros
                total_cost_micros += cost_micros
            
            total_cost_usd = total_cost_micros / 1_000_000
            logger.info(f"Total cost across all days: {total_cost_micros} micros = ${total_cost_usd:.2f} USD")
            logger.info(f"Aggregated spend across {len(daily_spend)} unique dates")
            
            # Validate if costs are realistic - user expects 300k-400k COP daily (~$75-100 USD)
            max_daily_cost_usd = max(cost_micros / 1_000_000 for cost_micros in daily_spend.values()) if daily_spend else 0
            
            # If this is a test account, reject the data
            if is_test_account:
                logger.warning(f"TEST ACCOUNT: This is a test account. Showing data for diagnostics; values may be non-production")
                # continue: do not filter test account data
                pass
            
            # If daily costs are unrealistically high (more than $1000 USD per day), reject
            if max_daily_cost_usd > 1000:  # More than $1k USD per day is suspicious for this user
                logger.warning(f"Daily costs high (${max_daily_cost_usd:.2f} USD). User expects ~$75-100 USD daily. Displaying data with caution.")
                # continue: show data with caution
                pass
                
            # Additional validation: if total cost is more than expected range, reject
            total_cost_usd = total_cost_micros / 1_000_000
            expected_daily_usd = 85  # Average of 300k-400k COP (~$75-100 USD)
            days_count = len(daily_spend)
            expected_total_usd = expected_daily_usd * days_count
            
            # If total is more than 10x expected, it's likely fake
            if total_cost_usd > (expected_total_usd * 10):
                logger.warning(f"Total cost ${total_cost_usd:.2f} USD is {total_cost_usd/expected_total_usd:.1f}x higher than expected ${expected_total_usd:.2f} USD. Displaying data with caution.")
                # continue: show data with caution
                pass
            
            # Convert to BillingRecord objects
            billing_records = []
            for date_str, cost_micros in daily_spend.items():
                billing_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Use the actual API currency, not the account_info currency
                record = BillingRecord(
                    customer_id=customer_id,
                    billing_date=billing_date,
                    amount_micros=cost_micros,
                    currency_code=api_currency  # Use currency from API response
                )
                billing_records.append(record)
            
            # Sort by date
            billing_records.sort(key=lambda x: x.billing_date)
            
            total_amount = sum(r.amount for r in billing_records)
            logger.info(f"Returning {len(billing_records)} records, total: ${total_amount:.2f} {api_currency}")
            
            # Final validation - if total is more than $10k USD equivalent, it's suspicious
            if api_currency == 'USD' and total_amount > 10000:
                logger.warning(f"HIGH COST WARNING: Total spend ${total_amount:.2f} USD seems very high")
            elif api_currency == 'COP' and total_amount > 40000000:  # 40M COP = ~$10k USD
                logger.warning(f"HIGH COST WARNING: Total spend ${total_amount:.2f} COP seems very high")
            
            return billing_records
            
        except Exception as e:
            logger.error(f"Error getting daily spend for {customer_id}: {e}")
            return []

    def get_multi_account_summary(self, customer_ids) -> Dict[str, BillingSummary]:
        """
        Get billing summaries for multiple accounts
        
        Args:
            customer_ids: Single customer ID (str) or list of customer IDs
            
        Returns:
            Dictionary mapping customer ID to BillingSummary
        """
        # Convert single customer_id to list
        if isinstance(customer_ids, str):
            customer_ids = [customer_ids]
        
        summaries = {}
        
        for customer_id in customer_ids:
            try:
                summary = self.get_billing_summary(customer_id)
                if summary:
                    summaries[customer_id] = summary
                else:
                    logger.warning(f"Could not get billing summary for {customer_id}")
            except Exception as e:
                logger.error(f"Error getting billing summary for {customer_id}: {e}")
        
        return summaries
    
    def get_budget_alerts(self, customer_ids, 
                         threshold: float = 0.8) -> List[Dict]:
        """
        Get budget alerts for accounts exceeding threshold
        
        Args:
            customer_ids: Single customer ID (str) or list of customer IDs
            threshold: Budget utilization threshold (0.0-1.0)
            
        Returns:
            List of alert dictionaries
        """
        # Convert single customer_id to list
        if isinstance(customer_ids, str):
            customer_ids = [customer_ids]
        
        alerts = []
        
        for customer_id in customer_ids:
            try:
                summary = self.get_billing_summary(customer_id)
                if not summary:
                    continue
                
                utilization = summary.budget_utilization
                
                if utilization >= threshold:
                    alert = {
                        'customer_id': customer_id,
                        'type': 'budget_threshold',
                        'severity': 'high' if utilization >= 1.0 else 'medium',
                        'message': f"Budget utilization at {format_percentage(utilization)}",
                        'current_spend': summary.current_spend,
                        'monthly_budget': summary.monthly_budget,
                        'utilization': utilization,
                        'currency_code': summary.currency_code
                    }
                    alerts.append(alert)
                    
            except Exception as e:
                logger.error(f"Error checking budget alerts for {customer_id}: {e}")
        
        return alerts
    
    def get_spend_trends(self, customer_id: str, days: int = 30) -> Dict:
        """
        Get spending trends for analysis
        
        Args:
            customer_id: Google Ads customer ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get daily spend data
            daily_records = self.get_daily_spend(customer_id, start_date, end_date)
            
            if not daily_records:
                return {'error': 'No spend data available'}
            
            # Calculate trends
            total_spend = sum(record.amount for record in daily_records)
            average_daily_spend = total_spend / len(daily_records) if daily_records else 0
            
            # Get spend for last 7 days vs previous 7 days
            recent_records = [r for r in daily_records if r.billing_date >= end_date - timedelta(days=7)]
            previous_records = [r for r in daily_records 
                              if end_date - timedelta(days=14) <= r.billing_date < end_date - timedelta(days=7)]
            
            recent_spend = sum(r.amount for r in recent_records)
            previous_spend = sum(r.amount for r in previous_records)
            
            # Calculate trend percentage
            if previous_spend > 0:
                trend_percentage = ((recent_spend - previous_spend) / previous_spend) * 100
            else:
                trend_percentage = 0
            
            return {
                'total_spend': total_spend,
                'average_daily_spend': average_daily_spend,
                'recent_spend': recent_spend,
                'previous_spend': previous_spend,
                'trend_percentage': trend_percentage,
                'trend_direction': 'up' if trend_percentage > 0 else 'down' if trend_percentage < 0 else 'stable',
                'currency_code': daily_records[0].currency_code if daily_records else 'USD'
            }
            
        except Exception as e:
            logger.error(f"Error getting spend trends for {customer_id}: {e}")
            return {'error': str(e)}
    
    def _get_monthly_budget(self, customer_id: str) -> float:
        """
        Get monthly budget for customer from config or default
        
        Args:
            customer_id: Google Ads customer ID
            
        Returns:
            Monthly budget amount
        """
        # Try to get from budgets config
        if customer_id in self.budgets_config:
            return self.budgets_config[customer_id].get('monthly_budget', 10000.0)
        
        # Default budget
        return 10000.0
    
    def _get_days_in_month(self, date_obj: date) -> int:
        """Get number of days in the month"""
        if date_obj.month == 12:
            next_month = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
        else:
            next_month = date_obj.replace(month=date_obj.month + 1, day=1)
        
        last_day = next_month - timedelta(days=1)
        return last_day.day
    
    def load_budgets_config(self, config_data: Dict):
        """
        Load budgets configuration
        
        Args:
            config_data: Budget configuration dictionary
        """
        self.budgets_config = config_data
        logger.info(f"Loaded budget configuration for {len(config_data)} accounts")
    
    def update_budget(self, customer_id: str, monthly_budget: float):
        """
        Update monthly budget for customer
        
        Args:
            customer_id: Google Ads customer ID
            monthly_budget: New monthly budget amount
        """
        if customer_id not in self.budgets_config:
            self.budgets_config[customer_id] = {}
        
        self.budgets_config[customer_id]['monthly_budget'] = monthly_budget
        logger.info(f"Updated budget for {customer_id}: {format_currency(monthly_budget)}")
    
    def export_billing_data(self, customer_ids, 
                           start_date: date, 
                           end_date: date) -> List[Dict]:
        """
        Export billing data for multiple accounts
        
        Args:
            customer_ids: Single customer ID (str) or list of customer IDs
            start_date: Start date
            end_date: End date
            
        Returns:
            List of billing data dictionaries for export
        """
        # Convert single customer_id to list
        if isinstance(customer_ids, str):
            customer_ids = [customer_ids]
        
        export_data = []
        
        for customer_id in customer_ids:
            try:
                daily_records = self.get_daily_spend(customer_id, start_date, end_date)
                
                for record in daily_records:
                    export_data.append({
                        'customer_id': record.customer_id,
                        'date': record.billing_date.isoformat(),
                        'amount': record.amount,
                        'currency_code': record.currency_code,
                        'formatted_amount': format_currency(record.amount, record.currency_code)
                    })
                    
            except Exception as e:
                logger.error(f"Error exporting billing data for {customer_id}: {e}")
        
        return export_data