"""
Data formatting utilities for Google Ads Dashboard
Provides consistent formatting for currency, percentages, dates, etc.
"""

import re
from typing import Union, Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import locale

class CurrencyFormatter:
    """Formatter for currency values"""
    
    def __init__(self, currency_code: str = "USD", locale_name: Optional[str] = None):
        """
        Initialize currency formatter
        
        Args:
            currency_code: ISO currency code (USD, EUR, etc.)
            locale_name: Locale for formatting (e.g., 'en_US', 'de_DE')
        """
        self.currency_code = currency_code
        self.locale_name = locale_name
        
        # Currency symbols mapping
        self.currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'CAD': 'C$',
            'AUD': 'A$',
            'CHF': 'CHF',
            'CNY': '¥',
            'SEK': 'kr',
            'NOK': 'kr',
            'DKK': 'kr',
            'PLN': 'zł',
            'CZK': 'Kč',
            'HUF': 'Ft',
            'RUB': '₽',
            'BRL': 'R$',
            'MXN': '$',
            'INR': '₹',
            'KRW': '₩',
            'SGD': 'S$',
            'HKD': 'HK$',
            'NZD': 'NZ$',
            'ZAR': 'R',
            'TRY': '₺',
            'ILS': '₪',
            'THB': '฿'
        }
        
        # Set locale if provided
        if locale_name:
            try:
                locale.setlocale(locale.LC_ALL, locale_name)
            except locale.Error:
                pass  # Use default locale
    
    def format(self, amount: Union[float, int, Decimal], 
               decimals: int = 2, 
               show_symbol: bool = True,
               show_code: bool = False,
               compact: bool = False) -> str:
        """
        Format currency amount
        
        Args:
            amount: Amount to format
            decimals: Number of decimal places
            show_symbol: Whether to show currency symbol
            show_code: Whether to show currency code
            compact: Whether to use compact notation (K, M, B)
            
        Returns:
            Formatted currency string
        """
        if amount is None:
            return "N/A"
        
        # Convert to Decimal for precise calculations
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # Round to specified decimals
        amount = amount.quantize(Decimal('0.' + '0' * decimals), rounding=ROUND_HALF_UP)
        
        # Handle compact notation
        if compact:
            return self._format_compact(float(amount), decimals, show_symbol, show_code)
        
        # Format with thousands separators
        formatted = f"{amount:,.{decimals}f}"
        
        # Add currency symbol/code
        if show_symbol and self.currency_code in self.currency_symbols:
            symbol = self.currency_symbols[self.currency_code]
            if self.currency_code in ['EUR']:
                formatted = f"{formatted} {symbol}"
            else:
                formatted = f"{symbol}{formatted}"
        
        if show_code:
            formatted = f"{formatted} {self.currency_code}"
        
        return formatted
    
    def _format_compact(self, amount: float, decimals: int, 
                       show_symbol: bool, show_code: bool) -> str:
        """Format amount with compact notation (K, M, B)"""
        abs_amount = abs(amount)
        sign = "-" if amount < 0 else ""
        
        if abs_amount >= 1_000_000_000:
            value = amount / 1_000_000_000
            suffix = "B"
        elif abs_amount >= 1_000_000:
            value = amount / 1_000_000
            suffix = "M"
        elif abs_amount >= 1_000:
            value = amount / 1_000
            suffix = "K"
        else:
            value = amount
            suffix = ""
        
        # Format value
        if suffix:
            formatted = f"{sign}{value:.1f}{suffix}"
        else:
            formatted = f"{sign}{value:.{decimals}f}"
        
        # Add currency symbol/code
        if show_symbol and self.currency_code in self.currency_symbols:
            symbol = self.currency_symbols[self.currency_code]
            if self.currency_code in ['EUR']:
                formatted = f"{formatted} {symbol}"
            else:
                formatted = f"{symbol}{formatted}"
        
        if show_code:
            formatted = f"{formatted} {self.currency_code}"
        
        return formatted
    
    def parse(self, currency_string: str) -> Optional[Decimal]:
        """
        Parse currency string back to decimal value
        
        Args:
            currency_string: Formatted currency string
            
        Returns:
            Decimal value or None if parsing fails
        """
        if not currency_string or currency_string == "N/A":
            return None
        
        # Remove currency symbols and codes
        cleaned = currency_string
        for symbol in self.currency_symbols.values():
            cleaned = cleaned.replace(symbol, "")
        
        # Remove currency codes
        for code in self.currency_symbols.keys():
            cleaned = cleaned.replace(code, "")
        
        # Remove whitespace and commas
        cleaned = re.sub(r'[,\s]', '', cleaned)
        
        # Handle compact notation
        multiplier = 1
        if cleaned.endswith('K'):
            multiplier = 1_000
            cleaned = cleaned[:-1]
        elif cleaned.endswith('M'):
            multiplier = 1_000_000
            cleaned = cleaned[:-1]
        elif cleaned.endswith('B'):
            multiplier = 1_000_000_000
            cleaned = cleaned[:-1]
        
        try:
            value = Decimal(cleaned) * multiplier
            return value
        except (ValueError, TypeError):
            return None

