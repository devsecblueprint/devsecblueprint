---
id: implementing-cloud-devsecops-pipelines
title: Building Cloud DevSecOps Pipelines (In Theory)
description: Building DevSecOps Pipelines In Theory
sidebar_position: 8
---

## Introduction

I want you to always remember: A well-designed DevSecOps pipeline follows the Secure Software Development Life Cycle (SSDLC). Rather than treating security as a separate or final step (SDLC), a DevSecOps pipeline embeds security into every aspect of development, testing, and deployment.

In this section, I'll outline the critical stages a DevSecOps pipeline *should* have, which will for just application deployment cases.

## CI/CD Platforms You Should Look Into

Now, there are plenty of platforms that you could use to manage your code and build pipelines to deploy your applications. However, these are the three that I would recommend you look into and use:

| **Tool Name**                                       | **Description**                                                                                     | **Link**                            |
|-----------------------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------|
| **[Jenkins](https://www.jenkins.io/)**              | A widely used open-source automation server for building, testing, and deploying code.               | [jenkins.io](https://www.jenkins.io/) |
| **[GitHub Actions](https://github.com/features/actions)** | A workflow automation platform integrated with GitHub repositories that supports CI/CD pipelines.     | [GitHub Actions](https://github.com/features/actions) |
| **[GitLab Runners](https://docs.gitlab.com/runner/)** | A tool that runs the jobs specified in GitLab CI/CD pipelines, supporting various environments.       | [gitlab.com](https://docs.gitlab.com/runner/) |
| **[Gitea Actions](https://gitea.com/gitea/actions)** | An open-source CI/CD platform built into Gitea for automating workflows and running pipelines.        | [gitea.com](https://gitea.com/gitea/actions) |

## Stages of a DevSecOps Pipeline

So, I've decided to use Jenkins compared to any other solution, because it's the one that I'm most familiar with. I personally think Jenkinsfile are easiest to read compared to GitLab Runners and GitHub/Gitea Actions files. Therefore, I highly advise you to go through this documentation how to write a Jenkinsfile: [Using A Jenkinsfile](https://www.jenkins.io/doc/book/pipeline/jenkinsfile/)

Usually, a **Jenkins pipeline** for DevSecOps typically involves the a variety of stages to build, test, scan, and deploy your application. The outline listed below is sudo code, with an small explanation in each stage to follow:

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                // Checking out code from Git repository (like GitHub, Gitea, GitLab, etc.)
                checkout scm
            }
        }

        stage('Build') {
            steps {
                // Example: Building the application
                // Could also include containerizing the application as well
            }
        }

        stage('Run Application Tests') {
            // Example: Running unit tests, acceptance tests, integration tests
            // It's usually best to do these in parallel to save time on builds :)
            parallel {
                stage('Unit Test'){
                    steps {
                    }
                }
                stage('Acceptance Test'){
                    steps {
                    }
                }
                stage('Integration Test'){
                    steps {
                    }
                }
            }
        }

        stage('Security Scanning') {
            parallel {
                stage('SAST Scanning'){
                    steps {
                        // This stage will run SAST Scanning tests against your code base. 
                    }
                }
                stage('DAST Scanning'){
                    steps {
                        // This stage will run DAST scans against your running application. 
                        // You'll want to ensure you run your app locally and run the solution against it.
                    }
                }
                stage('Container Scanning'){
                    steps {
                        // This stage would be dependant whether or not you're deploying
                        // a container to Kubernetes or Docker Swarm (or just plain old Docker).
                    }
                }
                stage('Dependency Scanning') {
                    steps {
                        // This stage will check your dependencies of you applicatino and 
                        // log any vulnerabilities. 
                    }
                }       
            }
        }

        stage('Deploy') {
            steps {
                // Lastly, we will deploy your application. This could to any 
                // environment you want.
            }
        }
    }
    
    post {
        always {
            // Example: Archiving reports and test results
            archiveArtifacts artifacts: '**/target/*.jar', allowEmptyArchive: true
            junit '**/target/test-*.xml'

            // Best practice - clean up the workspaces after it's all said an done. 
            // Don't be that guy...
            cleanWs()
        }
    }
}
```

## Security Tools To Integrate Into CI/CD Pipelines

| **Tool Name**                                       | **Description**                                                                                     | **Category**           |
|-----------------------------------------------------|-----------------------------------------------------------------------------------------------------|------------------------|
| [Checkov](https://github.com/bridgecrewio/checkov)  | A static analysis tool for detecting misconfigurations in Infrastructure as Code (Terraform, Kubernetes, etc.). | Cloud Security         |
| [Terrascan](https://github.com/accurics/terrascan)  | A static analysis tool for ensuring security and compliance of cloud infrastructure (Terraform, Kubernetes). | Cloud Security         |
| [TFSec](https://github.com/aquasecurity/tfsec)      | A static analysis security scanner for Terraform configurations, focusing on cloud security.          | Cloud Security         |
| [Falco](https://github.com/falcosecurity/falco)     | A runtime security tool for detecting anomalous behavior in containers and cloud-native environments. | Container & Cloud Security |
| [Cloud Custodian](https://github.com/cloud-custodian/cloud-custodian) | A rules engine for enforcing security, compliance, and governance policies in cloud environments.     | Cloud Security          |
| [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) | A policy engine that enforces security and compliance policies for Kubernetes, microservices, and cloud infrastructure. | Cloud Security          |
