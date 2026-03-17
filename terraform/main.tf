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

  progress_table_name = "dsb-platform-progress"
  tags                = var.common_tags
}

# IAM role for Lambda execution
module "iam" {
  source = "./modules/iam"

  role_name                   = "dsb-platform-lambda-execution"
  progress_table_arn          = module.dynamodb.progress_table_arn
  secret_arn                  = [module.github_oauth.secret_arn, module.jwt_secret.secret_arn]
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
    PROGRESS_TABLE               = module.dynamodb.progress_table_name
    GITHUB_SECRET_NAME           = module.github_oauth.secret_name
    JWT_SECRET_NAME              = module.jwt_secret.secret_name
    SESSION_TOKEN_LIFETIME_HOURS = 8
    GITHUB_CALLBACK_URL          = "https://${var.TFC_API_DOMAIN}/auth/github/callback"
    FRONTEND_URL                 = "https://${var.TFC_FRONTEND_DOMAIN}/dashboard"
    FRONTEND_ORIGIN              = "https://${var.TFC_FRONTEND_DOMAIN}"
    CONTENT_REGISTRY_BUCKET      = module.s3_content_registry.bucket_name
    TOTAL_MODULE_PAGES           = tostring(var.total_module_pages)
    MAILGUN_DOMAIN               = var.mailgun_domain
    MAILGUN_PARAM_NAME           = module.mailgun_api_key.parameter_name
    SUCCESS_STORY_TO_EMAIL       = "info@devsecblueprint.com"
    ADMIN_USERS                  = var.TFC_ADMIN_USERS
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