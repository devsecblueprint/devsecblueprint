variable "s3_bucket_id" {
  description = "S3 bucket ID for CloudFront origin"
  type        = string
}

variable "s3_bucket_regional_domain_name" {
  description = "S3 bucket regional domain name for CloudFront origin"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN from us-east-1 for CloudFront"
  type        = string
}

variable "custom_domain" {
  description = "Custom domain for CloudFront distribution (e.g., devsecblueprint.com)"
  type        = string
}

variable "custom_domain_aliases" {
  description = "Additional domain aliases for CloudFront (e.g., www.devsecblueprint.com)"
  type        = list(string)
  default     = []
}

variable "cloudfront_function_version" {
  description = "Version number for CloudFront function (increment to force recreation)"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
