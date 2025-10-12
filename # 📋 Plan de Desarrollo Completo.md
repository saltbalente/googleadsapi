# 📋 Plan de Desarrollo Completo
## Google Ads Multi-Account Dashboard (Flask + React)

**Preparado para:** Equipo de Desarrollo  
**Solicitado por:** Edwar Alexander Bechara (@saltbalente)  
**Empresa:** Marketing Creativo Innovador  
**Fecha:** 2025-10-09  
**Versión:** 1.0

---

## 🎯 Objetivo del Proyecto

Desarrollar una aplicación web completa para gestionar y monitorear **40+ cuentas de Google Ads** de manera centralizada, automatizando la supervisión de facturación, rendimiento de campañas y generación de reportes.

---

## 📊 Especificaciones Técnicas

### **Stack Tecnológico**

#### **Backend**
```
- Lenguaje: Python 3.10+
- Framework: Flask 3.0+
- API: Google Ads API v15
- Base de datos: PostgreSQL 15+ (producción) / SQLite (desarrollo)
- Cache: Redis 7.0+
- Task Queue: Celery 5.3+ con Redis broker
- Autenticación: JWT (JSON Web Tokens)
- ORM: SQLAlchemy 2.0+
```

#### **Frontend**
```
- Framework: React 18+
- UI Library: Material-UI (MUI) v5 o Ant Design v5
- State Management: Redux Toolkit o Zustand
- Routing: React Router v6
- Charts: Recharts o Chart.js
- HTTP Client: Axios
- Build Tool: Vite
- Tipo de código: TypeScript
```

#### **DevOps & Infraestructura**
```
- Containerización: Docker + Docker Compose
- Servidor web: Nginx (reverse proxy)
- Process Manager: Gunicorn (backend)
- Logs: Python logging + archivo rotativo
- Monitoreo: Basic health checks
- Variables de entorno: python-dotenv
```

---

## 🏗️ Arquitectura del Sistema

### **Diagrama de Componentes**

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Dashboard   │  │  Facturación │  │   Campañas   │  │
│  │    View      │  │     View     │  │     View     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Alertas    │  │   Reportes   │  │    Config    │  │
│  │    View      │  │     View     │  │     View     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (HTTPS)
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 BACKEND (Flask)                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              API REST Endpoints                   │  │
│  │  /api/auth  /api/accounts  /api/campaigns        │  │
│  │  /api/billing  /api/reports  /api/alerts         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Auth Service │  │Google Ads SDK│  │Cache Manager │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Celery Background Tasks                 │  │
│  │  - Sincronización de cuentas cada 1 hora        │  │
│  │  - Verificación de facturación cada 6 horas     │  │
│  │  - Generación de reportes diarios               │  │
│  │  - Envío de alertas por email                   │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌───────────────┐            ┌────────────────┐
│  PostgreSQL   │            │     Redis      │
│   Database    │            │  Cache/Queue   │
└───────────────┘            └────────────────┘
        │
        │
        ▼
