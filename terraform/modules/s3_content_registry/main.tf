# S3 bucket for content registry
resource "aws_s3_bucket" "content_registry" {
  bucket = var.bucket_name
  tags   = var.tags
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "content_registry" {
  bucket = aws_s3_bucket.content_registry.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning
resource "aws_s3_bucket_versioning" "content_registry" {
  bucket = aws_s3_bucket.content_registry.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption (AES256)
resource "aws_s3_bucket_server_side_encryption_configuration" "content_registry" {
  bucket = aws_s3_bucket.content_registry.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle rule for noncurrent version expiration
resource "aws_s3_bucket_lifecycle_configuration" "content_registry" {
  bucket = aws_s3_bucket.content_registry.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
