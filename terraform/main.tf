# DSB V3 Infrastructure
resource "random_id" "suffix" {
  byte_length = 4
}

# Secrets Manager for GitHub OAuth credentials
module "github_oauth" {
  source = "./modules/secrets"

  secret_name        = "dsb-platform-github-oauth-${random_id.suffix.id}"
  secret_description = "GitHub OAuth credentials for DSB V3"

  client_id     = var.TFC_CLIENT_ID
  client_secret = var.TFC_CLIENT_SECRET

  tags = var.common_tags
}

# Secrets Manager for GitLab OAuth credentials
module "gitlab_oauth" {
  source = "./modules/secrets"

  secret_name        = "dsb-platform-gitlab-oauth-${random_id.suffix.id}"
  secret_description = "GitLab OAuth credentials for DSB V3"

  client_id     = var.TFC_GITLAB_CLIENT_ID
  client_secret = var.TFC_GITLAB_CLIENT_SECRET

  tags = var.common_tags
}


# Secrets Manager for Bitbucket Cloud OAuth credentials
module "bitbucket_oauth" {
  source = "./modules/secrets"

  secret_name        = "dsb-platform-bitbucket-oauth-${random_id.suffix.id}"
  secret_description = "Bitbucket Cloud OAuth credentials for DSB V3"

  client_id     = var.TFC_BITBUCKET_CLIENT_ID
  client_secret = var.TFC_BITBUCKET_CLIENT_SECRET

  tags = var.common_tags
}

# Secrets Manager for Discord OAuth credentials
module "discord_oauth" {
  source = "./modules/secrets"

  secret_name        = "dsb-platform-discord-oauth-${random_id.suffix.id}"
  secret_description = "Discord OAuth credentials for DSB V3"

  client_id     = var.TFC_DISCORD_CLIENT_ID
  client_secret = var.TFC_DISCORD_CLIENT_SECRET

  tags = var.common_tags
}

# Secrets Manager for Discord Bot token
module "discord_bot" {
  source = "./modules/secrets"

  secret_name        = "dsb-platform-discord-bot-${random_id.suffix.id}"
  secret_description = "Discord Bot token for DSB V3"

  secret_key = var.TFC_DISCORD_BOT_TOKEN

  tags = var.common_tags
}

# Secrets Manager for Stripe secret key
module "stripe_secret_key" {
  source = "./modules/secrets"

  secret_name        = "dsb-platform-stripe-secret-key-${random_id.suffix.id}"
  secret_description = "Stripe secret key for DSB V3"

  secret_key = var.TFC_STRIPE_SECRET_KEY

  tags = var.common_tags
}

# Secrets Manager for Stripe webhook signing secret
module "stripe_webhook_secret" {
  source = "./modules/secrets"

  secret_name        = "dsb-platform-stripe-webhook-secret-${random_id.suffix.id}"
  secret_description = "Stripe webhook signing secret for DSB V3"

  secret_key = var.TFC_STRIPE_WEBHOOK_SECRET

  tags = var.common_tags
}

# Secrets Manager for JWT secret key
module "jwt_secret" {
  source = "./modules/secrets"

  secret_name        = "dsb-platform-jwt-secret-${random_id.suffix.id}"
  secret_description = "JWT secret key for session management"

  secret_key = var.TFC_SECRET_KEY

  tags = var.common_tags
}

# SSM Parameter Store for Mailgun API key
module "mailgun_api_key" {
  source = "./modules/ssm_parameter"

  parameter_name        = "/app/mailgun/api-key"
  parameter_description = "Mailgun API key for sending emails"
  parameter_value       = var.TFC_MAILGUN_API_KEY

  tags = var.common_tags
}

# DynamoDB tables for user data
module "dynamodb" {
  source = "./modules/dynamodb"

  progress_table_name   = "dsb-platform-progress"
  user_state_table_name = "dsb-platform-user-state"
  tags                  = var.common_tags
}

