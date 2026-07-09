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

# SSM Parameter Store for Mailgun API key (deprecated — kept for state compatibility)
# TODO: Remove after confirming SES migration is stable
module "mailgun_api_key" {
  source = "./modules/ssm_parameter"

  parameter_name        = "/app/mailgun/api-key"
  parameter_description = "Mailgun API key (deprecated - migrated to SES)"
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

# S3 bucket for content registry
module "s3_content_registry" {
  source = "./modules/s3_content_registry"

  bucket_name = "dsb-platform-content-registry-${data.aws_caller_identity.current.account_id}"
  tags        = var.common_tags
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

  domain_name            = var.TFC_BASE_DOMAIN
  frontend_subdomain     = var.TFC_FRONTEND_DOMAIN
  api_subdomain          = var.TFC_API_DOMAIN
  cloudfront_domain_name = module.cloudfront.distribution_domain_name
  cloudfront_zone_id     = "Z2FDTNDATAQYW2" # CloudFront hosted zone ID (constant for all distributions)
  alb_dns_name           = module.alb.alb_dns_name
  alb_zone_id            = module.alb.alb_zone_id
  tags                   = var.common_tags
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

# SES custom MAIL FROM records
resource "aws_route53_record" "ses_mail_from_mx" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "noreply.devsecblueprint.com"
  type    = "MX"
  ttl     = 300
  records = ["10 feedback-smtp.us-east-2.amazonses.com"]
}

resource "aws_route53_record" "ses_mail_from_spf" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "noreply.devsecblueprint.com"
  type    = "TXT"
  ttl     = 300
  records = ["v=spf1 include:amazonses.com ~all"]
}

# SES DKIM verification records
resource "aws_route53_record" "ses_dkim_1" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "4p7hvxg7dpj2ler6di3vqnajanvvxgh5._domainkey.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["4p7hvxg7dpj2ler6di3vqnajanvvxgh5.dkim.amazonses.com"]
}

resource "aws_route53_record" "ses_dkim_2" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "tsclevsy2zi6mibg7pj6gak4x7ltpyxi._domainkey.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["tsclevsy2zi6mibg7pj6gak4x7ltpyxi.dkim.amazonses.com"]
}

resource "aws_route53_record" "ses_dkim_3" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "gzhv3ewjnhvvyynx2r46phdy5bgkmxbt._domainkey.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["gzhv3ewjnhvvyynx2r46phdy5bgkmxbt.dkim.amazonses.com"]
}

resource "aws_route53_record" "dmarc" {
  count   = local.is_dsb_platform ? 1 : 0
  zone_id = module.route53.zone_id
  name    = "_dmarc.devsecblueprint.com"
  type    = "TXT"
  ttl     = 300
  records = ["v=DMARC1; p=none;"]
}


# =============================================================================
# ALB for ECS Fargate service
# =============================================================================

module "alb" {
  source = "./modules/alb"

  vpc_id            = data.aws_vpc.default.id
  public_subnet_ids = data.aws_subnets.default.ids
  certificate_arn   = module.acm.api_certificate_arn
  project_name      = "dsb-platform"
  tags              = var.common_tags

  depends_on = [aws_acm_certificate_validation.api]
}

# =============================================================================
# ECR Repository for ECS container images
# =============================================================================

module "ecr" {
  source = "./modules/ecr"

  repository_name = "dsb-platform"
  tags            = var.common_tags
}

# =============================================================================
# IAM Roles for ECS (Execution + Task)
# =============================================================================

module "iam_ecs" {
  source = "./modules/iam_ecs"

  project_name       = "dsb-platform"
  ecr_repository_arn = module.ecr.repository_arn
  log_group_arn      = "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/dsb-platform"
  dynamodb_table_arns = [
    module.dynamodb.progress_table_arn,
    module.dynamodb.user_state_table_arn,
    module.dynamodb_membership.table_arn,
    module.dynamodb.testimonials_table_arn,
    module.dynamodb.notifications_table_arn,
    module.dynamodb.broadcasts_table_arn
  ]
  secrets_arns = [
    module.github_oauth.secret_arn,
    module.gitlab_oauth.secret_arn,
    module.bitbucket_oauth.secret_arn,
    module.discord_oauth.secret_arn,
    module.discord_bot.secret_arn,
    module.stripe_secret_key.secret_arn,
    module.stripe_webhook_secret.secret_arn,
    module.jwt_secret.secret_arn
  ]
  s3_bucket_arn = module.s3_content_registry.bucket_arn
  ssm_parameter_arns = [
    module.mailgun_api_key.parameter_arn
  ]
  tags = var.common_tags
}

