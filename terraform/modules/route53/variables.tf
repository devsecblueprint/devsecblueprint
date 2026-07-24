variable "domain_name" {
  description = "The domain name for the hosted zone (e.g., devsecblueprint.com)"
  type        = string
}

variable "frontend_subdomain" {
  description = "Subdomain for frontend (empty string for apex domain, e.g., 'staging' for staging.devsecblueprint.com)"
  type        = string
  default     = ""
}

variable "api_subdomain" {
  description = "Subdomain for API (e.g., 'api-staging' for api-staging.devsecblueprint.com)"
  type        = string
  default     = "api"
}

variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  type        = string
}

variable "cloudfront_zone_id" {
  description = "CloudFront distribution hosted zone ID"
  type        = string
}

variable "alb_dns_name" {
  description = "ALB DNS name for API routing"
  type        = string
}

variable "alb_zone_id" {
  description = "ALB hosted zone ID"
  type        = string
}

variable "tags" {
  description = "Tags to apply to Route53 resources"
  type        = map(string)
  default     = {}
}
