output "table_name" {
  description = "Membership table name"
  value       = aws_dynamodb_table.membership.name
}

output "table_arn" {
  description = "Membership table ARN"
  value       = aws_dynamodb_table.membership.arn
}
