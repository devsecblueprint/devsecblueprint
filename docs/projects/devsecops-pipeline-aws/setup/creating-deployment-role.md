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

   - **Provider Type**: OpenID Connect
   - **Provider URL**: `https://app.terraform.io`
   - **Audience**: `aws.workload.identity`

   ![OIDC Provider Configuration](/img/projects/devsecops-pipeline-aws/setup/identity_provider.png)

## Step 2: Create an IAM Role for Terraform

1. In the **IAM Dashboard**, go to **Roles** and click **Create Role**.
2. Under **Trusted Entity Type**, select **Web Identity**.
3. Choose the `app.terraform.io` identity provider you just created.
4. Fill out the trust relationship as follows:

   - **Workload Type**: Workspace Run
   - **Organization**: `DSB`
   - **Project Name**: `AWS`
   - **Workspace Name**: `*`
   - **Run Phase**: `*`

   ![Trust Relationship Configuration](/img/projects/devsecops-pipeline-aws/setup/full_web_identity_form.png)

5. Attach the **AdministratorAccess** policy (or a scoped-down policy as needed for your environment).
6. Name the role `terraform-cloud-deployer-oidc` and create it.

After creating the role, note down the **Role ARN**. You’ll need this when configuring your Terraform Cloud workspace to assume the role using OIDC.
