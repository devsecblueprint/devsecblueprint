---
id: container-security
title: Container Security
description: Securing Applications through Containerization Best Practices
sidebar_position: 5
---

Author: [Damien Burks]

Now that you’ve explored the foundations of Application Security, the Secure SDLC, and the principles of DevSecOps, it’s time to focus on one of the most important parts of modern software delivery: **Container Security**.

## Overview

Containers have changed how we build, package, and deploy software. They make applications portable, consistent, and fast to ship, but they also introduce new attack surfaces that must be managed carefully. From outdated base images to leaked secrets and over-privileged containers, insecure configurations can make containers **the easiest entry point into your environment**.

In DevSecOps, container security isn’t just about scanning images. It’s about embedding security throughout the **entire container lifecycle**... from build, to ship, to runtime.

![Example Image](/img/blueprint/container_scanning_image.png)

:::note
You can find the original image here: [Securing Containers from Build to Runtime | Microsoft Defender for Cloud](https://techcommunity.microsoft.com/blog/microsoftdefendercloudblog/securing-containers-from-build-to-runtime/3612831)
Also, containers give speed, but speed without security invites risk. Treat every image and runtime as part of your security perimeter.
:::

## Common Attack Surfaces

To secure containers effectively, you need to understand where they’re most vulnerable:

| **Surface**           | **Description**                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------- |
| **Base Images**       | Outdated or unverified base images may include known CVEs and hidden dependencies.          |
| **Image Layers**      | Each layer can add unnecessary files, secrets, or unpatched binaries if not reviewed.       |
| **Secrets Exposure**  | Hardcoded credentials or unencrypted environment variables often end up baked into images.  |
| **Container Runtime** | Containers running as root or with privileged access can compromise the host system.        |
| **Networking**        | Misconfigured networks may expose internal services to the public internet.                 |
| **Registry Security** | Using unverified public images or insecure registries risks introducing malicious software. |

:::tip
Most container breaches stem from configuration mistakes, not advanced exploits. Start by securing the basics.
:::

## The Container Security Lifecycle

Container security follows the same shift-left philosophy as DevSecOps: **secure early, monitor continuously, and automate everything.**

### 1. **Build Phase**

- Scan base images and dependencies for known vulnerabilities.
- Use **minimal base images** to reduce the attack surface.
- Enforce consistent image signing and tagging.
- Maintain a **Software Bill of Materials (SBOM)** to track what’s inside every image.

### 2. **Ship Phase**

- Store only **trusted images** in private or verified registries.
- Apply access controls and automated scanning at the registry level.
- Sign and verify images before deployment.
- Avoid using the “latest” tag. Always version explicitly for traceability.

### 3. **Run Phase**

- Run containers with **least privilege** and never as root.
- Apply resource limits (CPU, memory) to prevent denial-of-service conditions.
- Enable runtime monitoring and anomaly detection.
- Isolate workloads using namespaces, cgroups, and sandboxing.

## Best Practices for Container Security

1. **Adopt Immutable Infrastructure**  
   Treat containers as disposable. Rebuild images to patch, never modify live ones.

2. **Minimize the Attack Surface**  
   Use lightweight base images (for example Alpine or Distroless) and remove unnecessary packages.

3. **Scan Early and Often**  
   Integrate container scanning into CI/CD pipelines to catch vulnerabilities before deployment.

4. **Protect Secrets**  
   Inject secrets securely at runtime using tools like **Vault** or **Secrets Manager**. Never bake them into images.

5. **Implement Image Signing and Verification**  
   Use tools like **Cosign** or **Notary** to verify image integrity before deployment.

6. **Monitor Runtime Behavior**  
   Watch for abnormal processes, network activity, and privilege escalations. Tools like **Falco** can help.

7. **Secure Registries**  
   Restrict access to trusted users and enforce scanning on every pushed image.

## Recommended Tools

| **Tool**                   | **Purpose**                                                            |
| -------------------------- | ---------------------------------------------------------------------- |
| **Trivy**                  | Scans images, file systems, and repos for vulnerabilities and secrets. |
| **Grype / Anchore Engine** | Performs deep image analysis and compliance reporting.                 |
| **Clair**                  | Scans Docker and OCI images for known vulnerabilities.                 |
| **Docker Scout**           | Integrates vulnerability insights directly into Docker builds.         |
| **Falco**                  | Detects runtime anomalies and suspicious behavior.                     |
| **Cosign**                 | Signs and verifies images for integrity and provenance.                |

:::note
Combine multiple tools to cover different stages of the container lifecycle. No single scanner does it all.
:::

## Practice What You’ve Learned

Now it’s your turn to apply what you’ve learned.

1. Choose a small containerized app (for example, a Flask API or Node.js microservice).
2. Scan your image for vulnerabilities using **Trivy** or **Grype**.
3. Add runtime monitoring with **Falco** or a similar tool.
4. Review your Dockerfile for security misconfigurations.

✅ **Capstone Goal:** Show that you can identify and remediate vulnerabilities across the container build, ship, and run phases.

:::important
Remember, security doesn’t end at deployment. Containers must be monitored, patched, and rebuilt regularly to stay secure.
:::

## Recommended Resources

### Recommended Certifications

| **Certification**                                 | **Provider**        | **Why It’s Relevant**                                       |
| ------------------------------------------------- | ------------------- | ----------------------------------------------------------- |
| Docker Certified Associate (DCA)                  | Docker              | Validates container lifecycle and security fundamentals.    |
| Certified Kubernetes Application Developer (CKAD) | CNCF                | Reinforces container orchestration and deployment security. |
| CompTIA Security+                                 | CompTIA             | Strengthens foundational security knowledge.                |
| Certified DevSecOps Professional (CDP)            | Practical DevSecOps | Focuses on container scanning and policy automation.        |

### 📚 Books

| **Book Title**                                                                             | **Author**                                     | **Link**                          | **Why It’s Useful**                                                                                           |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Container Security: Fundamental Technology Concepts That Protect Cloud Native Applications | Liz Rice                                       | [Amazon](https://amzn.to/48SqKN3) | Explains how containers work under the hood and how to secure them effectively throughout their lifecycle.    |
| Application Container Security Guide - NIST SP 800-190                                     | National Institute of Standards and Technology | [Amazon](https://amzn.to/4oNXcEP) | Provides official NIST guidance on container threats, mitigations, and best practices for secure deployments. |
| Kubernetes Security                                                                        | Liz Rice                                       | [Amazon](https://a.co/d/2kLIXF9)  | Provides a clear, technical guide to securing Kubernetes workloads and understanding container threats.       |

### 🎥 Videos

#### What is Container Security?

<iframe
  width="100%"
  height="480"
  src="https://www.youtube.com/embed/BVR08NmTW80?si=b-rf5jr1PhutO9vF"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### How To Secure & Harden Docker Containers

<iframe
  width="100%"
  height="480"
  src="https://www.youtube.com/embed/CQLtT_qeB40?si=JP-aZSIzdqJow82s"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

<!-- Links -->

[Damien Burks]: https://damienjburks.com
