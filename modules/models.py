"""
Data Models and DTOs for Google Ads Dashboard
Defines data structures for metrics, accounts, campaigns, etc.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from enum import Enum

class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AlertStatus(Enum):
    ACTIVE = "active"
    READ = "read"
    RESOLVED = "resolved"

class CampaignStatus(Enum):
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"

@dataclass
class Account:
    """Google Ads account information"""
    customer_id: str
    account_name: str
    currency_code: str = "USD"
    time_zone: str = "UTC"
    monthly_budget: float = 0.0
    is_active: bool = True
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class Campaign:
    """Campaign information"""
    campaign_id: str
    customer_id: str
    campaign_name: str
    campaign_status: CampaignStatus
    campaign_type: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class CampaignMetrics:
    """Campaign performance metrics"""
    campaign_id: str
    customer_id: str
    metric_date: date
    impressions: int = 0
    clicks: int = 0
    cost_micros: int = 0
    conversions: float = 0.0
    ctr: float = 0.0
    cpc_micros: int = 0
    conversion_rate: float = 0.0
    cost_per_conversion_micros: int = 0
    
    @property
    def cost(self) -> float:
        """Cost in currency units (not micros)"""
        return self.cost_micros / 1_000_000
    
    @property
    def cpc(self) -> float:
        """Cost per click in currency units"""
        return self.cpc_micros / 1_000_000
    
    @property
    def cost_per_conversion(self) -> float:
        """Cost per conversion in currency units"""
        return self.cost_per_conversion_micros / 1_000_000
    
    @property
    def roas(self) -> float:
        """Return on ad spend (requires conversion value)"""
        # This would need conversion value data from the API
        return 0.0

@dataclass
class BillingRecord:
    """Billing and spend information"""
    customer_id: str
    billing_date: date
    amount_micros: int
    currency_code: str = "USD"
    billing_status: str = "active"
    
    @property
    def amount(self) -> float:
        """Amount in currency units (not micros)"""
        return self.amount_micros / 1_000_000

@dataclass
class BillingSummary:
    """Monthly billing summary"""
    customer_id: str
    current_spend: float
    monthly_budget: float
    currency_code: str = "USD"
    projected_spend: float = 0.0
    days_remaining: int = 0
    
    @property
    def budget_utilization(self) -> float:
        """Budget utilization percentage (0.0 to 1.0+)"""
        if self.monthly_budget <= 0:
            return 0.0
        return self.current_spend / self.monthly_budget
    
    @property
    def is_over_budget(self) -> bool:
        """Check if spending is over budget"""
        return self.current_spend > self.monthly_budget
    
    @property
    def remaining_budget(self) -> float:
        """Remaining budget amount"""
        return max(0, self.monthly_budget - self.current_spend)

@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    # Optional customer scope; if None, applies to all unless filtered by customer_ids
    customer_id: Optional[str] = None
    # Name and type used across services
    rule_name: str = ""
    alert_type: str = ""  # e.g., values from AlertType enum
    # Generic conditions bag used by AlertService
    conditions: Dict[str, Any] = field(default_factory=dict)
    # Priority and enabled flag (keep legacy is_active for compatibility)
    priority: AlertPriority = AlertPriority.MEDIUM
    enabled: bool = True
    is_active: bool = True
    # Optional legacy fields for rule evaluation (kept for compatibility)
    rule_type: Optional[str] = None  # 'budget', 'performance', 'campaign_status'
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    comparison_operator: Optional[str] = None  # 'greater_than', 'less_than', 'equals'
    # Target customers and notification channels
    customer_ids: List[str] = field(default_factory=list)
    notification_channels: List[str] = field(default_factory=list)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # keep both flags in sync for backward compatibility
        if hasattr(self, 'is_active'):
            self.enabled = bool(self.is_active)

    def evaluate(self, actual_value: float) -> bool:
        """Evaluate if the rule should trigger an alert (legacy support)"""
        if not self.enabled:
            return False
        # If legacy fields aren't set, treat as non-evaluable here
        if self.comparison_operator is None or self.threshold_value is None:
            return False
        if self.comparison_operator == 'greater_than':
            return actual_value > self.threshold_value
        elif self.comparison_operator == 'less_than':
            return actual_value < self.threshold_value
        elif self.comparison_operator == 'equals':
            return abs(actual_value - self.threshold_value) < 0.001
        return False

@dataclass
class AlertInstance:
    """Individual alert instance"""
    alert_id: str
    rule_id: str
    customer_id: str
    triggered_at: datetime
    # Optional fields commonly used by AlertService
    alert_type: Optional[str] = None
    title: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    # Legacy fields kept optional for compatibility
    actual_value: Optional[float] = None
    threshold_value: Optional[float] = None
    priority: AlertPriority = AlertPriority.MEDIUM
    status: AlertStatus = AlertStatus.ACTIVE
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def __post_init__(self):
        if not self.alert_id:
            # Generate alert ID based on timestamp and rule
            timestamp = int(self.triggered_at.timestamp())
            self.alert_id = f"{self.rule_id}_{timestamp}"

@dataclass
class KPISummary:
    """Overall KPI summary for dashboard"""
    total_accounts: int = 0
    total_campaigns: int = 0
    total_spend: float = 0.0
    total_impressions: int = 0
    total_clicks: int = 0
    total_conversions: float = 0.0
    average_ctr: float = 0.0
    average_cpc: float = 0.0
    average_conversion_rate: float = 0.0
    currency_code: str = "USD"
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    @property
    def total_roas(self) -> float:
        """Total return on ad spend"""
        # Would need conversion value data
        return 0.0

@dataclass
class ReportConfig:
    """Configuration for custom reports"""
    report_name: str
    customer_ids: List[str]
    metrics: List[str]
    dimensions: List[str] = field(default_factory=list)
    date_range: str = "LAST_30_DAYS"
    filters: Dict[str, Any] = field(default_factory=dict)
    from_resource: str = "campaign"
    
    def to_gaql_query(self) -> str:
        """Convert report config to GAQL query"""
        select_fields = []
        
        # Add dimensions
        for dimension in self.dimensions:
            select_fields.append(dimension)
        
        # Add metrics
        for metric in self.metrics:
            select_fields.append(metric)
        
        # Build FROM resource dynamically
        query = f"SELECT {', '.join(select_fields)} FROM {self.from_resource}"
        
        # ✅ CORRECCIÓN: Add date range sin agregar comillas extras
        if self.date_range:
            dr = self.date_range.strip()
            
            # Check if it's an explicit date range with AND
            if ' AND ' in dr:
                # ✅ CAMBIO CRÍTICO: Remover comillas si ya las tiene, o agregarlas si no
                parts = dr.split(' AND ')
                start = parts[0].strip().strip("'\"")  # Quitar comillas existentes
                end = parts[1].strip().strip("'\"")    # Quitar comillas existentes
                
                # Agregar comillas simples UNA SOLA VEZ
                query += f" WHERE segments.date BETWEEN '{start}' AND '{end}'"
            else:
                # Use DURING for named ranges (e.g., LAST_30_DAYS)
                query += f" WHERE segments.date DURING {dr}"
        
        # Add filters
        for field, value in self.filters.items():
            # Support numeric values without quotes
            if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
                clause = f"{field} = {value}"
            else:
                # ✅ MEJORA: Escape comillas simples en valores string
                value_escaped = str(value).replace("'", "\\'")
                clause = f"{field} = '{value_escaped}'"
            
            if 'WHERE' in query:
                query += f" AND {clause}"
            else:
                query += f" WHERE {clause}"
        
        return query

# Utility functions for data conversion
def convert_micros_to_currency(micros: int) -> float:
    """Convert micros to currency units"""
    return micros / 1_000_000

def convert_currency_to_micros(amount: float) -> int:
    """Convert currency units to micros"""
    return int(amount * 1_000_000)

def format_currency(amount: float, currency_code: str = "USD") -> str:
    """Format currency amount for display"""
    if currency_code == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency_code}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage for display"""
    return f"{value * 100:.{decimals}f}%"

def format_large_number(value: int) -> str:
    """Format large numbers with K, M, B suffixes"""
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return str(value)