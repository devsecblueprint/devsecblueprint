# Advise — Enterprise Java on Jenkins and OpenShift

**Mode 1 — Advise.** No pipeline code is produced. This example demonstrates the
existing-tool decision pattern, ownership boundaries, and explicit Not Applicable
determinations.

---

## Scenario as supplied

> We're an enterprise running Jenkins. Java services built with Maven, artifacts in
> Artifactory, deployed to OpenShift. We already own Checkmarx, Black Duck, and Prisma
> Cloud. Our platform team runs the OpenShift clusters and has admission policy in place.
> What should our pipeline look like and what are we missing?

---

## 1. Workload profile

| Factor | Determined | Source |
|---|---|---|
| CI/CD platform | Jenkins | Stated |
| Language / build | Java, Maven | Stated |
| Artifact type | JAR **and** container image | Inferred — OpenShift deployment requires an image |
| Registry | Artifactory (JARs and images) | Stated |
| Deployment platform | OpenShift (Kubernetes) | Stated |
| Existing security products | Checkmarx (SAST), Black Duck (SCA), Prisma Cloud (container + IaC) | Stated |
| Cluster policy ownership | Platform team, admission policy in place | Stated |

**Assumptions made — confirm these:**

1. Container images are built in this pipeline, not by an OpenShift BuildConfig. If the
   cluster builds them, `DSB-SCAN-005` placement moves and `DSB-DEPLOY-002` needs
   re-examination.
2. A pre-production OpenShift environment exists and is representative enough to test
   against.
3. Kubernetes manifests or Helm charts live in the application repository. If the
   platform team owns them, `DSB-SCAN-007` becomes externally owned.

---

## 2. Phase mapping

```
BUILD    Maven compile + package → JAR → container image → push to Artifactory
TEST     JUnit via Maven Surefire; integration tests via Failsafe
SCAN     Secrets → SAST → SCA → image scan → manifest scan → (post-deploy) DAST
DEPLOY   Promote image by digest to OpenShift; verify; trigger runtime validation
```

---

## 3. Applicable controls

### The existing-tool decisions

Your three products cover five capabilities. Nothing new needs buying.

```
Required Capability:      Static Application Security Testing
Existing Organizational
Tool:                     Checkmarx
Decision:                 Use existing tool. Do not introduce a second SAST scanner.
DSB Requirement:          DSB-SCAN-002 — Satisfied
```

```
Required Capability:      Software Composition Analysis
Existing Organizational
Tool:                     Black Duck
Decision:                 Use existing tool. Do not introduce a second SCA scanner.
                          Notably: do NOT add OWASP Dependency-Check "for coverage" —
                          that is a DSB-SCAN-010 violation, not defense in depth.
DSB Requirement:          DSB-SCAN-003 — Satisfied
```

```
Required Capability:      Container / Image Scanning
Existing Organizational
Tool:                     Prisma Cloud
Decision:                 Use existing tool. Scan at build time in the pipeline AND rely
                          on Prisma's registry scanning for drift on published images.
                          This is not duplication — the two answer different questions
                          ("should this ship?" vs. "is what shipped still safe?").
DSB Requirement:          DSB-SCAN-005 — Satisfied
```

```
Required Capability:      Infrastructure-as-Code Scanning
Existing Organizational
Tool:                     Prisma Cloud IaC
Decision:                 Use existing tool, IF this repository contains IaC.
                          See Not Applicable below — for a typical service repo it does not.
DSB Requirement:          DSB-SCAN-006 — See §5
```

### Full control table

| Rule | Capability | Tool | Placement | Enforcement |
|---|---|---|---|---|
| `DSB-SRC-002` | Branch protection | Jenkins + SCM | Merge to `main` | BLOCK |
| `DSB-SCAN-004` | Secret scanning | **Gap — see §6** | Pre-merge + history | BLOCK |
| `DSB-SCAN-002` | SAST | Checkmarx | Post-checkout, pre-build | BLOCK on High+ |
| `DSB-BUILD-001` | Automated build | Jenkins + Maven | Build | BLOCK |
| `DSB-BUILD-002` | Dependency integrity | Artifactory as the only Maven repo | Build | BLOCK |
| `DSB-TEST-001` | Automated tests | Surefire / Failsafe | Test | BLOCK |
| `DSB-SCAN-003` | SCA | Black Duck | After `mvn dependency:resolve` | BLOCK on High+ with fix |
| `DSB-SC-001` | SBOM | Black Duck or CycloneDX Maven plugin | Build | REPORT |
| `DSB-BUILD-003` | Artifact identity | Image digest + Maven version | Build | BLOCK |
| `DSB-SCAN-005` | Image scanning | Prisma Cloud | After image build, before push | BLOCK on Critical |
| `DSB-SCAN-007` | Manifest scanning | **See §4 — partly externally owned** | Pre-merge | WARN |
| `DSB-SCAN-008` | Pipeline config scanning | **Gap — see §6** | Pre-merge | WARN |
| `DSB-ART-001` | Governed registry | Artifactory | Publish | BLOCK |
| `DSB-ART-002` | Artifact immutability | Artifactory immutable tags | Publish | BLOCK |
| `DSB-DEPLOY-001` | Gate verification | Jenkins stage dependencies | Deploy | BLOCK |
| `DSB-DEPLOY-002` | Deploy tested artifact | Digest-pinned image reference | Deploy | BLOCK |
| `DSB-DEPLOY-003` | Authorized deployment | Jenkins input step + RBAC | Deploy to prod | BLOCK |
| `DSB-DEPLOY-004` | Post-deploy verification | Smoke tests | After deploy | WARN |
| `DSB-SCAN-009` | DAST | **Gap — see §6** | Post-deploy to pre-prod only | WARN |
| `DSB-ID-002` | Least-privilege credentials | Jenkins credential scoping | Cross-cutting | BLOCK |
| `DSB-ID-003` | Managed secrets | Jenkins Credentials or Vault | Cross-cutting | BLOCK |
| `DSB-EVD-001` | Machine-readable evidence | JUnit XML, SARIF, CycloneDX | All gates | REPORT |

