variable "table_name" {
  description = "Name for the Membership DynamoDB table"
  type        = string
  default     = "dsb-platform-membership"
}

variable "tags" {
  description = "Tags to apply to the DynamoDB table"
  type        = map(string)
  default     = {}
}
