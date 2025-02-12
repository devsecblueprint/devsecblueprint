---
id: setup-terraform-cloud
title: Setting Up Terraform Cloud
sidebar_position: 3
---

## Overview

Terraform Cloud is an essential tool that simplifies infrastructure management and will quickly become a key part of your workflow. If you’re unfamiliar with Terraform, it’s highly recommended that you take some time to study it before proceeding. This guide will walk you through creating a Terraform Cloud account and setting up your first organization.

## Creating Your Account and Organization

1. Navigate to the [Terraform Cloud Sign-Up Page](https://app.terraform.io/public/signup/account).
2. Click **Continue with HCP account** to proceed with registration.
3. Select **Sign Up** at the bottom of the page, then click **Continue with GitHub** to link your account.

   > **Note:** If you are redirected back to the sign-in page, click **Continue with HCP** and then choose **Sign in with GitHub**.

4. Once logged in, you should arrive at the Terraform Cloud dashboard. If the "DSB" organization is not already created, it will appear empty:
   ![Terraform Cloud Dashboard](/img/projects/devsecops-pipeline-gcp/setup/tf-workspace-name.png)

5. Click **Create Organization**, and for the organization name, enter **DSB**. You can rename this organization later as needed after configuring the code.
6. Inside of the organization, create an API-Driven Workspace called `dsb-gcp-devsecops-infra`.
   ![Organization Creation](/img/projects/devsecops-pipeline-gcp/setup/tf-workspace-creation.png)
