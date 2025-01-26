---
id: install-config-gitea
title: Gitea
sidebar_position: 2
---

## Overview

> This installation happens on the `dsb-hub`.

According to [Gitea]'s documentation, Gitea is a painless self-hosted all-in-one software development service, including Git hosting, code review, team collaboration, package registry and CI/CD. It's open source under MIT license. It is designed to be lightweight, easy to use, and highly customizable, making it an ideal choice for both small teams and large organizations.

## Prerequisites

1. **Install PostgreSQL:**

   - Run the following command to install PostgreSQL and its contrib package:

     ```bash
     sudo apt install postgresql postgresql-contrib
     ```

   - Switch to the PostgreSQL user:

     ```bash
     sudo -i -u postgres
     ```

   - Update the PostgreSQL configuration files:

     ```bash
     sudo nano /etc/postgresql/16/main/postgresql.conf
     ```

   - Scroll down and uncomment the `listen_addresses` setting, then set it to `localhost`:

     ```conf
     listen_addresses = 'localhost'
     ```

   - Scroll down and uncomment the `password_encryption` setting, then set it to `scram-sha-256`:

     ```conf
     password_encryption = scram-sha-256
     ```

2. **Log into PostgreSQL:**

   - Log into the PostgreSQL command line as the `postgres` user:

     ```bash
     psql
     ```

3. **Configure the Database:**

   - Create a new role (user) for Gitea with a secure password and a new database owned by that role:

     ```sql
     CREATE ROLE gitea WITH LOGIN PASSWORD 'your_password';
     CREATE DATABASE giteadb WITH OWNER gitea TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8';
     ```

   - Update the `pg_hba.conf` file to allow the `gitea` user to connect to the `giteadb` database using `scram-sha-256`:

     ```bash
     sudo nano /etc/postgresql/16/main/pg_hba.conf
     ```

     Add the following line:

     ```conf
     local    giteadb    gitea    scram-sha-256
     ```

4. **Test Database Connection:**

   - Restart the PostgreSQL service and test the connection to the Gitea database:

     ```bash
     sudo systemctl restart postgresql.service
     psql -U gitea -d giteadb
     ```

5. **Install Nginx:**

   - Install Nginx using the following command:

     ```bash
     sudo apt install nginx
     ```

6. **Configure Nginx:**

   - Unlink the default configuration file:

     ```bash
     sudo unlink /etc/nginx/sites-enabled/default
     ```

   - Create a new configuration file for the reverse proxy:

     ```bash
     sudo nano /etc/nginx/sites-available/reverse-proxy
     ```

   - Copy the following configuration into the file, then save and close it:

     ```nginx
     server {
         listen 80;
         server_name localhost;

         location / {
             proxy_pass http://127.0.0.1:3000;
             proxy_set_header Host $host;
             proxy_set_header X-Real-IP $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Forwarded-Proto $scheme;
         }
     }
     ```

   - Activate the new proxy configuration and restart Nginx:

     ```bash
     sudo ln -s /etc/nginx/sites-available/reverse-proxy /etc/nginx/sites-enabled/
     sudo systemctl restart nginx
     ```

## Installation Steps

1. **Install Gitea:**

   - Install Gitea using Snap:

     ```bash
     sudo snap install gitea
     ```

   - Start the Gitea service:

     ```bash
     sudo snap start gitea
     ```

   - Configure web hooks:

   ```bash
   sudo nano /var/snap/gitea/common/conf/app.ini

   # Add this inside of the file
   [webhook]
   ALLOWED_HOST_LIST = localhost, 127.0.0.1
   ```

## Configuration Steps

1. **Configure Gitea:**

   - Open a web browser and navigate to your server's IP address or domain name.
   - Follow the on-screen instructions to configure Gitea, entering your previously created PostgreSQL database credentials when prompted.
     ![Gitea Setup Screenshot](/img/projects/devsecops-home-lab/installation-and-configuration/gitea-init-config.png)

1. **Create an Account:**

   - Create an admin account to manage your Gitea instance.
     ![Create Account Screenshot](/img/projects/devsecops-home-lab/installation-and-configuration/gitea-create-account.png)

## You're Done

Gitea is now successfully installed and configured on your server. Feel free to log in and take a look around.
![Success Screenshot](/img/projects/devsecops-home-lab/installation-and-configuration/gitea-success-account-creation.png)

<!-- Sources -->

[Gitea]: https://about.gitea.com/products/gitea/
