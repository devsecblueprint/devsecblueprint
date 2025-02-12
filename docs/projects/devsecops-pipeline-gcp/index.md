---
id: devsecops-pipeline-gcp
title: DevSecOps Pipeline - GCP
description: Build a DevSecOps Pipeline within GCP!
sidebar_position: 3
---

Author(s): [Damien Burks], [Iman Crooks]

![GCP Logo](/img/projects/devsecops-pipeline-gcp/gcp_logo.png)

## Know Before You Go

This project is a _little_ expense, and you will rack up a nice bill in GCP if you leave all your resources created. Therefore, I recommend that you **TEAR IT ALL DOWN** when you're done.

## Prerequisities

1. Before you begin this, you will want to have some knowledge of GCP services and how they work, as well as prior knowledge of Terraform. You can take a look at [Building Cloud DevSecOps Pipelines (In Theory)](../../blueprint/implementing-cloud-devsecops.md#other-infrastructure-as-code-iac-languages) for more information.
1. You will also want to ensure that you have an GCP project created. You can go through the account creation process here: [GCP Project Creation Process](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
1. Make sure you have the following installed on your local machine:
   - [Python](https://www.python.org/downloads/)
   - [Git](https://git-scm.com/downloads)
   - [Docker](https://docs.docker.com/engine/install/)
   - [Terraform CLI](https://developer.hashicorp.com/terraform/install)
   - [gcloud CLI](https://cloud.google.com/sdk/docs/install)

## Overview

So you've decided to go down the path of building your own Cloud Native DevSecOps pipeline within GCP? If so, you've come to the right place! We are going to show you how to setup your own GCP pipeline using Terraform Cloud. Unlike the [DevSecOps Home Lab](../devsecops-home-lab/index.md), we're just focused on developing the pipeline and deploying our application onto a Cloud Run resource.

Luckily for you all, you won't need to do anything. we've taken the liberty of developing all of the code for you. These are the two GitHub repositories that you need to look at before we get started:

1. DevSecOps Pipeline Infrastructure: https://github.com/devsecblueprint/dsb-gcp-devsecops-infra
1. FastAPI Application with Pipeline Definition: https://github.com/devsecblueprint/gcp-python-fastapi

## Architecture Diagram

![Architecture Diagram](/img/projects/devsecops-pipeline-gcp/architecture.drawio.svg)

### Architecture Breakdown

At a **VERY** high level, this architecture briefly covers the services that we will be leveraging for the DevSecOps Pipelines. Here are the descriptions with intent of each service:

- **Artifact Registry**: Stores container images and application artifacts for deployments.
- **Cloud IAM**: Provides secure identity and access management service accounts with roles for pipeline operations.
- **Cloud Build**: Automates build, test, and deployment processes within CI/CD workflows. This is defined by within the FastAPI Application Project.
- **Cloud Storage**: Stores build artifacts and logs generated during pipeline execution.
- **Secret Manager**: Securely manages sensitive data like API keys and credentials for pipelines.

### Flow Diagram

Now that we've covered the architecture diagram, let's put this together so you can understand the flow and who everything is supposed to work.

![Flow Diagram](/img/projects/devsecops-pipeline-gcp/flow.drawio.svg)

#### Flow Diagram Explained

1. A developer writes code and commits the changes to GitHub. This action triggers the Cloud Build pipeline.
1. The Cloud Build pipeline runs according to the stages defined in its YAML configuration file stored in GitHub. These stages include building, testing, scanning, and deploying the application, with all necessary secrets securely retrieved from Secrets Manager.
1. The pipeline performs comprehensive security scans on the code, including both source code and dependency analysis.
1. Trivy executes container scans to ensure security and compliance.
1. Upon successful completion of all pipeline stages, the containerized application is deployed to a Cloud Run resource.

## What You’ll Learn

By working through this guide, you’ll gain hands-on experience building and deploying a secure, cloud-native DevSecOps pipeline on GCP. Specifically, you will learn how to:

1. Configure and manage GCP resources using Terraform Cloud.
1. Integrate GitHub for version control and pipeline triggers.
1. Use Cloud Build to automate CI/CD processes, including build, test, and deployment stages.
1. Securely manage sensitive information with GCP Secret Manager.
1. Perform security scans on code and dependencies using tools like Trivy.
1. Deploy containerized applications to Cloud Run for scalable, serverless execution.

With all that being stated, **Please follow the order of the documents, otherwise you'll most likely run into errors and get lost.**

[Damien Burks]: https://www.youtube.com/@damienjburks
[Iman Crooks]: https://www.linkedin.com/in/iman-crooks
