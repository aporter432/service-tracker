# Project Structure

## Overview

ORBCOMM Service Tracker is organized following Python best practices for production-ready applications. This document describes the project structure and organization.

## Directory Tree

```
service-tracker/
├── .github/
│   └── workflows/
│       └── ci.yml                 # CI/CD pipeline configuration
│
├── orbcomm_tracker/               # Main Python package
│   ├── __init__.py               # Package initialization
│   ├── database.py               # Database layer (SQLite/PostgreSQL)
│   ├── gmail_api.py              # Gmail API integration
│   ├── parser.py                 # Email parsing logic
│   ├── sync.py                   # Sync orchestration
│   ├── monitoring.py             # Health checks & metrics
│   └── security.py               # Security features
│
├── templates/                     # Flask HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── notifications.html
│   ├── notification_detail.html
│   ├── stats.html
│   └── error.html
│
├── static/                        # Static assets
│   └── style.css
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_incident_parsing_simple.py  # Unit tests
│   └── test_integration.py       # Integration tests
│
├── scripts/                       # Utility scripts
│   ├── setup.sh                  # Initial setup automation
│   └── deploy.sh                 # Deployment automation
│
├── kubernetes/                    # Kubernetes manifests
│   └── deployment.yaml           # K8s deployment config
│
├── claudedocs/                    # Internal documentation
│   ├── SYSTEM_DESIGN.md
│   ├── GMAIL_API_SETUP.md
│   └── INBOX_STRATEGY.md
│
├── Application Entry Points       # Standalone executables
│   ├── orbcomm_dashboard.py      # Flask web dashboard
│   ├── orbcomm_scheduler.py      # Daily automation
│   ├── run_sync.py               # Manual sync CLI
│   ├── setup_gmail_auth.py       # OAuth setup
│   └── wsgi.py                   # WSGI entry point
│
├── Configuration Files
│   ├── config.py                 # Application configuration
│   ├── .env.example              # Environment template
│   ├── requirements.txt          # Base dependencies
│   ├── requirements-prod.txt     # Production dependencies
│   ├── gunicorn.conf.py         # Gunicorn configuration
│   ├── pytest.ini               # Pytest configuration
│   └── .pre-commit-config.yaml  # Pre-commit hooks
│
├── Docker & Container Files
│   ├── Dockerfile                # Production image
│   ├── Dockerfile.dev            # Development image
│   ├── docker-compose.yml        # Production stack
│   ├── docker-compose.dev.yml    # Development stack
│   ├── .dockerignore            # Docker ignore patterns
│   └── nginx.conf                # Nginx reverse proxy
│
├── Deployment Configurations
│   ├── Procfile                  # Heroku process definition
│   ├── app.json                  # Heroku app manifest
│   ├── runtime.txt               # Python runtime version
│   ├── cloudbuild.yaml          # Google Cloud Build
│   ├── app.yaml                  # Google App Engine
│   ├── aws-task-definition.json  # AWS ECS task
│   └── kubernetes/               # Kubernetes manifests
│
├── Documentation
│   ├── README.md                 # Main documentation
│   ├── QUICKSTART.md            # Quick start guide
│   ├── DEPLOYMENT.md            # Deployment guide
│   ├── CI_CD_GUIDE.md           # CI/CD documentation
│   ├── CONTRIBUTING.md          # Contribution guidelines
│   ├── PROJECT_STRUCTURE.md     # This file
│   └── SETUP_STEPS.md           # Detailed setup
│
├── Build & Development Tools
│   ├── Makefile                  # Common tasks automation
│   ├── .gitignore               # Git ignore patterns
│   └── .pre-commit-config.yaml  # Code quality hooks
│
└── Data Directory (runtime)
    └── ~/.orbcomm/               # User data (not in repo)
        ├── tracker.db            # SQLite database
        ├── credentials.json      # Gmail credentials
        ├── token.json            # OAuth token
        └── logs/                 # Application logs
```

## Module Descriptions

### Core Package (`orbcomm_tracker/`)

**Purpose:** Main application logic

| File | Purpose | Key Functions |
|------|---------|---------------|
| `database.py` | Database abstraction layer | `store_notification()`, `get_all_notifications()`, `get_stats()` |
| `gmail_api.py` | Gmail API integration | `get_gmail_service()`, `fetch_emails()` |
| `parser.py` | Email parsing | `parse_email()`, `extract_incident_data()` |
| `sync.py` | Orchestration | `run_sync()`, `process_emails()` |
| `monitoring.py` | Health & metrics | `HealthCheck`, `Metrics`, `register_health_routes()` |
| `security.py` | Security features | `RateLimiter`, `SecurityHeaders`, `SimpleAuth` |

### Application Entry Points

| File | Purpose | Usage |
|------|---------|-------|
| `orbcomm_dashboard.py` | Web interface | `python orbcomm_dashboard.py` |
| `run_sync.py` | Manual sync | `python run_sync.py --inbox 2` |
| `orbcomm_scheduler.py` | Automated sync | Runs daily via scheduler |
| `wsgi.py` | Production server | `gunicorn wsgi:application` |