class PercentageFormatter:
    """Formatter for percentage values"""
    
    @staticmethod
    def format(value: Union[float, int, Decimal], 
               decimals: int = 2,
               multiply_by_100: bool = True) -> str:
        """
        Format percentage value
        
        Args:
            value: Value to format (0.0-1.0 or 0-100 depending on multiply_by_100)
            decimals: Number of decimal places
            multiply_by_100: Whether to multiply by 100 (for 0.0-1.0 values)
            
        Returns:
            Formatted percentage string
        """
        if value is None:
            return "N/A"
        
        if multiply_by_100:
            value = float(value) * 100
        
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def parse(percentage_string: str, return_decimal: bool = True) -> Optional[float]:
        """
        Parse percentage string back to numeric value
        
        Args:
            percentage_string: Formatted percentage string
            return_decimal: Whether to return as decimal (0.0-1.0) or percentage (0-100)
            
        Returns:
            Numeric value or None if parsing fails
        """
        if not percentage_string or percentage_string == "N/A":
            return None
        
        # Remove % symbol and whitespace
        cleaned = percentage_string.replace('%', '').strip()
        
        try:
            value = float(cleaned)
            if return_decimal:
                value = value / 100
            return value
        except (ValueError, TypeError):
            return None

class NumberFormatter:
    """Formatter for large numbers"""
    
    @staticmethod
    def format(value: Union[int, float], 
               compact: bool = True,
               decimals: int = 1) -> str:
        """
        Format large numbers with K, M, B suffixes
        
        Args:
            value: Number to format
            compact: Whether to use compact notation
            decimals: Number of decimal places for compact notation
            
        Returns:
            Formatted number string
        """
        if value is None:
            return "N/A"
        
        if not compact:
            return f"{value:,}"
        
        abs_value = abs(value)
        sign = "-" if value < 0 else ""
        
        if abs_value >= 1_000_000_000:
            formatted = f"{sign}{value / 1_000_000_000:.{decimals}f}B"
        elif abs_value >= 1_000_000:
            formatted = f"{sign}{value / 1_000_000:.{decimals}f}M"
        elif abs_value >= 1_000:
            formatted = f"{sign}{value / 1_000:.{decimals}f}K"
        else:
            formatted = f"{sign}{value:,.0f}"
        
        return formatted

