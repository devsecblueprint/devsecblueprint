---
id: configuring-deployment-user
title: Configuring Deployment User/Role in AWS
sidebar_position: 4
---

## Overview

This guide will help you set up an IAM user in AWS that Terraform can assume to deploy infrastructure changes. By this stage, you should already have an AWS account ready for deployment.

## Creating and Configuring an IAM User

1. Log in to your AWS account.
2. Navigate to the **IAM Dashboard** and select **Users**, then click **Create User**.
3. Enter a **User Name** and click **Next**.
4. Under **Permissions**, select **Attach Policies Directly**, choose the **AdministratorAccess** policy, and click **Next**:

   ![Attach Policies Directly](/img/projects/devsecops-pipeline-aws/setup/image-3.png)

5. Click **Create User** to finalize the setup and proceed to the user's dashboard:

   ![User Dashboard](/img/projects/devsecops-pipeline-aws/setup/image-5.png)

6. On the right-hand side, click **Create Access Key** and follow these steps:
   1. **Use Case:** Select **CLI**, then confirm.
   2. Add a description for the access key and click **Create Access Key**.
   3. Click **Download CSV File** and save it in a secure location. These credentials will be required later.

With these steps completed, your IAM user is set up and ready to be used for Terraform deployments.
