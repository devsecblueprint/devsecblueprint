---
id: devsecops-terraform-code
title: Terraform and Pipeline Code - Explained
sidebar_position: 1
---

## Overview

With your environment configured and secrets set up, it’s time to look under the hood at the Terraform code that provisions the DevSecOps pipeline on Azure. This guide breaks down the structure of the Terraform configuration and explains the purpose of each file so you can clearly understand how the infrastructure is deployed and managed.

## Code Overview

All Terraform code is located in the `terraform` folder. This folder contains a single configuration that provisions the Azure DevOps project, service connections, and pipelines needed to build and deploy your FastAPI application securely.

Here’s a breakdown of the key files:

### `main.tf`

This is the core file that provisions all Azure DevOps resources.

#### Azure DevOps Project

- **Resource**: `azuredevops_project`
- **Purpose**:

  - Creates a new Azure DevOps project (`python-fastapi`).
  - Configures features such as **pipelines** (enabled) and disables unused ones (artifacts, boards, test plans, repositories).
  - Sets the project visibility to **private**.

:::important
Always keep your project visibility set to **private** for security reasons.
:::

#### GitHub Service Connection

- **Resource**: `azuredevops_serviceendpoint_github`
- **Purpose**:

  - Establishes a secure service connection between Azure DevOps and GitHub.
  - Uses the `TFC_AZ_DEVOPS_GITHUB_PAT` variable for authentication.

- **Benefit**: Enables Azure DevOps to fetch code directly from your forked repository.

#### Build Definition

- **Resource**: `azuredevops_build_definition`
- **Purpose**:

  - Defines a build pipeline in Azure DevOps.
  - Delegates build logic to the YAML file stored in the repository (`.azdo-pipelines/build.yml`).
  - Configures CI triggers to automatically run on commits to the `main` branch.

- **Repository Details**:

  - Source: `devsecblueprint/azure-python-fastapi` (your forked repo).
  - Branch: `refs/heads/main`.

- **Advantage**: Keeps pipeline logic versioned and controlled alongside your code.

:::note
By storing pipeline definitions in your repo, you ensure all changes are tracked and version-controlled.
:::

### `variables.tf`

- Defines input variables for sensitive and configurable values, including:

  - GitHub PAT (`TFC_AZ_DEVOPS_GITHUB_PAT`)
  - Azure Subscription ID, Tenant ID, Client ID, and Client Secret

- Encourages reusability and environment-specific customization.

:::important
Sensitive values should always be injected via **Terraform Cloud variable sets**, never hardcoded.
:::

### `providers.tf`

- Configures the **Azure DevOps provider**.
- Authenticates using your Azure DevOps PAT (`TFC_AZ_DEVOPS_PAT`).
- Ensures Terraform can provision and manage DevOps projects, pipelines, and connections.

:::tip
Lock provider versions to prevent unexpected changes in behavior during upgrades.
:::

### `data.tf`

- Used to fetch or reference existing Azure DevOps and Azure resources.
- Keeps the configuration modular by reusing values instead of hardcoding them.

### `outputs.tf`

- Provides outputs such as project IDs, pipeline IDs, or service endpoint IDs after a successful `apply`.
- Makes it easier to reference critical resources when wiring up other configurations.

:::note
Use outputs to pass important values into other systems, but never expose sensitive data like secrets or tokens.
:::

## FastAPI Project

Alongside the Terraform infrastructure, the pipeline integrates with a **FastAPI application** that will be scanned, built, and deployed. The application repository includes an `.azdo-pipelines` folder, which contains the pipeline definitions and templates.

### Pipeline Entry Point

- **`azure-pipelines.yml`**

  - Main entry point for Azure DevOps.
  - References modular templates for each stage of the pipeline.
  - Controls the build, scan, and deployment lifecycle of the FastAPI app.

### Pipeline Templates

The `pipeline_templates/` folder contains reusable steps broken down by function:

- **`build-image.yml`**: Builds the FastAPI Docker image.
- **`push-image.yml`**: Pushes the built image to the container registry.
- **`linting.yml`**: Runs code quality checks (linting) against the FastAPI project.
- **`unit-sec-scan.yml`**: Executes unit tests and security scans against the codebase.
- **`deploy.yml`**: Handles deployment of the FastAPI image to the target environment (such as AKS).

:::important
These templates are modular, which means you can reuse them across multiple pipelines or projects without duplicating logic.
:::

## Conclusion

This Terraform configuration defines the backbone of your Azure DevSecOps pipeline, while the **FastAPI project** provides the application layer that is continuously scanned, built, and deployed.

Together, they enable a secure and automated workflow where:

- Terraform provisions the Azure DevOps infrastructure.
- Pipelines orchestrate builds, tests, scans, and deployments.
- The FastAPI app serves as the workload being protected and delivered through DevSecOps practices.
