---
id: threat-modeling-fundamentals
title: Threat Modeling Fundamentals
description: Understanding and Applying Threat Modeling in DevSecOps
sidebar_position: 4
---

Author: [Damien Burks]

Welcome to one of the most important sections in this entire guide — **Threat Modeling Fundamentals**.

If you’ve been following along, you now understand how security fits into the **Secure Software Development Life Cycle (SSDLC)**. Threat modeling is the natural next step — it helps us think like attackers _before_ attackers even show up. The goal isn’t just to list risks; it’s to understand _how_ a system can fail and _what we can do_ to prevent that from happening.

---

## Overview

**Threat modeling** is the process of identifying potential security risks within a system, understanding how those threats might be realized, and defining controls to mitigate them.  
It’s about **anticipation** rather than reaction — designing software with security built-in, not bolted on.

> [!IMPORTANT]
> Threat modeling isn’t a one-time activity. It’s a **living process** that evolves with your architecture, your codebase, and your threat landscape.

## The Purpose of Threat Modeling

Threat modeling allows teams to:

- **Identify what to protect** — the assets, data, and functionality that matter most.
- **Anticipate what could go wrong** — both intentional (attacks) and accidental (misconfigurations).
- **Prioritize mitigations** — so security effort is focused where it counts.
- **Build shared understanding** — aligning developers, architects, and security engineers around real-world risks.

Ultimately, threat modeling helps you **design with intent** — not just “make it work,” but “make it secure by design.”

## Where It Fits in the Secure SDLC

Threat modeling primarily happens during the **Design Phase** of the Secure SDLC, right after you’ve gathered requirements and before writing a single line of code.

However, in modern DevSecOps environments, it’s also:

- Revisited during **development** (when new features are added)
- Reassessed during **testing** (when vulnerabilities are found)
- Updated during **maintenance** (when new threats emerge)

> [!NOTE]
> Treat threat modeling like code. Store your diagrams and notes in version control and update them when your architecture changes.

## The Four Core Questions

Microsoft’s foundational approach to threat modeling revolves around four key questions:

1. **What are we building?**  
   Define the system’s purpose, architecture, data flows, and dependencies.
2. **What can go wrong?**  
   Identify how attackers could exploit weaknesses.
3. **What are we going to do about it?**  
   Define mitigations, compensating controls, or design changes.
4. **Did we do a good job?**  
   Review and iterate — threat modeling is never “done.”

These questions form the **heartbeat** of any effective threat modeling session.

## Common Methodologies

Different frameworks exist to structure your thinking. The three most common are:

| **Methodology**                                                                                                  | **Focus Area**                                                                                                                  | **When to Use It**                                     |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **STRIDE** (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) | Identifying threats in system design and data flows                                                                             | When designing applications or APIs                    |
| **PASTA** (Process for Attack Simulation and Threat Analysis)                                                    | End-to-end risk-driven approach combining business impact and attack simulation                                                 | When modeling complex enterprise systems               |
| **LINDDUN**                                                                                                      | Privacy threat modeling (Linkability, Identifiability, Non-repudiation, Detectability, Disclosure, Unawareness, Non-compliance) | When focusing on user data protection and privacy laws |

> 💡 **Tip:** Most developers start with **STRIDE** because it’s simple, structured, and fits perfectly into early design reviews.

## Elements of a Threat Model

Every good threat model includes:

1. **Assets** – What are we protecting? (e.g., credentials, customer data, tokens)
2. **Data Flows** – How does data move between components?
3. **Trust Boundaries** – Where does data change hands or cross security zones?
4. **Threats** – What can go wrong at each step?
5. **Mitigations** – What can we do about it? (e.g., encryption, authentication, validation)

You can visualize this with a **Data Flow Diagram (DFD)**.  
Each trust boundary — such as between a web server and database — is where threats tend to emerge.

![Threat Model Diagram Reference](/img/blueprint/threat_model_example.webp)

> Image Source: [Microsoft Threat Modeling Tool Documentation](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool)

## ⚙️ Example Threat: A Web App Login

