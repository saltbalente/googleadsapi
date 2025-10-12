"""
Report Service for Google Ads Dashboard
Handles custom report generation, data export, and scheduled reporting
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
import csv
import json
import logging
from io import StringIO

from modules.google_ads_client import GoogleAdsClientWrapper
from modules.models import ReportConfig, CampaignMetrics, BillingRecord
from utils.cache import cache_google_ads_data
from utils.rate_limit import rate_limited
from utils.logger import log_api_call
from utils.formatters import format_currency, format_percentage, format_number, format_date

logger = logging.getLogger(__name__)

class ReportService:
    """Service for generating custom reports and data exports"""
    
    def __init__(self, google_ads_client: GoogleAdsClientWrapper):
        """
        Initialize report service
        
        Args:
            google_ads_client: Google Ads API client wrapper
        """
        self.client = google_ads_client
        self.predefined_reports = self._initialize_predefined_reports()
    
    def _initialize_predefined_reports(self) -> Dict[str, ReportConfig]:
        """Initialize predefined report configurations"""
        return {
            'campaign_performance': ReportConfig(
                report_name='Campaign Performance Report',
                customer_ids=[],
                metrics=[
                    'metrics.impressions',
                    'metrics.clicks',
                    'metrics.cost_micros',
                    'metrics.conversions',
                    'metrics.ctr',
                    'metrics.average_cpc',
                    'metrics.conversions_from_interactions_rate'
                ],
                dimensions=[
                    'campaign.id',
                    'campaign.name',
                    'campaign.status',
                    'segments.date'
                ],
                date_range='LAST_30_DAYS'
            ),
            'account_summary': ReportConfig(
                report_name='Account Summary Report',
                customer_ids=[],
                metrics=[
                    'metrics.impressions',
                    'metrics.clicks',
                    'metrics.cost_micros',
                    'metrics.conversions'
                ],
                dimensions=[
                    'customer.id',
                    'customer.descriptive_name',
                    'segments.date'
                ],
                date_range='LAST_7_DAYS'
            ),
            'keyword_performance': ReportConfig(
                report_name='Keyword Performance Report',
                customer_ids=[],
                metrics=[
                    'metrics.impressions',
                    'metrics.clicks',
                    'metrics.cost_micros',
                    'metrics.conversions',
                    'metrics.ctr',
                    'metrics.average_cpc'
                ],
                dimensions=[
                    'campaign.id',
                    'campaign.name',
                    'ad_group.id',
                    'ad_group.name',
                    'ad_group_criterion.keyword.text',
                    'segments.date'
                ],
                date_range='LAST_30_DAYS'
            ),
            'geographic_performance': ReportConfig(
                report_name='Geographic Performance Report',
                customer_ids=[],
                metrics=[
                    'metrics.impressions',
                    'metrics.clicks',
                    'metrics.cost_micros',
                    'metrics.conversions'
                ],
                dimensions=[
                    'campaign.id',
                    'campaign.name',
                    'geographic_view.country_criterion_id',
                    'geographic_view.location_type',
                    'segments.date'
                ],
                date_range='LAST_30_DAYS'
            )
        }
    
    @rate_limited('reports', tokens=1)
    @cache_google_ads_data("", "custom_report", ttl=3600)  # 1 hour
    @log_api_call("", "generate_custom_report")
    def generate_custom_report(self, report_config: ReportConfig) -> Dict[str, Any]:
        """
        Generate a custom report based on configuration
        
        Args:
            report_config: Report configuration
            
        Returns:
            Dictionary with report data and metadata
        """
        try:
            report_data = []
            errors = []
            
            for customer_id in report_config.customer_ids:
                try:
                    # Generate GAQL query
                    query = report_config.to_gaql_query()
                    logger.info(f"Executing report query for {customer_id}: {query}")
                    
                    # Execute query
                    results = self.client.execute_query(customer_id, query)
                    
                    if results:
                        # Process results
                        for row in results:
                            row_data = {'customer_id': customer_id}
                            
                            # Extract dimensions
                            for dimension in report_config.dimensions:
                                row_data[dimension] = self._extract_field_value(row, dimension)
                            
                            # Extract metrics
                            for metric in report_config.metrics:
                                row_data[metric] = self._extract_field_value(row, metric)
                            
                            report_data.append(row_data)
                    
                except Exception as e:
                    error_msg = f"Error generating report for customer {customer_id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return {
                'report_name': report_config.report_name,
                'generated_at': datetime.now().isoformat(),
                'customer_ids': report_config.customer_ids,
                'date_range': report_config.date_range,
                'total_rows': len(report_data),
                'data': report_data,
                'errors': errors,
                'success': len(errors) == 0
            }
            
        except Exception as e:
            logger.error(f"Error generating custom report: {e}")
            return {
                'report_name': report_config.report_name,
                'generated_at': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
    
    def generate_predefined_report(self, report_type: str, 
                                 customer_ids: List[str],
                                 date_range: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a predefined report
        
        Args:
            report_type: Type of predefined report
            customer_ids: List of customer IDs
            date_range: Optional date range override
            
        Returns:
            Dictionary with report data
        """
        if report_type not in self.predefined_reports:
            return {
                'error': f'Unknown report type: {report_type}',
                'available_types': list(self.predefined_reports.keys()),
                'success': False
            }
        
        # Get report config and customize
        report_config = self.predefined_reports[report_type]
        report_config.customer_ids = customer_ids
        
        if date_range:
            report_config.date_range = date_range
        
        return self.generate_custom_report(report_config)
    
    def export_to_csv(self, report_data: Dict[str, Any]) -> str:
        """
        Export report data to CSV format
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            CSV string
        """
        if not report_data.get('data'):
            return "No data to export"
        
        output = StringIO()
        
        # Get field names from first row
        fieldnames = list(report_data['data'][0].keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write data rows with formatting
        for row in report_data['data']:
            formatted_row = {}
            for key, value in row.items():
                # Format specific field types
                if 'cost_micros' in key and isinstance(value, (int, float)):
                    formatted_row[key] = value / 1_000_000  # Convert to currency units
                elif 'ctr' in key and isinstance(value, (int, float)):
                    formatted_row[key] = f"{value * 100:.2f}%"
                elif 'date' in key and value:
                    formatted_row[key] = format_date(value)
                else:
                    formatted_row[key] = value
            
            writer.writerow(formatted_row)
        
        return output.getvalue()
    
    def export_to_json(self, report_data: Dict[str, Any], pretty: bool = True) -> str:
        """
        Export report data to JSON format
        
        Args:
            report_data: Report data dictionary
            pretty: Whether to format JSON with indentation
            
        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(report_data, indent=2, default=str)
        else:
            return json.dumps(report_data, default=str)
    
    def get_performance_insights(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Generate performance insights report
        
        Args:
            customer_id: Google Ads customer ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with performance insights
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Generate campaign performance report
            report_config = ReportConfig(
                report_name='Performance Insights',
                customer_ids=[customer_id],
                metrics=[
                    'metrics.impressions',
                    'metrics.clicks',
                    'metrics.cost_micros',
                    'metrics.conversions',
                    'metrics.ctr',
                    'metrics.average_cpc'
                ],
                dimensions=[
                    'campaign.id',
                    'campaign.name',
                    'campaign.status'
                ],
                date_range=f'{start_date.strftime("%Y-%m-%d")} AND {end_date.strftime("%Y-%m-%d")}'
            )
            
            report = self.generate_custom_report(report_config)
            
            if not report.get('success') or not report.get('data'):
                return {'error': 'Could not generate performance insights'}
            
            # Analyze data for insights
            insights = self._analyze_performance_data(report['data'])
            
            return {
                'customer_id': customer_id,
                'analysis_period': f"{start_date} to {end_date}",
                'insights': insights,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating performance insights for {customer_id}: {e}")
            return {'error': str(e)}
    
    def get_spend_analysis(self, customer_ids: List[str], days: int = 30) -> Dict[str, Any]:
        """
        Generate spend analysis report across multiple accounts
        
        Args:
            customer_ids: List of customer IDs
            days: Number of days to analyze
            
        Returns:
            Dictionary with spend analysis
        """
        try:
            spend_data = []
            total_spend = 0.0
            
            for customer_id in customer_ids:
                try:
                    # Get account info
                    account_info = self.client.get_account_info(customer_id)
                    account_name = account_info.get('account_name', customer_id) if account_info else customer_id
                    
                    # Generate spend report
                    report_config = ReportConfig(
                        report_name='Spend Analysis',
                        customer_ids=[customer_id],
                        metrics=['metrics.cost_micros'],
                        dimensions=['segments.date'],
                        date_range=f'LAST_{days}_DAYS'
                    )
                    
                    report = self.generate_custom_report(report_config)
                    
                    if report.get('success') and report.get('data'):
                        # Calculate total spend for this account
                        account_spend = sum(
                            row.get('metrics.cost_micros', 0) / 1_000_000 
                            for row in report['data']
                        )
                        
                        spend_data.append({
                            'customer_id': customer_id,
                            'account_name': account_name,
                            'total_spend': account_spend,
                            'daily_data': report['data']
                        })
                        
                        total_spend += account_spend
                    
                except Exception as e:
                    logger.error(f"Error analyzing spend for {customer_id}: {e}")
            
            # Calculate spend distribution
            for account in spend_data:
                account['spend_percentage'] = (
                    (account['total_spend'] / total_spend * 100) if total_spend > 0 else 0
                )
            
            # Sort by spend
            spend_data.sort(key=lambda x: x['total_spend'], reverse=True)
            
            return {
                'analysis_period_days': days,
                'total_accounts': len(customer_ids),
                'total_spend': total_spend,
                'account_breakdown': spend_data,
                'top_spender': spend_data[0] if spend_data else None,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating spend analysis: {e}")
            return {'error': str(e)}
    
    def schedule_report(self, report_config: ReportConfig, 
                       schedule: str, 
                       export_format: str = 'csv') -> Dict[str, Any]:
        """
        Schedule a report for regular generation (placeholder for future implementation)
        
        Args:
            report_config: Report configuration
            schedule: Schedule string (e.g., 'daily', 'weekly', 'monthly')
            export_format: Export format ('csv', 'json')
            
        Returns:
            Dictionary with scheduling result
        """
        # This would integrate with a task scheduler in a production environment
        return {
            'message': 'Report scheduling is not yet implemented',
            'report_name': report_config.report_name,
            'schedule': schedule,
            'format': export_format,
            'status': 'pending_implementation'
        }
    
    def _extract_field_value(self, row: Any, field_path: str) -> Any:
        """
        Extract field value from Google Ads API response row
        
        Args:
            row: API response row
            field_path: Dot-separated field path (e.g., 'campaign.name')
            
        Returns:
            Field value or None if not found
        """
        try:
            # Split field path and traverse
            parts = field_path.split('.')
            value = row
            
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
            
            # Handle special cases
            if hasattr(value, 'name'):  # Enum values
                return value.name
            elif hasattr(value, 'value'):  # Some wrapped values
                return value.value
            else:
                return value
                
        except Exception as e:
            logger.debug(f"Error extracting field {field_path}: {e}")
            return None
    
    def _analyze_performance_data(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Analyze performance data to generate insights
        
        Args:
            data: List of performance data rows
            
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        if not data:
            return insights
        
        try:
            # Aggregate data by campaign
            campaign_data = {}
            for row in data:
                campaign_id = row.get('campaign.id')
                if not campaign_id:
                    continue
                
                if campaign_id not in campaign_data:
                    campaign_data[campaign_id] = {
                        'name': row.get('campaign.name', 'Unknown'),
                        'impressions': 0,
                        'clicks': 0,
                        'cost': 0,
                        'conversions': 0
                    }
                
                cd = campaign_data[campaign_id]
                cd['impressions'] += row.get('metrics.impressions', 0)
                cd['clicks'] += row.get('metrics.clicks', 0)
                cd['cost'] += row.get('metrics.cost_micros', 0) / 1_000_000
                cd['conversions'] += row.get('metrics.conversions', 0)
            
            # Generate insights
            if campaign_data:
                # Top performing campaign by conversions
                top_conversions = max(campaign_data.items(), key=lambda x: x[1]['conversions'])
                if top_conversions[1]['conversions'] > 0:
                    insights.append({
                        'type': 'top_performer',
                        'title': 'Top Converting Campaign',
                        'description': f"{top_conversions[1]['name']} generated {top_conversions[1]['conversions']} conversions",
                        'campaign_id': top_conversions[0],
                        'value': top_conversions[1]['conversions']
                    })
                
                # Highest spend campaign
                top_spend = max(campaign_data.items(), key=lambda x: x[1]['cost'])
                insights.append({
                    'type': 'high_spend',
                    'title': 'Highest Spend Campaign',
                    'description': f"{top_spend[1]['name']} spent {format_currency(top_spend[1]['cost'])}",
                    'campaign_id': top_spend[0],
                    'value': top_spend[1]['cost']
                })
                
                # Low CTR campaigns
                low_ctr_campaigns = []
                for campaign_id, cd in campaign_data.items():
                    if cd['impressions'] > 1000:  # Only consider campaigns with significant impressions
                        ctr = (cd['clicks'] / cd['impressions']) * 100
                        if ctr < 1.0:  # CTR below 1%
                            low_ctr_campaigns.append((campaign_id, cd, ctr))
                
                if low_ctr_campaigns:
                    insights.append({
                        'type': 'optimization_opportunity',
                        'title': 'Low CTR Campaigns',
                        'description': f"{len(low_ctr_campaigns)} campaigns have CTR below 1%",
                        'campaigns': [
                            {
                                'campaign_id': cid,
                                'name': cd['name'],
                                'ctr': ctr
                            }
                            for cid, cd, ctr in low_ctr_campaigns[:3]  # Top 3
                        ]
                    })
        
        except Exception as e:
            logger.error(f"Error analyzing performance data: {e}")
        
        return insights