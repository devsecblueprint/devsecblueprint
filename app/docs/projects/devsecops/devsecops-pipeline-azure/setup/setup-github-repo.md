---
id: setup-github-repos
title: Setting Up GitHub Repositories
sidebar_position: 1
---

## Overview

Your pipeline relies on GitHub repositories to host both the application code and the infrastructure definitions. In this section, you’ll fork the required repositories into your personal GitHub account so you can make changes, push updates, and run the pipeline independently.

If you’re new to GitHub, it’s a web-based platform built on top of Git (a distributed version control system). It allows developers to manage code, track changes, collaborate, and contribute from anywhere in the world. For a quick primer, check out this [Introduction to GitHub](https://www.geeksforgeeks.org/introduction-to-github/) article.

:::tip
GitHub offers free accounts, so you can get started without any upfront cost.
:::

## Prerequisites

Before proceeding, make sure you have a **GitHub account**.

- If you don’t already have one, follow this [guide to create a GitHub account](https://docs.github.com/en/get-started/start-your-journey/creating-an-account-on-github).

## Configuration Steps

### Forking Repositories

1. Log in to your **GitHub account**.

2. Navigate to the first project:
   [Azure DevSecOps Infrastructure](https://github.com/devsecblueprint/azure-devsecops-pipeline)

3. Click the **Fork** button in the top-right corner.

4. Select your personal account as the **Owner** and click **Create Fork**.

   - Make sure the option **Copy the main branch only** is enabled.

     ![Fork Repo](/img/projects/devsecops-pipeline-azure/setup/image-10.png)

5. Repeat the same steps for the second project:

   [Azure FastAPI](https://github.com/devsecblueprint/azure-python-fastapi)

6. Once forked, clone both repositories to your local machine. For example:

   ```bash
   git clone https://github.com/<your-username>/azure-python-fastapi
   git clone https://github.com/<your-username>/azure-devsecops-pipeline
   ```

## Conclusion

That’s it! 🎉 You now have your own copies of the **infrastructure** and **application** repositories inside your GitHub account. With these set up, you’re ready to configure secrets and wire up your DevSecOps pipeline in the next steps.
