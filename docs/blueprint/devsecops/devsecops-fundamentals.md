---
id: devsecops-fundamentals
title: DevSecOps Fundamentals
description: Defining and explaining DevSecOps at a high level
sidebar_position: 4
---

Author: [Damien Burks]

Now that you've learned how the Secure Software Development Life Cycle (SSDLC) integrates security throughout every phase of development, it's time to explore the culture and mindset that makes it work in practice: **DevSecOps**.

## Overview

According to [Red Hat](https://www.redhat.com/en/topics/devops/what-is-devsecops), _DevSecOps stands for development, security, and operations. It's an approach to culture, automation, and platform design that integrates security as a shared responsibility throughout the entire IT lifecycle._

What makes DevSecOps powerful is that it takes the principles of DevOps and extends them by embedding security into every phase of the software development lifecycle (SDLC). The ultimate goal is to **shift security left**, meaning security activities happen earlier in the process. This ensures vulnerabilities are identified and fixed before they can become critical issues.

![DevSecOps Model](/img/blueprint/devsecops_model.png)

:::note
You can find the original image source here: [Atlassian | DevSecOps Tools](https://www.atlassian.com/devops/devops-tools/devsecops-tools)
:::

Over time, DevSecOps has evolved from the limitations of traditional DevOps, where security was often treated as an afterthought. It emerged from the need to include security in agile and continuous delivery practices so that teams can reduce risk, improve reliability, and ensure compliance with industry standards.

## Why DevSecOps Matters

Traditional security practices can create bottlenecks in fast-moving DevOps environments, since they typically occur at the end of the development cycle. DevSecOps solves this by integrating security from the start, enabling faster and more secure software releases. In short, DevSecOps is about _prevention_, not _reaction_.

:::tip
The best DevSecOps teams view security as part of the delivery process, not something separate from it.
:::

## Core Principles of DevSecOps

To understand DevSecOps, you need to grasp its four core principles. Each one plays a role in creating a secure, collaborative, and efficient development culture.

### 1. **Integration of Security**

Security is built into every phase of the SDLC. In fact, the Secure SDLC (SSDLC) is a direct precursor to DevSecOps. This holistic approach ensures that security is not an afterthought but a **default part of how software is designed, developed, and deployed**.

### 2. **Automation**

Automation ensures security checks happen consistently and efficiently without slowing developers down. Tools like static code analysis, dependency scanning, and container image scanning can be integrated directly into CI/CD pipelines to catch issues early.

:::important
Do your best to ensure that your automation enhances, not hinders, the developer experience.
:::

### 3. **Collaboration**

DevSecOps thrives on collaboration between development, operations, and security teams. By breaking down silos and sharing responsibility, teams create a unified approach to secure delivery. This shared culture helps teams make better decisions faster and ensures that everyone owns security.

### 4. **Continuous Feedback and Monitoring**

Continuous feedback loops provide real-time insight into the security posture of both applications and infrastructure. Monitoring tools detect misconfigurations, vulnerabilities, and anomalies as they occur, allowing teams to respond quickly and improve over time.

:::tip
Think of monitoring as the “eyes and ears” of DevSecOps. It turns lessons learned into actionable improvements.
:::

## Putting It All Together

When these four principles work together, DevSecOps transforms how organizations build and ship software:

| **Principle**           | **Purpose**                             | **Example Practice**                        |
| ----------------------- | --------------------------------------- | ------------------------------------------- |
| Integration of Security | Build security into every SDLC phase    | Threat modeling, secure design reviews      |
| Automation              | Reduce human error and speed delivery   | SAST, DAST, IaC scanning                    |
| Collaboration           | Align teams across disciplines          | Shared Slack channels, joint retrospectives |
| Continuous Feedback     | Improve continuously through visibility | Centralized dashboards, alerts, metrics     |

## Recommended Resources

Before you move onto the next section, here are some recommended resources to help you deepen your understanding of DevSecOps.

### Books

| **Book Title**                                           | **Author**                                            | **Link**                          | **Why It’s Useful**                                                                                              |
| -------------------------------------------------------- | ----------------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| The Phoenix Project                                      | Gene Kim, Kevin Behr, and George Spafford             | [Amazon](https://a.co/d/7emFNLg)  | Explains the cultural and organizational transformation that drives successful DevOps and DevSecOps adoption.    |
| Continuous Delivery                                      | Jez Humble and David Farley                           | [Amazon](https://a.co/d/0ixNvOq)  | Demonstrates how to automate and streamline software delivery, forming the foundation of modern CI/CD pipelines. |
| The DevOps Handbook                                      | Gene Kim, Patrick Debois, John Willis, and Jez Humble | [Amazon](https://a.co/d/3NLl4hM)  | Provides real-world practices for collaboration, automation, and continuous improvement across teams.            |
| Securing DevOps                                          | Julien Vehent                                         | [Amazon](https://a.co/d/6Fgtzin)  | Bridges the gap between DevOps and security by focusing on practical techniques for securing cloud applications. |
| DevSecOps: A Leader’s Guide to Producing Secure Software | Glenn Wilson                                          | [Amazon](https://amzn.to/4fsfMye) | Offers a leadership perspective on building secure software pipelines without slowing development teams down.    |
| Cloud Native DevOps with Kubernetes                      | John Arundel and Justin Domingus                      | [Amazon](https://a.co/d/2fGdXaE)  | Explains how to apply DevOps and security principles in cloud-native environments using Kubernetes.              |
| Infrastructure as Code                                   | Kief Morris                                           | [Amazon](https://a.co/d/cINH2dd)  | Teaches how to manage infrastructure through code for consistent, automated, and secure deployments.             |
| Kubernetes Security                                      | Liz Rice                                              | [Amazon](https://a.co/d/2kLIXF9)  | Provides a clear, technical guide to securing Kubernetes workloads and understanding container threats.          |

### Recommended Certifications

| **Certification**                            | **Provider**        | **Why It’s Relevant**                                                     |
| -------------------------------------------- | ------------------- | ------------------------------------------------------------------------- |
| Certified DevSecOps Professional (CDP)       | Practical DevSecOps | Focuses on integrating security automation across CI/CD workflows.        |
| Certified Kubernetes Administrator (CKA)     | CNCF                | Strengthens container orchestration and security knowledge.               |
| AWS Certified DevOps Engineer – Professional | AWS                 | Validates advanced knowledge of automated deployment and secure delivery. |
| Microsoft Certified: DevOps Engineer Expert  | Microsoft           | Emphasizes secure CI/CD and cultural collaboration.                       |
| Google Professional Cloud DevOps Engineer    | Google Cloud        | Combines cloud-native DevOps and security best practices.                 |
| ISC² CSSLP                                   | (ISC)²              | Connects software security principles with continuous delivery pipelines. |

### 🎥 YouTube Videos

#### What is DevSecOps? DevSecOps explained in 8 Mins

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/nrhxNNH5lt0?si=OC_5Tq6pBROq7DyC"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### What is DevSecOps? DevSecOps explained in 7 Mins

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/VLEF6MU0Wfg?si=dYktpIAnAej9Z2A7"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### Accelerate Your DevSecOps Journey: 5 Key Skills in 5 Minutes

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/7J9rjMbPZm4?si=FuH6jox0BE57Ip-n"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### What is DevSecOps? - Hackitect's Playground

<iframe
  width="100%"
  height="400"
  src="https://www.youtube.com/embed/DOlE7691Q3o?si=oBUjzHIQawYkvTZJ"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

### 📰 Articles

- [IBM: What and Why of DevSecOps](https://developer.ibm.com/articles/devsecops-what-and-why/)
- [Microsoft: What is DevSecOps?](https://www.microsoft.com/en-us/security/business/security-101/what-is-devsecops)
- [Red Hat: What is DevSecOps?](https://www.redhat.com/en/topics/devops/what-is-devsecops)
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)

## Practice What You’ve Learned

Now that you understand the fundamentals, it’s time to put them into practice.

1. Choose a small project (for example, a web app or microservice).
2. Identify where security should be integrated into your CI/CD process.
3. Add at least one automated security scan (SAST, dependency, or container).
4. Write a short summary of how DevSecOps principles improved your workflow.

✅ **Capstone Goal:** Demonstrate that you can apply DevSecOps principles in a real project by integrating security, automation, and collaboration into your delivery process.

:::important
Remember, DevSecOps isn’t about adding more tools. It’s about changing how teams think about security every day.
:::

<!-- Links -->

[Damien Burks]: https://damienjburks.com
