---
id: what-is-the-secure-sdlc-and-sdlc
title: What is the Secure SDLC?
description: SDLC vs S-SDLC!
sidebar_position: 3
---

Author: [Damien Burks]

Now that we've covered Application Security, and you're familiar with key concepts of Application Security, let's dive into the Software Development Life Cycle (SDLC) and Secure Software Development Life Cycle (SSDLC).

## Overview

One of the most critical building blocks is the **Secure Software Development Life Cycle (Secure SDLC)**. By establishing a strong understanding of Secure SDLC, you will be better equipped to comprehend how security is integrated throughout the development lifecycle.

## What is the SDLC?

![SDLC](/img/blueprint/sdlc_image.webp)

> Image Source: [Software Development Life Cycle (SDLC) | Snyk](https://snyk.io/learn/secure-sdlc/#history)

The **Software Development Life Cycle (SDLC)** is a **structured** process used for developing software applications. To keep it short, the SDLC consists of six key phases:

1. **Planning and Requirements Gathering**: Understanding what the software needs to do and ensuring it aligns with business requirements.
2. **Design**: Architecting the solution to meet _functional_ and _non-functional_ requirements.
3. **Development**: Writing the _actual_ code... or programming.
4. **Testing**: Ensuring that the software works as intended and is free from bugs (that don't impact the features).
5. **Deployment**: Releasing the software into higher environments (QA, Production)
6. **Maintenance**: Ongoing updates/enhancements and fixes post-release

The downside to this process is that there is no security baked into any of phases. Formally known as the traditional SDLC, when developers follow this model, security is often treated as an _afterthought_ and addressed after the deployment phase and _well_ into the maintenance phase (and I do mean _well into the maintanence phase_). This reactive approach can result in security issues being discovered late, which can be quite costly and disruptive to fix overtime. So, when you're developing applications of any kind, pretty pretty please keep this in mind.

## The Secure SDLC

Now that we've covered the SDLC at a high-level, let's talk about the replacement (or the better process to follow).

The **Secure SDLC** (SSDLC) is an evolution of the traditional SDLC model, where security is a key consideration at **every phase** of the process. Rather than treating security as a final step, it becomes an significant part of each phase by helping to reduce vulnerabilities and risks earlier in the lifecycle. So, when you the term "shift-left" or "shifting-left", I want you think about the SSDLC, because that's essentially what we're doing. We are moving security from the end of the SDLC and integrating it into every phase within the SDLC.

One of the key benefits of the SSDLC is that you are finding and figuring out any security issues as you iterate through the Secure SDLC, which overtime helps save cost and eliminates the overhead and potential of releasing vulnerabilities into the wild.

![SSDLC](/img/blueprint/ssdlc_image.webp)

> Image Source: [Secure Software Development Life Cycle (SSDLC) | Snyk](https://snyk.io/learn/secure-sdlc/#phases)

### Key Phases of the Secure SDLC

There are 6 key phases that you should know:

1. **Planning and Requirements Gathering (with Security in Mind)**

   - At this phase, it’s crucial to gather both functional and security requirements. By considering security from the outset, you ensure that the software design accounts for potential threats and compliance with security standards such as GDPR, HIPPA, etc. Some example security activities that you should be aware of that happens at this phase include:

     1. Threat modeling (very... very... important)
     1. Conducting risk assessments
     1. Complaince mapping

2. **Design (Secure Architecture)**

   - During the design phase, architectural decisions should be made with security as a priority. This involves creating a robust design that can mitigate common security threats, which is **SUPER** important. Starting off with security in the design ensures that the developers code securely. Some example security activities that you should be aware of that happens at this phase include:

     1. Identifying security design patterns
     1. Defining security controls
     1. Identifying attack vectors and ways to mitigate them.

3. **Development (Secure Coding Practices)**

   - This is my **favorite phase**, because this is where the magic happens. However, you don't really get anywhere without coding _securely_. Secure coding is the first line of defense for your application. You're literally ensuring that you are preventing vulnerabilites by coding in secure manner and following best practices for preventing things like SQL Injection and Cross-Site Scripting (XSS). The best practices will differ based on the language that you're coding in, but the concept itself is transferable. Some example security activities that you should be aware of that happens at this phase include:

     1. Performing code reviews and pair programming
     1. Executing static application security testing (SAST) scans
     1. Checking your dependencies for vulnerabilities by running dependency scans against them.

4. **Testing (Security Testing)**

   - Okay... this is my _second_ favorite phase because you can to see if what you built truly works and is secured properly by performing automated and manual security tests. To add context, automated and manual security testing **should** be embedded in this phase to catch vulnerabilities early. Instead of relying solely on traditional testing, specific security tests like penetration testing and dynamic analysis are key. This can be achieved by:

     1. Performing or implementing Dynamic Application Security Testing (DAST) scanning
     1. Conducting penetration tests,
     1. Finding and using fuzz testing tools.

5. **Deployment (Secure Configuration and Monitoring)**

   - In this phase, security continues during deployment by ensuring that applications are deployed securely. This includes using secure configurations, Infrastructure as Code (IaC) security, and container security practices. Some example security activities that you should be aware of that happens at this phase include:

     1. The reviewal of deployment configurations to ensure that they adhere to best practices
     1. Container hardening and scanning
     1. Ensuring least privilege access controls for your application or infrastructure.

6. **Maintenance (Continuous Security and Monitoring)**

   - After deployment, the application enters the maintenance phase, where it’s essential to continue monitoring for new vulnerabilities and regularly apply patches or updates. If you did everything correctly the first time, your application should be pretty secure. From a security standpoint though, some common activities that happen in this phase that you should be aware of is:

     1. Implementing continous monitoring solutions and processes
     1. Creating patch management processes
     1. Developing and implementing an incident response plan (security and operations).

## Recommended Resources

Before we move onto the next section, here are some resources that I believe you should look into to help you better understand the SDLC and SSDLC:

### Books

| **Book Title**                                         | **Author**       | **Link**                          |
| ------------------------------------------------------ | ---------------- | --------------------------------- |
| Threat Modeling: Designing for Security                | Adam Shostack    | [Amazon](https://amzn.to/3Oa5dDP) |
| Designing Secure Software: A Guide for Developers      | Loren Kohnfelder | [Amazon](https://amzn.to/4euRz9c) |
| Clean Code: A Handbook of Agile Software Craftsmanship | Robert C. Martin | [Amazon](https://amzn.to/3O762xg) |

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

#### What is Threat Modeling and Why Is It Important?

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/h_BC6QMWDbA?si=Eb8VFjqBUYxsHcFim"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

<!-- Links -->

[Damien Burks]: https://www.youtube.com/@damienjburks
