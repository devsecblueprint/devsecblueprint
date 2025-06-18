---
id: configuring-deployment-role
title: Configuring Deployment Role in AWS
sidebar_position: 4
---

## Overview

This guide walks you through setting up an IAM role in AWS that leverages OpenID Connect (OIDC), allowing Terraform Cloud to assume the role and deploy infrastructure changes on your behalf. Before continuing, ensure you have an AWS account ready for deployment.

## Step 1: Add Terraform Cloud as an OIDC Provider

1. Log in to your AWS account.
2. Navigate to the **IAM Dashboard**, go to **Identity Providers**, and click **Add Provider**.
3. Complete the form with the following details:

   - **Provider Type**: `OpenID Connect`
   - **Provider URL**: `https://app.terraform.io`
   - **Audience**: `aws.workload.identity`

   ![OIDC Provider Configuration](/img/projects/devsecops-pipeline-aws/setup/identity_provider.png)

## Step 2: Create an IAM Role for Terraform

1. In the **IAM Dashboard**, go to **Roles** and click **Create Role**.
2. Under **Trusted Entity Type**, select **Web Identity**.
3. Choose the `app.terraform.io` identity provider you just created.
4. Fill out the trust relationship using the fields below. These settings define which Terraform Cloud runs are allowed to assume this role, based on specific workload identity attributes:

   - **Workload Type**: `Workspace Run`  
     This indicates that only actual Terraform runs (not agents or other services) will be able to assume the role.

   - **Organization**: `DSB`  
     This should match the name of your Terraform Cloud organization. It restricts access to only runs that originate from this specific org.

   - **Project Name**: `AWS`  
     If you're using Terraform Cloud projects, this narrows the access scope to a particular project. You can update this to match the exact name you're using, or leave it open-ended depending on your structure.

   - **Workspace Name**: `*`  
     Using an asterisk allows any workspace within the specified organization and project to assume the role. If you prefer to scope this more tightly, you can replace the `*` with a specific workspace name.

   - **Run Phase**: `*`  
     This allows the role to be assumed during any phase of a run (plan, apply, etc). You can scope this more tightly if needed, but `*` is most flexible during development.

   > 💡 These trust conditions form the basis of your IAM role’s **assume role policy**. It ensures that only authorized Terraform runs from specific contexts can use this role to deploy resources into AWS.

   ![Trust Relationship Configuration](/img/projects/devsecops-pipeline-aws/setup/full_web_identity_form.png)

5. Attach the **AdministratorAccess** policy (or a scoped-down policy as needed for your environment).
6. Name the role `terraform-cloud-deployer-oidc` and create it.

After creating the role, note down the **Role ARN**. You’ll need this when configuring your Terraform Cloud workspace to assume the role using OIDC.
