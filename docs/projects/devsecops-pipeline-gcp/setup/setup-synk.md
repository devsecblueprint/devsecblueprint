---
id: setup-snyk
title: Setting Up Snyk Account
sidebar_position: 2
---

## Overview

This guide will help you create a Snyk account and generate the required token and organization ID for scanning purposes. If you're following along with the video, this document covers the steps that were not detailed due to time constraints.

## Account Creation Process

1. Navigate to the [Snyk Sign-Up Page](https://app.snyk.io/login).
2. Sign up using the **GitHub** option and follow the prompts to create your account.

   > **Note:** The sign-up process is straightforward and does not require a credit card initially.

3. Once registration is complete, you will be redirected to your Snyk dashboard:

   ![Snyk Dashboard](/img/projects/devsecops-pipeline-gcp/setup/snyk-dashboard.png)

## Obtaining Tokens and Organization ID

1. Click on your name at the bottom-left corner of the page and select **Account Settings**.
2. In the **General** section, locate the **Auth Token** field. Click **Generate** to create a token and make note of it. This token will be required later for integration.

   ![Generate Auth Token](/img/projects/devsecops-pipeline-gcp/setup/snyk-auth-token.png)

3. Navigate to the **Settings** page, scroll down to find the **Organization ID**, and note this ID as well. You’ll need it for configuring your environment.

   ![Organization ID](/img/projects/devsecops-pipeline-gcp/setup/snyk-organization-id.png)

With these steps completed, your Snyk account is ready to use!
