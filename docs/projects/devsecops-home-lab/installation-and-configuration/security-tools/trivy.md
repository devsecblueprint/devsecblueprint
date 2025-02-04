---
id: install-config-trivy
title: Trivy
sidebar_position: 4
---

## Overview

> This installation happens on the `dsb-hub`.

According to [Trivy's GitHub Repository], Trivy is a comprehensive, easy-to-use open-source vulnerability scanner. It detects vulnerabilities in OS packages, container images, file systems, and Git repositories. Additionally, Trivy can identify configuration issues and hard-coded secrets, making it an essential tool for DevSecOps practices. This guide will walk you through the steps to install and configure Trivy on your system.

## Installation Steps

1. Configure and Install Package

   - Install required packages and add the Trivy repository key:

     ```bash
     sudo apt-get install wget apt-transport-https gnupg
     wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor | sudo tee /usr/share/keyrings/trivy.gpg > /dev/null
     ```

   - Add the Trivy repository to your sources list:

     ```bash
     echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
     ```

   - Update your package list and install Trivy:

     ```bash
     sudo apt-get update
     sudo apt-get install trivy
     ```

2. Check if Trivy is Installed Successfully

   - Verify that Trivy is installed and running correctly by running the `trivy` command:

     ```bash
     trivy
     ```

   - You should see output similar to the following, which confirms that Trivy is installed and provides usage instructions:

     ```text
     Scanner for vulnerabilities in container images, file systems, and Git repositories, as well as for configuration issues and hard-coded secrets

     Usage:
       trivy [global flags] command [flags] target
       trivy [command]

     Examples:
       # Scan a container image
       $ trivy image python:3.4-alpine

       # Scan a container image from a tar archive
       $ trivy image --input ruby-3.1.tar

       # Scan local filesystem
       $ trivy fs .

       # Run in server mode
       $ trivy server

     Scanning Commands:
       config      Scan config files for misconfigurations
       filesystem  Scan local filesystem
       image       Scan a container image
       kubernetes  [EXPERIMENTAL] Scan kubernetes cluster
       repository  Scan a repository
       rootfs      Scan rootfs
       sbom        Scan SBOM for vulnerabilities and licenses
       vm          [EXPERIMENTAL] Scan a virtual machine image

     Management Commands:
       module      Manage modules
       plugin      Manage plugins
       vex         [EXPERIMENTAL] VEX utilities

     Utility Commands:
       clean       Remove cached files
       completion  Generate the autocompletion script for the specified shell
       convert     Convert Trivy JSON report into a different format
       help        Help about any command
       server      Server mode
       version     Print the version

     Flags:
           --cache-dir string          cache directory (default "/home/damien/.cache/trivy")
       -c, --config string             config path (default "trivy.yaml")
       -d, --debug                     debug mode
       -f, --format string             version format (json)
           --generate-default-config   write the default config to trivy-default.yaml
       -h, --help                      help for trivy
           --insecure                  allow insecure server connections
       -q, --quiet                     suppress progress bar and log output
           --timeout duration          timeout (default 5m0s)
       -v, --version                   show version
     ```

## You're Done

Trivy is now installed and ready to be used for scanning vulnerabilities in container images, file systems, and more. With Trivy, you can ensure that your applications are secure and free from known vulnerabilities before deploying them to production.

<!-- Sources -->

[Trivy's GitHub Repository]: https://github.com/aquasecurity/trivy
