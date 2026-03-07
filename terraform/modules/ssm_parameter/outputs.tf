output "parameter_name" {
  description = "Name of the SSM parameter"
  value       = aws_ssm_parameter.this.name
}

output "parameter_arn" {
  description = "ARN of the SSM parameter"
  value       = aws_ssm_parameter.this.arn
}
