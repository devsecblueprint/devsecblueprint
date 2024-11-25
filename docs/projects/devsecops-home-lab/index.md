---
id: devsecops-home-lab
title: DevSecOps Home Lab
description: Build a DevSecOps Home Lab based on what I have done.
sidebar_position: 1
---

Author: [Damien Burks]

<iframe
  width="100%"
  height="500"
  src="https://www.youtube.com/embed/3612XpqUTfc?si=3612XpqUTfc"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>

## Overview

So you decided that you want to go down the route of building your own home lab? Well, hell... welcome! This is the first project where I'm going to show you how to setup your own home lab from scratch! This will include you going in and setting up and configuring databases, installing packages, and a lot of things that System Administrators would do.

> _According to [The Linux Handbook], a homelab is the name given to a server (or multiple server setup) that resides locally in your home and where you host several applications and virtualized systems for testing and developing or for home and functional usage._

To be more formal (in a sense), we're going to build a comprehensive DevSecOps Home Lab that simulates a real-world environment for testing, learning, and enhancing your DevSecOps skills. This lab is designed to give you hands-on experience with a variety of tools and technologies commonly used in the DevSecOps ecosystem.

## Don't have servers at home?

This is totally okay! There are two options that I'd recommend then:

1. Check out this video to learn how I went out to buy my systems for a very low price:
2. If you have experience with building things out in the cloud, you can replicate this exact architecture, although it may be a little different when connecting to your machines and vice versa.
3. Use tools like VirtualBox to create VM's locally. This comes with a bit of a learning curve.

## Architecture Overview and Debrief

My home lab consists of two servers running Ubuntu 24.04 LTS. To avoid any compatibility issues, you want to ensure that you are using this EXACT version.

![Architecture Diagram](/img/projects/devsecops-home-lab/architecture.drawio.svg)

The architecture is divided across two servers:

- `dsb-node-01`: This server is responsible for hosting essential infrastructure services, including a reverse proxy, containerization engine, and monitoring stack.
- `dsb-hub`: Dedicated to handling the DevSecOps toolchain, this server focuses on source code management, security scanning, continuous integration, and continuous delivery (CI/CD).

### Components Breakdown

#### 1. **Server: dsb-node-01**

This server lays the foundation for containerized environments and monitoring:

- **NGINX**: NGINX acts as a web server and reverse proxy, ensuring that incoming traffic is efficiently routed to the appropriate service.
- **Docker**: Docker provides containerization capabilities, allowing applications and services to run in isolated environments.
- **Containerized Web Application**: This could be anything (Python API, Java App, etc), as long as it is in a Docker container.
- **Prometheus**: Prometheus is responsible for collecting and monitoring system and application metrics, serving as the central component for alerting and monitoring.
- **Grafana**: Integrated with Prometheus, Grafana offers visual dashboards that make it easy to observe metrics and logs, giving you insights into system health and performance.

#### 2. **Server: dsb-hub**

This server hosts the critical components of the DevSecOps toolchain, enabling secure and automated workflows:

- **NGINX**: Similar to `dsb-node-01`, NGINX handles traffic management and routing for the services hosted on this server.
- **Gitea**: A lightweight, self-hosted Git service, Gitea provides version control capabilities, allowing you to manage your source code repositories.
- **SonarQube**: SonarQube is utilized for continuous code quality and security checks, detecting issues such as bugs, code smells, and vulnerabilities in the codebase.
- **Jenkins**: As a cornerstone of CI/CD, Jenkins automates the process of building, testing, and deploying applications, ensuring a streamlined development pipeline.
- **Trivy**: Trivy performs vulnerability scanning for Docker images, ensuring that containerized applications are free from known security risks.
- **Nexus**: Nexus is used for managing dependencies, artifacts, and binaries. It serves as a repository manager that integrates with Jenkins, allowing you to maintain control over project artifacts and their versions.
- **Docker**: Docker on this server continues to play a key role in containerizing applications and services, maintaining the consistency of deployment across the environment.

## What You'll Learn

By completing this project fully, you will gain hands-on experience (practical) on setting up a DevSecOps environment, such as:

- Containerization: Deploying and managing applications in Docker containers.
- Monitoring and Logging: Using Prometheus to monitor application health and performance.
- Security Scanning: Implementing security tools like Trivy and SonarQube to identify vulnerabilities and maintain code quality.
- Web Traffic Management: Configuring Nginx as a reverse proxy to efficiently route and secure web traffic.

<!-- Links -->

[Damien Burks]: https://www.youtube.com/@damienjburks
[The Linux Handbook]: https://linuxhandbook.com/homelab/
