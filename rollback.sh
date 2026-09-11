#!/bin/bash

###############################################################################
# Rollback Script - Revert to previous infrastructure state
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

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

###############################################################################
# Main Rollback Flow
###############################################################################

log_section "🔄 Infrastructure Rollback"

log_warning "This will revert to the previous Git commit and destroy the latest Terraform deployment"
log_warning "WARNING: This will destroy AWS resources created in the latest deployment!"
log_info "Continue? (type 'yes' to confirm)"

read -r CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log_info "Rollback cancelled"
    exit 0
fi

# Rollback Terraform
log_section "Rolling Back Terraform Deployment"

cd "$PROJECT_ROOT/terraform"

# Check if there's a previous state
if [ ! -f "terraform.tfstate" ]; then
    log_error "No terraform.tfstate found - nothing to rollback"
    exit 1
fi

log_info "Checking Terraform state..."
RESOURCES=$(terraform state list 2>/dev/null | wc -l)
log_info "Current resources in state: $RESOURCES"

if [ $RESOURCES -gt 0 ]; then
    log_warning "This will destroy the following resources:"
    terraform state list
    
    log_info "Destroying infrastructure... (this may take a few minutes)"
    terraform destroy -auto-approve
    log_success "Infrastructure destroyed"
else
    log_info "No resources to destroy"
fi

# Rollback Git
log_section "Rolling Back Git Commit"

cd "$PROJECT_ROOT"

# Get previous commit
CURRENT_COMMIT=$(git rev-parse --short HEAD)
PREVIOUS_COMMIT=$(git rev-parse --short HEAD~1)

log_info "Current commit: $CURRENT_COMMIT"
log_info "Previous commit: $PREVIOUS_COMMIT"

# Soft reset to keep files
git reset --soft HEAD~1
log_success "Reset to previous commit (files preserved)"

# Option to hard reset
log_warning "Keep current changes? (yes/no)"
read -r KEEP_CHANGES
if [ "$KEEP_CHANGES" != "yes" ]; then
    log_info "Discarding local changes..."
    git reset --hard HEAD
    log_success "Hard reset complete"
fi

# Don't force push - let user decide
log_info "To push rollback to GitHub, run:"
log_info "  git push origin main --force-with-lease"

log_section "✅ Rollback Complete!"
log_warning "Note: Remote GitHub may still have the latest commit. Force push if needed."

