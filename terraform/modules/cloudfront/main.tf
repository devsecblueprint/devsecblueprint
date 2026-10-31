# Origin Access Control for S3
resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "s3-oac-${var.s3_bucket_id}"
  description                       = "Origin Access Control for S3 bucket ${var.s3_bucket_id}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Key Value Store with video preview metadata (slug -> {"t","d","i"}) for link-preview crawlers.
# Written at runtime by the backend; the CloudFront function reads it.
resource "aws_cloudfront_key_value_store" "video_edge" {
  name    = "video-edge-${var.s3_bucket_id}"
  comment = "Video preview metadata for social link unfurling"
}

# CloudFront Function to handle www redirect, legacy redirects, and append .html to requests
resource "aws_cloudfront_function" "url_rewrite" {
  name    = "url-rewrite-${var.s3_bucket_id}-v${var.cloudfront_function_version}"
  runtime = "cloudfront-js-2.0"
  comment = "Redirect www to apex, handle legacy Docusaurus routes, and append .html for static export"
  publish = true
  code    = file("${path.module}/url_rewrite.js")

  key_value_store_associations = [aws_cloudfront_key_value_store.video_edge.arn]

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

  security_headers_config {
    content_security_policy {
      content_security_policy = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.cloudflarestream.com https://embed.cloudflarestream.com https://www.googletagmanager.com https://www.google-analytics.com; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: blob: https:; font-src 'self' data: https:; connect-src 'self' https:; frame-src https://iframe.videodelivery.net https://*.cloudflarestream.com https://www.youtube.com https://www.youtube-nocookie.com; frame-ancestors 'none'; media-src https://videodelivery.net https://*.cloudflarestream.com;"
      override                = true
    }

    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }

    xss_protection {
      mode_block = true
      protection = true
      override   = true
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

  # Custom error responses to serve 404.html for missing pages
  custom_error_response {
    error_code            = 403
    response_code         = 404
    response_page_path    = "/404.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 404
    response_page_path    = "/404.html"
    error_caching_min_ttl = 10
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
      },
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_id}",
          "arn:aws:s3:::${var.s3_bucket_id}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
