variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "unified-agentic-backend"
}

variable "upstash_redis_url" {
  description = "Upstash Redis URL"
  type        = string
  sensitive   = true
}

variable "upstash_redis_token" {
  description = "Upstash Redis token"
  type        = string
  sensitive   = true
}

variable "cors_origins" {
  description = "CORS allowed origins (comma-separated)"
  type        = string
  default     = "http://localhost:3000,http://localhost:3001,https://myfamilyassistant.ai,https://squark.ai,https://squark-web.ai"
}

variable "log_level" {
  description = "Logging level"
  type        = string
  default     = "INFO"
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "lambda_memory_mb" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "dynamodb_ttl_days" {
  description = "DynamoDB TTL in days"
  type        = number
  default     = 90
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Project = "unified-agentic-backend"
    Managed = "Terraform"
  }
}
