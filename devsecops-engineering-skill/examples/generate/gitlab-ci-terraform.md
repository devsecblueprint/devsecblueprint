# Generate — Terraform on GitLab CI

**Mode 2 — Design / Generate.** An infrastructure workload. Note how different the
applicable control set is from the application example — this is the selection algorithm
doing its job, not a weaker pipeline.

---

## Scenario as supplied

> Terraform for our AWS environments, GitLab CI, self-hosted GitLab. Separate state per
> environment in S3. We want the same rigor we apply to application code.

---

## 1. Workload profile

| Factor | Determined |
|---|---|
| CI/CD platform | GitLab CI (self-hosted) |
| Workload type | Infrastructure-as-code (Terraform) |
| Cloud | AWS |
| State backend | S3, separate per environment |
| Artifact | Terraform plan file — not a distributable artifact |
| Deployment | `terraform apply` to AWS environments |
| Existing security tooling | None stated |

**Assumptions — confirm:**

1. GitLab is configured as an OIDC identity provider trusted by AWS IAM. If not,
   `DSB-ID-001` is the first thing to fix — it precedes everything else here.
2. State locking is configured (DynamoDB table or S3 native locking).
3. Environments are `dev`, `staging`, `production`, with production requiring approval.

---

## 2. Phase mapping

Infrastructure follows the same four phases (`DSB-IAC-001`). The activities differ; the
structure does not.

```
BUILD    terraform init + validate + fmt — the deliverable is a valid configuration
TEST     Contract/policy tests where meaningful test surface exists
SCAN     Secret scan → IaC scan → plan-aware policy evaluation
DEPLOY   Plan → review → gated apply → post-apply verification
```

The most important difference from an application pipeline: **the plan is the review
artifact, and apply is the irreversible step.** Everything upstream exists to make the
plan trustworthy.

---

## 3. The pipeline

> **Digests below are placeholders.** `DSB-SC-002` requires pinning by digest, and the
> configuration demonstrates that shape — but resolve the real digests for the versions
> you adopt before use (`docker buildx imagetools inspect <image>:<tag>`). A copied
> placeholder digest will simply fail to pull, which is the safe failure mode, but do not
> mistake these for verified pins.

### `.gitlab-ci.yml`

