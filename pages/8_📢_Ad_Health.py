"""
Ad Health Dashboard - Ultra Modern Design 2030
Sistema de salud para anuncios con diseño glassmorphism dark theme
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict

from modules.auth import require_auth
from utils.logger import get_logger
from utils.formatters import format_currency, format_percentage, format_number
from services.database_service import DatabaseService
from services.ad_health_service import AdHealthService

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Ad Health - Google Ads Dashboard",
    page_icon="📢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS - ULTRA MODERN 2030 ====================
def inject_modern_css():
    """Inyecta CSS ultra moderno con glassmorphism"""
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
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.4);
        --shadow-md: 0 8px 32px rgba(0, 0, 0, 0.5);
        --shadow-lg: 0 20px 60px rgba(0, 0, 0, 0.6);
    }
    
    /* ==================== GLOBAL STYLES ==================== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-darker) 0%, var(--bg-dark) 50%, #1a1a2e 100%);
        background-attachment: fixed;
    }
    
    /* Animated background grid */
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
        box-shadow: var(--shadow-lg);
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
    
    /* ==================== METRICS (KPI CARDS) ==================== */
    [data-testid="metric-container"] {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 2rem 1.5rem;
        box-shadow: var(--shadow-md);
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
    
    [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
        font-size: 0.9rem !important;
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
    
    .stButton > button:active {
        transform: translateY(-1px);
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
        box-shadow: var(--shadow-md);
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
        box-shadow: var(--shadow-sm);
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
    
    /* ==================== MULTISELECT ==================== */
    .stMultiSelect > div > div {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
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
    
    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4);
        }
        50% {
            box-shadow: 0 0 0 15px rgba(102, 126, 234, 0);
        }
    }
    
    /* Apply animations */
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
            📢
        </div>
        <p style="font-size: 1rem; color: rgba(255, 255, 255, 0.6); 
                  font-weight: 500; letter-spacing: 3px; text-transform: uppercase;
                  margin-bottom: 0.5rem;">
            Google Ads Intelligence
        </p>
        <p style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.8); 
                  font-weight: 400; max-width: 600px; margin: 0 auto;">
            Sistema inteligente de optimización con health scores en tiempo real
        </p>
        <div style="width: 100px; height: 3px; 
                    background: linear-gradient(90deg, transparent, #667eea, transparent);
                    margin: 2rem auto 0 auto;"></div>
    </div>
    """, unsafe_allow_html=True)

def get_health_status(score: float) -> str:
    """Get status text based on health score"""
    if score >= 70:
        return "Healthy"
    elif score >= 40:
        return "Needs Attention"
    else:
        return "Critical"

def format_headlines(headlines_list) -> str:
    """Format headlines list para display"""
    if isinstance(headlines_list, str):
        import ast
        try:
            headlines_list = ast.literal_eval(headlines_list)
        except:
            return headlines_list
    
    if isinstance(headlines_list, (list, tuple)) and len(headlines_list) > 0:
        return " | ".join(headlines_list[:2])
    return "N/A"

