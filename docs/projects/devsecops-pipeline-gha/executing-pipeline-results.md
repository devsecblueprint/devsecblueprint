---
id: execution-pipeline-results
title: Pipeline Execution & Results
sidebar_position: 4
---

## Overview

With your infrastructure deployed and everything wired up, it’s time to put the pipeline to work and see it in action. This section walks you through running the pipeline, checking the results from the various security scans, and verifying that your Docker image has been successfully published to GitHub Container Registry (GHCR).

## Running the Pipeline

1. Head over to your `python-fastapi` repository on GitHub and click the **Actions** tab at the top.  
   ![Navigate to Actions](/img/projects/devsecops-pipeline-gha/python-fastapi-actions.png)

2. In the left-hand sidebar, select **Main Workflow**, then click **Run workflow** on the right.  
   ![Run Workflow](/img/projects/devsecops-pipeline-gha/running-workflow-example.png)

3. Once triggered, your pipeline will kick off and begin executing. It should look something like this:  
   ![Pipeline Running](/img/projects/devsecops-pipeline-gha/running-pipeline-example.png)

   > **Note:** This job takes about 5–7 minutes to complete, so go grab a coffee and check back in a bit.

## Reviewing the Results

After the workflow finishes running, here’s how to review the key outputs from your DevSecOps pipeline:

### GitHub Container Registry (GHCR)

Back on your repository’s homepage, scroll down to the **Packages** section. You should see your Docker image listed there. Click the image name to view details, including how to pull it using Docker.

![Packages Section](/img/projects/devsecops-pipeline-gha/releases-packages.png)  
![Pulling Image and Tags](/img/projects/devsecops-pipeline-gha/example-private-image.png)

### SonarCloud Analysis

If you’ve properly integrated SonarCloud, your repository should be scanned automatically as part of the pipeline. Navigate to your SonarCloud dashboard to explore:

- Code Smells
- Vulnerabilities
- Security Hotspots

Feel free to experiment by adding some insecure code or edge cases to test the scanner. You can also customize your **Quality Gates** directly from the SonarCloud interface.

![SonarCloud Dashboard](/img/projects/devsecops-pipeline-gha/main-branch-summary-sonarcloud.png)  
![Security Hotspots](/img/projects/devsecops-pipeline-gha/security-hotspots.png)

### OWASP ZAP Scan

The results of the OWASP ZAP scan can be found directly in the GitHub Actions logs. This scan runs against your running Docker container to detect common web vulnerabilities like injection flaws, insecure headers, and more.

Here’s an example of what it looks like in the workflow logs:  
![OWASP ZAP Logs](/img/projects/devsecops-pipeline-gha/owasp-zap-scan-logs.png)

### Trivy Scan Results

Trivy scan results are automatically uploaded to GitHub under the **Security** tab → **Code scanning alerts**. From there, you’ll be able to view any critical or high-severity vulnerabilities identified in your image.

![Trivy Results in GitHub](/img/projects/devsecops-pipeline-gha/trivy-results-codescanning.png)

## Conclusion

You're done!!! You’ve successfully executed your GitHub Actions DevSecOps pipeline. You’ve built, scanned, tested, and pushed a containerized app with security built in from the start.
