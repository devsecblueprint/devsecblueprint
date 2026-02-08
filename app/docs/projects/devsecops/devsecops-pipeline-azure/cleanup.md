---
id: cleanup
title: Clean Up
description: Clean up your Azure resources.
sidebar_position: 5
---

## Overview

Once you’ve finished working with the pipeline, it’s important to clean up your environment. This prevents unnecessary costs and ensures you leave no lingering resources in your Azure subscription.

This guide walks you through destroying the Terraform-defined infrastructure and verifying that everything has been removed.

## Steps

### 1. Destroy Terraform Resources

From the repository root, navigate into the Terraform directory and run the following command:

```bash
cd terraform/
terraform destroy --auto-approve
```

This will deprovision all resources that were created during the setup phase, including the Azure DevOps project and associated service connections.

:::important
Always double-check that you’re operating in the correct environment before running `destroy`. Running this in production could remove critical infrastructure.
:::

### 2. Verify Resource Deletion

After Terraform completes, verify that resources have been properly deleted:

- Log in to the **Azure Portal** and confirm that the project, pipelines, and container registry no longer exist.
- Review the **Terraform destroy logs** to ensure there were no errors or skipped resources.

:::note
Sometimes resource deletions may take a few minutes to fully propagate in the Azure Portal.
:::

## Conclusion

Congratulations! You’ve successfully completed the project and cleaned up all resources.

By tearing down your environment at the end, you:

- Avoid unexpected **Azure billing charges**.
- Keep your environment clean for future projects.
- Practice good cloud resource management habits.
