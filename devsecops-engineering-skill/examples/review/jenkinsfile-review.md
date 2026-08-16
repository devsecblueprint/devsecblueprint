# Review — Jenkinsfile Assessment

**Mode 3 — Review.** Demonstrates the fixed findings structure with compliant,
non-compliant, and Not Applicable outcomes in a single assessment.

---

## Pipeline under review

```groovy
pipeline {
    agent any

    environment {
        AWS_ACCESS_KEY_ID     = credentials('aws-access-key')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-key')
        REGISTRY              = 'registry.example.com'
        SONAR_TOKEN           = credentials('sonar-token')
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Build') {
            steps { sh 'mvn clean package -DskipTests' }
        }

        stage('SonarQube') {
            steps {
                sh 'mvn sonar:sonar -Dsonar.login=$SONAR_TOKEN'
            }
        }

        stage('Dependency Check') {
            steps {
                sh 'mvn org.owasp:dependency-check-maven:check'
                sh 'snyk test --severity-threshold=high || true'
            }
        }

        stage('Docker Build') {
            steps {
                sh """
                    docker build -t ${REGISTRY}/myapp:latest .
                    docker push ${REGISTRY}/myapp:latest
                """
            }
        }

        stage('Deploy') {
            steps {
                sh 'kubectl set image deployment/myapp app=${REGISTRY}/myapp:latest'
            }
        }
    }
}
```

**Workload determined:** Java/Maven service, containerized, deployed to Kubernetes.
No IaC in the repository. No Kubernetes manifests in the repository (deployment is
imperative).

---

## 1. Satisfied controls

Real credit where it is due — these are correctly present.

| Rule | Control | How it is satisfied |
|---|---|---|
| `DSB-BUILD-001` | Automated build from source control | Jenkins builds from SCM checkout, not from a workstation |
| `DSB-SCAN-001` | Scan phase present | SonarQube and dependency scanning both execute |
| `DSB-SCAN-002` | SAST | SonarQube covers the Java source |
| `DSB-SCAN-003` | SCA | OWASP Dependency-Check runs — see finding 4 on the duplication |
| `DSB-ID-003` | Secrets from a managed store | Jenkins Credentials, not hardcoded values |
| `DSB-ART-001` | Governed registry | Images publish to an organizational registry, not ad hoc storage |

---

## 2. Missing capabilities

Applicable to this workload, absent from the pipeline.

### 2.1 — No test execution (`DSB-TEST-001`, BLOCK) — **critical**

```groovy
sh 'mvn clean package -DskipTests'
```

`-DskipTests` is explicit. This pipeline never validates that the application works. Two
rules fail:

- `DSB-TEST-001` — no automated tests execute
- `DSB-TEST-002` — SonarQube and Dependency-Check are being relied on as though they
  constituted the Test phase. They do not. A SAST finding tells you nothing about whether
  the feature works.

This is the highest-severity finding in the review. Every other gate assumes a working
application.

### 2.2 — No secret scanning (`DSB-SCAN-004`, BLOCK)

`DSB-SCAN-004` is `always: true` — it carries no technology condition. Nothing here scans
for committed credentials, in the diff or in history.

### 2.3 — No container image scanning (`DSB-SCAN-005`, BLOCK)

The pipeline builds and pushes a container image and never scans it. The base image
contributes packages nobody on the team selected; this pipeline has no visibility into
what actually ships.

Placement: after `docker build`, **before** `docker push`.

### 2.4 — No SBOM (`DSB-SC-001`, WARN)

An artifact is released with no bill of materials. When the next widely-exploited library
CVE lands, answering "are we affected?" for this service is a manual investigation
instead of a query.

### 2.5 — No post-deployment verification (`DSB-DEPLOY-004`, WARN)

`kubectl set image` returns as soon as the API accepts the update. The pipeline reports
success whether or not the rollout completes or the pods become healthy.

### 2.6 — No DAST (`DSB-SCAN-009`, WARN)

A Java service on Kubernetes exposes an HTTP interface, and nothing tests it at runtime.
Add against a pre-production environment only — active testing against production
requires explicit organizational authorization.

---

## 3. Inappropriate enforcement

### 3.1 — Snyk cannot fail the build (`DSB-EXC-001`, BLOCK) — **critical**

```groovy
sh 'snyk test --severity-threshold=high || true'
```

