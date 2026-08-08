---
module_id: what-is-cloud-security-development
passing_score: 80
---

## Question 1

How is "Cloud Security Development" defined in comparison to standard Cloud Security?

A. It is the practice of only using built-in provider tools to configure settings.
B. It is the engineering of custom logic, tools, and automations that secure cloud environments.
C. It focuses exclusively on the software code within an application.
D. It is a manual process used to audit hardware in a provider's data center.

**Correct Answer:** B

**Explanation:** Cloud Security Development involves developing custom logic through APIs and SDKs to automate guardrails and enforce best practices at scale.

---

## Question 2

Why is Cloud Security Development considered essential for large organizations?

A. It replaces the need for any Identity and Access Management (IAM).
B. It allows organizations to stop using encryption for data at rest.
C. Manual processes are no longer enough to keep up with the speed and scale of the cloud.
D. It ensures that only the cloud provider is responsible for security.

**Correct Answer:** C

**Explanation:** With the speed of cloud growth, automation and custom security capabilities are required to stay proactive and handle the volume of new services and permissions.

---

## Question 3

Which core concept acts as the "source of truth" to identify "who did what" in the cloud?

A. Identity and Access Management (IAM)
B. Serverless Security Functions
C. Events and Logs
D. Encryption Keys (KMS)

**Correct Answer:** C

**Explanation:** Events represent actions in near real-time, while logs represent historical records; together they allow developers to build detection and response pipelines.

---

## Question 4

What is the primary focus of **DevSecOps** compared to Cloud Security Development?

A. Securing the cloud environment itself
B. Securing the software delivery lifecycle (CI/CD, code pipelines)
C. Managing physical server hardware
D. Building API-driven detections for infrastructure

**Correct Answer:** B

**Explanation:** DevSecOps focuses on building security *into* code (scanning/testing), whereas Cloud Security Development builds security *around* the infrastructure (tools/guardrails).

---

## Question 5

Which of the following is a common use case for Cloud Security Development?

A. Manually reviewing every pull request for syntax errors
B. Auto-remediating public resources or tagging owners automatically
C. Developing new marketing features for a web application
D. Increasing the CPU capacity of a virtual machine

**Correct Answer:** B

**Explanation:** Cloud Security Development aims to automate enforcement, such as correcting misconfigurations or enforcing tag compliance via code.

---

## Question 6

Why are **Serverless Security Functions** (e.g., AWS Lambda) preferred for building lightweight controls?

A. They allow developers to ignore least privilege principles.
B. They can listen for specific events and respond immediately without managing infrastructure.
C. They are only used for historical log analysis, not real-time response.
D. They replace the need for any encryption or key management.

**Correct Answer:** B

**Explanation:** The serverless model is ideal for event-driven security, allowing for automated responses to triggers like an S3 bucket being made public.

---

## Question 7

What is a "Guardrail" in the context of Cloud Security engineering?

A. A physical barrier around a provider's data center
B. A policy that defines what "good" looks like, such as "no unencrypted storage"
C. The speed limit for data transfers in the cloud
D. A manual checklist used by developers once per year

**Correct Answer:** B

**Explanation:** Guardrails are automated policies built into tools or functions that continuously check for and enforce compliance with internal standards.

---

## Question 8

Which risk involves overly broad permissions granting users unintended access to workloads?

A. Data Exposure
B. Compliance Gaps
C. Privilege Escalation
D. Operational Fatigue

**Correct Answer:** C

**Explanation:** Overly permissive IAM roles can lead to privilege escalation, which is why Cloud Security developers build utilities to check for these risks continuously.

---

## Question 9

Which certification focuses specifically on securing AWS workloads and incident response?

A. Google Professional Cloud Security Engineer
B. AWS Certified Security – Specialty
C. HashiCorp Certified: Terraform Associate
D. Microsoft Certified: Cybersecurity Architect Expert

**Correct Answer:** B

**Explanation:** The AWS Security Specialty focuses on best practices for securing native workloads, responding to incidents, and cloud-native security.

---

## Question 10

Everything in Cloud Security development begins with which of the following?

A. Automation
B. Visibility
C. Encryption
D. Deployment

**Correct Answer:** B

**Explanation:** Visibility—knowing who did what, when, and where—is the foundation required to build detection pipelines and automated responses.