```yaml
stages:
  - scan
  - build
  - plan
  - apply

variables:
  TF_VERSION: "1.10.3"
  TF_IN_AUTOMATION: "true"
  # DSB-EVD-002 — plan output is reviewed by humans; keep it readable but
  # never let it echo secret values.
  TF_CLI_ARGS: "-no-color"

default:
  # DSB-SC-002 — image pinned by digest, not by tag. A tag is mutable and this
  # image executes with credentials that can change your entire estate.
  image:
    name: hashicorp/terraform:1.10.3@sha256:6f8e4c7c1e8b4d3f2a1c9e0b7d6a5f4e3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f
    entrypoint: [""]

# DSB-ID-001 — short-lived credentials via GitLab OIDC. No AWS access keys in
# CI/CD variables anywhere in this pipeline.
.aws_oidc: &aws_oidc
  id_tokens:
    AWS_ID_TOKEN:
      aud: https://gitlab.example.com
  before_script:
    - >
      export AWS_WEB_IDENTITY_TOKEN_FILE=$(mktemp);
      echo "${AWS_ID_TOKEN}" > "${AWS_WEB_IDENTITY_TOKEN_FILE}";
      export AWS_ROLE_ARN="${TF_ROLE_ARN}";
      export AWS_DEFAULT_REGION="${AWS_REGION}"

# -----------------------------------------------------------------------------
# SCAN — needs only the source. Earliest valid placement.
# -----------------------------------------------------------------------------
secret-scan:
  # DSB-SCAN-004 — always applicable. Terraform repositories are a high-value
  # target for this specifically: variable files and state fragments are where
  # credentials most often get committed by accident.
  stage: scan
  image:
    name: zricethezav/gitleaks:v8.24.0@sha256:d4d6e0b0e0d1e5f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1
    entrypoint: [""]
  script:
    - gitleaks detect --source . --redact --report-format sarif --report-path gitleaks.sarif
  artifacts:
    when: always
    # DSB-EVD-001 — machine-readable evidence, retained.
    reports:
      sast: gitleaks.sarif
    expire_in: 90 days

iac-scan:
  # DSB-SCAN-006 — the repository IS infrastructure-as-code. This is the primary
  # scan control for this workload, where SAST would be for an application.
  stage: scan
  image:
    name: bridgecrew/checkov:3.2.334@sha256:9c8b7a6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b
    entrypoint: [""]
  script:
    - checkov -d . --framework terraform --output cli --output sarif --output-file-path console,checkov.sarif
  artifacts:
    when: always
    reports:
      sast: checkov.sarif
    expire_in: 90 days
  # DSB-SCAN-006 default is BLOCK. Retained: an IaC misconfiguration is
  # provisioned risk — a public bucket is created correctly and instantly by a
  # working pipeline.

pipeline-scan:
  # DSB-SCAN-008 — the pipeline definition is in the repository and holds a role
  # that can modify the entire AWS estate.
  stage: scan
  image:
    name: bridgecrew/checkov:3.2.334@sha256:9c8b7a6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b
    entrypoint: [""]
  script:
    - checkov -f .gitlab-ci.yml --framework gitlab_ci --soft-fail
  allow_failure: true # enforcement: WARN (DSB-SCAN-008 default)

# -----------------------------------------------------------------------------
# BUILD — for IaC, "build" means producing a valid, initialized configuration.
# -----------------------------------------------------------------------------
validate:
  # DSB-IAC-001 — infrastructure is a deliverable and gets the same treatment.
  # DSB-BUILD-002 — the committed .terraform.lock.hcl pins provider versions and
  # verifies their checksums. Without it, two runs can resolve different providers.
  stage: build
  <<: *aws_oidc
  script:
    - terraform init -backend=false
    - terraform validate
    - terraform fmt -check -recursive

# -----------------------------------------------------------------------------
# PLAN — the review artifact. DSB-IAC-002.
# -----------------------------------------------------------------------------
.plan_template: &plan_template
  stage: plan
  <<: *aws_oidc
  script:
    # DSB-IAC-003 — remote state, encrypted, access-controlled, locked. State is
    # never committed: it commonly contains secrets and always contains a
    # complete map of the environment.
    - terraform init -backend-config="key=${TF_ENVIRONMENT}/terraform.tfstate"
    - terraform plan -out=tfplan -input=false
    # A binary plan is not reviewable. The JSON form is what policy evaluation
    # and human review actually consume.
    - terraform show -json tfplan > tfplan.json
    # DSB-IAC-002 — policy evaluated against the PLAN, not the source. This
    # catches what the change will actually do, including resource replacements
    # that read as a one-line attribute edit in the diff.
    - checkov -f tfplan.json --framework terraform_plan --soft-fail
  artifacts:
    paths:
      - tfplan
      - tfplan.json
    # DSB-DEPLOY-002 — apply consumes THIS plan file. Re-planning at apply time
    # would apply something nobody reviewed.
    expire_in: 7 days

plan:dev:
  <<: *plan_template
  variables:
    TF_ENVIRONMENT: dev
    TF_ROLE_ARN: ${AWS_DEV_PLAN_ROLE_ARN}
  environment:
    name: dev
    action: prepare

plan:production:
  <<: *plan_template
  variables:
    TF_ENVIRONMENT: production
    # DSB-ID-002 — a read-only plan role, distinct from the apply role. A plan
    # job never needs write access.
    TF_ROLE_ARN: ${AWS_PROD_PLAN_ROLE_ARN}
  environment:
    name: production
    action: prepare
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# -----------------------------------------------------------------------------
# APPLY — the irreversible step.
# -----------------------------------------------------------------------------
apply:dev:
  # DSB-DEPLOY-001 — every upstream gate must have passed.
  stage: apply
  <<: *aws_oidc
  needs: [secret-scan, iac-scan, validate, "plan:dev"]
  variables:
    TF_ENVIRONMENT: dev
    TF_ROLE_ARN: ${AWS_DEV_APPLY_ROLE_ARN}
  script:
    - terraform init -backend-config="key=${TF_ENVIRONMENT}/terraform.tfstate"
    # DSB-DEPLOY-002 — apply the reviewed plan file. Never `terraform apply`
    # without a plan argument: that re-plans against current state and can apply
    # changes that appeared after review.
    - terraform apply -input=false tfplan
  environment:
    name: dev
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

apply:production:
  stage: apply
  <<: *aws_oidc
  needs: [secret-scan, iac-scan, validate, "plan:production"]
  variables:
    TF_ENVIRONMENT: production
    TF_ROLE_ARN: ${AWS_PROD_APPLY_ROLE_ARN}
  script:
    - terraform init -backend-config="key=${TF_ENVIRONMENT}/terraform.tfstate"
    - terraform apply -input=false tfplan
    # DSB-DEPLOY-004 — verify the change took effect as planned.
    - terraform plan -detailed-exitcode -input=false || test $? -ne 2
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      # DSB-DEPLOY-003 — manual gate plus GitLab protected-environment approval
      # records who authorized this apply, of which plan, from which commit.
      when: manual
  allow_failure: false
```

