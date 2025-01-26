---
id: install-config-node-exporter
title: Node Exporter
sidebar_position: 2
---

## Overview

> This installation happens on the `dsb-node-01`.

According to [Prometheus' Website], Node Exporter is an essential tool for monitoring the hardware and OS-level metrics of your Linux systems. It is part of the Prometheus ecosystem and is widely used to gather metrics such as CPU usage, memory usage, disk I/O, and more.

## Installation Steps

1. Create Necessary Directories

First, navigate to your `apps` directory and create a new directory for Node Exporter:

```bash
cd ~/apps
mkdir node-exporter
```

1. Create Docker Compose File

Navigate to the `node-exporter` directory and create a `docker-compose.yml` file:

```bash
cd ~/apps/node-exporter
touch docker-compose.yml
```

1. Configure Docker Compose File

Edit the `docker-compose.yml` file and add the following configuration:

```yaml
version: '3.8'

services:
  node-exporter:
    image: quay.io/prometheus/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    network_mode: "host"
    pid: "host"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points="^/(sys|proc|dev|host|etc)($$|/)"'
    network_mode: host
```

1. Deploy Node Exporter

Finally, use Docker Compose to deploy Node Exporter:

```bash
docker-compose up -d
```

## You're Done

<!-- Sources -->

[Prometheus' Website]: https://prometheus.io/docs/guides/node-exporter/
