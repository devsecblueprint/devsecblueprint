---
id: devsecops-terraform-code
title: DevSecOps Terraform Code - Explained
sidebar_position: 1
---

## Overview

With our environments configured and secrets created, it's time to dive into the Terraform code that defines the DevSecOps pipeline infrastructure. This guide provides a detailed explanation of the critical components so you can fully understand how the system works.

## Code Overview

All relevant code is located in the `terraform` folder, which contains two interconnected Terraform workspaces:

1. **EKS Cluster**
2. **Pipelines**

### EKS Cluster Workspace

This workspace provisions an Elastic Kubernetes Service (EKS) cluster, including node groups and essential cluster resources. While smaller in scope compared to the Pipelines workspace, it lays the foundation for Kubernetes-based deployments. Check out the codebase [here](https://github.com/devsecblueprint/aws-devsecops-pipeline/tree/main/terraform/eks-cluster).

- **Files**:
  - `main.tf`: Defines the EKS cluster, node groups, networking components, and default subnets.
  - `variables.tf`: Configures input variables, including cluster name, region, and node specifications.
  - `outputs.tf`: Outputs critical information such as the EKS cluster name and endpoint.

### Pipelines Workspace

This workspace contains the infrastructure for setting up CI/CD pipelines. While the folder includes several files, the `main.tf` file is the core component. Check out the codebase [here](https://github.com/devsecblueprint/aws-devsecops-pipeline/tree/main/terraform/eks-cluster). Below are the key elements explained in detail:

#### GitHub Connection Configuration

- **Resource**: `aws_codestarconnections_connection`
- **Purpose**:
  - Establishes a secure connection between AWS CodePipeline and a GitHub repository.
  - Utilizes a `random_id` resource to generate a unique connection name for traceability.
  - Configures the provider type as "GitHub."

#### Default S3 Bucket Configuration

- **Module**: `default_bucket`
- **Purpose**:
  - Provisions an S3 bucket for storing CodePipeline artifacts.
  - Standardizes bucket naming conventions using variables.
  - Ensures secure and centralized storage for build and deployment artifacts.

#### EKS Cluster Configuration

- **Module**: `cluster_auth`
- **Purpose**:
  - Manages authentication and RBAC settings for the EKS cluster.
  - Grants CodeBuild IAM roles permission to interact with the cluster by associating them with the `system:masters` group.
  - Adds an IAM user ("your_name") with administrative privileges to the cluster. You will want to replace this with the user name for the account.

#### FastAPI Pipeline Configuration

- **Module**: `awsome_fastapi_pipeline`
- **Purpose**:
  - Establishes a CI/CD pipeline for the "AWSOME FastAPI" project.
  - Leverages the GitHub connection to pull source code from the repository.
  - Integrates the pipeline with the S3 bucket and EKS cluster for seamless deployments.

#### Key Pipeline Parameters

- **GitHub Integration**:
  - Dynamically links the GitHub connection ARN to CodePipeline.
  - Configures repository details:
    - Repository: `The-DevSec-Blueprint/awsome-fastapi`
    - Branch: `main`
- **Build and Deployment**:
  - Buildspec: Located at `buildspecs/awsome-fastapi/build.yml`.
  - Deployspec: Located at `buildspecs/awsome-fastapi/deploy.yml`.
  - Build environment:
    - Compute type: `BUILD_GENERAL1_SMALL`
    - Image: `aws/codebuild/standard:5.0`
    - Environment type: `LINUX_CONTAINER`
    - Privileged mode enabled for containerized builds.
- **Security Scanning**:
  - Integrates Snyk for vulnerability scanning with `SNYK_ORG_ID` and `SNYK_TOKEN` variables.

By understanding the purpose and structure of these Terraform configurations, you'll have a clearer picture of how the DevSecOps pipeline functions, from provisioning infrastructure to enabling secure and automated CI/CD workflows.
