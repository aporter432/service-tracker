# CI/CD Pipeline Guide

Complete guide to the CI/CD pipeline for ORBCOMM Service Tracker.

## Overview

The project uses **GitHub Actions** for continuous integration and continuous deployment. The pipeline automatically:

- ✅ Tests code on multiple Python versions
- ✅ Runs linting and code quality checks
- ✅ Checks for security vulnerabilities
- ✅ Builds and scans Docker images
- ✅ Deploys to staging and production environments

## Pipeline Architecture

```
┌─────────────┐
│   Push to   │
│   GitHub    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         CI Pipeline (Test)          │
│  - Python 3.8, 3.9, 3.10, 3.11     │
│  - Unit & Integration Tests         │
│  - Code Coverage                    │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Code Quality (Lint)            │
│  - Black (formatting)               │
│  - isort (imports)                  │
│  - Flake8 (style)                   │
│  - Pylint (quality)                 │
│  - Bandit (security)                │
│  - Safety (dependencies)            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│       Build Docker Image            │
│  - Multi-stage build                │
│  - Push to registry                 │
│  - Trivy security scan              │
└──────┬──────────────────────────────┘
       │
       ├──────────────┬────────────────┐
       ▼              ▼                ▼
   Staging        Production      Manual Deploy
```

## GitHub Actions Workflows

### Main CI/CD Workflow

**File:** `.github/workflows/ci.yml`

**Triggered on:**
- Push to `main`, `develop`, or `claude/**` branches
- Pull requests to `main` or `develop`

**Jobs:**

1. **Test** (Matrix: Python 3.8-3.11)
   - Install dependencies
   - Run linting (black, isort, flake8)
   - Run tests with coverage
   - Upload coverage to Codecov

2. **Lint** (Code Quality)
   - Comprehensive flake8 checks
   - Pylint analysis
   - Security scanning (safety, bandit)
   - Upload security reports

3. **Build Docker**
   - Build multi-stage Docker image
   - Push to Docker Hub (on main/develop)
   - Run Trivy security scan
   - Upload SARIF to GitHub Security

4. **Deploy Staging** (develop branch)
   - Deploy to staging environment
   - Run smoke tests
   - Environment: staging

5. **Deploy Production** (main branch)
   - Deploy to production environment
   - Run smoke tests
   - Environment: production
   - Requires approval (GitHub Environments)

## Local CI Testing

Run the complete CI pipeline locally before pushing:

```bash
# Using Makefile
make ci

# Or manually
make install-dev
make lint
make test-cov
make security
```

## Setting Up GitHub Secrets

Required secrets for full CI/CD:

### Docker Hub
```bash
# Repository Settings → Secrets → Actions → New repository secret
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-token
```

### Heroku (if deploying)
```bash
HEROKU_API_KEY=your-heroku-api-key
HEROKU_APP_NAME=your-app-name
```

### Google Cloud (if deploying)
```bash
GCP_PROJECT_ID=your-project-id
GCP_SA_KEY=base64-encoded-service-account-key
```

### AWS (if deploying)
```bash
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

## Environment Configuration

### GitHub Environments

1. **Staging**
   - Branch: `develop`
   - URL: `https://staging.orbcomm-tracker.example.com`
   - No approval required
   - Automatic deployment

2. **Production**
   - Branch: `main`
   - URL: `https://orbcomm-tracker.example.com`
   - **Requires approval** (recommended)
   - Manual deployment trigger

**Setup Environments:**

1. Go to Repository Settings → Environments
2. Create `staging` and `production` environments
3. For production:
   - Check "Required reviewers"
   - Add reviewers who must approve deployments
   - Set deployment branch to `main`

## Branch Strategy

```
main (production)
  ├── develop (staging)
  │   ├── feature/new-feature
  │   ├── fix/bug-fix
  │   └── claude/ai-generated-changes
  └── hotfix/critical-fix
```

**Workflow:**

1. **Feature Development**
   ```bash
   git checkout develop
   git checkout -b feature/my-feature
   # Make changes
   git push origin feature/my-feature
   # Create PR to develop
   ```

2. **Deploy to Staging**
   ```bash
   # Merge PR to develop
   # CI automatically deploys to staging
   ```

3. **Deploy to Production**
   ```bash
   git checkout main
   git merge develop
   git push origin main
   # CI deploys to production (after approval)
   ```

## Pre-commit Hooks