# DynamoDB table for membership, Discord identity, and Stripe data
module "dynamodb_membership" {
  source = "./modules/dynamodb_membership"

  table_name = "dsb-platform-membership"
  tags       = var.common_tags
}

# SQS FIFO queue for Discord role sync events
module "sqs_discord_sync" {
  source = "./modules/sqs_fifo"

  queue_name                 = "dsb-discord-sync"
  max_receive_count          = 3
  visibility_timeout_seconds = 180
  tags                       = var.common_tags
}

# IAM role for membership Lambda execution
module "iam_membership" {
  source = "./modules/iam_membership"

  role_name            = "dsb-platform-membership-lambda-execution"
  membership_table_arn = module.dynamodb_membership.table_arn
  secret_arns = [
    module.discord_oauth.secret_arn,
    module.discord_bot.secret_arn,
    module.stripe_secret_key.secret_arn,
    module.stripe_webhook_secret.secret_arn,
    module.jwt_secret.secret_arn
  ]
  sqs_queue_arn = module.sqs_discord_sync.queue_arn
  tags          = var.common_tags
}

# IAM role for Lambda execution
module "iam" {
  source = "./modules/iam"

  role_name                   = "dsb-platform-lambda-execution"
  progress_table_arn          = module.dynamodb.progress_table_arn
  user_state_table_arn        = module.dynamodb.user_state_table_arn
  testimonials_table_arn      = module.dynamodb.testimonials_table_arn
  notifications_table_arn     = module.dynamodb.notifications_table_arn
  secret_arn                  = [module.github_oauth.secret_arn, module.gitlab_oauth.secret_arn, module.bitbucket_oauth.secret_arn, module.jwt_secret.secret_arn]
  content_registry_bucket_arn = module.s3_content_registry.bucket_arn
  aws_region                  = data.aws_region.current.id
  aws_account_id              = data.aws_caller_identity.current.account_id
  tags                        = var.common_tags
}

# S3 bucket for content registry
module "s3_content_registry" {
  source = "./modules/s3_content_registry"

  bucket_name = "dsb-platform-content-registry-${data.aws_caller_identity.current.account_id}"
  tags        = var.common_tags
}

# Lambda layer for Python dependencies
module "lambda_layer" {
  source = "./modules/lambda_layer"

  layer_name          = "dsb-platform-dependencies"
  layer_zip_path      = "${path.module}/python_dependencies_layer.zip"
  compatible_runtimes = ["python3.13"]
  description         = "Python dependencies for DSB platform (requests, python-jose)"
}

# Lambda function for API backend
module "lambda" {
  source = "./modules/lambda"

  function_name      = "dsb-platform-api"
  description        = "DSB Platform API backend - handles authentication, progress tracking, and content delivery"
  runtime            = "python3.13"
  handler            = "handler.main"
  execution_role_arn = module.iam.lambda_role_arn
  source_code_path   = local.backend_zip_path
  layers             = [module.lambda_layer.layer_arn]

  environment_variables = {
    ADMIN_USERS                  = var.TFC_ADMIN_USERS
    PROGRESS_TABLE               = module.dynamodb.progress_table_name
    USER_STATE_TABLE             = module.dynamodb.user_state_table_name
    GITHUB_SECRET_NAME           = module.github_oauth.secret_name
    GITLAB_SECRET_NAME           = module.gitlab_oauth.secret_name
    JWT_SECRET_NAME              = module.jwt_secret.secret_name
    SESSION_TOKEN_LIFETIME_HOURS = 8
    GITHUB_CALLBACK_URL          = "https://${var.TFC_API_DOMAIN}/auth/github/callback"
    GITLAB_CALLBACK_URL          = "https://${var.TFC_API_DOMAIN}/auth/gitlab/callback"
    BITBUCKET_SECRET_NAME        = module.bitbucket_oauth.secret_name
    BITBUCKET_CALLBACK_URL       = "https://${var.TFC_API_DOMAIN}/auth/bitbucket/callback"
    FRONTEND_URL                 = "https://${var.TFC_FRONTEND_DOMAIN}/dashboard"
    FRONTEND_ORIGIN              = "https://${var.TFC_FRONTEND_DOMAIN}"
    CONTENT_REGISTRY_BUCKET      = module.s3_content_registry.bucket_name
    TOTAL_MODULE_PAGES           = tostring(var.total_module_pages)
    MAILGUN_DOMAIN               = var.mailgun_domain
    MAILGUN_PARAM_NAME           = module.mailgun_api_key.parameter_name
    TESTIMONIAL_NOTIFY_EMAIL     = "info@devsecblueprint.com"
    TESTIMONIALS_TABLE           = module.dynamodb.testimonials_table_name
    NOTIFICATIONS_TABLE          = module.dynamodb.notifications_table_name
  }

