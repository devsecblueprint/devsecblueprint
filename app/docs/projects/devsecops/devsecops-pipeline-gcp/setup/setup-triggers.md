---
id: setup-repository-triggers
title: Setting Up Repository Triggers
sidebar_position: 6
---

## Purpose

Automating the build and deployment process is a critical aspect of modern DevSecOps workflows. By setting up repository triggers in Google Cloud Build, you can ensure that changes to your codebase automatically trigger builds, tests, and deployments, improving efficiency and security. This guide will walk you through configuring repository triggers in Google Cloud to streamline your DevSecOps pipeline.

## Setting Up Repository Triggers

Follow these steps to configure repository triggers in Google Cloud Build:

### 1. Connect Your Repository

1. Log into Google Cloud and navigate to the **Cloud Build** dashboard.
2. Click on **Repositories** and select **Create a new host connection**.
3. Choose **GitHub** as the host provider and fill out the necessary details:
   ![GitHub Connection](/img/projects/devsecops-pipeline-gcp/setup/github-connection.png)
4. If you are a new user, click **Install in a new account** to authorize access:
   ![Install GitHub App](/img/projects/devsecops-pipeline-gcp/setup/cloud-build-github-install.png)
5. Select your GitHub namespace or organization. Once done, your repositories and connections should appear:
   ![Repositories Connected](/img/projects/devsecops-pipeline-gcp/setup/verifying-connections.png)

### 2. Link Your Repository

1. Click the three-dot menu (**⋮**) on the right-hand side of the connected repository.
2. Select **Link Repositories**.
3. Choose the repository you want to create a trigger for and click **Link**:
   ![Link Repository](/img/projects/devsecops-pipeline-gcp/setup/link-repositories.png)

### 3. Configure Build Triggers

1. Navigate to the **Triggers** dashboard.
2. Click **Connect Repository**.
3. Fill out the required details to link your repository.
4. **Skip creating a trigger** at this stage if you want to manually configure it later:
   ![Connect Repository](/img/projects/devsecops-pipeline-gcp/setup/connecting-repositories.png)

## Next Steps

Once your repository is connected, you can define build triggers to automate deployments based on branch updates, pull requests, or tag creations. Fine-tune your configurations to align with your security and compliance requirements.

By implementing repository triggers, you enhance your CI/CD pipeline's efficiency, security, and reliability—key principles of a DevSecOps approach.
