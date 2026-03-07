# Infrastructure Outputs

# Frontend outputs
output "cloudfront_distribution_domain" {
  description = "CloudFront distribution domain name for the frontend"
  value       = module.cloudfront.distribution_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = module.s3_frontend.bucket_id
}

output "frontend_domain" {
  description = "Frontend custom domain"
  value       = var.frontend_domain
}

# API outputs
output "api_gateway_invoke_url" {
  description = "API Gateway invoke URL"
  value       = module.api_gateway.api_endpoint
}

output "api_gateway_custom_domain" {
  description = "API Gateway custom domain name"
  value       = module.api_gateway.custom_domain_name
}

# Lambda outputs
output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.lambda.function_name
}

# DynamoDB outputs
output "progress_table_name" {
  description = "DynamoDB Progress table name"
  value       = module.dynamodb.progress_table_name
}

# Secrets Manager outputs
output "github_secrets_arn" {
  description = "Secrets Manager secret ARN for GitHub OAuth credentials"
  value       = module.github_oauth.secret_arn
}

# Content Registry outputs
output "content_registry_bucket_name" {
  description = "S3 bucket name for content registry"
  value       = module.s3_content_registry.bucket_name
}

output "content_registry_bucket_arn" {
  description = "S3 bucket ARN for content registry"
  value       = module.s3_content_registry.bucket_arn
}

output "content_registry_bucket_region" {
  description = "S3 bucket region for content registry"
  value       = module.s3_content_registry.bucket_region
}

output "content_registry_build_policy_arn" {
  description = "IAM policy ARN for CI/CD build process to write to content registry bucket"
  value       = module.s3_content_registry.build_write_policy_arn
}

# Route53 Outputs
output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = module.route53.zone_id
}

output "route53_name_servers" {
  description = "Name servers for the hosted zone (update these at your domain registrar)"
  value       = module.route53.name_servers
}

output "frontend_fqdn" {
  description = "Frontend fully qualified domain name"
  value       = module.route53.frontend_fqdn
}

output "api_fqdn" {
  description = "API fully qualified domain name"
  value       = module.route53.api_fqdn
}
