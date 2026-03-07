output "progress_table_name" {
  description = "Progress table name"
  value       = aws_dynamodb_table.progress.name
}

output "progress_table_arn" {
  description = "Progress table ARN"
  value       = aws_dynamodb_table.progress.arn
}
