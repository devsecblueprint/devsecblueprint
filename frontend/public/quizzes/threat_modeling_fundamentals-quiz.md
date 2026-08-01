---
module_id: threat-modeling
passing_score: 80
---

## Question 1

How does the module define "Threat Modeling" in the context of system security?

A. A one-time meeting held after a breach to identify what went wrong
B. The process of identifying potential security risks and defining controls to mitigate them
C. A manual process for updating software patches on production servers
D. The act of writing code as quickly as possible to meet business requirements

**Correct Answer:** B

**Explanation:** Threat modeling is a proactive process of identifying security risks, understanding how they might be realized, and defining controls to prevent them.

---

## Question 2

Why is threat modeling described as a "living process" rather than a one-time activity?

A. Because it must evolve with the architecture, codebase, and the threat landscape
B. Because it is only required for legacy systems that are no longer being updated
C. Because it requires a subscription-based tool to be active at all times
D. Because it is only performed during the maintenance phase of the SSDLC

**Correct Answer:** A

**Explanation:** Threat modeling is continuous; it needs to be revisited whenever new features are added, vulnerabilities are found, or new threats emerge.

---

## Question 3

According to Microsoft’s foundational approach, which of the following is one of the "Four Core Questions"?

A. How much will this security feature cost to implement?
B. Which developer is responsible for the most bugs?
C. What can go wrong?
D. Can we automate the entire design phase?

**Correct Answer:** C

**Explanation:** The four core questions are: 1. What are we building? 2. What can go wrong? 3. What are we going to do about it? 4. Did we do a good job?.

---

## Question 4

Which threat modeling methodology is specifically recommended for beginners because it is structured and fits early design reviews?

A. PASTA
B. LINDDUN
C. STRIDE
D. DREAD

**Correct Answer:** C

**Explanation:** STRIDE is highly recommended for developers starting out because it provides a simple and structured way to identify threats in system design.

---

## Question 5

In a threat model, what is a **Trust Boundary**?

A. A shift from one security zone to another, such as from a browser to a backend API
B. The physical perimeter of the data center where the servers are located
C. A legal agreement between a company and its third-party vendors
D. The point where the software code is translated into machine language

**Correct Answer:** A

**Explanation:** Trust boundaries mark changes in security zones and are the areas where the strongest checks, like authentication and validation, should be applied.

---

## Question 6

Under the **STRIDE** framework, which category refers to an attacker impersonating a legitimate user?

A. Tampering
B. Repudiation
C. Spoofing
D. Denial of Service

**Correct Answer:** C

**Explanation:** Spoofing involves an attacker pretending to be someone else, such as using stolen credentials to access a system.

---

## Question 7

What is the primary purpose of creating a **Data Flow Diagram (DFD)** during threat modeling?

A. To show the marketing team how users interact with the UI
B. To map how information travels through a system to see where it might be intercepted
C. To replace the need for writing technical documentation
D. To list all the hardware components used in the office building

**Correct Answer:** B

**Explanation:** Mapping data flows allows teams to see how data is created, stored, and transmitted, highlighting where security controls are needed.

---

## Question 8

Which category of STRIDE is mitigated by using detailed audit logging to prevent users from denying they performed an action?

A. Information Disclosure
B. Repudiation
C. Elevation of Privilege
D. Tampering

**Correct Answer:** B

**Explanation:** Repudiation threats involve users denying they performed an action; audit logs provide the proof needed to mitigate this.

---

## Question 9

Where does threat modeling primarily happen within the **Secure SDLC**?

A. Maintenance Phase
B. Testing Phase
C. Design Phase
D. Deployment Phase

**Correct Answer:** C

**Explanation:** Threat modeling should happen during the design phase, after gathering requirements but before writing code, to ensure the system is secure by design.

---

## Question 10

Which of the following is a practical way to integrate threat modeling into a modern **DevSecOps** environment?

A. Add a threat modeling checklist to pull requests
B. Only allow the head architect to see the threat models
C. Wait until a penetration test is completed before starting a model
D. Store threat models in a separate physical safe that is disconnected from the network

**Correct Answer:** A

**Explanation:** DevSecOps integration should be lightweight and continuous, such as using checklists in PRs or storing models in version control like code.
