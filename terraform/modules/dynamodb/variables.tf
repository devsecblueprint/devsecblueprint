variable "progress_table_name" {
  description = "Name for the Progress DynamoDB table"
  type        = string
}

variable "user_state_table_name" {
  description = "Name for the User State DynamoDB table"
  type        = string
  default     = "dsb-platform-user-state"
}

variable "testimonials_table_name" {
  description = "Name for the Testimonials DynamoDB table"
  type        = string
  default     = "dsb-platform-testimonials"
}

variable "notifications_table_name" {
  description = "Name for the Notifications DynamoDB table"
  type        = string
  default     = "dsb-platform-notifications"
}

variable "tags" {
  description = "Tags to apply to DynamoDB tables"
  type        = map(string)
  default     = {}
}
