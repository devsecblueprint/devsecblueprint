# Reference the pre-built backend.zip file
# Build this file using: invoke build-backend
locals {
  backend_zip_path = "${path.module}/backend.zip"
}

# Data source for AWS account ID
data "aws_caller_identity" "current" {}

# Data source for AWS region
data "aws_region" "current" {}
