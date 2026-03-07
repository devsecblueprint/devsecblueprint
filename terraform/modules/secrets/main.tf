resource "aws_secretsmanager_secret" "this" {
  name        = var.secret_name
  description = var.secret_description

  tags = var.tags
}

# Create secret version with conditional structure
resource "aws_secretsmanager_secret_version" "this" {
  secret_id = aws_secretsmanager_secret.this.id
  secret_string = var.secret_key != "" ? jsonencode({
    secret_key = var.secret_key
    }) : jsonencode({
    client_id     = var.client_id
    client_secret = var.client_secret
  })
}