---

## 4. Satisfied (externally owned)

```
DSB-SCAN-007 — Kubernetes / workload configuration scanning
Owning process:  Platform team's OpenShift admission policy (SCC + admission controller)
Enforcement:     Workloads violating the baseline are rejected at admission
Coverage check:  ✅ Applies to all namespaces this service deploys into
Residual:        Admission rejects at deploy time, which is late feedback. Recommend a
                 WARN-level manifest scan pre-merge so teams learn before the deploy
                 fails — the platform control remains the enforcement point.
```

**This is the determination to scrutinize most.** Before accepting it, confirm all three:
the process is *named*, it is *enforced* rather than merely available, and it covers
*this* workload's namespaces. Two of three is a gap, not an external satisfaction.

---

## 5. Not Applicable

Required by `DSB-EVD-003`. Every excluded control, with the workload fact that excludes
it.

| Rule | Determination | Reason |
|---|---|---|
| `DSB-SCAN-006` | **N/A** | This service repository contains no infrastructure-as-code. Cluster and cloud infrastructure is defined in the platform team's repositories, where it carries its own `DSB-IAC-*` obligations. *If your service repo does contain Terraform, this flips to Applicable with Prisma Cloud IaC.* |
| `DSB-IAC-001` · `DSB-IAC-002` · `DSB-IAC-003` | **N/A** | No IaC in this repository. Same caveat as above. |
| `DSB-ART-003` | **N/A** | Images are consumed only by your own OpenShift clusters from your own Artifactory instance — no cross-trust-boundary distribution, and no organizational signing policy stated. Revisit if you distribute externally or adopt a signing requirement. |
| `DSB-SC-003` | **N/A** | Jenkins provides no native provenance attestation mechanism. Recorded as a platform limitation rather than an engineering choice — `DSB-BUILD-003` and `DSB-ART-004` carry the traceability burden instead. |

---

## 6. Gaps — what you are missing

Ordered by risk.

### Gap 1 — No secret scanning (`DSB-SCAN-004`, BLOCK)

Your three products cover code, dependencies, and images. **None of them scans for
committed credentials.** This is the most common gap in an otherwise mature enterprise
toolchain, because the expensive products create a sense of coverage that does not extend
here.

`DSB-SCAN-004` is one of only two scan rules that is `always: true` — it carries no
technology condition, because every repository can leak a credential regardless of what
it builds.

*Needs:* a secret-scanning capability covering both incoming changes and existing
history. History matters — a secret deleted in a later commit is still live.

### Gap 2 — No DAST or API security testing (`DSB-SCAN-009`, WARN)

Java services on OpenShift expose HTTP interfaces. Nothing in your stack tests them at
runtime.

*Needs:* DAST against a **pre-production** environment, triggered by
`DSB-DEPLOY-004` after deployment.

> Active DAST against production requires explicit, documented organizational
> authorization. Do not schedule it against production without that authorization in
> hand.

### Gap 3 — Jenkins pipeline configuration is unscanned (`DSB-SCAN-008`, WARN)

Your Jenkinsfiles are code with credentials to Artifactory and OpenShift, and they are
outside the scope of every scanner you own. Check specifically for: credentials bound at
pipeline scope rather than stage scope, unpinned shared-library references, and
`sh` steps interpolating values from SCM-controlled input.

### Gap 4 — Verify `DSB-DEPLOY-002` compliance

Confirm the OpenShift deployment references the image **digest** that Prisma scanned, not
a mutable tag. If OpenShift resolves `:latest` or a moving tag at deploy time, every scan
result you hold describes an image you may not be running.

---

## 7. Rationale

**Why no new products.** You already own capability for five of the required controls.
`DSB-SCAN-010` makes the minimum sufficient toolchain a requirement, not a preference:
duplicate scanners multiply triage cost and slow the pipeline until teams start routing
around it — which costs more security than the second scanner ever provided. Your gaps
are all in capabilities nobody sold you, which is exactly where mature toolchains leak.

**Why secret scanning ranks first.** It is the only gap where the risk is live from the
moment of commit, needs no attacker sophistication, and is not remediated by the fix
that appears to remediate it. SAST and SCA findings are potential; a committed credential
is actual.

**Why manifest scanning stays even though admission enforces it.** Admission control is
the correct enforcement point and stays that way. The pre-merge scan is a feedback
control — the same finding, ten minutes earlier, at WARN. Different placement, different
purpose, and not a `DSB-SCAN-010` duplication because only one of the two gates.

**Why enforcement is not uniform.** SAST and SCA BLOCK because findings are actionable
and remediation exists. DAST WARNs because it is slow and noisy against a pre-production
environment that may not fully represent production. Uniform BLOCK gates on noisy
controls are how pipelines acquire `continue-on-error` — an undocumented, unapproved,
unexpiring exception (`DSB-EXC-001`).

---

## 8. Curriculum pointers

- DevSecOps Foundations — the Build → Test → Scan → Deploy model and why testing and
  scanning are separate phases
- Pipeline Security — CI/CD as production infrastructure and its own attack surface
- Secrets Management — why history scanning is not optional and rotation is the only
  real remediation
- Container Security — image scanning placement, and build-time vs. registry scanning
- Kubernetes Security — admission control as an enforcement point and ownership
  boundaries between platform and application teams