┌──────────────────────────────────────┐
│      Google Ads API                  │
│  - 40+ Customer Accounts             │
│  - Real-time data queries            │
│  - Rate limiting: 15K ops/day (test) │
└──────────────────────────────────────┘
```

---

## 📦 Estructura del Proyecto

```
google-ads-dashboard/
│
├── backend/                          # Backend Flask
│   ├── app/
│   │   ├── __init__.py              # Inicialización de Flask
│   │   ├── config.py                # Configuración (dev, prod, test)
│   │   ├── models/                  # Modelos SQLAlchemy
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # Usuario del sistema
│   │   │   ├── account.py          # Cuenta de Google Ads
│   │   │   ├── campaign.py         # Campaña
│   │   │   ├── billing.py          # Información de facturación
│   │   │   ├── alert.py            # Alertas del sistema
│   │   │   └── report.py           # Reportes generados
│   │   │
│   │   ├── services/                # Lógica de negocio
│   │   │   ├── __init__.py
│   │   │   ├── google_ads_service.py    # Comunicación con Google Ads API
│   │   │   ├── auth_service.py          # Autenticación OAuth/JWT
│   │   │   ├── billing_service.py       # Gestión de facturación
│   │   │   ├── campaign_service.py      # Gestión de campañas
│   │   │   ├── alert_service.py         # Sistema de alertas
│   │   │   ├── report_service.py        # Generación de reportes
│   │   │   └── cache_service.py         # Gestión de caché Redis
│   │   │
│   │   ├── api/                     # Endpoints REST
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # /api/auth/*
│   │   │   ├── accounts.py         # /api/accounts/*
│   │   │   ├── campaigns.py        # /api/campaigns/*
│   │   │   ├── billing.py          # /api/billing/*
│   │   │   ├── reports.py          # /api/reports/*
│   │   │   ├── alerts.py           # /api/alerts/*
│   │   │   └── dashboard.py        # /api/dashboard/*
│   │   │
│   │   ├── tasks/                   # Tareas Celery
│   │   │   ├── __init__.py
│   │   │   ├── sync_tasks.py       # Sincronización de datos
│   │   │   ├── billing_tasks.py    # Verificación de facturación
│   │   │   ├── report_tasks.py     # Generación de reportes
│   │   │   └── alert_tasks.py      # Envío de alertas
│   │   │
│   │   ├── utils/                   # Utilidades
│   │   │   ├── __init__.py
│   │   │   ├── decorators.py       # Decoradores personalizados
│   │   │   ├── validators.py       # Validadores de datos
│   │   │   ├── helpers.py          # Funciones auxiliares
│   │   │   └── constants.py        # Constantes del sistema
│   │   │
│   │   └── extensions.py            # Extensiones Flask (db, jwt, celery)
│   │
│   ├── migrations/                  # Migraciones Alembic
│   ├── tests/                       # Tests unitarios e integración
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   │
│   ├── config/
│   │   ├── google-ads.yaml         # Config Google Ads API
│   │   └── client_secret.json      # OAuth credentials
│   │
│   ├── requirements.txt             # Dependencias Python
│   ├── .env.example                # Ejemplo variables de entorno
│   ├── Dockerfile                  # Docker backend
│   └── wsgi.py                     # Entry point WSGI
│
├── frontend/                        # Frontend React
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── components/              # Componentes reutilizables
│   │   │   ├── common/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   └── DataTable.tsx
│   │   │   │
│   │   │   ├── accounts/
│   │   │   │   ├── AccountList.tsx
│   │   │   │   ├── AccountCard.tsx
│   │   │   │   └── AccountDetails.tsx
│   │   │   │
│   │   │   ├── campaigns/
│   │   │   │   ├── CampaignList.tsx
│   │   │   │   ├── CampaignChart.tsx
│   │   │   │   └── CampaignMetrics.tsx
│   │   │   │
│   │   │   ├── billing/
│   │   │   │   ├── BillingStatus.tsx
│   │   │   │   ├── BillingHistory.tsx
│   │   │   │   └── PaymentAlert.tsx
│   │   │   │
│   │   │   ├── reports/
│   │   │   │   ├── ReportGenerator.tsx
│   │   │   │   ├── ReportList.tsx
│   │   │   │   └── ReportViewer.tsx
│   │   │   │
│   │   │   └── charts/
│   │   │       ├── LineChart.tsx
│   │   │       ├── BarChart.tsx
│   │   │       ├── PieChart.tsx
│   │   │       └── MetricCard.tsx
│   │   │
│   │   ├── pages/                   # Páginas principales
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Accounts.tsx
│   │   │   ├── Campaigns.tsx
│   │   │   ├── Billing.tsx
│   │   │   ├── Reports.tsx
│   │   │   ├── Alerts.tsx
│   │   │   └── Settings.tsx
│   │   │
│   │   ├── services/                # Servicios API
│   │   │   ├── api.ts              # Configuración Axios
│   │   │   ├── authService.ts
│   │   │   ├── accountService.ts
│   │   │   ├── campaignService.ts
│   │   │   ├── billingService.ts
│   │   │   └── reportService.ts
│   │   │
│   │   ├── store/                   # Redux/Zustand store
│   │   │   ├── index.ts
│   │   │   ├── slices/
│   │   │   │   ├── authSlice.ts
│   │   │   │   ├── accountSlice.ts
│   │   │   │   ├── campaignSlice.ts
│   │   │   │   └── uiSlice.ts
│   │   │   └── hooks.ts
│   │   │
│   │   ├── hooks/                   # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useAccounts.ts
│   │   │   ├── useCampaigns.ts
│   │   │   └── useDebounce.ts
│   │   │
│   │   ├── utils/                   # Utilidades frontend
│   │   │   ├── formatters.ts       # Formateo de datos
│   │   │   ├── validators.ts       # Validaciones
│   │   │   ├── constants.ts        # Constantes
│   │   │   └── helpers.ts          # Funciones auxiliares
│   │   │
│   │   ├── types/                   # TypeScript types
│   │   │   ├── account.ts
│   │   │   ├── campaign.ts
│   │   │   ├── billing.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── styles/                  # Estilos globales
│   │   │   ├── theme.ts            # Tema MUI/Ant Design
│   │   │   └── global.css
│   │   │
│   │   ├── App.tsx                 # Componente principal
│   │   ├── index.tsx               # Entry point
│   │   └── routes.tsx              # Definición de rutas
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── .env.example
│   └── Dockerfile                  # Docker frontend
│
├── docker-compose.yml               # Orquestación de servicios
├── .gitignore
├── README.md                        # Documentación del proyecto
└── docs/                            # Documentación adicional
    ├── API.md                      # Documentación de API
    ├── SETUP.md                    # Guía de instalación
    └── DEPLOYMENT.md               # Guía de despliegue
```

---

## 🔌 Especificación de API REST

### **Base URL**
```
Desarrollo: http://localhost:5000/api
Producción: https://api.tudominio.com/api
```

### **Autenticación**
```
Tipo: JWT Bearer Token
Header: Authorization: Bearer <token>
Expiración: 24 horas
Refresh: 7 días
```

---

### **Endpoints Detallados**

#### **1. Autenticación (`/api/auth`)**

```http
POST /api/auth/login
Request:
{
  "email": "string",
  "password": "string"
}
Response 200:
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "id": "number",
    "email": "string",
    "name": "string",
    "role": "admin|user"
  }
}
```

```http
POST /api/auth/refresh
Request:
{
  "refresh_token": "string"
}
Response 200:
{
  "access_token": "string"
}
```

```http
POST /api/auth/logout
Headers: Authorization: Bearer <token>
Response 204: No Content
```

---

#### **2. Cuentas de Google Ads (`/api/accounts`)**

```http
GET /api/accounts
Headers: Authorization: Bearer <token>
Query Parameters:
  - page: number (default: 1)
  - per_page: number (default: 20)
  - search: string (optional)
  - status: active|paused|all (default: all)
