---
id: configuring-deployment-user-gcp
title: Configuring Deployment User/Role in GCP
sidebar_position: 4
---

## Overview

This guide will help you set up a Service Account in Google Cloud Platform (GCP) that Terraform can use to deploy infrastructure changes. By this stage, you should already have a GCP project ready for deployment.

## Creating and Configuring a Service Account

1. Log in to your GCP account.
2. Navigate to the **IAM & Admin** section and select **Service Accounts** from the menu.
3. Click **Create Service Account**.
4. Enter a **Service Account Name** and optionally a description. Click **Create and Continue**.

   ![Create Service Account](/img/projects/devsecops-pipeline-gcp/setup/create_service_account.png)

5. Under **Grant this service account access to the project**, add the following roles:

   - **Owner** (for simplicity during setup, but in production, you should use the least privilege principle and only assign the required roles).
   - Click **Continue**.

   ![Grant Roles](/img/projects/devsecops-pipeline-gcp/setup/grant_roles.png)

6. Under **Grant users access to this service account**, leave it empty and click **Done**.

7. Once the service account is created, locate it in the list, click the **More Actions** menu (three dots), and select **Manage Keys**.
8. Click **Add Key**, then select **Create New Key**. Choose the **JSON** key type and click **Create**.
9. Save the downloaded key file in a secure location. This file contains the credentials needed for Terraform.

   ![Download JSON Key](/img/projects/devsecops-pipeline-gcp/setup/download_json_key.png)

## Setting Up the Environment

1. Move the downloaded JSON key file to your working directory.
2. Set the environment variable to use the key for authentication:

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-key-file.json"
   ```

   Replace `path/to/your-key-file.json` with the actual path to the JSON key file.

3. Test authentication to ensure it works:

   ```bash
   gcloud auth application-default login
   ```

With these steps completed, your GCP Service Account is set up and ready to be used for Terraform deployments.