class DateFormatter:
    """Formatter for dates and times"""
    
    @staticmethod
    def format_date(date_obj: Union[date, datetime, str], 
                   format_string: str = "%Y-%m-%d") -> str:
        """
        Format date object
        
        Args:
            date_obj: Date to format
            format_string: Format string
            
        Returns:
            Formatted date string
        """
        if date_obj is None:
            return "N/A"
        
        if isinstance(date_obj, str):
            # Try to parse string date
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except ValueError:
                return date_obj  # Return as-is if parsing fails
        
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        
        return date_obj.strftime(format_string)
    
    @staticmethod
    def format_datetime(datetime_obj: Union[datetime, str], 
                       format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format datetime object
        
        Args:
            datetime_obj: Datetime to format
            format_string: Format string
            
        Returns:
            Formatted datetime string
        """
        if datetime_obj is None:
            return "N/A"
        
        if isinstance(datetime_obj, str):
            # Try to parse string datetime
            try:
                datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
            except ValueError:
                return datetime_obj  # Return as-is if parsing fails
        
        return datetime_obj.strftime(format_string)
    
    @staticmethod
    def format_relative_time(datetime_obj: datetime) -> str:
        """
        Format datetime as relative time (e.g., "2 hours ago")
        
        Args:
            datetime_obj: Datetime to format
            
        Returns:
            Relative time string
        """
        if datetime_obj is None:
            return "N/A"
        
        now = datetime.now()
        if datetime_obj.tzinfo:
            now = now.replace(tzinfo=datetime_obj.tzinfo)
        
        diff = now - datetime_obj
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"

class MetricFormatter:
    """Formatter for Google Ads metrics"""
    
    def __init__(self, currency_code: str = "USD"):
        """
        Initialize metric formatter
        
        Args:
            currency_code: Currency code for cost metrics
        """
        self.currency_formatter = CurrencyFormatter(currency_code)
        self.percentage_formatter = PercentageFormatter()
        self.number_formatter = NumberFormatter()
    
    def format_metric(self, metric_name: str, value: Any, **kwargs) -> str:
        """
        Format metric based on its type
        
        Args:
            metric_name: Name of the metric
            value: Value to format
            **kwargs: Additional formatting options
            
        Returns:
            Formatted metric string
        """
        if value is None:
            return "N/A"
        
        # Cost metrics (in micros)
        if 'cost' in metric_name.lower() or 'spend' in metric_name.lower():
            if 'micros' in metric_name.lower():
                # Convert from micros to currency units
                value = value / 1_000_000
            return self.currency_formatter.format(value, **kwargs)
        
        # Percentage metrics
        elif any(term in metric_name.lower() for term in ['rate', 'ctr', 'percentage', 'ratio']):
            return self.percentage_formatter.format(value, **kwargs)
        
        # Count metrics
        elif any(term in metric_name.lower() for term in ['impressions', 'clicks', 'conversions']):
            return self.number_formatter.format(value, **kwargs)
        
        # Default formatting
        else:
            if isinstance(value, (int, float)):
                return self.number_formatter.format(value, **kwargs)
            else:
                return str(value)

# Global formatters
default_currency_formatter = CurrencyFormatter()
default_percentage_formatter = PercentageFormatter()
default_number_formatter = NumberFormatter()
default_date_formatter = DateFormatter()
default_metric_formatter = MetricFormatter()

# Convenience functions
def format_currency(amount: Union[float, int, Decimal], 
                   currency_code: str = "USD", **kwargs) -> str:
    """Format currency amount"""
    formatter = CurrencyFormatter(currency_code)
    return formatter.format(amount, **kwargs)

def format_percentage(value: Union[float, int, Decimal], **kwargs) -> str:
    """Format percentage value"""
    return default_percentage_formatter.format(value, **kwargs)

def format_number(value: Union[int, float], **kwargs) -> str:
    """Format large number"""
    return default_number_formatter.format(value, **kwargs)

def format_date(date_obj: Union[date, datetime, str], **kwargs) -> str:
    """Format date"""
    return default_date_formatter.format_date(date_obj, **kwargs)

def format_datetime(datetime_obj: Union[datetime, str], **kwargs) -> str:
    """Format datetime"""
    return default_date_formatter.format_datetime(datetime_obj, **kwargs)

def format_metric(metric_name: str, value: Any, currency_code: str = "USD", **kwargs) -> str:
    """Format metric based on its type"""
    formatter = MetricFormatter(currency_code)
    return formatter.format_metric(metric_name, value, **kwargs)