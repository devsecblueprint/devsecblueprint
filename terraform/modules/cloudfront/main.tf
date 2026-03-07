# Origin Access Control for S3
resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "s3-oac-${var.s3_bucket_id}"
  description                       = "Origin Access Control for S3 bucket ${var.s3_bucket_id}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Function to handle www redirect and append .html to requests
resource "aws_cloudfront_function" "url_rewrite" {
  name    = "url-rewrite-${var.s3_bucket_id}-v${var.cloudfront_function_version}"
  runtime = "cloudfront-js-2.0"
  comment = "Redirect www to apex and append .html to requests for static export"
  publish = true
  code    = <<-EOT
function handler(event) {
    var request = event.request;
    var host = request.headers.host.value;
    
    // Redirect www to apex domain
    if (host.startsWith('www.')) {
        var apexDomain = host.substring(4);
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                'location': { value: 'https://' + apexDomain + request.uri }
            }
        };
    }
    
    var uri = request.uri;
    
    // Check if URI already has an extension
    if (!uri.includes('.')) {
        // Check if URI ends with /
        if (uri.endsWith('/')) {
            request.uri = uri + 'index.html';
        } else {
            request.uri = uri + '.html';
        }
    }
    
    return request;
}
EOT

  lifecycle {
    create_before_destroy = true
  }
}

# Response Headers Policy to disable caching
resource "aws_cloudfront_response_headers_policy" "no_cache" {
  name    = "no-cache-policy-${var.s3_bucket_id}"
  comment = "Disable caching for HTML files to ensure users get latest code"

  custom_headers_config {
    items {
      header   = "Cache-Control"
      value    = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
      override = true
    }
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"
  aliases             = concat([var.custom_domain], var.custom_domain_aliases)

  origin {
    domain_name              = var.s3_bucket_regional_domain_name
    origin_id                = "S3-${var.s3_bucket_id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3_oac.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${var.s3_bucket_id}"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.url_rewrite.arn
    }

    # Disable caching for HTML files to ensure users get latest code
    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0

    # Add cache control headers
    response_headers_policy_id = aws_cloudfront_response_headers_policy.no_cache.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = var.tags
}

# S3 Bucket Policy to allow CloudFront OAC access
resource "aws_s3_bucket_policy" "cloudfront_oac" {
  bucket = var.s3_bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "arn:aws:s3:::${var.s3_bucket_id}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}
