# ECS Module Variables

variable "project_name" {
  description = "Name of the project, used for naming resources"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC where ECS resources will be deployed"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for the ECS service"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID of the ALB (for inbound rule)"
  type        = string
}

variable "target_group_arn" {
  description = "ARN of the ALB target group for the ECS service"
  type        = string
}

variable "execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "ecr_repository_url" {
  description = "URL of the ECR repository for the container image"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "environment_variables" {
  description = "Map of environment variables to inject into the container"
  type        = map(string)
  default     = {}
}

variable "aws_region" {
  description = "AWS region for CloudWatch Logs configuration"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
