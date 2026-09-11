output "api_endpoint" {
  description = "HTTP API endpoint"
  value       = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.default_stage.name}"
}

output "api_endpoint_raw" {
  description = "HTTP API endpoint (raw)"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "api_id" {
  description = "HTTP API ID"
  value       = aws_apigatewayv2_api.http_api.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

output "dynamodb_workflows_table" {
  description = "DynamoDB Workflows table name"
  value       = aws_dynamodb_table.workflows.name
}

output "dynamodb_executions_table" {
  description = "DynamoDB Executions table name"
  value       = aws_dynamodb_table.executions.name
}

output "dynamodb_audit_table" {
  description = "DynamoDB Audit Logs table name"
  value       = aws_dynamodb_table.audit_logs.name
}

output "dynamodb_templates_table" {
  description = "DynamoDB Templates table name"
  value       = aws_dynamodb_table.templates.name
}

output "cloudwatch_log_group_api" {
  description = "CloudWatch log group for API Gateway"
  value       = aws_cloudwatch_log_group.api_logs.name
}

output "cloudwatch_log_group_lambda" {
  description = "CloudWatch log group for Lambda"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "iam_role_arn" {
  description = "IAM role ARN for Lambda"
  value       = aws_iam_role.lambda_role.arn
}

output "deployment_summary" {
  description = "Deployment summary"
  value = {
    api_endpoint   = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.default_stage.name}"
    lambda_name    = aws_lambda_function.api.function_name
    lambda_memory  = aws_lambda_function.api.memory_size
    lambda_timeout = aws_lambda_function.api.timeout
    workflows_table = aws_dynamodb_table.workflows.name
    executions_table = aws_dynamodb_table.executions.name
    audit_table     = aws_dynamodb_table.audit_logs.name
    log_retention   = var.log_retention_days
    estimated_cost  = "< $50/month"
    features = [
      "Multi-tenant workflows",
      "Streaming execution",
      "Cost tracking",
      "Audit logging",
      "CORS configured",
      "9+ built-in agents",
      "Real-time updates"
    ]
  }
}

output "integration_guide_urls" {
  description = "Integration guide URLs"
  value = {
    myfamilyassistant = "docs/INTEGRATE_MYFAMILY.md"
    squark_ai         = "docs/INTEGRATE_SQUARK_AI.md"
    squark_web        = "docs/INTEGRATE_SQUARK.md"
  }
}
