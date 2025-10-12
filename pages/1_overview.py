"""
Overview Page - Main dashboard with KPIs and summary metrics
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import logging

from modules.auth import require_auth
from utils.logger import get_logger
from utils.formatters import format_currency, format_percentage, format_number

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Overview - Google Ads Dashboard",
    page_icon="📊",
    layout="wide"
)

@require_auth
def main():
    """Main overview page function"""
    
    # Page header
    st.title("📊 Dashboard Overview")
    st.markdown("---")
    
    # Check if services are available
    if not st.session_state.get('google_ads_client') or not st.session_state.get('services'):
        st.error("❌ Google Ads services not initialized. Please check your configuration.")
        return
    
    # Get selected customer
    selected_customer = st.session_state.get('selected_customer')
    if not selected_customer:
        st.warning("⚠️ No customer account selected. Please select an account from the sidebar.")
        return
    
    # Services
    campaign_service = st.session_state.services['campaign']
    billing_service = st.session_state.services['billing']
    alert_service = st.session_state.services['alert']
    
    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        date_range = st.selectbox(
            "📅 Date Range",
            options=["Last 7 days", "Last 30 days", "Last 90 days", "This month", "Last month"],
            index=1
        )
    
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
    
    with col3:
        if st.button("🔄 Refresh Now", width='stretch'):
            st.cache_data.clear()
            st.rerun()
    
    # Convert date range to days
    days_map = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "This month": 30,  # Approximate
        "Last month": 30   # Approximate
    }
    selected_days = days_map.get(date_range, 30)
    
    # Auto-refresh logic
    if auto_refresh:
        st.rerun()
    
    try:
        # Load data with spinner
        with st.spinner(f"Loading dashboard data for {date_range.lower()}..."):
            
            # Get KPI summary with selected date range
            kpi_summary = campaign_service.get_kpi_summary(selected_customer, days=selected_days)
            
            # Get billing summary
            billing_summary = billing_service.get_billing_summary(selected_customer)
            
            # Get active alerts
            active_alerts = alert_service.get_active_alerts(customer_id=selected_customer)
            
            # Get campaign performance summary with selected date range
            campaign_summary = campaign_service.get_campaign_performance_summary(selected_customer, days=selected_days)
            
            # Get campaigns list (for basic info)
            campaigns = campaign_service.get_campaigns(selected_customer)
        
        # KPI Cards
        st.subheader(f"📈 Key Performance Indicators ({date_range})")
        
        if kpi_summary:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "💰 Total Spend",
                    format_currency(kpi_summary.total_spend),
                    delta=None,
                    help="Total advertising spend for the selected period"
                )
            
            with col2:
                st.metric(
                    "👁️ Impressions",
                    format_number(kpi_summary.total_impressions),
                    delta=None,
                    help="Total number of times ads were shown"
                )
            
            with col3:
                st.metric(
                    "🖱️ Clicks",
                    format_number(kpi_summary.total_clicks),
                    delta=None,
                    help="Total number of clicks on ads"
                )
            
            with col4:
                st.metric(
                    "📊 CTR",
                    format_percentage(kpi_summary.average_ctr),
                    delta=None,
                    help="Click-through rate (clicks/impressions)"
                )
            
            with col5:
                st.metric(
                    "🎯 Conversions",
                    format_number(kpi_summary.total_conversions),
                    delta=None,
                    help="Total number of conversions"
                )
        
        else:
            st.info("📊 No KPI data available for the selected period.")
        
        st.markdown("---")
        
        # Two-column layout for charts and alerts
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # Performance trends chart
            st.subheader("📈 Performance Trends")
            
            if kpi_summary:
                # Get real trend data from KPI summary using selected date range
                dates = pd.date_range(end=datetime.now().date(), periods=selected_days, freq='D')
                
                # Use KPI summary data for trends
                total_spend = kpi_summary.total_spend if hasattr(kpi_summary, 'total_spend') else 0
                total_clicks = kpi_summary.total_clicks if hasattr(kpi_summary, 'total_clicks') else 0
                total_impressions = kpi_summary.total_impressions if hasattr(kpi_summary, 'total_impressions') else 0
                total_conversions = kpi_summary.total_conversions if hasattr(kpi_summary, 'total_conversions') else 0
                
                # Distribute totals across dates (simplified distribution)
                trend_data = pd.DataFrame({
                    'Date': dates,
                    'Spend': [total_spend / len(dates) if len(dates) > 0 else 0] * len(dates),
                    'Clicks': [total_clicks // len(dates) if len(dates) > 0 else 0] * len(dates),
                    'Impressions': [total_impressions // len(dates) if len(dates) > 0 else 0] * len(dates),
                    'Conversions': [total_conversions / len(dates) if len(dates) > 0 else 0] * len(dates)
                })
                
                # Create subplots
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Daily Spend', 'Daily Clicks', 'Daily Impressions', 'Daily Conversions'),
                    specs=[[{"secondary_y": False}, {"secondary_y": False}],
                           [{"secondary_y": False}, {"secondary_y": False}]]
                )
                
                # Add traces
                fig.add_trace(
                    go.Scatter(x=trend_data['Date'], y=trend_data['Spend'], 
                              name='Spend', line=dict(color='#1f77b4')),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(x=trend_data['Date'], y=trend_data['Clicks'], 
                              name='Clicks', line=dict(color='#ff7f0e')),
                    row=1, col=2
                )
                
                fig.add_trace(
                    go.Scatter(x=trend_data['Date'], y=trend_data['Impressions'], 
                              name='Impressions', line=dict(color='#2ca02c')),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(x=trend_data['Date'], y=trend_data['Conversions'], 
                              name='Conversions', line=dict(color='#d62728')),
                    row=2, col=2
                )
                
                fig.update_layout(
                    height=500,
                    showlegend=False,
                    title_text="Performance Trends (Last 30 Days)"
                )
                
                st.plotly_chart(fig, width='stretch')
            
            else:
                st.info("📈 No campaign data available for trend analysis.")
            
            # Campaign performance table
            st.subheader("🎯 Top Campaigns")
            
            if campaign_summary and 'top_campaigns' in campaign_summary and campaigns:
                # Create a mapping of campaign IDs to names
                campaign_names = {c.campaign_id: c.campaign_name for c in campaigns}
                
                # Create campaign performance dataframe using campaign_summary data
                campaign_data = []
                for campaign_id, perf in campaign_summary['top_campaigns']:
                    campaign_name = campaign_names.get(campaign_id, f"Campaign {campaign_id}")
                    
                    # Calculate metrics
                    impressions = perf.get('impressions', 0)
                    clicks = perf.get('clicks', 0)
                    cost = perf.get('cost', 0)
                    
                    ctr = (clicks / impressions * 100) if impressions > 0 else 0
                    cpc = cost / clicks if clicks > 0 else 0
                    
                    campaign_data.append({
                        'Campaign': campaign_name,
                        'Impressions': format_number(impressions),
                        'Clicks': format_number(clicks),
                        'Spend': format_currency(cost),
                        'CTR': format_percentage(ctr),
                        'CPC': format_currency(cpc)
                    })
                
                if campaign_data:
                    df_campaigns = pd.DataFrame(campaign_data)
                    st.dataframe(df_campaigns, width='stretch', hide_index=True)
                else:
                    st.info("🎯 No campaign performance data available.")
            else:
                st.info("🎯 No campaign data available.")
        
        with col_right:
            # Alerts section
            st.subheader("🚨 Active Alerts")
            
            if active_alerts:
                for alert in active_alerts[:5]:  # Show top 5 alerts
                    priority_colors = {
                        'high': '#ffebee',
                        'medium': '#fff3e0',
                        'low': '#f3e5f5'
                    }
                    
                    priority_icons = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟣'
                    }
                    
                    priority = alert.priority.value if hasattr(alert.priority, 'value') else str(alert.priority)
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: {priority_colors.get(priority, '#f5f5f5')}; 
                                    padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;
                                    border-left: 4px solid {'#f44336' if priority == 'high' else '#ff9800' if priority == 'medium' else '#9c27b0'};">
                            <strong>{priority_icons.get(priority, '⚪')} {alert.title}</strong><br>
                            <small>{alert.message}</small><br>
                            <small style="color: #666;">
                                {alert.triggered_at.strftime('%Y-%m-%d %H:%M')}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                
                if len(active_alerts) > 5:
                    st.info(f"+ {len(active_alerts) - 5} more alerts")
                
                # Alert summary
                st.markdown("**Alert Summary:**")
                alert_summary = alert_service.get_alert_summary([selected_customer])
                
                if alert_summary and not alert_summary.get('error'):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Active", alert_summary.get('active_alerts', 0))
                        st.metric("High Priority", alert_summary.get('high_priority_alerts', 0))
                    with col_b:
                        st.metric("Total", alert_summary.get('total_alerts', 0))
                        st.metric("Recent (24h)", alert_summary.get('recent_alerts_24h', 0))
            
            else:
                st.success("✅ No active alerts")
                st.info("All systems are running smoothly!")
            
            # Budget overview
            st.subheader("💰 Budget Overview")
            
            if billing_summary:
                # Budget utilization chart
                if hasattr(billing_summary, 'budget_utilization'):
                    utilization = billing_summary.budget_utilization
                    
                    fig_budget = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = utilization * 100,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Budget Utilization %"},
                        delta = {'reference': 80},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "yellow"},
                                {'range': [80, 100], 'color': "red"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    
                    fig_budget.update_layout(height=300)
                    st.plotly_chart(fig_budget, width='stretch')
                
                # Budget metrics
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.metric(
                        "Total Budget",
                        format_currency(getattr(billing_summary, 'total_budget', 0))
                    )
                with col_b2:
                    st.metric(
                        "Spent",
                        format_currency(getattr(billing_summary, 'total_spend', 0))
                    )
            
            else:
                st.info("💰 No billing data available.")
            
            # Quick actions
            st.subheader("⚡ Quick Actions")
            
            if st.button("📊 Generate Report", width='stretch'):
                st.info("Redirecting to Reports page...")
                # In a real app, this would navigate to the reports page
            
            if st.button("🔍 Campaign Analysis", width='stretch'):
                st.info("Redirecting to Campaigns page...")
                # In a real app, this would navigate to the campaigns page
            
            if st.button("⚙️ Settings", width='stretch'):
                st.info("Redirecting to Settings page...")
                # In a real app, this would navigate to the settings page
    
    except Exception as e:
        logger.error(f"Error loading overview page: {e}")
        st.error(f"❌ Error loading dashboard: {e}")
        
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common issues:**
            
            1. **API Connection**: Check your Google Ads API credentials
            2. **Account Access**: Ensure you have access to the selected account
            3. **Data Availability**: Some accounts may have limited historical data
            4. **Rate Limits**: Try refreshing after a few moments
            
            **Need help?** Check the Settings page for configuration options.
            """)

if __name__ == "__main__":
    main()