---
id: setup-sonarcloud
title: Setting Up SonarCloud
sidebar_position: 2
---

## Overview

This guide will walk you through the process of integrating SonarCloud into your GitHub repository. If you're unfamiliar with SonarCloud, it's a cloud-based code quality and security service that performs Static Application Security Testing (SAST). It helps identify bugs, vulnerabilities, and code smells in your application—before they make it to production. SonarCloud seamlessly integrates with GitHub and supports over 25 programming languages. For more background, check out this article: [SonarCloud Documentation](https://docs.sonarsource.com/sonarqube-cloud/). Plus, SonarCloud is **free**, which is a HUGE plus.

## Instructions

1. Go to the [SonarCloud Login Page](https://sonarcloud.io/login).

1. Click **Sign in with GitHub** to create your SonarCloud account.  
   ![Sign in with GitHub](/img/projects/devsecops-pipeline-gha/setup/sonarcloud-login.png)

1. After signing in, you’ll be prompted to install the SonarCloud GitHub App.  
   Select your GitHub account or organization and proceed with the installation.  
   ![Select Your App](/img/projects/devsecops-pipeline-gha/setup/default.png)  
   ![Install and Authorize](/img/projects/devsecops-pipeline-gha/setup/install_sonarcloud_github.png)

1. Once installed, you’ll land on the **Analyze Projects** screen.  
   Select the `python-fastapi` repository to import it into SonarCloud.  
   ![Analyze Projects](/img/projects/devsecops-pipeline-gha/setup/analyze_projects.png)

1. After importing, you’ll be redirected to your project dashboard.  
   It may look empty at first—but once your pipeline runs, it’ll populate with results like this:  
   ![SonarCloud Dashboard](/img/projects/devsecops-pipeline-gha/setup/python-fastapi-dashboard.png)
