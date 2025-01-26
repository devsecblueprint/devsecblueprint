---
id: create-jenkins-piepline
title: Creating & Configuring Jenkins Pipeline
description: A step-by-step guide to creating a Jenkins pipeline for OWASP Juice Shop using Gitea, SonarQube, and SSH keys.
sidebar_position: 2
---

## Step 1: Configure Access Token in Gitea

1. In Gitea, click on your user avatar at the top right, then select **Settings** > **Applications**.

   ![Applications](/img/projects/devsecops-home-lab/create-configure-pipeline/gitea-manage-access-tokens.png)

2. Enter a token name (e.g., `Jenkins`), set it to `Private`, and select all permissions as READ/WRITE. Click **Generate Token**.

   ![Generate Token](/img/projects/devsecops-home-lab/create-configure-pipeline/gitea-configure-token-permissions.png)

3. Copy the token and store it in a secure place. This token will be used for Jenkins authentication.

## Step 2: Install Required Plugins in Jenkins

1. Log into Jenkins. From the **Dashboard**, click **Manage Jenkins** > **Manage Plugins**.

   ![Manage Plugins](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-manage-plugins.png)

2. Under **Available Plugins**, search for and install the following:

   - **Gitea**
   - **SonarQube Scanner**
   - **Prometheus Metrics**

   ![Install Plugins](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-install-plugins.png)

## Step 3: Create Jenkins Pipeline

1. From the Jenkins **Dashboard**, click **New Item**.

   ![New Item](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-dashboard.png)

2. Select **Organization Folder** and name it (e.g., `OWASP Juice Shop Pipeline`).

   ![Organization Folder](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-organization-folder.png)

3. Scroll down to **Repository Sources** and select **Gitea Organization**.

   ![Repository Sources](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-configure-gitea-pipeline.png)

4. Under **Credentials**, click **Add**. Select the organization folder name, set the **Kind** to **Gitea Personal Access Token (PAT)**, and paste the token generated from Gitea.

   ![Gitea PAT](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-configure-gitea-pat.png)

5. Set the **Owner** to your Gitea username, and then click **Apply** and **Save**.

   ![Save Configuration](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-config-gitea-organization.png)

## Step 4: Configure Webhook in Gitea

1. In Jenkins, go to **Manage Jenkins** > **Configure System**. Scroll down to **Gitea Servers** and add your Gitea server details.

   ![Gitea Server](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-config-gitea-server.png)

   - **Discover branches**: Only branches filed as PRs or master/main branch.
   - **Discover pull requests from origin**: Both the current pull request revision and the pull request merged with the current target branch revision.

2. Click **Apply** and **Save**.

3. In Gitea, navigate to the project, click on **Settings** > **Webhooks**.

   ![Webhooks](/img/projects/devsecops-home-lab/create-configure-pipeline/gitea-config-webhook.png)

4. Click **Add Webhook**, then select **Gitea**. Fill out the form:

   - **URL**: `<http://localhost:8080/gitea-webhook/post>`
   - **Method**: `POST`
   - **Content Type**: `application/json`
   - **Branch filter**: `*`

   ![Add Webhook](/img/projects/devsecops-home-lab/create-configure-pipeline/gitea-add-webhook-jenkins.png)

5. Click **Add Webhook** to save the configuration.

## Step 5: Configure SSH Keys

1. On your local machine (DSB Hub), generate an SSH key pair:

   ```bash
   ssh-keygen -t rsa -b 4096 -C "jenkins@dsb-hub.com"
   ```

   ```plaintext
   Generating public/private rsa key pair.
   Enter file in which to save the key (/home/<your_username>/.ssh/id_rsa):
   Enter passphrase (empty for no passphrase):
   Enter same passphrase again:
   Your identification has been saved in /home/<your_username>/.ssh/id_rsa
   Your public key has been saved in /home/<your_username>/.ssh/id_rsa.pub
   The key fingerprint is:
   SHA256:iIitv6/AYHsTTND7ooLJtG0M2NZrOWMer7E0E6hZ8XI jenkins@dsb-hub.com
   The key's randomart image is:
   ```

2. Copy the public key to your remote server:

   ```bash
   ssh-copy-id <your_username>@dsb-node-01.local
   ```

3. In Jenkins, go to **Manage Jenkins** > **Credentials** > **System** > **Global Credentials (unrestricted)**. Select **Add Credentials** and choose **SSH Username with private key**.

   ![SSH Credentials](/img/projects/devsecops-home-lab/create-configure-pipeline/jenkins-config-ssh-username.png)

4. Fill out the form and hit **Create** to store your SSH credentials.

## Conclusion

You've now successfully set up a Jenkins pipeline for the OWASP Juice Shop project with Gitea, SonarQube, and Docker integration. Your pipeline is configured to handle code quality checks, security scans, and deployments, ensuring that your application maintains a high standard throughout the development lifecycle.
