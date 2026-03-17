# Terraform Variables
variable "TFC_CLIENT_ID" {

}

variable "TFC_CLIENT_SECRET" {

}

variable "TFC_SECRET_KEY" {

}

variable "TFC_ADMIN_USERS" {
  description = "Comma-separated list of GitHub usernames with admin access"
  type        = string
}

variable "TFC_MAILGUN_API_KEY" {
  description = "Mailgun API key for sending emails"
  type        = string
  sensitive   = true
}

variable "TFC_FRONTEND_DOMAIN" {
  description = "Custom domain for the frontend CloudFront distribution"
  type        = string
  default     = "devsecblueprint.com"
}

variable "TFC_API_DOMAIN" {
  description = "Custom domain for the API Gateway"
  type        = string
  default     = "api.devsecblueprint.com"
}

variable "TFC_BASE_DOMAIN" {
  description = "Custom domain for the frontend CloudFront distribution"
  type        = string
  default     = "devsecblueprint.com"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    ManagedBy = "Terraform Cloud"
  }
}

variable "total_module_pages" {
  description = "Total number of module pages (automatically calculated from modules.json during deployment)"
  type        = number
}

variable "mailgun_domain" {
  description = "Mailgun domain for sending emails"
  type        = string
  default     = "mg.devsecblueprint.com"
}
