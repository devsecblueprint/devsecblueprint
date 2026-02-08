---
id: testing-detective-control
title: Testing the Detective Control
sidebar_position: 2
---

## Overview

With the detective control deployed, the next step is to validate that it works as expected.

This section walks through intentionally introducing a known misconfiguration, a publicly accessible S3 bucket, and observing how the control responds in real time using CloudTrail and EventBridge.

By the end of this test, you should have high confidence that:

- S3 configuration changes are being captured
- The detection logic is executing correctly
- Notifications are being delivered with actionable context

## Triggering the Detection

Follow the steps below to create a public S3 bucket and trigger the control.

1. Log in to the **AWS Management Console** and navigate to the **Amazon S3 dashboard**.

2. Click **Create bucket**.

3. Provide a **unique bucket name**.

   :::note
   A recommended naming pattern is to include your **AWS account ID** and **region** to avoid collisions and make the bucket easier to identify in alerts.
   :::

4. Scroll to the **Block Public Access settings for this bucket** section and:
   - Uncheck **Block all public access**
   - Check the acknowledgment box confirming you understand the risk

   ![Disable Public Access Block](/img/projects/cloud_security_development/aws_detective_control/image-4.png)

5. Scroll to the bottom of the page and click **Create bucket**.

## Observing the Results

Because this control is **event-driven and real time**, detection occurs immediately after the configuration change is recorded by CloudTrail and delivered through EventBridge.

Within a few seconds, you should receive an **SNS notification** indicating that a public S3 bucket was detected.

![SNS Alert Email](/img/projects/cloud_security_development/aws_detective_control/image-5.png)

The notification includes:

- Bucket name
- AWS account ID
- Region
- Actor (IAM user or role)
- Triggering event
- Timestamp

## Validation Checklist

A successful test confirms the following:

- ✅ CloudTrail captured the S3 configuration change
- ✅ EventBridge routed the event correctly
- ✅ Lambda evaluated the bucket’s current configuration
- ✅ Public exposure was detected
- ✅ SNS notification was delivered

If all of the above occurred, the detective control is functioning correctly.

## Failure Modes

If you **do not** receive an alert or expected behavior differs, review the scenarios below.

### No SNS Email Received

- Confirm the **SNS subscription was approved** via the confirmation email.
- Verify the email address configured in Terraform is correct.
- Check that the SNS topic ARN is correctly injected into the Lambda environment variables.

### Lambda Was Not Invoked

- Verify the **EventBridge rule** exists and is enabled.
- Confirm the rule is matching the correct **CloudTrail event names**:
  - `PutBucketPolicy`
  - `PutBucketAcl`
  - `PutPublicAccessBlock`
  - `DeletePublicAccessBlock`
- Check EventBridge metrics for failed or filtered events.

### Lambda Invocation Errors

- Review **CloudWatch Logs** for the Lambda function.
- Confirm required IAM permissions are attached:
  - `s3:GetPublicAccessBlock`
  - `s3:GetBucketPolicyStatus`
  - `s3:GetBucketAcl`
  - `sns:Publish`
- If using third-party libraries, ensure dependencies are properly packaged or provided via a Lambda layer.

### Bucket Was Not Flagged as Public

- Verify that the bucket configuration actually results in public exposure.
- Confirm the control evaluates **current state**, not just the triggering event.
- Check that Public Access Block, policy, or ACL changes are not being reverted by another control.

## Considerations

- This test intentionally introduces a **real misconfiguration**. Remember to clean up the bucket after validation.
- Detection is based on **current-state evaluation**, not assumptions about the triggering event alone.
- The same pattern applies to policy changes, ACL changes, and Public Access Block modifications.

Once validated, this control can be treated as a reliable, real-time signal for S3 public access exposure.
