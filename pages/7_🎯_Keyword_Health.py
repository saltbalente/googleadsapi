"""
Keyword Health Page - Dashboard Ultra Moderno 2030
Sistema inteligente de optimización con health scores y glassmorphism dark theme
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import uuid
from typing import List, Dict, Optional

from modules.auth import require_auth
from utils.logger import get_logger
from utils.formatters import format_currency, format_percentage, format_number
from services.database_service import DatabaseService
from services.keyword_health_service import KeywordHealthService
from services.action_execution_service import ActionExecutionService, BidChangeRequest
from services.scheduler_service import SchedulerService
from services.campaign_service import CampaignService
from modules.models import CampaignStatus, ReportConfig

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Keyword Health - Google Ads Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS - ULTRA MODERN 2030 ====================
def inject_ultra_modern_css():
    """Inyecta CSS ultra moderno con glassmorphism y animaciones"""
    st.markdown("""
    <style>
    /* ==================== IMPORTS & VARIABLES ==================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    :root {
        --primary: #667eea;
        --primary-dark: #764ba2;
        --success: #38ef7d;
        --warning: #f5576c;
        --info: #4facfe;
        --bg-dark: #0a0a1a;
        --bg-darker: #050510;
        --glass-bg: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.08);
        --text-primary: #ffffff;
        --text-secondary: rgba(255, 255, 255, 0.7);
        --text-muted: rgba(255, 255, 255, 0.4);
    }
    
    /* ==================== GLOBAL ==================== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-darker) 0%, var(--bg-dark) 50%, #1a1a2e 100%);
        background-attachment: fixed;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            linear-gradient(rgba(102, 126, 234, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(102, 126, 234, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }
    
    /* ==================== SIDEBAR ==================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 10, 26, 0.95) 0%, rgba(5, 5, 16, 0.98) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid var(--glass-border);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* ==================== HEADERS ==================== */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
        letter-spacing: -2px;
        font-size: 3.5rem !important;
        margin-bottom: 0.5rem !important;
        text-align: center;
        animation: fadeInDown 0.8s ease-out;
    }
    
    h2 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -1px;
        font-size: 1.8rem !important;
        margin-top: 2rem !important;
    }
    
    h3, h4 {
        color: var(--text-secondary);
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* ==================== METRICS ==================== */
    [data-testid="metric-container"] {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 2rem 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
        opacity: 0;
        transition: opacity 0.4s;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-8px);
        border-color: rgba(102, 126, 234, 0.4);
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.2);
    }
    
    [data-testid="metric-container"]:hover::before {
        opacity: 1;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* ==================== BUTTONS ==================== */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.85rem 2.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 36px rgba(102, 126, 234, 0.5);
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    /* ==================== INPUTS ==================== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.85rem 1.2rem !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
        background: rgba(102, 126, 234, 0.05) !important;
    }
    
    /* ==================== SLIDERS ==================== */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
    }
    
    .stSlider > div > div > div {
        background: var(--glass-bg) !important;
    }
    
    /* ==================== DATAFRAMES ==================== */
    [data-testid="stDataFrame"] {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }
    
    [data-testid="stDataFrame"] table {
        color: var(--text-primary);
    }
    
    [data-testid="stDataFrame"] thead tr {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
    }
    
    [data-testid="stDataFrame"] tbody tr:hover {
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* ==================== TABS ==================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: transparent;
        border-bottom: none;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        color: var(--text-secondary);
        font-weight: 600;
        padding: 1rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.15);
        border-color: rgba(102, 126, 234, 0.4);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        border-color: transparent;
        color: white;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
    
    /* ==================== EXPANDERS ==================== */
    .streamlit-expanderHeader {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        color: var(--text-primary);
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--primary);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
    }
    
    /* ==================== ALERTS ==================== */
    .stAlert {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    
    /* ==================== CHECKBOX ==================== */
    .stCheckbox {
        background: var(--glass-bg);
        padding: 0.75rem 1rem;
        border-radius: 10px;
        border: 1px solid var(--glass-border);
        transition: all 0.3s ease;
    }
    
    .stCheckbox:hover {
        border-color: var(--primary);
        background: rgba(102, 126, 234, 0.05);
    }
    
    /* ==================== MULTISELECT ==================== */
    .stMultiSelect > div > div {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
    }
    
    /* ==================== SCROLLBAR ==================== */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-darker);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        border-radius: 10px;
        border: 2px solid var(--bg-darker);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
    }
    
    /* ==================== ANIMATIONS ==================== */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    [data-testid="metric-container"],
    [data-testid="stDataFrame"],
    .stTabs {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* ==================== HIDE STREAMLIT BRANDING ==================== */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* ==================== RESPONSIVE ==================== */
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem !important;
        }
        
        [data-testid="metric-container"] {
            padding: 1.5rem 1rem;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_hero_section():
    """Renderiza el hero header ultra moderno"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 3rem 0; position: relative;">
        <div style="font-size: 5rem; margin-bottom: 1rem; 
                    animation: fadeInDown 0.8s ease-out;
                    filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.5));">
            🎯
        </div>
        <p style="font-size: 1rem; color: rgba(255, 255, 255, 0.6); 
                  font-weight: 500; letter-spacing: 3px; text-transform: uppercase;
                  margin-bottom: 0.5rem;">
            Keyword Intelligence System
        </p>
        <p style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.8); 
                  font-weight: 400; max-width: 700px; margin: 0 auto;">
            Sistema inteligente de optimización con health scores y acciones automatizadas
        </p>
        <div style="width: 100px; height: 3px; 
                    background: linear-gradient(90deg, transparent, #667eea, transparent);
                    margin: 2rem auto 0 auto;"></div>
    </div>
    """, unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services"""
    return {
        'db': DatabaseService(),
        'health': KeywordHealthService(),
        'action': ActionExecutionService(),
        'scheduler': SchedulerService(st.session_state.google_ads_client),
        'campaign': CampaignService(st.session_state.google_ads_client)
    }

def get_health_color(score: float) -> str:
    """Get color based on health score"""
    if score >= 70:
        return "🟢"
    elif score >= 40:
        return "🟡"
    else:
        return "🔴"

def get_health_status(score: float) -> str:
    """Get status text based on health score"""
    if score >= 70:
        return "Healthy"
    elif score >= 40:
        return "Needs Attention"
    else:
        return "Critical"

@require_auth
def main():
    """Main keyword health page function"""
    
    # Inject modern CSS
    inject_ultra_modern_css()
    
    # Hero header
    render_hero_section()
    
    # Check if services are available
    if not st.session_state.get('google_ads_client') or not st.session_state.get('services'):
        st.error("❌ Google Ads services not initialized. Please check your configuration.")
        return
    
    # Get selected customer
    selected_customer = st.session_state.get('selected_customer')
    if not selected_customer:
        st.warning("⚠️ No customer account selected. Please select an account from the sidebar.")
        return
    
    # Initialize services
    services = get_services()
    db_service = services['db']
    health_service = services['health']
    action_service = services['action']
    scheduler_service = services['scheduler']
    campaign_service = services['campaign']
    report_service = st.session_state.services['report']

    # Ensure scheduler is running
    try:
        status = scheduler_service.get_job_status()
        if not status.get('scheduler_running'):
            scheduler_service.start()
            logger.info("Scheduler started from Keyword Health page")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎛️ CONTROL PANEL")
        st.markdown("---")
        
        # Date range selector
        date_range = st.selectbox(
            "📅 Analysis Period",
            options=["Last 7 days", "Last 30 days", "Last 90 days"],
            index=1
        )
        
        days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
        selected_days = days_map.get(date_range, 30)
        
        st.markdown("---")
        
        # Health score filter
        min_health_score = st.slider(
            "🎯 Min Health Score",
            min_value=0,
            max_value=100,
            value=0,
            help="Filter keywords by minimum health score"
        )
        
        # Include criticals toggle
        include_criticals_kpis = st.checkbox(
            "🧨 Incluir críticos en KPIs (Score = 0)",
            value=True,
            help="Incluye palabras clave con Health Score = 0 en los KPIs y gráficos"
        )
        
        st.markdown("---")
        
        # Action type filter
        action_filter = st.multiselect(
            "⚡ Action Types",
            options=["Quick Wins", "Vampire Keywords", "Saturation Alerts", "Bid Recommendations"],
            default=["Quick Wins", "Vampire Keywords"]
        )
        
        st.markdown("---")
        
        # Auto-refresh
        auto_refresh = st.checkbox("🔄 Auto-refresh (60s)", value=False)
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Auto-refresh logic
    if auto_refresh:
        st.rerun()
    
    try:
        # Load data with spinner
        with st.spinner("⏳ Loading keyword health data..."):
            
            # Get health scores
            raw_health_scores = db_service.get_health_scores(selected_customer, days_back=selected_days)
            
            if not raw_health_scores:
                latest_scores = db_service.get_latest_health_scores(selected_customer, limit=1000)
                
                def _hs_to_dict(s):
                    return {
                        'customer_id': s.customer_id,
                        'campaign_id': s.campaign_id,
                        'ad_group_id': s.ad_group_id,
                        'keyword_text': s.keyword_text,
                        'health_score': float(getattr(s, 'health_score', 0) or 0),
                        'conv_rate_score': float(getattr(s, 'conv_rate_score', 0) or 0),
                        'cpa_score': float(getattr(s, 'cpa_score', 0) or 0),
                        'ctr_score': float(getattr(s, 'ctr_score', 0) or 0),
                        'confidence_score': float(getattr(s, 'confidence_score', 0) or 0),
                        'quality_score_points': float(getattr(s, 'quality_score_points', 0) or 0),
                        'health_category': getattr(s, 'health_category', 'warning') or 'warning',
                        'recommended_action': getattr(s, 'recommended_action', 'monitor') or 'monitor',
                        'action_priority': int(getattr(s, 'action_priority', 5) or 5),
                        'data_period_start': s.data_period_start.isoformat() if getattr(s, 'data_period_start', None) else None,
                        'data_period_end': s.data_period_end.isoformat() if getattr(s, 'data_period_end', None) else None,
                        'total_spend': float(getattr(s, 'total_spend', 0) or 0),
                        'total_conversions': float(getattr(s, 'total_conversions', 0) or 0),
                        'total_clicks': int(getattr(s, 'total_clicks', 0) or 0),
                        'calculated_at': s.calculated_at.isoformat() if getattr(s, 'calculated_at', None) else None
                    }
                health_scores = [_hs_to_dict(s) for s in latest_scores] if latest_scores else []
            else:
                health_scores = raw_health_scores
            
            # Get keyword metrics
            keyword_metrics = db_service.get_keyword_metrics(selected_customer, days_back=selected_days)
            
            # Get optimization actions
            recent_actions = db_service.get_recent_actions(selected_customer, days_back=7)
            
            # Calculate health scores in real-time
            rt_df_kw = None
            grouped_kw_rt = None
            health_scores_rt = []
            try:
                rt_end_date = datetime.now().date()
                rt_start_date = rt_end_date - timedelta(days=selected_days)
                rt_start_date_str = rt_start_date.strftime("%Y-%m-%d")
                rt_end_date_str = rt_end_date.strftime("%Y-%m-%d")
                rt_config = ReportConfig(
                    report_name='Keyword Performance RT',
                    customer_ids=[selected_customer],
                    metrics=[
                        'metrics.impressions', 'metrics.clicks', 'metrics.cost_micros',
                        'metrics.conversions', 'metrics.conversions_value',
                        'metrics.ctr', 'metrics.average_cpc'
                    ],
                    dimensions=[
                        'campaign.id', 'campaign.name',
                        'ad_group.id', 'ad_group.name',
                        'ad_group_criterion.keyword.text',
                        'ad_group_criterion.quality_info.quality_score',
                        'segments.date'
                    ],
                    date_range=f"'{rt_start_date_str}' AND '{rt_end_date_str}'",
                    from_resource='keyword_view',
                    filters={
                        'campaign.status': 'ENABLED',
                        'ad_group_criterion.status': 'ENABLED'
                    }
                )
                rt_report = report_service.generate_custom_report(rt_config)
                if rt_report.get('success') and rt_report.get('data'):
                    rt_df_kw = pd.DataFrame(rt_report['data'])
                    for c in [
                        'metrics.impressions','metrics.clicks','metrics.cost_micros',
                        'metrics.conversions','metrics.conversions_value','metrics.ctr','metrics.average_cpc',
                        'ad_group_criterion.quality_info.quality_score'
                    ]:
                        if c in rt_df_kw.columns:
                            rt_df_kw[c] = pd.to_numeric(rt_df_kw[c], errors='coerce').fillna(0.0)
                    rt_df_kw['Spend'] = rt_df_kw['metrics.cost_micros'] / 1_000_000
                    req_cols = ['ad_group_criterion.keyword.text','campaign.id','campaign.name','ad_group.id','ad_group.name']
                    if all(col in rt_df_kw.columns for col in req_cols):
                        grouped_kw_rt = rt_df_kw.groupby(req_cols, as_index=False).agg({
                            'metrics.impressions':'sum',
                            'metrics.clicks':'sum',
                            'metrics.conversions':'sum',
                            'metrics.conversions_value':'sum',
                            'Spend':'sum',
                            'ad_group_criterion.quality_info.quality_score':'mean'
                        })
                        grouped_kw_rt['CTR'] = (grouped_kw_rt['metrics.clicks'] / grouped_kw_rt['metrics.impressions'].replace(0, np.nan) * 100).fillna(0.0).round(2)
                        grouped_kw_rt['Avg CPC'] = (grouped_kw_rt['Spend'] / grouped_kw_rt['metrics.clicks'].replace(0, np.nan)).fillna(0.0).round(2)
                        grouped_kw_rt['Conv Rate'] = (grouped_kw_rt['metrics.conversions'] / grouped_kw_rt['metrics.clicks'].replace(0, np.nan) * 100).fillna(0.0).round(2)
                        grouped_kw_rt['CPA'] = (grouped_kw_rt['Spend'] / grouped_kw_rt['metrics.conversions'].replace(0, np.nan)).fillna(0.0).round(2)
                        grouped_kw_rt['Spend'] = grouped_kw_rt['Spend'].round(2)
                        rt_bench = db_service.get_account_benchmarks(selected_customer)
                        target_conv_rate = rt_bench.target_conv_rate
                        target_cpa = rt_bench.target_cpa
                        benchmark_ctr = rt_bench.benchmark_ctr
                        grouped_kw_rt['conv_rate_decimal'] = grouped_kw_rt['Conv Rate'] / 100
                        grouped_kw_rt['conv_rate_score'] = np.minimum(
                            (grouped_kw_rt['conv_rate_decimal'] / target_conv_rate) * 30, 30
                        ).fillna(0)
                        grouped_kw_rt['cpa_score'] = np.where(
                            grouped_kw_rt['CPA'] == 0,
                            0,
                            np.minimum((target_cpa / grouped_kw_rt['CPA']) * 30, 30)
                        ).astype(float)
                        grouped_kw_rt['ctr_decimal'] = grouped_kw_rt['CTR'] / 100
                        grouped_kw_rt['ctr_score'] = np.minimum(
                            (grouped_kw_rt['ctr_decimal'] / benchmark_ctr) * 20, 20
                        ).fillna(0)
                        grouped_kw_rt['confidence_score'] = np.minimum(
                            grouped_kw_rt['metrics.clicks'] / 100 * 10, 10
                        ).fillna(0)
                        grouped_kw_rt['quality_score_points'] = (
                            grouped_kw_rt['ad_group_criterion.quality_info.quality_score'].fillna(5) * 1
                        ).clip(0, 10)
                        grouped_kw_rt['Health Score'] = (
                            grouped_kw_rt['conv_rate_score'] + grouped_kw_rt['cpa_score'] + grouped_kw_rt['ctr_score'] + grouped_kw_rt['confidence_score'] + grouped_kw_rt['quality_score_points']
                        ).round(2)
                        grouped_kw_rt['data_confidence'] = np.minimum(
                            grouped_kw_rt['metrics.clicks'] / 50, 1.0
                        )
                        grouped_kw_rt['Health Score'] = (
                            grouped_kw_rt['Health Score'] * grouped_kw_rt['data_confidence']
                        ).round(2)
                        grouped_kw_rt['Status'] = grouped_kw_rt['Health Score'].apply(get_health_status)
                        health_scores_rt = [{'health_score': float(x)} for x in grouped_kw_rt['Health Score'].tolist()]
            except Exception as e:
                logger.error(f"Error calculando health scores en tiempo real: {e}")
        
            health_scores_slider_filtered = [h for h in (health_scores_rt or []) if h.get('health_score', 0) >= min_health_score]
            
            if include_criticals_kpis:
                health_scores_for_kpis = [
                    h for h in (health_scores_rt or [])
                    if h.get('health_score', 0) >= min_health_score or h.get('health_score', 0) == 0
                ]
            else:
                health_scores_for_kpis = health_scores_slider_filtered
        
        st.caption(
            f"Health scores: {len(health_scores)} total, KPIs: {len(health_scores_for_kpis)}, filtrados: {len(health_scores_slider_filtered)}"
        )
        
        # Main dashboard metrics
        st.markdown(f"## 📊 Health Overview")
        st.markdown(f"<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Período: {date_range}</p>", unsafe_allow_html=True)
        
        if health_scores_for_kpis:
            total_keywords = len(health_scores_for_kpis)
            avg_health_score = sum(h.get('health_score', 0) for h in health_scores_for_kpis) / total_keywords
            
            healthy_count = len([h for h in health_scores_for_kpis if h.get('health_score', 0) >= 70])
            attention_count = len([h for h in health_scores_for_kpis if 40 <= h.get('health_score', 0) < 70])
            critical_count = len([h for h in health_scores_for_kpis if h.get('health_score', 0) < 40])
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("🎯 Total Keywords", format_number(total_keywords))
            
            with col2:
                st.metric("📈 Avg Health", f"{avg_health_score:.1f}")
            
            with col3:
                st.metric("🟢 Healthy", format_number(healthy_count), 
                         delta=f"{(healthy_count/total_keywords)*100:.1f}%")
            
            with col4:
                st.metric("🟡 Attention", format_number(attention_count),
                         delta=f"{(attention_count/total_keywords)*100:.1f}%")
            
            with col5:
                st.metric("🔴 Critical", format_number(critical_count),
                         delta=f"{(critical_count/total_keywords)*100:.1f}%")
        
        else:
            st.info("📊 No hay datos de health score con los filtros actuales.")
        
        st.markdown("---")
        
        # Two-column layout
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("### 📊 Health Score Distribution")
            
            if health_scores_for_kpis:
                df_health = pd.DataFrame(health_scores_for_kpis)
                
                fig_hist = px.histogram(
                    df_health, x='health_score', nbins=20,
                    labels={'health_score': 'Health Score', 'count': 'Keywords'},
                    color_discrete_sequence=['#667eea']
                )
                fig_hist.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='rgba(255,255,255,0.8)'),
                    showlegend=False,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                fig_hist.add_vline(x=40, line_dash="dash", line_color="#f5576c", annotation_text="Critical")
                fig_hist.add_vline(x=70, line_dash="dash", line_color="#38ef7d", annotation_text="Healthy")
                zero_count = len([h for h in health_scores_for_kpis if h.get('health_score', 0) == 0])
                fig_hist.add_annotation(x=2, y=0, yshift=30, showarrow=False, text=f"Score = 0: {zero_count}")
                st.plotly_chart(fig_hist, use_container_width=True)
                
                st.markdown("### 📈 Health Score Trends")
                if rt_df_kw is not None and 'segments.date' in rt_df_kw.columns:
                    daily = rt_df_kw.groupby('segments.date', as_index=False).agg({
                        'metrics.impressions':'sum',
                        'metrics.clicks':'sum',
                        'metrics.conversions':'sum',
                        'metrics.cost_micros':'sum'
                    })
                    daily['Spend'] = daily['metrics.cost_micros'] / 1_000_000
                    daily['CTR'] = (daily['metrics.clicks'] / daily['metrics.impressions'].replace(0, np.nan)).fillna(0.0)
                    daily['Conv Rate'] = (daily['metrics.conversions'] / daily['metrics.clicks'].replace(0, np.nan)).fillna(0.0)
                    daily['CPA'] = (daily['Spend'] / daily['metrics.conversions'].replace(0, np.nan)).fillna(0.0)
                    rt_bench = db_service.get_account_benchmarks(selected_customer)
                    target_conv_rate = rt_bench.target_conv_rate
                    target_cpa = rt_bench.target_cpa
                    benchmark_ctr = rt_bench.benchmark_ctr
                    daily['conv_rate_score'] = np.minimum((daily['Conv Rate'] / target_conv_rate) * 30, 30).fillna(0)
                    daily['cpa_score'] = np.where(daily['CPA'] == 0, 0, np.minimum((target_cpa / daily['CPA']) * 30, 30)).astype(float)
                    daily['ctr_score'] = np.minimum((daily['CTR'] / benchmark_ctr) * 20, 20).fillna(0)
                    daily['confidence_score'] = np.minimum(daily['metrics.clicks'] / 100 * 10, 10).fillna(0)
                    daily['Health Score'] = (
                        daily['conv_rate_score'] + daily['cpa_score'] + daily['ctr_score'] + daily['confidence_score']
                    )
                    daily['Date'] = pd.to_datetime(daily['segments.date'], errors='coerce')
                    daily_health = daily[['Date','Health Score']].copy()
                    daily_health.rename(columns={'Health Score':'Avg_Health_Score'}, inplace=True)
                    fig_trend = px.line(
                        daily_health, x='Date', y='Avg_Health_Score',
                        markers=True
                    )
                    fig_trend.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='rgba(255,255,255,0.8)'),
                        showlegend=False,
                        margin=dict(l=0, r=0, t=0, b=0)
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("No hay datos para tendencias")
            else:
                st.info("No hay datos para distribución")
        
        with col_right:
            st.markdown("### ⚡ Quick Actions")
            
            scheduler_status = scheduler_service.get_job_status()
            
            if scheduler_status.get('scheduler_running'):
                st.success("✅ Scheduler Active")
            else:
                st.error("❌ Scheduler Inactive")
            
            if st.button("🔄 Trigger Ingestion", use_container_width=True):
                with st.spinner("Triggering..."):
                    success = scheduler_service.trigger_job_manually('daily_data_ingestion')
                    if success:
                        st.success("✅ Triggered")
                    else:
                        st.error("❌ Failed")
            
            if st.button("🎯 Calculate Scores", use_container_width=True):
                with st.spinner("Calculating..."):
                    success = scheduler_service.trigger_job_manually('calculate_health_scores')
                    if success:
                        st.success("✅ Triggered")
                    else:
                        st.error("❌ Failed")
            
            st.markdown("---")
            st.markdown("### 📋 Recent Actions")
            
            if recent_actions:
                for action in recent_actions[:5]:
                    status_icon = "✅" if action.get('status') == 'completed' else "⏳" if action.get('status') == 'pending' else "❌"
                    st.write(f"{status_icon} {action.get('action_type', 'Unknown')} - {action.get('keyword_text', 'N/A')}")
            else:
                st.info("No recent actions")
        
        st.markdown("---")
        
        # Action Recommendations Section
        st.markdown("## 🎯 Action Recommendations")
        
        if health_scores and keyword_metrics:
            recommendations = []
            
            if "Quick Wins" in action_filter:
                quick_wins = health_service.get_quick_wins(selected_customer)
                recommendations.extend([{**qw, 'type': 'Quick Win'} for qw in quick_wins[:10]])
            
            if "Vampire Keywords" in action_filter:
                vampires = health_service.get_vampire_keywords(selected_customer)
                recommendations.extend([{**v, 'type': 'Vampire'} for v in vampires[:10]])
            
            if "Saturation Alerts" in action_filter:
                saturated = health_service.get_saturation_alerts(selected_customer)
                recommendations.extend([{**s, 'type': 'Saturation'} for s in saturated[:10]])
            
            if "Bid Recommendations" in action_filter:
                bid_recs = health_service.get_bid_recommendations(selected_customer, days_back=selected_days)
                recommendations.extend([{**b, 'type': 'Bid Change'} for b in bid_recs[:10]])
            
            if recommendations:
                tab_names = list(set([r['type'] for r in recommendations]))
                tabs = st.tabs(tab_names)
                
                for i, tab_name in enumerate(tab_names):
                    with tabs[i]:
                        tab_recommendations = [r for r in recommendations if r['type'] == tab_name]
                        
                        display_data = []
                        for rec in tab_recommendations:
                            display_data.append({
                                'Keyword': rec.get('keyword_text', 'N/A'),
                                'Health Score': f"{get_health_color(rec.get('health_score', 0))} {rec.get('health_score', 0):.1f}",
                                'Current Bid': format_currency(rec.get('current_bid', 0)),
                                'Recommended Bid': format_currency(rec.get('recommended_bid', 0)) if rec.get('recommended_bid') else 'N/A',
                                'Change %': f"{rec.get('bid_change_percent', 0):+.1f}%" if rec.get('bid_change_percent') else 'N/A',
                                'Justification': rec.get('justification', 'N/A')[:50] + '...' if len(rec.get('justification', '')) > 50 else rec.get('justification', 'N/A'),
                                'Risk': rec.get('risk_level', 'medium').title()
                            })
                        
                        if display_data:
                            df_display = pd.DataFrame(display_data)
                            st.dataframe(df_display, use_container_width=True)
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if st.button(f"👁️ Preview {tab_name}", key=f"preview_{tab_name}"):
                                    st.session_state[f'preview_{tab_name}'] = True
                            
                            with col2:
                                if st.button(f"⚡ Execute {tab_name}", key=f"execute_{tab_name}"):
                                    st.session_state[f'execute_{tab_name}'] = True
                            
                            with col3:
                                if st.button(f"⏸️ Pause", key=f"pause_{tab_name}"):
                                    st.session_state[f'pause_{tab_name}'] = True
                            
                            if st.session_state.get(f'preview_{tab_name}'):
                                show_preview_modal(tab_recommendations, tab_name)
                            
                            if st.session_state.get(f'execute_{tab_name}'):
                                show_execution_modal(tab_recommendations, tab_name, action_service)
                            
                            if st.session_state.get(f'pause_{tab_name}'):
                                show_pause_modal(tab_recommendations, tab_name, action_service)
                        
                        else:
                            st.info(f"No {tab_name.lower()} recommendations found")
            
            else:
                st.info("No recommendations available")
        
        else:
            st.info("📊 Insufficient data")
        
        st.markdown("---")
        
        # Detailed Keyword Analysis Table
        st.markdown("## 📋 Detailed Keyword Analysis")

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=selected_days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        df_detailed = None
        try:
            with st.spinner("⏳ Loading keyword performance..."):
                kw_config = ReportConfig(
                    report_name='Keyword Performance Report RT',
                    customer_ids=[selected_customer],
                    metrics=[
                        'metrics.impressions',
                        'metrics.clicks',
                        'metrics.cost_micros',
                        'metrics.conversions',
                        'metrics.conversions_value',
                        'metrics.ctr',
                        'metrics.average_cpc'
                    ],
                    dimensions=[
                        'campaign.id',
                        'campaign.name',
                        'ad_group.id',
                        'ad_group.name',
                        'ad_group_criterion.keyword.text',
                        'ad_group_criterion.keyword.match_type',
                        'ad_group_criterion.status',
                        'ad_group_criterion.quality_info.quality_score',
                        'segments.date'
                    ],
                    date_range=f"{start_date_str} AND {end_date_str}",
                    from_resource='keyword_view',
                    filters={
                        'campaign.status': 'ENABLED',
                        'ad_group_criterion.status': 'ENABLED'
                    }
                )
                kw_report = report_service.generate_custom_report(kw_config)
            
            with st.expander("🧪 API Diagnostics", expanded=False):
                st.caption("**GAQL executed:**")
                st.code(kw_config.to_gaql_query(), language="sql")
                st.write({
                    'Success': kw_report.get('success'),
                    'Rows': kw_report.get('total_rows'),
                    'Errors': kw_report.get('errors')
                })
            
            if kw_report.get('success') and kw_report.get('data'):
                df_kw = pd.DataFrame(kw_report['data'])
                
                numeric_cols = [
                    'metrics.impressions', 'metrics.clicks', 'metrics.cost_micros',
                    'metrics.conversions', 'metrics.conversions_value',
                    'metrics.ctr', 'metrics.average_cpc',
                    'ad_group_criterion.quality_info.quality_score'
                ]
                for c in numeric_cols:
                    if c in df_kw.columns:
                        df_kw[c] = pd.to_numeric(df_kw[c], errors='coerce').fillna(0.0)
                
                df_kw['Spend'] = df_kw['metrics.cost_micros'] / 1_000_000
                
                required_cols = [
                    'ad_group_criterion.keyword.text',
                    'campaign.id', 'campaign.name',
                    'ad_group.id', 'ad_group.name'
                ]
                
                if all(col in df_kw.columns for col in required_cols):
                    grouped_kw = df_kw.groupby(required_cols, as_index=False).agg({
                        'metrics.impressions': 'sum',
                        'metrics.clicks': 'sum',
                        'metrics.conversions': 'sum',
                        'metrics.conversions_value': 'sum',
                        'Spend': 'sum',
                        'ad_group_criterion.quality_info.quality_score': 'mean'
                    })
                    
                    grouped_kw['CTR'] = (grouped_kw['metrics.clicks'] / grouped_kw['metrics.impressions'].replace(0, np.nan) * 100).fillna(0.0).round(2)
                    grouped_kw['Avg CPC'] = (grouped_kw['Spend'] / grouped_kw['metrics.clicks'].replace(0, np.nan)).fillna(0.0).round(2)
                    grouped_kw['Conv Rate'] = (grouped_kw['metrics.conversions'] / grouped_kw['metrics.clicks'].replace(0, np.nan) * 100).fillna(0.0).round(2)
                    grouped_kw['CPA'] = (grouped_kw['Spend'] / grouped_kw['metrics.conversions'].replace(0, np.nan)).fillna(0.0).round(2)
                    grouped_kw['Spend'] = grouped_kw['Spend'].round(2)
                    
                    benchmarks = db_service.get_account_benchmarks(selected_customer)
                    target_conv_rate = benchmarks.target_conv_rate
                    target_cpa = benchmarks.target_cpa
                    benchmark_ctr = benchmarks.benchmark_ctr
                    
                    grouped_kw['conv_rate_decimal'] = grouped_kw['Conv Rate'] / 100
                    grouped_kw['conv_rate_score'] = np.minimum(
                        (grouped_kw['conv_rate_decimal'] / target_conv_rate) * 30, 30
                    ).fillna(0)
                    
                    grouped_kw['cpa_score'] = np.where(
                        grouped_kw['CPA'] == 0,
                        0,
                        np.minimum((target_cpa / grouped_kw['CPA']) * 30, 30)
                    ).astype(float)
                    
                    grouped_kw['ctr_decimal'] = grouped_kw['CTR'] / 100
                    grouped_kw['ctr_score'] = np.minimum(
                        (grouped_kw['ctr_decimal'] / benchmark_ctr) * 20, 20
                    ).fillna(0)
                    
                    grouped_kw['confidence_score'] = np.minimum(
                        grouped_kw['metrics.clicks'] / 100 * 10, 10
                    ).fillna(0)
                    
                    grouped_kw['quality_score_normalized'] = grouped_kw['ad_group_criterion.quality_info.quality_score'].apply(
                        lambda x: None if x == 0 or pd.isna(x) else x
                    )

                    grouped_kw['quality_score_points'] = grouped_kw['quality_score_normalized'].apply(
                        lambda x: 5.0 if pd.isna(x) else min(float(x), 10)
                    )

                    grouped_kw['quality_score_display'] = grouped_kw['quality_score_normalized'].apply(
                        lambda x: 'N/A' if pd.isna(x) else f"{x:.1f}"
                    )
                    
                    grouped_kw['Health Score Raw'] = (
                        grouped_kw['conv_rate_score'] +
                        grouped_kw['cpa_score'] +
                        grouped_kw['ctr_score'] +
                        grouped_kw['confidence_score'] +
                        grouped_kw['quality_score_points']
                    )
                    
                    grouped_kw['data_confidence'] = np.minimum(
                        grouped_kw['metrics.clicks'] / 50, 1.0
                    )
                    grouped_kw['Health Score'] = (
                        grouped_kw['Health Score Raw'] * grouped_kw['data_confidence']
                    ).round(2)
                    
                    def get_category_from_score(score):
                        if score >= 70:
                            return 'excellent'
                        elif score >= 40:
                            return 'good'
                        elif score > 0:
                            return 'warning'
                        else:
                            return 'critical'
                    
                    grouped_kw['Status'] = grouped_kw['Health Score'].apply(get_health_status)
                    grouped_kw['Status Emoji'] = grouped_kw['Health Score'].apply(get_health_color)
                    grouped_kw['Category'] = grouped_kw['Health Score'].apply(get_category_from_score)
                    
                    def get_recommended_action_rt(row):
                        score = row['Health Score']
                        clicks = row['metrics.clicks']
                        conversions = row['metrics.conversions']
                        qs = row['quality_score_normalized']
                        
                        if pd.isna(qs):
                            if clicks < 20:
                                return 'monitor'
                            if clicks >= 50 and conversions == 0:
                                return 'optimize'
                            if score >= 70:
                                return 'increase_bid_moderate'
                            if score < 30:
                                return 'decrease_bid'
                            return 'monitor'
                        
                        if clicks < 20:
                            return 'monitor'
                        
                        if qs < 4:
                            return 'pause_recreate'
                        
                        if score < 30 and clicks > 50 and conversions == 0:
                            return 'pause'
                        
                        if 30 <= score < 50:
                            return 'decrease_bid'
                        if 70 <= score < 85:
                            return 'increase_bid_moderate'
                        if score >= 85:
                            return 'increase_bid_aggressive'
                        
                        return 'monitor'
                    
                    grouped_kw['Recommended Action'] = grouped_kw.apply(get_recommended_action_rt, axis=1)
                    
                    action_priority_map = {
                        'pause': 1,
                        'pause_recreate': 1,
                        'increase_bid_aggressive': 1,
                        'decrease_bid': 2,
                        'increase_bid_moderate': 2,
                        'monitor': 3
                    }
                    grouped_kw['Priority'] = grouped_kw['Recommended Action'].map(action_priority_map).fillna(3)
                    
                    grouped_kw.rename(columns={
                        'ad_group_criterion.keyword.text': 'Keyword',
                        'campaign.name': 'Campaign',
                        'campaign.id': 'Campaign ID',
                        'ad_group.name': 'Ad Group',
                        'ad_group.id': 'Ad Group ID',
                        'metrics.impressions': 'Impressions',
                        'metrics.clicks': 'Clicks',
                        'metrics.conversions': 'Conversions',
                    }, inplace=True)

                    display_columns = [
                        'Keyword', 'Campaign', 'Ad Group',
                        'Status Emoji', 'Health Score', 'Status', 'Category',
                        'Impressions', 'Clicks', 'CTR', 'Avg CPC', 'Spend',
                        'Conversions', 'Conv Rate', 'CPA',
                        'quality_score_display',
                        'Recommended Action', 'Priority'
                    ]

                    df_detailed = grouped_kw[display_columns].copy()
                    df_detailed.rename(columns={'quality_score_display': 'Quality Score'}, inplace=True)
                    
                    df_detailed = df_detailed[df_detailed['Health Score'] >= min_health_score]
                    df_detailed = df_detailed.sort_values('Health Score', ascending=False)
                    
                    st.caption(f"✅ {len(df_detailed)} keywords (min filter: {min_health_score})")
                
                else:
                    st.warning("⚠️ Missing expected columns")
                    df_detailed = None
            else:
                st.info("📋 No keyword data for selected period")
                df_detailed = None

        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            logger.error(f"Error in keyword table: {e}", exc_info=True)
            df_detailed = None

        if df_detailed is not None and not df_detailed.empty:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_term = st.text_input("🔍 Search", placeholder="Type to filter...")
            
            with col2:
                status_filter = st.selectbox(
                    "Filter by Status",
                    options=["All"] + list(df_detailed['Status'].unique())
                )
            
            with col3:
                category_filter = st.selectbox(
                    "Filter by Category",
                    options=["All"] + list(df_detailed['Category'].unique())
                )
            
            filtered_df = df_detailed.copy()
            
            if search_term:
                filtered_df = filtered_df[filtered_df['Keyword'].str.contains(search_term, case=False, na=False)]
            
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['Status'] == status_filter]
            
            if category_filter != "All":
                filtered_df = filtered_df[filtered_df['Category'] == category_filter]
            
            qs_na_count = (df_detailed['Quality Score'] == 'N/A').sum()
            if qs_na_count > 0:
                st.info(
                    f"ℹ️ {qs_na_count} keywords have Quality Score 'N/A' (new or insufficient history). "
                    f"Neutral QS (5) assumed for Health Score calculation."
                )
            
            try:
                st.dataframe(
                    filtered_df.style.background_gradient(
                        subset=['Health Score'],
                        cmap='RdYlGn',
                        vmin=0,
                        vmax=100
                    ).format({
                        'Health Score': '{:.1f}',
                        'CTR': '{:.2f}%',
                        'Avg CPC': '${:.2f}',
                        'Spend': '${:.2f}',
                        'Conv Rate': '{:.2f}%',
                        'CPA': '${:.2f}',
                    }),
                    use_container_width=True,
                    height=500
                )
            except Exception as e:
                st.dataframe(filtered_df, use_container_width=True, height=500)
             
            st.caption(f"Showing {len(filtered_df)} of {len(df_detailed)} keywords")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📥 Export CSV", use_container_width=True):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download",
                        data=csv,
                        file_name=f"keyword_health_{selected_customer}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                                mime="text/csv",
                        use_container_width=True
                    )
        else:
            st.info("📋 No detailed data available")
        
        # Automatic Bid Adjustments Section
        show_automatic_bid_adjustments(df_detailed, selected_customer)

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        st.error(f"❌ Error loading data: {str(e)}")


def show_preview_modal(recommendations: List[Dict], tab_name: str):
    """Show preview modal for recommendations"""
    st.markdown(f"### 👁️ Preview {tab_name} Actions")
    
    if recommendations:
        preview_data = []
        for rec in recommendations:
            preview_data.append({
                'Keyword': rec.get('keyword_text', 'N/A'),
                'Current Bid': format_currency(rec.get('current_bid', 0)),
                'Recommended Bid': format_currency(rec.get('recommended_bid', 0)) if rec.get('recommended_bid') else 'N/A',
                'Change %': f"{rec.get('bid_change_percent', 0):+.1f}%" if rec.get('bid_change_percent') else 'N/A',
                'Risk': rec.get('risk_level', 'medium').title(),
                'Justification': rec.get('justification', 'N/A')
            })
        
        df_preview = pd.DataFrame(preview_data)
        st.dataframe(df_preview, use_container_width=True)
        
        if st.button(f"Close Preview", key=f"close_preview_{tab_name}"):
            st.session_state[f'preview_{tab_name}'] = False
            st.rerun()
    else:
        st.info("No recommendations to preview")


def show_execution_modal(recommendations: List[Dict], tab_name: str, action_service):
    """Show execution modal for recommendations"""
    st.markdown(f"### ⚡ Execute {tab_name} Actions")
    
    if recommendations:
        st.warning(f"⚠️ You are about to execute {len(recommendations)} {tab_name.lower()} actions. This cannot be undone.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"✅ Confirm Execute", key=f"confirm_execute_{tab_name}"):
                bid_requests = []
                for rec in recommendations:
                    if rec.get('recommended_bid'):
                        bid_requests.append(BidChangeRequest(
                            customer_id=rec.get('customer_id', ''),
                            campaign_id=rec.get('campaign_id', ''),
                            ad_group_id=rec.get('ad_group_id', ''),
                            keyword_text=rec.get('keyword_text', ''),
                            current_bid=rec.get('current_bid', 0),
                            new_bid=rec.get('recommended_bid', 0),
                            change_percent=rec.get('bid_change_percent', 0),
                            justification=rec.get('justification', ''),
                            health_score=rec.get('health_score', 0),
                            risk_level=rec.get('risk_level', 'medium')
                        ))
                
                if bid_requests:
                    with st.spinner(f"Executing {len(bid_requests)} bid changes..."):
                        try:
                            result = action_service.execute_bid_changes(bid_requests)
                            
                            if result['successful'] > 0:
                                st.success(f"✅ Executed {result['successful']} actions successfully!")
                            
                            if result['failed'] > 0:
                                st.error(f"❌ Failed to execute {result['failed']} actions")
                                
                                if result['errors']:
                                    with st.expander("View Errors"):
                                        for error in result['errors']:
                                            st.write(f"- {error.get('keyword', 'Unknown')}: {error.get('error', 'Unknown error')}")
                        
                        except AttributeError:
                            st.error("❌ Action service not available. Check configuration.")
                            logger.error("ActionExecutionService missing execute_bid_changes method")
                        except Exception as e:
                            st.error(f"❌ Error executing actions: {str(e)}")
                            logger.error(f"Error in execute_bid_changes: {e}", exc_info=True)
                
                st.session_state[f'execute_{tab_name}'] = False
                st.rerun()
        
        with col2:
            if st.button(f"❌ Cancel", key=f"cancel_execute_{tab_name}"):
                st.session_state[f'execute_{tab_name}'] = False
                st.rerun()
    else:
        st.info("No actions to execute")


def show_pause_modal(recommendations: List[Dict], tab_name: str, action_service):
    """Show pause modal for recommendations"""
    st.markdown(f"### ⏸️ Pause Keywords from {tab_name}")
    
    if recommendations:
        st.warning(f"⚠️ You are about to pause {len(recommendations)} keywords. This will stop them from showing ads.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"✅ Confirm Pause", key=f"confirm_pause_{tab_name}"):
                pause_requests = []
                for rec in recommendations:
                    pause_requests.append({
                        'customer_id': rec.get('customer_id', ''),
                        'campaign_id': rec.get('campaign_id', ''),
                        'ad_group_id': rec.get('ad_group_id', ''),
                        'keyword_text': rec.get('keyword_text', '')
                    })
                
                if pause_requests:
                    try:
                        with st.spinner(f"Pausing {len(pause_requests)} keywords..."):
                            result = action_service.pause_keywords(pause_requests)
                            
                            if result.get('successful', 0) > 0:
                                st.success(f"✅ Paused {result['successful']} keywords successfully!")
                            
                            if result.get('failed', 0) > 0:
                                st.error(f"❌ Failed to pause {result['failed']} keywords")
                                
                                if result.get('errors'):
                                    with st.expander("View Errors"):
                                        for error in result['errors']:
                                            st.write(f"- {error.get('keyword', 'Unknown')}: {error.get('error', 'Unknown error')}")
                    
                    except AttributeError as e:
                        st.error("❌ Pause service not available. Check configuration.")
                        logger.error(f"ActionExecutionService pause error: {e}", exc_info=True)
                    except Exception as e:
                        st.error(f"❌ Error pausing keywords: {str(e)}")
                        logger.error(f"Error in pause_keywords: {e}", exc_info=True)
                else:
                    st.warning("⚠️ No keywords to pause")
                
                st.session_state[f'pause_{tab_name}'] = False
                st.rerun()
        
        with col2:
            if st.button(f"❌ Cancel", key=f"cancel_pause_{tab_name}"):
                st.session_state[f'pause_{tab_name}'] = False
                st.rerun()
    else:
        st.info("No keywords to pause")


def show_automatic_bid_adjustments(df_detailed, selected_customer):
    """Muestra la sección de ajustes automáticos de pujas con diseño moderno"""
    st.markdown("---")
    st.markdown("## 🤖 Automatic Bid Adjustments")
    st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Ajustes inteligentes basados en health scores</p>", unsafe_allow_html=True)

    st.info(
        "ℹ️ **Importante:** Solo se pueden ajustar pujas de keywords con **CPC Manual**. "
        "Keywords con estrategias automáticas se saltearán automáticamente."
    )

    with st.expander("🔧 Debug Info (Google Ads Client)", expanded=False):
        if st.session_state.get('google_ads_client'):
            client_obj = st.session_state.google_ads_client
            st.write("**Tipo de objeto:**", type(client_obj).__name__)
            st.write("**Tiene atributo `.client`:**", hasattr(client_obj, 'client'))
            
            if hasattr(client_obj, 'client'):
                st.write("**Tipo de `.client`:**", type(client_obj.client).__name__)
                st.write("**`.client` tiene `get_service`:**", hasattr(client_obj.client, 'get_service'))
            else:
                st.error("❌ El wrapper NO tiene atributo `.client`")
                st.write("**Atributos disponibles:**", [attr for attr in dir(client_obj) if not attr.startswith('_')])
            
            st.write("**Wrapper tiene `get_service`:**", hasattr(client_obj, 'get_service'))
            st.write("**Wrapper tiene `get_type`:**", hasattr(client_obj, 'get_type'))
        else:
            st.error("❌ `google_ads_client` no está en session_state")

    if df_detailed is not None and not df_detailed.empty:
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📈 Aumentar Pujas")
            increase_threshold = st.slider(
                "Health Score mínimo",
                min_value=70,
                max_value=100,
                value=80,
                help="Aumentar puja para keywords con health score mayor a este valor"
            )
            increase_percent = st.slider(
                "Porcentaje de aumento",
                min_value=5,
                max_value=50,
                value=20,
                step=5,
                help="% de aumento en la puja"
            )
        
        with col2:
            st.markdown("#### 📉 Reducir Pujas")
            decrease_threshold = st.slider(
                "Health Score máximo",
                min_value=0,
                max_value=50,
                value=40,
                help="Reducir puja para keywords con health score menor a este valor"
            )
            decrease_percent = st.slider(
                "Porcentaje de reducción",
                min_value=5,
                max_value=50,
                value=20,
                step=5,
                help="% de reducción en la puja"
            )
        
        with col3:
            st.markdown("#### ⏸️ Pausar Keywords")
            pause_min_spend = st.number_input(
                "Gasto mínimo para pausar",
                min_value=0,
                max_value=1000,
                value=50,
                help="Solo pausar si el gasto es mayor a este valor"
            )
            pause_min_clicks = st.number_input(
                "Clicks mínimos para pausar",
                min_value=0,
                max_value=200,
                value=30,
                help="Solo pausar si tiene al menos estos clicks"
            )
        
        keywords_to_increase = df_detailed[df_detailed['Health Score'] >= increase_threshold]
        keywords_to_decrease = df_detailed[df_detailed['Health Score'] < decrease_threshold]
        keywords_to_pause = df_detailed[
            (df_detailed['Conversions'] == 0) & 
            (df_detailed['Spend'] >= pause_min_spend) &
            (df_detailed['Clicks'] >= pause_min_clicks)
        ]
        
        st.markdown("#### 📊 Resumen de Cambios Propuestos")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📈 Keywords a Aumentar",
                len(keywords_to_increase),
                delta=f"+{increase_percent}%"
            )
        
        with col2:
            st.metric(
                "📉 Keywords a Reducir",
                len(keywords_to_decrease),
                delta=f"-{decrease_percent}%"
            )
        
        with col3:
            st.metric(
                "⏸️ Keywords a Pausar",
                len(keywords_to_pause),
                delta="0 conversions"
            )
        
        with st.expander("👁️ Vista Previa de Cambios", expanded=False):
            tab1, tab2, tab3 = st.tabs(["📈 Aumentar", "📉 Reducir", "⏸️ Pausar"])
            
            with tab1:
                if not keywords_to_increase.empty:
                    preview_increase = keywords_to_increase[['Keyword', 'Health Score', 'Spend', 'Conversions']].head(10)
                    st.dataframe(preview_increase, use_container_width=True)
                    if len(keywords_to_increase) > 10:
                        st.caption(f"... y {len(keywords_to_increase) - 10} más")
                else:
                    st.info("✨ No hay keywords que cumplan el criterio")
            
            with tab2:
                if not keywords_to_decrease.empty:
                    preview_decrease = keywords_to_decrease[['Keyword', 'Health Score', 'Spend', 'Conversions']].head(10)
                    st.dataframe(preview_decrease, use_container_width=True)
                    if len(keywords_to_decrease) > 10:
                        st.caption(f"... y {len(keywords_to_decrease) - 10} más")
                else:
                    st.info("✨ No hay keywords que cumplan el criterio")
            
            with tab3:
                if not keywords_to_pause.empty:
                    preview_pause = keywords_to_pause[['Keyword', 'Spend', 'Clicks', 'Conversions']].head(10)
                    st.dataframe(preview_pause, use_container_width=True)
                    if len(keywords_to_pause) > 10:
                        st.caption(f"... y {len(keywords_to_pause) - 10} más")
                else:
                    st.info("✨ No hay keywords que cumplan el criterio")
        
        st.markdown("#### ⚙️ Modo de Ejecución")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            dry_run = st.checkbox(
                "🧪 Modo Prueba (Dry Run)",
                value=True,
                help="Simula los cambios sin aplicarlos realmente"
            )
        
        with col2:
            confirm_changes = st.checkbox(
                "✅ Confirmo que quiero aplicar estos cambios",
                value=False,
                help="Debes confirmar para habilitar la ejecución"
            )
        
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            execute_button = st.button(
                "🚀 Aplicar Cambios Automáticos" if not dry_run else "🧪 Simular Cambios",
                disabled=not dry_run and not confirm_changes,
                use_container_width=True,
                type="primary"
            )
        
        if execute_button:
            try:
                from services.bid_adjustment_service import BidAdjustmentService, BidAdjustment
                
                if not st.session_state.get('google_ads_client'):
                    st.error("❌ Cliente de Google Ads no inicializado")
                    st.stop()
                
                try:
                    bid_service = BidAdjustmentService(st.session_state.google_ads_client)
                    logger.info("✅ BidAdjustmentService inicializado correctamente")
                except Exception as e:
                    st.error(f"❌ Error inicializando servicio: {e}")
                    st.stop()
                
                with st.spinner("🔄 Procesando ajustes de pujas..."):
                    
                    all_keywords = list(set(
                        keywords_to_increase['Keyword'].tolist() +
                        keywords_to_decrease['Keyword'].tolist() +
                        keywords_to_pause['Keyword'].tolist()
                    ))
                    
                    keyword_map = bid_service.get_keyword_criterion_ids(selected_customer, all_keywords)
                    
                    keywords_found = len(keyword_map)
                    keywords_with_manual_bid = sum(1 for kw_data in keyword_map.values() if kw_data['current_bid_micros'] > 0)
                    keywords_without_bid = keywords_found - keywords_with_manual_bid
                    
                    st.caption(
                        f"📊 {keywords_found} encontradas | "
                        f"✅ {keywords_with_manual_bid} con puja manual | "
                        f"⚠️ {keywords_without_bid} saltadas (estrategia automática)"
                    )
                    
                    adjustments = []
                    skipped_auto_bidding = []
                    
                    for _, row in keywords_to_increase.iterrows():
                        kw_text = row['Keyword']
                        if kw_text in keyword_map:
                            kw_data = keyword_map[kw_text]
                            current_bid = kw_data['current_bid_micros']
                            
                            if current_bid > 0:
                                new_bid = int(current_bid * (1 + increase_percent / 100))
                                adjustments.append(BidAdjustment(
                                    customer_id=selected_customer,
                                    ad_group_id=str(kw_data['ad_group_id']),
                                    criterion_id=str(kw_data['criterion_id']),
                                    keyword_text=kw_text,
                                    current_bid_micros=current_bid,
                                    new_bid_micros=new_bid,
                                    adjustment_percent=increase_percent,
                                    reason=f"Health Score: {row['Health Score']:.1f}"
                                ))
                            else:
                                skipped_auto_bidding.append(kw_text)
                    
                    for _, row in keywords_to_decrease.iterrows():
                        kw_text = row['Keyword']
                        if kw_text in keyword_map:
                            kw_data = keyword_map[kw_text]
                            current_bid = kw_data['current_bid_micros']
                            
                            if current_bid > 0:
                                new_bid = int(current_bid * (1 - decrease_percent / 100))
                                adjustments.append(BidAdjustment(
                                    customer_id=selected_customer,
                                    ad_group_id=str(kw_data['ad_group_id']),
                                    criterion_id=str(kw_data['criterion_id']),
                                    keyword_text=kw_text,
                                    current_bid_micros=current_bid,
                                    new_bid_micros=new_bid,
                                    adjustment_percent=-decrease_percent,
                                    reason=f"Health Score: {row['Health Score']:.1f}"
                                ))
                            else:
                                skipped_auto_bidding.append(kw_text)
                    
                    if adjustments:
                        results = bid_service.bulk_adjust_bids(adjustments, dry_run=dry_run)
                        
                        if dry_run:
                            st.info(f"🧪 **Simulación completada** - No se hicieron cambios reales")
                        else:
                            st.success(f"✅ **Cambios aplicados exitosamente**")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Exitosos", results['successful'])
                        with col2:
                            st.metric("Fallidos", results['failed'])
                        with col3:
                            st.metric("Ajustados a min", results.get('adjusted_to_min', 0))
                        with col4:
                            st.metric("Saltadas", len(skipped_auto_bidding))
                        
                        with st.expander("📋 Ver Detalles de Cambios"):
                            details_df = pd.DataFrame(results['details'])
                            st.dataframe(details_df, use_container_width=True)
                        
                        if results['errors']:
                            with st.expander("⚠️ Ver Errores"):
                                for error in results['errors']:
                                    st.error(f"**{error['keyword']}**: {error['error']}")
                        
                        if skipped_auto_bidding:
                            with st.expander(f"⚠️ Keywords saltadas ({len(skipped_auto_bidding)})"):
                                st.write("Estas keywords usan estrategia de puja automática:")
                                for kw in skipped_auto_bidding[:50]:
                                    st.write(f"- {kw}")
                                if len(skipped_auto_bidding) > 50:
                                    st.write(f"... y {len(skipped_auto_bidding) - 50} más")
                    else:
                        st.warning("⚠️ No hay keywords con puja manual para ajustar")
                    
                    paused = 0
                    failed_pause = 0
                    
                    if not keywords_to_pause.empty and not dry_run:
                        st.markdown("---")
                        st.markdown("### ⏸️ Pausando Keywords...")
                        
                        for _, row in keywords_to_pause.iterrows():
                            kw_text = row['Keyword']
                            if kw_text in keyword_map:
                                kw_data = keyword_map[kw_text]
                                success, msg = bid_service.pause_keyword(
                                    customer_id=selected_customer,
                                    ad_group_id=str(kw_data['ad_group_id']),
                                    criterion_id=str(kw_data['criterion_id']),
                                    dry_run=dry_run
                                )
                                
                                if success:
                                    paused += 1
                                else:
                                    failed_pause += 1
                                    st.error(f"Error pausando **{kw_text}**: {msg}")
                        
                        if paused > 0:
                            st.success(f"✅ {paused} keywords pausadas")
                        if failed_pause > 0:
                            st.error(f"❌ {failed_pause} keywords fallaron")
        
            except Exception as e:
                st.error(f"❌ Error general procesando ajustes automáticos: {e}")
                logger.error(f"Error en ejecución: {e}", exc_info=True)

    else:
        st.info("📊 No hay datos de keywords para aplicar ajustes automáticos")


if __name__ == "__main__":
    main()