---
id: secure-coding
title: Secure Coding Overview
description: Writing Software That Is Secure by Design
sidebar_position: 3
---

Author: [Damien Burks]

Now that you understand the **Secure Software Development Life Cycle (Secure SDLC)** and how security is embedded across every phase of software delivery, it’s time to zoom in on one of the most critical phases in that lifecycle: **development**.

This page focuses on **secure coding**, which is the practice of writing software in a way that reduces risk by design, not by accident. While the Secure SDLC defines _where_ security belongs, secure coding defines _how_ developers actually implement it in code.

## Overview

Secure coding is the discipline of writing software that _anticipates misuse_, enforces trust boundaries, and fails safely when things go wrong. In modern applications, code is constantly exposed to untrusted inputs, third-party dependencies, APIs, and users, ultimately making secure coding the _**first meaningful line of defense**_.

![Secure Coding Diagram](/img/blueprint/secure_coding_design.png)

:::note
You can find the original image here: [Secure coding - What is it all about? | GeeksForGeeks](https://www.geeksforgeeks.org/blogs/secure-coding-what-is-it-all-about/). Be sure to give this article a read as it further emphasizes the importance of secure coding.
:::

Within the Secure SDLC, secure coding lives primarily in the **development phase**, but its impact extends far beyond it. Decisions made while writing code directly influence the effectiveness of testing, deployment, monitoring, and incident response later on.

In DevSecOps, secure coding is a core **shift-left practice**. The earlier insecure patterns are avoided in code, the less costly and disruptive they are to fix downstream.

## Common Secure Coding Failure Patterns

Most software vulnerabilities are not caused by advanced attackers, but by **repeated, predictable failure patterns** during development.

| **Pattern**               | **What Goes Wrong**                   | **Why It Happens**                      |
| ------------------------- | ------------------------------------- | --------------------------------------- |
| Untrusted Input Handling  | SQL Injection, XSS, command injection | Inputs are assumed to be safe           |
| Broken Access Control     | IDOR, privilege escalation            | Authorization checks occur too late     |
| Insecure State Management | Session fixation, auth bypass         | Trust is tied to client-controlled data |
| Secrets in Code           | Credential leaks, token exposure      | Convenience over lifecycle security     |
| Insecure Serialization    | Remote code execution                 | Unsafe parsing of untrusted data        |
| Poor Error Handling       | Information disclosure                | Errors reveal internal system details   |

:::tip
Secure coding is about eliminating entire classes of risk, not _just_ chasing individual bugs.
:::

## Secure Coding Across the SDLC

Secure coding decisions occur throughout the software development lifecycle, not just during implementation.

### 1. **Design Phase**

- Identify trust boundaries and untrusted inputs
- Define authorization requirements early
- Minimize implicit trust between components
- Favor secure defaults over flexible configurations

### 2. **Implementation Phase**

- Validate and constrain all external inputs
- Use safe language and framework APIs
- Handle errors securely without exposing internals
- Avoid hardcoding secrets or sensitive configuration

### 3. **Review & Enforcement Phase**

- Perform security-focused code reviews
- Use static analysis to enforce consistency
- Treat findings as feedback, not failures
- Prevent insecure patterns from re-entering the codebase

## Secure Coding Best Practices

1. **Treat All Input as Untrusted**  
   Assume all external data can be malicious, regardless of source.

2. **Enforce Authorization Explicitly**  
   Never rely on client-side checks or implied trust.

3. **Fail Securely**  
   Errors should protect the system, not expose it.

4. **Prefer Secure Defaults**  
   Make the secure path the easiest path.

5. **Protect Secrets Throughout Their Lifecycle**  
   Inject secrets at runtime and rotate them regularly.

6. **Reduce Complexity Where Possible**  
   Simpler code is easier to reason about and secure.

## Integrating Secure Coding into DevSecOps Pipelines

Secure coding practices scale when reinforced by automation. So make sure you:

- Run static analysis early in CI pipelines
- Enforce secure coding standards consistently
- Use linters and SAST tools to detect common failure patterns
- Avoid blocking pipelines without clear remediation guidance

:::important
Automation supports secure coding. However, it does not replace secure design or thoughtful implementation.
:::

## Recommended Tools

| **Tool**                                                     | **Purpose**                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------------- |
| [SonarQube](https://www.sonarsource.com/products/sonarqube/) | Detects code quality issues and common security flaws               |
| [Semgrep](https://semgrep.dev/)                              | Pattern-based static analysis for insecure coding patterns          |
| [Snyk](https://snyk.io/)                                     | Identifies vulnerabilities in code and open-source dependencies     |
| [Trivy](https://trivy.dev/)                                  | Scans repositories, dependencies, and artifacts for vulnerabilities |

## Recommended Resources

### Books

| **Book Title**                    | **Author**  | **Link**                          | **Why It’s Useful**                                                                                                                                                                       |
| --------------------------------- | ----------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Alice and Bob Learn Secure Coding | Tanya Janca | [Amazon](https://amzn.to/3LXvvf0) | A practical, developer-focused guide to writing secure code by understanding common vulnerability patterns, secure design principles, and how attackers exploit insecure implementations. |

### YouTube Videos

#### Common Secure Coding Techniques

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/oa1qGqRWa1M?si=mDXvRyFBPvqkTmLI"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### Secure Coding Techniques (CompTIA Security+)

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/IEIGEjy-W4Q?si=IDJmvbUOC0-3Fv-F"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### Secure Code Review for Beginners

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/videoseries?si=_zcbKsdfZpgLcrvU&amp;list=PLtsU37FO9pdrYs4QdcK9WPU8XC2DRi8XL"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

### Articles & Standards

- https://owasp.org/www-project-top-ten/
- https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/
- https://csrc.nist.gov/projects/ssdf
- https://www.securecoding.org/

## Practice What You’ve Learned

Design and document a **Secure Coding blueprint** for a small application of your choice.

1. **Identify trust boundaries and external inputs** within the application (user input, APIs, files, environment variables).
2. Map common **secure coding failure patterns** (for example, untrusted input handling or broken access control) to areas of the code where they could realistically occur.
3. Choose at least one **secure coding enforcement mechanism** (for example, Semgrep, SonarQube, Snyk, or Trivy) and document what patterns it would help detect.
4. Create a short **Secure Coding flow diagram** using Lucidchart, Excalidraw, or Draw.io that shows where secure coding decisions and checks occur during development.
5. _Bonus:_ integrate one secure coding check into a CI/CD pipeline to reinforce how insecure patterns can be caught before deployment.

✅ **Capstone Goal:** Demonstrate the ability to identify insecure coding patterns early, apply secure-by-design principles during implementation, and reinforce those decisions with automated checks. Your deliverable should serve as a reusable Secure Coding reference for future projects or teams.

<!-- Links -->

[Damien Burks]: https://damienjburks.com
