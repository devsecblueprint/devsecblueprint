output "execution_role_arn" {
  description = "ARN of the ECS task execution role (used by ECS agent to pull images and send logs)"
  value       = aws_iam_role.ecs_execution.arn
}

output "task_role_arn" {
  description = "ARN of the ECS task role (used by the application container at runtime)"
  value       = aws_iam_role.ecs_task.arn
}
