---
id: install-config-prometheus
title: Prometheus
sidebar_position: 4
---

## Overview

> This installation happens on the `dsb-node-01`.

According to [Prometheus' Website], Prometheus is an open-source systems monitoring and alerting toolkit originally built at SoundCloud. It is designed for reliability and scalability, collecting metrics from configured targets at given intervals, evaluating rule expressions, displaying the results, and triggering alerts if needed. This guide will walk you through the steps to install and configure Prometheus using Docker Compose on your system.

## Prerequisites

1. **Install Docker**

   - Install Docker using Snap:

     ```bash
     sudo snap install docker
     ```

2. **Create Docker Group and Add User to It**

   - Create a Docker group and add your user to it:

     ```bash
     sudo groupadd docker
     sudo usermod -aG docker $USER
     sudo reboot
     ```

## Installation Steps

1. Create a Docker-Compose File for Prometheus

   - Create the necessary directories and Docker Compose file:

     ```bash
     mkdir -p ~/apps/prometheus
     touch ~/apps/prometheus/docker-compose.yml
     ```

2. Copy and Save the Docker-Compose Configuration

   - Use the following configuration in your `docker-compose.yml` file:

     ```yaml
     version: "3.7"

     services:
       prometheus:
         image: prom/prometheus:latest
         container_name: prometheus
         volumes:
           - prometheus_data:/prometheus
           - ./prometheus.yml:/etc/prometheus/prometheus.yml
         ports:
           - "9090:9090"
         restart: always
         network_mode: host

     volumes:
       prometheus_data:
     ```

   - Open the file with nano or your preferred text editor and paste the configuration:

     ```bash
     nano ~/apps/prometheus/docker-compose.yml
     ```

   - Save and close the file.

3. Create a Custom `prometheus.yml` File

   - Create the `prometheus.yml` file in the Prometheus directory:

     ```bash
     touch ~/apps/prometheus/prometheus.yml
     ```

   - Add the following configuration to the `prometheus.yml` file:

     ```yaml
     global:
       scrape_interval: 15s
       evaluation_interval: 15s

     scrape_configs:
       - job_name: "cadvisor"
         static_configs:
           - targets: ["localhost:8080"]

       - job_name: "node_exporter"
         static_configs:
           - targets: ["localhost:9100"]

       - job_name: "jenkins"
         metrics_path: /prometheus/
         static_configs:
           - targets: ["<your_ip_address>:8080"]
     ```

     > **NOTE**: This configuration sets up Prometheus to scrape metrics from cAdvisor, Node Exporter, and Jenkins. Replace `<your_ip_address>` with the actual IP address of your Jenkins server.

4. Run Prometheus with Docker-Compose

   - Navigate to the Prometheus directory and run the container:

     ```bash
     cd ~/apps/prometheus
     docker-compose up -d
     ```

5. Confirm Prometheus is Running

   - Check if Prometheus is up and running by visiting `http://localhost:9090` in your web browser.

     ![Prometheus Dashboard](/img/projects/devsecops-home-lab/installation-and-configuration/prometheus-dashboard.png)

## You're Done

You’ve successfully installed and configured Prometheus on your system. Your Prometheus server is now up and running, ready to scrape metrics from the configured targets and provide insights into your system’s performance and health.

<!-- Sources -->

[Prometheus' Website]: https://prometheus.io/docs/introduction/overview/
