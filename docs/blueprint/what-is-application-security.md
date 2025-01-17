---
id: what-is-application-security
title: What is Application Security?
description: Application Security Defined
sidebar_position: 2
---

Author: [Damien Burks]

Welcome to the very first page of The DevSec Blueprint. I've been sure to do my best structuring this content in an order that makes sense. Before we dive into the concept of DevSecOps and defining it, there are a _few_ concepts that I think you all need to be aware of starting with Application Security.

## Overview

So, what is Application Security? According to [Imperva](https://www.imperva.com/learn/application-security/application-security/), Application Security aims to protect software application code and data against cybersecurity threats and vulnerabilities. This includes using tools to scan your code, fixing the issues within your code, and doing a bit of threat modeling when designing your application to ensure that you're preventing vulnerabilites from being introduced into your code.

This process really happens within phases within the _Secure Software Development Life Cycle (SSDLC)_, which we'll define and explain in more detail in the next page. But, let's talk a little bit about why this is actually important.

## Why is Application Security Important?

We're in the digital age where information is bought and sold for a price. The thing that I want you to understand is that most of this information is stored behind or within some type of application. I am most certain that you log into a web application to pay your bills or view what's your bank account right? So imagine if that application that you using to view that data and pay those bills is vulnerable. At this point, there is a _way_ for someone to compromise the system, potentially your sensitive information and possibly someone elses, and then use that against you or/and sell it on the dark web.

So, to help bring this home, I want you to understand that applications are often targeted by attackers looking to exploit vulnerabilities for unauthorized access, data theft, or other malicious purposes. If an application is poorly structured, threat modeled, or secured, here are some of the underlying impacts and affects:

- **Data breaches**: Loss or exposure of sensitive data.
- **Compliance violations**: Non-compliance with industry regulations like GDPR or HIPAA.
- **Reputational damage**: Loss of customer trust and market position.

## Common Application Security Vulnerabilities

There are a list of common security vulnerabilites that change every year. You'll want to ensure that you pay close attention to the [OWASP Top 10](https://owasp.org/www-project-top-ten/) as it is an excellent way to stay up-to-date on the most common vulnerabilities that affect organizations in a **major** way.

However, I've taken the liberty of listing out some of the most common vulnerabilites that I"ve experienced that are still pretty impactful that you should know:

1. **SQL Injection**: Malicious input allows attackers to manipulate queries to a database, potentially gaining access to sensitive information.
2. **Cross-Site Scripting (XSS)**: Attackers inject malicious scripts into web pages, potentially affecting other users.
3. **Insecure Authentication and Authorization**: Weak or improperly configured access controls can allow unauthorized users to access sensitive data.
4. **Sensitive Data Exposure**: Inadequate protection of sensitive information, such as encryption or tokenization, can lead to data breaches.

## SAST and DAST

There are ways mitigate and eliminate those vulnerabilites by leveraging two key testing methods: **Static Application Security Testing (SAST)** and **Dynamic Application Security Testing (DAST)**. These techniques play an essential role in identifying vulnerabilities within your code or your running application.

**Static Application Security Testing (SAST)** is a white-box testing technique that analyzes the application's source code, bytecode, or compiled binaries for vulnerabilities. White-box testing refers to the hacker an understanding of the system prior to testing it for vulnerabilites.

SAST tools scan the code without executing the program, allowing developers to catch potential security issues early in the development process, which is nice. The benefits of SAST are:

- **Early Detection**: Since SAST runs on the source code, it can detect security issues during development, even before the code is compiled or deployed.
- **Comprehensive Coverage**: SAST can analyze all code paths and uncover vulnerabilities such as SQL injection, XSS, buffer overflows, and insecure coding practices.
- **Automated**: SAST tools can be integrated into the CI/CD pipeline, automatically analyzing code upon each commit or build.

On the other hand, **Dynamic Application Security Testing (DAST)** is a black-box testing technique that examines the application's running state by simulating real-world attacks. Black-box testing refers to the tester not having any knowledge about the application or product, which is what most pentesters or hackers do anyway.

DAST tools test applications in their operational environments (e.g., web apps, APIs) to find vulnerabilities that may only become apparent during runtime, which can give you a very _accurate_ assessment of what is truly components of your app is truly vulnerable. Here are some of the benefits of DAST:

- **Runtime Detection**: Since DAST tests a running application, it can catch vulnerabilities like misconfigurations, authentication issues, and other flaws that arise when the application is in use.
- **No Access to Source Code**: DAST doesn’t need access to the application’s code, making it effective for identifying vulnerabilities in third-party applications and APIs.
- **Real-World Simulation**: DAST mimics the behavior of a real-world attacker, identifying potential attack vectors from an external perspective.

While SAST focuses on finding vulnerabilities in the code itself, DAST assesses how the application performs once deployed. Together, they provide a comprehensive approach to security testing:

- **SAST**: Ideal for early-stage detection, scanning static code and catching issues before the application is deployed.
- **DAST**: Crucial for identifying vulnerabilities that can only be found in the operational environment, such as misconfigurations or runtime-specific issues.

By incorporating both SAST and DAST into the SDLC, you ensure that security testing occurs at both the code level and the operational level, minimizing the risk of vulnerabilities slipping through the cracks.

## Tools and Projects

There are a plethora of tools that you should play around with. Some of these will really test your application penetration testing skills and help you better understand how these vulnerabilities work. I've listed them all out in a table below:

| **Project Name**                                                                      | **Description**                                                                                                           |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/)                         | A vulnerable web app for practicing web security testing with a focus on OWASP Top 10 vulnerabilities.                    |
| [Damn Vulnerable Web Application (DVWA)](https://github.com/digininja/DVWA)           | PHP/MySQL-based web app designed for practicing penetration testing skills.                                               |
| [Vulnerable Node.js Application (VulnNode)](https://github.com/cr0hn/vulnerable-node) | A vulnerable Node.js application for practicing JavaScript/Node.js specific security testing.                             |
| [Hackazon](https://github.com/rapid7/hackazon)                                        | An e-commerce platform that simulates a real-world site with multiple security vulnerabilities.                           |
| [Mutillidae II](https://github.com/webpwnized/mutillidae)                             | A free, open-source vulnerable web application that covers over 40 vulnerabilities for testing.                           |
| [bWAPP](http://www.itsecgames.com/)                                                   | A PHP-based vulnerable app with over 100 web vulnerabilities, covering OWASP Top 10 and beyond.                           |
| [OWASP WebGoat](https://owasp.org/www-project-webgoat/)                               | An insecure web application designed for practicing web security vulnerabilities and solutions.                           |
| [NodeGoat](https://github.com/OWASP/NodeGoat)                                         | A deliberately insecure Node.js app, focusing on vulnerabilities specific to JavaScript and Node.js.                      |
| [OWASP Security Shepherd](https://owasp.org/www-project-security-shepherd/)           | A platform designed for learning security principles with a capture-the-flag format for both beginner and advanced users. |

## Additional Resources

To help you better understand application security, here are some resources that I've hand picked out for you to review and look at:

### Books

| **Book Title**                                                               | **Author**                     | **Link**                          |
| ---------------------------------------------------------------------------- | ------------------------------ | --------------------------------- |
| Alice and Bob Learn Application Security                                     | Tanya Janca                    | [Amazon](https://a.co/d/awZU6Mb)  |
| The Web Application Hacker's Handbook: Finding and Exploiting Security Flaws | Dafydd Stuttard & Marcus Pinto | [Amazon](https://amzn.to/4fJwQPU) |
| Hacking APIs: Breaking Web Application Programming Interfaces                | Corey J. Ball                  | [Amazon](https://amzn.to/4fOGHnK) |

### YouTube Videos

#### Application Security 101 - What you need to know in 8 minutes

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/Dp019cWu1cg?si=AHNFdEYNPoa4XGWZ"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### What is SAST and DAST?

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/Nz7WCh9HQpo?si=jlloCTA87MRipc0b"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

### Articles

If you're into blogs and want to dive more deeply into Application Security, check out the ones below:

- https://www.crowdstrike.com/en-us/cybersecurity-101/application-security/
- https://www.ibm.com/topics/application-security
- https://medium.com/googledeveloperseurope/what-is-application-security-all-you-need-to-know-guide-blog-3ceee69deb11

<!-- Links -->

[Damien Burks]: https://www.youtube.com/@damienjburks
