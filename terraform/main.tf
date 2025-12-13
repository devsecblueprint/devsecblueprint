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

# Additional security considerations (optional)
# Uncomment if you want extra security measures

# resource "aws_s3_bucket_public_access_block" "additional_security" {
#   bucket = module.website.website_bucket_name
#   
#   block_public_acls       = true
#   block_public_policy     = true
#   ignore_public_acls      = true
#   restrict_public_buckets = true
# }

# resource "aws_cloudfront_response_headers_policy" "security_headers" {
#   name = "devsecblueprint-security-headers"
#   
#   security_headers_config {
#     strict_transport_security {
#       access_control_max_age_sec = 31536000
#       include_subdomains         = true
#       preload                    = true
#     }
#     
#     content_type_options {
#       override = true
#     }
#     
#     frame_options {
#       frame_option = "DENY"
#     }
#     
#     referrer_policy {
#       referrer_policy = "strict-origin-when-cross-origin"
#     }
#   }
# }