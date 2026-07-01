variable "role_name" {
  description = "Name of the IAM role for membership Lambda execution"
  type        = string
}

variable "membership_table_arn" {
  description = "ARN of the membership DynamoDB table"
  type        = string
}

variable "secret_arns" {
  description = "List of Secrets Manager secret ARNs to grant access to"
  type        = list(string)
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS FIFO queue for Discord sync events"
  type        = string
}

variable "tags" {
  description = "Tags to apply to IAM resources"
  type        = map(string)
  default     = {}
}
