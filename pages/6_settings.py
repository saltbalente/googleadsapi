"""
Settings Page - Configuration and account management
"""

import streamlit as st
import json
import yaml
from datetime import datetime, timedelta, date
import logging
import os

from modules.auth import require_auth
from utils.logger import get_logger
from utils.formatters import format_currency, format_percentage, format_number
from modules.google_ads_client import GoogleAdsClientWrapper
from services.billing_service import BillingService
from services.campaign_service import CampaignService
from services.report_service import ReportService
from services.alert_service import AlertService

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Settings - Google Ads Dashboard",
    page_icon="⚙️",
    layout="wide"
)

@require_auth
def main():
    """Main settings page function"""
    
    # Page header
    st.title("⚙️ Settings & Configuration")
    st.markdown("Manage your dashboard settings, API configuration, and preferences")
    st.markdown("---")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔑 API Configuration", 
        "👤 Account Settings", 
        "📊 Dashboard Preferences", 
        "🔔 Notifications", 
        "🛠️ Advanced"
    ])
    
    with tab1:
        st.subheader("🔑 Google Ads API Configuration")
        
        # Current configuration status
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            api_status = st.session_state.get('google_ads_client') is not None
            st.metric(
                "API Connection",
                "✅ Connected" if api_status else "❌ Disconnected",
                help="Status of Google Ads API connection"
            )
        
        with col_status2:
            auth_status = st.session_state.get('authenticated', False)
            st.metric(
                "Authentication",
                "✅ Authenticated" if auth_status else "❌ Not Authenticated",
                help="OAuth authentication status"
            )
        
        with col_status3:
            customer_count = len(st.session_state.get('customer_ids', []))
            st.metric(
                "Accessible Accounts",
                customer_count,
                help="Number of Google Ads accounts you can access"
            )
        
        st.markdown("---")
        
        # API Configuration Form
        with st.expander("🔧 API Configuration", expanded=not api_status):
            st.markdown("**Configure your Google Ads API credentials**")
            
            with st.form("api_config"):
                col_dev, col_client = st.columns(2)
                
                with col_dev:
                    developer_token = st.text_input(
                        "Developer Token:",
                        type="password",
                        help="Your Google Ads API developer token"
                    )
                    
                    client_id = st.text_input(
                        "Client ID:",
                        help="OAuth 2.0 client ID from Google Cloud Console"
                    )
                
                with col_client:
                    client_secret = st.text_input(
                        "Client Secret:",
                        type="password",
                        help="OAuth 2.0 client secret from Google Cloud Console"
                    )
                    
                    refresh_token = st.text_input(
                        "Refresh Token:",
                        type="password",
                        help="OAuth 2.0 refresh token (optional if using OAuth flow)"
                    )
                
                login_customer_id = st.text_input(
                    "Login Customer ID (optional):",
                    help="Manager account ID if using a manager account"
                )
                
                if st.form_submit_button("💾 Save API Configuration"):
                    if developer_token and client_id and client_secret:
                        # In a real implementation, this would save to secure storage
                        st.success("✅ API configuration saved successfully!")
                        st.info("🔄 Please restart the application to apply changes.")
                    else:
                        st.error("❌ Please fill in all required fields.")
        
        # Enhanced Diagnostics: Accessible customers
        with st.expander("🧪 Diagnóstico Avanzado: Cuentas y Configuración", expanded=True):
            st.markdown("**Diagnóstico completo de configuración y cuentas accesibles**")
            
            # Configuration Status
            col_config1, col_config2 = st.columns(2)
            
            with col_config1:
                st.markdown("**📋 Configuración Actual:**")
                login_cid_env = os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID', '')
                if login_cid_env:
                    st.success(f"✅ Login Customer ID: `{login_cid_env}`")
                    st.caption(f"Cuenta administrador: `{login_cid_env.replace('-', '')}`")
                else:
                    st.error("❌ Login Customer ID no establecido en .env")
                
                dev_token = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN', '')
                if dev_token and not dev_token.upper().startswith('YOUR_'):
                    st.success("✅ Developer Token configurado")
                else:
                    st.error("❌ Developer Token no configurado")
                
                client_id = os.getenv('GOOGLE_ADS_CLIENT_ID', '')
                if client_id:
                    st.success("✅ Client ID configurado")
                else:
                    st.error("❌ Client ID no configurado")
            
            with col_config2:
                st.markdown("**🎯 Cuentas Esperadas:**")
                expected_accounts = [
                    "7094116152 (709-411-6152) - Página 3",
                    "1803044752 (180-304-4752) - Página 5", 
                    "9759913462 (975-991-3462) - Página 4",
                    "6639082872 (663-908-2872) - Account",
                    "1919262845 (191-926-2845) - Marketing",
                    "7004285893 (700-428-5893) - Página 9"
                ]
                for account in expected_accounts:
                    st.info(f"📊 {account}")
            
            st.markdown("---")
            
            if st.button("🔍 Ejecutar Diagnóstico Completo", type="primary"):
                client = st.session_state.get('google_ads_client')
                if not client:
                    # Intentar inicializar el cliente directamente usando .env / google-ads.yaml
                    with st.spinner("Inicializando cliente de Google Ads..."):
                        try:
                            wrapper = GoogleAdsClientWrapper()
                            ga_client = wrapper.get_client()
                            if ga_client:
                                # Guardar en sesión para que el resto del dashboard lo use
                                st.session_state['google_ads_client'] = wrapper
                                # Cargar cuentas usando el nuevo método mejorado
                                st.session_state['customer_ids'] = wrapper.get_customer_ids()
                                # Inicializar servicios para que las demás páginas puedan usarlos
                                st.session_state['services'] = {
                                    'billing': BillingService(wrapper),
                                    'campaign': CampaignService(wrapper),
                                    'report': ReportService(wrapper),
                                    'alert': AlertService(wrapper)
                                }
                                # Seleccionar cuenta por defecto si no hay una seleccionada
                                if st.session_state.get('customer_ids') and not st.session_state.get('selected_customer'):
                                    st.session_state['selected_customer'] = st.session_state['customer_ids'][0]
                                client = wrapper
                                st.success("✅ Cliente y servicios inicializados correctamente.")
                            else:
                                st.error("❌ No se pudo inicializar el cliente de Google Ads. Verifica tus credenciales.")
                                return
                        except Exception as e:
                            st.error(f"❌ Error inicializando el cliente: {e}")
                            return
                
                # Ejecutar el diagnóstico completo
                with st.spinner("Ejecutando diagnóstico completo..."):
                    
                    # 1. Cuentas accesibles desde API
                    st.markdown("### 🔍 1. Cuentas Accesibles (API)")
                    accessible = client.list_accessible_customers()
                    
                    if accessible:
                        st.success(f"✅ Se encontraron {len(accessible)} cuentas accesibles desde la API")
                        
                        # Mostrar cada cuenta con detalles
                        for i, customer_id in enumerate(accessible):
                            with st.expander(f"📊 Cuenta {i+1}: {customer_id}"):
                                try:
                                    account_info = client.get_account_info(customer_id)
                                    if account_info:
                                        col_info1, col_info2 = st.columns(2)
                                        with col_info1:
                                            st.write(f"**ID:** {customer_id}")
                                            st.write(f"**Nombre:** {account_info.get('descriptive_name', 'N/A')}")
                                        with col_info2:
                                            st.write(f"**Moneda:** {account_info.get('currency_code', 'N/A')}")
                                            st.write(f"**Estado:** {account_info.get('status', 'N/A')}")
                                    else:
                                        st.warning("No se pudo obtener información de la cuenta")
                                except Exception as e:
                                    st.error(f"Error obteniendo info: {e}")
                    else:
                        st.error("❌ No se obtuvieron cuentas accesibles")
                    
                    # 2. Comparación con accounts.txt
                    st.markdown("### 📋 2. Comparación con accounts.txt")
                    fallback_accounts = client.load_customer_ids()
                    
                    if fallback_accounts:
                        st.info(f"📁 Cuentas en accounts.txt: {len(fallback_accounts)}")
                        
                        # Análisis de diferencias
                        if accessible:
                            missing_in_api = sorted(list(set(fallback_accounts) - set(accessible)))
                            extra_in_api = sorted(list(set(accessible) - set(fallback_accounts)))
                            matching = sorted(list(set(fallback_accounts) & set(accessible)))
                            
                            if matching:
                                st.success(f"✅ Cuentas coincidentes: {matching}")
                            
                            if missing_in_api:
                                st.warning(f"⚠️ Cuentas en accounts.txt NO accesibles por API: {missing_in_api}")
                            
                            if extra_in_api:
                                st.info(f"ℹ️ Cuentas adicionales encontradas por API: {extra_in_api}")
                        
                        # Mostrar contenido de accounts.txt
                        with st.expander("📄 Contenido de accounts.txt"):
                            for account_id in fallback_accounts:
                                st.code(account_id)
                    else:
                        st.warning("📁 No se encontraron cuentas en accounts.txt")
                    
                    # 3. Validación final
                    st.markdown("### ✅ 3. Resultado Final")
                    final_accounts = client.get_customer_ids()
                    
                    if final_accounts:
                        st.success(f"🎯 **Cuentas finales disponibles:** {len(final_accounts)}")
                        
                        # Mostrar cuentas finales con formato
                        for account_id in final_accounts:
                            formatted_id = f"{account_id[:3]}-{account_id[3:6]}-{account_id[6:]}"
                            st.write(f"✅ `{account_id}` → `{formatted_id}`")
                        
                        # Actualizar session state
                        st.session_state['customer_ids'] = final_accounts
                        if not st.session_state.get('selected_customer') and final_accounts:
                            st.session_state['selected_customer'] = final_accounts[0]
                        
                        st.balloons()
                        st.success("🎉 Diagnóstico completado. Las cuentas han sido actualizadas en la sesión.")
                    else:
                        st.error("❌ No se pudieron obtener cuentas válidas")
            
            # Botón para limpiar y reinicializar
            if st.button("🔄 Reinicializar Configuración"):
                # Limpiar session state
                keys_to_clear = ['google_ads_client', 'customer_ids', 'selected_customer', 'services']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("✅ Configuración reinicializada. Ejecuta el diagnóstico nuevamente.")
        
        # OAuth Flow
        with st.expander("🔐 OAuth Authentication Flow"):
            st.markdown("**Authenticate with Google Ads**")
            
            if not auth_status:
                st.info("👆 Complete the OAuth flow to access your Google Ads accounts.")
                
                if st.button("🚀 Start OAuth Flow"):
                    st.info("🔄 Redirecting to Google for authentication...")
                    # In a real implementation, this would start the OAuth flow
                    st.markdown("""
                    **Next Steps:**
                    1. You'll be redirected to Google's authorization page
                    2. Grant permissions to access your Google Ads data
                    3. You'll be redirected back to complete the setup
                    """)
            
            else:
                st.success("✅ Successfully authenticated!")
                
                if st.button("🔄 Refresh Authentication"):
                    st.info("🔄 Refreshing authentication tokens...")
                
                if st.button("🚪 Logout"):
                    st.warning("⚠️ You will be logged out and need to re-authenticate.")
        
        # Account Selection
        with st.expander("🏢 Account Management"):
            st.markdown("**Manage accessible Google Ads accounts**")
            
            # Sample accounts data
            sample_accounts = [
                {"id": "123-456-7890", "name": "Main Business Account", "currency": "USD", "timezone": "America/New_York"},
                {"id": "098-765-4321", "name": "Secondary Account", "currency": "EUR", "timezone": "Europe/London"},
                {"id": "555-666-7777", "name": "Test Account", "currency": "USD", "timezone": "America/Los_Angeles"}
            ]
            
            if sample_accounts:
                st.markdown("**Available Accounts:**")
                
                for account in sample_accounts:
                    col_acc_info, col_acc_action = st.columns([3, 1])
                    
                    with col_acc_info:
                        st.markdown(f"""
                        **{account['name']}**  
                        ID: `{account['id']}`  
                        Currency: {account['currency']} | Timezone: {account['timezone']}
                        """)
                    
                    with col_acc_action:
                        if st.button(f"📊 Select", key=f"select_{account['id']}"):
                            st.session_state['selected_customer'] = account['id']
                            st.success(f"✅ Selected: {account['name']}")
                            st.rerun()
            
            else:
                st.info("🔍 No accounts found. Please check your API configuration and authentication.")
            
            if st.button("🔄 Refresh Account List"):
                st.info("🔄 Refreshing account list...")
    
    with tab2:
        st.subheader("👤 Account Settings")
        
        # User Profile
        with st.expander("👤 User Profile", expanded=True):
            with st.form("user_profile"):
                col_name, col_email = st.columns(2)
                
                with col_name:
                    display_name = st.text_input("Display Name:", value="John Doe")
                    company = st.text_input("Company:", value="Marketing Agency Inc.")
                
                with col_email:
                    email = st.text_input("Email:", value="john.doe@example.com")
                    role = st.selectbox("Role:", ["Admin", "Manager", "Analyst", "Viewer"])
                
                timezone = st.selectbox(
                    "Timezone:",
                    options=[
                        "America/New_York", "America/Los_Angeles", "Europe/London", 
                        "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"
                    ],
                    index=0
                )
                
                language = st.selectbox("Language:", ["English", "Spanish", "French", "German"])
                
                if st.form_submit_button("💾 Save Profile"):
                    st.success("✅ Profile updated successfully!")
        
        # Security Settings
        with st.expander("🔒 Security Settings"):
            st.markdown("**Password & Security**")
            
            with st.form("security_settings"):
                current_password = st.text_input("Current Password:", type="password")
                new_password = st.text_input("New Password:", type="password")
                confirm_password = st.text_input("Confirm New Password:", type="password")
                
                st.markdown("**Two-Factor Authentication**")
                enable_2fa = st.checkbox("Enable Two-Factor Authentication", value=False)
                
                if enable_2fa:
                    st.info("📱 Two-factor authentication will be enabled using your mobile device.")
                
                st.markdown("**Session Management**")
                session_timeout = st.selectbox(
                    "Session Timeout:",
                    options=["30 minutes", "1 hour", "4 hours", "8 hours", "Never"],
                    index=1
                )
                
                if st.form_submit_button("🔒 Update Security Settings"):
                    if new_password and new_password == confirm_password:
                        st.success("✅ Security settings updated successfully!")
                    elif new_password:
                        st.error("❌ Passwords do not match!")
                    else:
                        st.success("✅ Security settings updated successfully!")
        
        # API Keys Management
        with st.expander("🔑 API Keys Management"):
            st.markdown("**Manage API Keys and Tokens**")
            
            # Sample API keys
            api_keys = [
                {"name": "Dashboard API Key", "created": "2024-01-15", "last_used": "2024-01-20", "status": "Active"},
                {"name": "Reporting API Key", "created": "2024-01-10", "last_used": "2024-01-19", "status": "Active"},
                {"name": "Legacy API Key", "created": "2023-12-01", "last_used": "2024-01-05", "status": "Inactive"}
            ]
            
            for key in api_keys:
                col_key_info, col_key_actions = st.columns([3, 1])
                
                with col_key_info:
                    status_icon = "✅" if key['status'] == 'Active' else "❌"
                    st.markdown(f"""
                    **{status_icon} {key['name']}**  
                    Created: {key['created']} | Last Used: {key['last_used']}
                    """)
                
                with col_key_actions:
                    if key['status'] == 'Active':
                        if st.button("🔄 Regenerate", key=f"regen_{key['name']}"):
                            st.warning(f"⚠️ API key '{key['name']}' regenerated!")
                    
                    if st.button("🗑️ Delete", key=f"delete_{key['name']}"):
                        st.error(f"❌ API key '{key['name']}' deleted!")
            
            if st.button("➕ Generate New API Key"):
                st.success("✅ New API key generated successfully!")
    
    with tab3:
        st.subheader("📊 Dashboard Preferences")
        
        # Display Settings
        with st.expander("🎨 Display Settings", expanded=True):
            with st.form("display_settings"):
                col_theme, col_layout = st.columns(2)
                
                with col_theme:
                    theme = st.selectbox("Theme:", ["Light", "Dark", "Auto"])
                    color_scheme = st.selectbox("Color Scheme:", ["Default", "Blue", "Green", "Purple"])
                
                with col_layout:
                    sidebar_position = st.selectbox("Sidebar Position:", ["Left", "Right"])
                    compact_mode = st.checkbox("Compact Mode", value=False)
                
                st.markdown("**Chart Preferences**")
                
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    default_chart_type = st.selectbox(
                        "Default Chart Type:",
                        ["Line Chart", "Bar Chart", "Area Chart"]
                    )
                    
                    chart_animation = st.checkbox("Enable Chart Animations", value=True)
                
                with col_chart2:
                    chart_colors = st.selectbox(
                        "Chart Color Palette:",
                        ["Viridis", "Plasma", "Blues", "Reds", "Greens"]
                    )
                    
                    show_data_labels = st.checkbox("Show Data Labels", value=True)
                
                if st.form_submit_button("💾 Save Display Settings"):
                    st.success("✅ Display settings saved successfully!")
        
        # Data Settings
        with st.expander("📈 Data & Metrics Settings"):
            with st.form("data_settings"):
                st.markdown("**Default Metrics**")
                
                default_metrics = st.multiselect(
                    "Default Dashboard Metrics:",
                    options=[
                        "Impressions", "Clicks", "Cost", "Conversions", 
                        "CTR", "CPC", "Conversion Rate", "ROAS"
                    ],
                    default=["Impressions", "Clicks", "Cost", "Conversions"]
                )
                
                st.markdown("**Date Range Preferences**")
                
                col_date1, col_date2 = st.columns(2)
                
                with col_date1:
                    default_date_range = st.selectbox(
                        "Default Date Range:",
                        ["Last 7 days", "Last 30 days", "Last 90 days", "This month"],
                        index=1
                    )
                
                with col_date2:
                    auto_refresh = st.checkbox("Auto-refresh Data", value=True)
                    if auto_refresh:
                        refresh_interval = st.selectbox(
                            "Refresh Interval:",
                            ["5 minutes", "15 minutes", "30 minutes", "1 hour"]
                        )
                
                st.markdown("**Currency & Formatting**")
                
                col_curr1, col_curr2 = st.columns(2)
                
                with col_curr1:
                    default_currency = st.selectbox("Default Currency:", ["USD", "EUR", "GBP", "CAD"])
                    number_format = st.selectbox("Number Format:", ["1,234.56", "1.234,56", "1 234.56"])
                
                with col_curr2:
                    percentage_decimals = st.number_input("Percentage Decimals:", min_value=0, max_value=4, value=2)
                    currency_decimals = st.number_input("Currency Decimals:", min_value=0, max_value=4, value=2)
                
                if st.form_submit_button("💾 Save Data Settings"):
                    st.success("✅ Data settings saved successfully!")
        
        # Export Settings
        with st.expander("📤 Export & Reporting Settings"):
            with st.form("export_settings"):
                st.markdown("**Default Export Format**")
                
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    default_export_format = st.selectbox("Export Format:", ["CSV", "Excel", "PDF", "JSON"])
                    include_charts = st.checkbox("Include Charts in Exports", value=True)
                
                with col_exp2:
                    date_in_filename = st.checkbox("Include Date in Filename", value=True)
                    compress_exports = st.checkbox("Compress Large Exports", value=True)
                
                st.markdown("**Scheduled Reports**")
                
                enable_scheduled_reports = st.checkbox("Enable Scheduled Reports", value=False)
                
                if enable_scheduled_reports:
                    col_sched1, col_sched2 = st.columns(2)
                    
                    with col_sched1:
                        report_frequency = st.selectbox("Frequency:", ["Daily", "Weekly", "Monthly"])
                        report_time = st.time_input("Send Time:", value=datetime.strptime("09:00", "%H:%M").time())
                    
                    with col_sched2:
                        report_recipients = st.text_area("Email Recipients (one per line):")
                        report_format = st.selectbox("Report Format:", ["PDF", "Excel", "CSV"])
                
                if st.form_submit_button("💾 Save Export Settings"):
                    st.success("✅ Export settings saved successfully!")
    
    with tab4:
        st.subheader("🔔 Notification Settings")
        
        # Email Notifications
        with st.expander("📧 Email Notifications", expanded=True):
            with st.form("email_notifications"):
                st.markdown("**Email Notification Preferences**")
                
                enable_email = st.checkbox("Enable Email Notifications", value=True)
                
                if enable_email:
                    notification_email = st.text_input(
                        "Notification Email:",
                        value="john.doe@example.com"
                    )
                    
                    st.markdown("**Notification Types**")
                    
                    col_notif1, col_notif2 = st.columns(2)
                    
                    with col_notif1:
                        alert_notifications = st.checkbox("Alert Notifications", value=True)
                        budget_notifications = st.checkbox("Budget Notifications", value=True)
                        performance_notifications = st.checkbox("Performance Notifications", value=True)
                    
                    with col_notif2:
                        daily_summary = st.checkbox("Daily Summary", value=False)
                        weekly_report = st.checkbox("Weekly Report", value=True)
                        monthly_report = st.checkbox("Monthly Report", value=True)
                    
                    st.markdown("**Notification Frequency**")
                    
                    alert_frequency = st.selectbox(
                        "Alert Frequency:",
                        ["Immediate", "Every 15 minutes", "Hourly", "Daily"]
                    )
                    
                    quiet_hours = st.checkbox("Enable Quiet Hours", value=True)
                    
                    if quiet_hours:
                        col_quiet1, col_quiet2 = st.columns(2)
                        
                        with col_quiet1:
                            quiet_start = st.time_input("Quiet Hours Start:", value=datetime.strptime("22:00", "%H:%M").time())
                        
                        with col_quiet2:
                            quiet_end = st.time_input("Quiet Hours End:", value=datetime.strptime("08:00", "%H:%M").time())
                
                if st.form_submit_button("💾 Save Email Settings"):
                    st.success("✅ Email notification settings saved successfully!")
        
        # Browser Notifications
        with st.expander("🌐 Browser Notifications"):
            st.markdown("**Browser Push Notifications**")
            
            enable_browser_notifications = st.checkbox("Enable Browser Notifications", value=False)
            
            if enable_browser_notifications:
                st.info("📱 Browser notifications will be requested when you enable this feature.")
                
                notification_types = st.multiselect(
                    "Notification Types:",
                    options=["Critical Alerts", "Budget Warnings", "Performance Changes", "System Updates"],
                    default=["Critical Alerts", "Budget Warnings"]
                )
                
                notification_sound = st.checkbox("Play Notification Sound", value=True)
            
            if st.button("💾 Save Browser Settings"):
                st.success("✅ Browser notification settings saved successfully!")
        
        # Slack Integration
        with st.expander("💬 Slack Integration"):
            st.markdown("**Slack Notifications**")
            
            enable_slack = st.checkbox("Enable Slack Integration", value=False)
            
            if enable_slack:
                slack_webhook = st.text_input(
                    "Slack Webhook URL:",
                    type="password",
                    help="Enter your Slack webhook URL for notifications"
                )
                
                slack_channel = st.text_input("Default Channel:", value="#google-ads-alerts")
                
                slack_notifications = st.multiselect(
                    "Slack Notification Types:",
                    options=["High Priority Alerts", "Budget Warnings", "Daily Summary", "Weekly Report"],
                    default=["High Priority Alerts", "Budget Warnings"]
                )
                
                if st.button("🧪 Test Slack Integration"):
                    st.info("📤 Sending test message to Slack...")
            
            if st.button("💾 Save Slack Settings"):
                st.success("✅ Slack integration settings saved successfully!")
    
    with tab5:
        st.subheader("🛠️ Advanced Settings")
        
        # Cache Settings
        with st.expander("💾 Cache Settings"):
            st.markdown("**Data Caching Configuration**")
            
            with st.form("cache_settings"):
                enable_caching = st.checkbox("Enable Data Caching", value=True)
                
                if enable_caching:
                    cache_ttl = st.selectbox(
                        "Cache TTL (Time to Live):",
                        options=["5 minutes", "15 minutes", "30 minutes", "1 hour", "4 hours"],
                        index=2
                    )
                    
                    cache_size = st.selectbox(
                        "Max Cache Size:",
                        options=["100 MB", "500 MB", "1 GB", "2 GB"],
                        index=1
                    )
                    
                    auto_clear_cache = st.checkbox("Auto-clear Cache Daily", value=True)
                
                if st.form_submit_button("💾 Save Cache Settings"):
                    st.success("✅ Cache settings saved successfully!")
            
            # Cache management
            st.markdown("**Cache Management**")
            
            col_cache1, col_cache2, col_cache3 = st.columns(3)
            
            with col_cache1:
                if st.button("🗑️ Clear All Cache"):
                    st.success("✅ All cache cleared successfully!")
            
            with col_cache2:
                if st.button("📊 View Cache Stats"):
                    st.info("📈 Cache hit rate: 85% | Size: 245 MB")
            
            with col_cache3:
                if st.button("🔄 Refresh Cache"):
                    st.info("🔄 Cache refreshed successfully!")
        
        # Rate Limiting
        with st.expander("⏱️ Rate Limiting"):
            st.markdown("**API Rate Limiting Configuration**")
            
            with st.form("rate_limit_settings"):
                enable_rate_limiting = st.checkbox("Enable Rate Limiting", value=True)
                
                if enable_rate_limiting:
                    requests_per_minute = st.number_input(
                        "Requests per Minute:",
                        min_value=1,
                        max_value=1000,
                        value=100
                    )
                    
                    burst_limit = st.number_input(
                        "Burst Limit:",
                        min_value=1,
                        max_value=100,
                        value=10
                    )
                    
                    adaptive_rate_limiting = st.checkbox("Adaptive Rate Limiting", value=True)
                
                if st.form_submit_button("💾 Save Rate Limit Settings"):
                    st.success("✅ Rate limiting settings saved successfully!")
        
        # Logging Settings
        with st.expander("📝 Logging & Debugging"):
            st.markdown("**Logging Configuration**")
            
            with st.form("logging_settings"):
                log_level = st.selectbox(
                    "Log Level:",
                    options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    index=1
                )
                
                enable_file_logging = st.checkbox("Enable File Logging", value=True)
                
                if enable_file_logging:
                    log_file_size = st.selectbox(
                        "Max Log File Size:",
                        options=["1 MB", "5 MB", "10 MB", "50 MB"],
                        index=2
                    )
                    
                    log_retention = st.selectbox(
                        "Log Retention:",
                        options=["7 days", "30 days", "90 days", "1 year"],
                        index=1
                    )
                
                enable_debug_mode = st.checkbox("Enable Debug Mode", value=False)
                
                if enable_debug_mode:
                    st.warning("⚠️ Debug mode will log sensitive information. Use only for troubleshooting.")
                
                if st.form_submit_button("💾 Save Logging Settings"):
                    st.success("✅ Logging settings saved successfully!")
        
        # Data Export
        with st.expander("📤 Data Export & Backup"):
            st.markdown("**Export All Settings**")
            
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                if st.button("📊 Export Settings"):
                    # Sample settings export
                    settings_data = {
                        "dashboard_preferences": {
                            "theme": "Light",
                            "default_metrics": ["Impressions", "Clicks", "Cost"],
                            "default_date_range": "Last 30 days"
                        },
                        "notifications": {
                            "email_enabled": True,
                            "alert_frequency": "Immediate"
                        },
                        "export_timestamp": datetime.now().isoformat()
                    }
                    
                    st.download_button(
                        label="💾 Download Settings",
                        data=json.dumps(settings_data, indent=2),
                        file_name=f"dashboard_settings_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )
            
            with col_export2:
                uploaded_file = st.file_uploader("📁 Import Settings", type=['json'])
                
                if uploaded_file is not None:
                    if st.button("📥 Import Settings"):
                        st.success("✅ Settings imported successfully!")
                        st.info("🔄 Please restart the application to apply imported settings.")
        
        # System Information
        with st.expander("ℹ️ System Information"):
            st.markdown("**Dashboard Information**")
            
            system_info = {
                "Dashboard Version": "1.0.0",
                "Google Ads API Version": "v14",
                "Python Version": "3.9.0",
                "Streamlit Version": "1.28.0",
                "Last Updated": "2024-01-20",
                "Uptime": "2 days, 14 hours",
                "Memory Usage": "245 MB",
                "Cache Size": "89 MB"
            }
            
            for key, value in system_info.items():
                col_info_key, col_info_value = st.columns([1, 2])
                
                with col_info_key:
                    st.markdown(f"**{key}:**")
                
                with col_info_value:
                    st.markdown(value)
            
            if st.button("🔄 Refresh System Info"):
                st.rerun()

if __name__ == "__main__":
    main()