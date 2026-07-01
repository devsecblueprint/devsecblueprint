# Terraform Variables
variable "TFC_CLIENT_ID" {
  description = "Github Client ID"
}

variable "TFC_CLIENT_SECRET" {
  description = "Github Client Secret"
}

variable "TFC_GITLAB_CLIENT_ID" {
  description = "GitLab Client ID"
}

variable "TFC_GITLAB_CLIENT_SECRET" {
  description = "Gitlab Client Secret"
}

variable "TFC_BITBUCKET_CLIENT_ID" {
  description = "Bitbucket Cloud Client ID"
}

variable "TFC_BITBUCKET_CLIENT_SECRET" {
  description = "Bitbucket Cloud Client Secret"
}

variable "TFC_DISCORD_CLIENT_ID" {
  description = "Discord OAuth Client ID"
  type        = string
}

variable "TFC_DISCORD_CLIENT_SECRET" {
  description = "Discord OAuth Client Secret"
  type        = string
  sensitive   = true
}

variable "TFC_DISCORD_BOT_TOKEN" {
  description = "Discord Bot token for guild management"
  type        = string
  sensitive   = true
}

variable "TFC_STRIPE_SECRET_KEY" {
  description = "Stripe secret API key"
  type        = string
  sensitive   = true
}

variable "TFC_STRIPE_WEBHOOK_SECRET" {
  description = "Stripe webhook signing secret"
  type        = string
  sensitive   = true
}

variable "TFC_SECRET_KEY" {

}

variable "TFC_ADMIN_USERS" {
  description = "Comma-separated list of provider:username pairs with admin access (e.g. github:damienjburks,gitlab:damienjburks). Bare usernames without a provider prefix are treated as github."
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

variable "TFC_DISCORD_GUILD_ID" {
  description = "Discord Guild (server) ID for role synchronization"
  type        = string
}

variable "TFC_DISCORD_ROLE_FREE_ID" {
  description = "Discord Role ID for the FREE membership tier"
  type        = string
}

variable "TFC_DISCORD_ROLE_EXPLORER_ID" {
  description = "Discord Role ID for the EXPLORER membership tier"
  type        = string
}

variable "TFC_DISCORD_ROLE_BUILDER_ID" {
  description = "Discord Role ID for the BUILDER membership tier"
  type        = string
}

variable "TFC_DISCORD_ROLE_BUILDER_ACADEMY_ID" {
  description = "Discord Role ID for the BUILDER_ACADEMY membership tier"
  type        = string
}
