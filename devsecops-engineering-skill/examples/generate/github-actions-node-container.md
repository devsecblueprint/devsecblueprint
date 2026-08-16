# Generate — Node.js Container on GitHub Actions to EKS

**Mode 2 — Design / Generate.** Implementation-ready configuration, annotated with rule
IDs. Note what is *absent* as much as what is present.

---

## Scenario as supplied

> Node.js API, TypeScript, npm. We build a container image, push to ECR, deploy to EKS.
> GitHub Actions. No existing security tooling — greenfield. What should the pipeline be?

---

## 1. Workload profile

| Factor | Determined |
|---|---|
| CI/CD platform | GitHub Actions |
| Language / runtime | TypeScript on Node.js |
| Package manager | npm (lockfile present) |
| Artifact | Container image |
| Registry | Amazon ECR |
| Deployment platform | Amazon EKS |
| Existing security tooling | None — greenfield |

**Assumptions — confirm:**

1. Kubernetes manifests live in this repository (`k8s/`). If a platform team owns them,
   `DSB-SCAN-007` becomes Satisfied (externally owned).
2. A `staging` environment exists and is representative enough for post-deploy testing.
3. No organizational artifact-signing policy exists yet.

Greenfield means every tool below is a proposal, not a reconciliation. If your
organization later adopts a commercial SAST or SCA platform, replace the corresponding
tool here — do not run both (`DSB-SCAN-010`).

---

## 2. Phase mapping

```
BUILD    npm ci (lockfile-pinned) → tsc → docker build → push by digest to ECR
TEST     Jest unit + integration
SCAN     Secrets → SAST → SCA → image scan → manifest scan → workflow scan → DAST
DEPLOY   Deploy digest to EKS staging → verify → DAST → gated promotion to production
```

---

## 3. The pipeline

### `.github/workflows/delivery.yml`