Let’s model a simple **login page** that sends credentials to a backend API connected to a database.

| **STRIDE Category**        | **Threat Example**                                              | **Mitigation**                                            |
| -------------------------- | --------------------------------------------------------------- | --------------------------------------------------------- |
| **Spoofing**               | Attacker impersonates a legitimate user via stolen credentials. | Implement MFA and strong authentication.                  |
| **Tampering**              | Login request modified in transit.                              | Use HTTPS/TLS; validate request integrity.                |
| **Repudiation**            | User denies having performed a login.                           | Enable detailed audit logging.                            |
| **Information Disclosure** | Sensitive data exposed through verbose error messages.          | Mask errors; avoid returning stack traces.                |
| **Denial of Service**      | Multiple failed logins overload the backend.                    | Implement rate limiting or CAPTCHA.                       |
| **Elevation of Privilege** | Regular user gains admin rights.                                | Use role-based access control (RBAC) and least privilege. |

> 💡 **Tip:** You can perform this same analysis for _any_ data flow — API requests, CI/CD pipelines, or cloud resources.

## Threat Modeling in DevSecOps

In modern DevSecOps environments, threat modeling shouldn’t be a big-bang meeting that happens once.  
It should be lightweight, continuous, and collaborative.

### Practical Integration Ideas

- Add a **threat modeling checklist** to your pull requests.
- Conduct short “threat-storming” sessions in sprint planning.
- Automate simple model generation using tools like **Threat Dragon**, **IriusRisk**, or **Threagile**.
- Store your models in GitHub — versioned like code.

> 💡 **Tip:** Threat modeling is not just for architects.  
> Developers, testers, and ops engineers should all contribute — because threats evolve with how systems are _actually used_.

## 🔍 Applied Reflection (Capstone Prompt)

Now that you understand the fundamentals, it’s time to apply what you’ve learned.

Imagine you’re designing a small **microservice-based application** or a **CI/CD pipeline** for one of your own projects.

1. List the main **components** and **data flows**.
2. Identify **at least three threats** using STRIDE categories.
3. Define **mitigations** you would implement to reduce risk.
4. (Optional) Draw a simple diagram showing your data flow and trust boundaries.

✅ **Capstone Goal:**  
Demonstrate that you can think critically about _how your system could fail_ and _how to build resilience in by design._

> 💡 **Pro Tip:** The more you practice this, the faster you’ll be able to identify weak points during architecture or code reviews.

## Recommended Resources

### 📚 Books

| **Title**                                          | **Author**                     | **Why It’s Useful**                                     |
| -------------------------------------------------- | ------------------------------ | ------------------------------------------------------- |
| _Threat Modeling: Designing for Security_          | Adam Shostack                  | The definitive guide to modern threat modeling.         |
| _Designing Secure Software_                        | Loren Kohnfelder               | Focuses on security architecture and design principles. |
| _The Security Engineer’s Guide to Threat Modeling_ | Izar Tarandach & Matthew Coles | Practical advice for applying threat modeling at scale. |

### 🎥 Videos

- [Microsoft Threat Modeling Explained](https://www.youtube.com/watch?v=GGMnE0P7nTI)
- [Threat Modeling for Developers (OWASP Global AppSec)](https://www.youtube.com/watch?v=O9G8Y7Ck6_0)
- [How to Integrate Threat Modeling into Agile](https://www.youtube.com/watch?v=H8F2-H2x8mM)

### Recommended Certifications

| **Certification**                             | **Provider**        | **Relevance**                                       |
| --------------------------------------------- | ------------------- | --------------------------------------------------- |
| Certified Threat Modeling Professional (CTMP) | ThreatModeler       | Focused on enterprise-scale modeling.               |
| CSSLP                                         | ISC²                | Emphasizes secure design and lifecycle integration. |
| CDP (Certified DevSecOps Professional)        | Practical DevSecOps | Ties threat modeling into CI/CD and automation.     |

By mastering threat modeling, you’re not just securing systems. You’re **engineering with foresight** and building software that anticipates risk rather than reacts to it.

<!-- Links -->

[Damien Burks]: https://damienjburks.com