Response 200:
{
  "data": [
    {
      "id": "number",
      "customer_id": "string",
      "name": "string",
      "currency": "string",
      "timezone": "string",
      "status": "active|paused",
      "last_sync": "datetime",
      "metrics_30d": {
        "cost": "number",
        "impressions": "number",
        "clicks": "number",
        "conversions": "number"
      }
    }
  ],
  "pagination": {
    "page": "number",
    "per_page": "number",
    "total": "number",
    "pages": "number"
  }
}
```

```http
GET /api/accounts/{customer_id}
Headers: Authorization: Bearer <token>
Response 200:
{
  "id": "number",
  "customer_id": "string",
  "name": "string",
  "currency": "string",
  "timezone": "string",
  "status": "string",
  "billing_info": {
    "payments_account": "string",
    "billing_status": "string",
    "last_payment_date": "datetime"
  },
  "metrics": {
    "last_7_days": {...},
    "last_30_days": {...},
    "last_90_days": {...}
  }
}
```

```http
POST /api/accounts/sync
Headers: Authorization: Bearer <token>
Request:
{
  "customer_ids": ["string"] // opcional, si vacío sincroniza todas
}
Response 202:
{
  "task_id": "string",
  "message": "Synchronization started"
}
```

```http
GET /api/accounts/sync/{task_id}
Headers: Authorization: Bearer <token>
Response 200:
{
  "status": "pending|running|completed|failed",
  "progress": "number (0-100)",
  "result": {...} // si completed
}
```

---

#### **3. Campañas (`/api/campaigns`)**

```http
GET /api/campaigns
Headers: Authorization: Bearer <token>
Query Parameters:
  - customer_id: string (required)
  - date_range: last_7_days|last_30_days|last_90_days|custom
  - start_date: date (if custom)
  - end_date: date (if custom)
  - status: enabled|paused|removed|all
  - page: number
  - per_page: number
Response 200:
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "status": "string",
      "type": "SEARCH|DISPLAY|VIDEO|SHOPPING|PERFORMANCE_MAX",
      "budget": "number",
      "metrics": {
        "cost": "number",
        "impressions": "number",
        "clicks": "number",
        "conversions": "number",
        "ctr": "number",
        "avg_cpc": "number",
        "conversion_rate": "number"
      }
    }
  ],
  "summary": {
    "total_campaigns": "number",
    "total_cost": "number",
    "total_conversions": "number"
  }
}
```

```http
GET /api/campaigns/{campaign_id}
Headers: Authorization: Bearer <token>
Query Parameters:
  - customer_id: string (required)
  - date_range: string
Response 200:
{
  "id": "string",
  "name": "string",
  "status": "string",
  "type": "string",
  "budget": {...},
  "targeting": {...},
  "metrics": {...},
  "ad_groups": [...],
  "performance_chart": {
    "dates": ["string"],
    "cost": ["number"],
    "conversions": ["number"]
  }
}
```

---

#### **4. Facturación (`/api/billing`)**

```http
GET /api/billing/status
Headers: Authorization: Bearer <token>
Query Parameters:
  - customer_ids: string[] (optional, comma-separated)
Response 200:
{
  "data": [
    {
      "customer_id": "string",
      "account_name": "string",
      "billing_status": "active|suspended|pending",
      "payment_method": "string",
      "next_payment_date": "datetime",
      "current_balance": "number",
      "spending_limit": "number",
      "alert_level": "none|low|medium|high|critical"
    }
  ],
  "summary": {
    "total_accounts": "number",
    "accounts_with_issues": "number",
    "total_balance": "number"
  }
}
```

```http
GET /api/billing/history
Headers: Authorization: Bearer <token>
Query Parameters:
  - customer_id: string (required)
  - start_date: date
  - end_date: date
Response 200:
{
  "data": [
    {
      "date": "datetime",
      "amount": "number",
      "currency": "string",
      "status": "successful|failed|pending",
      "payment_method": "string",
      "invoice_id": "string"
    }
  ]
}
```

```http
POST /api/billing/alerts/configure
Headers: Authorization: Bearer <token>
Request:
{
  "customer_id": "string",
  "alert_threshold": "number",
  "notification_emails": ["string"],
  "alert_types": ["low_balance", "payment_failed", "budget_exceeded"]
}
Response 200:
{
  "message": "Alert configuration saved",
  "config": {...}
}
```

---

#### **5. Reportes (`/api/reports`)**

```http
GET /api/reports
Headers: Authorization: Bearer <token>
Query Parameters:
  - page: number
  - per_page: number
Response 200:
{
  "data": [
    {
      "id": "number",
      "name": "string",
      "type": "billing|performance|comprehensive",
      "created_at": "datetime",
      "created_by": "string",
      "period": "string",
      "status": "completed|processing|failed",
      "file_url": "string" // si completed
    }
  ]
}
```

```http
POST /api/reports/generate
Headers: Authorization: Bearer <token>
Request:
{
  "report_type": "billing|performance|comprehensive|custom",
  "customer_ids": ["string"],
  "date_range": {
    "start_date": "date",
    "end_date": "date"
  },
  "format": "pdf|excel|csv",
  "sections": ["overview", "campaigns", "billing", "recommendations"],
  "email_to": ["string"] // opcional
}
Response 202:
{
  "task_id": "string",
  "message": "Report generation started"
}
```

```http
GET /api/reports/{report_id}/download
Headers: Authorization: Bearer <token>
Response 200: File stream (PDF/Excel/CSV)
```

---

#### **6. Alertas (`/api/alerts`)**

```http
GET /api/alerts
Headers: Authorization: Bearer <token>
Query Parameters:
  - status: unread|read|all
  - severity: low|medium|high|critical
  - page: number
