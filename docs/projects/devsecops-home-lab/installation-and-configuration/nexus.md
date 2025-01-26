---
id: install-config-nexus
title: Nexus
sidebar_position: 4
---

## Overview

> This installation happens on the `dsb-hub`.

[Nexus Repository Manager](https://www.sonatype.com/products/sonatype-nexus-oss) is a tool for managing components and build artifacts across various formats like Docker, Maven, and npm. We are using Docker Compose to install Nexus to avoid conflicts with SonarQube's JDK requirements. Nexus will be used to manage Docker images, allowing us to proxy images from Docker Hub, cache them locally, and securely manage retrieval.

## Installation Steps

1. **Create a new directory for Nexus:**

   ```bash
   mkdir -p apps/nexus/nexus-data
   sudo chown -R 200 apps/nexus/nexus-data
   ```

2. **Create the Docker Compose YAML file:**

   ```bash
   cd apps/nexus
   touch docker-compose.yml
   ```

3. **Add the following content to the `docker-compose.yml`:**

   ```yaml
   version: "3"
   services:
     nexus:
       image: sonatype/nexus3
       restart: always
       volumes:
         - "./nexus-data:/nexus-data"
       ports:
         - "8081:8081"
         - "8082:8082"
         - "8085:8085"
   volumes:
     nexus-data:
       driver: local
   ```

4. **Run the application:**

   ```bash
   docker compose up -d
   ```

5. **Confirm that the application is up and running by visiting:**

   ```text
   http://your-ip-address:8081
   ```

![Nexus is live](/img/projects/devsecops-home-lab/installation-and-configuration/nexus-initial-view.png)

## Configuration Steps

1. **Click the "Sign In" button and locate the admin password:**

   ```bash
   cat nexus-data/admin.password
   ```

   ![Admin Password](/img/projects/devsecops-home-lab/installation-and-configuration/nexus-found-admin-pw.png)

2. **Use the password to log in and complete the initial setup:**

   - Change your password.
   - Enable anonymous access if desired.

   ![Login](/img/projects/devsecops-home-lab/installation-and-configuration/nexus-change-admin-pw.png)

3. **As admin, navigate to the UI and create a new repository:**
   ![Create Repository](/img/projects/devsecops-home-lab/installation-and-configuration/nexus-create-repository.png)

4. **For the new repository, choose "Docker proxy" and input the following information:**

   1. Name: `docker-proxy`
   2. Remote Storage Proxy URL: `https://registry.hub.docker.com`
   3. Docker Index: `Docker Hub`
   4. Enable anonymous pulls.
   5. Set HTTP to `8082`.

5. **Create a local user with the username `nx-anonymous` and complete the setup:**

   ![Create User](/img/projects/devsecops-home-lab/installation-and-configuration/nexus-create-user.png)

## You're Done

You've successfully set up your Nexus server.
