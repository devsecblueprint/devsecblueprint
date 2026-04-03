variable "progress_table_name" {
  description = "Name for the Progress DynamoDB table"
  type        = string
}

variable "user_state_table_name" {
  description = "Name for the User State DynamoDB table"
  type        = string
  default     = "dsb-platform-user-state"
}

variable "tags" {
  description = "Tags to apply to DynamoDB tables"
  type        = map(string)
  default     = {}
}
