---
id: what-is-the-secure-sdlc-and-sdlc
title: What is the Secure SDLC?
sidebar_position: 2
---

Author: [Damien Burks]

Now that we've covered Application Security, and you're familiar with key concepts of Application Security, let's dive into the Software Development Life Cycle and Secure Software Development Life Cycle.

## Overview

One of the most critical building blocks is the **Secure Software Development Life Cycle (Secure SDLC)**. By establishing a strong understanding of Secure SDLC, you will be better equipped to comprehend how security is integrated throughout the development lifecycle.

## What is the SDLC?

![SDLC](/img/blueprint/sdlc_image.webp)

> Image Source: [Software Development Life Cycle (SDLC) | Snyk](https://snyk.io/learn/secure-sdlc/#history)

The **Software Development Life Cycle (SDLC)** is a **structured** process used for developing software applications. To keep it short, the SDLC consists of six key phases:

1. **Planning and Requirements Gathering**: Understanding what the software needs to do.
2. **Design**: Architecting the solution to meet functional and non-functional requirements.
3. **Development**: Writing the actual code.
4. **Testing**: Ensuring that the software works as intended and is free from bugs.
5. **Deployment**: Releasing the software to production environments.
6. **Maintenance**: Ongoing updates and fixes post-release.

The downside to this process is that there is no security backed into any of phases. Formally known as the traditional SDLC, when developers follow this model, security is often treated as an afterthought and addressed only in the testing or deployment stages. This reactive approach can result in security issues being discovered late, which can be quite costly and disruptive to fix overtime. So, when you're developing applications of any kind, keep this in mind.

## The Secure SDLC

Now that we've covered the SDLC at a high-level, let's talk about the replacement (or the better process to follow).

The **Secure SDLC** is an evolution of the traditional SDLC model, where security is a key consideration at **every stage** of the process. Rather than treating security as a final step, it becomes an integral part of each phase, helping to reduce vulnerabilities and risks earlier in the lifecycle. The key benefit of this process is that you are finding and figuring out any security issues as you iterate through the Secure SDLC, which overtime helps save cost and eliminates the overhead and potential of releasing vulnerabilities into the wild.

![SSDLC](/img/blueprint/ssdlc_image.webp)

> Image Source: [Secure Software Development Life Cycle (SSDLC) | Snyk](https://snyk.io/learn/secure-sdlc/#phases)

### Key Phases of the Secure SDLC

There are 6 key phases that you should know:

1. **Planning and Requirements Gathering (with Security in Mind)**

   - At this stage, it’s crucial to gather both functional and security requirements. By considering security from the outset, you ensure that the software design accounts for potential threats and compliance with security standards (e.g., GDPR, HIPAA).
   - **Example Security Activities**: Threat modeling, risk assessments, and compliance mapping.

2. **Design (Secure Architecture)**

   - During the design phase, architectural decisions should be made with security as a priority. This involves creating a robust design that can mitigate common security threats.
   - **Example Security Activities**: Security design patterns, defining security controls, and identifying attack vectors.

3. **Development (Secure Coding Practices)**

   - Secure coding is the first line of defense for your application. You're literally ensuring that you are preventing vulnerabilites by coding in secure manner and following best practices for preventing things like SQL Injection and Cross-Site Scripting (XSS). The best practices will differ based on the language that you're coding in, but the concept itself is transferable.
   - **Example Security Activities**: Code reviews, static application security testing (SAST), and dependency scanning.

4. **Testing (Security Testing)**

   - Automated and manual security testing should be embedded in this phase to catch vulnerabilities early. Instead of relying solely on traditional testing, specific security tests like penetration testing and dynamic analysis are key.
   - **Example Security Activities**: Dynamic Application Security Testing (DAST), penetration testing, and fuzz testing.

5. **Deployment (Secure Configuration and Monitoring)**

   - Security continues during deployment by ensuring that applications are deployed securely. This includes using secure configurations, Infrastructure as Code (IaC) security, and container security practices.
   - **Example Security Activities**: Reviewing deployment configurations, container security, and ensuring least privilege access controls.

6. **Maintenance (Continuous Security and Monitoring)**
   - After deployment, the application enters the maintenance phase, where it’s essential to continue monitoring for new vulnerabilities and regularly apply patches.
   - **Example Security Activities**: Continuous monitoring, patch management, and incident response.

## Recommended Resources

Before we move onto the next section, here are some resources that I believe you should look into to help you better understand the SDLC and SSDLC:

### YouTube Videos

#### Secure SDLC

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/snJGzyXzVec?si=eFEeMQKn3207uc_g"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### Introduction To The Software Development Life Cycle (SDLC)

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/Fi3_BjVzpqk?si=OhL-aUx9PSdjCPnf"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### Agile vs Waterfall Methodlogy

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/5RocT_OdQcA?si=4d7jjvy_y7aPrhSm"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

<!-- Links -->

[Damien Burks]: https://www.linkedin.com/in/damienjburks/