`|| true` discards the exit code. This is an **undocumented, unapproved, unscoped,
non-expiring exception** to a BLOCK-level control. Every field `DSB-EXC-001` requires is
absent: no named approver, no scope, no justification, no expiry.

This is worse than not running Snyk. The stage reports green, so the pipeline looks like
it has SCA enforcement it does not have.

**Remediation:** either enforce it, or record a real exception with all five fields. If
the problem is unfixable transitive findings, scope the exception to those specifically —
not to the entire control.

### 3.2 — SonarQube results do not gate (`DSB-SCAN-002`, BLOCK)

`mvn sonar:sonar` submits results and exits successfully regardless of the quality gate
outcome. Findings are produced but nothing acts on them. This is REPORT-level behavior
where `DSB-SCAN-002` defaults to BLOCK — and, unlike a deliberate downgrade, it is
almost certainly unintentional.

### 3.3 — Deployment requires no authorization (`DSB-DEPLOY-003`, BLOCK)

Any merge deploys straight to what appears to be a production cluster, with no approval
gate and no record of who authorized it. Nothing in the pipeline distinguishes
environments at all.

---

## 4. Duplicate tooling (`DSB-SCAN-010`, WARN)

```groovy
sh 'mvn org.owasp:dependency-check-maven:check'
sh 'snyk test --severity-threshold=high || true'
```

**Two SCA tools for one capability.** `DSB-SCAN-010` requires the minimum sufficient
toolchain. This costs build time and doubles triage on largely overlapping findings, and
one of the two cannot fail the build anyway (finding 3.1).

**Decision required:** pick one.

```
Required Capability:      Software Composition Analysis
Candidate tools:          OWASP Dependency-Check (free, noisier, no fix guidance)
                          Snyk (commercial, better remediation data, licence cost)
Decision:                 Choose ONE based on your licensing position.
                          Retire the other entirely — do not leave it running unenforced.
DSB Requirement:          DSB-SCAN-003 — will be Satisfied by whichever is retained
```

Two scanners where one cannot fail the build is not defense in depth. It is one scanner
plus latency.

---

## 5. Pipeline security weaknesses

The pipeline as an attack surface (`DSB-SCAN-008`, and Principle 16).

### 5.1 — Long-lived static AWS credentials (`DSB-ID-001`, BLOCK) — **critical**

```groovy
AWS_ACCESS_KEY_ID     = credentials('aws-access-key')
AWS_SECRET_ACCESS_KEY = credentials('aws-secret-key')
```

Static AWS keys, exposed as environment variables to **every stage**. Any compromised
dependency in the Maven build — or any `sh` step — can read them, and they remain valid
indefinitely after exfiltration.

**Remediation:** federated workload identity (Jenkins OIDC → AWS IAM role) issuing
short-lived credentials.

### 5.2 — Credentials bound at pipeline scope (`DSB-ID-002`, BLOCK)

Every credential in the `environment` block is available to every stage. The build stage
holds registry and cloud credentials it has no need for — so a poisoned build dependency
reaches production directly. Bind credentials inside the stage that needs them.

### 5.3 — `agent any` (`DSB-BUILD-004`, WARN)

Builds run on any available agent, with no isolation or ephemerality guarantee. On a
persistent shared agent, workspace remnants and cached credentials survive between
builds — including between builds of *different projects*.

### 5.4 — Unpinned base image (`DSB-SC-002`, BLOCK)

Not visible in the Jenkinsfile, but verify the `Dockerfile`: base images must be pinned
by digest.

### 5.5 — Pipeline definition is unscanned (`DSB-SCAN-008`, WARN)

The Jenkinsfile is in the repository and is in scope for scanning. It has never been
scanned — which is why findings 5.1 through 5.3 went unnoticed.

---

## 6. Not Applicable

Required by `DSB-EVD-003`. These controls are absent **correctly** — their absence is not
a finding.

| Rule | Determination | Reason |
|---|---|---|
| `DSB-SCAN-006` | **N/A** | No infrastructure-as-code in this repository |
| `DSB-IAC-001` · `DSB-IAC-002` · `DSB-IAC-003` | **N/A** | No IaC in this repository |
| `DSB-SCAN-007` | **N/A** | No Kubernetes manifests in the repository — deployment is imperative via `kubectl set image`. *This is itself a `DSB-SRC-001` finding: the deployment configuration is not in version control. Declarative manifests would fix that and make `DSB-SCAN-007` Applicable — a net improvement.* |
| `DSB-ART-003` | **N/A** | No organizational signing policy stated; images stay within one governed registry |
| `DSB-SC-003` | **N/A** | Jenkins provides no native provenance attestation mechanism — a platform limitation, recorded as such |

