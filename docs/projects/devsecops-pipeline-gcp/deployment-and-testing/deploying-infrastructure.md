---
id: deploying-infrastructure-code
title: Deploying and Configuring Your DevSecOps Pipeline
sidebar_position: 1
---

## Overview

We've finally reached the stage where we deploy our infrastructure using Terraform Cloud. This guide will walk you through creating, configuring, and deploying the necessary DevSecOps pipelines for your project.

## Configuration Steps

### Deploying Changes via GitHub Actions

With the workspaces configured, you can now deploy changes using GitHub Actions.

1. Log into GitHub and open your forked project: `gcp-dsb-devsecops-infra`.
2. Navigate to **Actions** and click on `.github/workflows/main.yml`.
   ![Workflow File](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/image-3.png)
3. On the right-hand side, select the **Run Workflow** dropdown and click **Run Workflow**. This triggers the pipeline to:

   - Checkout the repository.
   - Plan and apply changes in Terraform Cloud.
   - Create Cloud Build pipeline and any additional resources.

4. Confirm that the plans have been applied successfully. You should see successful builds in both GitHub and Terraform Cloud. Example results are shown below:

   **GitHub Pipeline Execution**:
   ![GitHub Execution Results](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/image-4.png)

   **Terraform Cloud Deployment**:
   ![Terraform Deployment Results](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/image-5.png)

   **GCP Overview**:
   ![GCP Overview](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/image-6.png)

With these steps completed, your pipeline is fully operational and ready to detect and deploy changes from your GitHub repository.
