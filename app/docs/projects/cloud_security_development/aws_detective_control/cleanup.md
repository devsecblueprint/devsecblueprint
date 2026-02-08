---
id: cleanup
title: Clean Up
description: Clean up AWS resources created for the detective control.
sidebar_position: 5
---

## Overview

Once you’ve completed testing, it’s important to clean up the AWS resources created for this detective control.

This guide walks through safely tearing down all Terraform-managed infrastructure to avoid unnecessary costs and ensure your environment is left in a clean state.

## Cleanup Steps

### 1. Destroy Terraform-Managed Resources

Navigate to the Terraform directory for the detective control and destroy all associated resources:

```bash
terraform destroy --auto-approve
```

This command removes all AWS resources created by Terraform, including:

- Lambda function
- EventBridge rule
- SNS topic and subscriptions
- CloudTrail resources
- IAM roles and policies

### 2. Verify Resource Deletion

After the destroy operation completes, verify that all resources have been removed:

- Review the Terraform output for successful destruction.
- Check the AWS Management Console to confirm that no related resources remain.

## Conclusion

You’ve successfully completed the project and cleaned up all associated resources.

Properly tearing down infrastructure after testing:

- Prevents unexpected AWS charges
- Reduces resource sprawl
- Keeps your environments clean and manageable

This step is just as important as deployment and testing when building real-world security controls.
