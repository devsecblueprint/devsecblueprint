---
id: setup-azure-devops
title: Setting Up Azure DevOps
sidebar_position: 4
---

## Overview

Before wiring up your pipeline, you’ll need an Azure DevOps organization and a Personal Access Token (PAT). This section walks you through creating your DevOps organization, setting its visibility, and generating a PAT that will be used later in your pipeline configuration.

## Creating an Azure DevOps Organization

1. While logged into the **Azure Portal**, open a new tab and go to [Azure DevOps](https://dev.azure.com).

   - Fill out the form with your details and click **Continue**.
   - Make sure to set the **Visibility** to **Private**.

     ![Azure DevOps Form](/img/projects/devsecops-pipeline-azure/setup/image-4.png)

2. Once complete, navigate back to the Azure DevOps homepage.

   - Click **New organization** and choose a unique name (example: `devsecblueprint`).

     ![Create Organization](/img/projects/devsecops-pipeline-azure/setup/image-5.png)

## Generating a Personal Access Token (PAT)

1. In Azure DevOps, click the **gear icon** in the top-right corner and select **Personal access tokens**.

   ![Navigate to PAT](/img/projects/devsecops-pipeline-azure/setup/image-6.png)

2. Click **New Token**.

   - Set the scope to **Full access**.
   - Generate and **save the token securely** — you’ll use this later in your Terraform and pipeline setup.

## Conclusion

That’s it! 🎉 You now have an **Azure DevOps organization** and a **Personal Access Token** ready to go. With this in place, you’ll be able to integrate Azure DevOps into your pipeline workflows in the next steps.
