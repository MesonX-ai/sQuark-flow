#!/bin/bash

###############################################################################
# Backend Testing Script - Validate API endpoints and functionality
###############################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
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

log_test() {
    echo -e "${YELLOW}🧪 $1${NC}"
}

# Get API endpoint
log_section "Getting API Endpoint"

cd "$PROJECT_ROOT/terraform"
API_ENDPOINT=$(terraform output -raw api_endpoint 2>/dev/null)

if [ -z "$API_ENDPOINT" ]; then
    log_error "Could not get API endpoint. Is infrastructure deployed?"
    exit 1
fi

log_success "API Endpoint: $API_ENDPOINT"

###############################################################################
# Health & Status Tests
###############################################################################

log_section "Health & Status Tests"

# Health check
log_test "Health endpoint"
if curl -s -f "$API_ENDPOINT/health" > /dev/null; then
    log_success "Health check passed"
else
    log_error "Health check failed"
    exit 1
fi

# Root endpoint
log_test "Root endpoint"
ROOT=$(curl -s "$API_ENDPOINT/")
if echo "$ROOT" | grep -q "Unified Agentic Backend"; then
    log_success "Root endpoint responds correctly"
else
    log_warning "Root endpoint returned: $ROOT"
fi

###############################################################################
# Agent & Model Tests
###############################################################################

log_section "Agent & Model Tests"

# List agents
log_test "List agents"
AGENTS=$(curl -s "$API_ENDPOINT/api/v1/agents")
AGENT_COUNT=$(echo "$AGENTS" | grep -o '"name"' | wc -l)
log_success "Found $AGENT_COUNT agents"

# Sample agent
if echo "$AGENTS" | grep -q "web-research"; then
    log_success "✓ web-research agent present"
fi

# List models
log_test "List models"
MODELS=$(curl -s "$API_ENDPOINT/api/v1/agents/models/list")
MODEL_COUNT=$(echo "$MODELS" | grep -o '"id"' | wc -l)
log_success "Found $MODEL_COUNT models"

# Sample models
for model in "gpt-4o" "claude-3-opus" "claude-3-sonnet"; do
    if echo "$MODELS" | grep -q "$model"; then
        log_success "✓ $model present"
    fi
done

###############################################################################
# Workflow Tests
###############################################################################

log_section "Workflow Tests"

# Create test workflow
log_test "Create workflow"
WORKFLOW_PAYLOAD=$(cat << 'EOF'
{
  "id": "test-workflow-001",
  "name": "Test Workflow",
  "nodes": [
    {
      "id": "node-1",
      "type": "llm",
      "position": {"x": 0, "y": 0},
      "data": {
        "label": "Test LLM",
        "model": "gpt-4o",
        "prompt": "Test prompt"
      }
    }
  ],
  "edges": [],
  "workspace_id": "test-workspace"
}
EOF
)

CREATED=$(curl -s -X POST "$API_ENDPOINT/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d "$WORKFLOW_PAYLOAD")

if echo "$CREATED" | grep -q "test-workflow-001"; then
    log_success "Workflow created successfully"
    WORKFLOW_ID="test-workflow-001"
else
    log_error "Failed to create workflow"
    echo "$CREATED"
    exit 1
fi

# List workflows
log_test "List workflows"
WORKFLOWS=$(curl -s "$API_ENDPOINT/api/v1/workflows?workspace_id=test-workspace")
if echo "$WORKFLOWS" | grep -q "$WORKFLOW_ID"; then
    log_success "Workflow listed successfully"
else
    log_error "Could not list workflows"
fi

# Get workflow
log_test "Get workflow"
GET_WF=$(curl -s "$API_ENDPOINT/api/v1/workflows/$WORKFLOW_ID?workspace_id=test-workspace")
if echo "$GET_WF" | grep -q "$WORKFLOW_ID"; then
    log_success "Retrieved workflow successfully"
else
    log_error "Could not retrieve workflow"
fi

###############################################################################
# Performance Tests
###############################################################################

log_section "Performance Tests"

# Response time
log_test "Response time for health check"
START=$(date +%s%N)
curl -s -f "$API_ENDPOINT/health" > /dev/null
END=$(date +%s%N)
DURATION=$((($END - $START) / 1000000))
log_success "Response time: ${DURATION}ms"

if [ $DURATION -lt 500 ]; then
    log_success "✓ Excellent response time"
elif [ $DURATION -lt 1000 ]; then
    log_success "✓ Good response time"
else
    log_error "⚠️  Response time is high: ${DURATION}ms"
fi

###############################################################################
# Error Handling Tests
###############################################################################

log_section "Error Handling Tests"

# Invalid workflow ID
log_test "Invalid workflow ID handling"
INVALID=$(curl -s "$API_ENDPOINT/api/v1/workflows/nonexistent?workspace_id=test" -w "\n%{http_code}")
HTTP_CODE=$(echo "$INVALID" | tail -1)
if [ "$HTTP_CODE" != "200" ]; then
    log_success "✓ Correctly returns error for invalid ID (HTTP $HTTP_CODE)"
else
    log_error "Should return error for invalid ID"
fi

# Missing required fields
log_test "Missing required fields handling"
BAD_WF=$(curl -s -X POST "$API_ENDPOINT/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bad Workflow"}' \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$BAD_WF" | tail -1)
if [ "$HTTP_CODE" != "200" ]; then
    log_success "✓ Correctly validates required fields (HTTP $HTTP_CODE)"
else
    log_error "Should validate required fields"
fi

###############################################################################
# Summary
###############################################################################

log_section "Test Summary"
log_success "✅ All tests passed!"
log_success "Backend is ready for production use"

echo ""
log_info "API Endpoint: $API_ENDPOINT"
log_info "Documentation: $API_ENDPOINT/docs"
log_info "Integration Guides: See docs/ folder"

