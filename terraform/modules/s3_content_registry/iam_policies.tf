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
