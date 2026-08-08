---
module_id: serverless
passing_score: 80
---

## Question 1

How does the module define "Serverless Computing" in the context of security engineering?

A. A method of security that requires no internet connection
B. A model where the cloud provider manages the infrastructure, allowing developers to run code without thinking about servers
C. A system where the security engineer is responsible for patching all underlying operating systems
D. A security protocol that only works for on-premises data centers

**Correct Answer:** B

**Explanation:** Serverless allows security teams to focus purely on the logic of their security functions while the provider handles provisioning, scaling, and management.

---

## Question 2

What is the primary role of **Orchestration** in a Cloud Security environment?

A. To manually review every log entry created by a user
B. To coordinate multiple serverless functions or workflows into a single automated process
C. To replace the need for an Identity and Access Management (IAM) system
D. To increase the cost of cloud services by adding more servers

**Correct Answer:** B

**Explanation:** Orchestration acts as a "conductor," connecting individual functions into a structured symphony of security automation.

---

## Question 3

Why is serverless computing considered a breakthrough for **Incident Response**?

A. It requires more humans to be involved in every decision
B. it turns detection into action, reducing response time from hours to seconds
C. It allows for the storage of plaintext passwords in function code
D. It prevents any cloud events from being triggered

**Correct Answer:** B

**Explanation:** Because serverless functions react instantly to events, they can quarantine compromised workloads or disable leaked keys in real time.

---

## Question 4

Which phase of the **Serverless Security Lifecycle** involves connecting functions into structured processes using services like AWS Step Functions?

A. Trigger
B. Execute
C. Orchestrate
D. Improve

**Correct Answer:** C

**Explanation:** Orchestration is the stage where multiple actions (like remediation and alerting) are chained together into a logical workflow.

---

## Question 5

Which of the following is an example of a **Compute Event** trigger for a security function?

A. Scanning an uploaded file for malware in a storage bucket
B. Detecting the creation of a risky IAM role
C. Quarantining an instance launched in an unapproved network
D. Routing a finding to a Slack channel

**Correct Answer:** C

**Explanation:** Compute events specifically relate to actions taken by or against virtual machines or workloads.

---

## Question 6

What is a significant security risk when a function is assigned an **Overprivileged Role**?

A. The function will run too slowly to be effective
B. It increases the blast radius of a compromise if the function logic is exploited
C. The cloud provider will charge extra for each permission granted
D. It prevents the function from being triggered by EventBridge

**Correct Answer:** B

**Explanation:** Following the principle of least privilege is vital; functions should only have the exact permissions needed to perform their job.

---

## Question 7

Why is **Input Validation** critical for serverless functions?

A. To ensure the cloud provider doesn't delete the function
B. To prevent unsanitized event payloads from leading to injection or privilege escalation
C. To allow the function to run without an IAM role
D. To bypass the need for centralized logging

**Correct Answer:** B

**Explanation:** Since functions process event data, that data must be treated as untrusted to prevent malicious payloads from subverting the function.

---

## Question 8

What is the purpose of using **Dead Letter Queues (DLQs)** in serverless security?

A. To store secrets that are no longer in use
B. To capture failed invocations for later investigation and observability
C. To prevent any logs from being recorded in CloudWatch
D. To automatically delete non-compliant resources

**Correct Answer:** B

**Explanation:** DLQs ensure that if a security automation fails, the failure is visible and can be investigated rather than failing silently.

---

## Question 9

Which service is used in **Azure** to chain actions and apply conditional logic for automation?

A. Step Functions
B. Logic Apps
C. Pub/Sub
D. CloudTrail

**Correct Answer:** B

**Explanation:** Azure Logic Apps (and Durable Functions) are the primary tools for workflow orchestration within the Azure ecosystem.

---

## Question 10

According to the **Capstone Goal**, what is the primary indicator of a successful serverless security mission?

A. Writing the longest possible code for a function
B. Demonstrating real-time detection and automated response to a security event
C. Using every single cloud provider at the same time
D. Disabling all logging to improve function performance

**Correct Answer:** B

**Explanation:** The goal of serverless security is to prove that you can move from a passive alert to an active, automated remediation.

---