  tags = var.common_tags
}

# ACM certificates for custom domains (multi-region)
module "acm" {
  source = "./modules/acm"

  frontend_domain = var.TFC_FRONTEND_DOMAIN
  api_domain      = var.TFC_API_DOMAIN
  tags            = var.common_tags

  providers = {
    aws.us_east_1 = aws.us_east_1
  }
}

# Route53 validation records for CloudFront certificate
resource "aws_route53_record" "cloudfront_cert_validation" {
  for_each = {
    for dvo in module.acm.cloudfront_domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = module.route53.zone_id
}

# Route53 validation records for API certificate
resource "aws_route53_record" "api_cert_validation" {
  for_each = {
    for dvo in module.acm.api_domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = module.route53.zone_id
}

# Certificate validation for CloudFront
resource "aws_acm_certificate_validation" "cloudfront" {
  provider                = aws.us_east_1
  certificate_arn         = module.acm.cloudfront_certificate_arn
  validation_record_fqdns = [for record in aws_route53_record.cloudfront_cert_validation : record.fqdn]
}

# Certificate validation for API
resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = module.acm.api_certificate_arn
  validation_record_fqdns = [for record in aws_route53_record.api_cert_validation : record.fqdn]
}

# API Gateway HTTP API
module "api_gateway" {
  source = "./modules/api_gateway"

  api_name             = "dsb-platform-api"
  lambda_invoke_arn    = module.lambda.invoke_arn
  lambda_function_name = module.lambda.function_name
  acm_certificate_arn  = module.acm.api_certificate_arn
  custom_domain        = var.TFC_API_DOMAIN
  allowed_origins      = ["https://${var.TFC_FRONTEND_DOMAIN}"]
  tags                 = var.common_tags

  depends_on = [aws_acm_certificate_validation.api]
}

# S3 bucket for frontend static assets
module "s3_frontend" {
  source = "./modules/s3_frontend"

  bucket_name = "dsb-platform-frontend-${data.aws_caller_identity.current.account_id}"
  tags        = var.common_tags
}

# CloudFront distribution for frontend
module "cloudfront" {
  source = "./modules/cloudfront"

  s3_bucket_id                   = module.s3_frontend.bucket_id
  s3_bucket_regional_domain_name = module.s3_frontend.bucket_regional_domain_name
  acm_certificate_arn            = module.acm.cloudfront_certificate_arn
  custom_domain                  = var.TFC_FRONTEND_DOMAIN
  custom_domain_aliases          = ["www.${var.TFC_FRONTEND_DOMAIN}"]
  cloudfront_function_version    = 2
  tags                           = var.common_tags

  depends_on = [aws_acm_certificate_validation.cloudfront]
}

# Route53 hosted zone and DNS records
module "route53" {
  source = "./modules/route53"

  domain_name             = var.TFC_BASE_DOMAIN
  frontend_subdomain      = var.TFC_FRONTEND_DOMAIN
  api_subdomain           = var.TFC_API_DOMAIN
  cloudfront_domain_name  = module.cloudfront.distribution_domain_name
  cloudfront_zone_id      = "Z2FDTNDATAQYW2" # CloudFront hosted zone ID (constant for all distributions)
  api_gateway_domain_name = module.api_gateway.custom_domain_target
  api_gateway_zone_id     = module.api_gateway.custom_domain_hosted_zone_id
  tags                    = var.common_tags
}

# Google Workspace MX records (for email)
resource "aws_route53_record" "mx" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = var.TFC_BASE_DOMAIN
  type    = "MX"
  ttl     = 300
  records = [
    "1 aspmx.l.google.com",
    "5 alt1.aspmx.l.google.com",
    "5 alt2.aspmx.l.google.com",
    "10 alt3.aspmx.l.google.com",
    "10 alt4.aspmx.l.google.com"
  ]
}

