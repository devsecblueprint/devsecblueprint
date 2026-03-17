# Reference the pre-built backend.zip file
# Build this file using: invoke build-backend
locals {
  backend_zip_path = "${path.module}/backend.zip"
  is_dsb_platform  = terraform.workspace == "dsb-platform"
}

# Data source for AWS account ID
data "aws_caller_identity" "current" {}

# Data source for AWS region
data "aws_region" "current" {}
