output "bucket_id" {
  description = "The ID of the content registry S3 bucket"
  value       = aws_s3_bucket.content_registry.id
}

output "bucket_arn" {
  description = "The ARN of the content registry S3 bucket"
  value       = aws_s3_bucket.content_registry.arn
}

output "bucket_name" {
  description = "The name of the content registry S3 bucket"
  value       = aws_s3_bucket.content_registry.bucket
}

output "build_write_policy_arn" {
  description = "ARN of the IAM policy for CI/CD build process write access"
  value       = aws_iam_policy.build_process_write.arn
}

output "bucket_region" {
  description = "The AWS region of the content registry S3 bucket"
  value       = aws_s3_bucket.content_registry.region
}
