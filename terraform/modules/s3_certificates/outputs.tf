output "bucket_name" {
  description = "Name of the certificates S3 bucket"
  value       = aws_s3_bucket.certificates.bucket
}

output "bucket_arn" {
  description = "ARN of the certificates S3 bucket"
  value       = aws_s3_bucket.certificates.arn
}

output "bucket_id" {
  description = "ID of the certificates S3 bucket"
  value       = aws_s3_bucket.certificates.id
}
