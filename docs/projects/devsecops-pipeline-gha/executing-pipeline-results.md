---
id: execution-pipeline-results
title: Pipeline Execution & Results
sidebar_position: 4
---

## Overview

With your infrastructure deployed and everything set up, it's time to put the pipeline to work and see it in action. This section walks you through triggering the pipeline, reviewing the results from the various security scans, and verifying that the Docker image has been successfully published to GitHub Container Registry (GHCR).

## Running the Pipeline

1. Log into GitHub, navigate to your `python-fastapi` repository, and click the **Actions** tab near the top of the page.  
   ![Navigate to Actions](/img/projects/devsecops-pipeline-gha/python-fastapi-actions.png)

2. On the left-hand sidebar, click on **Main Workflow**, then hit the **Run workflow** button on the right-hand side.  
   ![Run Workflow](/img/projects/devsecops-pipeline-gha/running-workflow-example.png)

3. Once started, your pipeline should begin executing. It should look something like this:  
   ![Pipeline Running](/img/projects/devsecops-pipeline-gha/running-pipeline-example.png)
   > **NOTE:** The workflow may take 5–7 minutes to complete. Feel free to take a break while it runs.

## Reviewing the Results

Once the pipeline completes, it’s time to dive into the results. Here’s what to look for:

### SonarCloud Analysis

If SonarCloud is properly configured, your repository should already be scanned once the pipeline completes. Head to your SonarCloud dashboard to review:

- **Code Smells**
- **Vulnerabilities**
- **Security Hotspots**

Try introducing a known vulnerability or poor code pattern just to see how well the scanner picks it up, and play around more with the console to great your own Quality Gates.

![SonarCloud Dashboard](/img/projects/devsecops-pipeline-gha/main-branch-summary-sonarcloud.png)  
![Security Hotspots](/img/projects/devsecops-pipeline-gha/security-hotspots.png)

### Trivy Scan Results

Trivy scan results are uploaded to GitHub under the **Security** tab in the **Code Scanning Alerts** section. Here, you can view any critical or high-severity vulnerabilities found in your Docker image.

![Trivy Results in GitHub](/img/projects/devsecops-pipeline-gha/trivy-results-codescanning.png)

## Conclusion

That’s it! You’ve successfully run your GitHub Actions DevSecOps pipeline!
