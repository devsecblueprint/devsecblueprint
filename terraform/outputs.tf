output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.website.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.website.cloudfront_distribution_id
}

output "website_bucket_name" {
  description = "Primary website S3 bucket name"
  value       = module.website.website_bucket_name
}

output "website_url" {
  description = "Website URL"
  value       = "https://${module.website.cloudfront_domain_name}"
}