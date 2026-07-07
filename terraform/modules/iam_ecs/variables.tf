variable "project_name" {
  description = "Project name prefix for IAM role naming"
  type        = string
}

variable "ecr_repository_arn" {
  description = "ARN of the ECR repository the execution role can pull from"
  type        = string
}

variable "log_group_arn" {
  description = "ARN of the CloudWatch Logs log group for ECS container logs"
  type        = string
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs the task role can access (progress, user-state, membership)"
  type        = list(string)
}

variable "secrets_arns" {
  description = "List of Secrets Manager secret ARNs the task role can read"
  type        = list(string)
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 content registry bucket the task role can read"
  type        = string
}

variable "ssm_parameter_arns" {
  description = "List of SSM Parameter Store ARNs the task role can access"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to all IAM resources"
  type        = map(string)
  default     = {}
}
