---
id: testing-pipeline
title: Triggering Jenkins Pipeline
sidebar_position: 1
---

## Triggering the OWASP Juice Shop Pipeline in Jenkins

1. Log into Jenkins

   - Start by logging into your Jenkins server using your credentials.

2. Navigate to the OWASP Juice Shop Pipeline

   - From the Jenkins Dashboard, locate and select the **OWASP Juice Shop** pipeline from your list of projects.

3. Select the Master Branch

   - Inside the pipeline project, click on the **master** branch to view its details and available actions.

4. Trigger the Pipeline Build

   - Click the **Build Now** button to manually trigger the pipeline build for the master branch.

5. Monitor the Pipeline Execution

   - As the pipeline runs, you can monitor the execution of each stage in real-time. Jenkins will display logs and outputs for each step, allowing you to track the progress.

6. Verify the Deployment

   - Once the pipeline has successfully completed, verify the deployment by opening a web browser and navigating to:

     ```bash
     http://<your_ip_address>:8084/
     ```

   - The OWASP Juice Shop application should be accessible at this URL, confirming that the deployment was successful.

7. Automate Pipeline Triggers

   - Note that your Gitea repository should be configured to automatically trigger this Jenkins pipeline whenever a commit is made to the master branch. This ensures continuous integration and deployment for your project.

## Conclusion

Congratulations! Your Jenkins pipeline is now set up and working. You’ve successfully triggered, monitored, and verified a build and deployment for the OWASP Juice Shop application.
1