---

## 4. Supporting configuration

### `CODEOWNERS` (`DSB-SRC-003`)

```
# Security-relevant paths require review by their owners.
/.gitlab-ci.yml          @security-team
/modules/iam/            @security-team
/environments/production/ @platform-leads @security-team
```

### Protected branches and environments (`DSB-SRC-002`, `DSB-DEPLOY-003`)

- `main` protected: no direct push, merge request required, pipeline must succeed
- `production` as a protected environment with a designated approver group
- The apply roles assumable **only** by the pipeline identity, never by humans

That last point is what makes the pipeline the sole path to change. If engineers can
assume the apply role directly, every control above becomes optional.

---

## 5. Not Applicable

Required by `DSB-EVD-003`. This workload excludes more controls than the application
example — because it genuinely does less, not because it is held to a lower standard.

| Rule | Determination | Reason |
|---|---|---|
| `DSB-SCAN-002` | **N/A** | No first-party application source code. Terraform configuration is covered by `DSB-SCAN-006`, which is the correct control for it — running a SAST tool here would produce noise, not assurance. |
| `DSB-SCAN-005` | **N/A** | No container image is produced. The pinned Terraform runner image is a build input, governed by `DSB-SC-002`, not a deliverable. |
| `DSB-SCAN-007` | **N/A** | No Kubernetes manifests in this repository. Flips to Applicable if EKS workload definitions are added. |
| `DSB-SCAN-009` | **N/A** | This workload exposes no runtime interface. It provisions infrastructure that may host services with their own interfaces; those services carry `DSB-SCAN-009` in their own pipelines. |
| `DSB-DEPLOY-004` (full form) | **Partial** | No application to smoke-test. Satisfied in the reduced form of a post-apply drift check, which is the meaningful equivalent for this workload. |
| `DSB-ART-001` · `DSB-ART-002` · `DSB-ART-003` · `DSB-ART-004` | **N/A** | No distributable artifact is produced. The plan file is an intra-pipeline intermediate, not a promoted artifact. *If you publish reusable Terraform modules to a registry, all four become Applicable.* |
| `DSB-SC-001` | **N/A** | No released artifact to describe. Provider dependencies are pinned and checksum-verified by `.terraform.lock.hcl` under `DSB-BUILD-002`. |
| `DSB-SC-003` | **N/A** | No released artifact for which to generate provenance. |
| `DSB-TEST-001` | **Conditional** | Applicable if the repository contains reusable modules with contract-testable behavior. For an environment-composition repository, `terraform validate` plus plan review is the meaningful validation surface — writing assertions that a resource block contains the values it literally contains would be a `DSB-TEST-003` violation. |

---

## 6. Rationale

**Why the plan is the review artifact.** Terraform diffs routinely hide destructive
changes — a resource *replacement* can read as a one-line attribute edit in the source.
The plan is the only artifact showing what will actually happen, which is why policy
evaluation runs against `tfplan.json` and not against the `.tf` files alone.

**Why `terraform apply tfplan` and never bare `terraform apply`.** A bare apply re-plans
against current state at apply time and can execute changes that appeared after the
review. Applying the saved plan is the IaC equivalent of `DSB-DEPLOY-002` — deploy the
artifact that was reviewed, not a fresh one.

**Why separate plan and apply roles.** A plan needs read access only. Splitting them
means a compromised merge request can, at worst, read your infrastructure layout — it
cannot change it (`DSB-ID-002`).

**Why the state backend rules are BLOCK.** State files commonly contain secrets in
plaintext and always contain a complete map of the environment. Unlocked state
additionally lets two concurrent applies corrupt the environment outright, which is a
correctness failure before it is a security one.

**Why so many controls are N/A here.** This is the selection algorithm working. Applying
container scanning to a repository that builds no container produces zero findings, zero
assurance, and real pipeline latency — and teaches the team the gates are theatre. Nine
Not Applicable determinations, each written down and each automatically wrong the moment
the workload changes, is a stronger position than nine scanners that find nothing.

---

## 7. Curriculum pointers

- Infrastructure as Code — Terraform delivery patterns and plan-review discipline
- Cloud Identity — OIDC federation from CI/CD to AWS IAM
- Policy as Code — evaluating plan output rather than source
- State Management — remote backends, encryption, and locking
- DevSecOps Foundations — why the four phases apply identically to infrastructure
