# ORBCOMM Service Tracker - Deployment Guide

This guide covers deploying the ORBCOMM Service Tracker to various platforms.

## Table of Contents

1. [Quick Start with Docker](#quick-start-with-docker)
2. [Deploy to Heroku](#deploy-to-heroku)
3. [Deploy to Google Cloud](#deploy-to-google-cloud)
4. [Deploy to AWS](#deploy-to-aws)
5. [Deploy to Kubernetes](#deploy-to-kubernetes)
6. [Environment Variables](#environment-variables)
7. [Database Migration](#database-migration)
8. [Monitoring & Logs](#monitoring--logs)

---

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Gmail API credentials configured

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/aporter432/service-tracker.git
cd service-tracker

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your configuration
nano .env

# 4. Build and run with Docker Compose
docker-compose -f docker-compose.dev.yml up --build

# Access at http://localhost:5000
```

### Production

```bash
# 1. Build production image
docker build -t orbcomm-tracker:latest .

# 2. Run production stack
docker-compose up -d

# 3. View logs
docker-compose logs -f orbcomm-tracker

# 4. Stop services
docker-compose down
```

### With Monitoring (Prometheus + Grafana)

```bash
# Start full stack with monitoring
docker-compose --profile monitoring up -d

# Access points:
# - Application: http://localhost:5000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

---

## Deploy to Heroku

### Prerequisites
- Heroku CLI installed and logged in
- Git repository

### Deployment Steps

```bash
# 1. Create Heroku app
heroku create your-app-name

# 2. Add required add-ons
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini

# 3. Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set LOG_LEVEL=INFO
heroku config:set METRICS_ENABLED=true

# 4. Deploy
git push heroku main

# 5. Scale dynos
heroku ps:scale web=1 worker=1

# 6. Open application
heroku open

# 7. View logs
heroku logs --tail
```

### One-Click Deploy

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

---

## Deploy to Google Cloud

### Option 1: Cloud Run (Recommended for Serverless)

```bash
# 1. Set project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 3. Build and deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml

# 4. Alternative: Direct deploy
gcloud run deploy orbcomm-tracker \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production

# 5. Get service URL
gcloud run services describe orbcomm-tracker --region us-central1 --format 'value(status.url)'
```

### Option 2: App Engine

```bash
# 1. Deploy to App Engine
gcloud app deploy app.yaml

# 2. View application
gcloud app browse

# 3. Stream logs
gcloud app logs tail -s default
```

### Option 3: Google Kubernetes Engine (GKE)

```bash
# 1. Create GKE cluster
gcloud container clusters create orbcomm-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-1

# 2. Get credentials
gcloud container clusters get-credentials orbcomm-cluster --zone us-central1-a

# 3. Build and push image
docker build -t gcr.io/$PROJECT_ID/orbcomm-tracker:latest .
docker push gcr.io/$PROJECT_ID/orbcomm-tracker:latest

# 4. Update deployment.yaml with your PROJECT_ID
sed -i "s/PROJECT_ID/$PROJECT_ID/g" kubernetes/deployment.yaml

# 5. Deploy to Kubernetes
kubectl apply -f kubernetes/deployment.yaml

# 6. Get external IP
kubectl get service orbcomm-tracker
```

---

## Deploy to AWS

### Option 1: Elastic Container Service (ECS) with Fargate

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name orbcomm-tracker

# 2. Get login credentials
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 3. Build and push image
docker build -t orbcomm-tracker .
docker tag orbcomm-tracker:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/orbcomm-tracker:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/orbcomm-tracker:latest

# 4. Create EFS file system for persistent data
aws efs create-file-system --creation-token orbcomm-data

# 5. Update aws-task-definition.json with your ACCOUNT_ID and EFS file system ID

# 6. Register task definition
aws ecs register-task-definition --cli-input-json file://aws-task-definition.json

# 7. Create ECS cluster
aws ecs create-cluster --cluster-name orbcomm-cluster

# 8. Create service
aws ecs create-service \
  --cluster orbcomm-cluster \
  --service-name orbcomm-tracker \
  --task-definition orbcomm-tracker \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Option 2: Elastic Beanstalk

```bash
# 1. Initialize Elastic Beanstalk
eb init -p docker orbcomm-tracker --region us-east-1

# 2. Create environment
eb create orbcomm-prod --instance-type t3.small

# 3. Deploy
eb deploy

# 4. Open application
eb open

# 5. View logs
eb logs
```

---

## Deploy to Kubernetes

### Prerequisites
- Kubernetes cluster (any cloud provider or local)
- kubectl configured

### Deployment

```bash
# 1. Create namespace
kubectl create namespace orbcomm

# 2. Create secrets
kubectl create secret generic orbcomm-secrets \
  --from-literal=secret-key=$(python -c "import secrets; print(secrets.token_hex(32))") \
  --from-literal=database-url="sqlite:////app/data/tracker.db" \
  -n orbcomm

# 3. Deploy application
kubectl apply -f kubernetes/deployment.yaml -n orbcomm

# 4. Check deployment status
kubectl get pods -n orbcomm
kubectl get services -n orbcomm

# 5. Port forward for testing (if no LoadBalancer)
kubectl port-forward service/orbcomm-tracker 8080:80 -n orbcomm

# 6. Access application
# With LoadBalancer: Get external IP from kubectl get svc
# With port-forward: http://localhost:8080
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Environment | `production` |
| `SECRET_KEY` | Flask secret key | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ORBCOMM_DATA_DIR` | Data directory | `/app/data` |
| `DATABASE_PATH` | Database file path | `/app/data/tracker.db` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `5000` |
| `WORKERS` | Gunicorn workers | `4` |
| `CORS_ENABLED` | Enable CORS | `true` |
| `CORS_ORIGINS` | Allowed origins | `*` |
| `RATELIMIT_ENABLED` | Enable rate limiting | `true` |
| `METRICS_ENABLED` | Enable Prometheus metrics | `false` |

### Security Variables

| Variable | Description |
|----------|-------------|
| `DASHBOARD_USERNAME` | Dashboard username (optional) |
| `DASHBOARD_PASSWORD_HASH` | Dashboard password hash (optional) |
| `SSL_KEYFILE` | SSL private key file |
| `SSL_CERTFILE` | SSL certificate file |

---

## Database Migration

### From SQLite to PostgreSQL

For production deployments with multiple instances, migrate to PostgreSQL:

```bash
# 1. Install PostgreSQL adapter
pip install psycopg2-binary

# 2. Set DATABASE_URL
export DATABASE_URL="postgresql://user:password@host:5432/dbname"

# 3. Export SQLite data
python scripts/export_sqlite_data.py > data.json

# 4. Import to PostgreSQL
python scripts/import_to_postgres.py data.json
```

---

## Monitoring & Logs

### Health Checks

```bash
# Basic health check
curl http://your-app/health

# Detailed health check
curl http://your-app/health/detailed

# Kubernetes liveness probe
curl http://your-app/health/live

# Kubernetes readiness probe
curl http://your-app/health/ready
```

### Prometheus Metrics

Access metrics at: `http://your-app/metrics`

Example metrics:
- `orbcomm_requests_total` - Total request count
- `orbcomm_request_duration_seconds` - Request duration
- `orbcomm_emails_fetched_total` - Emails fetched
- `orbcomm_notifications_total` - Notification count

### Viewing Logs

**Docker:**
```bash
docker-compose logs -f orbcomm-tracker
```

**Heroku:**
```bash
heroku logs --tail
```

**Google Cloud:**
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --format json
```

**AWS CloudWatch:**
```bash
aws logs tail /ecs/orbcomm-tracker --follow
```

**Kubernetes:**
```bash
kubectl logs -f deployment/orbcomm-tracker -n orbcomm
```

---

## Performance Tuning

### Gunicorn Workers

Calculate optimal workers:
```python
workers = (2 * CPU_cores) + 1
```

Set in environment:
```bash
export WORKERS=9  # For 4-core system
```

### Database Optimization

```bash
# Vacuum database periodically
python -c "from orbcomm_tracker.database import Database; Database().vacuum_database()"

# Backup database
python -c "from orbcomm_tracker.database import Database; Database().backup_database()"
```

---

## Troubleshooting

### Common Issues

**1. Database locked error**
- Solution: Migrate to PostgreSQL for multi-instance deployments

**2. Gmail API quota exceeded**
- Solution: Reduce sync frequency or request quota increase

**3. Health check failing**
- Check: Database connectivity, disk space, memory usage
- View detailed health: `curl http://your-app/health/detailed`

**4. High memory usage**
- Reduce `WORKERS` count
- Enable worker recycling (gunicorn `max_requests`)

---

## Security Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Enable HTTPS in production
- [ ] Set strong passwords for authentication
- [ ] Configure CORS allowed origins
- [ ] Enable rate limiting
- [ ] Review security headers
- [ ] Keep dependencies updated
- [ ] Monitor security scan results
- [ ] Use environment variables for secrets
- [ ] Enable authentication if needed

---

## Next Steps

1. **Set up monitoring**: Configure Prometheus + Grafana
2. **Configure backups**: Schedule database backups
3. **SSL certificates**: Set up Let's Encrypt or use cloud provider certificates
4. **Custom domain**: Configure DNS and domain mapping
5. **Alerting**: Set up alerts for errors and performance issues

---

For more information, see:
- [README.md](README.md) - General documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [CI/CD Pipeline](.github/workflows/ci.yml) - Automated deployment