Response 200:
{
  "data": [
    {
      "id": "number",
      "type": "billing|performance|system",
      "severity": "string",
      "title": "string",
      "message": "string",
      "customer_id": "string",
      "customer_name": "string",
      "created_at": "datetime",
      "read": "boolean",
      "action_required": "boolean",
      "action_url": "string"
    }
  ],
  "summary": {
    "unread_count": "number",
    "critical_count": "number"
  }
}
```

```http
PATCH /api/alerts/{alert_id}/read
Headers: Authorization: Bearer <token>
Response 200:
{
  "message": "Alert marked as read"
}
```

```http
DELETE /api/alerts/{alert_id}
Headers: Authorization: Bearer <token>
Response 204: No Content
```

---

#### **7. Dashboard (`/api/dashboard`)**

```http
GET /api/dashboard/overview
Headers: Authorization: Bearer <token>
Query Parameters:
  - date_range: last_7_days|last_30_days|last_90_days
Response 200:
{
  "accounts": {
    "total": "number",
    "active": "number",
    "paused": "number",
    "with_issues": "number"
  },
  "spending": {
    "total": "number",
    "by_currency": {...},
    "trend": "number" // % change vs previous period
  },
  "performance": {
    "total_impressions": "number",
    "total_clicks": "number",
    "total_conversions": "number",
    "avg_ctr": "number",
    "avg_cpc": "number"
  },
  "alerts": {
    "critical": "number",
    "high": "number",
    "medium": "number",
    "low": "number"
  },
  "top_accounts": [
    {
      "customer_id": "string",
      "name": "string",
      "cost": "number",
      "conversions": "number"
    }
  ],
  "spending_chart": {
    "dates": ["string"],
    "values": ["number"]
  }
}
```

```http
GET /api/dashboard/widgets/{widget_name}
Headers: Authorization: Bearer <token>
Widgets disponibles:
  - recent-activity
  - billing-summary
  - campaign-performance
  - account-health
Response 200: Widget-specific data
```

---

## 🗄️ Esquema de Base de Datos

### **Tablas Principales**

#### **1. users**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### **2. google_ads_accounts**
```sql
CREATE TABLE google_ads_accounts (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    currency VARCHAR(10),
    timezone VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    descriptive_name VARCHAR(255),
    manager_account_id VARCHAR(20),
    is_test_account BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(50) DEFAULT 'pending'
);
```

#### **3. campaigns**
```sql
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    type VARCHAR(50),
    budget_amount DECIMAL(15,2),
    budget_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES google_ads_accounts(customer_id)
);
```

#### **4. campaign_metrics**
```sql
CREATE TABLE campaign_metrics (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    cost_micros BIGINT,
    impressions INTEGER,
    clicks INTEGER,
    conversions DECIMAL(10,2),
    ctr DECIMAL(10,4),
    avg_cpc_micros BIGINT,
    conversion_rate DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    UNIQUE(campaign_id, date)
);
```

#### **5. billing_info**
```sql
CREATE TABLE billing_info (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    billing_setup_id VARCHAR(50),
    status VARCHAR(50),
    payments_account VARCHAR(255),
    payment_method_type VARCHAR(50),
    start_date_time TIMESTAMP,
    end_date_time TIMESTAMP,
    current_balance_micros BIGINT,
    spending_limit_micros BIGINT,
    last_payment_date TIMESTAMP,
    next_payment_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES google_ads_accounts(customer_id)
);
```

#### **6. alerts**
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    customer_id VARCHAR(20),
    campaign_id VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    action_required BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES google_ads_accounts(customer_id)
);
```

#### **7. reports**
```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    format VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'processing',
    created_by INTEGER NOT NULL,
    customer_ids TEXT[], -- Array de customer IDs
    date_range_start DATE,
    date_range_end DATE,
    file_path VARCHAR(500),
    file_size INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

#### **8. sync_logs**
```sql
CREATE TABLE sync_logs (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(20),
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    records_processed INTEGER,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER
);
```

#### **9. system_settings**
```sql
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    value_type VARCHAR(50) DEFAULT 'string',
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);
```

#### **10. notification_config**
```sql
CREATE TABLE notification_config (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    threshold_value DECIMAL(15,2),
    notification_emails TEXT[],
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES google_ads_accounts(customer_id)
);
```

### **Índices Recomendados**
```sql
-- Performance indexes
CREATE INDEX idx_campaigns_customer_id ON campaigns(customer_id);
CREATE INDEX idx_campaign_metrics_campaign_id ON campaign_metrics(campaign_id);
CREATE INDEX idx_campaign_metrics_date ON campaign_metrics(date);
CREATE INDEX idx_alerts_customer_id ON alerts(customer_id);
CREATE INDEX idx_alerts_is_read ON alerts(is_read);
CREATE INDEX idx_billing_customer_id ON billing_info(customer_id);
CREATE INDEX idx_reports_created_by ON reports(created_by);
CREATE INDEX idx_sync_logs_customer_id ON sync_logs(customer_id);
```

---

## ⚙️ Configuración de Variables de Entorno

### **Backend (.env)**
```bash
# Flask Configuration
FLASK_APP=app
FLASK_ENV=development  # development | production
SECRET_KEY=your-secret-key-here-generate-random-string
DEBUG=True

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/google_ads_dashboard
# Para SQLite en desarrollo:
# DATABASE_URL=sqlite:///app.db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=Kqg431In6DxoZnSMJk0hQg
GOOGLE_ADS_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your-client-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=9759913462

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=86400  # 24 horas en segundos
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 días en segundos

