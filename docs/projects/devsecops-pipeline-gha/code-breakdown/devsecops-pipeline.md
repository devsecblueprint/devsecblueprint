---
id: devsecops-gha-code
title: DevSecOps GitHub Actions Code - Explained
sidebar_position: 1
---

## Overview

Alright, now that you’ve seen how the pipeline flows and what tools we’re using, let’s take a step back and walk through how this thing is actually put together. This section gives you a breakdown of each workflow file so you know what’s going on under the hood, and how everything ties together to give us a secure, automated CI/CD setup using GitHub Actions.

## Code Overview

All of the workflow logic lives inside the `.github/workflows` folder. Each file in this directory is responsible for a specific part of the pipeline—building images, running tests, scanning for vulnerabilities, and pushing to registries. The real magic happens in the `main.yml` and `pr.yml` files, which orchestrate the order of operations depending on whether code is being pushed to main or coming in through a pull request.

### Main Workflow

This is the primary CI/CD pipeline that runs on every push to the `main` branch or when manually triggered. It chains together the full DevSecOps flow—building the image, checking code quality, running tests and security scans, and pushing the Docker image.

- **File**: `main.yml`
  - Triggers on push to `main` or manual invocation
  - Sequentially calls `build-image`, `lint-format`, `unit-sec-test`, and `push-docker-image`

### PR Workflow

This workflow runs when a pull request is opened, edited, or synchronized. It runs a subset of the pipeline to validate incoming changes before merging.

- **File**: `pr.yml`
  - Triggers on pull request events
  - Executes `build-image`, followed by `lint-format`, and then `unit-sec-test`

### Build Image Workflow

This workflow builds the Docker image from the current application source. It is invoked by both the main and PR workflows as an early validation step.

- **File**: `build-image.yml`
  - Builds a Docker image using the application code
  - Tags the image with the commit SHA

### Linting and Formatting Workflow

This workflow ensures Python code quality and consistency by running `pylint` and `black`. It enforces coding standards before proceeding to tests or deployment.

- **File**: `lint-format.yml`
  - Runs `pylint` on the codebase
  - Runs `black` to check for proper code formatting

### Unit & Security Test Workflow

This workflow runs unit tests and performs two types of container security scans—Trivy for static analysis and OWASP ZAP for dynamic application testing.

- **File**: `unit-sec-test.yml`
  - **Unit tests**: Executes pytest after installing dependencies
  - **Trivy scans**: Detects high/critical vulnerabilities in the built Docker image
  - **OWASP ZAP**: Runs a DAST scan against the running container

### Push Docker Image Workflow

This workflow builds and tags a Docker image, then pushes it to GitHub Container Registry (GHCR). It's triggered after all validations have passed.

- **File**: `push-docker-image.yml`
  - Builds the image
  - Tags it with the commit SHA, `latest`, and `testing`
  - Pushes to GHCR

### Push Image to Docker Hub Workflow

This optional workflow pushes an image to Docker Hub instead of GHCR. It is intended for alternate registry support and includes login and build steps.

- **File**: `push-image.yml`
  - Authenticates with Docker Hub
  - Uses `buildx` and `build-push-action` to build and push `user/app:latest`

Once you understand the purpose and layout of these Terraform configs, you'll have a solid grasp on how the DevSecOps pipeline works from spinning up infrastructure to running secure, automated CI/CD workflows.
