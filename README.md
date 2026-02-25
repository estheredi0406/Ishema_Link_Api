
---

## Overview

IshemaLink is an enterprise-grade logistics platform designed specifically for Rwanda's unique transport and regulatory environment. It handles domestic and international shipments, mobile money payments, government compliance, and real-time analytics.

### Key Features

-  **Unified Booking System** - Domestic & International shipments
- **Mobile Money Integration** - MTN/Airtel payment processing
- **Government Compliance** - RRA (Tax), RURA (Licensing), EAC (Customs)
- **Real-time Analytics** - BI dashboard for MINICOM road planning
- **Multi-channel Notifications** - SMS + Email alerts
- **Production Deployment** - Docker, PostgreSQL, Redis, Nginx
- **Enterprise Security** - RBAC, JWT, encryption, audit logging

### Rwanda-Specific

-  Districts & Sectors validation (30 districts, 416 sectors)
-  Phone format validation (+250XXXXXXXXX)
-  National ID validation (16 digits)
-  RWF currency with 18% VAT
- Kigali timezone (Africa/Kigali)
- Government API integration (RRA EBM, RURA)

---

## Architecture

```
┌─────────────┐
│   Clients   │  Web Dashboard, Mobile App, Gov Portal
└──────┬──────┘
       │
┌──────▼──────┐
│    Nginx    │  Reverse Proxy + SSL
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│  Django App (Gunicorn)      │  4 workers + 2 threads
│  - Authentication           │
│  - Booking Service          │
│  - Payment Gateway          │
│  - Notification Engine      │
│  - Analytics Service        │
└──────┬──────────────────────┘
       │
┌──────▼────────┬──────────┐
│  PostgreSQL   │  Redis   │
│  (Primary DB) │  (Cache) │
└───────────────┴──────────┘
```

[Full Architecture →](docs/ARCHITECTURE.md)

---

##  Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)
- Git

### Docker Deployment (Recommended)
```bash
# Clone repository
git clone https://github.com/yourusername/ishema-link-api.git
cd ishema-link-api

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Build and start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access application
open http://localhost:8000/api/docs/
```

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver

# Access API
open http://localhost:8000/api/docs/
```

---

##  API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Core Endpoints

#### Authentication
```bash
POST   /api/core/auth/token/obtain/        # Get JWT token
POST   /api/core/auth/token/refresh/       # Refresh token
POST   /api/core/auth/register/            # Register user
```

#### Bookings
```bash
POST   /api/domestic/shipments/            # Create shipment
GET    /api/domestic/shipments/            # List shipments
GET    /api/domestic/shipments/{id}/       # Get details
PATCH  /api/domestic/shipments/{id}/       # Update status
```

#### Payments
```bash
POST   /api/payments/initiate/             # Start payment
POST   /api/payments/webhook/              # Payment callback
GET    /api/payments/                      # Payment history
```

#### Government Integration
```bash
POST   /api/core/gov/ebm/sign-receipt/          # RRA tax receipt
GET    /api/core/gov/rura/verify-license/{id}/  # License check
POST   /api/core/gov/customs/generate-manifest/ # EAC manifest
```

#### Analytics
```bash
GET    /api/analytics/routes/top/               # Top routes
GET    /api/analytics/commodities/breakdown/    # Cargo stats
GET    /api/analytics/revenue/heatmap/          # Revenue map
GET    /api/analytics/drivers/leaderboard/      # Performance
```

---

## Testing

### Run Tests
```bash
# All tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html

