output "function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

output "invoke_arn" {
  description = "Lambda invoke ARN for API Gateway"
  value       = aws_lambda_function.api.invoke_arn
}

output "function_version" {
  description = "Published version"
  value       = aws_lambda_function.api.version
}
