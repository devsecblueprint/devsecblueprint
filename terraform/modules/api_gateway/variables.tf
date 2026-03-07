variable "api_name" {
  description = "Name of the API Gateway HTTP API"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Lambda function invoke ARN for API Gateway integration"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name for permission resource"
  type        = string
}

variable "acm_certificate_arn" {
  description = "Regional ACM certificate ARN (us-east-2) for custom domain"
  type        = string
}

variable "custom_domain" {
  description = "Custom domain name for the API (e.g., api.devsecblueprint.com)"
  type        = string
}

variable "allowed_origins" {
  description = "List of allowed origins for CORS configuration"
  type        = list(string)
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
