---
module_id: container-security
passing_score: 80
---

## Question 1

Why are containers often considered a significant attack surface in modern software delivery?

A. They are slower to deploy than traditional virtual machines
B. Insecure configurations can make them the easiest entry point into an environment
C. They do not support the use of encryption for data at rest
D. They require physical hardware access to be managed effectively

**Correct Answer:** B

**Explanation:** While containers offer speed and portability, outdated base images and leaked secrets can turn them into a primary target for attackers.

---

## Question 2

According to the module, where must security be embedded to be truly effective for containers?

A. Only during the final testing phase
B. Only at the network firewall level
C. Throughout the entire container lifecycle: build, ship, and run
D. Exclusively within the developer's local environment

**Correct Answer:** C

**Explanation:** In DevSecOps, container security is a continuous process that covers the build, ship, and runtime phases.

---

## Question 3

Which of the following is a common attack surface related to **Container Runtime**?

A. Hardcoded API keys in the source code
B. Containers running as root or with privileged access
C. Using a private registry for image storage
D. Explicitly versioning image tags instead of using "latest"

**Correct Answer:** B

**Explanation:** Running containers as root or with excessive privileges can allow an attacker to escape the container and compromise the host system.

---

## Question 4

What is a key security activity that should happen during the **Build Phase**?

A. Running containers with least privilege
B. Using minimal base images to reduce the attack surface
C. Implementing runtime anomaly detection
D. Monitoring network traffic for resource exhaustion

**Correct Answer:** B

**Explanation:** Using lightweight base images (like Alpine or Distroless) minimizes the number of unnecessary files and binaries an attacker could exploit.

---

## Question 5

In the **Ship Phase**, why is it recommended to avoid using the "latest" tag for images?

A. The "latest" tag is automatically encrypted by most registries
B. It ensures that the most recent vulnerabilities are always included
C. Explicit versioning is required for traceability and consistent deployments
D. Using "latest" prevents the image from being signed

**Correct Answer:** C

**Explanation:** Versioning tags explicitly ensures you know exactly which version of the code is deployed, avoiding "hidden" updates that "latest" might pull.

---

## Question 6

What does the principle of **Immutable Infrastructure** mean for containers?

A. Containers should be manually patched while they are running in production
B. Container settings should be changed frequently to confuse attackers
C. Containers are disposable; you rebuild images to patch rather than modifying live ones
D. The hardware hosting the containers can never be upgraded

**Correct Answer:** C

**Explanation:** Immutable infrastructure means you never "hot-fix" a running container; you update the image and redeploy it to ensure consistency.

---

## Question 7

Which tool is specifically recommended for **detecting runtime anomalies** and suspicious behavior in live containers?

A. Trivy
B. Grype
C. Falco
D. Cosign

**Correct Answer:** C

**Explanation:** Falco acts as a security camera for the run phase, watching for abnormal processes or privilege escalations.

---

## Question 8

What is the best practice for managing **Secrets** in a containerized environment?

A. Baking them into the environment variables of the Dockerfile
B. Injecting them securely at runtime using tools like Vault or Secrets Manager
C. Hardcoding them into the base image for easier access
D. Storing them in a public GitHub repository for transparency

**Correct Answer:** B

**Explanation:** Secrets should never be part of the image; they should be injected at runtime so they aren't exposed in the image layers.

---

## Question 9

Which tool would you use to **sign and verify** images to ensure their integrity?

A. Docker Scout
B. Clair
C. Cosign
D. Anchore Engine

**Correct Answer:** C

**Explanation:** Cosign (and Notary) allow you to sign images so you can verify that they haven't been tampered with before they are deployed.

---

## Question 10

What is the purpose of maintaining a **Software Bill of Materials (SBOM)** for your containers?

A. To track exactly what libraries and dependencies are inside every image
B. To calculate the financial cost of running the container in the cloud
C. To replace the need for runtime monitoring tools like Falco
D. To list the physical hardware components of the server

**Correct Answer:** A

**Explanation:** An SBOM provides a clear inventory of everything inside the image, making it easier to identify if a new vulnerability affects your stack.

---