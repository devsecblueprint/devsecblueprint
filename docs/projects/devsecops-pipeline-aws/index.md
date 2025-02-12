---
id: devsecops-pipeline-aws
title: DevSecOps Pipeline - AWS
description: Build a DevSecOps Pipeline within AWS!
sidebar_position: 3
---

Author: [Damien Burks]

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/otleFroshZU?si=otleFroshZU"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

## Know Before You Go

This project is a _little_ expense, and you will rack up a nice bill in AWS if you leave all your resources created. Therefore, I recommend that you **TEAR IT ALL DOWN** when you're done. **Do not leave your EKS cluster running, you'll be charged for it.**

## Prerequisities

1. Before you begin this, you will want to have some knowledge of AWS services and how they work, as well as prior knowledge of Terraform. You can take a look at [Building Cloud DevSecOps Pipelines (In Theory)](../../blueprint/implementing-cloud-devsecops.md#other-infrastructure-as-code-iac-languages) for more information.
1. You will also want to ensure that you have an AWS account created. You can go through the account creation process here: [AWS Account Creation Process](https://aws.amazon.com/resources/create-account/)
1. Make sure you have the following installed on your local machine:
   - [Python](https://www.python.org/downloads/)
   - [Git](https://git-scm.com/downloads)
   - [Docker](https://docs.docker.com/engine/install/)
   - [Terraform CLI](https://developer.hashicorp.com/terraform/install)

## Overview

So you've decided to go down the path of building your own Cloud Native DevSecOps pipeline within AWS? Well, hell... welcome! This is the one of my _favorite_ projects where I'm going to show you how to setup your own AWS pipeline using Terraform Cloud. Unlike the [DevSecOps Home Lab](../devsecops-home-lab/index.md), we're just focused on developing the pipeline and deploying an application into Elastic Kubernetes Service (EKS).

Luckily for you all, you won't need to do anything. I've taken the liberty of developing all of the code for you. These are the two GitHub repositories that you need to look at before we get started:

1. DevSecOps Pipeline: https://github.com/devsecblueprint/aws-devsecops-pipeline
1. FastAPI Application: https://github.com/devsecblueprint/awsome-fastapi

## Architecture Diagram

![Architecture Diagram](/img/projects/devsecops-pipeline-aws/architecture.drawio.svg)

### Architecture Breakdown

At a **VERY** high level, the architecture represents an automated CI/CD pipeline leveraging several AWS services to deploy containerized applications:

1. **AWS CodePipeline**: Manages the end-to-end flow of code changes, automating build, test, and deployment stages.
2. **AWS CodeBuild**: Builds and tests the application code, generating deployable artifacts, and executing Security Scans with Snyk and Trivy.
3. **Amazon S3**: Stores artifacts like build outputs and deployment files.
4. **AWS Systems Manager (SSM) Parameter Store**: Securely manages configuration data and secrets used for Snyk.
5. **Amazon EKS**: Serves as the deployment environment for containerized workloads, providing scalability and orchestration.

**Flow Overview**:

- CodePipeline orchestrates the process.
- CodeBuild validates, scans, and compiles the code while also interacting with SSM.
- Artifacts are stored in S3.
- Applications are deployed to the EKS cluster.

This architecture ensures automation, security, and scalability for modern DevSecOps workflows.

## What You’ll Learn

By working through this guide, you’ll gain hands-on experience building and deploying a secure, cloud-native DevSecOps pipeline on AWS. Specifically, you will learn how to:

- **Architect and Implement a Secure CI/CD Pipeline:**  
  Understand how AWS CodePipeline, CodeBuild, S3, SSM Parameter Store, and EKS work together in an automated, end-to-end workflow.

- **Integrate Security Scanning into the Pipeline:**  
  Use tools like Snyk and Trivy to scan application code and container images for vulnerabilities before production deployment.

- **Leverage Terraform for Infrastructure as Code (IaC):**  
  Employ Terraform to provision and manage AWS resources consistently and at scale.

- **Deploy a Containerized Application to Amazon EKS:**  
  Gain confidence in running containerized workloads on Kubernetes with EKS, ensuring scalability and simplified orchestration.

- **Securely Manage Configuration and Secrets:**  
  Store and retrieve sensitive data using AWS Systems Manager Parameter Store, following security best practices throughout your pipeline.

With all that being stated, **Please follow the order of the documents, otherwise you'll most likely run into errors and get lost.**

## Additional Reference Guides

This section includes reference guides for you all just in case you get lost and the video doesn't help you:

| Name                                                                   | Link                                                                                                                 | Type                           |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Building a Cloud-Native DevSecOps Pipeline on AWS with Terraform Cloud | https://medium.com/@gregoryeast1/building-a-cloud-native-devsecops-pipeline-on-aws-with-terraform-cloud-28060c3d9896 | Blog written by [Gregory East] |

[Gregory East]: https://medium.com/@gregoryeast1
[Damien Burks]: https://www.youtube.com/@damienjburks
