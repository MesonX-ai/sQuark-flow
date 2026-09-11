#!/bin/bash

###############################################################################
# Quick Deploy Script - Git Check-in + Terraform Apply Only
# Use this for faster deployments after build_lambda.sh has already run
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}▶ $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Quick Git Check-in
log_section "Quick Git Check-in"

cd "$PROJECT_ROOT"

# Check for changes
if git diff-index --quiet HEAD --; then
    log_info "No uncommitted changes"
else
    git add -A
    git commit -m "Quick deploy: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
    log_success "Pushed to GitHub"
fi

# Quick Terraform Deploy
log_section "Quick Terraform Apply"

cd "$PROJECT_ROOT/terraform"

# Plan
terraform plan -out=tfplan -auto-approve

# Apply
terraform apply tfplan

log_success "Infrastructure updated!"

# Get endpoint and verify
API_ENDPOINT=$(terraform output -raw api_endpoint)

log_section "Verification"
log_info "Testing health endpoint..."

if curl -s -f "$API_ENDPOINT/health" > /dev/null; then
    log_success "✅ API is healthy!"
    log_info "Endpoint: $API_ENDPOINT"
else
    log_error "Health check failed"
    exit 1
fi

log_success "🚀 Quick deployment complete!"