# =============================================================================
# ECS Fargate Service
# =============================================================================

module "ecs" {
  source = "./modules/ecs"

  project_name          = "dsb-platform"
  vpc_id                = data.aws_vpc.default.id
  public_subnet_ids     = data.aws_subnets.default.ids
  alb_security_group_id = module.alb.alb_security_group_id
  target_group_arn      = module.alb.target_group_arn
  execution_role_arn    = module.iam_ecs.execution_role_arn
  task_role_arn         = module.iam_ecs.task_role_arn
  ecr_repository_url    = module.ecr.repository_url
  image_tag             = var.image_tag
  aws_region            = data.aws_region.current.id

  environment_variables = {
    # From dsb-platform-api Lambda
    ADMIN_USERS                  = var.TFC_ADMIN_USERS
    PROGRESS_TABLE               = module.dynamodb.progress_table_name
    USER_STATE_TABLE             = module.dynamodb.user_state_table_name
    GITHUB_SECRET_NAME           = module.github_oauth.secret_name
    GITLAB_SECRET_NAME           = module.gitlab_oauth.secret_name
    JWT_SECRET_NAME              = module.jwt_secret.secret_name
    SESSION_TOKEN_LIFETIME_HOURS = "8"
    GITHUB_CALLBACK_URL          = "https://${var.TFC_API_DOMAIN}/auth/github/callback"
    GITLAB_CALLBACK_URL          = "https://${var.TFC_API_DOMAIN}/auth/gitlab/callback"
    BITBUCKET_SECRET_NAME        = module.bitbucket_oauth.secret_name
    BITBUCKET_CALLBACK_URL       = "https://${var.TFC_API_DOMAIN}/auth/bitbucket/callback"
    FRONTEND_URL                 = "https://${var.TFC_FRONTEND_DOMAIN}/dashboard"
    FRONTEND_ORIGIN              = "https://${var.TFC_FRONTEND_DOMAIN}"
    CONTENT_REGISTRY_BUCKET      = module.s3_content_registry.bucket_name
    TOTAL_MODULE_PAGES           = tostring(var.total_module_pages)
    SES_SENDER_EMAIL             = "noreply@devsecblueprint.com"
    SES_REGION                   = "us-east-2"
    TESTIMONIAL_NOTIFY_EMAIL     = "info@devsecblueprint.com"
    TESTIMONIALS_TABLE           = module.dynamodb.testimonials_table_name
    NOTIFICATIONS_TABLE          = module.dynamodb.notifications_table_name
    BROADCASTS_TABLE             = module.dynamodb.broadcasts_table_name

    # From dsb-platform-membership Lambda
    MEMBERSHIP_TABLE                = module.dynamodb_membership.table_name
    DISCORD_SECRET_NAME             = module.discord_oauth.secret_name
    DISCORD_BOT_SECRET_NAME         = module.discord_bot.secret_name
    STRIPE_SECRET_NAME              = module.stripe_secret_key.secret_name
    STRIPE_WEBHOOK_SECRET_NAME      = module.stripe_webhook_secret.secret_name
    DISCORD_GUILD_ID                = var.TFC_DISCORD_GUILD_ID
    DISCORD_ROLE_FREE_ID            = var.TFC_DISCORD_ROLE_FREE_ID
    DISCORD_ROLE_EXPLORER_ID        = var.TFC_DISCORD_ROLE_EXPLORER_ID
    DISCORD_ROLE_BUILDER_ID         = var.TFC_DISCORD_ROLE_BUILDER_ID
    DISCORD_ROLE_BUILDER_ACADEMY_ID = var.TFC_DISCORD_ROLE_BUILDER_ACADEMY_ID
    DISCORD_CALLBACK_URL            = "https://${var.TFC_API_DOMAIN}/auth/discord/callback"
  }

  tags = var.common_tags
}


