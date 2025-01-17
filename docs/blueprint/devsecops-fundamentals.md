---
id: devsecops-fundamentals
title: DevSecOps Fundamentals
description: Defining and explaining DevSecOps at a high-level
sidebar_position: 4
---

Author: [Damien Burks]

OKAY! You've reach my favorite section of the blueprint - _What is DevSecOps?_

At this point, you should have a fundamental understanding all the concept I've listed below:

1. DevOps
1. Version Control System(s)
1. Programming
1. Linux/Bash Scripting
1. CI/CD
1. Application Security
1. the Secure Software Development Life Cycle (SSDLC)... and the Software Development Life Cycle (SDLC)

If you do, then you're free to move forward. If you haven't, then I **HIGHLY** suggest you go back, read, experiment, and try to play around with the projects and tools.

## Overview

According to [RedHat](https://www.redhat.com/en/topics/devops/what-is-devsecops), _DevSecOps stands for development, security, and operations. It's an approach to culture, automation, and platform design that integrates security as a shared responsibility throughout the entire IT lifecycle._

The beautiful thing about this is that it extends the principles of DevOps (collaboration, automation, and continuous delivery) by embedding security into every phase of the software development lifecycle (SDLC), which will be covered later.

Ultimately, the goal is to shift security "left," or earlier, in the SDLC, ensuring that vulnerabilities are identified and mitigated before they can become critical issues.

![DevSecOps Model](/img/blueprint/devsecops_model.png)

> Image Source: [Atlassian | DevSecOps Tools](https://www.atlassian.com/devops/devops-tools/devsecops-tools)

Over time, DevSecOps has evolved as a response to the limitations of DevOps, where security was often an afterthought. It emerged from the need to include security in the agile and continuous delivery practices of DevOps, which allows organizations to reduce the risk of security vulnerabilities and ensure compliance with industry regulations.

### Why is it important?

Well, traditional security practices often creßate bottlenecks in the fast-paced world of DevOps, as they typically occur at the end of the development cycle. DevSecOps addresses this by incorporating security measures from the start, enabling faster and more secure software releases.

## Core Principles of DevSecOps

To get a better understanding of DevSecOps as a whole, you need to understand the core principles of DevSecOps. I've listed the **four** key principals that you need to understand below:

1. **Integration of Security**

   Security is integrated into every phase and sub-phase of the SDLC. In reality, the SSDLC is a precursor of DevSecOps. This holistic approach ensures that **security is NOT an afterthought** but a fundamental aspect of the development process.

2. **Automation**

   Automation is crucial in DevSecOps to ensure that security checks are consistently applied without _**severly**_ impacting the developer experience. Extra _emphasis_ on minimizing the impact on the developer experience. In addition, automated security tests, such as static code analysis and vulnerability scans, can and should be integrated into CI/CD pipelines to catch issues early in the development lifecycle.

3. **Collaboration**

   DevSecOps fosters a culture of collaboration among development, security, and operations teams. This cultural movement breaks down silos and encourages a shared responsibility between the developers, operations, and security team, leading to creation of a very cohesive and effective strategy for secure software development and deployment.

4. **Continuous Feedback & Monitoring**

   Continuous feedback loops and monitoring allows for real-time insights into the security posture of the application and infrastructure. This enables teams to quickly identify and remediate security issues as they arise.

## Additional Resources

Before you move onto the next section, here are some of the various resources that I recommend you look into, such as certifications, books to read, and YouTube videos, etc:

### Books

| **Book Name**                                                                                                           | **Author**                                            | **Link**                          |
| ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | --------------------------------- |
| The Phoenix Project                                                                                                     | Gene Kim, Kevin Behr, and George Spafford             | [Amazon](https://a.co/d/7emFNLg)  |
| Continuous Delivery                                                                                                     | Jez Humble and David Farley                           | [Amazon](https://a.co/d/0ixNvOq)  |
| The DevOps Handbook                                                                                                     | Gene Kim, Patrick Debois, John Willis, and Jez Humble | [Amazon](https://a.co/d/3NLl4hM)  |
| Securing DevOps                                                                                                         | Julien Vehent                                         | [Amazon](https://a.co/d/6Fgtzin)  |
| DevSecOps: A leader’s guide to producing secure software without compromising flow, feedback and continuous improvement | Glenn Wilson                                          | [Amazon](https://amzn.to/4fsfMye) |
| Cloud Native DevOps with Kubernetes                                                                                     | John Arundel and Justin Domingus                      | [Amazon](https://a.co/d/2fGdXaE)  |
| Infrastructure as Code                                                                                                  | Kief Morris                                           | [Amazon](https://a.co/d/cINH2dd)  |
| Kubernetes Security                                                                                                     | Liz Rice                                              | [Amazon](https://a.co/d/2kLIXF9)  |
| Securing DevOps                                                                                                         | Julien Vehent                                         | [Amazon](https://a.co/d/6Fgtzin)  |

### Articles

- https://developer.ibm.com/articles/devsecops-what-and-why/
- https://www.microsoft.com/en-us/security/business/security-101/what-is-devsecops
- https://www.redhat.com/en/topics/devops/what-is-devsecops
- https://aws.amazon.com/compliance/shared-responsibility-model/

### Certifications

So if I had to recommend certifications that you should get in order to transition into DevSecOps, here are the list of things that I would recommend (not in a specific order):

| Name                                                                                                                           | Level        |
| ------------------------------------------------------------------------------------------------------------------------------ | ------------ |
| [CompTIA Security+](https://www.comptia.org/certifications/security)                                                           | Beginner     |
| [CompTIA Linux+](https://www.comptia.org/certifications/linux)                                                                 | Beginner     |
| [Certified Kubernetes Administrator (CKA)](https://www.cncf.io/certification/cka/)                                             | Intermediate |
| [Certified Kubernetes Application Developer (CKAD)](https://www.cncf.io/certification/ckad/)                                   | Intermediate |
| [Certified DevSecOps Professional (CDP)](https://www.practical-devsecops.com/certifications/certified-devsecops-professional/) | Intermediate |
| [Certified DevSecOps Expert (CDE)](https://www.practical-devsecops.com/certifications/certified-devsecops-expert/)             | Expert       |
| [ISC^2 CSSLP](https://www.isc2.org/Certifications/CSSLP)                                                                       | Expert       |

If you're looking to specialize in Cloud, then you'll want to look at these:

| **Name**                                                                                                                            | **Level**    |
| ----------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| [AWS Certified Security – Specialty](https://aws.amazon.com/certification/certified-security-specialty/)                            | Intermediate |
| [Microsoft Certified: Azure Security Engineer Associate](https://learn.microsoft.com/en-us/certifications/azure-security-engineer/) | Intermediate |
| [Google Professional Cloud Security Engineer](https://cloud.google.com/certification/cloud-security-engineer)                       | Intermediate |

### YouTube Videos

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

#### What is DevSecOps? - Hackitect's playground

<iframe
    width="100%"
    height="400"
    src="https://www.youtube.com/embed/DOlE7691Q3o?si=oBUjzHIQawYkvTZJ"
    frameborder="0"
    allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen
></iframe>

<!-- Links -->

[Damien Burks]: https://www.youtube.com/@damienjburks
