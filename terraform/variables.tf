variable "bucket_name" {
  type        = string
  description = "Name for the S3 bucket (must be globally unique)"
  default     = "devsecblueprint-ui"
}

variable "aws_region" {
  type        = string
  description = "Default AWS region"
  default     = "us-east-1"
}

variable "primary_region" {
  type        = string
  description = "Primary AWS region for S3 bucket"
  default     = "us-east-1"
}

variable "failover_region" {
  type        = string
  description = "Failover AWS region for S3 bucket"
  default     = "us-west-2"
}