# Security Capability Catalog

Capabilities, not products. Each entry states the condition that makes the capability
applicable, the earliest stage at which it produces meaningful results, and the DSB rule
that owns it.

Tool names throughout are **illustrative**. Naming a product confers no DSB endorsement
and creates no requirement to adopt it. A custom, proprietary, or internal tool satisfies
the capability identically (`tooling.prefer_existing_tool: true` on every rule).

---

## 1. Application and repository security

| Capability | Applicable when | Earliest valid placement | Owning rule |
|---|---|---|---|
| **Static application security testing (SAST)** | First-party source code exists in a supported language | On the change, pre-merge — needs only source | `DSB-SCAN-002` |
| **Software composition analysis (SCA)** | Any third-party dependency is resolved | After dependency resolution — needs the resolved graph | `DSB-SCAN-003` |
| **Secret scanning** | A source repository exists (always) | On the change, pre-merge, plus full history | `DSB-SCAN-004` |
| **Dependency / package integrity** | Dependencies resolve from an external source | During resolution, in Build | `DSB-BUILD-002` |
| **License and compliance analysis** | Organizational policy or distribution model requires it | Alongside SCA | `DSB-SCAN-003` |

*Illustrative:* Checkmarx, Semgrep, SonarQube, CodeQL, Fortify · Black Duck, Snyk,
Dependabot, Trivy, OWASP Dependency-Check · Gitleaks, TruffleHog, platform-native secret
scanning.

**Placement note:** SCA before dependency resolution scans a manifest, not a dependency
graph, and misses the transitive majority. This is the single most common placement
error.

---

## 2. Infrastructure and platform security

| Capability | Applicable when | Earliest valid placement | Owning rule |
|---|---|---|---|
| **IaC scanning** | The repository contains infrastructure-as-code | On the change, pre-merge — needs only the definitions | `DSB-SCAN-006` |
| **Kubernetes / workload config scanning** | Kubernetes manifests, charts, or overlays exist | On the change; re-evaluate rendered output if templated | `DSB-SCAN-007` |
| **Policy-as-code enforcement** | The organization maintains policy as code | Pre-merge on definitions, and at admission for defense in depth | `DSB-SCAN-007`, `DSB-IAC-002` |
| **Plan / change-set review** | IaC applies to a shared or production environment | After plan generation, before apply | `DSB-IAC-002` |
| **CI/CD pipeline configuration scanning** | Pipeline definitions live in the repository | On the change, pre-merge | `DSB-SCAN-008` |

*Illustrative:* Checkov, tfsec, Terrascan, Trivy config, Prisma Cloud IaC · Kubescape,
Datree · OPA/Gatekeeper, Kyverno, Sentinel · zizmor, octoscan.

**Placement note:** for templated Kubernetes (Helm, Kustomize), scan the *rendered*
output. Scanning the template alone misses everything values files introduce.

---

## 3. Artifact and supply chain security

| Capability | Applicable when | Earliest valid placement | Owning rule |
|---|---|---|---|
| **Container / image scanning** | A container image is built or published | After image build, before publication | `DSB-SCAN-005` |
| **SBOM generation** | A released artifact contains third-party components | At build, when the resolved set is known | `DSB-SC-001` |
| **Third-party component pinning** | The pipeline consumes actions, plugins, modules, or base images | In the pipeline definition itself | `DSB-SC-002` |
| **Artifact integrity verification** | Artifacts move between stages or systems | Before consumption or deployment | `DSB-DEPLOY-002`, `DSB-ART-002` |
| **Artifact signing** | Policy or cross-boundary distribution requires it | At publication; verify before deploy | `DSB-ART-003` |
| **Provenance / build attestation** | The platform supports generation | At build; verify before deploy | `DSB-SC-003` |

*Illustrative:* Prisma Cloud, Trivy, Grype, Clair, registry-native scanning · Syft,
cdxgen, CycloneDX and SPDX tooling · Sigstore Cosign, in-toto, Notary.

**Placement note:** an SBOM generated after publication describes an artifact you have
already shipped. Generate at build; attach at publication.

---

## 4. Dynamic and post-deployment security

| Capability | Applicable when | Earliest valid placement | Owning rule |
|---|---|---|---|
| **DAST** | A network-reachable interface exists and a testable environment is available | After deployment to an authorized environment | `DSB-SCAN-009` |
| **API security testing** | An API is exposed, ideally with a specification | After deployment to an authorized environment | `DSB-SCAN-009` |
| **Post-deployment validation** | Any deployment to a testable environment occurs | Immediately after deploy | `DSB-DEPLOY-004` |
| **Runtime validation** | Runtime behavior is in scope for the organization | Continuous, post-deployment | `DSB-SCAN-009` |

*Illustrative:* OWASP ZAP, Burp Suite Enterprise, Invicti, StackHawk.

> **Production authorization.** Active dynamic testing against production requires
> explicit, documented organizational authorization. Without it, do not generate it and
> do not recommend it. Active scanning is operationally indistinguishable from an attack
> and can cause real outages and real data mutation.

**Not a fifth phase.** These execute after Deploy but belong to Scan/verification.

---

## 5. Advanced and organization-dependent

Incorporated when workload context, policy, or organizational requirements make them
applicable. **Not baseline** — do not propose them by default, and do not treat their
absence as a gap.

| Capability | Consider when |
|---|---|
| **Fuzz testing** | The workload parses untrusted input at a boundary — protocols, file formats, deserialization |
| **Interactive application security testing (IAST)** | Instrumented runtime is acceptable and a rich integration test suite already exists |
| **Specialized compliance scanners** | A specific regime obliges it (payment, health, government) |
| **Proprietary / internal tools** | The organization has built capability of its own — satisfies rules identically |
| **Penetration testing workflows** | Policy, release cadence, or contract requires human-led assessment |

---

## Placement summary

```
PRE-MERGE (on the change)
  ├─ Secret scanning                    DSB-SCAN-004   always
  ├─ SAST                               DSB-SCAN-002   if first-party code
  ├─ IaC scanning                       DSB-SCAN-006   if IaC
  ├─ K8s / config scanning              DSB-SCAN-007   if K8s
  └─ Pipeline config scanning           DSB-SCAN-008   if pipeline-as-code

BUILD
  ├─ Dependency integrity               DSB-BUILD-002  if dependencies
  ├─ SCA (post-resolution)              DSB-SCAN-003   if dependencies
  ├─ SBOM generation                    DSB-SC-001     if released artifact
  └─ Provenance / attestation           DSB-SC-003     if platform supports

POST-BUILD, PRE-PUBLISH
  ├─ Container / image scanning         DSB-SCAN-005   if image built
  └─ Artifact signing                   DSB-ART-003    if policy requires

PRE-DEPLOY
  ├─ Gate verification                  DSB-DEPLOY-001 always
  ├─ Digest-pinned promotion            DSB-DEPLOY-002 if artifact promoted
  └─ Signature / provenance verification DSB-ART-003   if signed

POST-DEPLOY (authorized environment only)
  ├─ Deployment verification            DSB-DEPLOY-004 if environment exists
  ├─ DAST                               DSB-SCAN-009   if runtime interface
  └─ API security testing               DSB-SCAN-009   if API exposed
```
