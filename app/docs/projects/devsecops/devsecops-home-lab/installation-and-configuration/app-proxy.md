---
id: config-app-proxy
title: Nginx Reverse Proxy
sidebar_position: 5
---

## Overview

> This installation will happen on the `dsb-node-01`.

In this guide, we will set up a reverse proxy for your application using Nginx. This will allow you to manage incoming traffic more effectively and forward requests to your application running on a different port.

## Installation Steps

1. **Install Nginx**

To begin, you need to install Nginx on your server. This can be done using the following command:

```bash
sudo apt install nginx
```

This command will install Nginx along with any required dependencies.

## Configuration Steps

After installing Nginx, you need to configure it to act as a reverse proxy for your application.

1. **Remove Default Configuration:**

   First, unlink the default Nginx configuration file to avoid any conflicts:

   ```bash
   sudo unlink /etc/nginx/sites-enabled/default
   ```

2. **Create a New Configuration File:**

   Next, create a new configuration file specifically for your reverse proxy setup:

   ```bash
   sudo nano /etc/nginx/sites-available/reverse-proxy
   ```

   In the file that opens, paste the following configuration:

   ```nginx
   server {
       listen 80;
       server_name localhost;

       location / {
           client_max_body_size 1000M;
           proxy_pass http://127.0.0.1:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   This configuration tells Nginx to listen on port 80 (the default HTTP port) and forward all incoming traffic to your application running on `http://127.0.0.1:8080`. It also sets various headers that can be useful for your application's logging and security purposes.

3. **Enable the New Configuration:**

   Activate the new reverse proxy configuration by creating a symbolic link to the `sites-enabled` directory:

   ```bash
   sudo ln -s /etc/nginx/sites-available/reverse-proxy /etc/nginx/sites-enabled/
   ```

4. **Restart Nginx:**

   Finally, restart Nginx to apply the new configuration:

   ```bash
   sudo systemctl restart nginx
   ```

## You're Done

You've setup and configured the Nginx reverse proxy!
