---
id: install-config-docker
title: Docker
sidebar_position: 1
---

## Overview

> This installation happens on both of the machines.

According to [Docker's Website], Docker is an open platform for developing, shipping, and running applications. Docker enables you to separate your applications from your infrastructure so you can deliver software quickly. With Docker, you can manage your infrastructure in the same ways you manage your applications. By taking advantage of Docker's methodologies for shipping, testing, and deploying code, you can significantly reduce the delay between writing code and running it in production.

## Docker Installation Steps

1. **Update the Package Index**

   First, update your existing list of packages:

   ```bash
   sudo apt-get update
   ```

2. **Install Required Packages**

   Install the necessary packages to allow apt to use a repository over HTTPS:

   ```bash
   sudo apt-get install \
       ca-certificates \
       curl \
       gnupg \
       lsb-release
   ```

3. **Add Docker’s Official GPG Key**

   Add Docker’s official GPG key to your system:

   ```bash
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   ```

4. **Set Up the Stable Repository**

   Use the following command to set up the stable Docker repository:

   ```bash
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```

5. **Install Docker Engine**

   Update the package index again and install Docker Engine, along with `containerd` and `docker-compose`:

   ```bash
   sudo apt-get update
   sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose
   ```

6. **Verify Docker Installation**

   After the installation, verify that Docker is installed and running correctly:

   ```bash
   sudo docker --version
   ```

   This command should return the Docker version installed.

7. **Start and Enable Docker Service**

   Ensure Docker starts on boot:

   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

8. **Manage Docker as a Non-Root User (Optional)**

   By default, Docker commands need to be run with `sudo`. If you want to run Docker commands as a non-root user, you need to add your user to the `docker` group:

   ```bash
   sudo usermod -aG docker $USER
   sudo usermod -aG docker jenkins
   ```

   After running this command, log out and back in, or run the following command to apply the group membership:

   ```bash
   newgrp docker
   ```

9. **Test Docker Installation**

   Test the Docker installation by running a simple Docker container:

   ```bash
   docker run hello-world
   ```

   This command will download a test image, run it in a container, and print a confirmation message.

10. **(Optional) Install Additional Docker Tools**

You may also want to install Docker Compose if it's not already included:

```bash
sudo apt-get install docker-compose-plugin
```

## Docker Registry Installation Steps

Setting up your own Docker registry locally allows you to host your Docker images privately without relying on a third-party service like Docker Hub. Below are the steps to set up and use a local Docker registry on your machine or server.

1. **Create Necessary Directories and Files**

   Begin by navigating to your home directory and creating directories to store your Docker registry files:

   ```bash
   cd ~
   mkdir -p apps/docker
   cd apps/docker
   touch docker-compose.yml
   ```

1. **Set Up `docker-compose.yml`**

   Next, edit the `docker-compose.yml` file with the following content:

   ```yaml
   version: "3.8"

   services:
     registry:
       image: registry:2.8.2
       ports:
         - "5000:5000"
       environment:
         REGISTRY_HTTP_HEADERS_Access-Control-Allow-Origin: "[http://registry.example.com]"
         REGISTRY_HTTP_HEADERS_Access-Control-Allow-Methods: "[HEAD,GET,OPTIONS,DELETE]"
         REGISTRY_HTTP_HEADERS_Access-Control-Allow-Credentials: "[true]"
         REGISTRY_HTTP_HEADERS_Access-Control-Allow-Headers: "[Authorization,Accept,Cache-Control]"
         REGISTRY_HTTP_HEADERS_Access-Control-Expose-Headers: "[Docker-Content-Digest]"
         REGISTRY_STORAGE_DELETE_ENABLED: "true"
         REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY: /var/lib/registry
       volumes:
         - ./registry-data:/var/lib/registry

     ui:
       image: joxit/docker-registry-ui:latest
       ports:
         - "8082:80"
       environment:
         - SINGLE_REGISTRY=true
         - REGISTRY_TITLE=Docker Registry UI
         - DELETE_IMAGES=true
         - SHOW_CONTENT_DIGEST=true
         - NGINX_PROXY_PASS_URL=http://<your_dsb_hub_ip_address>:5000
         - SHOW_CATALOG_NB_TAGS=true
         - CATALOG_MIN_BRANCHES=1
         - CATALOG_MAX_BRANCHES=1
         - TAGLIST_PAGE_SIZE=100
         - REGISTRY_SECURED=false
         - CATALOG_ELEMENTS_LIMIT=1000
       depends_on:
         - registry

   volumes:
     registry-data:
   ```

1. **Deploy the Docker Registry**

   Use Docker Compose to deploy the Docker registry and the UI:

   ```bash
   docker compose up -d
   ```

1. **Configure Docker Daemon**

   To allow Docker to interact with your insecure registry, you need to update the Docker daemon configuration:

   ```bash
   sudo nano /etc/docker/daemon.json
   ```

   Add the following content:

   ```json
   {
     "insecure-registries": ["<your_dsb_hub_ip_address>:5000"]
   }
   ```

1. **Restart Docker Service**

   After updating the Docker daemon configuration, restart Docker to apply the changes:

   ```bash
   sudo systemctl restart docker
   ```

1. **Configure Additional Docker Nodes (if applicable)**

   If you're working with additional Docker nodes, such as `dsb-hub-01`, you'll need to apply similar settings:

   ```bash
   sudo nano /var/snap/docker/current/config/daemon.json
   ```

   Add the following content:

   ```json
   {
     "log-level": "error",
     "insecure-registries": ["<your_dsb_hub_ip_address>:5000"]
   }
   ```

   Then, restart the Docker service:

   ```bash
   sudo snap restart docker
   ```

## You're Done

You've completed configuring and installing Docker and the Docker Registry on your servers.

<!-- Sources -->

[Docker's Website]: https://docs.docker.com/get-started/overview/
