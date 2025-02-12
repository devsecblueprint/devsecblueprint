---
id: executing-pipeline
title: Running the Pipeline and Analyzing Outputs
sidebar_position: 2
---

## Overview

With the infrastructure deployed and verified, the next step is to execute the pipeline and analyze its outputs. This guide will walk you through running the pipeline, reviewing security scan results, and testing the deployed application.

## Running the Pipeline

1. Open the **Cloud Build Dashboard**, click Triggers, and find to the `gh-trigger-gcp-python-fastapi` pipeline.

   ![alt text](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/python-fastapi-trigger.png)

2. Click **Run Trigger**, then confirm by clicking **Run**. This action triggers the pipeline to:

   - Pull the latest code from the GitHub repository.
   - Build the project.
   - Run tests and security scans.
   - Deploy the application into the GKE Cluster.

   > **Note**: The pipeline process may take 10-30 minutes to complete. Use this time to take a break and return once it finishes.

## Reviewing Results

After the pipeline completes, review the results of the security scans. Below are examples from Snyk and Trivy:

![alt text](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/snyk-scan-results.png)

> **Snyk Results**

![alt text](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/trivy-scan-results.png)

> **Trivy Results**

- The Trivy scan results are extensive and might be challenging to address comprehensively. Focus on the most critical issues first.
- If you want the pipeline to fail for certain vulnerabilities, you can configure the `cloudbuild.yaml` file in the `GCP-FastAPI` repository accordingly.

  > **NOTE**: Vulnerabilities may evolve over time, so periodic reviews and updates are essential.

## Testing the API Application

1. Open the **Cloud Run dashboard** and select the `gcp-python-fastapi-service`.
2. At the top of the screen, you should see the URL to the running service.

   ![alt text](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/fastapi-url-python.png)

3. Copy the provided URL and paste it into your web browser. It should resemble the following:

   ```text
   https://gcp-python-fastapi-service-724455289756.us-central1.run.app
   ```

   ![alt text](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/gcp-python-fastapi-service.png)

You're done!
