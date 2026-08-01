---
module_id: api-patterns-and-sdks
passing_score: 80
---

## Question 1

How are APIs and SDKs related in the context of cloud development?

A. APIs are used for manual configuration, while SDKs are only for automated testing.
B. SDKs act as language-specific wrappers around APIs to make automation easier.
C. APIs replace the need for an SDK entirely.
D. SDKs are only used to manage physical hardware in a data center.

**Correct Answer:** B

**Explanation:** APIs provide the communication interface, and SDKs provide the tools and libraries for specific programming languages to interact with those APIs.

---

## Question 2

Which of the following is a primary risk of using **Over-Privileged Tokens**?

A. It increases the time it takes to deploy a new server.
B. It increases the blast radius if the token is compromised.
C. It prevents the application from using encryption.
D. It forces the developer to use a different cloud provider.

**Correct Answer:** B

**Explanation:** Tokens with excessive permissions (like "Owner") give an attacker total control if they are stolen.

---

## Question 3

During the **Design Phase** of the API lifecycle, what is a best practice for standardizing behavior?

A. Using OpenAPI/Swagger specifications
B. Hardcoding the IP addresses of the servers
C. Allowing plain HTTP calls for faster development
D. Using long-lived API keys for all integrations

**Correct Answer:** A

**Explanation:** OpenAPI and Swagger help define a clear contract for the API, ensuring consistency and enabling automated validation.

---

## Question 4

Why is it recommended to use **Official SDKs** from cloud providers?

A. They are free of all security vulnerabilities.
B. they ensure consistent authentication, version control, and reliability.
C. They allow you to bypass all IAM permissions.
D. They are the only way to access the cloud console.

**Correct Answer:** B

**Explanation:** Official SDKs are maintained by providers to handle complex tasks like authentication and retry logic securely and consistently.

---

## Question 5

What is the purpose of implementing **Exponential Backoff** in an automation script?

A. To encrypt data before it is sent to the API
B. To handle API throttling gracefully by gradually increasing the wait time between retries
C. To delete unused resources automatically
D. To prevent the script from running on the weekends

**Correct Answer:** B

**Explanation:** Exponential backoff prevents overwhelming the API when it is throttled, improving the reliability of the automation.

---

## Question 6

Which tool is specifically designed to manage and rotate cloud credentials securely?

A. Postman
B. AWS Secrets Manager
C. Swagger
D. CloudTrail

**Correct Answer:** B

**Explanation:** Secrets managers allow you to store and rotate credentials automatically, so they are never hardcoded in your scripts.

---

## Question 7

What is a risk of **Poor Input Validation** in an API?

A. It can lead to injection attacks or privilege escalation.
B. It makes the API too slow for the marketing team to use.
C. It requires the developer to use a physical hardware key.
D. It automatically encrypts all incoming data.

**Correct Answer:** A

**Explanation:** Without validation, attackers can send malicious parameters that can manipulate the backend system.

---

## Question 8

Which service would you use to **log every interaction** with a cloud API for audit purposes?

A. AWS CloudWatch
B. AWS CloudTrail
C. Postman
D. OpenAPI

**Correct Answer:** B

**Explanation:** CloudTrail (and similar logs in other clouds) provides the historical record of every API call made in the account.

---

## Question 9

What is the **Principle of Least Privilege** in the context of API security?

A. Granting only the minimal permissions required for a service integration
B. Granting the same permissions to every API endpoint
C. Using the most expensive cloud resources possible
D. Requiring users to change their password every hour

**Correct Answer:** A

**Explanation:** Least privilege ensures that if an API or token is compromised, the damage is restricted to only what that specific token was authorized to do.

---

## Question 10

According to the **Capstone Mission**, what should you _never_ do with credentials?

A. Store them in an environment variable
B. Hardcode them in your code or configuration
C. Use them with an official SDK
D. Rotate them automatically

**Correct Answer:** B

**Explanation:** Hardcoded credentials are a massive security risk and can easily be leaked through version control systems.
