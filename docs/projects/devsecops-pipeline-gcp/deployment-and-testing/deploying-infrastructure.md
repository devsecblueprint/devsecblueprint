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

   ![alt text](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/github_action.png)

3. On the right-hand side, select the **Run Workflow** dropdown and click **Run Workflow**. This triggers the pipeline to:

   - Checkout the repository.
   - Plan and apply changes in Terraform Cloud.
   - Create Cloud Build pipeline and any additional resources.

4. Confirm that the plans have been applied successfully. You should see successful builds in both GitHub and Terraform Cloud. Example results are shown below:

   **GitHub Pipeline Execution**:
   ![alt text](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/completed_github_action.png)

   **Terraform Cloud Deployment**:
   ![alt text](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/completed_tf_run.png)

With these steps completed, your pipeline is fully operational and ready to detect and deploy changes from your GitHub repository.
