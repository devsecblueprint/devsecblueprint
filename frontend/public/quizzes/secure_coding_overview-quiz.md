---
module_id: secure-coding-overview
passing_score: 80
---

## Question 1

Which of the following best defines "Secure Coding" as discussed in the modules?

A. The process of manually fixing bugs after a production breach has occurred
B. The practice of writing software that anticipates misuse and fails safely
C. The act of using complex encryption for every single line of source code
D. A method of coding that prioritizes performance and speed over user experience

**Correct Answer:** B

**Explanation:** Secure coding is a proactive discipline where software is written to account for untrusted inputs and potential errors from the very start.

---

## Question 2

Why is secure coding considered a core "Shift-Left" practice in DevSecOps?

A. It moves security testing to the very end of the deployment pipeline
B. It involves developers fixing insecure patterns before they reach downstream phases
C. It ensures that only the security team is responsible for the code quality
D. It requires moving the entire server infrastructure to a decentralized cloud

**Correct Answer:** B

**Explanation:** Catching and avoiding insecure patterns while the code is still in development is significantly less costly and disruptive than fixing them later.

---

## Question 3

During the **Design Phase**, what is a primary goal when setting the "Rules of the House"?

A. To allow all users to access any resource by default for better usability
B. To determine where internal data meets untrusted external inputs (Trust Boundaries)
C. To encrypt every database table regardless of its sensitivity level
D. To remove the need for any firewalls or external networking hardware

**Correct Answer:** B

**Explanation:** Identifying trust boundaries helps developers know exactly where rigorous validation and authorization are required before any code is written.

---

## Question 4

Which failure pattern occurs when an application assumes that all external inputs are safe, leading to vulnerabilities like SQL Injection?

A. Secrets in Code
B. Insecure Serialization
C. Untrusted Input Handling
D. Poor Error Handling

**Correct Answer:** C

**Explanation:** Untrusted Input Handling happens when inputs are assumed to be safe, allowing malicious data to manipulate the application.

---

## Question 5

What is the primary risk associated with the "Secrets in Code" failure pattern?

A. Slow application performance during peak traffic hours
B. Credential leaks and unauthorized exposure of sensitive tokens
C. The application crashing due to an invalid memory address
D. A user being able to bypass the front-end styling of the website

**Correct Answer:** B

**Explanation:** Hardcoding secrets is often done for convenience but leads to credential leaks and token exposure in the source code.

---

## Question 6

In the **Implementation Phase**, why is "Failing Securely" considered a best practice?

A. It ensures the system stays online no matter how much data is lost
B. It prevents error messages from revealing internal system details to attackers
C. It allows developers to skip testing for edge cases during development
D. It automatically fixes the bug so the application never stops running

**Correct Answer:** B

**Explanation:** Secure error handling ensures that when things go wrong, the resulting error messages protect the system rather than revealing internal details.

---

## Question 7

Which tool in "The Arsenal" is specifically noted for pattern-based static analysis to detect insecure coding patterns?

A. SonarQube
B. Semgrep
C. Trivy
D. Snyk

**Correct Answer:** B

**Explanation:** Semgrep is designed for pattern-based static analysis to hunt for specific insecure coding patterns in the source.

---

## Question 8

What does the principle of "Prefer Secure Defaults" imply for application design?

A. Users should have to manually enable every security feature themselves
B. The most secure path should be the easiest and default path for users
C. Security should only be applied to administrative accounts
D. The application should run without any permissions until a user logs in

**Correct Answer:** B

**Explanation:** Favoring secure defaults ensures the system is protected "out of the box," making the secure path the easiest path for the user.

---

## Question 9

What is a primary goal of the **Review & Enforcement** phase of secure coding?

A. To replace all automated tools with human manual testing
B. To ensure that insecure patterns do not re-enter the codebase through peer feedback
C. To find a developer to blame for any security issues found in the pipeline
D. To increase the length of the development cycle as much as possible

**Correct Answer:** B

**Explanation:** This phase uses peer reviews and automated checks as feedback to prevent insecure patterns from re-entering the codebase.

---

## Question 10

According to the "Arsenal" module, what is a key rule for integrating security tools into CI pipelines?

A. Only run tools after the application has been deployed to production
B. Never show remediation guidance to developers to keep them on their toes
C. Avoid blocking pipelines without providing clear remediation guidance
D. Ensure that security tools are only used by the dedicated security team

**Correct Answer:** C

**Explanation:** Automation should support developers; blocking a pipeline without explaining how to fix the issue causes friction and slows down delivery.

**Would you like me to start drafting Phase 2 of the blueprint (Secure SDLC), or is there another section you'd like to tackle first?**