# Email Configuration (para alertas)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=contactodeamarres@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=contactodeamarres@gmail.com

# Rate Limiting
API_RATE_LIMIT=1000 per day
GOOGLE_ADS_RATE_LIMIT=15000  # operaciones por día (test token)

# Celery Task Configuration
CELERY_SYNC_INTERVAL=3600  # 1 hora en segundos
CELERY_BILLING_CHECK_INTERVAL=21600  # 6 horas en segundos

# Logging
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
LOG_FILE_PATH=logs/app.log

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# File Storage
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB en bytes
ALLOWED_EXTENSIONS=pdf,xlsx,csv
```

### **Frontend (.env)**
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:5000/api
VITE_API_TIMEOUT=30000

# Environment
VITE_ENV=development  # development | production

# Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG_TOOLS=true

# App Configuration
VITE_APP_NAME=Google Ads Dashboard
VITE_APP_VERSION=1.0.0
```

---

## 📅 Plan de Desarrollo por Fases

### **FASE 1: Setup e Infraestructura (Semana 1)**
**Duración estimada:** 5 días laborables  
**Equipo:** 1 DevOps + 1 Backend Dev

#### **Tareas:**
1. **Configuración del repositorio**
   - Crear estructura de carpetas
   - Configurar Git (`.gitignore`, branches: `main`, `develop`, `feature/*`)
   - Setup de pre-commit hooks (linting, formatting)
   - Documentación inicial en README.md

2. **Configuración de Docker**
   - Crear Dockerfiles (backend, frontend)
   - Crear docker-compose.yml
   - Configurar volúmenes persistentes
   - Setup de networks entre servicios

3. **Configuración de Base de Datos**
   - Setup de PostgreSQL container
   - Crear esquema inicial
   - Configurar migraciones con Alembic
   - Scripts de seed data para testing

4. **Configuración de Redis**
   - Setup de Redis container
   - Configurar caché
   - Configurar message broker para Celery

5. **Setup de Google Ads API**
   - Configurar credenciales OAuth 2.0
   - Generar refresh token
   - Validar acceso a las 40+ cuentas
   - Documentar límites de rate limiting

**Entregables:**
- ✅ Repositorio configurado
- ✅ Docker Compose funcionando
- ✅ Base de datos inicializada
- ✅ Conexión exitosa a Google Ads API

---

### **FASE 2: Backend Core (Semanas 2-3)**
**Duración estimada:** 10 días laborables  
**Equipo:** 2 Backend Developers

#### **Sprint 1: Autenticación y Modelos (5 días)**

**Tareas:**
1. **Sistema de autenticación**
   - Implementar modelos de User
   - Crear endpoints de auth (login, logout, refresh)
   - Implementar JWT tokens
   - Middleware de autenticación
   - Decorador `@jwt_required`

2. **Modelos de datos**
   - Crear todos los modelos SQLAlchemy
   - Configurar relaciones entre tablas
   - Implementar validaciones
   - Crear migraciones

3. **Google Ads Service (Base)**
   - Clase base para comunicación con API
   - Manejo de autenticación OAuth
   - Wrapper para llamadas comunes
   - Sistema de retry y error handling

**Entregables:**
- ✅ Auth endpoints funcionando
- ✅ Modelos creados y migrados
- ✅ Conexión con Google Ads API establecida

#### **Sprint 2: Servicios de Negocio (5 días)**

**Tareas:**
1. **Account Service**
   - Listar cuentas
   - Obtener detalles de cuenta
   - Sincronizar datos desde Google Ads
   - Caché de datos en Redis

2. **Campaign Service**
   - Obtener campañas por cuenta
   - Métricas de rendimiento
   - Filtros y búsqueda
   - Agregación de datos

3. **Billing Service**
   - Consultar estado de facturación
   - Historial de pagos
   - Detección de alertas
   - Cálculo de umbrales

4. **Cache Service**
   - Estrategias de caché
   - Invalidación de caché
   - Warm-up de caché

**Entregables:**
- ✅ CRUD completo de cuentas
- ✅ Endpoints de campañas funcionando
- ✅ Sistema de facturación implementado
- ✅ Caché funcionando

---

### **FASE 3: Background Tasks (Semana 4)**
**Duración estimada:** 5 días laborables  
**Equipo:** 1 Backend Developer

#### **Tareas:**
1. **Configuración de Celery**
   - Setup de Celery worker
   - Configurar beat scheduler
   - Monitoreo con Flower (opcional)

2. **Tareas de sincronización**
   - Sync de cuentas (cada 1 hora)
   - Sync de campañas (cada 2 horas)
   - Sync de métricas (cada 4 horas)
   - Manejo de errores y reintentos

3. **Tareas de facturación**
   - Verificación de estado de billing (cada 6 horas)
   - Detección de problemas de pago
   - Generación de alertas automáticas

4. **Tareas de reportes**
   - Generación asíncrona de reportes
   - Reportes programados (diario, semanal)
   - Envío por email

5. **Sistema de alertas**
   - Evaluación de reglas de alertas
   - Envío de notificaciones por email
   - Logging de alertas generadas