# Specific test categories
pytest core/test.py -v                    # Authentication
pytest domestic/test_tarrif.py -v        # Tariff calculation
pytest core/test_security.py -v          # Security tests
pytest test_integration_happy_path.py    # Integration
```

### Test Coverage

- **Overall**: 45%
- **Critical Modules**: 80%+
- **Tests Passing**: 14/16 (88%)

Full Testing Report → (docs/testing-report.md)

---

## Security

### Authentication

- **JWT Tokens**: Mobile apps (30 min access, 7 day refresh)
- **Session Auth**: Web dashboard (8 hour sessions)
- **Rate Limiting**: 100 req/hr (anonymous), 1000 req/hr (authenticated)

### Authorization (RBAC)

| Role | Permissions |
|------|------------|
| CUSTOMER | Create shipments, view own data, payments |
| DRIVER | View assigned shipments (no pricing) |
| ADMIN | Full system access, analytics, user management |
| GOV_OFFICIAL | Read-only access, audit logs, statistics |

### Data Protection

- NID encryption (Fernet symmetric encryption)
- Password hashing (Argon2)
- HTTPS/SSL in production
- Secure cookies (HttpOnly, Secure, SameSite)
- CSRF protection
- SQL injection prevention (Django ORM)

---

## Features Overview

**Unified booking workflow with payment and notifications**

- Domestic & International shipment creation
- Real-time tariff calculation (weight + distance + mode)
- Mobile Money integration (MTN/Airtel)
- SMS notifications to senders
- Email notifications to exporters
- Admin control tower dashboard


### Production Readiness

**Docker deployment with monitoring**

- Multi-container setup (6 services)
- Nginx + Gunicorn + PostgreSQL + Redis
- Health check endpoints
- Prometheus-compatible metrics
- Maintenance mode support
- Auto-restart on failure

### GovTech Integration 

**Compliance with Rwanda regulations**

- **RRA**: Electronic Billing Machine (EBM) receipt signing
- **RURA**: Driver license and vehicle insurance verification
- **EAC**: Customs manifest generation (XML)
- Government audit trail (read-only portal)

### BI Analytics 

**Data-driven insights for MINICOM**

- Top traffic routes (infrastructure planning)
- Commodity breakdown (Food vs Electronics vs Construction)
- Revenue heatmap (business expansion)
- Driver performance metrics (anonymized)

---

## Rwanda Context

### Why Generic Software Fails in Rwanda
---

## Deployment

### Production Deployment (Ubuntu Server)

[Full Deployment Guide →](docs/DEPLOYMENT.md)
```bash
# Quick deployment
git clone https://github.com/yourusername/ishema-link-api.git
cd ishema-link-api
cp .env.example .env
# Edit .env
docker-compose -f docker-compose.yml up -d
```

### Environment Variables
```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=ishemalink.rw,www.ishemalink.rw

# Database
DATABASE_URL=postgresql://user:pass@db:5432/ishemalink

# Redis
REDIS_URL=redis://redis:6379/0

# SMS (Africa's Talking)
SMS_API_KEY=your-africastalking-key

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-key
```

---

## Scalability Plan

### Current Capacity
- **Concurrent Users**: 500
- **Requests/Second**: 100
- **Database Size**: 10GB
- **Response Time**: < 500ms (p95)

### Year 1 (50,000 Users)

**Infrastructure**:
- Add 2 more web servers (load balanced)
- PostgreSQL read replicas for analytics
- Redis cluster (3 nodes)
- CDN for static files

**Optimizations**:
- Database connection pooling (PgBouncer)
- Query optimization & indexing
- Async task offloading (Celery)
- Horizontal scaling (Kubernetes)

**Estimated Cost**: $500-800/month (Rwanda Cloud)

---

## Tech Stack

### Backend
- **Framework**: Django 6.0.2
- **API**: Django REST Framework 3.15
- **Auth**: JWT (simplejwt) + Session
- **Tasks**: Celery 5.3
- **Language**: Python 3.12


## Project Structure
```
ishema-link-api/
├── core/                    # Authentication, users, RBAC
│   ├── models.py           # User model, audit logs
│   ├── views.py            # Auth endpoints
│   ├── permissions.py      # RBAC logic
│   └── tests.py            # 14 tests
├── domestic/               # Domestic shipments
│   ├── models.py           # Shipment, tariff models
│   ├── views.py            # CRUD endpoints
│   ├── analytics_service.py # BI queries
│   └── test_tarrif.py      # Tariff tests
├── payments/               # Payment processing
│   ├── models.py           # Payment, transaction
│   ├── momo_service.py     # Mobile Money integration
│   └── views.py            # Payment endpoints
├── notifications/          # SMS & Email
│   ├── services.py         # Notification logic
│   └── views.py            # Send/broadcast
├── bookings/               # Unified booking
├── international/          # Cross-border shipments
├── docker-compose.yml      # 6 services orchestration
├── Dockerfile              # Python 3.12 multi-stage
├── nginx/                  # Reverse proxy config
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # System design
│   ├── DEPLOYMENT.md       # Deployment guide
│   ├── testing-report.md   # Test results
│   └── *.md               # Additional docs
└── scripts/                # Deployment scripts
```

---

