---
module_id: iac-security
passing_score: 80
---

## Question 1

How does the module define "Infrastructure as Code" (IaC)?

A. The process of manually clicking through a cloud console to create resources.
B. The practice of defining and managing infrastructure through machine-readable configuration files.
C. A system that only works for on-premises hardware and physical servers.
D. A manual checklist that developers use once a year during audits.

**Correct Answer:** B

**Explanation:** IaC allows developers to describe their entire environment in code, making it versioned, repeatable, and auditable.

---

## Question 2

What is the primary security risk of using automated IaC without guardrails?

A. It makes the infrastructure too slow to deploy.
B. Misconfigurations written once can be deployed everywhere instantly.
C. It prevents developers from using Git for version control.
D. It requires physical hardware security keys for every change.

**Correct Answer:** B

**Explanation:** IaC acts as a multiplier; if a template is insecure, that flaw spreads across the entire environment as fast as the code can be deployed.

---

## Question 3

Why is the **Declarative Model** (e.g., Terraform) considered ideal for security?

A. It requires developers to write step-by-step instructions for every action.
B. It exposes "intent," allowing scanners to judge whether a configuration is safe before it is built.
C. it bypasses the need for Identity and Access Management (IAM).
D. it automatically encrypts all source code files locally.

**Correct Answer:** B

**Explanation:** Declarative code describes the "desired state," making it predictable and easy for policy engines to audit for compliance.

---

## Question 4

What is **Policy as Code (PaC)**?

A. A manual review process where a security officer signs off on every change.
B. Logical rules written in code that automatically evaluate configurations for compliance.
C. A legal document that developers must read before using the cloud.
D. The act of hardcoding passwords into a configuration file.

**Correct Answer:** B

**Explanation:** PaC turns governance into automated logic gates, ensuring that only compliant infrastructure reaches production.

---

## Question 5

Which language is used by the **Open Policy Agent (OPA)** to define compliant configurations?

A. Python
B. Rego
C. JSON
D. YAML

**Correct Answer:** B

**Explanation:** Rego is a declarative logic language used to judge whether a configuration meets security requirements.

---

## Question 6

What is **Configuration Drift**?

A. When the cloud provider updates their hardware automatically.
B. When manual console changes cause the deployed environment to deviate from the defined code.
C. When a developer moves from one cloud provider to another.
D. When the infrastructure code is updated to a newer version of Terraform.

**Correct Answer:** B

**Explanation:** Drift creates blind spots because the "source of truth" in version control no longer matches the reality of what is running in the cloud.

---

## Question 7

What is a primary security benefit of **Immutable Infrastructure**?

A. It allows live servers to be patched without being restarted.
B. It ensures clean, verifiable deployments by replacing resources instead of modifying them.
C. It allows developers to share root passwords across teams.
D. It makes the cloud environment invisible to all users.

**Correct Answer:** B

**Explanation:** Immutability eliminates "snowflake" servers and legacy misconfigurations by recreating the environment from a versioned baseline every time.

---

## Question 8

Which tool can be used to scan IaC templates for misconfigurations **before** deployment?

A. AWS Secrets Manager
B. Checkov
C. Postman
D. CloudTrail

**Correct Answer:** B

**Explanation:** Scanners like Checkov, Trivy, and Trivy analyze IaC files to detect security flaws like public buckets or unencrypted disks.

---

## Question 9

In the **Capstone Task**, what is the purpose of the "Enforcement Layer"?

A. To automatically delete any resource that is older than 30 days.
B. To block or flag noncompliant changes within the CI/CD pipeline.
C. To encrypt the hard drives of developers' laptops.
D. To provide the marketing team with a report of all active servers.

**Correct Answer:** B

**Explanation:** The enforcement layer acts as a gatekeeper, ensuring that insecure code never makes it onto the "highway" to production.

---

## Question 10

According to the module, what should you **never** do with credentials in IaC?

A. Retrieve them dynamically from a secrets manager.
B. Hardcode them into IaC files or variables.
C. Use them in a development environment.
D. Rotate them using an automated script.

**Correct Answer:** B

**Explanation:** Hardcoding secrets is a major risk that can lead to credential theft if the IaC files are stored in version control.

---
