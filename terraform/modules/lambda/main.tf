# Lambda Module
# Creates Lambda function with CloudWatch log group

resource "aws_lambda_function" "api" {
  filename         = var.source_code_path
  function_name    = var.function_name
  role             = var.execution_role_arn
  handler          = var.handler
  runtime          = var.runtime
  source_code_hash = filebase64sha256(var.source_code_path)
  layers           = var.layers

  timeout = 120 # 2 minutes

  environment {
    variables = var.environment_variables
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 7

  tags = var.tags
}