### Configuration Management

**Environment-based configuration:**

```python
# config.py
class Config:              # Base configuration
class DevelopmentConfig:   # Development settings
class ProductionConfig:    # Production settings
class TestingConfig:       # Testing settings
```

**Usage:**
```python
from config import get_config

config = get_config('production')
app.config.from_object(config)
```

### Testing Structure

```
tests/
├── test_incident_parsing_simple.py   # Unit tests for parser
└── test_integration.py                # Integration tests
    ├── TestDatabaseIntegration       # Database operations
    ├── TestConfigurationManagement   # Config loading
    ├── TestHealthChecks             # Health endpoints
    ├── TestSecurityFeatures         # Security utilities
    └── TestFlaskEndpoints           # API endpoints
```

**Test execution:**
```bash
pytest tests/                    # All tests
pytest tests/test_integration.py # Integration only
pytest -m unit                   # Unit tests only
make test-cov                    # With coverage
```

## Deployment Artifacts

### Docker Images

**Production Image:**
- Base: `python:3.10-slim`
- Multi-stage build
- Non-root user
- Health checks
- Size: ~150MB

**Development Image:**
- Hot-reload support
- Debug tools
- IPython included

### Kubernetes Resources

```yaml
- Deployment (3 replicas)
- Service (LoadBalancer)
- PersistentVolumeClaim (10Gi)
- Secrets (credentials)
- HorizontalPodAutoscaler (2-10 pods)
```

## Data Flow

```
┌─────────────────┐
│  Gmail API      │
│  (Email Source) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  gmail_api.py   │
│  (Fetch Emails) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  parser.py      │
│  (Parse HTML)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  database.py    │
│  (Store Data)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flask Routes   │
│  (Web UI)       │
└─────────────────┘
```

## API Endpoints

### Web Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Dashboard |
| `/notifications` | GET | All notifications |
| `/notification/<ref>` | GET | Notification detail |
| `/stats` | GET | Statistics page |

### API Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/stats` | GET | Current statistics |
| `/api/sync` | POST | Trigger sync |

### Health & Monitoring

| Route | Purpose |
|-------|---------|
| `/health` | Basic health check |
| `/health/detailed` | Component health |
| `/health/live` | Liveness probe |
| `/health/ready` | Readiness probe |
| `/metrics` | Prometheus metrics |
| `/info` | Application info |

## Configuration Hierarchy

```
Environment Variables (.env)
         ↓
    config.py (Config classes)
         ↓
    Application (Flask app config)
         ↓
    Runtime (Active configuration)
```

**Priority:**
1. Environment variables (highest)
2. `.env` file
3. Config class defaults
4. Hard-coded defaults (lowest)

## Development Workflow

### 1. Setup
```bash
./scripts/setup.sh
source venv/bin/activate
```

### 2. Development
```bash
# Start development server
python orbcomm_dashboard.py

# Or with Docker
docker-compose -f docker-compose.dev.yml up
```

### 3. Testing
```bash
make test           # Run tests
make lint           # Check code quality
make format         # Auto-format code
```

### 4. Deployment
```bash
make docker-build   # Build image
make deploy         # Deploy to platform
```

## Build Artifacts

### Python Package
```bash
python setup.py sdist bdist_wheel
# Creates: dist/orbcomm-tracker-1.1.0.tar.gz
```

### Docker Image
```bash
docker build -t orbcomm-tracker:1.1.0 .
# Creates: orbcomm-tracker:1.1.0
```

### Documentation
- HTML docs (if using Sphinx)
- API documentation
- Deployment guides

## File Naming Conventions

- **Python files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions:** `snake_case()`
- **Constants:** `UPPER_CASE`
- **Templates:** `kebab-case.html`
- **Config files:** `lowercase.extension`

## Code Organization Principles

1. **Separation of Concerns:** Each module has single responsibility
2. **DRY (Don't Repeat Yourself):** Shared code in utilities
3. **Testability:** All modules easily testable
4. **Documentation:** Docstrings for all public APIs
5. **Type Hints:** Where beneficial for clarity

## Dependencies Management

### Production (`requirements.txt`)
- Core application dependencies
- Minimal footprint
- Locked versions

### Development (`requirements-prod.txt`)
- Includes production dependencies
- Testing frameworks
- Code quality tools
- Security scanners

## Version Control

### Ignored Files (`.gitignore`)
- Virtual environments
- Database files
- Credentials
- Logs
- Cache files
- Build artifacts

### Tracked Files
- Source code
- Configuration templates
- Documentation
- Tests
- Deployment configs

## Future Structure

Potential additions:
- `alembic/` - Database migrations
- `docs/` - Sphinx documentation
- `locales/` - Internationalization
- `plugins/` - Plugin system
- `api/` - Separate API package

---

For questions about the project structure, see [CONTRIBUTING.md](CONTRIBUTING.md).
