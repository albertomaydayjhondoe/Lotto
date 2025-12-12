#!/bin/bash

# =============================================
# Railway Health Check Script
# Verifies all services are running correctly
# =============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🏥 Railway Health Check"
echo "======================"
echo ""

# Get service URLs
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
# Get Service Domains
# =============================================

print_step "Getting service domains..."

BACKEND_DOMAIN=$(railway domain --service backend 2>/dev/null || echo "")
DASHBOARD_DOMAIN=$(railway domain --service dashboard 2>/dev/null || echo "")

if [ -z "$BACKEND_DOMAIN" ]; then
    print_error "Backend domain not found. Is the service deployed?"
    exit 1
fi

if [ -z "$DASHBOARD_DOMAIN" ]; then
    print_error "Dashboard domain not found. Is the service deployed?"
    exit 1
fi

print_success "Backend:   $BACKEND_DOMAIN"
print_success "Dashboard: $DASHBOARD_DOMAIN"
echo ""

# =============================================
# Backend Health Check
# =============================================

print_step "Checking backend health..."

BACKEND_HEALTH=$(curl -s -w "\n%{http_code}" "$BACKEND_DOMAIN/health" 2>/dev/null)
BACKEND_STATUS=$(echo "$BACKEND_HEALTH" | tail -n1)
BACKEND_BODY=$(echo "$BACKEND_HEALTH" | head -n-1)

if [ "$BACKEND_STATUS" = "200" ]; then
    print_success "Backend is healthy (HTTP $BACKEND_STATUS)"
    echo "$BACKEND_BODY" | jq '.' 2>/dev/null || echo "$BACKEND_BODY"
    
    # Check database connectivity
    if echo "$BACKEND_BODY" | jq -e '.database == "connected"' > /dev/null 2>&1; then
        print_success "Database connected"
    else
        print_warning "Database may not be connected"
    fi
else
    print_error "Backend health check failed (HTTP $BACKEND_STATUS)"
    echo "$BACKEND_BODY"
fi

echo ""

# =============================================
# Dashboard Health Check
# =============================================

print_step "Checking dashboard health..."

DASHBOARD_HEALTH=$(curl -s -w "\n%{http_code}" "$DASHBOARD_DOMAIN/api/health" 2>/dev/null)
DASHBOARD_STATUS=$(echo "$DASHBOARD_HEALTH" | tail -n1)
DASHBOARD_BODY=$(echo "$DASHBOARD_HEALTH" | head -n-1)

if [ "$DASHBOARD_STATUS" = "200" ]; then
    print_success "Dashboard is healthy (HTTP $DASHBOARD_STATUS)"
    echo "$DASHBOARD_BODY" | jq '.' 2>/dev/null || echo "$DASHBOARD_BODY"
else
    print_error "Dashboard health check failed (HTTP $DASHBOARD_STATUS)"
    echo "$DASHBOARD_BODY"
fi

echo ""

# =============================================
# API Endpoints Test
# =============================================

print_step "Testing API endpoints..."

# Test root endpoint
API_ROOT=$(curl -s -w "\n%{http_code}" "$BACKEND_DOMAIN/" 2>/dev/null)
API_ROOT_STATUS=$(echo "$API_ROOT" | tail -n1)

if [ "$API_ROOT_STATUS" = "200" ]; then
    print_success "API root endpoint working"
else
    print_error "API root endpoint failed (HTTP $API_ROOT_STATUS)"
fi

# Test OpenAPI docs
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_DOMAIN/docs" 2>/dev/null)

if [ "$DOCS_STATUS" = "200" ]; then
    print_success "OpenAPI docs accessible"
    echo "  📖 Docs: $BACKEND_DOMAIN/docs"
else
    print_warning "OpenAPI docs not accessible (HTTP $DOCS_STATUS)"
fi

echo ""

# =============================================
# Dashboard Pages Test
# =============================================

print_step "Testing dashboard pages..."

# Test dashboard root
DASHBOARD_ROOT=$(curl -s -o /dev/null -w "%{http_code}" "$DASHBOARD_DOMAIN/" 2>/dev/null)

if [ "$DASHBOARD_ROOT" = "200" ] || [ "$DASHBOARD_ROOT" = "307" ]; then
    print_success "Dashboard root accessible"
else
    print_warning "Dashboard root returned HTTP $DASHBOARD_ROOT"
fi

# Test dashboard login page
DASHBOARD_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" "$DASHBOARD_DOMAIN/login" 2>/dev/null)

if [ "$DASHBOARD_LOGIN" = "200" ]; then
    print_success "Dashboard login page accessible"
else
    print_warning "Dashboard login page returned HTTP $DASHBOARD_LOGIN"
fi

echo ""

# =============================================
# Service Status via Railway CLI
# =============================================

print_step "Checking Railway service status..."

railway status 2>/dev/null || print_warning "Railway CLI status not available"

echo ""

# =============================================
# Summary
# =============================================

echo "=========================================="
echo "📊 Health Check Summary"
echo "=========================================="
echo ""

if [ "$BACKEND_STATUS" = "200" ] && [ "$DASHBOARD_STATUS" = "200" ]; then
    print_success "All services are healthy! 🎉"
    echo ""
    echo "🌐 URLs:"
    echo "  Backend:   $BACKEND_DOMAIN"
    echo "  Dashboard: $DASHBOARD_DOMAIN"
    echo "  API Docs:  $BACKEND_DOMAIN/docs"
    echo ""
    echo "✅ Next steps:"
    echo "  1. Visit $DASHBOARD_DOMAIN to use the application"
    echo "  2. Check logs: railway logs --tail"
    echo "  3. Monitor metrics: railway metrics"
    exit 0
else
    print_error "Some services are not healthy"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "  1. Check logs: railway logs --service backend --tail"
    echo "  2. Check logs: railway logs --service dashboard --tail"
    echo "  3. Verify environment variables: railway variables --service backend"
    echo "  4. Restart services: railway restart --service backend"
    echo ""
    echo "📖 See DEPLOY_RAILWAY.md for more help"
    exit 1
fi