**Entregables:**
- ✅ Celery workers funcionando
- ✅ Sincronización automática activa
- ✅ Sistema de alertas operativo
- ✅ Generación de reportes automática

---

### **FASE 4: API REST Completa (Semana 5)**
**Duración estimada:** 5 días laborables  
**Equipo:** 2 Backend Developers

#### **Tareas:**
1. **Endpoints de Dashboard**
   - Overview general
   - Widgets configurables
   - Métricas agregadas
   - Gráficos de tendencias

2. **Endpoints de Reports**
   - Crear reporte
   - Listar reportes
   - Descargar reporte
   - Estado de generación

3. **Endpoints de Alerts**
   - Listar alertas
   - Marcar como leída
   - Eliminar alerta
   - Configurar alertas personalizadas

4. **Documentación de API**
   - Swagger/OpenAPI spec
   - Ejemplos de requests/responses
   - Códigos de error
   - Rate limiting docs

5. **Testing**
   - Tests unitarios (>80% coverage)
   - Tests de integración
   - Tests de endpoints
   - Tests de tasks Celery

**Entregables:**
- ✅ Todos los endpoints documentados
- ✅ API completamente funcional
- ✅ Documentación Swagger
- ✅ Tests pasando (>80% coverage)

---

### **FASE 5: Frontend Base (Semanas 6-7)**
**Duración estimada:** 10 días laborables  
**Equipo:** 2 Frontend Developers

#### **Sprint 1: Setup y Autenticación (5 días)**

**Tareas:**
1. **Setup del proyecto React**
   - Configurar Vite + TypeScript
   - Instalar dependencias (MUI/Ant Design, Redux, Axios)
   - Configurar ESLint + Prettier
   - Configurar routing

2. **Sistema de autenticación**
   - Página de Login
   - Manejo de tokens (localStorage/sessionStorage)
   - Protected routes
   - Auto-logout en token expirado
   - Refresh token automático

3. **Layout base**
   - Header con navegación
   - Sidebar con menú
   - Footer
   - Responsive design
   - Dark/Light theme toggle

4. **Servicios API**
   - Configurar Axios con interceptors
   - Manejo de errores global
   - Loading states
   - Request/Response types (TypeScript)

**Entregables:**
- ✅ Login funcional
- ✅ Layout base responsive
- ✅ Routing configurado
- ✅ API service layer completo

#### **Sprint 2: Páginas Principales (5 días)**

**Tareas:**
1. **Dashboard Page**
   - Cards de métricas principales
   - Gráfico de gasto temporal
   - Lista de top cuentas
   - Widget de alertas recientes

2. **Accounts Page**
   - Tabla de cuentas con paginación
   - Búsqueda y filtros
   - Modal de detalles de cuenta
   - Indicadores de estado visual

3. **Campaigns Page**
   - Selector de cuenta
   - Tabla de campañas
   - Gráficos de rendimiento
   - Filtros por tipo, estado, fecha

4. **Componentes comunes**
   - DataTable reutilizable
   - Loading spinner
   - Error boundary
   - Toast notifications
   - Confirmation dialogs

**Entregables:**
- ✅ 3 páginas principales funcionando
- ✅ Componentes reutilizables creados
- ✅ Integración con backend completa
- ✅ UX fluida y responsive

---

### **FASE 6: Frontend Avanzado (Semanas 8-9)**
**Duración estimada:** 10 días laborables  
**Equipo:** 2 Frontend Developers

#### **Sprint 1: Facturación y Reportes (5 días)**

**Tareas:**
1. **Billing Page**
   - Tabla de estado de facturación
   - Indicadores visuales de alertas
   - Historial de pagos
   - Modal de configuración de alertas
   - Exportar datos

2. **Reports Page**
   - Formulario de generación de reportes
   - Lista de reportes históricos
   - Preview de reportes
   - Descarga de archivos
   - Indicador de progreso

3. **Gráficos avanzados**
   - Line charts para tendencias
   - Bar charts para comparativas
   - Pie charts para distribución
   - Tooltips interactivos
   - Responsive charts

**Entregables:**
- ✅ Billing page completa
- ✅ Reports page funcional
- ✅ Gráficos interactivos implementados

#### **Sprint 2: Alertas y Configuración (5 días)**

**Tareas:**
1. **Alerts Page**
   - Lista de alertas con filtros
   - Badges de severidad
   - Marcar como leída
   - Eliminar alertas
   - Notificaciones en tiempo real (opcional: WebSockets)

2. **Settings Page**
   - Configuración de usuario
   - Configuración de notificaciones
   - Gestión de cuentas de Google Ads
   - Logs del sistema
   - Tema y preferencias

3. **Optimizaciones**
   - Lazy loading de componentes
   - Code splitting
   - Memoization de componentes pesados
   - Debounce en búsquedas
   - Virtual scrolling en tablas grandes

**Entregables:**
- ✅ Alerts system completo
- ✅ Settings page funcional
- ✅ Performance optimizado

---

### **FASE 7: Testing y Refinamiento (Semana 10)**
**Duración estimada:** 5 días laborables  
**Equipo:** Todo el equipo

#### **Tareas:**
1. **Testing del sistema completo**
   - Tests E2E con Playwright/Cypress
   - Testing en diferentes navegadores
   - Testing responsive (mobile, tablet, desktop)
   - Testing de carga (stress testing)
   - Security testing (OWASP top 10)

2. **Refinamiento de UX**
   - Ajustes de diseño
   - Mejoras de accesibilidad (a11y)
   - Feedback de usuarios internos
   - Optimización de flujos

