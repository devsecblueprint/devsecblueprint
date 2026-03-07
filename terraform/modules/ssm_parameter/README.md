# SSM Parameter Module

This module creates an AWS Systems Manager (SSM) Parameter Store parameter with SecureString encryption.

## Usage

```hcl
module "mailgun_api_key" {
  source = "./modules/ssm_parameter"

  parameter_name        = "/app/mailgun/api-key"
  parameter_description = "Mailgun API key for sending emails"
  parameter_value       = var.TFC_MAILGUN_API_KEY

  tags = var.common_tags
}
```

## Inputs

| Name | Description | Type | Required |
|------|-------------|------|----------|
| parameter_name | Name of the SSM parameter | string | yes |
| parameter_description | Description of the SSM parameter | string | no |
| parameter_value | Value of the SSM parameter (sensitive) | string | yes |
| tags | Tags to apply to the SSM parameter | map(string) | no |

## Outputs

| Name | Description |
|------|-------------|
| parameter_name | Name of the SSM parameter |
| parameter_arn | ARN of the SSM parameter |

## Notes

- The parameter is created as a SecureString type, which uses AWS KMS for encryption
- The Lambda IAM role already has permissions to read parameters under `/app/mailgun/*`
- The parameter value is marked as sensitive to prevent it from appearing in logs
