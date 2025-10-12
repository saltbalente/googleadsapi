"""
Campaign Service for Google Ads Dashboard
Handles campaign data retrieval, performance analysis, and management
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from modules.google_ads_client import GoogleAdsClientWrapper
from modules.models import Campaign, CampaignMetrics, CampaignStatus, KPISummary
from utils.cache import cache_google_ads_data
from utils.rate_limit import rate_limited
from utils.logger import log_api_call
from utils.formatters import format_currency, format_percentage, format_number

logger = logging.getLogger(__name__)

class CampaignService:
    """Service for managing campaign data and performance"""
    
    def __init__(self, google_ads_client: GoogleAdsClientWrapper):
        """
        Initialize campaign service
        
        Args:
            google_ads_client: Google Ads API client wrapper
        """
        self.client = google_ads_client
    
    @rate_limited('search', tokens=2)
    @cache_google_ads_data("", "campaigns", ttl=300)  # 5 minutes
    @log_api_call("", "get_campaigns")
    def get_campaigns(self, customer_id: str, 
                     status_filter: Optional[List[CampaignStatus]] = None) -> List[Campaign]:
        """
        Get campaigns for a customer
        
        Args:
            customer_id: Google Ads customer ID
            status_filter: Optional list of campaign statuses to filter by
            
        Returns:
            List of Campaign objects
        """
        try:
            # Build query
            query = """
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign.advertising_channel_type,
                    campaign.start_date,
                    campaign.end_date
                FROM campaign
            """
            
            # Add status filter if provided
            if status_filter:
                status_values = [f"'{status.value}'" for status in status_filter]
                query += f" WHERE campaign.status IN ({', '.join(status_values)})"
            
            results = self.client.execute_query(customer_id, query)
            if not results:
                return []
            
            campaigns = []
            for row in results:
                campaign = Campaign(
                    campaign_id=str(row.campaign.id),
                    customer_id=customer_id,
                    campaign_name=row.campaign.name,
                    campaign_status=CampaignStatus(row.campaign.status.name),
                    campaign_type=row.campaign.advertising_channel_type.name,
                    created_at=self._parse_date(row.campaign.start_date) if hasattr(row.campaign, 'start_date') else None
                )
                campaigns.append(campaign)
            
            logger.info(f"Retrieved {len(campaigns)} campaigns for customer {customer_id}")
            return campaigns
            
        except Exception as e:
            logger.error(f"Error getting campaigns for {customer_id}: {e}")
            return []
    
    @rate_limited('search', tokens=3)
    @cache_google_ads_data("", "campaign_metrics", ttl=300)  # 5 minutes
    @log_api_call("", "get_campaign_metrics")
    def get_campaign_metrics(self, customer_id: str, 
                           start_date: date, 
                           end_date: date,
                           campaign_ids: Optional[List[str]] = None) -> List[CampaignMetrics]:
        """
        Get campaign performance metrics
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for metrics
            end_date: End date for metrics
            campaign_ids: Optional list of specific campaign IDs
            
        Returns:
            List of CampaignMetrics objects
        """
        try:
            # Build query
            query = f"""
                SELECT
                    campaign.id,
                    segments.date,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.conversions_from_interactions_rate,
                    metrics.cost_per_conversion
                FROM campaign
                WHERE segments.date >= '{start_date}'
                AND segments.date <= '{end_date}'
            """
            
            # Add campaign filter if provided
            if campaign_ids:
                campaign_filter = ', '.join(campaign_ids)
                query += f" AND campaign.id IN ({campaign_filter})"
            
            results = self.client.execute_query(customer_id, query)
            if not results:
                return []
            
            metrics_list = []
            for row in results:
                # Parse date
                metric_date = datetime.strptime(row.segments.date, '%Y-%m-%d').date()
                
                # Calculate derived metrics
                ctr = row.metrics.ctr if hasattr(row.metrics, 'ctr') else 0.0
                conversion_rate = (row.metrics.conversions_from_interactions_rate 
                                 if hasattr(row.metrics, 'conversions_from_interactions_rate') else 0.0)
                
                metrics = CampaignMetrics(
                    campaign_id=str(row.campaign.id),
                    customer_id=customer_id,
                    metric_date=metric_date,
                    impressions=row.metrics.impressions,
                    clicks=row.metrics.clicks,
                    cost_micros=row.metrics.cost_micros,
                    conversions=row.metrics.conversions,
                    ctr=ctr,
                    cpc_micros=int(row.metrics.average_cpc) if hasattr(row.metrics, 'average_cpc') else 0,
                    conversion_rate=conversion_rate,
                    cost_per_conversion_micros=int(row.metrics.cost_per_conversion) if hasattr(row.metrics, 'cost_per_conversion') else 0
                )
                metrics_list.append(metrics)
            
            logger.info(f"Retrieved {len(metrics_list)} metric records for customer {customer_id}")
            return metrics_list
            
        except Exception as e:
            logger.error(f"Error getting campaign metrics for {customer_id}: {e}")
            return []
    
    def get_campaign_performance_summary(self, customer_id: str, 
                                       days: int = 30) -> Dict[str, Any]:
        """
        Get campaign performance summary
        
        Args:
            customer_id: Google Ads customer ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with performance summary
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get campaigns and metrics
            campaigns = self.get_campaigns(customer_id, [CampaignStatus.ENABLED])
            metrics = self.get_campaign_metrics(customer_id, start_date, end_date)
            
            if not metrics:
                return {'error': 'No performance data available'}
            
            # Aggregate metrics
            total_impressions = sum(m.impressions for m in metrics)
            total_clicks = sum(m.clicks for m in metrics)
            total_cost = sum(m.cost for m in metrics)
            total_conversions = sum(m.conversions for m in metrics)
            
            # Calculate averages
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            avg_cpc = total_cost / total_clicks if total_clicks > 0 else 0
            avg_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            cost_per_conversion = total_cost / total_conversions if total_conversions > 0 else 0
            
            # Get top performing campaigns
            campaign_performance = {}
            for metric in metrics:
                if metric.campaign_id not in campaign_performance:
                    campaign_performance[metric.campaign_id] = {
                        'impressions': 0,
                        'clicks': 0,
                        'cost': 0,
                        'conversions': 0
                    }
                
                perf = campaign_performance[metric.campaign_id]
                perf['impressions'] += metric.impressions
                perf['clicks'] += metric.clicks
                perf['cost'] += metric.cost
                perf['conversions'] += metric.conversions
            
            # Sort by cost (top spending campaigns)
            top_campaigns = sorted(
                campaign_performance.items(),
                key=lambda x: x[1]['cost'],
                reverse=True
            )[:5]
            
            return {
                'period_days': days,
                'total_campaigns': len(campaigns),
                'active_campaigns': len([c for c in campaigns if c.campaign_status == CampaignStatus.ENABLED]),
                'total_impressions': total_impressions,
                'total_clicks': total_clicks,
                'total_cost': total_cost,
                'total_conversions': total_conversions,
                'avg_ctr': avg_ctr,
                'avg_cpc': avg_cpc,
                'avg_conversion_rate': avg_conversion_rate,
                'cost_per_conversion': cost_per_conversion,
                'top_campaigns': top_campaigns,
                'currency_code': 'USD'  # Should get from account info
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign performance summary for {customer_id}: {e}")
            return {'error': str(e)}
    
    def get_campaign_trends(self, customer_id: str, 
                          campaign_id: str, 
                          days: int = 30) -> Dict[str, Any]:
        """
        Get performance trends for a specific campaign
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Specific campaign ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get metrics for specific campaign
            metrics = self.get_campaign_metrics(
                customer_id, start_date, end_date, [campaign_id]
            )
            
            if not metrics:
                return {'error': 'No trend data available'}
            
            # Group by date
            daily_metrics = {}
            for metric in metrics:
                date_str = metric.metric_date.isoformat()
                if date_str not in daily_metrics:
                    daily_metrics[date_str] = {
                        'date': date_str,
                        'impressions': 0,
                        'clicks': 0,
                        'cost': 0,
                        'conversions': 0
                    }
                
                daily = daily_metrics[date_str]
                daily['impressions'] += metric.impressions
                daily['clicks'] += metric.clicks
                daily['cost'] += metric.cost
                daily['conversions'] += metric.conversions
            
            # Convert to sorted list
            trend_data = sorted(daily_metrics.values(), key=lambda x: x['date'])
            
            # Calculate period comparison (last 7 days vs previous 7 days)
            if len(trend_data) >= 14:
                recent_data = trend_data[-7:]
                previous_data = trend_data[-14:-7]
                
                recent_cost = sum(d['cost'] for d in recent_data)
                previous_cost = sum(d['cost'] for d in previous_data)
                
                cost_change = ((recent_cost - previous_cost) / previous_cost * 100) if previous_cost > 0 else 0
            else:
                cost_change = 0
            
            return {
                'campaign_id': campaign_id,
                'period_days': days,
                'daily_data': trend_data,
                'cost_change_percentage': cost_change,
                'trend_direction': 'up' if cost_change > 0 else 'down' if cost_change < 0 else 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign trends for {campaign_id}: {e}")
            return {'error': str(e)}
    
    def get_underperforming_campaigns(self, customer_id: str, 
                                    min_spend: float = 100.0,
                                    max_ctr: float = 1.0,
                                    days: int = 30) -> List[Dict]:
        """
        Identify underperforming campaigns
        
        Args:
            customer_id: Google Ads customer ID
            min_spend: Minimum spend threshold
            max_ctr: Maximum CTR threshold (%)
            days: Number of days to analyze
            
        Returns:
            List of underperforming campaign data
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get campaigns and metrics
            campaigns = self.get_campaigns(customer_id, [CampaignStatus.ENABLED])
            metrics = self.get_campaign_metrics(customer_id, start_date, end_date)
            
            # Aggregate metrics by campaign
            campaign_performance = {}
            for metric in metrics:
                if metric.campaign_id not in campaign_performance:
                    campaign_performance[metric.campaign_id] = {
                        'impressions': 0,
                        'clicks': 0,
                        'cost': 0,
                        'conversions': 0
                    }
                
                perf = campaign_performance[metric.campaign_id]
                perf['impressions'] += metric.impressions
                perf['clicks'] += metric.clicks
                perf['cost'] += metric.cost
                perf['conversions'] += metric.conversions
            
            # Find underperforming campaigns
            underperforming = []
            campaign_dict = {c.campaign_id: c for c in campaigns}
            
            for campaign_id, perf in campaign_performance.items():
                if perf['cost'] < min_spend:
                    continue  # Skip low-spend campaigns
                
                ctr = (perf['clicks'] / perf['impressions'] * 100) if perf['impressions'] > 0 else 0
                
                if ctr <= max_ctr:
                    campaign = campaign_dict.get(campaign_id)
                    underperforming.append({
                        'campaign_id': campaign_id,
                        'campaign_name': campaign.campaign_name if campaign else 'Unknown',
                        'cost': perf['cost'],
                        'ctr': ctr,
                        'clicks': perf['clicks'],
                        'impressions': perf['impressions'],
                        'conversions': perf['conversions'],
                        'issue': 'Low CTR'
                    })
            
            # Sort by cost (highest spend first)
            underperforming.sort(key=lambda x: x['cost'], reverse=True)
            
            return underperforming
            
        except Exception as e:
            logger.error(f"Error finding underperforming campaigns for {customer_id}: {e}")
            return []
    
    def get_kpi_summary(self, customer_ids, days: int = 30) -> KPISummary:
        """
        Get overall KPI summary across multiple accounts or single account
        
        Args:
            customer_ids: Single customer ID (str) or list of customer IDs
            days: Number of days to analyze
            
        Returns:
            KPISummary object
        """
        try:
            # Convert single customer_id to list
            if isinstance(customer_ids, str):
                customer_ids = [customer_ids]
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            total_accounts = len(customer_ids)
            total_campaigns = 0
            total_spend = 0.0
            total_impressions = 0
            total_clicks = 0
            total_conversions = 0.0
            
            for customer_id in customer_ids:
                try:
                    # Get campaigns count
                    campaigns = self.get_campaigns(customer_id)
                    total_campaigns += len(campaigns)
                    
                    # Get metrics
                    metrics = self.get_campaign_metrics(customer_id, start_date, end_date)
                    
                    for metric in metrics:
                        total_spend += metric.cost
                        total_impressions += metric.impressions
                        total_clicks += metric.clicks
                        total_conversions += metric.conversions
                        
                except Exception as e:
                    logger.error(f"Error processing KPIs for {customer_id}: {e}")
                    continue
            
            # Calculate averages
            avg_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0.0
            avg_cpc = total_spend / total_clicks if total_clicks > 0 else 0.0
            avg_conversion_rate = (total_conversions / total_clicks) if total_clicks > 0 else 0.0
            
            return KPISummary(
                total_accounts=total_accounts,
                total_campaigns=total_campaigns,
                total_spend=total_spend,
                total_impressions=total_impressions,
                total_clicks=total_clicks,
                total_conversions=total_conversions,
                average_ctr=avg_ctr,
                average_cpc=avg_cpc,
                average_conversion_rate=avg_conversion_rate,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting KPI summary: {e}")
            return KPISummary()
    
    def export_campaign_data(self, customer_id: str, 
                           start_date: date, 
                           end_date: date) -> List[Dict]:
        """
        Export campaign data for analysis
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of campaign data dictionaries
        """
        try:
            campaigns = self.get_campaigns(customer_id)
            metrics = self.get_campaign_metrics(customer_id, start_date, end_date)
            
            # Create campaign lookup
            campaign_dict = {c.campaign_id: c for c in campaigns}
            
            export_data = []
            for metric in metrics:
                campaign = campaign_dict.get(metric.campaign_id)
                
                export_data.append({
                    'customer_id': customer_id,
                    'campaign_id': metric.campaign_id,
                    'campaign_name': campaign.campaign_name if campaign else 'Unknown',
                    'campaign_status': campaign.campaign_status.value if campaign else 'Unknown',
                    'date': metric.metric_date.isoformat(),
                    'impressions': metric.impressions,
                    'clicks': metric.clicks,
                    'cost': metric.cost,
                    'conversions': metric.conversions,
                    'ctr': metric.ctr,
                    'cpc': metric.cpc,
                    'conversion_rate': metric.conversion_rate,
                    'cost_per_conversion': metric.cost_per_conversion
                })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting campaign data for {customer_id}: {e}")
            return []
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        try:
            return datetime.strptime(date_string, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None