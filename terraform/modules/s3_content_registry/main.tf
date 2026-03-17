# IAM policy for CI/CD build process (write access)
resource "aws_iam_policy" "build_process_write" {
  name        = "${var.bucket_name}-build-write"
  description = "Allows CI/CD build process to write content registry to S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.content_registry.arn,
          "${aws_s3_bucket.content_registry.arn}/*"
        ]
      }
    ]
  })

  tags = var.tags
}

# S3 bucket for content registry
resource "aws_s3_bucket" "content_registry" {
  bucket        = var.bucket_name
  force_destroy = true
  tags          = var.tags
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
    bucket_key_enabled = true
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

resource "aws_s3_bucket_policy" "content_registry_tls_only" {
  bucket = aws_s3_bucket.content_registry.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.content_registry.arn,
          "${aws_s3_bucket.content_registry.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
