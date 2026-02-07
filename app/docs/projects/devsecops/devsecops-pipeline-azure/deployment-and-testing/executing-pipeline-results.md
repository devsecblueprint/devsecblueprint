---
id: executing-pipeline
title: Running the Pipeline & Analyzing Outputs
sidebar_position: 2
---

## Overview

With the infrastructure deployed and verified, the next step is to execute the pipeline and analyze its outputs. This guide will walk you through running the pipeline, reviewing the results of integrated security scans, and validating the deployed container image.

## Running the Pipeline

1. Navigate to the **Azure DevOps project** called `python-fastapi`.
   ![Azure DevOps Project](/img/projects/devsecops-pipeline-azure/deployment-and-testing/image-3.png)

2. Click the project, then select **Pipelines**. Under the **All** tab, click the pipeline named **Default**.
   ![Default Pipeline](/img/projects/devsecops-pipeline-azure/deployment-and-testing/image-4.png)

3. Click **Run pipeline** and wait for the results. This process typically takes **15–20 minutes**.
   ![Run Pipeline](/img/projects/devsecops-pipeline-azure/deployment-and-testing/image-5.png)

:::important
If you encounter an exception related to enabling parallelism, you’ll need to fill out this request form: [Azure DevOps Parallelism Request](https://aka.ms/azpipelines-parallelism-request). Approval takes about **3 business days**, and no notification will be sent once your request is approved.
:::

## Reviewing Results

Once the pipeline completes, you can review the outputs from multiple security scans.

### Trivy Dependency Scan

![Trivy Dependency Scan](/img/projects/devsecops-pipeline-azure/deployment-and-testing/image-6.png)

- Detects vulnerabilities in application dependencies.
- Focus on addressing **critical** and **high-severity** issues first.

### Trivy Image Scan

![Trivy Image Scan](/img/projects/devsecops-pipeline-azure/deployment-and-testing/image-7.png)

- Scans the built Docker image for OS-level vulnerabilities.
- Ensures your container base image and packages are hardened before deployment.

### OWASP ZAP Scan

![ZAP Scan Results](/img/projects/devsecops-pipeline-azure/deployment-and-testing/image-8.png)

- Runs a dynamic application security test (DAST) against the deployed FastAPI service.
- Detects web vulnerabilities such as injection flaws, insecure headers, and weak authentication.

:::tip
Trivy scan results can be extensive. If you want the pipeline to fail on specific vulnerabilities, you can modify the `unit-sec-test.yml` file in the `azure-python-fastapi` repository to enforce stricter thresholds.
:::

## Validating the Image

1. Log in to the **Azure Portal** and search for your container registry (`DSBContainerRegistry`).

   - Navigate to **Repositories** → `python-fastapi`.
     ![Container Registry Repo](/img/projects/devsecops-pipeline-azure/deployment-and-testing/image-9.png)

2. Click the repository link and verify that a new image tag has been published.
   ![Image Tag](/img/projects/devsecops-pipeline-azure/deployment-and-testing/image-10.png)

This confirms that your pipeline not only scanned the application but also successfully pushed the image to your Azure Container Registry.

## Conclusion

You’ve now executed the Azure DevOps pipeline and validated its outputs:

- Security scans (Trivy + OWASP ZAP) provide visibility into vulnerabilities.
- Scan thresholds can be tuned to enforce stricter build gates.
- The FastAPI Docker image is built, scanned, and pushed into Azure Container Registry.

**You’re done!** Your DevSecOps pipeline is fully operational, combining automated builds, security checks, and deployments.
