---
id: executing-pipeline
title: Running the Pipeline and Analyzing Outputs
sidebar_position: 2
---

## Overview

With the infrastructure deployed and verified, the next step is to execute the pipeline and analyze its outputs. This guide will walk you through running the pipeline, reviewing security scan results, and testing the deployed application.

## Running the Pipeline

1. Open the **Cloud Build Dashboard** and navigate to the `gcp-fastapi` pipeline. Click the pipeline name.
   ![Pipeline Dashboard](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/image-11.png)
2. Click **Run Trigger**, then confirm by clicking **Run**. This action triggers the pipeline to:

   - Pull the latest code from the GitHub repository.
   - Build the project.
   - Run tests and security scans.
   - Deploy the application into the GKE Cluster.

   > **Note**: The pipeline process may take 10-30 minutes to complete. Use this time to take a break and return once it finishes.

## Reviewing Results

After the pipeline completes, review the results of the security scans. Below are examples from Snyk and Trivy:

![Snyk Results](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/image-12.png)

> **Snyk Results**

![Trivy Results](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/image-13.png)

> **Trivy Results**

- The Trivy scan results are extensive and might be challenging to address comprehensively. Focus on the most critical issues first.
- If you want the pipeline to fail for certain vulnerabilities, you can configure the `cloudbuild.yaml` file in the `GCP-FastAPI` repository accordingly.

  > **Note**: Vulnerabilities may evolve over time, so periodic reviews and updates are essential.

## Testing the API Application

1. Open the **GKE Clusters Dashboard** and select the `dsb-devsecops-cluster`.
2. Under **Resources**, navigate to **Service and Networking > Services** and locate the `gcp-fastapi` service. This will display the following screen:
   ![Service Dashboard](/img/projects/devsecops-pipeline-gcp/deployment-and-testing/image-14.png)

3. Copy the provided URL and paste it into your web browser. It should resemble the following:

```text
http://aacbaaa4740274a1a83351e8723871d7-2065184365.us-central1.cloudfunctions.net/
```
