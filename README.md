# Google Ads Dashboard

A comprehensive Streamlit-based dashboard for monitoring and managing Google Ads campaigns, built with real-time data visualization, advanced analytics, and intelligent alerting.

## Features

### 📊 **Dashboard Overview**
- Real-time KPI monitoring (Spend, Impressions, Clicks, CTR, Conversions)
- Performance trend visualization
- Top-performing campaigns analysis
- Active alerts and budget overview
- Quick action buttons for common tasks

### 💰 **Billing & Budget Management**
- Comprehensive spend tracking and analysis
- Budget vs. actual spend visualization
- Budget utilization monitoring with alerts
- Daily and cumulative spend trends
- Budget recommendations and insights
- Export capabilities for financial reporting

### 🎯 **Campaign Performance**
- Detailed campaign performance analysis
- Interactive scatter plots and comparison charts
- Campaign filtering and sorting options
- Performance insights and optimization opportunities
- Underperforming campaign identification
- Campaign statistics and trends

### 📈 **Advanced Reporting**
- Custom report builder with flexible configuration
- Multiple visualization types (line, bar, scatter, pie, heatmap, funnel)
- Predefined report templates
- Data export options (CSV, JSON)
- Advanced analytics (trend analysis, anomaly detection, forecasting)
- Custom GAQL query builder

### 🚨 **Intelligent Alerts**
- Real-time alert monitoring and management
- Customizable alert rules and conditions
- Multiple alert types (budget, performance, status, anomaly)
- Alert history and trend analysis
- Campaign health monitoring
- Notification management

### ⚙️ **Settings & Configuration**
- Google Ads API configuration and OAuth setup
- Account and security settings
- Dashboard preferences and customization
- Notification settings (email, browser, Slack)
- Advanced settings (caching, rate limiting, logging)
- Data export/import capabilities

## Deployment

### Vercel Deployment (Recommended for Production)

This project is optimized for deployment on Vercel with the following configuration:

#### Prerequisites
- Vercel account (Pro recommended for better performance)
- GitHub repository
- Google Ads API credentials

#### Step-by-Step Deployment

1. **Prepare the Repository:**
   ```bash
   # Clone and push to your GitHub repository
   git clone https://github.com/saltbalente/googleadsapi
   cd googleadsapi
   git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Configure Environment Variables:**
   - Copy `.env.example` to create your environment configuration
   - In Vercel dashboard, add these environment variables:
     ```
     GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
     GOOGLE_ADS_CLIENT_ID=your_client_id
     GOOGLE_ADS_CLIENT_SECRET=your_client_secret
     GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
     SECRET_KEY=your_secret_key
     VERCEL_ENV=production
     ```

3. **Deploy to Vercel:**
   - Connect your GitHub repository to Vercel
   - Vercel will automatically detect the `vercel.json` configuration
   - The build process will install dependencies from `requirements.txt`
   - Your app will be available at `https://your-app-name.vercel.app`

#### Vercel Configuration

The project includes a `vercel.json` file with optimized settings:
- Python runtime configuration
- 5-minute function timeout (suitable for API operations)
- Proper routing for Streamlit applications

#### Important Considerations for Vercel

1. **Stateless Architecture:** Vercel functions are stateless, so local caching is limited
2. **Cold Starts:** First requests may be slower due to function initialization
3. **File Storage:** Use external storage for persistent data (consider Supabase or AWS S3)
4. **Database:** For production, migrate from SQLite to PostgreSQL (Supabase recommended)

#### Alternative Deployment Options

**Streamlit Cloud (Easiest):**
```bash
# Simply connect your GitHub repo to Streamlit Cloud
# Add secrets in the Streamlit Cloud dashboard
```

**Railway:**
```bash
# Connect GitHub repo to Railway
# Add environment variables in Railway dashboard
```

**Render:**
```bash
# Connect GitHub repo to Render
# Configure build and start commands
```

### Local Development

### Prerequisites
- Python 3.8 or higher
- Google Ads API access
- Google Ads Developer Token

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd dashboard-api-googleads
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Google Ads API:**
   - Copy `config/google-ads.yaml` and update with your credentials:
     - Developer Token
     - Client ID and Client Secret
     - Refresh Token
   - Add your customer account IDs to `config/accounts.txt`

4. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```

5. **Access the dashboard:**
   Open your browser and navigate to `http://localhost:8501`

## Configuration

### Google Ads API Setup

