---
id: threat-modeling-fundamentals
title: Threat Modeling Fundamentals
description: Understanding and Applying Threat Modeling in DevSecOps
sidebar_position: 3
---

Author: [Damien Burks]

Welcome to one of the most important sections in this entire guide: **Threat Modeling Fundamentals**.

If you’ve been following along, you now understand how security fits into the **Secure Software Development Life Cycle (SSDLC)**. Threat modeling is the natural next step :it helps us think like attackers _before_ attackers even show up. The goal isn’t just to list risks; it’s to understand _how_ a system can fail and _what we can do_ to prevent that from happening.

## Overview

**Threat modeling** is the process of identifying potential security risks within a system, understanding how those threats might be realized, and defining controls to mitigate them.  
It’s about **anticipation** rather than reaction :designing software with security built-in, not bolted on.

:::important
Threat modeling isn’t a one-time activity. It’s a **living process** that evolves with your architecture, your codebase, and your threat landscape.
:::

## The Purpose of Threat Modeling

Threat modeling allows teams to:

- **Identify what to protect** :the assets, data, and functionality that matter most.
- **Anticipate what could go wrong** :both intentional (attacks) and accidental (misconfigurations).
- **Prioritize mitigations** :so security effort is focused where it counts.
- **Build shared understanding** :aligning developers, architects, and security engineers around real-world risks.

