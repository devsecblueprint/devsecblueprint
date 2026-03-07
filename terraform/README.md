# DSB V3 Terraform Infrastructure

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- Python 3.12
- pip

## Building Lambda Layer

Before deploying, you need to build the Lambda layer with Python dependencies:

```bash
cd terraform
./scripts/build_layer.sh
```

This will create `python_dependencies_layer.zip` containing:
- requests>=2.31.0
- python-jose[cryptography]>=3.3.0

Note: boto3 is excluded as it's already provided by the Lambda runtime.

## Deployment

1. Build the Lambda layer (see above)
2. Initialize Terraform:
   ```bash
   terraform init
   ```
3. Review the plan:
   ```bash
   terraform plan
   ```
4. Apply the infrastructure:
   ```bash
   terraform apply
   ```

## What Gets Deployed

- DynamoDB tables for user progress and state
- Lambda function with the backend code
- Lambda layer with Python dependencies
- API Gateway HTTP API
- S3 bucket for frontend
- CloudFront distribution
- ACM certificates for custom domains
- IAM roles and policies
- Secrets Manager for GitHub OAuth

## Layer Updates

If you update `requirements.txt`, rebuild the layer:
```bash
./scripts/build_layer.sh
terraform apply
```
