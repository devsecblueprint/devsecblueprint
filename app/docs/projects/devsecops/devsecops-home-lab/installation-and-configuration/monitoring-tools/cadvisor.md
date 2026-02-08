---
id: install-config-cadvisor
title: cAdvisor
sidebar_position: 4
---

## Overview

> This installation happens on the `dsb-node-01`.

According to [cAdvisor's GitHub Repository], cAdvisor (Container Advisor) is an open-source tool from Google designed to provide insights into resource usage and performance characteristics of running containers. It collects, aggregates, processes, and exports information about running containers, making it a valuable tool for monitoring containerized environments. This guide will walk you through the steps to install and configure cAdvisor using Docker Compose on your system.

## Installation Steps

1. **Create Necessary Directories**

   First, navigate to your `apps` directory and create a new directory for cAdvisor:

   ```bash
   cd apps
   mkdir cadvisor
   ```

   Next, create the Docker library directory if it does not already exist:

   ```bash
   cd /var/lib
   mkdir docker
   chown -R root:root docker
   ```

2. **Create Docker Compose File**

   Navigate back to the `cadvisor` directory and create a `docker-compose.yml` file:

   ```bash
   cd ~/apps/cadvisor
   touch docker-compose.yml
   ```

3. **Configure Docker Compose File**

   Edit the `docker-compose.yml` file and add the following configuration:

   ```yaml
   version: "3.8"

   services:
     cadvisor:
       image: gcr.io/cadvisor/cadvisor
       container_name: cadvisor
       privileged: true
       restart: unless-stopped
       ports:
         - "8080:8080"
       volumes:
         - /:/rootfs:ro
         - /var/run:/var/run:ro
         - /sys:/sys:ro
       network_mode: host
   ```

4. **Deploy cAdvisor**

   Finally, use Docker Compose to deploy cAdvisor:

   ```bash
   docker-compose up -d
   ```

## You're Done

Congratulations! You have successfully installed and configured cAdvisor. The cAdvisor service is now running and can be accessed via port 8080 on your host machine. This setup will allow you to monitor and visualize the performance metrics of your running containers in real-time.

<!-- Sources -->

[cAdvisor's GitHub Repository]: https://github.com/google/cadvisor