# Google site verification TXT record
resource "aws_route53_record" "txt_verification" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "devsecblueprint.com"
  type    = "TXT"
  ttl     = 300
  records = [
    "google-site-verification=xHeqrDv2asGBQ_nD-v1VeMVG6BtaNjzk0Do7uEvzumw"
  ]
}

# Spreadshop ACME challenge validation
resource "aws_route53_record" "acme_challenge_shop" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "_acme-challenge.shop.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["na1887483.myspreadshop-validations.com"]
}

# Spreadshop subdomain
resource "aws_route53_record" "shop" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "shop.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["cdn.myspreadshop.com"]
}

# Mailgun
resource "aws_route53_record" "mg_include_all" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "mg.devsecblueprint.com"
  type    = "TXT"
  ttl     = 300
  records = ["v=spf1 include:mailgun.org ~all"]
}

resource "aws_route53_record" "mx_domainkey_txt" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "mx._domainkey.mg.devsecblueprint.com"
  type    = "TXT"
  ttl     = 300
  records = ["k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCn3BIAsfWUNEy2OOGqrDpsQLx0ryELBtB3YNEKPu0ZuNhDS/qZrfYPCAzxmjchoIsq4Vp9inxYIzr4aMjyuZzYW2KQOPo0qS6NzvB/9hYY4y95XnM5gXg+JD74XoBao14siKwTvzVTiQVrssgvOhvuewqZfapOiQ4A7eDhCbAbkQIDAQAB"]
}

resource "aws_route53_record" "mg_mx" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "mg.devsecblueprint.com"
  type    = "MX"
  ttl     = 300
  records = ["10 mxa.mailgun.org", "50 mxb.mailgun.org"]
}

resource "aws_route53_record" "mg_email_domain" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "email.mg.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["mailgun.org"]
}

# =============================================================================
# Membership Lambda & Integrations
# =============================================================================

# Lambda function for membership API (Discord identity, Stripe, sync)
module "lambda_membership" {
  source = "./modules/lambda"

  function_name      = "dsb-platform-membership"
  description        = "DSB Platform Membership API - handles Discord identity, Stripe subscriptions, and role synchronization"
  runtime            = "python3.13"
  handler            = "handler.main"
  execution_role_arn = module.iam_membership.lambda_role_arn
  source_code_path   = local.membership_backend_zip_path
  layers             = [module.lambda_layer.layer_arn]

  environment_variables = {
    MEMBERSHIP_TABLE                = module.dynamodb_membership.table_name
    DISCORD_SECRET_NAME             = module.discord_oauth.secret_name
    DISCORD_BOT_SECRET_NAME         = module.discord_bot.secret_name
    STRIPE_SECRET_NAME              = module.stripe_secret_key.secret_name
    STRIPE_WEBHOOK_SECRET_NAME      = module.stripe_webhook_secret.secret_name
    JWT_SECRET_NAME                 = module.jwt_secret.secret_name
    DISCORD_SYNC_QUEUE_URL          = module.sqs_discord_sync.queue_url
    DISCORD_GUILD_ID                = var.TFC_DISCORD_GUILD_ID
    DISCORD_ROLE_FREE_ID            = var.TFC_DISCORD_ROLE_FREE_ID
    DISCORD_ROLE_EXPLORER_ID        = var.TFC_DISCORD_ROLE_EXPLORER_ID
    DISCORD_ROLE_BUILDER_ID         = var.TFC_DISCORD_ROLE_BUILDER_ID
    DISCORD_ROLE_BUILDER_ACADEMY_ID = var.TFC_DISCORD_ROLE_BUILDER_ACADEMY_ID
    FRONTEND_URL                    = "https://${var.TFC_FRONTEND_DOMAIN}"
    ADMIN_USERS                     = var.TFC_ADMIN_USERS
  }

