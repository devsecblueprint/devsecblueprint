module "website" {
  source  = "damienjburks/secure-static-site/aws"
  version = "1.0.5"

  bucket_name             = "${var.bucket_name}-${data.aws_caller_identity.current.account_id}"
  enable_domain           = false
  logging_enabled         = true
  enable_failover         = true
  enable_replication      = true
  enable_security_headers = true
  create_route53_zone     = true
  primary_region          = var.primary_region
  failover_region         = var.failover_region

  domain_name = "devsecblueprint.com"

  tags = {
    Environment = "Production"
    ManagedBy   = "Terraform Cloud"
  }
}