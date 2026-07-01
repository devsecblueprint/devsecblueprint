# DynamoDB Membership Module
# Creates the dsb-platform-membership table with GSIs, TTL, encryption, and PITR

resource "aws_dynamodb_table" "membership" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "discord_user_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "stripe_customer_id"
    type = "S"
  }

  # GSI1: Reverse Discord lookup (duplicate detection)
  # PK=discord_user_id, SK=user_id
  global_secondary_index {
    name            = "GSI1"
    hash_key        = "discord_user_id"
    range_key       = "user_id"
    projection_type = "ALL"
  }

  # GSI2: Stripe Customer → User resolution
  # PK=stripe_customer_id, SK=user_id
  global_secondary_index {
    name            = "GSI2"
    hash_key        = "stripe_customer_id"
    range_key       = "user_id"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}
