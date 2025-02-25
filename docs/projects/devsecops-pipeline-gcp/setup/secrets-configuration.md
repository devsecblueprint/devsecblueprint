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

   ![Variable Sets](/img/projects/devsecops-pipeline-gcp/setup/tf-variable-sets.png)

3. Click **Create Organization Variable Set**, and fill in the following details:
   - **Name**: Provide a meaningful name for the variable set.
   - **Description**: Add a brief description for clarity.
   - **Variable Set Scope**: Select **Apply to all projects and workspaces**. (You can modify this later if needed.)
4. Scroll down to the **Variables** section and click **Add Variable**. Add the following keys, marking them as **Sensitive**:
   - `GOOGLE_CREDENTIALS`: Paste the contents of your GCP service account JSON key file.
5. Navigate to the workspace, and click on Variables, and create a Workspace variable named `SNYK_TOKEN`, making it sensitive. Paste the value of the API Key or token in it and save it.

   ![alt text](/img/projects/devsecops-pipeline-gcp/setup/tf-snyk-variable.png)

6. After adding the variables, your variable set should look similar to this:

   ![alt text](/img/projects/devsecops-pipeline-gcp/setup/tf-variable-sets-complete.png)

## GitHub Configuration

After forking the repositories, you need to configure the necessary secrets for GitHub Actions in the `gcp-devsecops-pipeline` repository. These secrets will enable automated deployments when updates are pushed to the main branch.

1. Log in to GitHub and open the `gcp-devsecops-pipeline` repository.
2. Navigate to **Settings** > **Secrets and Variables** under the **Security** section.
3. Click **Actions**, then select **New Repository Secret**.
4. Add the following secrets:
   - `GOOGLE_CREDENTIALS`: Paste the contents of your GCP service account JSON key file.
   - `TF_API_TOKEN`: Your Terraform Cloud API token.

With these steps completed, your secrets and environment variables are fully configured for GCP and Terraform Cloud.
