---
id: config-secrets
title: Configuring Secrets & Environment Variables
sidebar_position: 5
---

## Overview

With your deployment principals created, the next step is wiring up secrets and environment variables so Terraform Cloud and GitHub Actions can authenticate securely. This ensures your pipeline can provision resources and trigger deployments without exposing sensitive credentials.

In this section, you’ll configure:

- **Terraform Cloud Variable Sets** for managing environment variables at the organization level.
- **GitHub Repository Secrets** for authenticating pipelines.

## Terraform Cloud Configuration

1. Log in to **Terraform Cloud** and select your **DSB** organization.

2. From the left-hand menu, go to **Settings** → **Variable Sets**. You’ll see a page like this:

   ![Variable Sets](/img/projects/devsecops-pipeline-azure/setup/image-111.png)

3. Click **Create Organization Variable Set** and fill out the details:

   - **Name**: Something descriptive (e.g., `Azure Deployment Variables`).
   - **Description**: Add a short explanation for clarity.
   - **Variable Set Scope**: Select **Apply to all projects and workspaces**. (This can be narrowed later if needed.)

4. Under the **Variables** section, click **Add Variable** and define the following keys. Be sure to set each one as an **Environment Variable**:

   - `TFC_AZ_CLIENT_ID`: Application ID of the Terraform Deployment Service Principal
   - `TFC_AZ_CLIENT_PASSWORD`: Client Secret value of the Terraform Deployment Service Principal
   - `TFC_AZ_DEVOPS_GITHUB_PAT`: GitHub PAT generated earlier
   - `TFC_AZ_DEVOPS_ORG_SERVICE_URL`: `https://dev.azure.com/your_organization`
   - `TFC_AZ_DEVOPS_PAT`: Azure DevOps PAT you created earlier
   - `TFC_AZ_SUBSCRIPTION_NAME`: Subscription Name
   - `TFC_AZ_SUBSCRIPTION_ID`: Subscription ID of your default subscription
   - `TFC_AZ_TENANT_ID`: Directory (Tenant) ID of the Terraform Service Principal

5. Once complete, your variable set should look something like this:

   ![Terraform Cloud Variable Set](/img/projects/devsecops-pipeline-azure/setup/image-9.png)

:::warning
These values are sensitive. Store them securely and rotate them regularly to maintain security best practices.
:::

## GitHub Configuration

Next, configure GitHub to store the secrets required by your pipeline. This will allow GitHub Actions to securely connect to Terraform Cloud.

1. Log in to GitHub and open your fork of the `azure-devsecops-pipeline` repository.

2. Navigate to **Settings** → **Secrets and Variables** under the **Security** section.

3. Click **Actions**, then select **New Repository Secret**.

4. Create a secret named:

   - `TF_API_TOKEN` → Paste in the Terraform Cloud API token you generated earlier.

## Conclusion

That’s it! You’ve successfully configured your secrets in **Terraform Cloud** and **GitHub**. With this step complete, your pipeline is now ready to authenticate, provision resources, and automate deployments securely.
