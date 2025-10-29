#!/bin/bash
# Deployment script for ORBCOMM Service Tracker
# Supports multiple deployment targets

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check requirements
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
}

check_heroku_cli() {
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI not found. Install from: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
}

check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK not found. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
}

check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Install from: https://aws.amazon.com/cli/"
        exit 1
    fi
}

# Deployment functions
deploy_docker() {
    print_header "Deploying with Docker"

    check_docker

    echo "Building Docker image..."
    docker build -t orbcomm-tracker:latest .
    print_success "Image built successfully"

    echo "Starting containers..."
    docker-compose up -d
    print_success "Containers started"

    echo "Checking health..."
    sleep 5
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        print_success "Application is healthy!"
        echo "Access at: http://localhost:5000"
    else
        print_warning "Health check failed. Check logs with: docker-compose logs"
    fi
}

deploy_heroku() {
    print_header "Deploying to Heroku"

    check_heroku_cli

    # Check if logged in
    if ! heroku auth:whoami &> /dev/null; then
        print_error "Not logged in to Heroku. Run: heroku login"
        exit 1
    fi

    # Check if app exists
    if [ -z "$HEROKU_APP_NAME" ]; then
        read -p "Enter Heroku app name: " HEROKU_APP_NAME
    fi

    echo "Deploying to Heroku app: $HEROKU_APP_NAME"

    # Push to Heroku
    git push heroku main
    print_success "Code deployed"

    # Scale dynos
    heroku ps:scale web=1 worker=1 --app "$HEROKU_APP_NAME"
    print_success "Dynos scaled"

    # Get app URL
    app_url=$(heroku info --app "$HEROKU_APP_NAME" | grep "Web URL" | awk '{print $3}')
    print_success "Deployment complete!"
    echo "Access at: $app_url"
}

deploy_gcp() {
    print_header "Deploying to Google Cloud Run"

    check_gcloud

    if [ -z "$GCP_PROJECT_ID" ]; then
        read -p "Enter GCP Project ID: " GCP_PROJECT_ID
    fi

    echo "Setting project: $GCP_PROJECT_ID"
    gcloud config set project "$GCP_PROJECT_ID"

    echo "Deploying to Cloud Run..."
    gcloud run deploy orbcomm-tracker \
        --source . \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated \
        --set-env-vars FLASK_ENV=production

    print_success "Deployment complete!"

    # Get service URL
    service_url=$(gcloud run services describe orbcomm-tracker --region us-central1 --format 'value(status.url)')
    echo "Access at: $service_url"
}

deploy_aws() {
    print_header "Deploying to AWS ECS"

    check_aws_cli
    check_docker

    if [ -z "$AWS_ACCOUNT_ID" ]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    fi

    AWS_REGION=${AWS_REGION:-us-east-1}
    ECR_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/orbcomm-tracker"

    echo "Building and pushing to ECR..."

    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

    # Build image
    docker build -t orbcomm-tracker .
    docker tag orbcomm-tracker:latest "$ECR_REPO:latest"

    # Push image
    docker push "$ECR_REPO:latest"
    print_success "Image pushed to ECR"

    # Update ECS service
    echo "Updating ECS service..."
    aws ecs update-service \
        --cluster orbcomm-cluster \
        --service orbcomm-tracker \
        --force-new-deployment \
        --region "$AWS_REGION"

    print_success "Deployment initiated. Check AWS Console for status."
}

# Main menu
show_menu() {
    print_header "ORBCOMM Service Tracker - Deployment"

    echo "Select deployment target:"
    echo "1) Docker (local)"
    echo "2) Heroku"
    echo "3) Google Cloud Run"
    echo "4) AWS ECS"
    echo "5) Exit"
    echo ""
    read -p "Enter choice [1-5]: " choice

    case $choice in
        1)
            deploy_docker
            ;;
        2)
            deploy_heroku
            ;;
        3)
            deploy_gcp
            ;;
        4)
            deploy_aws
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_menu
else
    case $1 in
        docker)
            deploy_docker
            ;;
        heroku)
            deploy_heroku
            ;;
        gcp|gcloud)
            deploy_gcp
            ;;
        aws)
            deploy_aws
            ;;
        *)
            echo "Usage: $0 [docker|heroku|gcp|aws]"
            exit 1
            ;;
    esac
fi
