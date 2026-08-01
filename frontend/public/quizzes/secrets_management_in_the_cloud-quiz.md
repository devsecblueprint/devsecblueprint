---
module_id: secrets-management-in-the-cloud 
passing_score: 80
---

## Question 1

How does the module define "Secrets Management"?

A. The process of making all company data public for transparency.
B. The practice of securely storing, accessing, and distributing sensitive credentials like API keys and passwords.
C. A method for increasing the speed of a database by removing encryption.
D. The act of manually writing down passwords in a notebook.

**Correct Answer:** B

**Explanation:** Secrets management ensures sensitive information doesn't end up in insecure places like code, logs, or config files.

---

## Question 2

Which of the following is a common risk when managing secrets poorly?

A. Encrypting data at rest
B. Hardcoding secrets in source code or `.env` files
C. Using short-lived tokens
D. Enabling multi-factor authentication

**Correct Answer:** B

**Explanation:** Leaving credentials in code is a major pitfall that leads to accidental exposure in repositories.

---

## Question 3

What is the primary benefit of **Centralization** in a secrets management strategy?

A. It allows every user to have the same password for simplicity.
B. It provides visibility, control, and consistency by storing secrets in a dedicated vault.
C. It ensures secrets are stored in plaintext for faster access.
D. It removes the need for any IAM roles.

**Correct Answer:** B

**Explanation:** Storing secrets in one governed location (like AWS Secrets Manager or Vault) makes them easier to manage and audit.

---

## Question 4

Under the **Lifecycle Management** pillar, what should happen to secrets regularly?

A. They should be shared with as many people as possible.
B. They should be rotated and expired automatically.
C. They should be kept the same for the entire life of the project.
D. They should be printed in the application logs for troubleshooting.

**Correct Answer:** B

**Explanation:** Rotating secrets reduces the window of time an attacker can use a stolen credential.

---

## Question 5

Which cloud service is noted for its ability to generate **Dynamic Secrets** on-demand?

A. AWS SSM Parameter Store
B. Azure Key Vault
C. HashiCorp Vault
D. GCP Secret Manager

**Correct Answer:** C

**Explanation:** HashiCorp Vault is well-known for dynamic secrets that are created when requested and automatically expire after a set time.

---

## Question 6

Why is **Auditing and Traceability** essential for a secrets management system?

A. To identify which secrets are taking up the most storage space
B. To track every access request and know who accessed what, when, and from where
C. To allow users to retrieve secrets without authentication
D. To provide the marketing team with user login patterns

**Correct Answer:** B

**Explanation:** If access to a secret can't be audited, it cannot be trusted as part of a secure system.

---

## Question 7

What is a "Dynamic Secret"?

A. A secret that is hardcoded in the application's DNA
B. A credential that is generated on-demand and expires automatically
C. An API key that is shared by all developers on a team
D. A password that never changes

**Correct Answer:** B

**Explanation:** Dynamic secrets are highly secure because they only exist for the duration they are needed.

---

## Question 8

Which of the following is a best practice for isolating environments?

A. Using the same API keys for Dev, Test, and Production
B. Never reusing secrets across different development stages
C. Storing all secrets in a single public S3 bucket
D. Hardcoding production database passwords in the README file

**Correct Answer:** B

**Explanation:** Isolating environments prevents a compromise in a lower-security "Dev" environment from affecting "Production".

---

## Question 9

According to the module, what is the "Invisible Shield" role of secrets management?

A. It makes secrets work silently in the background to protect the environment when managed properly.
B. It makes the cloud console disappear for security.
C. It hides the application from the public internet entirely.
D. It removes the need for any developers to have passwords.

**Correct Answer:** A

**Explanation:** When secrets are handled automatically and traceably, they protect the system without creating friction for developers.

---

## Question 10

According to the **Capstone Goal**, what is the final step in proving you can manage a secret's lifecycle?

A. Sharing the secret on social media
B. Rotating the secret automatically or manually
C. Deleting the secrets manager service entirely
D. Moving the secret into a plaintext `.env` file

**Correct Answer:** B

**Explanation:** Proving you can rotate a secret demonstrates full control over its lifecycle from creation to renewal.

---
