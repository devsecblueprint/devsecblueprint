---
id: devsecops-terraform-code
title: DevSecOps Terraform Code - Explained
sidebar_position: 1
---

## Overview

With our environments configured and secrets created, it's time to dive into the Terraform code that defines the DevSecOps pipeline infrastructure. This guide provides a detailed explanation of the critical components so you can fully understand how the system works.

## Code Overview

All relevant code is located in the `terraform` folder, which contains two interconnected Terraform workspaces:

1. **GKE Cluster**
2. **Pipelines**

### GKE Cluster Workspace

This workspace provisions a Google Kubernetes Engine (GKE) cluster, including node pools and essential cluster resources. While smaller in scope compared to the Pipelines workspace, it lays the foundation for Kubernetes-based deployments. Check out the codebase [here](https://github.com/The-DevSec-Blueprint/gcp-devsecops-pipeline/tree/main/terraform/gke-cluster).

- **Files**:
  - `main.tf`: Defines the GKE cluster, node pools, networking components, and default subnets.
  - `variables.tf`: Configures input variables, including cluster name, region, and node specifications.
  - `outputs.tf`: Outputs critical information such as the GKE cluster name and endpoint.

### Pipelines Workspace

This workspace contains the infrastructure for setting up CI/CD pipelines. While the folder includes several files, the `main.tf` file is the core component. Check out the codebase [here](https://github.com/The-DevSec-Blueprint/gcp-devsecops-pipeline/tree/main/terraform/pipelines). Below are the key elements explained in detail:

#### GitHub Connection Configuration

- **Resource**: `google_cloudbuild_trigger`
- **Purpose**:
  - Establishes a secure connection between Google Cloud Build and a GitHub repository.
  - Uses a trigger to automatically build and deploy upon code changes.
  - Configures the provider type as "GitHub."

#### Default Cloud Storage Bucket Configuration

- **Module**: `default_bucket`
- **Purpose**:
  - Provisions a Cloud Storage bucket for storing Cloud Build artifacts.
  - Standardizes bucket naming conventions using variables.
  - Ensures secure and centralized storage for build and deployment artifacts.

#### GKE Cluster Configuration

- **Module**: `cluster_auth`
- **Purpose**:
  - Manages authentication and RBAC settings for the GKE cluster.
  - Grants Cloud Build service account permission to interact with the cluster.
  - Adds an IAM user ("your_name") with administrative privileges to the cluster. You will want to replace this with the user name for the account.

#### FastAPI Pipeline Configuration

- **Module**: `gcp_fastapi_pipeline`
- **Purpose**:
  - Establishes a CI/CD pipeline for the "GCP FastAPI" project.
  - Leverages the GitHub connection to pull source code from the repository.
  - Integrates the pipeline with the Cloud Storage bucket and GKE cluster for seamless deployments.

#### Key Pipeline Parameters

- **GitHub Integration**:
  - Dynamically links the GitHub connection to Cloud Build triggers.
  - Configures repository details:
    - Repository: `The-DevSec-Blueprint/gcp-fastapi`
    - Branch: `main`
- **Build and Deployment**:
  - Buildspec: Located at `cloudbuilds/gcp-fastapi/build.yaml`.
  - Deployspec: Located at `cloudbuilds/gcp-fastapi/deploy.yaml`.
  - Build environment:
    - Machine type: `E2_SMALL`
    - Image: `gcr.io/cloud-builders/gcloud`
    - Privileged mode enabled for containerized builds.
- **Security Scanning**:
  - Integrates Google Cloud Security Command Center for vulnerability scanning.
  - Uses `GCP_SECURITY_TOKEN` and `GCP_PROJECT_ID` variables for authentication.

By understanding the purpose and structure of these Terraform configurations, you'll have a clearer picture of how the DevSecOps pipeline functions, from provisioning infrastructure to enabling secure and automated CI/CD workflows.
