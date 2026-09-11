#!/bin/bash

###############################################################################
# Unified Backend Deployment Script
# Checks in changes to GitHub and deploys to AWS Lambda + API Gateway
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_REMOTE="https://github.com/MesonX-ai/sQuark-flow.git"
AWS_REGION="us-east-2"
ENVIRONMENT="production"

###############################################################################
# Helper Functions
###############################################################################

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

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        exit 1
    fi
}

###############################################################################
# Validation
###############################################################################

validate_environment() {
    log_section "Validating Environment"
    
    check_command "git"
    check_command "aws"
    check_command "terraform"
    check_command "python3"
    check_command "pip"
    
    log_success "All required tools installed"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws login'"
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log_success "AWS Account: $ACCOUNT_ID"
    
    # Check Git repository
    if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not a Git repository"
        exit 1
    fi
    
    log_success "Git repository validated"
}

###############################################################################
# Git Operations
###############################################################################

git_check_in() {
    log_section "Checking In Changes to GitHub"
    
    cd "$PROJECT_ROOT"
    
    # Check for uncommitted changes
    if git diff-index --quiet HEAD --; then
        log_warning "No changes to commit"
        return 0
    fi
    
    # Show what will be committed
    log_info "Changes to commit:"
    git diff --stat
    
    # Stage all changes
    git add -A
    log_success "Staged all changes"
    
    # Commit
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    git commit -m "Deploy: $TIMESTAMP - Production deployment"
    log_success "Committed changes"
    
    # Push to GitHub
    log_info "Pushing to GitHub..."
    git push origin main
    log_success "Pushed to GitHub (main branch)"
    
    # Show commit log
    log_info "Latest commits:"
    git log --oneline -3
}

###############################################################################
# Build Lambda Package
###############################################################################

build_lambda_package() {
    log_section "Building Lambda Deployment Package"
    
    cd "$PROJECT_ROOT"
    
    if [ ! -f "build_lambda.sh" ]; then
        log_error "build_lambda.sh not found"
        exit 1
    fi
    
    chmod +x build_lambda.sh
    ./build_lambda.sh
    
    if [ ! -f "lambda_deployment.zip" ]; then
        log_error "Lambda deployment package not created"
        exit 1
    fi
    
    LAMBDA_SIZE=$(du -h lambda_deployment.zip | cut -f1)
    log_success "Lambda package built: $LAMBDA_SIZE"
}

###############################################################################
# Terraform Deployment
###############################################################################

terraform_deploy() {
    log_section "Deploying Infrastructure with Terraform"
    
    cd "$PROJECT_ROOT/terraform"
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    log_success "Terraform initialized"
    
    # Validate configuration
    log_info "Validating Terraform configuration..."
    terraform validate
    log_success "Configuration valid"
    
    # Plan deployment
    log_info "Planning deployment..."
    terraform plan -out=tfplan
    
    # Show plan
    log_warning "Review the plan above. Continue? (yes/no)"
    read -r response
    if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
        log_error "Deployment cancelled"
        exit 1
    fi
    
    # Apply deployment
    log_info "Applying Terraform configuration..."
    terraform apply tfplan
    log_success "Infrastructure deployed!"
    
    # Get outputs
    log_info "Deployment outputs:"
    terraform output -raw deployment_summary
}

###############################################################################
# Post-Deployment Verification
###############################################################################

verify_deployment() {
    log_section "Verifying Deployment"
    
    cd "$PROJECT_ROOT/terraform"
    
    # Get API endpoint
    API_ENDPOINT=$(terraform output -raw api_endpoint)
    log_success "API Endpoint: $API_ENDPOINT"
    
    # Health check
    log_info "Running health check..."
    if curl -s -f "$API_ENDPOINT/health" > /dev/null; then
        log_success "✅ Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
    
    # Get agents
    log_info "Fetching available agents..."
    AGENTS=$(curl -s "$API_ENDPOINT/api/v1/agents" | grep -o '"name":"[^"]*"' | wc -l)
    log_success "✅ Found $AGENTS agents"
    
    # Get models
    log_info "Fetching available models..."
    MODELS=$(curl -s "$API_ENDPOINT/api/v1/agents/models/list" | grep -o '"id":"[^"]*"' | wc -l)
    log_success "✅ Found $MODELS LLM models"
}

###############################################################################
# Documentation
###############################################################################

print_integration_guide() {
    log_section "Integration Guide"
    
    cd "$PROJECT_ROOT/terraform"
    API_ENDPOINT=$(terraform output -raw api_endpoint)
    
    cat << EOF

Your unified backend is deployed and ready! 🚀

${GREEN}API Endpoint:${NC}
  $API_ENDPOINT

${GREEN}Next Steps:${NC}

1️⃣  MyFamilyAssistant.ai Integration
   📖 See: docs/INTEGRATE_MYFAMILY.md
   🔧 Tech: Next.js 14 + React Flow
   
2️⃣  sQuark.ai Integration  
   📖 See: docs/INTEGRATE_SQUARK_AI.md
   🔧 Tech: Next.js 15 + React Flow
   
3️⃣  sQuark AI Browser Integration
   📖 See: docs/INTEGRATE_SQUARK_BROWSER.md
   🔧 Tech: PyQt6 Desktop App

${GREEN}Quick Test Commands:${NC}

  # Health check
  curl $API_ENDPOINT/health
  
  # List agents
  curl $API_ENDPOINT/api/v1/agents | jq .
  
  # List models
  curl $API_ENDPOINT/api/v1/agents/models/list | jq .
  
  # Swagger UI (if accessible)
  open "$API_ENDPOINT/docs"

${GREEN}Monitor & Debug:${NC}

  # View logs
  aws logs tail /aws/lambda/unified-backend --follow
  
  # View metrics
  aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Duration \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Average

${YELLOW}Save this endpoint:${NC}
  export UNIFIED_BACKEND_URL=$API_ENDPOINT

EOF
}

###############################################################################
# Main Deployment Flow
###############################################################################

main() {
    log_section "🚀 Unified Backend Deployment"
    log_info "Start time: $(date)"
    
    # Step 1: Validate
    validate_environment
    
    # Step 2: Git check-in
    git_check_in
    
    # Step 3: Build Lambda package
    build_lambda_package
    
    # Step 4: Deploy infrastructure
    terraform_deploy
    
    # Step 5: Verify
    verify_deployment
    
    # Step 6: Show integration guide
    print_integration_guide
    
    log_section "✨ Deployment Complete!"
    log_info "End time: $(date)"
}

###############################################################################
# Error Handler
###############################################################################

trap 'log_error "Deployment failed at line $LINENO"; exit 1' ERR

###############################################################################
# Run Main
###############################################################################

main "$@"
