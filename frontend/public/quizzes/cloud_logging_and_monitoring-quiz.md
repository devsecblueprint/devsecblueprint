---
module_id: cloud-logging-and-monitoring
passing_score: 80
---

## Question 1

How does the module distinguish between **Logs** and **Events** in the cloud?

A. Logs are real-time signals; Events are historical records of actions.
B. Logs are records of actions taken by users or services; Events are real-time signals that something has occurred.
C. Logs are only created by human users; Events are only created by automated scripts.
D. There is no technical difference between logs and events in cloud security.

**Correct Answer:** B

**Explanation:** Logging provides the "paper trail" of what happened in the past, while events provide the "motion detection" needed for real-time awareness.

---

## Question 2

What is the primary risk of having **Short Retention Periods** for your cloud logs?

A. It makes the cloud environment too slow for the developers.
B. Logs may be deleted before investigations or audits can successfully use them.
C. It prevents the system from generating real-time events.
D. It forces the cloud provider to charge more for data storage.

**Correct Answer:** B

**Explanation:** Without adequate retention, the "security camera footage" of your environment is lost before an analyst has a chance to review it during a forensic investigation or audit.

---

## Question 3

Which cloud service is used to route real-time signals to automation in **AWS**?

A. CloudTrail
B. CloudWatch Logs
C. EventBridge
D. Activity Logs

**Correct Answer:** C

**Explanation:** EventBridge is the serverless event bus that takes real-time signals and routes them to targets like Lambda functions for automated response.

---

## Question 4

What visibility gap occurs when records live in separate accounts or regions without being combined?

A. Dormant Events
B. Uncentralized Storage
C. Partial Logging
D. Missing Context

**Correct Answer:** B

**Explanation:** Uncentralized storage creates data silos, making it nearly impossible to correlate activity across a large, multi-account organization.

---

## Question 5

In the **Visibility Lifecycle**, what happens immediately after an action occurs?

A. An event is emitted.
B. A log is recorded.
C. A response is triggered.
D. Processing happens.

**Correct Answer:** B

**Explanation:** The first technical step after a change is made by a user or workload is for the cloud provider to capture the details of that action in a log.

---

## Question 6

What is the primary purpose of the **Security Value Chain**?

A. To reduce the cost of cloud computing resources.
B. To transform raw telemetry from logs and events into active defense.
C. To automate the creation of new user accounts.
D. To replace the need for encryption and secrets management.

**Correct Answer:** B

**Explanation:** The value chain is the process of moving from mere passive observation (data collection) to intelligent, automated security responses.

---

## Question 7

Which of the following is considered a **Best Practice** for logging and event security?

A. Only enable logging in production regions to save money.
B. Centralize and encrypt logs in a secured location.
C. Grant write access to logs to all developers for easier troubleshooting.
D. Avoid using automated event handlers to prevent false alarms.

**Correct Answer:** B

**Explanation:** Centralization provides a single source of truth for the entire environment, while encryption ensures those records remain untampered and secure.

---

## Question 8

What does the "Correlation" step in the Security Value Chain aim to achieve?

A. Deleting duplicate logs to save storage space
B. Connecting events to specific users, systems, and environments
C. Encrypting logs before they are sent to the SIEM
D. Routing events to different cloud providers

**Correct Answer:** B

**Explanation:** Correlation allows a security architect to see the full "story" of an incident by linking related actions together across different data points.

---

## Question 9

According to the module, if secrets protect your systems, visibility protects your ******\_\_****** of them.

A. Deployment
B. Understanding
C. Ownership
D. Encryption

**Correct Answer:** B

**Explanation:** Visibility ensures you are not "operating blind" and provides the context needed to truly understand the activity happening within your perimeter.

---

## Question 10

According to the **Capstone Goal**, what two elements must a functioning pipeline provide?

A. Encryption and Throttling
B. History (via logs) and Real-time awareness (via events)
C. Higher costs and more complex code
D. Manual auditing and physical security

**Correct Answer:** B

**Explanation:** A complete visibility strategy requires both the historical record for forensic analysis and the ability to act on changes instantly as they happen.

---
