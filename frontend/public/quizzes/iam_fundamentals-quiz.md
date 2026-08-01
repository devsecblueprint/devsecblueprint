---
module_id: iam-fundamentals
passing_score: 80
---

## Question 1

How does the module define Identity and Access Management (IAM) in the cloud?

A. A manual process for creating physical security badges for data centers
B. The framework that enables the right individuals or services to access the right resources for the right reasons
C. A system used exclusively for managing marketing email lists
D. The tool used to increase the storage capacity of cloud databases

**Correct Answer:** B

**Explanation:** IAM is the backbone of cloud security, ensuring that both human and machine identities have appropriate access under the right conditions.

---

## Question 2

What is the difference between **Authentication** and **Authorization** in IAM?

A. Authentication is about what you can do; Authorization is about who you are.
B. Authentication is about who you are; Authorization is about what you are allowed to do.
C. Both terms refer to the process of rotating long-lived credentials.
D. Authentication is for human users, while Authorization is only for machine workloads.

**Correct Answer:** B

**Explanation:** Authentication verifies identity (e.g., via password or MFA), while authorization determines the permissions granted to that identity.

---

## Question 3

Which of the following is identified as one of the **most common causes** of security incidents in the cloud?

A. Using the wrong cloud provider region
B. IAM misconfigurations
C. High network latency
D. Using open-source software libraries

**Correct Answer:** B

**Explanation:** Misconfigurations, such as overly broad permissions, are a leading cause of cloud breaches, making IAM hygiene a top priority.

---

## Question 4

What does the **Principle of Least Privilege** imply?

A. Granting "Owner" level access to all developers to speed up production.
B. Starting with no permissions and granting only what is truly necessary for a task.
C. Giving every user the same set of permissions for consistency.
D. Allowing users to share their credentials with one other team member.

**Correct Answer:** B

**Explanation:** Least privilege minimizes the attack surface by ensuring identities only have the specific access required to perform their function.

---

## Question 5

Which IAM attack surface involves static access keys stored in code or scripts without rotation?

A. Shared Roles
B. Overly Broad Permissions
C. Long-Lived Credentials
D. Weak Authentication

**Correct Answer:** C

**Explanation:** Long-lived credentials are risky because they are often hardcoded and rarely changed, making them an easy target for attackers.

---

## Question 6

In the **IAM Lifecycle**, which phase focuses on enabling access logging and detecting unused permissions?

A. Define Phase
B. Enforce Phase
C. Monitor Phase
D. Improve Phase

**Correct Answer:** C

**Explanation:** Monitoring involves using logs (like CloudTrail or Activity Logs) and analyzers to track activity and identify security gaps.

---

## Question 7

Why is it a best practice to **Use Roles, Not Users** for cloud workloads?

A. Roles allow for permanent, static credentials that never expire.
B. Roles provide temporary credentials, reducing the risk of credential theft.
C. Users are more difficult to create in a cloud console than roles.
D. Only roles can be used to access storage buckets.

**Correct Answer:** B

**Explanation:** Temporary credentials (like those provided via AWS STS) are significantly more secure than long-lived user access keys.

---

## Question 8

Which cloud provider uses a **Policy Binding System** where roles are inherited through resource levels?

A. AWS
B. Azure
C. GCP
D. IBM Cloud

**Correct Answer:** C

**Explanation:** GCP's IAM model relies on binding policies to resources, with permissions often inherited from higher levels in the organization.

---

## Question 9

What is the primary purpose of **Multi-Factor Authentication (MFA)** in an IAM strategy?

A. To make the login process faster for developers
B. To provide an additional layer of security beyond just a password
C. To automate the rotation of access keys
D. To encrypt data while it is in transit

**Correct Answer:** B

**Explanation:** MFA is a critical defense that prevents account takeover even if a user's password is compromised.

---

## Question 10

According to the "Practice What You've Learned" section, what is the goal of the **IAM Hardening Report**?

A. To document a plan for migrating all data to a different cloud provider
B. To show how privilege risks were identified and mitigated through automation
C. To list every single user in the organization for the marketing team
D. To record the hardware specifications of all virtual machines

**Correct Answer:** B

**Explanation:** The capstone goal is to demonstrate practical ability in identifying and fixing IAM security flaws using automated tools.
