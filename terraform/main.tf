module "website" {
  source  = "damienjburks/secure-static-site/aws"
  version = "1.2.10"

  bucket_name             = "${var.bucket_name}-${data.aws_caller_identity.current.account_id}"
  enable_domain           = true
  logging_enabled         = true
  enable_failover         = true
  enable_replication      = true
  enable_security_headers = true
  content_security_policy = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.googletagmanager.com https://*.google-analytics.com https://cloudflareinsights.com https://static.cloudflareinsights.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https: https://*.google-analytics.com https://*.googletagmanager.com https://img.shields.io https://api.visitorbadge.io https://raw.githubusercontent.com https://*.githubusercontent.com; frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com; connect-src 'self' https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com https://cloudflareinsights.com"
  enable_spa_routing      = true
  create_route53_zone     = true
  enable_waf              = true
  primary_region          = var.primary_region
  failover_region         = var.failover_region

  security_notification_email = "info@devsecblueprint.com"
  domain_name                 = "devsecblueprint.com"

  tags = {
    Environment = "Production"
    ManagedBy   = "Terraform Cloud"
  }
}

# Google Workspace MX records (for email)
resource "aws_route53_record" "mx" {
  zone_id = module.website.route53_zone_id
  name    = "devsecblueprint.com"
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
  zone_id = module.website.route53_zone_id
  name    = "devsecblueprint.com"
  type    = "TXT"
  ttl     = 300
  records = [
    "google-site-verification=xHeqrDv2asGBQ_nD-v1VeMVG6BtaNjzk0Do7uEvzumw"
  ]
}

# Spreadshop ACME challenge validation
resource "aws_route53_record" "acme_challenge_shop" {
  zone_id = module.website.route53_zone_id
  name    = "_acme-challenge.shop.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["na1887483.myspreadshop-validations.com"]
}

# Spreadshop subdomain
resource "aws_route53_record" "shop" {
  zone_id = module.website.route53_zone_id
  name    = "shop.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["cdn.myspreadshop.com"]
}

# Staging (Development) Environment
resource "aws_route53_record" "staging" {
  zone_id = module.website.route53_zone_id
  name    = "staging.devsecblueprint.com"
  type    = "A"
  alias {
    name = "d1xqoizz9drza.cloudfront.net."
    zone_id = "Z2FDTNDATAQYW2"
    evaluate_target_health = true
  }
}
resource "aws_route53_record" "staging_api" {
  zone_id = module.website.route53_zone_id
  name    = "api-staging.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["d-pamefw0o7l.execute-api.us-east-2.amazonaws.com"]
}
resource "aws_route53_record" "staging_api_cert" {
  zone_id = module.website.route53_zone_id
  name    = "_bf3fffcae7a708c326c9295997669de0.api-staging.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["_707d4a872ca3b975dd8666ccd8ce5ade.jkddzztszm.acm-validations.aws."]
}
resource "aws_route53_record" "staging_cert" {
  zone_id = module.website.route53_zone_id
  name    = "_21c1b79fe9f1ddb04cccba1d43781b60.staging.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["_81900aa9a3471da298fb44b59918dec8.jkddzztszm.acm-validations.aws."]
}

# Mailgun
resource "aws_route53_record" "mg_include_all" {
  zone_id = module.website.route53_zone_id
  name    = "mg.devsecblueprint.com"
  type    = "TXT"
  ttl     = 300
  records = ["v=spf1 include:mailgun.org ~all"]
}

resource "aws_route53_record" "mx_domainkey_txt" {
  zone_id = module.website.route53_zone_id
  name    = "mx._domainkey.mg.devsecblueprint.com"
  type    = "TXT"
  ttl     = 300
  records = ["k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCn3BIAsfWUNEy2OOGqrDpsQLx0ryELBtB3YNEKPu0ZuNhDS/qZrfYPCAzxmjchoIsq4Vp9inxYIzr4aMjyuZzYW2KQOPo0qS6NzvB/9hYY4y95XnM5gXg+JD74XoBao14siKwTvzVTiQVrssgvOhvuewqZfapOiQ4A7eDhCbAbkQIDAQAB"]
}

resource "aws_route53_record" "mg_mx" {
  zone_id = module.website.route53_zone_id
  name    = "mg.devsecblueprint.com"
  type    = "MX"
  ttl     = 300
  records = ["10 mxa.mailgun.org","50 mxb.mailgun.org"]
}

resource "aws_route53_record" "mg_email_domain" {
  zone_id = module.website.route53_zone_id
  name    = "email.mg.devsecblueprint.com"
  type    = "CNAME"
  ttl     = 300
  records = ["mailgun.org"]
}