3. **Documentación**
   - Manual de usuario
   - Guía de instalación
   - Guía de deployment
   - Troubleshooting guide
   - Video tutorials (opcional)

4. **Bug fixing**
   - Resolver issues reportados
   - Optimizar queries lentas
   - Mejorar mensajes de error
   - Refactoring de código duplicado

**Entregables:**
- ✅ Sistema completamente testeado
- ✅ Bugs críticos resueltos
- ✅ Documentación completa
- ✅ UX pulida y optimizada

---

### **FASE 8: Deployment (Semana 11)**
**Duración estimada:** 5 días laborables  
**Equipo:** 1 DevOps + 1 Backend Dev

#### **Tareas:**
1. **Preparación para producción**
   - Configurar variables de entorno de prod
   - Setup de SSL/HTTPS
   - Configurar CORS correctamente
   - Habilitar logging en producción
   - Configurar backups automáticos de DB

2. **Deployment del backend**
   - Deploy en servidor (VPS/Cloud)
   - Configurar Nginx como reverse proxy
   - Setup de Gunicorn con múltiples workers
   - Configurar Celery workers
   - Configurar supervisord/systemd

3. **Deployment del frontend**
   - Build de producción
   - Deploy en CDN o hosting (Vercel/Netlify/etc)
   - Configurar dominio custom
   - Setup de analytics (opcional)

4. **Monitoreo y alertas**
   - Configurar health checks
   - Setup de alertas de sistema (email/Slack)
   - Monitoreo de logs
   - Dashboard de métricas (opcional: Grafana)

5. **Migración de datos**
   - Importar cuentas de Google Ads
   - Primera sincronización completa
   - Verificar integridad de datos
   - Setup de backups

**Entregables:**
- ✅ Sistema en producción
- ✅ Dominio configurado con SSL
- ✅ Monitoreo activo
- ✅ Datos migrados correctamente

---

## 📊 Métricas de Calidad y Rendimiento

### **Código**
```
✅ Backend:
   - Test coverage: >80%
   - Linting: 0 errors, <10 warnings
   - Code complexity: <10 por función
   - Documentación: Docstrings en todas las funciones públicas

✅ Frontend:
   - Test coverage: >70%
   - Linting: 0 errors, <5 warnings
   - Bundle size: <500KB (gzipped)
   - TypeScript: Strict mode enabled
```

### **Performance**
```
✅ Backend API:
   - Response time: <500ms (p95)
   - Throughput: >100 requests/second
   - Error rate: <1%
   - Uptime: >99.5%

✅ Frontend:
   - First Contentful Paint: <2s
   - Time to Interactive: <3s
   - Lighthouse Score: >90
   - Core Web Vitals: All green
```

### **Base de Datos**
```
✅ Queries:
   - Query time: <100ms (p95)
   - Index usage: >95%
   - Connection pooling: configurado
   - Backups: diarios automáticos
```

### **Google Ads API**
```
✅ Rate Limiting:
   - Operaciones/día: <15,000 (test token)
   - Reintentos: máximo 3 con backoff exponencial
   - Cache hit rate: >80%
   - Error handling: 100% de errores manejados
```

---

## 🔒 Seguridad

### **Medidas Obligatorias**

#### **Backend**
```
✅ Autenticación:
   - Passwords hasheados con bcrypt (cost=12)
   - JWT con expiración
   - Refresh tokens con rotación
   - Rate limiting en login (5 intentos/minuto)

✅ API:
   - HTTPS obligatorio en producción
   - CORS configurado restrictivamente
   - Input validation en todos los endpoints
   - SQL injection protection (ORM)
   - XSS protection en responses

✅ Datos sensibles:
   - Credenciales en variables de entorno
   - No hardcodear secrets
   - Logging sin datos sensibles
   - Encriptar datos críticos en DB
```

#### **Frontend**
```
✅ Tokens:
   - Almacenar en httpOnly cookies (preferido) o localStorage
   - No exponer tokens en URLs
   - Limpiar tokens en logout

✅ XSS Prevention:
   - Sanitizar inputs de usuario
   - Content Security Policy headers
   - React escapa automáticamente (usar dangerouslySetInnerHTML con cuidado)

✅ CSRF Protection:
   - CSRF tokens en formularios
   - SameSite cookies
```

#### **Infraestructura**
```
✅ Servidor:
   - Firewall configurado
   - Acceso SSH solo con keys
   - Actualizaciones automáticas de seguridad
   - Fail2ban o similar

✅ Base de datos:
   - No exponer puerto públicamente
   - Usuario con permisos mínimos
   - Backups encriptados
   - Auditoría de accesos
```

---

## 📚 Dependencias del Proyecto

### **Backend (requirements.txt)**
```txt
# Core
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-JWT-Extended==4.5.3
Flask-CORS==4.0.0

# Database
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23

# Google Ads
google-ads==23.0.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0

# Celery & Redis
celery==5.3.4
redis==5.0.1
flower==2.0.1  # opcional: monitoreo de Celery

# Utilities
python-dotenv==1.0.0
requests==2.31.0
pytz==2023.3
python-dateutil==2.8.2

# Excel/CSV
openpyxl==3.1.2
pandas==2.1.4

# PDF
reportlab==4.0.7  # o WeasyPrint

# Email
Flask-Mail==0.9.1

# Validation
marshmallow==3.20.1

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-flask==1.3.0
factory-boy==3.3.0

# Code quality
flake8==6.1.0
black==23.12.1
isort==5.13.2

# Production
gunicorn==21.2.0
```

