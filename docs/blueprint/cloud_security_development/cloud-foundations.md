---
id: cloud-foundations-for-security-builders
title: Cloud Foundations for Security Builders
description: Understanding the Core Concepts of Cloud Infrastructure
sidebar_position: 1
---

Author: [Damien Burks]

Welcome to the next page of the **Cloud Security Development** section! Before we start diving into identity, logging, and event-driven security, it’s important that we first understand the **building blocks of the cloud** itself. You can’t secure what you don’t understand, and this page will give you the foundation you’ll need to approach cloud security from an engineering mindset.

## Overview

So, what are **Cloud Foundations**?

In simple terms, cloud foundations refer to the **core services and architecture patterns** that every cloud provider—AWS, Azure, and Google Cloud—builds on top of. These services form the backbone of all workloads that you deploy, secure, and monitor.

According to [Google Cloud](https://cloud.google.com/architecture/framework/foundations), a solid foundation includes areas such as identity, networking, resource hierarchy, and monitoring. For security builders, these areas are where you’ll develop an understanding of how permissions, policies, and configurations actually interact in real environments.

Before we talk about automation or detection, let’s establish what these core areas are and why they matter.

## Why Cloud Foundations Matter

Every service, function, and container in the cloud is built on top of fundamental components like compute, storage, networking, and identity.  
When you understand these layers, you can identify where risk originates—and more importantly, **where to apply controls**.

Without that foundation, it’s easy to fall into patterns like:

- Over-provisioning accounts with administrator access.
- Creating public storage buckets that anyone can view.
- Forgetting to restrict traffic within a virtual network.
- Not understanding the difference between user data and metadata.

Each of these small missteps can lead to major exposure. Let’s look at each of the foundational components and what they mean for you as a security builder.

## Core Cloud Components

### 1. Compute

Compute resources are what actually “run” your code—virtual machines, containers, and serverless functions. From a security perspective, you’ll want to understand:

- **Isolation:** Ensure workloads are separated by accounts, projects, or namespaces.
- **Least privilege execution:** Functions, VMs, and containers should only assume roles that grant the permissions they need.
- **Patching:** Serverless functions may auto-patch, but EC2 or VM instances need lifecycle management.
- **Runtime visibility:** Monitor for drift, process injection, and unexpected outbound calls.

### 2. Storage

Storage is where your data lives—object storage (S3, Blob, GCS), block storage (EBS, Disk), and databases. The common risks include:

- **Public exposure:** Buckets or blobs configured for public access.
- **Encryption gaps:** Missing encryption at rest or in transit.
- **Improper IAM bindings:** Overly broad access roles like `Storage Admin` or `s3:*`.
- **Data lifecycle:** Forgotten snapshots, orphaned backups, and old versions of sensitive files.

When building security controls later, these are often the first areas to monitor and protect.

### 3. Networking

Networking connects all your resources together. Every cloud environment contains a virtual network (VPC, VNet, or VPC Network) that defines routing, access, and segmentation.

Security builders should pay attention to:

- **Segmentation:** Separate workloads by environment (dev, test, prod).
- **Inbound rules:** Avoid `0.0.0.0/0` (open to the internet).
- **Private endpoints:** Use internal gateways for communication between services.
- **Flow logs:** Enable logging to understand who’s talking to what.

The network layer is often the first line of defense, especially for lateral movement.

### 4. Identity and Access Management (IAM)

Identity is the most critical foundation in the cloud. It controls _who can do what, where, and when_. IAM consists of principals (users, groups, roles, or service accounts) and permissions (actions on resources).

Key best practices for builders include:

- **Principle of Least Privilege:** Grant only what’s needed for the task.
- **Separation of Duties:** Avoid giving both deploy and approval permissions to the same identity.
- **Role-Based Access:** Use roles instead of attaching policies directly to users.
- **Short-Lived Credentials:** Prefer temporary tokens and role assumption over static keys.

We’ll cover IAM in more depth in the next chapter, but you should always think of identity as your **first control layer**.

### 5. Monitoring and Logging

Visibility is the foundation of detection and response. Without logs, it’s impossible to prove who made a change or when it occurred.

Each cloud provider offers built-in logging and monitoring services, such as:

| **Cloud Provider** | **Logging Service**             | **Monitoring Service** |
| ------------------ | ------------------------------- | ---------------------- |
| AWS                | CloudTrail / CloudWatch Logs    | CloudWatch Metrics     |
| Azure              | Activity Logs / Diagnostic Logs | Azure Monitor          |
| Google Cloud       | Audit Logs / Cloud Logging      | Cloud Monitoring       |

Logs become your single source of truth for **attribution**, **compliance**, and **forensics**.

## The Shared Responsibility Model

Every cloud provider follows the **Shared Responsibility Model**, which divides security tasks between the **cloud provider** and the **customer**.

| **Cloud Provider Responsibility**                                                  | **Customer Responsibility**                                     |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Securing the physical infrastructure, hypervisors, networking, and storage layers. | Securing data, identities, configurations, and access policies. |

A common mistake is assuming that “the cloud handles security automatically.”  
The truth is, while providers manage _security of the cloud_, you’re responsible for _security in the cloud._

## Common Misconfigurations

Here are a few of the most common issues security engineers encounter when dealing with cloud foundations:

1. **Publicly Accessible Buckets:** Buckets exposed to the internet due to misconfigured access policies.
2. **Overly Broad IAM Policies:** Wildcard permissions like `*:*` that allow any action on any resource.
3. **Unrestricted Ingress/Egress Rules:** Open ports or full access networks.
4. **Lack of Encryption:** Missing encryption in storage or database services.
5. **Disabled Logging:** Audit trails not turned on or retained for too short a time.

These are exactly the types of problems that cloud security developers automate checks for later.

## Key Takeaways

- Cloud foundations are the **core building blocks** of every service.
- Without understanding compute, storage, networking, and IAM, you can’t design secure systems.
- The **shared responsibility model** is non-negotiable—you own your configurations and data.
- Misconfigurations, not zero-days, are the biggest cause of cloud breaches.
- Observability (logging + monitoring) is your first defensive measure.

## Additional Resources

To help you understand cloud foundations more deeply, here are some of my favorite references:

### Books

| **Book Title**                               | **Author**                | **Link**                         |
| -------------------------------------------- | ------------------------- | -------------------------------- |
| Cloud Security Handbook                      | Eyal Estrin               | [Amazon](https://a.co/d/f7fCK6r) |
| AWS Certified Cloud Practitioner Study Guide | Ben Piper & David Clinton | [Amazon](https://a.co/d/dcV0amr) |
| Google Cloud for Beginners                   | Matteo Baccan             | [Amazon](https://a.co/d/8iYyAZ0) |

### YouTube Videos

#### Cloud Computing Explained in 7 Minutes

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/M988_fsOSWo"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

#### What is the Shared Responsibility Model?

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/S7u1FpKzQ0s"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

### Articles

If you’d like to dive deeper into cloud foundations, check out the following resources:

- https://aws.amazon.com/architecture/well-architected/
- https://cloud.google.com/architecture/framework/foundations
- https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/scaling-best-practices
- https://medium.com/google-cloud/cloud-security-basics-what-every-engineer-should-know-5d31215da7b6

<!-- Links -->

[Damien Burks]: https://damienjburks.com
