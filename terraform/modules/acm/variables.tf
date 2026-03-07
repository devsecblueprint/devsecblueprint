variable "frontend_domain" {
  description = "Frontend custom domain for CloudFront (e.g., devsecblueprint.com)"
  type        = string
}

variable "api_domain" {
  description = "API custom domain for API Gateway (e.g., api.devsecblueprint.com)"
  type        = string
}

variable "tags" {
  description = "Resource tags to apply to ACM certificates"
  type        = map(string)
  default     = {}
}
