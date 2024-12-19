---
id: config-secrets
title: Configuring Secrets and Environment Variables
sidebar_position: 5
---

## Overview

Now that the foundational setup is complete, this guide will walk you through configuring secrets and environment variables within both GitHub and Terraform Cloud.

## Terraform Cloud Configuration

1. Log in to Terraform Cloud and select the **DSB** organization.
2. On the left-hand menu, click **Settings** > **Variable Sets**. You should see a screen similar to this:

   ![Variable Sets](/img/projects/devsecops-pipeline-aws/setup/image-6.png)

3. Click **Create Organization Variable Set**, and fill in the following details:
   - **Name**: Provide a meaningful name for the variable set.
   - **Description**: Add a brief description for clarity.
   - **Variable Set Scope**: Select **Apply to all projects and workspaces**. (You can modify this later if needed.)
4. Scroll down to the **Variables** section and click **Add Variable**. Add the following keys, marking them as **Sensitive**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
     > **Note:** Use the credentials from the spreadsheet you saved earlier.
5. After adding the variables, your variable set should look similar to this:

   ![Final Variable Set](/img/projects/devsecops-pipeline-aws/setup/image-7.png)

## GitHub Configuration

After forking the repositories, you need to configure the necessary secrets for GitHub Actions in the `aws-devsecops-pipeline` repository. These secrets will enable automated deployments when updates are pushed to the main branch.

1. Log in to GitHub and open the `aws-devsecops-pipeline` repository.
2. Navigate to **Settings** > **Secrets and Variables** under the **Security** section.
3. Click **Actions**, then select **New Repository Secret**.
4. Create a secret with the name `TF_API_TOKEN` and paste the Terraform Cloud token you generated earlier.

With these steps completed, your repositories and environment are fully configured and ready for use.
