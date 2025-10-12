---
id: devsecops-pipeline-azure
title: DevSecOps Pipeline - Azure
description: Build a DevSecOps Pipeline within Azure!
sidebar_position: 3
---

Author(s): [Timothy Hogue], [Damien Burks]

<!-- markdownlint-disable MD033 -->
<p align="center">
   <img src="/img/projects/devsecops-pipeline-azure/azure_logo.png" alt="GitHub Actions Logo" width="400" />
</p>

## Know Before You Go

This project is a _little_ expense, and you will rack up a nice bill in Azure if you leave all your resources created. Therefore, I recommend that you **TEAR IT ALL DOWN** when you're done.

## Prerequisities

1. Before you begin this, you will want to have some knowledge of Azure services and how they work, as well as prior knowledge of Terraform. You can take a look at [Building Cloud DevSecOps Pipelines (In Theory)](../../blueprint/devsecops/implementing-cloud-devsecops.md#other-infrastructure-as-code-iac-languages) for more information.
1. You will also want to ensure that you have an Azure project created. You can go through the account creation process here: [Azure Project Creation Process](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account)
1. Make sure you have the following installed on your local machine:
   - [Python](https://www.python.org/downloads/)
   - [Git](https://git-scm.com/downloads)
   - [Docker](https://docs.docker.com/engine/install/)
   - [Terraform CLI](https://developer.hashicorp.com/terraform/install)
   - [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)

## Overview

So you've decided to go down the path of building your own Cloud Native DevSecOps pipeline within Azure? If so, you've come to the right place! We are going to show you how to setup your own Azure pipeline using Terraform Cloud. Unlike the [DevSecOps Home Lab](../devsecops-home-lab/index.md), we're just focused on developing the pipeline and deploying our containerized application into the Azure Container Registry.

Luckily for you all, you won't need to do anything. we've taken the liberty of developing all of the code for you. These are the two GitHub repositories that you need to look at before we get started:

1. DevSecOps Pipeline Infrastructure: https://github.com/devsecblueprint/azure-devsecops-pipeline
1. FastAPI Application with Pipeline Definition: https://github.com/devsecblueprint/azure-python-fastapi

## Architecture Diagram

![Architecture Diagram](/img/projects/devsecops-pipeline-azure/architecture.drawio.svg)

### Architecture Breakdown

At a **VERY** high level, this architecture briefly covers the services that we will be leveraging for the DevSecOps Pipelines. Here are the descriptions with intent of each service:

- **Azure DevOps** – Provides end-to-end CI/CD pipelines and project management tools to automate builds, tests, and deployments in the cloud.
- **Azure Container Registry** – A secure, private registry for storing and managing Docker container images used in your deployments.
- **Federated Identity / User Assigned Identity** – Enables workloads to authenticate securely to Azure resources without embedding secrets, by leveraging managed or federated identities.
- **Resource Group** – A logical container that organizes and manages related Azure resources as a single unit for easier governance and lifecycle management.
- **Azure Resource Manager Service Connection (AzureRM)** – Connects Azure DevOps pipelines to Azure subscriptions, enabling deployments and resource management through secure federated authentication.

### Flow Diagram

Now that we've covered the architecture diagram, let's put this together so you can understand the flow and how everything is supposed to work.

![Flow Diagram](/img/projects/devsecops-pipeline-azure/flow.drawio.svg)

#### Flow Diagram Explained

1. A developer writes code and commits the changes to GitHub. This action triggers the Azure DevOps pipeline.
1. The Azure DevOps pipeline runs according to the stages defined in its YAML configuration file stored in GitHub. These stages include building, testing, scanning, and deploying the application
1. The Python application image is built. In addition, the source code is checked for any formatting and linting errors.
1. The Python source code, dependencies and the containerized application will be scanned for any security vulnerabilities using ZAP by Checkmarx and Trivy.
1. Upon successful completion of all pipeline stages, the containerized application is checked into Azure Container Registry.

## What You’ll Learn

By working through this guide, you’ll gain hands-on experience building and deploying a secure, cloud-native DevSecOps pipeline on Azure. Specifically, you will learn how to:

1. Configure and manage Azure resources using Terraform Cloud.
1. Integrate GitHub with Azure DevOps for version control and pipeline triggers.
1. Use Azure DevOps to automate CI/CD processes, including build, test, and deployment stages.
1. Perform security scans on code and dependencies using tools like Trivy and ZAP by Checkmarx.
1. Deploy containerized application or image into Azure Container Registry.

With all that being stated, **Please follow the order of the documents, otherwise you'll most likely run into errors and get lost.**

[Damien Burks]: https://damienjburks.com
[Timothy Hogue]: https://www.linkedin.com/in/timothy-hogue/