The `DSB-SCAN-007` row is worth reading twice. The control is genuinely N/A, *and* the
reason it is N/A is itself a defect elsewhere. Recording both is the point of the
section.

---

## 7. Remediation, ordered by risk

| # | Action | Rule | Severity |
|---|---|---|---|
| 1 | Replace static AWS keys with OIDC federation to a scoped IAM role | `DSB-ID-001` | **Critical** |
| 2 | Remove `-DskipTests`; execute the test suite as a gate | `DSB-TEST-001` | **Critical** |
| 3 | Remove `\|\| true` from the Snyk step; enforce or record a scoped, expiring exception | `DSB-EXC-001` | **Critical** |
| 4 | Add container image scanning between build and push | `DSB-SCAN-005` | **High** |
| 5 | Add secret scanning covering diff and full history | `DSB-SCAN-004` | **High** |
| 6 | Bind credentials at stage scope, not pipeline scope | `DSB-ID-002` | **High** |
| 7 | Retire one of the two SCA tools | `DSB-SCAN-010` | **High** |
| 8 | Enforce the SonarQube quality gate | `DSB-SCAN-002` | **High** |
| 9 | Replace mutable `:latest` with a commit-derived tag; deploy by digest | `DSB-DEPLOY-002` | **High** |
| 10 | Add environment separation and an approval gate before production | `DSB-DEPLOY-003` | **High** |
| 11 | Move deployment configuration into version control as manifests | `DSB-SRC-001` | Medium |
| 12 | Add rollout verification after deploy | `DSB-DEPLOY-004` | Medium |
| 13 | Add SBOM generation at build | `DSB-SC-001` | Medium |
| 14 | Add DAST against pre-production only | `DSB-SCAN-009` | Medium |
| 15 | Use ephemeral agents instead of `agent any` | `DSB-BUILD-004` | Medium |
| 16 | Add Jenkinsfile scanning to the pipeline | `DSB-SCAN-008` | Medium |

### A note on `:latest` (item 9)

```groovy
docker build -t ${REGISTRY}/myapp:latest .
docker push ${REGISTRY}/myapp:latest
kubectl set image deployment/myapp app=${REGISTRY}/myapp:latest
```

This violates three rules at once:

- `DSB-BUILD-003` — no unique artifact identifier; every build overwrites the last
- `DSB-ART-002` — the published tag is mutable
- `DSB-DEPLOY-002` — Kubernetes resolves `:latest` at pull time, so the running image may
  not be the one this pipeline built

The consequence is that **no scan result can be attributed to a running workload**. Even
after you add image scanning (item 4), `:latest` makes the result describe an artifact
you cannot prove you are running. Item 9 is a prerequisite for item 4 being worth
anything.

---

## 8. Rationale

**Why the credential findings outrank the missing scanners.** A missing scanner means
undetected risk. Static, pipeline-scoped AWS keys mean any compromised build dependency
gets durable cloud access — the pipeline is not just failing to find risk, it is the
delivery mechanism for it.

**Why skipped tests rank equally.** This pipeline has never verified that the application
works. That is a delivery failure before it is a security failure, and `DSB-TEST-002`
exists precisely because scanners create the appearance that it has been covered.

**Why `|| true` is called out as an exception rather than a bug.** It *is* a risk
acceptance — just an invisible one, with no approver, no scope, and no expiry. Naming it
under `DSB-EXC-001` puts it in front of someone who can decide whether to accept it,
which is the entire purpose of the exception path.

**Why the duplicate SCA is only High and not Critical.** It wastes time and triage
capacity but does not create risk. It is ranked where it is because retiring one tool is
cheap and immediately makes the pipeline faster — and a faster pipeline is one teams do
not route around.

---

## 9. Curriculum pointers

- Pipeline Security — credential scoping, agent isolation, and CI/CD as attack surface
- Cloud Identity — replacing static keys with OIDC federation
- Container Security — image scanning placement and immutable tagging
- DevSecOps Foundations — why Test and Scan are separate phases
- Risk Management — exceptions, and what distinguishes acceptance from suppression