```yaml
name: Delivery

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

# DSB-ID-002 — least privilege by default; jobs opt in to what they need.
permissions:
  contents: read

concurrency:
  group: delivery-${{ github.ref }}
  cancel-in-progress: true

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: my-api

jobs:
  # ---------------------------------------------------------------------------
  # SCAN (pre-merge) — controls needing only source. Earliest valid placement.
  # ---------------------------------------------------------------------------
  secret-scan:
    # DSB-SCAN-004 — always applicable. Full history, not just the diff:
    # a secret deleted in a later commit is still a live credential.
    name: Secret scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          fetch-depth: 0 # required for history scanning
      # DSB-SC-002 — third-party actions pinned to a commit SHA, not a tag.
      - uses: gitleaks/gitleaks-action@83373cf2f8c4db6e24b41c1a9b086bb9619e9cd3 # v2.3.7
        env:
          GITLEAKS_ENABLE_SUMMARY: "true"

  sast:
    # DSB-SCAN-002 — first-party TypeScript exists.
    name: SAST
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write # DSB-EVD-001 — SARIF upload
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: github/codeql-action/init@48ab28a6f5dbc2a99bf1e0131198dd8f1df78169 # v3.28.0
        with:
          languages: javascript-typescript
      - uses: github/codeql-action/analyze@48ab28a6f5dbc2a99bf1e0131198dd8f1df78169 # v3.28.0

  workflow-scan:
    # DSB-SCAN-008 — pipeline definitions are in the repository, so they are in
    # scope. The pipeline holds ECR and EKS credentials; it is production
    # infrastructure. WARN, not BLOCK — findings are advisory at this maturity.
    name: Workflow config scan
    runs-on: ubuntu-latest
    continue-on-error: true # enforcement: WARN (DSB-SCAN-008 default)
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: zizmorcore/zizmor-action@5ca5fc7a4779c5263a3ffa0e1f693009994446d1 # v0.1.2

  manifest-scan:
    # DSB-SCAN-007 — Kubernetes manifests exist in this repository.
    name: Kubernetes manifest scan
    runs-on: ubuntu-latest
    continue-on-error: true # enforcement: WARN
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: bridgecrewio/checkov-action@d6369fdf8a2897ebc8936a03ea82f61d6b28a166 # v12.2996.0
        with:
          directory: k8s/
          framework: kubernetes
          soft_fail: true

  # ---------------------------------------------------------------------------
  # BUILD + TEST + SCAN (artifact) — one job so the tested tree is the built tree.
  # ---------------------------------------------------------------------------
  build-test-scan:
    name: Build, test, scan
    runs-on: ubuntu-latest
    needs: [secret-scan, sast]
    permissions:
      contents: read
      id-token: write # DSB-ID-001 — OIDC federation, no static AWS keys
    outputs:
      image-digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

      - uses: actions/setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af # v4.1.0
        with:
          node-version: '22'
          cache: npm

      # DSB-BUILD-002 — `npm ci` installs strictly from the committed lockfile
      # with integrity hashes. `npm install` would resolve fresh and make the
      # build non-deterministic.
      - name: Install dependencies
        run: npm ci

      # DSB-SCAN-003 — SCA AFTER resolution. Scanning package.json before
      # install sees direct dependencies only and misses the transitive
      # majority, which is where most exploitable risk lives.
      - name: SCA
        run: npm audit --audit-level=high

      # DSB-TEST-001 — project-native framework. DSB-TEST-002: this does not
      # substitute for the scan phase, and the scans do not substitute for it.
      - name: Test
        run: npm test -- --ci --reporters=default --reporters=jest-junit

      # DSB-EVD-001 — machine-readable evidence, retained.
      - uses: actions/upload-artifact@6f51ac03b9356f520e9adb1b1b7802705f340c2b # v4.5.0
        if: always()
        with:
          name: test-results
          path: junit.xml
          retention-days: 90

      - name: Build application
        run: npm run build

      # DSB-ID-001 — short-lived credentials from OIDC federation. There is no
      # long-lived AWS access key anywhere in this pipeline.
      - uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502 # v4.0.2
        with:
          role-to-assume: ${{ vars.AWS_BUILD_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - uses: aws-actions/amazon-ecr-login@062b18b96a7aff071d4dc91bc00c4c1a7945b076 # v2.0.1
        id: ecr

      # DSB-BUILD-003 — the image is identified by digest, traceable to this
      # commit and this run.
      - name: Build image
        run: |
          docker build \
            --build-arg NODE_VERSION=22 \
            -t "${{ steps.ecr.outputs.registry }}/${ECR_REPOSITORY}:${GITHUB_SHA}" \
            .

      # DSB-SCAN-005 — scan the built image BEFORE it is published. The base
      # image contributes packages nobody on the team selected; this is the only
      # point at which what actually ships is visible.
      - name: Image scan
        uses: aquasecurity/trivy-action@18f2510ee396bbf400402947b394f2dd8c87dbb0 # v0.29.0
        with:
          image-ref: ${{ steps.ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
          exit-code: '1'
          severity: 'CRITICAL,HIGH'
          ignore-unfixed: true # WARN-equivalent for findings with no available fix

      # DSB-SC-001 — SBOM generated at build, when the resolved set is known.
      - name: Generate SBOM
        uses: anchore/sbom-action@f325610c9f50a54015d37c8d16cb3b0e2c8f4de0 # v0.18.0
        with:
          image: ${{ steps.ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
          format: cyclonedx-json
          artifact-name: sbom.cdx.json

      # DSB-DEPLOY-001 — publication happens only after every gate above passed.
      - name: Push image
        id: push
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: |
          IMAGE="${{ steps.ecr.outputs.registry }}/${ECR_REPOSITORY}"
          docker push "${IMAGE}:${GITHUB_SHA}"
          DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "${IMAGE}:${GITHUB_SHA}" | cut -d@ -f2)
          echo "digest=${DIGEST}" >> "$GITHUB_OUTPUT"

  # ---------------------------------------------------------------------------
  # DEPLOY
  # ---------------------------------------------------------------------------
  deploy-staging:
    name: Deploy to staging
    runs-on: ubuntu-latest
    needs: [build-test-scan, workflow-scan, manifest-scan]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: staging
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

      - uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502 # v4.0.2
        with:
          # DSB-ID-002 — a deploy role, distinct from the build role.
          role-to-assume: ${{ vars.AWS_STAGING_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      # DSB-DEPLOY-002 — deploy by DIGEST. The image that was scanned is the
      # image that runs. A mutable tag here would silently invalidate every scan
      # result above.
      - name: Deploy
        env:
          IMAGE_DIGEST: ${{ needs.build-test-scan.outputs.image-digest }}
        run: |
          aws eks update-kubeconfig --name staging-cluster
          kubectl set image deployment/my-api \
            api="${{ vars.ECR_REGISTRY }}/${ECR_REPOSITORY}@${IMAGE_DIGEST}"
          kubectl rollout status deployment/my-api --timeout=5m

      # DSB-DEPLOY-004 — deployment succeeding is not the system working.
      - name: Smoke test
        run: curl -fsS --retry 5 --retry-delay 10 "${{ vars.STAGING_URL }}/healthz"

  dast:
    # DSB-SCAN-009 — runtime-dependent, so it runs after deployment. It remains
    # part of Scan/verification, not a fifth phase.
    #
    # STAGING ONLY. Active DAST against production requires explicit, documented
    # organizational authorization. This job must never be pointed at the
    # production URL without it.
    name: DAST (staging)
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    continue-on-error: true # enforcement: WARN — slow and noisy by nature
    steps:
      - uses: zaproxy/action-baseline@7c4deb10e6261301961c86d65d54a516394f9aed # v0.14.0
        with:
          target: ${{ vars.STAGING_URL }}

  deploy-production:
    name: Deploy to production
    runs-on: ubuntu-latest
    needs: [deploy-staging, dast]
    # DSB-DEPLOY-003 — the `production` environment carries required reviewers,
    # so this records who authorized the deployment, of which artifact, from
    # which commit.
    environment: production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502 # v4.0.2
        with:
          role-to-assume: ${{ vars.AWS_PROD_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      # DSB-DEPLOY-002 — the SAME digest that passed staging. Not a rebuild.
      - name: Promote
        env:
          IMAGE_DIGEST: ${{ needs.build-test-scan.outputs.image-digest }}
        run: |
          aws eks update-kubeconfig --name production-cluster
          kubectl set image deployment/my-api \
            api="${{ vars.ECR_REGISTRY }}/${ECR_REPOSITORY}@${IMAGE_DIGEST}"
          kubectl rollout status deployment/my-api --timeout=10m
```

