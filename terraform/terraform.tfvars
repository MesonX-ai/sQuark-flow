# Terraform Variables for Unified Backend
# AWS Account: 873363353263 (sQuarkAI)

aws_region = "us-east-2"
environment = "production"
app_name = "unified-agentic-backend"

# Upstash Redis (from myfamilyassistant setup)
upstash_redis_url = "https://us1-fit-shark-873363353263.upstash.io"
upstash_redis_token = "AXM1AAIjZTAxZWJlOWQwNWY0NGE0YjkzNDQ0MDAxN2U1NTgyMDU0MwFsDGQDrQGiE7k=" # Replace with actual token

# CORS Configuration for 3 projects
cors_origins = "http://localhost:3000,http://localhost:3001,https://myfamilyassistant.ai,https://squark.ai,https://squark-web.ai"

# Logging
log_level = "INFO"
enable_monitoring = true
log_retention_days = 7

# Lambda Configuration
lambda_memory_mb = 512
lambda_timeout_seconds = 30

# DynamoDB
dynamodb_ttl_days = 90

# Tags
tags = {
  Project     = "unified-agentic-backend"
  Environment = "production"
  Account     = "sQuarkAI-873363353263"
  ManagedBy   = "Terraform"
}
