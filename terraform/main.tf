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