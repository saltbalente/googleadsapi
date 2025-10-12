"""
Alert Service for Google Ads Dashboard
Handles alert rules, monitoring, and notifications
"""

from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from enum import Enum

from modules.google_ads_client import GoogleAdsClientWrapper
from modules.models import (
    AlertRule, AlertInstance, AlertPriority, AlertStatus,
    CampaignMetrics, BillingRecord
)
from utils.cache import cache_google_ads_data
from utils.rate_limit import rate_limited
from utils.logger import log_api_call
from utils.formatters import format_currency, format_percentage, format_number

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Types of alerts that can be configured"""
    BUDGET_EXCEEDED = "budget_exceeded"
    LOW_CTR = "low_ctr"
    HIGH_CPC = "high_cpc"
    LOW_CONVERSIONS = "low_conversions"
    CAMPAIGN_PAUSED = "campaign_paused"
    SPEND_ANOMALY = "spend_anomaly"
    PERFORMANCE_DROP = "performance_drop"
    BUDGET_DEPLETION = "budget_depletion"

class AlertService:
    """Service for managing alerts and monitoring"""
    
    def __init__(self, google_ads_client: GoogleAdsClientWrapper):
        """
        Initialize alert service
        
        Args:
            google_ads_client: Google Ads API client wrapper
        """
        self.client = google_ads_client
        self.alert_rules: List[AlertRule] = []
        self.alert_instances: List[AlertInstance] = []
        self.notification_handlers: Dict[str, Callable] = {}
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                rule_id="budget_90_percent",
                rule_name="Budget 90% Depleted",
                alert_type=AlertType.BUDGET_DEPLETION.value,
                conditions={
                    "budget_utilization_threshold": 0.9,
                    "time_remaining_days": 7
                },
                priority=AlertPriority.HIGH,
                enabled=True,
                customer_ids=[],
                notification_channels=["email", "dashboard"]
            ),
            AlertRule(
                rule_id="low_ctr_campaigns",
                rule_name="Low CTR Campaigns",
                alert_type=AlertType.LOW_CTR.value,
                conditions={
                    "ctr_threshold": 0.01,  # 1%
                    "min_impressions": 1000,
                    "days_to_check": 7
                },
                priority=AlertPriority.MEDIUM,
                enabled=True,
                customer_ids=[],
                notification_channels=["dashboard"]
            ),
            AlertRule(
                rule_id="high_cpc_alert",
                rule_name="High CPC Alert",
                alert_type=AlertType.HIGH_CPC.value,
                conditions={
                    "cpc_threshold": 5.0,  # $5
                    "min_clicks": 100,
                    "days_to_check": 3
                },
                priority=AlertPriority.MEDIUM,
                enabled=True,
                customer_ids=[],
                notification_channels=["email", "dashboard"]
            ),
            AlertRule(
                rule_id="campaign_paused",
                rule_name="Campaign Paused",
                alert_type=AlertType.CAMPAIGN_PAUSED.value,
                conditions={},
                priority=AlertPriority.HIGH,
                enabled=True,
                customer_ids=[],
                notification_channels=["email", "dashboard"]
            ),
            AlertRule(
                rule_id="spend_anomaly",
                rule_name="Unusual Spend Pattern",
                alert_type=AlertType.SPEND_ANOMALY.value,
                conditions={
                    "deviation_threshold": 2.0,  # 2x standard deviation
                    "baseline_days": 14,
                    "comparison_days": 3
                },
                priority=AlertPriority.HIGH,
                enabled=True,
                customer_ids=[],
                notification_channels=["email", "dashboard"]
            )
        ]
        
        self.alert_rules.extend(default_rules)
    
    def add_alert_rule(self, alert_rule: AlertRule) -> bool:
        """
        Add a new alert rule
        
        Args:
            alert_rule: Alert rule to add
            
        Returns:
            True if added successfully
        """
        try:
            # Check if rule with same ID already exists
            existing_rule = next((r for r in self.alert_rules if r.rule_id == alert_rule.rule_id), None)
            if existing_rule:
                logger.warning(f"Alert rule with ID {alert_rule.rule_id} already exists")
                return False
            
            self.alert_rules.append(alert_rule)
            logger.info(f"Added alert rule: {alert_rule.rule_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding alert rule: {e}")
            return False
    
    def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing alert rule
        
        Args:
            rule_id: ID of the rule to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            rule = next((r for r in self.alert_rules if r.rule_id == rule_id), None)
            if not rule:
                logger.warning(f"Alert rule with ID {rule_id} not found")
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(rule, field):
                    setattr(rule, field, value)
            
            rule.updated_at = datetime.now()
            logger.info(f"Updated alert rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating alert rule {rule_id}: {e}")
            return False
    
    def delete_alert_rule(self, rule_id: str) -> bool:
        """
        Delete an alert rule
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            rule = next((r for r in self.alert_rules if r.rule_id == rule_id), None)
            if not rule:
                logger.warning(f"Alert rule with ID {rule_id} not found")
                return False
            
            self.alert_rules.remove(rule)
            logger.info(f"Deleted alert rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting alert rule {rule_id}: {e}")
            return False
    
    def get_alert_rules(self, customer_id: Optional[str] = None, 
                       enabled_only: bool = False) -> List[AlertRule]:
        """
        Get alert rules, optionally filtered
        
        Args:
            customer_id: Filter by customer ID
            enabled_only: Only return enabled rules
            
        Returns:
            List of alert rules
        """
        rules = self.alert_rules
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        if customer_id:
            rules = [r for r in rules if not r.customer_ids or customer_id in r.customer_ids]
        
        return rules
    
    @rate_limited('general', tokens=3)
    @log_api_call("", "check_alerts")
    def check_alerts(self, customer_ids: Optional[List[str]] = None) -> List[AlertInstance]:
        """
        Check all alert rules and generate alert instances
        
        Args:
            customer_ids: Optional list of customer IDs to check
            
        Returns:
            List of new alert instances
        """
        new_alerts = []
        
        try:
            # Get customer IDs to check
            if not customer_ids:
                customer_ids = self.client.get_customer_ids()
            
            # Check each enabled rule
            enabled_rules = self.get_alert_rules(enabled_only=True)
            
            for rule in enabled_rules:
                try:
                    # Filter customer IDs for this rule
                    rule_customer_ids = customer_ids
                    if rule.customer_ids:
                        rule_customer_ids = [cid for cid in customer_ids if cid in rule.customer_ids]
                    
                    # Check rule for each customer
                    for customer_id in rule_customer_ids:
                        alert_instances = self._check_rule_for_customer(rule, customer_id)
                        new_alerts.extend(alert_instances)
                
                except Exception as e:
                    logger.error(f"Error checking rule {rule.rule_id}: {e}")
            
            # Store new alerts
            self.alert_instances.extend(new_alerts)
            
            # Send notifications for new alerts
            for alert in new_alerts:
                self._send_notifications(alert)
            
            logger.info(f"Alert check completed. Found {len(new_alerts)} new alerts")
            return new_alerts
            
        except Exception as e:
            logger.error(f"Error during alert check: {e}")
            return []
    
    def _check_rule_for_customer(self, rule: AlertRule, customer_id: str) -> List[AlertInstance]:
        """
        Check a specific rule for a customer
        
        Args:
            rule: Alert rule to check
            customer_id: Customer ID
            
        Returns:
            List of alert instances
        """
        alerts = []
        
        try:
            alert_type = AlertType(rule.alert_type)
            
            if alert_type == AlertType.BUDGET_EXCEEDED:
                alerts.extend(self._check_budget_exceeded(rule, customer_id))
            elif alert_type == AlertType.BUDGET_DEPLETION:
                alerts.extend(self._check_budget_depletion(rule, customer_id))
            elif alert_type == AlertType.LOW_CTR:
                alerts.extend(self._check_low_ctr(rule, customer_id))
            elif alert_type == AlertType.HIGH_CPC:
                alerts.extend(self._check_high_cpc(rule, customer_id))
            elif alert_type == AlertType.CAMPAIGN_PAUSED:
                alerts.extend(self._check_campaign_paused(rule, customer_id))
            elif alert_type == AlertType.SPEND_ANOMALY:
                alerts.extend(self._check_spend_anomaly(rule, customer_id))
            elif alert_type == AlertType.PERFORMANCE_DROP:
                alerts.extend(self._check_performance_drop(rule, customer_id))
        
        except Exception as e:
            logger.error(f"Error checking rule {rule.rule_id} for customer {customer_id}: {e}")
        
        return alerts
    
    def _check_budget_depletion(self, rule: AlertRule, customer_id: str) -> List[AlertInstance]:
        """Check for budget depletion alerts"""
        alerts = []
        
        try:
            # Get campaign budgets and spend
            query = """
                SELECT 
                    campaign.id,
                    campaign.name,
                    campaign_budget.amount_micros,
                    metrics.cost_micros
                FROM campaign 
                WHERE campaign.status = 'ENABLED'
                AND segments.date DURING LAST_30_DAYS
            """
            
            results = self.client.execute_query(customer_id, query)
            if not results:
                return alerts
            
            # Aggregate spend by campaign
            campaign_data = {}
            for row in results:
                campaign_id = row.campaign.id
                if campaign_id not in campaign_data:
                    campaign_data[campaign_id] = {
                        'name': row.campaign.name,
                        'budget': row.campaign_budget.amount_micros / 1_000_000,
                        'spend': 0
                    }
                campaign_data[campaign_id]['spend'] += row.metrics.cost_micros / 1_000_000
            
            # Check budget utilization
            threshold = rule.conditions.get('budget_utilization_threshold', 0.9)
            
            for campaign_id, data in campaign_data.items():
                if data['budget'] > 0:
                    utilization = data['spend'] / data['budget']
                    if utilization >= threshold:
                        alert = AlertInstance(
                            alert_id=f"{rule.rule_id}_{customer_id}_{campaign_id}_{datetime.now().strftime('%Y%m%d')}",
                            rule_id=rule.rule_id,
                            customer_id=customer_id,
                            alert_type=rule.alert_type,
                            priority=rule.priority,
                            status=AlertStatus.ACTIVE,
                            title=f"Budget {utilization*100:.1f}% depleted",
                            message=f"Campaign '{data['name']}' has used {format_percentage(utilization)} of its budget",
                            details={
                                'campaign_id': campaign_id,
                                'campaign_name': data['name'],
                                'budget': data['budget'],
                                'spend': data['spend'],
                                'utilization': utilization
                            },
                            triggered_at=datetime.now()
                        )
                        alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error checking budget depletion for {customer_id}: {e}")
        
        return alerts
    
    def _check_low_ctr(self, rule: AlertRule, customer_id: str) -> List[AlertInstance]:
        """Check for low CTR alerts"""
        alerts = []
        
        try:
            days = rule.conditions.get('days_to_check', 7)
            ctr_threshold = rule.conditions.get('ctr_threshold', 0.01)
            min_impressions = rule.conditions.get('min_impressions', 1000)
            
            query = f"""
                SELECT 
                    campaign.id,
                    campaign.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.ctr
                FROM campaign 
                WHERE campaign.status = 'ENABLED'
                AND segments.date DURING LAST_{days}_DAYS
            """
            
            results = self.client.execute_query(customer_id, query)
            if not results:
                return alerts
            
            # Aggregate by campaign
            campaign_data = {}
            for row in results:
                campaign_id = row.campaign.id
                if campaign_id not in campaign_data:
                    campaign_data[campaign_id] = {
                        'name': row.campaign.name,
                        'impressions': 0,
                        'clicks': 0
                    }
                campaign_data[campaign_id]['impressions'] += row.metrics.impressions
                campaign_data[campaign_id]['clicks'] += row.metrics.clicks
            
            # Check CTR
            for campaign_id, data in campaign_data.items():
                if data['impressions'] >= min_impressions:
                    ctr = data['clicks'] / data['impressions'] if data['impressions'] > 0 else 0
                    if ctr < ctr_threshold:
                        alert = AlertInstance(
                            alert_id=f"{rule.rule_id}_{customer_id}_{campaign_id}_{datetime.now().strftime('%Y%m%d')}",
                            rule_id=rule.rule_id,
                            customer_id=customer_id,
                            alert_type=rule.alert_type,
                            priority=rule.priority,
                            status=AlertStatus.ACTIVE,
                            title=f"Low CTR: {ctr*100:.2f}%",
                            message=f"Campaign '{data['name']}' has CTR of {format_percentage(ctr)} (below {format_percentage(ctr_threshold)})",
                            details={
                                'campaign_id': campaign_id,
                                'campaign_name': data['name'],
                                'ctr': ctr,
                                'threshold': ctr_threshold,
                                'impressions': data['impressions'],
                                'clicks': data['clicks']
                            },
                            triggered_at=datetime.now()
                        )
                        alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error checking low CTR for {customer_id}: {e}")
        
        return alerts
    
    def _check_high_cpc(self, rule: AlertRule, customer_id: str) -> List[AlertInstance]:
        """Check for high CPC alerts"""
        alerts = []
        
        try:
            days = rule.conditions.get('days_to_check', 3)
            cpc_threshold = rule.conditions.get('cpc_threshold', 5.0)
            min_clicks = rule.conditions.get('min_clicks', 100)
            
            query = f"""
                SELECT 
                    campaign.id,
                    campaign.name,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.average_cpc
                FROM campaign 
                WHERE campaign.status = 'ENABLED'
                AND segments.date DURING LAST_{days}_DAYS
            """
            
            results = self.client.execute_query(customer_id, query)
            if not results:
                return alerts
            
            # Aggregate by campaign
            campaign_data = {}
            for row in results:
                campaign_id = row.campaign.id
                if campaign_id not in campaign_data:
                    campaign_data[campaign_id] = {
                        'name': row.campaign.name,
                        'clicks': 0,
                        'cost': 0
                    }
                campaign_data[campaign_id]['clicks'] += row.metrics.clicks
                campaign_data[campaign_id]['cost'] += row.metrics.cost_micros / 1_000_000
            
            # Check CPC
            for campaign_id, data in campaign_data.items():
                if data['clicks'] >= min_clicks:
                    cpc = data['cost'] / data['clicks'] if data['clicks'] > 0 else 0
                    if cpc > cpc_threshold:
                        alert = AlertInstance(
                            alert_id=f"{rule.rule_id}_{customer_id}_{campaign_id}_{datetime.now().strftime('%Y%m%d')}",
                            rule_id=rule.rule_id,
                            customer_id=customer_id,
                            alert_type=rule.alert_type,
                            priority=rule.priority,
                            status=AlertStatus.ACTIVE,
                            title=f"High CPC: {format_currency(cpc)}",
                            message=f"Campaign '{data['name']}' has CPC of {format_currency(cpc)} (above {format_currency(cpc_threshold)})",
                            details={
                                'campaign_id': campaign_id,
                                'campaign_name': data['name'],
                                'cpc': cpc,
                                'threshold': cpc_threshold,
                                'clicks': data['clicks'],
                                'cost': data['cost']
                            },
                            triggered_at=datetime.now()
                        )
                        alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error checking high CPC for {customer_id}: {e}")
        
        return alerts
    
    def _check_campaign_paused(self, rule: AlertRule, customer_id: str) -> List[AlertInstance]:
        """Check for paused campaigns"""
        alerts = []
        
        try:
            query = """
                SELECT 
                    campaign.id,
                    campaign.name,
                    campaign.status
                FROM campaign 
                WHERE campaign.status = 'PAUSED'
            """
            
            results = self.client.execute_query(customer_id, query)
            if not results:
                return alerts
            
            for row in results:
                alert = AlertInstance(
                    alert_id=f"{rule.rule_id}_{customer_id}_{row.campaign.id}_{datetime.now().strftime('%Y%m%d')}",
                    rule_id=rule.rule_id,
                    customer_id=customer_id,
                    alert_type=rule.alert_type,
                    priority=rule.priority,
                    status=AlertStatus.ACTIVE,
                    title="Campaign Paused",
                    message=f"Campaign '{row.campaign.name}' is currently paused",
                    details={
                        'campaign_id': row.campaign.id,
                        'campaign_name': row.campaign.name,
                        'status': row.campaign.status.name
                    },
                    triggered_at=datetime.now()
                )
                alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error checking paused campaigns for {customer_id}: {e}")
        
        return alerts
    
    def _check_spend_anomaly(self, rule: AlertRule, customer_id: str) -> List[AlertInstance]:
        """Check for spend anomalies"""
        alerts = []
        
        try:
            baseline_days = rule.conditions.get('baseline_days', 14)
            comparison_days = rule.conditions.get('comparison_days', 3)
            deviation_threshold = rule.conditions.get('deviation_threshold', 2.0)
            
            # Get baseline spend data
            baseline_query = f"""
                SELECT 
                    segments.date,
                    metrics.cost_micros
                FROM campaign 
                WHERE segments.date DURING LAST_{baseline_days}_DAYS
            """
            
            baseline_results = self.client.execute_query(customer_id, baseline_query)
            if not baseline_results:
                return alerts
            
            # Calculate baseline statistics
            daily_spends = [row.metrics.cost_micros / 1_000_000 for row in baseline_results]
            if len(daily_spends) < 7:  # Need at least a week of data
                return alerts
            
            avg_spend = sum(daily_spends) / len(daily_spends)
            variance = sum((x - avg_spend) ** 2 for x in daily_spends) / len(daily_spends)
            std_dev = variance ** 0.5
            
            # Get recent spend data
            recent_query = f"""
                SELECT 
                    segments.date,
                    metrics.cost_micros
                FROM campaign 
                WHERE segments.date DURING LAST_{comparison_days}_DAYS
            """
            
            recent_results = self.client.execute_query(customer_id, recent_query)
            if not recent_results:
                return alerts
            
            recent_spends = [row.metrics.cost_micros / 1_000_000 for row in recent_results]
            recent_avg = sum(recent_spends) / len(recent_spends)
            
            # Check for anomaly
            if std_dev > 0:
                z_score = abs(recent_avg - avg_spend) / std_dev
                if z_score > deviation_threshold:
                    direction = "increased" if recent_avg > avg_spend else "decreased"
                    alert = AlertInstance(
                        alert_id=f"{rule.rule_id}_{customer_id}_{datetime.now().strftime('%Y%m%d')}",
                        rule_id=rule.rule_id,
                        customer_id=customer_id,
                        alert_type=rule.alert_type,
                        priority=rule.priority,
                        status=AlertStatus.ACTIVE,
                        title=f"Spend Anomaly Detected",
                        message=f"Daily spend has {direction} significantly: {format_currency(recent_avg)} vs {format_currency(avg_spend)} baseline",
                        details={
                            'recent_avg_spend': recent_avg,
                            'baseline_avg_spend': avg_spend,
                            'z_score': z_score,
                            'threshold': deviation_threshold,
                            'direction': direction
                        },
                        triggered_at=datetime.now()
                    )
                    alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error checking spend anomaly for {customer_id}: {e}")
        
        return alerts
    
    def _check_performance_drop(self, rule: AlertRule, customer_id: str) -> List[AlertInstance]:
        """Check for performance drops (placeholder implementation)"""
        # This would compare recent performance metrics to historical averages
        # Implementation would be similar to spend anomaly but for CTR, conversion rate, etc.
        return []
    
    def _check_budget_exceeded(self, rule: AlertRule, customer_id: str) -> List[AlertInstance]:
        """Check for budget exceeded alerts (placeholder implementation)"""
        # This would check if actual spend exceeds budget limits
        return []
    
    def get_active_alerts(self, customer_id: Optional[str] = None,
                         priority: Optional[AlertPriority] = None) -> List[AlertInstance]:
        """
        Get active alert instances
        
        Args:
            customer_id: Filter by customer ID
            priority: Filter by priority
            
        Returns:
            List of active alert instances
        """
        alerts = [a for a in self.alert_instances if a.status == AlertStatus.ACTIVE]
        
        if customer_id:
            alerts = [a for a in alerts if a.customer_id == customer_id]
        
        if priority:
            alerts = [a for a in alerts if a.priority == priority]
        
        # Sort by priority and triggered time
        priority_order = {AlertPriority.HIGH: 0, AlertPriority.MEDIUM: 1, AlertPriority.LOW: 2}
        alerts.sort(key=lambda x: (priority_order.get(x.priority, 3), x.triggered_at), reverse=True)
        
        return alerts
    
    def acknowledge_alert(self, alert_id: str, user_id: Optional[str] = None) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert instance ID
            user_id: User acknowledging the alert
            
        Returns:
            True if acknowledged successfully
        """
        try:
            alert = next((a for a in self.alert_instances if a.alert_id == alert_id), None)
            if not alert:
                return False
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = user_id
            
            logger.info(f"Alert {alert_id} acknowledged by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False
    
    def resolve_alert(self, alert_id: str, user_id: Optional[str] = None,
                     resolution_notes: Optional[str] = None) -> bool:
        """
        Resolve an alert
        
        Args:
            alert_id: Alert instance ID
            user_id: User resolving the alert
            resolution_notes: Optional resolution notes
            
        Returns:
            True if resolved successfully
        """
        try:
            alert = next((a for a in self.alert_instances if a.alert_id == alert_id), None)
            if not alert:
                return False
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            alert.resolved_by = user_id
            if resolution_notes:
                alert.details['resolution_notes'] = resolution_notes
            
            logger.info(f"Alert {alert_id} resolved by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
    
    def register_notification_handler(self, channel: str, handler: Callable):
        """
        Register a notification handler for a channel
        
        Args:
            channel: Notification channel name
            handler: Callable to handle notifications
        """
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for channel: {channel}")
    
    def _send_notifications(self, alert: AlertInstance):
        """
        Send notifications for an alert
        
        Args:
            alert: Alert instance to send notifications for
        """
        try:
            # Get the rule to determine notification channels
            rule = next((r for r in self.alert_rules if r.rule_id == alert.rule_id), None)
            if not rule:
                return
            
            # Send to each configured channel
            for channel in rule.notification_channels:
                if channel in self.notification_handlers:
                    try:
                        self.notification_handlers[channel](alert)
                    except Exception as e:
                        logger.error(f"Error sending notification to {channel}: {e}")
                else:
                    logger.warning(f"No handler registered for notification channel: {channel}")
        
        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.alert_id}: {e}")
    
    def get_alert_summary(self, customer_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get alert summary statistics
        
        Args:
            customer_ids: Optional list of customer IDs to filter by
            
        Returns:
            Dictionary with alert summary
        """
        try:
            alerts = self.alert_instances
            
            if customer_ids:
                alerts = [a for a in alerts if a.customer_id in customer_ids]
            
            # Count by status
            status_counts = {}
            for status in AlertStatus:
                status_counts[status.value] = len([a for a in alerts if a.status == status])
            
            # Count by priority
            priority_counts = {}
            for priority in AlertPriority:
                priority_counts[priority.value] = len([a for a in alerts if a.priority == priority])
            
            # Recent alerts (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_alerts = [a for a in alerts if a.triggered_at >= recent_cutoff]
            
            return {
                'total_alerts': len(alerts),
                'active_alerts': status_counts.get('active', 0),
                'acknowledged_alerts': status_counts.get('acknowledged', 0),
                'resolved_alerts': status_counts.get('resolved', 0),
                'high_priority_alerts': priority_counts.get('high', 0),
                'medium_priority_alerts': priority_counts.get('medium', 0),
                'low_priority_alerts': priority_counts.get('low', 0),
                'recent_alerts_24h': len(recent_alerts),
                'total_rules': len(self.alert_rules),
                'enabled_rules': len([r for r in self.alert_rules if r.enabled])
            }
            
        except Exception as e:
            logger.error(f"Error generating alert summary: {e}")
            return {'error': str(e)}