Install pre-commit hooks to catch issues before committing:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Hooks configured:**
- Trailing whitespace removal
- File formatting
- YAML/JSON validation
- Black formatting
- isort import sorting
- Flake8 linting
- Bandit security checks

## Code Quality Standards

### Formatting
- **Black** for code formatting (line length: 88)
- **isort** for import sorting (profile: black)

### Linting
- **Flake8** for style guide enforcement
  - Max line length: 127
  - Max complexity: 10
- **Pylint** for code quality

### Security
- **Bandit** for security vulnerability scanning
- **Safety** for dependency vulnerability checking

### Testing
- **Pytest** for testing framework
- Minimum coverage: Not enforced (recommended: 80%+)

## Test Configuration

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
addopts = -v --strict-markers --tb=short
markers =
    slow: slow running tests
    integration: integration tests
    unit: unit tests
```

**Run tests:**
```bash
# All tests
make test

# With coverage
make test-cov

# Specific marker
pytest -m unit
pytest -m "not slow"
```

## Docker Build Pipeline

### Multi-stage Build

1. **Builder Stage**
   - Base: `python:3.10-slim`
   - Install dependencies
   - Create virtual environment

2. **Runtime Stage**
   - Base: `python:3.10-slim`
   - Copy virtual environment
   - Non-root user (orbcomm:1000)
   - Health check configured

### Security Scanning

**Trivy** scans Docker images for:
- OS vulnerabilities
- Application dependencies
- Misconfigurations
- Secrets

Results uploaded to GitHub Security tab.

## Deployment Environments

### Staging

**Purpose:** Test changes before production

**Configuration:**
- Branch: `develop`
- Automatic deployment on push
- Relaxed rate limits
- Verbose logging

**Access:**
```bash
# Via kubectl (if K8s)
kubectl get pods -n orbcomm-staging

# Via Docker
docker-compose -f docker-compose.staging.yml up
```

### Production

**Purpose:** Live environment

**Configuration:**
- Branch: `main`
- Manual approval required
- Strict security
- Error-level logging

**Deployment checklist:**
- [ ] All tests passing
- [ ] Security scans clean
- [ ] Staging validated
- [ ] Approval obtained
- [ ] Backup created

## Monitoring Pipeline

### Build Status Badge

Add to README.md:
```markdown
![CI/CD](https://github.com/aporter432/service-tracker/workflows/CI/CD%20Pipeline/badge.svg)
```

### Notifications

Configure GitHub Actions notifications:
- Slack webhook
- Email alerts
- Discord integration

## Troubleshooting

### Common Issues

**1. Tests failing in CI but passing locally**
```bash
# Check Python version
python --version

# Run in same version as CI
docker run -it python:3.10 bash
pip install -r requirements-prod.txt
pytest
```

**2. Docker build failing**
```bash
# Build locally to debug
docker build -t orbcomm-tracker:debug .

# Check build logs
docker build --progress=plain -t orbcomm-tracker:debug .
```

**3. Deployment failing**
```bash
# Check GitHub Actions logs
# Settings → Actions → Workflow runs → View logs

# Check secrets
# Settings → Secrets → Actions → Verify all required secrets set
```

**4. Coverage drop**
```bash
# Generate coverage report
pytest --cov=orbcomm_tracker --cov-report=html

# View report
open htmlcov/index.html

# Add missing tests
```

## Best Practices

### 1. Write Tests First
```python
# tests/test_feature.py
def test_new_feature():
    result = new_feature()
    assert result == expected
```

### 2. Keep PRs Small
- One feature per PR
- Max 400 lines changed
- Clear description

### 3. Review Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] CI passing
- [ ] Code reviewed

### 4. Commit Message Format
```
type(scope): Brief description

Detailed explanation of changes.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### 5. Version Tagging
```bash
# Tag release
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

## Performance Optimization

### Caching

**pip dependencies:**
```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.10'
    cache: 'pip'
```

**Docker layers:**
```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Parallel Jobs

Run tests in parallel:
```yaml
strategy:
  matrix:
    python-version: ['3.8', '3.9', '3.10', '3.11']
```

## Security

### Secrets Management

**Never commit:**
- API keys
- Passwords
- Private keys
- Tokens

**Use GitHub Secrets:**
```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
```

### Dependabot

Enable automatic dependency updates:

**File:** `.github/dependabot.yml`
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python Testing](https://docs.pytest.org/)
- [Security Scanning](https://github.com/marketplace/actions/aqua-security-trivy)

---

For questions or issues with CI/CD, create an issue on GitHub.