@require_auth
def main():
    """Main ad health page function"""
    
    # Inject modern CSS
    inject_modern_css()
    
    # Hero header
    render_hero_section()
    
    # Check services
    if not st.session_state.get('google_ads_client') or not st.session_state.get('services'):
        st.error("❌ Google Ads services not initialized. Please check your configuration.")
        return
    
    # Get selected customer
    selected_customer = st.session_state.get('selected_customer')
    if not selected_customer:
        st.warning("⚠️ No customer account selected. Please select an account from the sidebar.")
        return
    
    # Initialize services
    db_service = DatabaseService()
    ad_health_service = AdHealthService(st.session_state.google_ads_client, db_service)
    
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
            help="Filter ads by minimum health score"
        )
        
        # Ad status filter
        status_filter = st.multiselect(
            "📊 Ad Status",
            options=["ENABLED", "PAUSED"],
            default=["ENABLED"]
        )
        
        # Action type filter
        action_filter = st.multiselect(
            "⚡ Show Recommendations",
            options=["Winners", "Vampires", "Dormant", "Policy Issues"],
            default=["Vampires", "Policy Issues"]
        )
        
        st.markdown("---")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    try:
        # Calculate health scores in real-time
        with st.spinner("🔄 Calculando health scores de anuncios..."):
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=selected_days)
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            health_data = ad_health_service.calculate_ad_health_scores_realtime(
                customer_id=selected_customer,
                start_date=start_date_str,
                end_date=end_date_str
            )
            
            if health_data.empty:
                st.warning("⚠️ No se encontraron datos de anuncios para el período seleccionado")
                return
            
            df_ads = health_data
        
        # Apply filters
        df_filtered = df_ads[df_ads['health_score'] >= min_health_score]
        if status_filter:
            df_filtered = df_filtered[df_filtered['ad_status'].isin(status_filter)]
        
        st.caption(f"✅ {len(df_ads)} anuncios analizados | {len(df_filtered)} mostrados tras filtros")
        
        # Main dashboard metrics
        st.markdown(f"## 📊 Health Overview")
        st.markdown(f"<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Período: {date_range}</p>", unsafe_allow_html=True)
        
        if not df_filtered.empty:
            # Calculate summary metrics
            total_ads = len(df_filtered)
            avg_health_score = df_filtered['health_score'].mean()
            healthy_count = len(df_filtered[df_filtered['health_score'] >= 70])
            attention_count = len(df_filtered[(df_filtered['health_score'] >= 40) & (df_filtered['health_score'] < 70)])
            critical_count = len(df_filtered[df_filtered['health_score'] < 40])
            
            # KPI cards
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("📢 Total Ads", format_number(total_ads))
            
            with col2:
                st.metric("📈 Avg Health", f"{avg_health_score:.1f}")
            
            with col3:
                st.metric("🟢 Healthy", format_number(healthy_count), 
                         delta=f"{(healthy_count/total_ads)*100:.1f}%")
            
            with col4:
                st.metric("🟡 Attention", format_number(attention_count),
                         delta=f"{(attention_count/total_ads)*100:.1f}%")
            
            with col5:
                st.metric("🔴 Critical", format_number(critical_count),
                         delta=f"{(critical_count/total_ads)*100:.1f}%")
        
        st.markdown("---")
        
        # Two-column layout
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("### 📊 Health Score Distribution")
            
            if not df_filtered.empty:
                fig_hist = px.histogram(
                    df_filtered, x='health_score', nbins=20,
                    labels={'health_score': 'Health Score', 'count': 'Ads'},
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
                st.plotly_chart(fig_hist, use_container_width=True)
        
        with col_right:
            st.markdown("### 📊 Quick Stats")
            
            if not df_filtered.empty:
                total_spend = df_filtered['spend'].sum()
                total_conversions = df_filtered['conversions'].sum()
                avg_ctr = df_filtered['ctr'].mean()
                avg_conv_rate = df_filtered['conv_rate'].mean()
                
                st.metric("💰 Total Spend", format_currency(total_spend))
                st.metric("🎯 Conversions", f"{total_conversions:.0f}")
                st.metric("👆 Avg CTR", f"{avg_ctr:.2f}%")
                st.metric("📈 Avg Conv Rate", f"{avg_conv_rate:.2f}%")
        
        st.markdown("---")
        
        # Recommendations Section
        st.markdown("## 🎯 Ad Recommendations")
        
        recommendations = {}
        
        if "Winners" in action_filter:
            winners = ad_health_service.get_winner_ads(df_filtered)
            if not winners.empty:
                recommendations['🌟 Winners'] = winners
        
        if "Vampires" in action_filter:
            vampires = ad_health_service.get_vampire_ads(df_filtered)
            if not vampires.empty:
                recommendations['🧛 Vampires'] = vampires
        
        if "Dormant" in action_filter:
            dormant = ad_health_service.get_dormant_ads(df_filtered)
            if not dormant.empty:
                recommendations['😴 Dormant'] = dormant
        
        if "Policy Issues" in action_filter:
            policy_issues = ad_health_service.get_policy_issues(df_filtered)
            if not policy_issues.empty:
                recommendations['⚠️ Policy Issues'] = policy_issues
        
        if recommendations:
            tabs = st.tabs(list(recommendations.keys()))
            
            for i, (tab_name, tab_data) in enumerate(recommendations.items()):
                with tabs[i]:
                    st.write(f"**{len(tab_data)} {tab_name.lower()} encontrados**")
                    
                    display_cols = [
                        'status_emoji', 'headlines', 'campaign_name', 'ad_group_name',
                        'health_score', 'spend', 'clicks', 'conversions',
                        'ctr', 'conv_rate', 'recommended_action'
                    ]
                    
                    preview = tab_data[display_cols].head(10).copy()
                    preview['headlines'] = preview['headlines'].apply(format_headlines)
                    preview.columns = [
                        'Status', 'Headlines', 'Campaign', 'Ad Group',
                        'Health', 'Spend', 'Clicks', 'Conv',
                        'CTR', 'Conv Rate', 'Action'
                    ]
                    
                    st.dataframe(preview, use_container_width=True)
                    
                    if len(tab_data) > 10:
                        st.caption(f"... y {len(tab_data) - 10} más")
        else:
            st.info("No recommendations found with current filters")
        
        st.markdown("---")
        
        # Detailed Table
        st.markdown("## 📋 Detailed Ad Analysis")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search", placeholder="Search by headline or campaign...")
        
        with col2:
            health_filter = st.selectbox("Filter by Health", ["All", "Healthy", "Needs Attention", "Critical"])
        
        with col3:
            campaign_filter = st.selectbox("Filter by Campaign", ["All"] + sorted(df_filtered['campaign_name'].unique().tolist()))
        
        # Apply filters
        df_display = df_filtered.copy()
        
        if search_term:
            df_display = df_display[
                df_display['headlines'].astype(str).str.contains(search_term, case=False, na=False) |
                df_display['campaign_name'].str.contains(search_term, case=False, na=False)
            ]
        
        if health_filter != "All":
            if health_filter == "Healthy":
                df_display = df_display[df_display['health_score'] >= 70]
            elif health_filter == "Needs Attention":
                df_display = df_display[(df_display['health_score'] >= 40) & (df_display['health_score'] < 70)]
            elif health_filter == "Critical":
                df_display = df_display[df_display['health_score'] < 40]
        
        if campaign_filter != "All":
            df_display = df_display[df_display['campaign_name'] == campaign_filter]
        
        if not df_display.empty:
            display_df = df_display[[
                'status_emoji', 'headlines', 'campaign_name', 'ad_group_name',
                'health_score', 'health_category', 'impressions', 'clicks',
                'ctr', 'conversions', 'conv_rate', 'spend', 'cpa',
                'approval_status', 'recommended_action'
            ]].copy()
            
            display_df['headlines'] = display_df['headlines'].apply(format_headlines)
            display_df.columns = [
                'Status', 'Headlines', 'Campaign', 'Ad Group',
                'Health Score', 'Category', 'Impressions', 'Clicks',
                'CTR (%)', 'Conv', 'Conv Rate (%)', 'Spend', 'CPA',
                'Approval', 'Action'
            ]
            
            try:
                st.dataframe(
                    display_df.style.background_gradient(
                        subset=['Health Score'], cmap='RdYlGn', vmin=0, vmax=100
                    ).format({
                        'Health Score': '{:.1f}', 'CTR (%)': '{:.2f}',
                        'Conv Rate (%)': '{:.2f}', 'Spend': '${:.2f}', 'CPA': '${:.2f}'
                    }),
                    use_container_width=True, height=500
                )
            except:
                st.dataframe(display_df, use_container_width=True, height=500)
            
            st.caption(f"Showing {len(display_df)} of {len(df_filtered)} ads")
            
            # Export
            if st.button("📥 Export CSV", use_container_width=False):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download", csv,
                    file_name=f"ad_health_{selected_customer}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No ads match the current filters")
        
         # ===== AD MANAGEMENT SECTION =====
        st.markdown("---")
        st.markdown("## 🎛️ Ad Management")
        
        if not df_filtered.empty:
            # Tabs para diferentes acciones
            action_tab1, action_tab2, action_tab3 = st.tabs([
                "⏸️ Pause Ads",
                "▶️ Enable Ads",
                "📊 Bulk Actions"
            ])
            
            # ===== TAB 1: PAUSE ADS =====
            with action_tab1:
                st.markdown("### ⏸️ Pause Underperforming Ads")
                st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Pausa automáticamente anuncios con bajo rendimiento</p>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🎯 Selection Criteria")
                    
                    pause_health_threshold = st.slider(
                        "Max Health Score",
                        min_value=0,
                        max_value=50,
                        value=30,
                        help="Pause ads with health score below this value"
                    )
                    
                    pause_min_spend = st.number_input(
                        "Min Spend (to consider)",
                        min_value=0.0,
                        max_value=1000.0,
                        value=50.0,
                        step=10.0,
                        help="Only consider ads that spent at least this amount"
                    )
                    
                    pause_min_clicks = st.number_input(
                        "Min Clicks (to consider)",
                        min_value=0,
                        max_value=500,
                        value=30,
                        help="Only consider ads with at least this many clicks"
                    )
                
                with col2:
                    st.markdown("#### 📋 Ads to Pause")
                    
                    # Filter ads that meet pause criteria
                    ads_to_pause = df_filtered[
                        (df_filtered['health_score'] < pause_health_threshold) &
                        (df_filtered['spend'] >= pause_min_spend) &
                        (df_filtered['clicks'] >= pause_min_clicks) &
                        (df_filtered['ad_status'] == 'ENABLED')
                    ].copy()
                    
                    if not ads_to_pause.empty:
                        st.metric("Ads Selected", len(ads_to_pause))
                        st.metric("Total Spend", f"${ads_to_pause['spend'].sum():.2f}")
                        st.metric("Total Conversions", f"{ads_to_pause['conversions'].sum():.0f}")
                        
                        # Preview
                        with st.expander("👁️ Preview Ads to Pause"):
                            preview_pause = ads_to_pause[[
                                'ad_id', 'headlines', 'campaign_name', 'health_score', 
                                'spend', 'conversions'
                            ]].head(10).copy()
                            preview_pause['headlines'] = preview_pause['headlines'].apply(format_headlines)
                            st.dataframe(preview_pause, use_container_width=True)
                            if len(ads_to_pause) > 10:
                                st.caption(f"... and {len(ads_to_pause) - 10} more")
                    else:
                        st.info("✨ No ads meet the pause criteria with current filters")
                
                # Execution controls
                if not ads_to_pause.empty:
                    st.markdown("---")
                    st.markdown("#### ⚙️ Execution Mode")
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        dry_run_pause = st.checkbox(
                            "🧪 Dry Run Mode",
                            value=True,
                            help="Simulate without actually pausing",
                            key="dry_run_pause"
                        )
                    
                    with col2:
                        confirm_pause = st.checkbox(
                            "✅ I confirm I want to pause these ads",
                            value=False,
                            help="Required to enable execution",
                            key="confirm_pause"
                        )
                    
                    # Execute button
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        execute_pause = st.button(
                            "⏸️ Pause Selected Ads" if not dry_run_pause else "🧪 Simulate Pause",
                            disabled=not dry_run_pause and not confirm_pause,
                            use_container_width=True,
                            type="primary",
                            key="execute_pause_btn"
                        )
                    
                    if execute_pause:
                        # Import service
                        from services.ad_management_service import AdManagementService, AdAction
                        
                        try:
                            # Initialize service
                            ad_mgmt_service = AdManagementService(st.session_state.google_ads_client)
                            
                            # Prepare actions
                            actions = []
                            for _, row in ads_to_pause.iterrows():
                                actions.append(AdAction(
                                    customer_id=selected_customer,
                                    ad_group_id=str(row['ad_group_id']),
                                    ad_id=str(row['ad_id']),
                                    ad_headlines=format_headlines(row['headlines']),
                                    campaign_name=row['campaign_name'],
                                    ad_group_name=row['ad_group_name'],
                                    current_status=row['ad_status'],
                                    reason=f"Health Score: {row['health_score']:.1f}, Spend: ${row['spend']:.2f}, Conv: {row['conversions']:.0f}"
                                ))
                            
                            # Execute
                            with st.spinner(f"⏳ {'Simulating' if dry_run_pause else 'Pausing'} {len(actions)} ads..."):
                                results = ad_mgmt_service.bulk_pause_ads(actions, dry_run=dry_run_pause)
                            
                            # Show results
                            if dry_run_pause:
                                st.info(f"🧪 **Simulation completed** - No real changes made")
                            else:
                                st.success(f"✅ **Ads paused successfully**")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Successful", results['successful'])
                            with col2:
                                st.metric("Failed", results['failed'])
                            with col3:
                                st.metric("Total", len(actions))
                            
                            # Details
                            with st.expander("📋 View Details"):
                                details_df = pd.DataFrame(results['details'])
                                st.dataframe(details_df, use_container_width=True)
                            
                            # Errors
                            if results['errors']:
                                with st.expander("⚠️ View Errors"):
                                    for error in results['errors']:
                                        st.error(f"**{error['headlines']}** (ID: {error['ad_id']}): {error['error']}")
                        
                        except Exception as e:
                            st.error(f"❌ Error executing pause action: {e}")
                            logger.error(f"Error in pause execution: {e}", exc_info=True)
            
            # ===== TAB 2: ENABLE ADS =====
            with action_tab2:
                st.markdown("### ▶️ Enable Paused Ads")
                st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Reactiva anuncios que fueron pausados previamente</p>", unsafe_allow_html=True)
                
                # Filter paused ads
                paused_ads = df_filtered[df_filtered['ad_status'] == 'PAUSED'].copy()
                
                if not paused_ads.empty:
                    st.write(f"**Found {len(paused_ads)} paused ads**")
                    
                    # Selection
                    ads_to_enable = st.multiselect(
                        "Select ads to enable",
                        options=paused_ads['ad_id'].tolist(),
                        format_func=lambda x: format_headlines(
                            paused_ads[paused_ads['ad_id'] == x]['headlines'].iloc[0]
                        ),
                        key="ads_to_enable_multiselect"
                    )
                    
                    if ads_to_enable:
                        selected_ads = paused_ads[paused_ads['ad_id'].isin(ads_to_enable)]
                        
                        st.write(f"**{len(selected_ads)} ads selected**")
                        
                        with st.expander("👁️ Preview"):
                            preview_enable = selected_ads[[
                                'ad_id', 'headlines', 'campaign_name', 'health_score'
                            ]].copy()
                            preview_enable['headlines'] = preview_enable['headlines'].apply(format_headlines)
                            st.dataframe(preview_enable, use_container_width=True)
                        
                        # Execute
                        if st.button("▶️ Enable Selected Ads", type="primary", key="execute_enable_btn"):
                            from services.ad_management_service import AdManagementService, AdAction
                            
                            try:
                                ad_mgmt_service = AdManagementService(st.session_state.google_ads_client)
                                
                                actions = []
                                for _, row in selected_ads.iterrows():
                                    actions.append(AdAction(
                                        customer_id=selected_customer,
                                        ad_group_id=str(row['ad_group_id']),
                                        ad_id=str(row['ad_id']),
                                        ad_headlines=format_headlines(row['headlines']),
                                        campaign_name=row['campaign_name'],
                                        ad_group_name=row['ad_group_name'],
                                        current_status=row['ad_status'],
                                        reason="Manual enable from dashboard"
                                    ))
                                
                                with st.spinner(f"⏳ Enabling {len(actions)} ads..."):
                                    results = ad_mgmt_service.bulk_enable_ads(actions, dry_run=False)
                                
                                st.success(f"✅ {results['successful']} ads enabled successfully")
                                
                                if results['failed'] > 0:
                                    st.error(f"❌ {results['failed']} ads failed to enable")
                                    with st.expander("View Errors"):
                                        for error in results['errors']:
                                            st.write(f"- {error['headlines']}: {error['error']}")
                                
                                # Refresh data
                                st.cache_data.clear()
                                st.rerun()
                            
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                                logger.error(f"Error enabling ads: {e}", exc_info=True)
                    else:
                        st.info("Select one or more ads to enable from the list above")
                else:
                    st.info("✨ No paused ads found in the current selection")
            
            # ===== TAB 3: BULK ACTIONS =====
            with action_tab3:
                st.markdown("### 📊 Bulk Actions by Category")
                st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Acciones rápidas en masa por tipo de anuncio</p>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🧛 Pause All Vampires")
                    st.markdown("<p style='color: rgba(245,87,108,0.7); font-size: 0.85rem;'>Anuncios con alto gasto y 0 conversiones</p>", unsafe_allow_html=True)
                    
                    vampires = ad_health_service.get_vampire_ads(df_filtered)
                    vampires_enabled = vampires[vampires['ad_status'] == 'ENABLED'] if not vampires.empty else pd.DataFrame()
                    
                    if not vampires_enabled.empty:
                        st.metric("Vampire Ads Found", len(vampires_enabled))
                        st.metric("Total Wasted Spend", f"${vampires_enabled['spend'].sum():.2f}")
                        
                        with st.expander("👁️ View Vampires"):
                            vampire_preview = vampires_enabled[['headlines', 'spend', 'clicks', 'conversions']].head(5).copy()
                            vampire_preview['headlines'] = vampire_preview['headlines'].apply(format_headlines)
                            st.dataframe(vampire_preview, use_container_width=True)
                        
                        if st.button("⏸️ Pause All Vampires", key="pause_vampires_btn", use_container_width=True):
                            from services.ad_management_service import AdManagementService, AdAction
                            
                            ad_mgmt_service = AdManagementService(st.session_state.google_ads_client)
                            
                            actions = []
                            for _, row in vampires_enabled.iterrows():
                                actions.append(AdAction(
                                    customer_id=selected_customer,
                                    ad_group_id=str(row['ad_group_id']),
                                    ad_id=str(row['ad_id']),
                                    ad_headlines=format_headlines(row['headlines']),
                                    campaign_name=row['campaign_name'],
                                    ad_group_name=row['ad_group_name'],
                                    current_status=row['ad_status'],
                                    reason="Vampire ad: high spend, 0 conversions"
                                ))
                            
                            with st.spinner("Pausing vampire ads..."):
                                results = ad_mgmt_service.bulk_pause_ads(actions, dry_run=False)
                            
                            st.success(f"✅ {results['successful']} vampire ads paused")
                            
                            if results['failed'] > 0:
                                st.error(f"❌ {results['failed']} failed")
                            
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        st.success("✨ No vampire ads found - Great!")
                
                with col2:
                    st.markdown("#### ⚠️ Pause Policy Issues")
                    st.markdown("<p style='color: rgba(245,87,108,0.7); font-size: 0.85rem;'>Anuncios rechazados por políticas de Google</p>", unsafe_allow_html=True)
                    
                    policy_issues = ad_health_service.get_policy_issues(df_filtered)
                    policy_enabled = policy_issues[
                        (policy_issues['ad_status'] == 'ENABLED') &
                        (policy_issues['approval_status'] == 'DISAPPROVED')
                    ] if not policy_issues.empty else pd.DataFrame()
                    
                    if not policy_enabled.empty:
                        st.metric("Disapproved Ads Active", len(policy_enabled))
                        st.metric("Total Spend", f"${policy_enabled['spend'].sum():.2f}")
                        
                        with st.expander("👁️ View Policy Issues"):
                            policy_preview = policy_enabled[['headlines', 'approval_status', 'spend']].head(5).copy()
                            policy_preview['headlines'] = policy_preview['headlines'].apply(format_headlines)
                            st.dataframe(policy_preview, use_container_width=True)
                        
                        if st.button("⏸️ Pause Disapproved Ads", key="pause_policy_btn", use_container_width=True):
                            from services.ad_management_service import AdManagementService, AdAction
                            
                            ad_mgmt_service = AdManagementService(st.session_state.google_ads_client)
                            
                            actions = []
                            for _, row in policy_enabled.iterrows():
                                actions.append(AdAction(
                                    customer_id=selected_customer,
                                    ad_group_id=str(row['ad_group_id']),
                                    ad_id=str(row['ad_id']),
                                    ad_headlines=format_headlines(row['headlines']),
                                    campaign_name=row['campaign_name'],
                                    ad_group_name=row['ad_group_name'],
                                    current_status=row['ad_status'],
                                    reason="Disapproved by policy"
                                ))
                            
                            with st.spinner("Pausing disapproved ads..."):
                                results = ad_mgmt_service.bulk_pause_ads(actions, dry_run=False)
                            
                            st.success(f"✅ {results['successful']} disapproved ads paused")
                            
                            if results['failed'] > 0:
                                st.error(f"❌ {results['failed']} failed")
                            
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        st.success("✨ No policy issues found - Perfect!")
        
        else:
            st.info("📊 No ads available for management actions with current filters")
    
    except Exception as e:
        logger.error(f"Error in ad health dashboard: {e}", exc_info=True)
        st.error(f"❌ Error loading data: {str(e)}")

if __name__ == "__main__":
    main()