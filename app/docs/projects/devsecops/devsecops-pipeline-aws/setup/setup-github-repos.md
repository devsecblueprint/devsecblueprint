---
id: setup-github-repos
title: Setting Up GitHub Repositories
sidebar_position: 1
---

## Overview

This guide will walk you through the process of setting up GitHub repositories in your personal account. If you're unfamiliar with GitHub, it is a web-based platform that leverages Git, a version control system, to help developers manage and track changes in their code. It also facilitates collaboration on projects, tracks revisions, and enables code contributions from anywhere in the world. For more details, check out this article named [introduction to GitHub on GeeksforGeeks](https://www.geeksforgeeks.org/introduction-to-github/). Plus, GitHub offers free accounts, which is always a bonus!

## Prerequisites

Before proceeding, ensure you have a GitHub account. If you don't already have one, follow this [guide to create a GitHub account](https://docs.github.com/en/get-started/start-your-journey/creating-an-account-on-github).

## Configuration Steps

### Forking Repositories

To begin, you'll need to fork the repositories into your personal GitHub account:

1. Log in to your GitHub account.
2. Navigate to the landing page of the first project: [AWS DevSecOps Pipeline](https://github.com/devsecblueprint/aws-devsecops-pipeline).
3. Click the **Fork** button in the top-right corner.
4. Select your personal account as the **Owner** and click **Create Fork**. Ensure the **Copy the main branch only** option is enabled.

   ![alt text](/img/projects/devsecops-pipeline-aws/setup/image-8.png)

5. Repeat the above steps for the second project: [Awesome FastAPI](https://github.com/devsecblueprint/awsome-fastapi).
6. Clone both repositories onto your local machine using the following command, as an example:

   ```text
   git clone https://github.com/devsecblueprint/awsome-fastapi.git
   ```
