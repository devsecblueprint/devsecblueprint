# S3 Content Registry Module

This Terraform module creates an S3 bucket for storing the content registry JSON file, which contains metadata and validation rules for all learning content (quizzes, modules, capstones, and walkthroughs).

## Features

- **Private Bucket**: All public access is blocked
- **Versioning Enabled**: Maintains version history of registry files
- **Encryption**: Server-side encryption with AES256
- **Lifecycle Rules**: Automatically deletes noncurrent versions after 30 days
- **IAM Policies**: Provides write policy for CI/CD build process

## Usage

```hcl
module "s3_content_registry" {
  source = "./modules/s3_content_registry"

  bucket_name = "content-registry-prod"
  tags = {
    Environment = "production"
    Project     = "dsb-platform"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| bucket_name | Name of the S3 bucket for content registry | string | n/a | yes |
| tags | Resource tags to apply to the S3 bucket | map(string) | {} | no |

## Outputs

| Name | Description |
|------|-------------|
| bucket_id | The ID of the content registry S3 bucket |
| bucket_arn | The ARN of the content registry S3 bucket |
| bucket_name | The name of the content registry S3 bucket |
| build_write_policy_arn | ARN of the IAM policy for CI/CD build process write access |

## IAM Policies

### Build Process Write Policy

The module creates an IAM policy that grants write access to the bucket for CI/CD build processes. This policy allows:

- `s3:PutObject` - Upload registry files
- `s3:PutObjectAcl` - Set object ACLs
- `s3:ListBucket` - List bucket contents
- `s3:DeleteObject` - Delete old versions

To use this policy, attach it to your CI/CD IAM user or role:

```bash
aws iam attach-user-policy \
  --user-name github-actions-user \
  --policy-arn <build_write_policy_arn>
```

### Lambda Read Policy

Lambda functions need read-only access to the bucket. This is configured in the `iam` module by passing the `content_registry_bucket_arn` variable.

## Bucket Structure

The bucket stores registry files with the following structure:

```
s3://content-registry-{environment}/
├── content-registry/
│   ├── latest.json                          # Always points to latest version
│   ├── v1.0.0-20240115-103000.json         # Versioned with timestamp
│   ├── v1.0.0-20240114-153000.json         # Previous version
│   └── v1.0.0-20240113-093000.json         # Older version
```

## Lifecycle Management

The module configures a lifecycle rule that automatically deletes noncurrent versions after 30 days. This keeps the bucket size manageable while maintaining recent version history for rollback purposes.

## Environment-Specific Buckets

Create separate buckets for each environment:

- **Development**: `content-registry-dev`
- **Staging**: `content-registry-staging`
- **Production**: `content-registry-prod`

## Security

- All public access is blocked
- Server-side encryption is enabled (AES256)
- Versioning is enabled for audit trail
- IAM policies follow least privilege principle
- No cross-account access is configured
