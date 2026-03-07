output "cloudfront_certificate_arn" {
  description = "ARN of the ACM certificate for CloudFront (us-east-1)"
  value       = aws_acm_certificate.cloudfront.arn
}

output "api_certificate_arn" {
  description = "ARN of the ACM certificate for API Gateway (us-east-2)"
  value       = aws_acm_certificate.api.arn
}

output "cloudfront_domain_validation_options" {
  description = "Domain validation options for CloudFront certificate"
  value       = aws_acm_certificate.cloudfront.domain_validation_options
}

output "api_domain_validation_options" {
  description = "Domain validation options for API certificate"
  value       = aws_acm_certificate.api.domain_validation_options
}