1. **Get API Access:**
   - Apply for Google Ads API access at [Google Ads API](https://developers.google.com/google-ads/api)
   - Obtain your Developer Token

2. **Create OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Ads API
   - Create OAuth 2.0 credentials (Desktop Application)
   - Download the credentials JSON file

3. **Generate Refresh Token:**
   - Use the OAuth credentials to generate a refresh token
   - You can use the Google Ads API authentication flow or tools like `google-ads-auth`

4. **Update Configuration:**
   ```yaml
   # config/google-ads.yaml
   developer_token: "YOUR_DEVELOPER_TOKEN"
   client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com"
   client_secret: "YOUR_CLIENT_SECRET"
   refresh_token: "YOUR_REFRESH_TOKEN"
   ```

5. **Add Account IDs:**
   ```
   # config/accounts.txt
   1234567890  # Your Google Ads Customer ID
   ```

### Configuration Files

- **`config/google-ads.yaml`**: Google Ads API credentials and settings
- **`config/budgets.yaml`**: Budget thresholds, alerts, and templates
- **`config/rules.yaml`**: Alert rules and conditions
- **`config/accounts.txt`**: Customer account IDs

## Project Structure

```
dashboard-api-googleads/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── config/               # Configuration files
│   ├── google-ads.yaml   # API credentials
│   ├── budgets.yaml      # Budget configuration
│   ├── rules.yaml        # Alert rules
│   └── accounts.txt      # Account IDs
├── core/                 # Core modules
│   ├── __init__.py
│   ├── auth.py          # Authentication
│   ├── client.py        # Google Ads client
│   └── config.py        # Configuration management
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── cache.py         # Caching utilities
│   ├── rate_limit.py    # Rate limiting
│   ├── logger.py        # Logging utilities
│   └── formatters.py    # Data formatters
├── services/             # Business services
│   ├── __init__.py
│   ├── billing_service.py    # Billing operations
│   ├── campaign_service.py   # Campaign operations
│   ├── report_service.py     # Reporting operations
│   └── alert_service.py      # Alert management
└── pages/                # Streamlit pages
    ├── 1_overview.py     # Dashboard overview
    ├── 2_billing.py      # Billing page
    ├── 3_campaigns.py    # Campaigns page
    ├── 4_reports.py      # Reports page
    ├── 5_alerts.py       # Alerts page
    └── 6_settings.py     # Settings page
```

## Features in Detail

### Authentication & Security
- OAuth 2.0 integration with Google Ads API
- Secure credential management
- Session-based authentication
- API key validation and testing

### Performance & Scalability
- Intelligent caching with TTL support
- Rate limiting to respect API quotas
- Adaptive rate limiting based on API responses
- Efficient data processing and visualization

### Data Visualization
- Interactive charts using Plotly and Altair
- Real-time data updates
- Responsive design for all screen sizes
- Export capabilities for all visualizations

### Alert System
- Real-time monitoring of campaign performance
- Customizable alert rules and thresholds
- Multiple notification channels
- Alert history and trend analysis
- Automatic alert resolution

### Reporting & Analytics
- Custom report builder with drag-and-drop interface
- Predefined report templates
- Advanced analytics and forecasting
- Data export in multiple formats
- GAQL query builder for advanced users

## Troubleshooting

### Common Issues

1. **Authentication Errors:**
   - Verify your Google Ads API credentials
   - Check if your developer token is approved
   - Ensure refresh token is valid

2. **API Quota Exceeded:**
   - The dashboard includes rate limiting
   - Check your API usage in Google Cloud Console
   - Consider upgrading your API quota if needed

3. **No Data Displayed:**
   - Verify customer account IDs in `config/accounts.txt`
   - Check if accounts have sufficient data
   - Ensure date ranges are appropriate

4. **Performance Issues:**
   - Enable caching in configuration
   - Reduce date ranges for large accounts
   - Consider using data sampling for very large datasets

### Getting Help

1. Check the configuration files for proper setup
2. Review the Streamlit logs for error messages
3. Verify Google Ads API access and permissions
4. Ensure all dependencies are installed correctly

## Development

### Adding New Features

1. **New Pages:** Add to the `pages/` directory following the naming convention
2. **New Services:** Add business logic to the `services/` directory
3. **New Utilities:** Add helper functions to the `utils/` directory
4. **Configuration:** Update relevant YAML files for new settings

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for all functions and classes
- Include error handling and logging

### Testing
- Test with different Google Ads accounts
- Verify API rate limiting behavior
- Test alert rules and notifications
- Validate data export functionality

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support and questions:
- Check the troubleshooting section
- Review Google Ads API documentation
- Open an issue in the repository