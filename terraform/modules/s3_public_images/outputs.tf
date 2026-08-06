output "bucket_id" {
  description = "The ID of the public images S3 bucket"
  value       = aws_s3_bucket.images.id
}

output "bucket_arn" {
  description = "The ARN of the public images S3 bucket"
  value       = aws_s3_bucket.images.arn
}

output "bucket_name" {
  description = "The name of the public images S3 bucket"
  value       = aws_s3_bucket.images.bucket
}

output "bucket_regional_domain_name" {
  description = "The regional domain name of the S3 bucket (for direct HTTPS access)"
  value       = aws_s3_bucket.images.bucket_regional_domain_name
}

output "bucket_website_url" {
  description = "The base URL for accessing images (https://<bucket>.s3.<region>.amazonaws.com)"
  value       = "https://${aws_s3_bucket.images.bucket_regional_domain_name}"
}
