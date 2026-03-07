output "api_id" {
  description = "API Gateway HTTP API ID"
  value       = aws_apigatewayv2_api.api.id
}

output "api_endpoint" {
  description = "API Gateway invoke URL"
  value       = aws_apigatewayv2_api.api.api_endpoint
}

output "api_execution_arn" {
  description = "API Gateway execution ARN for Lambda permissions"
  value       = aws_apigatewayv2_api.api.execution_arn
}

output "custom_domain_name" {
  description = "Custom domain name for the API"
  value       = aws_apigatewayv2_domain_name.api.domain_name
}

output "custom_domain_target" {
  description = "Target domain for DNS configuration (A/AAAA record)"
  value       = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
}

output "custom_domain_hosted_zone_id" {
  description = "Hosted zone ID for the API Gateway custom domain"
  value       = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].hosted_zone_id
}
