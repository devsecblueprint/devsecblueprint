---
id: cleanup
title: Clean Up
description: Clean up your AWS DevSecOps resources.
sidebar_position: 5
---

## Overview

With our environments configured and secrets created, it's time to clean up the Terraform-defined DevSecOps pipeline infrastructure. This guide provides a step-by-step explanation to ensure a proper cleanup of all resources.

## Steps

### 1. Destroy Repository Resources

Navigate to the repository Terraform directory and destroy the associated resources:

```bash
cd terraform/repositories
terraform destroy --auto-approve
```

### 2. Destroy EKS Cluster Resources

Navigate to the EKS cluster Terraform directory and destroy its resources:

```bash
cd terraform/eks-cluster
terraform destroy --auto-approve
```

### 3. Verify Resource Deletion

After running the destroy commands, verify that all resources have been deleted by:

- Checking the AWS Management Console.
- Reviewing Terraform logs for confirmation.

## Conclusion

Congratulations! You’ve successfully completed this project and cleaned up all resources. By properly tearing down your resources, you avoid unnecessary charges and ensure cost efficiency.
