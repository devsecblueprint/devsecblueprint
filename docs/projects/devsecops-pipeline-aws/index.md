---
id: devsecops-pipeline-github-actions
title: DevSecOps Pipeline - AWS
description: Build a DevSecOps Pipeline within AWS!
sidebar_position: 3
---

>**This page is still a work in progress. Please come back later.**

Author: [Damien Burks]

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/otleFroshZU?si=otleFroshZU"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

> **NOTE**: This video does not cover all of the things that you need to do, therefore, I decided to write things out so that you learn how to do these things completely. However, feel free to follow this video if you get lost somewhere.

## Prerequisities

Before you begin this, you will want to have some knowledge of AWS services and how they work, as well as prior knowledge of Terraform. You can take a look at [Building Cloud DevSecOps Pipelines (In Theory)](../../blueprint/implementing-cloud-devsecops.md#other-infrastructure-as-code-iac-languages) for more information.

You will also want to ensure that you have an AWS account created. You can go through the account creation process here: [AWS Account Creation Process](https://aws.amazon.com/resources/create-account/)

## Overview

So you've decided to go down the path of building your own Cloud Native DevSecOps pipeline within AWS? Well, hell... welcome! This is the one of my _favorite_ projects where I'm going to show you how to setup your own AWS pipeline using Terraform Cloud. Unlike the [home lab](../devsecops-home-lab/index.md), we're just focused on developing the pipeline and deploying an application into Elastic Kubernetes Service (EKS).

Luckily for you all, you won't need to do anything. I've taken the liberty of developing all of the code for you. These are the two GitHub repositories that you need to look at before we get started:

1. DevSecOps Pipeline: https://github.com/The-DevSec-Blueprint/aws-devsecops-pipeline
1. FastAPI Application: https://github.com/The-DevSec-Blueprint/awsome-fastapi

## Architecture Diagram

![Architecture Diagram](/img/projects/devsecops-pipeline-aws/architecture.drawio.svg)
> TODO: Add in security tools and talk through the actual scanning process.

### Architecture Breakdown

At a **VERY** high level, the architecture represents an automated CI/CD pipeline leveraging several AWS services to deploy containerized applications:

1. **AWS CodePipeline**: Manages the end-to-end flow of code changes, automating build, test, and deployment stages.
2. **AWS CodeBuild**: Builds and tests the application code, generating deployable artifacts.
3. **Amazon S3**: Stores artifacts like build outputs and deployment files.
4. **AWS Systems Manager (SSM) Parameter Store**: Securely manages configuration data and secrets used during deployment.
5. **Amazon EKS**: Serves as the deployment environment for containerized workloads, providing scalability and orchestration.

**Flow Overview**:

- CodePipeline orchestrates the process.
- CodeBuild validates and compiles the code.
- Artifacts are stored in S3.
- EKS pulls secure configurations from SSM Parameter Store.
- Applications are deployed to the EKS cluster.

This architecture ensures automation, security, and scalability for modern DevSecOps workflows.

But this isn't all. There are some security tools that we have in place to make this happen, but I'll explain that in more detail as you go through this project. The fun begins... now.

[Damien Burks]: https://www.youtube.com/@damienjburks
