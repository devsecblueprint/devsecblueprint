---
id: aws-event-driven-s3-public-access-detective-control
title: Event-Driven Detective Control (AWS)
description: Detect publicly accessible S3 buckets using AWS-native, event-driven telemetry.
sidebar_position: 1
---

Author: [Kosisochukwu Akaeze], [Damien Burks]

## Overview

Publicly accessible object storage remains one of the most common... and **most damaging** issue within the realm of cloud security.

This project demonstrates how to build a **custom, event-driven detective control** that detects when an **Amazon S3 bucket becomes publicly accessible** and sends an **actionable notification** in near real time.

Rather than relying on periodic scans or managed security products as the primary signal, this control uses **AWS-native telemetry** and **custom detection logic** to evaluate configuration changes *as they happen*.

The result is a deterministic, auditable control that can be deployed consistently across environments and scaled as part of a broader cloud security program.

## Misconfiguration Definition

An S3 bucket is considered **public** if **any** of the following conditions are met:

- The bucket policy allows public access (e.g., `Principal: "*"`)
- The bucket ACL grants public access
- Public Access Block is disabled or removed such that public access is possible

This definition is intentionally explicit to avoid ambiguity and false positives.

## Architecture Overview and Debrief

This control follows a simple, event-driven architecture:

![Architecture Diagram](/img/projects/cloud_security_development/aws_detective_control/architecture.drawio.svg)

Configuration changes to S3 buckets are captured via CloudTrail, evaluated in real time by EventBridge, and processed by a Lambda function that determines whether the bucket is publicly accessible. If a violation is detected, a structured notification is published to SNS.

This approach avoids polling, scheduled scans, or dependency on aggregated security findings.

## Components Breakdown

### 1. CloudTrail

CloudTrail provides the authoritative audit log for S3 configuration changes. This control relies on CloudTrail events as the **source of truth** for detecting when bucket access settings are modified.

### 2. EventBridge

EventBridge evaluates CloudTrail events in near real time and filters for relevant API calls related to S3 access control changes.

**Triggering events include:**

- `PutBucketPolicy`
- `PutBucketAcl`
- `DeletePublicAccessBlock`
- `PutPublicAccessBlock`

Only relevant events are forwarded to the detection logic, reducing noise and unnecessary execution.

### 3. Lambda (Detection Logic)

The Lambda function performs the core detection logic:

1. Identifies the affected S3 bucket from the CloudTrail event
2. Retrieves the bucket’s current configuration (policy, ACL, Public Access Block)
3. Determines whether the bucket is publicly accessible
4. Generates a structured finding if public access is detected
5. Publishes a notification to SNS

Detection is based on **current state evaluation**, not assumptions about the triggering event alone.

### 4. SNS (Notification)

When a public bucket is detected, an SNS notification is sent with actionable context.

**Notification content includes:**

- Bucket name
- Account ID
- Region
- Actor (IAM user or role)
- Event name (optional)
- Event timestamp (optional)

This ensures alerts are immediately useful to security and platform teams.

## Infrastructure as Code

This control is deployed entirely using **Infrastructure as Code**, ensuring reproducibility and consistency.

**Supported tooling:**

- Terraform (preferred)
- CloudFormation
- AWS CDK

**Required resources:**

- EventBridge rule
- Lambda function and IAM role
- SNS topic with at least one subscription (email is acceptable)

## Validation and Testing

Successful implementation must demonstrate:

1. A private S3 bucket (baseline state)
2. Introduction of a public configuration
3. Successful event detection
4. SNS notification delivery
5. Logged, structured finding for auditability

## Why This Control Matters

This project serves as a **reference implementation** for building event-driven detective controls in AWS.

It demonstrates how to:

- Detect misconfigurations **as they occur**
- Avoid reliance on periodic scans
- Build controls that are portable and auditable
- Treat security controls as first-class infrastructure

This pattern is intentionally reusable and will be extended across future DevSec Blueprint controls.

## What You’ll Learn

By studying or deploying this control, you’ll gain experience with:

- Designing event-driven security architectures
- Defining misconfigurations precisely
- Writing custom detection logic using AWS-native telemetry
- Building scalable, automated detective controls
- Applying Infrastructure as Code to security engineering

<!-- Links -->
[Kosisochukwu Akaeze]: https://www.linkedin.com/in/kosisochukwu-akaeze-a4853a1a7/
[Damien Burks]: https://damienjburks.com
