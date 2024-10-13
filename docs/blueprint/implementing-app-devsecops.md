---
id: implementing-app-devsecops-pipelines
title: Building Application DevSecOps Pipelines (In Theory)
description: Building DevSecOps Pipelines In Theory
sidebar_position: 5
---

Author: [Damien Burks]

So now that you've learned a lot about DevSecOps, lets put the theory into practice (somewhat). This'll help you visualize what a pipeline "should" look like in theory, so that you can go off and build your own.

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

Usually, a **Jenkins pipeline** for DevSecOps typically involves the a variety of stages to build, test, scan, and deploy your application. The outline listed below is sudo code, with an explanation to follow:

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                // Checking out code from Git repository
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

                    }
                }
                stage('DAST Scanning'){
                    steps {
                        // 
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

I've compiled a list of tools that are commonly used in DevSecOps pipelines. These tools cover everything from SAST and DAST to container and cloud security.

| **Tool Name**                                       | **Description**                                                                                     | **Category**           |
|-----------------------------------------------------|-----------------------------------------------------------------------------------------------------|------------------------|
| [SonarQube](https://www.sonarqube.org/)             | One of the most popular SAST tools, SonarQube analyzes code quality and security across multiple languages. | SAST                   |
| [Semgrep](https://semgrep.dev/)                    | A fast and flexible static analysis tool for identifying security vulnerabilities in source code.    | SAST                   |
| [Bandit](https://bandit.readthedocs.io/en/latest/)  | Popular Python-focused SAST tool for identifying security issues in Python codebases.                | SAST                   |
| [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/) | A widely-used tool that checks for known vulnerabilities in project dependencies.                    | SAST                   |
| [OWASP ZAP](https://owasp.org/www-project-zap/)     | One of the most popular DAST tools, ZAP identifies security vulnerabilities in running web applications. | DAST                   |
| [Arachni](https://www.arachni-scanner.com/)         | A modular DAST scanner that is widely used for testing modern web applications.                      | DAST                   |
| [Nikto](https://github.com/sullo/nikto)             | A highly popular DAST tool that scans web servers for vulnerabilities and misconfigurations.         | DAST                   |
| [Trivy](https://github.com/aquasecurity/trivy)      | A comprehensive vulnerability scanner for containers and cloud-native applications.                  | Container Security      |
| [Anchore Engine](https://github.com/anchore/anchore-engine) | Open-source tool for scanning container images for vulnerabilities and enforcing security policies.   | Container Security      |
| [Clair](https://github.com/quay/clair)              | A popular open-source tool for scanning vulnerabilities in Docker and OCI container images.          | Container Security      |
| [Checkov](https://github.com/bridgecrewio/checkov)  | A static analysis tool for detecting misconfigurations in Infrastructure as Code (Terraform, Kubernetes, etc.). | Cloud Security         |
| [Terrascan](https://github.com/accurics/terrascan)  | A static analysis tool for ensuring security and compliance of cloud infrastructure (Terraform, Kubernetes). | Cloud Security         |
| [TFSec](https://github.com/aquasecurity/tfsec)      | A static analysis security scanner for Terraform configurations, focusing on cloud security.          | Cloud Security         |
| [Falco](https://github.com/falcosecurity/falco)     | A runtime security tool for detecting anomalous behavior in containers and cloud-native environments. | Container & Cloud Security |
| [Cloud Custodian](https://github.com/cloud-custodian/cloud-custodian) | A rules engine for enforcing security, compliance, and governance policies in cloud environments.     | Cloud Security          |
| [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) | A policy engine that enforces security and compliance policies for Kubernetes, microservices, and cloud infrastructure. | Cloud Security          |

<!-- Links -->

[Damien Burks]: https://www.linkedin.com/in/damienjburks/
