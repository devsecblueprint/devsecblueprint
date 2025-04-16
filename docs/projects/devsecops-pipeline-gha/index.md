---
id: devsecops-pipeline-gha
title: DevSecOps Pipeline - GitHub Actions
description: Build a DevSecOps Pipeline using GitHub Actions!
sidebar_position: 3
---

Author(s): [Timothy Hogue], [Damien Burks]

![GitHub Actions Logo](/img/projects/devsecops-pipeline-gha/gha_logo.svg)

## Prerequisities

1. Before you begin this, you will want to have some knowledge of GCP services and how they work, as well as prior knowledge of Terraform. You can take a look at [Building Cloud DevSecOps Pipelines (In Theory)](../../blueprint/implementing-cloud-devsecops.md#other-infrastructure-as-code-iac-languages) for more information.
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

![Architecture Diagram](/img/projects/devsecops-pipeline-gha/architecture.drawio.svg)

### Architecture Breakdown

At a **VERY** high level, this architecture briefly covers the services that we will be leveraging for the DevSecOps Pipelines. Here are the descriptions with intent of each service:

### Flow Diagram

Now that we've covered the architecture diagram, let's put this together so you can understand the flow and who everything is supposed to work.

![Flow Diagram](/img/projects/devsecops-pipeline-gha/flow.drawio.svg)

#### Flow Diagram Explained

## What You’ll Learn

By working through this guide, you’ll gain hands-on experience building and deploying a secure, cloud-native DevSecOps pipeline on GCP. Specifically, you will learn how to:

With all that being stated, **Please follow the order of the documents, otherwise you'll most likely run into errors and get lost.**

[Damien Burks]: https://www.youtube.com/@damienjburks
[Timothy Hogue]: https://www.linkedin.com/in/timothy-hogue-2b2722230/
