---
id: application-code
title: Application Code - Explained
sidebar_position: 2
---

## Overview

This section provides a detailed explanation of the application's codebase. The project is a simple Python-based FastAPI application that can be run locally or containerized for deployment. Its primary purpose is to demonstrate a secure and automated DevSecOps pipeline while highlighting potential vulnerabilities for testing purposes.

## Defining GCP-FastAPI

The project sets up a FastAPI application inside a Docker container. It uses the official Python runtime and includes all the necessary configurations to deploy the app efficiently. Upon starting, the container automatically runs the FastAPI app, exposing it on port 80.

The goal of this project is to push it through a DevSecOps pipeline, as it intentionally contains some vulnerabilities. For more details, you can review the code in the [main.py](https://github.com/devsecblueprint/gcp-fastapi/blob/main/main.py) file.

### Requirements

- **Docker**: For containerizing and running the application.
- **Python 3.12+**: The latest stable version ensures compatibility with modern features.
- **FastAPI**: Framework for building the API.
- **Uvicorn**: ASGI server for running the application.

### Features

- **Dockerized Application**: Simplifies deployment using containers.
- **Python 3.12.5 Runtime**: Ensures compatibility with the latest features and security patches.
- **Optimized Dependency Installation**: Leverages `requirements.txt` for streamlined package management.

### Project Structure

```bash
gcp-fastapi/
├── Dockerfile         # Configuration for the Docker container
├── requirements.txt   # Python dependencies
├── main.py            # Entry point for the FastAPI app (contains sample vulnerabilities)
└── ...
```

### Setup and Installation

#### 1. Clone the Repository

Clone the project repository using the following command:

```bash
git clone https://github.com/your-username/gcp-fastapi.git
cd gcp-fastapi
```

#### 2. Build the Docker Image

Run the following command in the project root to build the Docker image:

```bash
docker build -t gcp-fastapi .
```

#### 3. Run the Docker Container

After building the image, start the container:

```bash
docker run -d -p 80:80 gcp-fastapi
```

This command will start the FastAPI app on port 80 of your localhost.

#### 4. Access the Application

Once the container is running, you can access the application in your browser:

```text
http://localhost:80
```

### Dependencies

The application relies on the following Python packages, specified in the `requirements.txt` file:

- `fastapi`: The main framework for building APIs.
- `uvicorn`: The ASGI server for running the application.

To install these dependencies locally, run:

```bash
pip install -r requirements.txt
```

### Notes

- The default entry point for the FastAPI application is `main.py`, where the application instance is named `app`. If your setup differs, update the `CMD` directive in the Dockerfile accordingly.
- By default, the container exposes the application on port 80. To use a different port, modify the `EXPOSE` and `CMD` directives in the Dockerfile as needed.

This straightforward setup ensures you can run, test, and deploy the FastAPI application with minimal effort while integrating it into a secure DevSecOps pipeline.
