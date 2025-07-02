---
id: configuring-deployment-user-gcp
title: Configuring Deployment Service Account in GCP
sidebar_position: 4
---

## Overview

This guide walks you through setting up a Google Cloud Platform (GCP) Service Account for **Terraform Cloud** deployments using **OIDC (OpenID Connect)** via **Workload Identity Federation (WIF)**. This setup allows Terraform Cloud to securely authenticate to GCP without relying on long-lived service account keys, ultimately enabling short-lived, scoped credentials per workspace.

> ✅ **Before you begin:** Ensure you have a GCP project available and sufficient permissions to create service accounts and manage IAM.

## Step 1: Create and Configure the Service Account

1. **Log in to your GCP account.**

2. In the left-hand menu, go to:  
   **IAM & Admin** → **Service Accounts**

3. Click **Create Service Account**, and fill in:
   - **Name**: `terraform-deployer`
   - **Description**: (optional)
   - Click **Create and Continue**

   ![Service Account Creation Screenshot](/img/projects/devsecops-pipeline-gcp/setup/service-account-creation.png)

4. **Grant the following roles** to the service account:
   - `Editor`
   - `Project IAM Admin`
   - `Role Administrator`
   - `Secret Manager Admin`
   - `Secret Manager Secret Accessor`
   - `IAM Service Account Token Creator`

5. Under **Grant users access to this service account**, leave it blank and click **Done**.

## Step 2: Configure Workload Identity Federation

1. In the GCP Console, go to **IAM & Admin** → **Workload Identity Federation**

2. Click **Create Pool** and enter the following:
   - **Pool Name**: `Terraform Cloud`
   - **Pool ID**: `terraform-cloud`
   - ✅ Check the box: **Enabled Provider**

3. In the same flow, add a new provider:
   - **Provider Type**: `OIDC`
   - **Provider Name**: `default`
   - **Issuer URL**: `https://app.terraform.io`
   - **Audiences**: Select `Default Audience`

4. **Configure Attribute Mappings**:

   | Google Attribute                     | OIDC Assertion                       |
   | ------------------------------------ | ------------------------------------ |
   | `attribute.terraform_full_workspace` | `assertion.terraform_full_workspace` |
   | `google.sub`                         | `assertion.sub`                      |
   | `attribute.terraform_workspace`      | `assertion.terraform_workspace_id`   |

5. **Add Attribute Condition**:

   ```hcl
   assertion.terraform_organization_name == "DSB"
   ```

6. Click **Create** to finalize the pool and provider.

## Step 3: Grant Access via Impersonation

1. After the pool and provider are created, click **Grant Access**.

2. Choose **Grant access using service account impersonation**.

3. Select the previously created service account (`terraform-deployer`).

4. Add the **Terraform Workspace Principal**:
   - Use your workspace ID to define the principal.
   - Example format:

   ```text
   principalSet://iam.googleapis.com/projects/<project-number>/locations/global/workloadIdentityPools/terraform-cloud/attribute.terraform_workspace_id/<workspace-id>
   ```

   ![Service Account Grant Screenshot](/img/projects/devsecops-pipeline-gcp/setup/grant-sa-permissions-oidc.png)

With this setup complete, Terraform Cloud will now be able to authenticate to GCP using OIDC and impersonate the `terraform-deployer` service account during runs — **without the need for storing or rotating service account keys**.

You can now move on to configuring your Terraform provider and environment variables.
