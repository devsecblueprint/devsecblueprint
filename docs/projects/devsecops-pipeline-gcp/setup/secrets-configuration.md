---
id: config-secrets-gcp
title: Configuring Secrets and Environment Variables in GCP
sidebar_position: 5
---

## Overview

Now that the foundational setup is complete, this guide will walk you through configuring secrets and environment variables within both Google Cloud Platform (GCP) and Terraform Cloud.

## Terraform Cloud Configuration

1. Log in to Terraform Cloud and select the **DSB** organization.
2. On the left-hand menu, click **Settings** > **Variable Sets**. You should see a screen similar to this:

   ![Variable Sets](/img/projects/devsecops-pipeline-gcp/setup/variable_sets.png)

3. Click **Create Organization Variable Set**, and fill in the following details:
   - **Name**: Provide a meaningful name for the variable set.
   - **Description**: Add a brief description for clarity.
   - **Variable Set Scope**: Select **Apply to all projects and workspaces**. (You can modify this later if needed.)
4. Scroll down to the **Variables** section and click **Add Variable**. Add the following keys, marking them as **Sensitive**:
   - `GOOGLE_CREDENTIALS`: Paste the contents of your GCP service account JSON key file.
   - `TF_API_TOKEN`: Your Terraform Cloud API token.
5. After adding the variables, your variable set should look similar to this:

   ![Final Variable Set](/img/projects/devsecops-pipeline-gcp/setup/final_variable_set.png)

## GCP Secrets Manager Configuration

To securely manage sensitive information like API keys, follow these steps to set up secrets in GCP Secrets Manager:

1. Navigate to **Secret Manager** in the GCP Console.
2. Click **Create Secret**.
3. Provide the following details:
   - **Name**: Enter a meaningful name for the secret (e.g., `db-credentials`).
   - **Secret Value**: Enter the sensitive information (e.g., database username and password).
4. Click **Create Secret** to finalize.
5. To grant access to the secret, navigate to the secret's **Permissions** tab and click **Add Principal**:
   - **New Principal**: Enter the service account that will need access to the secret.
   - **Role**: Select **Secret Manager Secret Accessor**.
   - Click **Save**.

## GitHub Configuration

After forking the repositories, you need to configure the necessary secrets for GitHub Actions in the `gcp-devsecops-pipeline` repository. These secrets will enable automated deployments when updates are pushed to the main branch.

1. Log in to GitHub and open the `gcp-devsecops-pipeline` repository.
2. Navigate to **Settings** > **Secrets and Variables** under the **Security** section.
3. Click **Actions**, then select **New Repository Secret**.
4. Add the following secrets:
   - `GOOGLE_CREDENTIALS`: Paste the contents of your GCP service account JSON key file.
   - `TF_API_TOKEN`: Your Terraform Cloud API token.

With these steps completed, your secrets and environment variables are fully configured for GCP and Terraform Cloud.