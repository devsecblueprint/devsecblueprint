---
id: creating-deployment-principals
title: Creating & Configuring Deployment Principals
sidebar_position: 3
---

## Overview

Before your pipeline can deploy infrastructure and containerized applications, it needs a way to authenticate securely with Azure and GitHub. This section walks you through creating and configuring the deployment principals required for Terraform, Azure Container Registry (ACR), and GitHub.

You’ll create:

- A **Terraform Service Principal** to provision resources in Azure.
- A **Container Registry Service Principal** to manage images in ACR/AKS.
- A **GitHub Personal Access Token (PAT)** to integrate with your repository.

## Terraform Service Principal

This principal gives Terraform the necessary rights to deploy and manage Azure resources.

1. Head to **App registrations** in the Azure portal and click **New registration**.

   - Enter a name (e.g., `test-registration`) and click **Register**.

     ![App Registration](/img/projects/devsecops-pipeline-azure/setup/image.png)

2. Navigate to your **Subscription** in the Azure portal.

   - Go to **Access Control (IAM)** → **Role assignments**.
   - Click **+ Add** → **Add role assignment**.
   - Assign the **Contributor** role to your service principal.

   ![Assign Contributor Role](/img/projects/devsecops-pipeline-azure/setup/image-1.png)

   Repeat the process and also assign the **User Access Administrator** role.

   ![Assign User Access Administrator Role](/img/projects/devsecops-pipeline-azure/setup/image-3.png)

3. Back in your app registration, go to **Certificates & secrets**.

   - Click **+ New client secret**.

   - Set the expiry to **180 days**.

   - Save the generated **Client ID** and **Client Secret** — you’ll need them later.

   ![Client Secret](/img/projects/devsecops-pipeline-azure/setup/image-7.png)

   :::important
   These credentials are sensitive. Store them securely in a secret manager or someplace safe locally.
   :::

## Container Registry Service Principal

This principal will be used for authentication with ACR or AKS.

1. Navigate again to **App registrations**.

   - Click **New registration** and provide a name that indicates its purpose (e.g., `test-registration-CR` or `test-registration-AKS`).

2. Once created, go to **Certificates & secrets**.

   - Click **+ New client secret**.
   - Set the expiry to **180 days**.
   - Save the **Client ID** and **Client Secret** securely for later use.
     ![Client Secret](/img/projects/devsecops-pipeline-azure/setup/image-7.png)

## GitHub Personal Access Token (PAT)

A GitHub PAT allows your pipeline to push and pull code securely from your repository.

1. Log in to GitHub and head to: [Personal Access Tokens](https://github.com/settings/personal-access-tokens).

   - Select **Fine-grained tokens**.
   - Click **Generate new token** and choose your forked repository (e.g., `azure-python-fastapi`).
   - Assign the required repository-level scopes.

2. Copy the token and store it securely (e.g., GitHub Secrets, Azure Key Vault).

   - Your screen should look similar to this once generated:
     ![GitHub PAT](/img/projects/devsecops-pipeline-azure/setup/image-8.png)

## Conclusion

That’s it! You’ve set up all the deployment principals needed for your DevSecOps pipeline. With these in place, Terraform can provision resources, your pipeline can interact with ACR/AKS, and GitHub can authenticate workflows securely.
