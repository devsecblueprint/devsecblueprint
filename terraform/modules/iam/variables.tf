variable "role_name" {
  description = "Name of the IAM role for Lambda execution"
  type        = string
}

variable "progress_table_arn" {
  description = "ARN of the Progress DynamoDB table"
  type        = string
}

variable "user_state_table_arn" {
  description = "ARN of the User State DynamoDB table"
  type        = string
}

variable "testimonials_table_arn" {
  description = "ARN of the Testimonials DynamoDB table"
  type        = string
}

variable "secret_arn" {
  description = "ARN(s) of the Secrets Manager secret(s)"
  type        = list(string)
}

variable "content_registry_bucket_arn" {
  description = "ARN of the content registry S3 bucket"
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region for Parameter Store and KMS resources"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID for Parameter Store and KMS resources"
  type        = string
}

variable "tags" {
  description = "Tags to apply to IAM resources"
  type        = map(string)
  default     = {}
}
