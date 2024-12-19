---
id: deploying-infrastructure-code
title: Deploying and Configuring Your DevSecOps Pipeline
sidebar_position: 1
---

## Overview

We've finally reached the stage where we deploy our infrastructure using Terraform Cloud. This guide will walk you through creating, configuring, and deploying the necessary DevSecOps pipelines for your project.

## Configuration Steps

### Terraform Cloud Setup

1. Log into Terraform Cloud and select the **DSB organization**.
2. Click the **New** button to create a new project. Provide a name and description as needed.
3. Navigate to **Workspace**, select the project you created, and click **Continue**.
4. Choose **CLI-Driven Workflow** (required for GitHub Actions).
5. Enter the workspace name as `dsb-aws-devsecops-eks-cluster`. Add an optional description and click **Create**.
6. Repeat the same steps for another workspace named `dsb-aws-devsecops-pipelines`.

At the end of this process, you should have two workspaces created. Here’s an example of how they should appear in your organization (without the Run Status applied):

![Workspaces Overview](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image.png)

#### Configuring Secrets in Terraform Cloud

1. Navigate to the `dsb-aws-devsecops-pipelines` workspace and select **Variables**.

   ![Workspace Variables](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-1.png)

2. Under **Workspace Variables**, create two sensitive variables:

   - `SNYK_ORG_ID`
   - `SNYK_TOKEN`

   Populate these variables with the respective values. The final setup should resemble this:
   ![Configured Variables](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-2.png)

### Deploying Changes via GitHub Actions

With the workspaces configured, you can now deploy changes using GitHub Actions.

1. Log into GitHub and open your forked project: `aws-devsecops-pipelines`.
2. Navigate to **Actions** and click on `.github/workflows/main.yml`.
   ![Workflow File](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-3.png)
3. On the right-hand side, select the **Run Workflow** dropdown and click **Run Workflow**. This triggers the pipeline to:

   - Checkout the repository.
   - Plan and apply changes in Terraform Cloud.
   - Deploy the EKS Cluster and DevSecOps pipeline for `AWSOME-FastAPI`.

   > **Note**: This process may take around 30 minutes. Feel free to step away during this time as the EKS Cluster creation is time-intensive.

4. Confirm that the plans have been applied successfully. You should see successful builds in both GitHub and Terraform Cloud. Example results are shown below:

   **GitHub Pipeline Execution**:
   ![GitHub Execution Results](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-4.png)

   **Terraform Cloud Deployment**:
   ![Terraform Deployment Results](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-5.png)

   **AWS Overview**:
   ![AWS Overview](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-6.png)

### Configuring and Testing CodeStar Connection

With your infrastructure deployed, the next step is configuring the CodeStar Connection to link AWS with GitHub. This ensures automatic detection and deployment of changes to your Python project, `AWSOME-FastAPI`.

1. Navigate to the **CodePipeline Dashboard** in AWS.
2. Click **Settings > Connections** and select the `dsb-github-connection` name. Its status will likely be `Pending`, which explains why the pipeline is in a `failed` state. The connection needs to be `Active`.

   ![Pending Connection](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-7.png)

3. Click **Update Pending Connection**. A browser pop-up will appear.
4. Click **Install a New App**.

   ![Install App](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-8.png)

5. Select your GitHub username to install the AWS Connector for GitHub.

   ![Select GitHub Username](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-9.png)

6. Once redirected back to the Connect to GitHub dashboard, click **Connect**. The connection status should now display as `Available`.

   ![Available Connection](/img/projects/devsecops-pipeline-aws/deployment-and-testing/image-10.png)

With these steps completed, your pipeline is fully operational and ready to detect and deploy changes from your GitHub repository.
