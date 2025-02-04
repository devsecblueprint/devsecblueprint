---
id: install-nexus-grafana-dashboard
title: Installing a Grafana Dashboard for Nexus
sidebar_position: 3
---

## Overview

This installation process is for creating and installing a Nexus dashboard within Grafana for monitoring purposes.

## Prerequisites

1. **Set Up Nexus Repository Manager Monitoring**

   - Ensure Nexus Repository Manager is configured to expose metrics for Prometheus.
   - Edit the `nexus.properties` file, typically located in the `etc/` directory within your Nexus installation:

     ```bash
     sudo nano ./apps/nexus/nexus-data/etc/nexus.properties
     ```

     Add the following property to enable Prometheus metrics:

     ```bash
     nexus.prometheus.enabled=true
     ```

   - Restart Nexus for the changes to take effect:

     ```bash
     docker compose down && docker compose up -d
     ```

2. **Set Up Prometheus**

   - Add Nexus as a target in the Prometheus configuration (`prometheus.yml`) by specifying its host and port:

     ```yaml
     scrape_configs:
       - job_name: "nexus"
         static_configs:
           - targets: ["<nexus_host>:<nexus_port>"]
     ```

     Replace `<nexus_host>` with your Nexus server's hostname or IP address and `<nexus_port>` with the port where Nexus is running (default is 8081).

   - Start or restart Prometheus to begin collecting Nexus metrics.

## Installation Steps

1. **Import the Nexus Dashboard in Grafana**

- To visualize Nexus traffic in Grafana, follow these steps:
  1. Log in to your Grafana instance.
  2. Click on **Create** (the plus icon on the left) and select **Import**.
  3. Paste the dashboard ID: **16459**, or use the URL: [https://grafana.com/grafana/dashboards/16459-infra-nexus/](https://grafana.com/grafana/dashboards/16459-infra-nexus/).
  4. Click **Load**.
  5. Select your Prometheus data source, which scrapes metrics from Nexus.
  6. Click **Import** to add the dashboard to your Grafana instance.

1. **Monitor and Refine**

- After importing, you can monitor Nexus traffic and performance metrics through the dashboard.
- Customize the dashboard as needed by refining queries or adding additional panels.
- Set up alerts in Grafana based on performance thresholds or traffic conditions to get notified proactively.

## You're Done

With this setup, Grafana will now display Nexus traffic and performance data, allowing you to monitor the health and usage of your Nexus Repository Manager effectively.
