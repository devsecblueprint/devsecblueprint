variable "progress_table_name" {
  description = "Name for the Progress DynamoDB table"
  type        = string
}

variable "tags" {
  description = "Tags to apply to DynamoDB tables"
  type        = map(string)
  default     = {}
}
