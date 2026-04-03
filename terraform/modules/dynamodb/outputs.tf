output "progress_table_name" {
  description = "Progress table name"
  value       = aws_dynamodb_table.progress.name
}

output "progress_table_arn" {
  description = "Progress table ARN"
  value       = aws_dynamodb_table.progress.arn
}

output "user_state_table_name" {
  description = "User State table name"
  value       = aws_dynamodb_table.user_state.name
}

output "user_state_table_arn" {
  description = "User State table ARN"
  value       = aws_dynamodb_table.user_state.arn
}