---

## 4. Supporting configuration

### `.github/CODEOWNERS`

```
# DSB-SRC-003 — security-relevant paths require review by someone who owns them.
# Without this, the controls above can be edited by anyone with write access.
/.github/workflows/   @devsecblueprint/security
/k8s/                 @devsecblueprint/platform
/Dockerfile           @devsecblueprint/security
```

### Branch protection (`DSB-SRC-002`)

Configure on `main` — this is the enforcement point that makes every gate above
unavoidable:

- Require a pull request with at least one approving review
- Require status checks: `secret-scan`, `sast`, `build-test-scan`
- Prevent direct pushes, including for administrators

Without branch protection, all of the above is advisory: any contributor can push
directly to `main` and skip it entirely.

---

## 5. Not Applicable

Required by `DSB-EVD-003`.

| Rule | Determination | Reason |
|---|---|---|
| `DSB-SCAN-006` | **N/A** | No infrastructure-as-code in this repository. The EKS cluster and ECR repository are provisioned elsewhere. Flips to Applicable the moment a `terraform/` directory appears. |
| `DSB-IAC-001` · `DSB-IAC-002` · `DSB-IAC-003` | **N/A** | No IaC in this repository. |
| `DSB-ART-003` | **N/A** | No organizational signing policy, and images are consumed only by your own EKS clusters from your own ECR — no cross-trust-boundary distribution. Revisit when either changes. |
| `DSB-SC-003` | **Deferred, not N/A** | GitHub Actions *does* support provenance attestation, so the platform condition is met. Omitted from v1 of this pipeline as a deliberate sequencing choice, which makes it a gap rather than a Not Applicable. Add `actions/attest-build-provenance` with verification at deploy — generating provenance without verifying it provides no security value. |

The `DSB-SC-003` row is the important one. It is the difference between "the workload
makes this meaningless" (N/A) and "we chose not to do it yet" (a gap, and if it bypasses
a BLOCK gate, an exception under `DSB-EXC-001`).

---

## 6. Rationale

**Why `npm ci` and not `npm install`.** `npm install` may resolve versions not in the
lockfile, so the tree you scanned is not necessarily the tree you built. `npm ci` fails
if the lockfile and manifest disagree — a deterministic build is what makes every
downstream scan result meaningful (`DSB-BUILD-002`).

**Why SCA runs after install.** Scanning `package.json` sees direct dependencies only.
Most exploitable risk arrives transitively, through packages nobody explicitly chose.
This is the most common placement error in the catalog.

**Why every action is SHA-pinned.** A tag is mutable. `@v4` resolves to whatever the
maintainer's account pushes there, which makes it remote code execution scheduled for
whenever that account is compromised. `DSB-SC-002` requires immutable references; use
Dependabot or Renovate to keep the pins moving deliberately.

**Why build and test are one job.** Splitting them means re-checkout and re-install, and
the tested tree is then not provably the built tree. One job keeps `DSB-DEPLOY-002`
honest end to end.

**Why deploy by digest.** A tag can be overwritten. The digest is the artifact. Every
scan result above describes exactly one digest; deploying anything else discards them
all silently.

**Why DAST is WARN and staging-only.** DAST is slow and noisy, and staging is not
production, so findings need triage rather than an automatic stop. Staging-only is not a
preference — active scanning against production is operationally indistinguishable from
an attack and requires explicit organizational authorization.

**Why there is no second SAST or SCA tool.** `DSB-SCAN-010`. One tool per capability.
Adding Semgrep alongside CodeQL, or Snyk alongside `npm audit`, multiplies triage cost
without adding assurance — and a pipeline slow enough to route around is a net security
loss.

---

## 7. Curriculum pointers

- CI/CD Fundamentals — job dependencies, gating, and why the four phases exist
- Supply Chain Security — lockfiles, SHA pinning, SBOM, and provenance
- Container Security — image scanning placement and base image selection
- Cloud Identity — OIDC federation and eliminating static cloud credentials
- Kubernetes Security — digest-pinned deployments and admission policy
