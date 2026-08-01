---
module_id: what-is-application-security
passing_score: 80
---

## Question 1

According to the overview, what is the primary aim of Application Security?

A. To replace the need for cloud infrastructure security
B. To protect software application code and data against cybersecurity threats and vulnerabilities
C. To increase the speed of the internet connection for users
D. To manually manage hardware servers in a data center

**Correct Answer:** B

**Explanation:** Application Security focuses on protecting the "soul" of the system—the code and data—by using tools, fixing issues, and threat modeling during the design phase.

---

## Question 2

If an application is poorly secured and a data breach occurs, which of the following is a potential impact?

A. Increased customer trust
B. Improved SEO rankings
C. Reputational damage and loss of market position
D. Faster deployment of new features

**Correct Answer:** C

**Explanation:** Beyond data loss, a breach often leads to compliance violations (like GDPR or HIPAA) and a permanent loss of customer trust.

---

## Question 3

Which OWASP Top 10 vulnerability (A01:2025) is compared to a hotel guest being able to open every door in the building with their single room key?

A. Injection
B. Security Misconfiguration
C. Broken Access Control
D. Cryptographic Failures

**Correct Answer:** C

**Explanation:** Broken Access Control occurs when users can act outside of their intended permissions, such as accessing data or features belonging to other users.

---

## Question 4

What is a defining characteristic of **Static Application Security Testing (SAST)**?

A. It requires the application to be running in a test environment
B. It is a "white-box" technique that analyzes source code without executing the program
C. It simulates a real-world attacker with no knowledge of the system
D. It only checks for hardware failures

**Correct Answer:** B

**Explanation:** SAST is the "X-Ray" of AppSec; it scans the static DNA of the code early in the development process to find hidden flaws.

---

## Question 5

Why is SAST considered beneficial for the "Shift Left" philosophy?

A. It is only performed after the application is in production
B. It can detect security issues during development, before the code is compiled or deployed
C. It bypasses the need for a CI/CD pipeline
D. It fixes the code automatically without developer intervention

**Correct Answer:** B

**Explanation:** Because SAST runs on the source code, it provides early detection, making bugs much cheaper and easier to fix than if they were found later.

---

## Question 6

**Dynamic Application Security Testing (DAST)** is described as what type of testing technique?

A. White-box testing
B. Logic-gate testing
C. Black-box testing
D. Blueprint testing

**Correct Answer:** C

**Explanation:** DAST is a "black-box" technique because the tester mimics a real-world attacker who has no prior knowledge of the application's inner workings.

---

## Question 7

What is a major benefit of using DAST in your security workflow?

A. It provides comprehensive coverage of all code paths
B. It can catch runtime-specific issues like misconfigurations and authentication flaws
C. It allows developers to scan code before they hit "save"
D. It eliminates the need for any other security testing

**Correct Answer:** B

**Explanation:** Unlike static scans, DAST tests the "live" machine, finding vulnerabilities that only become apparent when the application is operational.

---

## Question 8

Which intentionally vulnerable application is specifically designed for practicing JavaScript and Node.js security testing?

A. OWASP Juice Shop
B. VulnNode
C. Mutillidae II
D. DVWA

**Correct Answer:** B

**Explanation:** VulnNode is a target specifically designed for those looking to master security flaws unique to the Node.js ecosystem.

---

## Question 9

In the "The Credentials" module, which book is recommended for understanding AppSec through the stories of characters named Alice and Bob?

A. Hacking APIs
B. The Web Application Hacker's Handbook
C. Alice and Bob Learn Application Security
D. The DevSecOps Guide

**Correct Answer:** C

**Explanation:** Written by Tanya Janca, this book is a highly recommended resource for learning application security through relatable narrative scenarios.

---

## Question 10

Why does a comprehensive AppSec strategy incorporate both SAST and DAST?

A. Because using only one method leaves gaps at either the code level or the operational level
B. Because it is a legal requirement for all cloud providers
C. Because it allows you to skip the DevOps phase
D. Because one method is for developers and the other is only for marketing

**Correct Answer:** A

**Explanation:** Combining SAST and DAST ensures that security testing occurs during both the creation of the code and the operation of the application, minimizing overall risk.