Ultimately, threat modeling helps you **design with intent** (not just "make it work”) but "make it secure by design.”

## Where It Fits in the Secure SDLC

Threat modeling primarily happens during the **Design Phase** of the Secure SDLC, right after you’ve gathered requirements and before writing a single line of code.

However, in modern DevSecOps environments, it’s also:

- Revisited during **development** (when new features are added)
- Reassessed during **testing** (when vulnerabilities are found)
- Updated during **maintenance** (when new threats emerge)

:::important
Treat threat modeling like code. Store your diagrams and notes in version control and update them when your architecture changes. You'll save yourself a LOT of time, I promise :smile:
:::

## The Four Core Questions

Microsoft’s foundational approach to threat modeling revolves around four key questions:

1. **What are we building?**  
   Define the system’s purpose, architecture, data flows, and dependencies.
2. **What can go wrong?**  
   Identify how attackers could exploit weaknesses.
3. **What are we going to do about it?**  
   Define mitigations, compensating controls, or design changes.
4. **Did we do a good job?**  
   Review and iterate :threat modeling is never "done.”

These questions form the **heartbeat** of any effective threat modeling session.

## Common Methodologies

Different frameworks exist to structure your thinking. The three most common are:

| **Methodology**                                                                                                  | **Focus Area**                                                                                                                  | **When to Use It**                                     |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **STRIDE** (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) | Identifying threats in system design and data flows                                                                             | When designing applications or APIs                    |
| **PASTA** (Process for Attack Simulation and Threat Analysis)                                                    | End-to-end risk-driven approach combining business impact and attack simulation                                                 | When modeling complex enterprise systems               |
| **LINDDUN**                                                                                                      | Privacy threat modeling (Linkability, Identifiability, Non-repudiation, Detectability, Disclosure, Unawareness, Non-compliance) | When focusing on user data protection and privacy laws |

:::tip
Most developers start with **STRIDE**, because it’s simple, structured, and fits perfectly into early design reviews.
:::

## Elements of a Threat Model

Every good threat model includes the following building blocks. Think of these as the "what,” "how,” and "where” of your system’s security story.

### 1. **Assets — What are we protecting?**

These are the things that matter most. Examples include credentials, customer data, API keys, and source code. Ask yourself:

> "If this was stolen or changed, would it impact my users or business?”

### 2. **Data Flows — How does data move?**

Data flows describe how information travels through your system, such as who sends it, who receives it, and how. By mapping these flows, you can see where sensitive data is created, stored, or transmitted.

:::tip
Use arrows to show direction and label where encryption or access controls apply.
:::

### 3. **Trust Boundaries — Where does trust change?**

A trust boundary marks a shift from one security zone to another. For example, when data leaves a user’s browser and enters your backend API. These are the areas where you should apply the strongest checks, like authentication, validation, and input filtering.

### 4. **Threats — What can go wrong?**

Once you understand your system, think like an attacker.  
Ask questions such as:

- Could someone steal or guess credentials?
- Could a request be tampered with?
- Could data leak from logs or error messages?

Frameworks like **STRIDE** help you stay organized when identifying risks.

### 5. **Mitigations — What can we do about it?**

For every threat you find, define what protects against it. Examples include:

- Using encryption for data at rest and in transit
- Validating input and sanitizing output
- Enforcing least privilege access
- Adding rate limits and monitoring for anomalies

### 6. **Attack Vectors — How could someone get in?**

Attack vectors are the ways an attacker might reach your system. Understanding them helps you decide what controls to add.

| **Category**    | **Example**                  | **Mitigation**                            |
| --------------- | ---------------------------- | ----------------------------------------- |
| **Web/API**     | SQL injection or weak tokens | Input validation, WAF, short-lived tokens |
| **Network**     | No TLS, exposed ports        | Enforce HTTPS, firewall rules             |
| **Secrets**     | Keys in code or CI logs      | Store in Vault or Secrets Manager         |
| **Third-Party** | Unverified webhooks          | Use signature validation                  |
| **DoS**         | Resource exhaustion          | Rate limiting, autoscaling                |

### Example Data Flow Diagram (DFD)

Below is a simple example of what a DFD might look like. It shows how users, apps, and services interact, and where trust boundaries live.

![DFD Example](https://www.practical-devsecops.com/wp-content/uploads/2024/01/threat-modeling-data-flow-diagram-.png)

:::note
You can find the original source for this image [here](https://www.practical-devsecops.com/threat-modeling-data-flow-diagrams/). Also, Start simple. Even a hand-drawn diagram on a whiteboard can help your team understand where to focus defenses.
:::

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

:::note
You can perform this same analysis for _any_ data flow :API requests, CI/CD pipelines, or cloud resources.
:::

## Threat Modeling in DevSecOps

In modern DevSecOps environments, threat modeling shouldn’t be a big-bang meeting that happens once. It should be lightweight, continuous, and collaborative.

### Practical Integration Ideas

- Add a **threat modeling checklist** to your pull requests.
- Conduct short "threat-storming” sessions in sprint planning.
- Automate simple model generation using tools like **Threat Dragon**, **IriusRisk**, or **Threagile**.
- Store your models in GitHub :versioned like code.

:::tip
Threat modeling is not just for architects. Developers, testers, and ops engineers should all contribute, because threats evolve with how systems are _actually used_.
:::

## 🔍 Applied Reflection (Capstone Prompt)

Now that you understand the fundamentals, it’s time to apply what you’ve learned.

Imagine you’re designing a small **microservice-based application** or a **CI/CD pipeline** for one of your own projects.

1. List the main **components** and **data flows**.
2. Identify **at least three threats** using STRIDE categories.
3. Define **mitigations** you would implement to reduce risk.
4. (Optional) Draw a simple diagram showing your data flow and trust boundaries.

✅ **Capstone Goal:** Demonstrate that you can think critically about _how your system could fail_ and _how to build resilience in by design._

:::note
The more you practice this, the faster you’ll be able to identify weak points during architecture or code reviews.
:::

## Recommended Resources

### Books

| **Book Title**                                           | **Author**                       | **Link**                          | **Why It’s Useful**                                                                                             |
| -------------------------------------------------------- | -------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Threat Modeling: Designing for Security                  | Adam Shostack                    | [Amazon](https://amzn.to/47jcEDc) | The definitive guide to modern threat modeling and understanding attacker thinking during design.               |
| Securing Systems                                         | Brook S. E. Schoenfield          | [Amazon](https://amzn.to/3X6JS2F) | Provides a structured approach to building secure architectures and embedding security into system design.      |
| Threat Modeling: A Practical Guide for Development Teams | Izar Tarandach and Matthew Coles | [Amazon](https://amzn.to/3WTQi5n) | Offers practical, team-focused strategies for applying threat modeling consistently across real-world projects. |

### YouTube Videos

#### What is Threat Modeling and Why Is It Important?

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/h_BC6QMWDbA?si=nRbBZzvWLOP70Dbc"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### STRIDE Threat Modeling for Beginners

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/rEnJYNkUde0?si=-7LO8REer5zLSmZx"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

### Recommended Certifications

| **Certification**                             | **Provider**        | **Relevance**                                       |
| --------------------------------------------- | ------------------- | --------------------------------------------------- |
| Certified Threat Modeling Professional (CTMP) | ThreatModeler       | Focused on enterprise-scale modeling.               |
| CSSLP                                         | ISC²                | Emphasizes secure design and lifecycle integration. |
| CDP (Certified DevSecOps Professional)        | Practical DevSecOps | Ties threat modeling into CI/CD and automation.     |

<!-- Links -->

[Damien Burks]: https://damienjburks.com
