---
id: detection-logic-and-infrastructure
title: Detection Logic & Infrastructure
sidebar_position: 3
---

## Overview

This section provides a detailed explanation of the control’s codebase. This project is a **Python-based AWS Lambda function** deployed with **Terraform**, designed to detect when an **Amazon S3 bucket becomes publicly accessible** and send an alert via **Amazon SNS**.

## Defining aws-event-driven-s3-public-detective-control

This project contains two major parts:

1. **`lambda_function.py`** — the detection logic that evaluates whether a bucket is publicly accessible.
2. **Terraform (`main.tf`, `providers.tf`, `variables.tf`)** — infrastructure that deploys CloudTrail, EventBridge, Lambda, and SNS so the control runs automatically.

For more details, review:

- `lambda_function.py` (Lambda detection logic)
- `main.tf` (Terraform infrastructure)

### Requirements

- **AWS CLI**: configured for an account you can deploy into
- **Terraform**: version `>= 1.0`
- **Python 3.11+**: for building / packaging dependencies (if you choose to package them)
- **AWS Services Used**
  - CloudTrail
  - EventBridge (CloudWatch Events)
  - Lambda
  - SNS
  - S3 (both as the monitored service and for CloudTrail log storage)

### Features

- **Event-Driven Detection**: triggers only on relevant S3 access-related API calls via CloudTrail + EventBridge
- **Current-State Evaluation**: confirms exposure by reading the bucket’s live configuration
- **Multi-Signal Checks**:
  - Public Access Block configuration
  - Bucket Policy public status
  - Bucket ACL grants for public groups
- **SNS Notifications**: sends a human-readable alert with actionable context
- **Terraform Deployment**: reproducible provisioning and teardown

### Project Structure

```bash
aws-event-driven-s3-public-detective-control/
├── main.tf                # Terraform: CloudTrail, SNS, IAM, Lambda, EventBridge wiring
├── providers.tf           # Terraform provider + Terraform Cloud workspace config
├── variables.tf           # Terraform variables (region + notification email)
├── lambda_function.py     # Lambda detection logic
├── requirements.txt       # Python deps (boto3 + python-dateutil)
├── lambda_function.zip    # Pre-built zip (present in repo)
└── README.md              # Setup notes (WIP)
```

### Setup and Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/devsecblueprint/aws-event-driven-s3-public-detective-control.git
cd aws-event-driven-s3-public-detective-control
```

#### 2. Configure Terraform Variables

Update values in `variables.tf` (or use `terraform.tfvars` if you prefer):

- `aws_region` (default: `us-east-1`)
- `notification_email` (default: `info@devsecblueprint.com`)

> SNS email subscriptions require confirmation. Watch for the “Confirm subscription” email.

#### 3. Initialize Terraform

```bash
terraform init
```

> Note: `providers.tf` is configured for **Terraform Cloud**:
>
> - Organization: `devsecblueprint`
> - Workspace: `aws-event-driven-s3-public-detective-control`
>
> If you’re not using Terraform Cloud, remove or adjust the `terraform { cloud { ... } }` block.

#### 4. Deploy the Control

```bash
terraform plan
terraform apply
```

After apply completes, the control will begin triggering on S3 access-related changes.

## Terraform Infrastructure

Terraform is responsible for provisioning the entire control plane needed for the detective control to work.

### What Terraform Creates

**CloudTrail + Log Bucket**

- A dedicated S3 bucket is created to store CloudTrail logs:

  - `aws_s3_bucket.trail_bucket`
- A bucket policy is applied to allow CloudTrail to write logs:

  - `aws_s3_bucket_policy.trail_bucket_policy`
- A CloudTrail trail is created:

  - `aws_cloudtrail.s3_trail`

**SNS Topic + Email Subscription**

- SNS topic for alerts:

  - `aws_sns_topic.s3_public_alerts`
- Email subscription:

  - `aws_sns_topic_subscription.email_subscription`

**Lambda IAM Role + Policy**

- Lambda execution role:

  - `aws_iam_role.lambda_role`
- Inline policy granting:

  - S3 read permissions used for checks
  - `sns:Publish` to the topic
  - CloudWatch Logs permissions
  - `aws_iam_policy.lambda_policy`
- Role attachment:

  - `aws_iam_role_policy_attachment.lambda_attach`

**Lambda Function**

- The function:

  - `aws_lambda_function.s3_public_alert`
- Environment variable injected:

  - `SNS_TOPIC_ARN`

**EventBridge Rule + Target**

- Rule triggers on CloudTrail API calls:

  - `PutBucketPolicy`
  - `PutBucketAcl`
  - `PutBucketPublicAccessBlock`
  - `DeletePublicAccessBlock`
- Target forwards events to Lambda:

  - `aws_cloudwatch_event_target.lambda_target`
- Permission allowing EventBridge to invoke Lambda:

  - `aws_lambda_permission.allow_eventbridge`

---

### Application Code Summary (Lambda)

The Lambda function (`lambda_function.py`) follows a simple flow:

1. Extracts the bucket name and identity details from the CloudTrail event
2. Evaluates the bucket for public exposure using three checks:

   - Public Access Block (`get_public_access_block`)
   - Bucket Policy status (`get_bucket_policy_status`)
   - Bucket ACL (`get_bucket_acl`) for public group grants
3. If any findings exist, publishes an SNS message including:

   - Bucket name
   - Account ID
   - Region
   - Actor ARN
   - Event name and timestamp
   - List of security findings

### Dependencies

The project includes a `requirements.txt`:

- `boto3>=1.26.0`
- `python-dateutil>=2.8.0`

### Notes

- **Packaging gotcha (important):**
  Terraform currently builds the zip like this:

  - `data "archive_file" "lambda_zip"` packages **only** `lambda_function.py`

  But the Lambda imports `python-dateutil`, which is **not included** in that zip unless you package dependencies yourself (or use a Lambda layer). If you deploy as-is, you may hit an import error at runtime.

  Fix options (pick one):

  - Bundle dependencies into the zip (vendor site-packages into the deployment package)
  - Use a Lambda Layer for `python-dateutil`
  - Remove the dependency and use Python’s standard library for ISO timestamps

- **Terraform Cloud:**
  `providers.tf` is configured to run via Terraform Cloud under the `devsecblueprint` org/workspace. If this is meant to be reusable by the community, consider documenting the “local Terraform” variant.

- **SNS Email Confirmation:**
  Email alerts won’t send until the subscription is confirmed.

- **CloudTrail Scope:**
  CloudTrail here is configured as a single-region trail and disables global service events. That’s fine for a reference control, but multi-account / multi-region rollouts should standardize this.

This setup keeps the control simple, deployable, and easy to reuse as the baseline pattern for future event-driven detective controls, and if you're up for the challenge, you can also create autoremediative controls using this pattern also.
