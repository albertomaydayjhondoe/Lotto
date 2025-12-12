#!/bin/bash

# =============================================
# Railway Deployment Script
# Stakazo Production Deployment
# =============================================

set -e  # Exit on error

echo "🚀 Stakazo Railway Deployment Script"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================
# Helper Functions
# =============================================

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
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

# =============================================
# Check Prerequisites
# =============================================

print_step "Checking prerequisites..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    print_error "Railway CLI not found!"
    echo "Install it with: npm install -g @railway/cli"
    echo "Or: brew install railway"
    exit 1
fi

print_success "Railway CLI found"

# Check if logged in
if ! railway whoami &> /dev/null; then
    print_error "Not logged in to Railway!"
    echo "Run: railway login"
    exit 1
fi

print_success "Logged in to Railway as: $(railway whoami)"

# =============================================
# Generate Secrets
# =============================================

print_step "Generating production secrets..."

# Generate SECRET_KEY (32 bytes)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
print_success "Generated SECRET_KEY"

# Generate CREDENTIALS_ENCRYPTION_KEY (Fernet key)
CREDENTIALS_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
print_success "Generated CREDENTIALS_ENCRYPTION_KEY"

# Generate NEXTAUTH_SECRET (32 bytes base64)
NEXTAUTH_SECRET=$(openssl rand -base64 32)
print_success "Generated NEXTAUTH_SECRET"

echo ""
print_warning "Save these secrets securely:"
echo "SECRET_KEY=$SECRET_KEY"
echo "CREDENTIALS_ENCRYPTION_KEY=$CREDENTIALS_ENCRYPTION_KEY"
echo "NEXTAUTH_SECRET=$NEXTAUTH_SECRET"
echo ""
read -p "Press Enter to continue..."

# =============================================
# Create Railway Project
# =============================================

print_step "Creating Railway project..."

read -p "Enter project name (default: stakazo-prod): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-stakazo-prod}

# Check if project exists
if railway list 2>/dev/null | grep -q "$PROJECT_NAME"; then
    print_warning "Project '$PROJECT_NAME' already exists"
    read -p "Use existing project? (y/n): " USE_EXISTING
    if [ "$USE_EXISTING" != "y" ]; then
        print_error "Deployment cancelled"
        exit 1
    fi
else
    railway init --name "$PROJECT_NAME"
    print_success "Created project: $PROJECT_NAME"
fi

# Link to project
railway link "$PROJECT_NAME"

# =============================================
# Add PostgreSQL Database
# =============================================

print_step "Adding PostgreSQL database..."

if railway run --service postgres echo "exists" &> /dev/null; then
    print_warning "PostgreSQL service already exists"
else
    railway add --service postgres
    print_success "Added PostgreSQL database"
    
    # Wait for database to be ready
    print_step "Waiting for database to initialize (30s)..."
    sleep 30
fi

# =============================================
# Deploy Backend Service
# =============================================

print_step "Deploying Backend service..."

cd backend

# Set environment variables for backend
print_step "Setting backend environment variables..."

railway variables set \
    SECRET_KEY="$SECRET_KEY" \
    CREDENTIALS_ENCRYPTION_KEY="$CREDENTIALS_ENCRYPTION_KEY" \
    PYTHONUNBUFFERED="1" \
    DEBUG_ENDPOINTS_ENABLED="false" \
    WORKER_ENABLED="true" \
    WORKER_POLL_INTERVAL="2" \
    MAX_JOB_RETRIES="3" \
    AI_LLM_MODE="stub" \
    AI_WORKER_ENABLED="false" \
    VIDEO_STORAGE_DIR="/app/storage/videos" \
    TELEMETRY_INTERVAL_SECONDS="5" \
    --service backend

print_success "Backend environment variables set"

# Deploy backend
print_step "Deploying backend to Railway..."
railway up --service backend --detach

print_success "Backend deployed"

# Run migrations
print_step "Running database migrations..."
railway run --service backend alembic upgrade head
print_success "Migrations completed"

cd ..

# =============================================
# Deploy Dashboard Service
# =============================================

print_step "Deploying Dashboard service..."

cd dashboard

# Get backend URL (will be set after backend is deployed)
BACKEND_URL=$(railway domain --service backend 2>/dev/null || echo "https://stakazo-backend.up.railway.app")

# Set environment variables for dashboard
print_step "Setting dashboard environment variables..."

railway variables set \
    NEXT_PUBLIC_API_BASE_URL="$BACKEND_URL/api" \
    NEXTAUTH_SECRET="$NEXTAUTH_SECRET" \
    NODE_ENV="production" \
    PORT="3000" \
    NEXT_TELEMETRY_DISABLED="1" \
    --service dashboard

print_success "Dashboard environment variables set"

# Deploy dashboard
print_step "Deploying dashboard to Railway..."
railway up --service dashboard --detach

print_success "Dashboard deployed"

cd ..

# =============================================
# Enable Public Domains
# =============================================

print_step "Enabling public domains..."

# Generate domains for services
railway domain --service backend
railway domain --service dashboard

BACKEND_DOMAIN=$(railway domain --service backend)
DASHBOARD_DOMAIN=$(railway domain --service dashboard)

print_success "Backend URL: $BACKEND_DOMAIN"
print_success "Dashboard URL: $DASHBOARD_DOMAIN"

# =============================================
# Update CORS Settings
# =============================================

print_step "Updating CORS settings..."

railway variables set \
    BACKEND_CORS_ORIGINS="[\"$DASHBOARD_DOMAIN\",\"$BACKEND_DOMAIN\"]" \
    --service backend

print_success "CORS settings updated"

# =============================================
# Deployment Summary
# =============================================

echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "📊 Service URLs:"
echo "  Backend:   $BACKEND_DOMAIN"
echo "  Dashboard: $DASHBOARD_DOMAIN"
echo ""
echo "🔍 Health Checks:"
echo "  Backend:   $BACKEND_DOMAIN/health"
echo "  Dashboard: $DASHBOARD_DOMAIN/api/health"
echo ""
echo "📝 Next Steps:"
echo "  1. Visit $DASHBOARD_DOMAIN to access the dashboard"
echo "  2. Check logs: railway logs --service backend"
echo "  3. Monitor services: railway status"
echo ""
echo "🔐 Secrets (save these securely):"
echo "  SECRET_KEY=$SECRET_KEY"
echo "  CREDENTIALS_ENCRYPTION_KEY=$CREDENTIALS_ENCRYPTION_KEY"
echo "  NEXTAUTH_SECRET=$NEXTAUTH_SECRET"
echo ""
echo "💰 Estimated Monthly Cost: ~$20-30 USD"
echo "  - PostgreSQL: ~$5"
echo "  - Backend: ~$5-10"
echo "  - Dashboard: ~$5-10"
echo "  - Bandwidth: ~$0-5"
echo ""

# =============================================
# Run Health Checks
# =============================================

print_step "Running health checks..."

sleep 10  # Wait for services to start

# Check backend health
if curl -f -s "$BACKEND_DOMAIN/health" > /dev/null; then
    print_success "Backend health check passed"
else
    print_error "Backend health check failed"
    echo "Check logs with: railway logs --service backend"
fi

# Check dashboard health
if curl -f -s "$DASHBOARD_DOMAIN/api/health" > /dev/null; then
    print_success "Dashboard health check passed"
else
    print_error "Dashboard health check failed"
    echo "Check logs with: railway logs --service dashboard"
fi

echo ""
print_success "Deployment script completed!"