  tags = var.common_tags
}

# API Gateway integration for membership Lambda
resource "aws_apigatewayv2_integration" "membership_lambda" {
  api_id                 = module.api_gateway.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = module.lambda_membership.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# API Gateway routes for Discord OAuth
resource "aws_apigatewayv2_route" "auth_discord_get" {
  api_id    = module.api_gateway.api_id
  route_key = "GET /auth/discord/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# API Gateway routes for Discord API (POST)
resource "aws_apigatewayv2_route" "api_discord_post" {
  api_id    = module.api_gateway.api_id
  route_key = "POST /api/discord/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# API Gateway routes for Discord API (GET)
resource "aws_apigatewayv2_route" "api_discord_get" {
  api_id    = module.api_gateway.api_id
  route_key = "GET /api/discord/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# API Gateway routes for Discord API (DELETE)
resource "aws_apigatewayv2_route" "api_discord_delete" {
  api_id    = module.api_gateway.api_id
  route_key = "DELETE /api/discord/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# API Gateway routes for Stripe API (POST)
resource "aws_apigatewayv2_route" "api_stripe_post" {
  api_id    = module.api_gateway.api_id
  route_key = "POST /api/stripe/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# API Gateway routes for Stripe API (GET)
resource "aws_apigatewayv2_route" "api_stripe_get" {
  api_id    = module.api_gateway.api_id
  route_key = "GET /api/stripe/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# API Gateway routes for Admin Discord (GET)
resource "aws_apigatewayv2_route" "admin_discord_get" {
  api_id    = module.api_gateway.api_id
  route_key = "GET /admin/discord/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# API Gateway routes for Admin Discord (POST)
resource "aws_apigatewayv2_route" "admin_discord_post" {
  api_id    = module.api_gateway.api_id
  route_key = "POST /admin/discord/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# API Gateway routes for Admin Discord (DELETE)
resource "aws_apigatewayv2_route" "admin_discord_delete" {
  api_id    = module.api_gateway.api_id
  route_key = "DELETE /admin/discord/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.membership_lambda.id}"
}

# Lambda permission for API Gateway to invoke membership Lambda
resource "aws_lambda_permission" "api_gateway_membership" {
  statement_id  = "AllowAPIGatewayInvokeMembership"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_membership.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${module.api_gateway.api_execution_arn}/*/*"
}

# SQS event source mapping for Discord sync queue
resource "aws_lambda_event_source_mapping" "sqs_discord_sync" {
  event_source_arn = module.sqs_discord_sync.queue_arn
  function_name    = module.lambda_membership.function_name
  batch_size       = 1
  enabled          = true
}

# IAM role for EventBridge Scheduler to invoke Lambda
resource "aws_iam_role" "scheduler_execution" {
  name = "dsb-platform-scheduler-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  name = "invoke-membership-lambda"
  role = aws_iam_role.scheduler_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = module.lambda_membership.function_arn
      }
    ]
  })
}

# EventBridge Scheduler rule for Discord role reconciliation (every 24 hours)
resource "aws_scheduler_schedule" "discord_reconciliation" {
  name       = "dsb-discord-reconciliation"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(24 hours)"

  target {
    arn      = module.lambda_membership.function_arn
    role_arn = aws_iam_role.scheduler_execution.arn

    input = jsonencode({
      source = "scheduler"
      action = "reconciliation"
    })
  }
}
