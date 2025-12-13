module "website" {
  source  = "damienjburks/secure-static-site/aws"
  version = "1.1.1"

  bucket_name             = "${var.bucket_name}-${data.aws_caller_identity.current.account_id}"
  enable_domain           = true
  logging_enabled         = true
  enable_failover         = true
  enable_replication      = true
  enable_security_headers = true
  enable_spa_routing      = true
  create_route53_zone     = true
  primary_region          = var.primary_region
  failover_region         = var.failover_region

  domain_name = "devsecblueprint.com"

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

# Custom security headers policy to allow YouTube embeds
resource "aws_cloudfront_response_headers_policy" "security_headers" {
  name = "devsecblueprint-security-headers"
  
  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
    }
    
    content_type_options {
      override = true
    }
    
    frame_options {
      frame_option = "SAMEORIGIN"  # Allow framing from same origin
    }
    
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
    }
    
    content_security_policy {
      content_security_policy = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' *.googletagmanager.com *.google-analytics.com *.cloudflareinsights.com static.cloudflareinsights.com; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https: *.google-analytics.com *.googletagmanager.com img.shields.io api.visitorbadge.io raw.githubusercontent.com *.githubusercontent.com; frame-src 'self' *.youtube.com *.youtube-nocookie.com https:; child-src 'self' *.youtube.com *.youtube-nocookie.com https:; connect-src 'self' *.google-analytics.com *.analytics.google.com *.googletagmanager.com *.cloudflareinsights.com;"
      override = true
    }
  }
}