### **Frontend (package.json)**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "@mui/material": "^5.15.0",
    "@mui/icons-material": "^5.15.0",
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0",
    "@reduxjs/toolkit": "^2.0.1",
    "react-redux": "^9.0.4",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "date-fns": "^3.0.6",
    "react-query": "^3.39.3",
    "react-hook-form": "^7.49.2",
    "yup": "^1.3.3",
    "notistack": "^3.0.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.15.0",
    "@typescript-eslint/parser": "^6.15.0",
    "@vitejs/plugin-react": "^4.2.1",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "prettier": "^3.1.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.8",
    "vitest": "^1.1.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5"
  }
}
```

---

## 🚀 Comandos de Desarrollo

### **Iniciar proyecto completo (Docker)**
```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar servicios
docker-compose down
```

### **Backend (sin Docker)**
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Crear base de datos
flask db upgrade

# Iniciar servidor de desarrollo
flask run --debug

# Iniciar Celery worker
celery -A app.celery worker --loglevel=info

# Iniciar Celery beat (scheduler)
celery -A app.celery beat --loglevel=info
```

### **Frontend**
```bash
# Instalar dependencias
npm install

# Iniciar desarrollo
npm run dev

# Build de producción
npm run build

# Preview de build
npm run preview

# Linting
npm run lint

# Testing
npm run test
```

---

## 📈 Estimación de Costos (Infraestructura)

### **Desarrollo Local**
```
💻 Gratis
   - Todo corre en Docker localmente
   - No requiere servicios cloud
```

### **Producción (Estimado mensual)**
```
💰 Opción Económica (~$30-50/mes):
   - VPS (DigitalOcean/Linode): $12-24/mes (2GB RAM, 1 CPU)
   - Base de datos managed: $15/mes (opcional, puede ir en VPS)
   - Dominio: $10-15/año
   - SSL: Gratis (Let's Encrypt)
   - Frontend hosting: Gratis (Vercel/Netlify)

💰 Opción Robusta (~$100-150/mes):
   - VPS más grande: $48/mes (4GB RAM, 2 CPU)
   - PostgreSQL managed: $25/mes
   - Redis managed: $10/mes
   - CDN: $10-20/mes
   - Backups automáticos: $5/mes
   - Monitoreo: $10-20/mes
```

---

## 🎓 Conocimientos Requeridos del Equipo

### **Backend Developer**
```
✅ Esenciales:
   - Python 3.10+
   - Flask framework
   - SQLAlchemy ORM
   - PostgreSQL
   - REST API design
   - OAuth 2.0 flow
   - Celery tasks
   - Redis

✅ Deseables:
   - Google Ads API experience
   - Docker
   - Testing (pytest)
   - Performance optimization
```

### **Frontend Developer**
```
✅ Esenciales:
   - React 18+
   - TypeScript
   - Redux/Zustand
   - Material-UI o Ant Design
   - Axios/Fetch API
   - React Router
   - Charts libraries

✅ Deseables:
   - Performance optimization
   - Accessibility (a11y)
   - Testing (Vitest/Jest)
   - Responsive design
```

### **DevOps/Full Stack**
```
✅ Esenciales:
   - Docker & Docker Compose
   - Linux server administration
   - Nginx configuration
   - Git/GitHub
   - CI/CD básico

✅ Deseables:
   - PostgreSQL administration
   - SSL/HTTPS setup
   - Monitoring tools
   - Backup strategies
```

---

## 🎯 Criterios de Éxito

### **MVP (Producto Mínimo Viable)**
```
✅ Usuario puede:
   - Login/logout
   - Ver dashboard con 40+ cuentas
   - Ver estado de facturación de todas las cuentas
   - Ver campañas de cualquier cuenta
   - Recibir alertas de problemas de billing
   - Generar reporte básico
   
✅ Sistema:
   - Sincroniza datos cada hora automáticamente
   - Detecta problemas de facturación
   - Envía alertas por email
   - Responde en <500ms
```

### **Producto Completo**
```
✅ Todas las funciones del MVP +
   - Reportes avanzados (PDF, Excel)
   - Dashboard personalizable
   - Configuración de alertas por cuenta
   - Gráficos interactivos avanzados
   - Exportación de datos
   - Búsqueda y filtros avanzados
   - Logs de actividad
   - Configuración multi-usuario
```

---

## 📞 Puntos de Contacto y Responsables

```
📋 Product Owner: Edwar Alexander Bechara (@saltbalente)
   Email: contactodeamarres@gmail.com
   Responsabilidad: Requisitos, prioridades, feedback

🔧 Tech Lead: [Asignar]
   Responsabilidad: Arquitectura, revisión de código, decisiones técnicas

💻 Backend Team Lead: [Asignar]
   Responsabilidad: API, database, integración Google Ads

🎨 Frontend Team Lead: [Asignar]
   Responsabilidad: UI/UX, componentes, integración con API

🚀 DevOps Lead: [Asignar]
   Responsabilidad: Infraestructura, deployment, monitoreo
```

---

## 📅 Calendario de Entregas

```
📍 Semana 1 (2025-10-16):  Setup completo
📍 Semana 3 (2025-10-30):  Backend core + Auth
📍 Semana 4 (2025-11-06):  Background tasks
📍 Semana 5 (2025-11-13):  API completa
📍 Semana 7 (2025-11