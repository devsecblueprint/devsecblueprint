output "zone_id" {
  description = "Route53 hosted zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "zone_name" {
  description = "Route53 hosted zone name"
  value       = aws_route53_zone.main.name
}

output "name_servers" {
  description = "Name servers for the hosted zone"
  value       = aws_route53_zone.main.name_servers
}

output "frontend_fqdn" {
  description = "Fully qualified domain name for frontend"
  value       = aws_route53_record.frontend.fqdn
}

output "api_fqdn" {
  description = "Fully qualified domain name for API"
  value       = aws_route53_record.api.fqdn
}
