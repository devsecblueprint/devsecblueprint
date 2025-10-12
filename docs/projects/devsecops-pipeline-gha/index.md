---
id: devsecops-pipeline-gha
title: DevSecOps Pipeline - GitHub Actions
description: Build a DevSecOps Pipeline using GitHub Actions!
sidebar_position: 3
---

Author(s): [Timothy Hogue], [Damien Burks]

<!-- markdownlint-disable MD033 -->
<p align="center">
   <img src="/img/projects/devsecops-pipeline-gha/gha_logo.svg" alt="GitHub Actions Logo" width="400" />
</p>

## Prerequisities

1. Before you begin this, you will want to have some knowledge of GCP services and how they work, as well as prior knowledge of Terraform. You can take a look at [Building Cloud DevSecOps Pipelines (In Theory)](../../blueprint/devsecops/implementing-cloud-devsecops.md#other-infrastructure-as-code-iac-languages) for more information.
1. You will also want to ensure that you have an GitHub account created. If you don't have a GitHub account created, you can follow the documentation here: [Creating A GitHub Account](https://docs.github.com/en/get-started/start-your-journey/creating-an-account-on-github)
1. Make sure you have the following installed on your local machine:
   - [Python](https://www.python.org/downloads/)
   - [Git](https://git-scm.com/downloads)
   - [Docker](https://docs.docker.com/engine/install/)

## Overview

So you've decided to go down the path of building a DevSecOps pipeline within GitHub? If so, you've come to the right place! We are going to show you how to build your own DevSecOps pipeline using GitHub Actions. Unlike the any of the other pipelines, we are not going to build and our own infrastructure. We are going to leverage the infrastructure that GitHub has that their Actions rely on.

Luckily for you all, you won't need to do anything. we've taken the liberty of developing all of the code for you. These are the _one_ GitHub repositories that you need to look at before we get started:

1. DevSecOps Pipeline Infrastructure (Python FastAPI): https://github.com/devsecblueprint/python-fastapi/.github/workflows

## Architecture Diagram

<p align="center">
![Architecture Diagram](/img/projects/devsecops-pipeline-gha/architecture.drawio.svg)
</p>

### Architecture Breakdown

At a **VERY** high level, this architecture briefly covers the services that we will be leveraging for the DevSecOps Pipelines. Here are the descriptions with intent of each service:

- **GitHub**: Acts as the central version control system and CI/CD trigger point. Engineers push changes and raise pull requests here, which kick off the pipeline.
- **GitHub Actions**: Orchestrates all automation in the pipeline. It handles build, test, static/dynamic scanning, and image publishing workflows.
- **SonarCloud**: Performs Static Application Security Testing (SAST) on the codebase for quality issues and security vulnerabilities before merging.
- **Trivy**: Scans the Docker image and dependencies for known vulnerabilities (CVEs) during the build process.
- **ZAP by Checkmarx**: Executes Dynamic Application Security Testing (DAST) against the running container to catch runtime vulnerabilities such as XSS, injection flaws, and misconfigurations.
- **Docker**: Serves as the containerization platform for building and packaging the application, which is used both for testing and deployment.
- **GitHub Container Registry (GHCR)**: Stores the final, security-validated Docker image that can be pulled into downstream environments.

### Flow Diagram

Now that we've covered the architecture diagram, let's put this together so you can understand the flow and who everything is supposed to work.

<p align="center">
![Flow Diagram](/img/projects/devsecops-pipeline-gha/flow.drawio.svg)
</p>

#### Flow Diagram Explained

1. An engineer pushes their changes to the repository and opens a Pull Request (PR).
1. Once the PR is created, SonarCloud automatically scans the codebase for bugs, code smells, and security vulnerabilities. If any critical issues are detected, the PR check will fail.
1. In parallel, GitHub Actions is triggered to build the project or Docker image.
1. Unit tests are executed to validate the functionality of the changes.
1. Upon successful completion of unit tests:
   1. An ZAP by Checkmarx scan runs against the running Docker container to detect common web application vulnerabilities.
   1. A Trivy scan is also performed to identify vulnerabilities in dependencies and the container image.
1. If all checks pass, a reviewer merges the PR. This triggers the pipeline to run again for the main branch, and the final, verified Docker image is published to GitHub Container Registry.

## What You’ll Learn

By working through this guide, you’ll gain hands-on experience building and deploying a secure DevSecOps pipeline using GitHub Actions. Specifically, you will learn how to:

- Build a secure DevSecOps pipeline using GitHub Actions
- Automate builds, tests, and security scans in pull request workflows
- Run SAST with SonarCloud
- Scan containers and dependencies using Trivy
- Perform DAST with ZAP by Checkmarx
- Package applications with Docker and publishing to GHCR
- Enforce security gates before merging code
- Leverage GitHub’s hosted infrastructure for CI/CD

With all that being stated, **Please follow the order of the documents, otherwise you'll most likely run into errors and get lost.**

<!-- markdownlint-enable MD033 -->

[Damien Burks]: https://damienjburks.com
[Timothy Hogue]: https://www.linkedin.com/in/timothy-hogue-2b2722230/
