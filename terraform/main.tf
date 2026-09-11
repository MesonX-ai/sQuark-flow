terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      CreatedBy   = "Terraform"
    }
  }
}

# Data source for Lambda deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../build"
  output_path = "${path.module}/../lambda_deployment.zip"
}

# ==================== DynamoDB Tables ====================

# Workflows Table
resource "aws_dynamodb_table" "workflows" {
  name           = "${var.app_name}-workflows"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "workspace_id"
  range_key      = "workflow_id"
  stream_specification {
    stream_view_type = "NEW_AND_OLD_IMAGES"
  }

  attribute {
    name = "workspace_id"
    type = "S"
  }

  attribute {
    name = "workflow_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "workspace_created_index"
    hash_key        = "workspace_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "Workflows Table"
  }
}

# Executions Table
resource "aws_dynamodb_table" "executions" {
  name           = "${var.app_name}-executions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "execution_id"
  range_key      = "workflow_id"
  stream_specification {
    stream_view_type = "NEW_AND_OLD_IMAGES"
  }

  attribute {
    name = "execution_id"
    type = "S"
  }

  attribute {
    name = "workflow_id"
    type = "S"
  }

  attribute {
    name = "workspace_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "workspace_status_index"
    hash_key        = "workspace_id"
    range_key       = "status"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "Executions Table"
  }
}

# Audit Logs Table
resource "aws_dynamodb_table" "audit_logs" {
  name           = "${var.app_name}-audit-logs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "workspace_id"
  range_key      = "timestamp"
  stream_specification {
    stream_view_type = "NEW_AND_OLD_IMAGES"
  }

  attribute {
    name = "workspace_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "Audit Logs Table"
  }
}

# Templates Table
resource "aws_dynamodb_table" "templates" {
  name           = "${var.app_name}-templates"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "template_id"
  range_key      = "version"

  attribute {
    name = "template_id"
    type = "S"
  }

  attribute {
    name = "version"
    type = "N"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "Templates Table"
  }
}

# ==================== IAM Role & Policy ====================

resource "aws_iam_role" "lambda_role" {
  name = "${var.app_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "dynamodb_access" {
  name        = "${var.app_name}-dynamodb-access"
  description = "Policy for Lambda to access DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.workflows.arn,
          aws_dynamodb_table.executions.arn,
          aws_dynamodb_table.audit_logs.arn,
          aws_dynamodb_table.templates.arn,
          "${aws_dynamodb_table.workflows.arn}/index/*",
          "${aws_dynamodb_table.executions.arn}/index/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}

# ==================== Lambda Function ====================

resource "aws_lambda_function" "api" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.app_name}-api"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_handler.handler"
  runtime         = "python3.12"
  architectures   = ["arm64"]
  memory_size     = var.lambda_memory_mb
  timeout         = var.lambda_timeout_seconds
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_WORKFLOWS_TABLE   = aws_dynamodb_table.workflows.name
      DYNAMODB_EXECUTIONS_TABLE  = aws_dynamodb_table.executions.name
      DYNAMODB_AUDIT_TABLE       = aws_dynamodb_table.audit_logs.name
      DYNAMODB_TEMPLATES_TABLE   = aws_dynamodb_table.templates.name
      UPSTASH_REDIS_URL          = var.upstash_redis_url
      UPSTASH_REDIS_TOKEN        = var.upstash_redis_token
      CORS_ORIGINS               = var.cors_origins
      LOG_LEVEL                  = var.log_level
      ENVIRONMENT                = var.environment
    }
  }

  layers = []

  depends_on = [
    aws_iam_role_policy_attachment.lambda_dynamodb,
    aws_iam_role_policy_attachment.lambda_basic_execution
  ]

  tags = {
    Name = "Unified Backend API"
  }
}

# ==================== API Gateway ====================

resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.app_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = split(",", var.cors_origins)
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    allow_headers = ["*"]
    expose_headers = ["*"]
    max_age      = 86400
  }

  tags = {
    Name = "Unified Backend HTTP API"
  }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_method = "POST"
  payload_format_version = "2.0"
  target           = aws_lambda_function.api.arn
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationLatency = "$context.integration.latency"
      error          = "$context.error.message"
      errorType      = "$context.error.messageString"
    })
  }

  depends_on = [aws_cloudwatch_log_group.api_logs]

  tags = {
    Name = "Production Stage"
  }
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# ==================== CloudWatch Logs ====================

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.app_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "API Gateway Logs"
  }
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.app_name}-api"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "Lambda Function Logs"
  }
}

# ==================== CloudWatch Alarms ====================

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.app_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Alert when Lambda errors exceed threshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_read_capacity" {
  alarm_name          = "${var.app_name}-dynamodb-read-capacity"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ConsumedReadCapacityUnits"
  namespace           = "AWS/DynamoDB"
  period              = "60"
  statistic           = "Sum"
  threshold           = "40000"
  alarm_description   = "Alert when DynamoDB read capacity is high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.workflows.name
  }
}

# ==================== CloudWatch Dashboard ====================

resource "aws_cloudwatch_dashboard" "main" {
  count          = var.enable_monitoring ? 1 : 0
  dashboard_name = "${var.app_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", { stat = "Average" }],
            [".", "Errors", { stat = "Sum" }],
            [".", "Invocations", { stat = "Sum" }],
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Performance"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits"],
            [".", "ConsumedWriteCapacityUnits"],
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "DynamoDB Usage"
        }
      }
    ]
  })
}
