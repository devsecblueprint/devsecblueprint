# Framework Mappings

DSB rules are cross-referenced against five authoritative external references. Each rule
in `rules/*.yaml` carries a `framework_mappings` block with all five keys; an empty list
means the rule has no meaningful correspondence in that framework, which is a legitimate
and common outcome.

```
Industry Standards / Best Practices
              ↓
DSB DevSecOps Engineering Methodology
              ↓
DSB Rules
              ↓
Organizational Context
              ↓
Platform / Tool Implementation
```

**Frameworks inform the methodology. They do not replace engineering judgment and they
do not dictate pipeline architecture.** A rule exists because it is sound engineering,
not because a framework lists it — the mapping documents the correspondence, it does not
justify the rule.

**Compliance mapping is deferred by design.** Compliance regimes (SOC 2, PCI DSS,
FedRAMP, HIPAA) are not the driver of this methodology and are not mapped in v0.1.0.
Where an organization needs that traceability, the framework mappings below are the
bridge — most regimes already map to NIST SSDF.

---

## The five references

| Key | Reference | What it contributes |
|---|---|---|
| `nist_ssdf` | NIST SP 800-218, Secure Software Development Framework | Practice-level coverage across the whole lifecycle — the broadest mapping surface |
| `slsa` | Supply-chain Levels for Software Artifacts | Build integrity and provenance, expressed as progressive levels |
| `owasp_cicd` | OWASP Top 10 CI/CD Security Risks | The pipeline itself as attack surface |
| `owasp_samm` | OWASP Software Assurance Maturity Model | Organizational maturity and process ownership |
| `cncf_supply_chain` | CNCF Software Supply Chain Security guidance | Cloud-native supply chain, from source through deployment |

---

## NIST SSDF (SP 800-218)

Referenced by practice identifier. The four groups:

| Group | Meaning | DSB families drawing on it |
|---|---|---|
| **PO** — Prepare the Organization | People, process, and toolchain readiness | `DSB-ID`, `DSB-SRC`, `DSB-EXC`, `DSB-IAC` |
| **PS** — Protect the Software | Integrity and protection of code and artifacts | `DSB-ART`, `DSB-SC`, `DSB-BUILD`, `DSB-DEPLOY` |
| **PW** — Produce Well-Secured Software | Design, build, and verification practices | `DSB-BUILD`, `DSB-TEST`, `DSB-SCAN` |
| **RV** — Respond to Vulnerabilities | Identification, remediation, and root cause | `DSB-SCAN`, `DSB-EVD`, `DSB-EXC` |

SSDF is the widest mapping in the catalog because it is the only one of the five that
covers organizational preparation, production, and response together.

---

## SLSA

Referenced by track and level rather than by control ID.

| Reference used | DSB correspondence |
|---|---|
| Build L1 — scripted build | `DSB-BUILD-001`, `DSB-SRC-001`, `DSB-IAC-001` |
| Build L2 — hosted build platform, signed provenance | `DSB-BUILD-001`, `DSB-BUILD-004`, `DSB-ID-001`, `DSB-EVD-002` |
| Build L3 — hardened, isolated builds, non-falsifiable provenance | `DSB-BUILD-004`, `DSB-ID-002`, `DSB-SC-002`, `DSB-SC-003` |
| Provenance — available / authenticated / verified | `DSB-SC-003`, `DSB-ART-002`, `DSB-ART-003`, `DSB-DEPLOY-002` |

DSB does not require a specific SLSA level. The mapping tells an organization which DSB
rules move it up the track — the level target is theirs to set.

---

## OWASP Top 10 CI/CD Security Risks

The only one of the five that treats the pipeline itself as the target.

| Risk | DSB rules addressing it |
|---|---|
| CICD-SEC-1 Insufficient Flow Control Mechanisms | `DSB-DEPLOY-001`, `DSB-SRC-002`, `DSB-IAC-002`, `DSB-EXC-001`, `DSB-SCAN-001` |
| CICD-SEC-2 Inadequate Identity and Access Management | `DSB-ID-001`, `DSB-ID-002`, `DSB-SRC-003`, `DSB-DEPLOY-003`, `DSB-SCAN-008` |
| CICD-SEC-3 Dependency Chain Abuse | `DSB-BUILD-002`, `DSB-SCAN-003`, `DSB-SC-001`, `DSB-SC-002` |
| CICD-SEC-4 Poisoned Pipeline Execution | `DSB-BUILD-001`, `DSB-BUILD-004`, `DSB-SC-002`, `DSB-SCAN-008` |
| CICD-SEC-5 Insufficient PBAC | `DSB-ID-002`, `DSB-SRC-002`, `DSB-DEPLOY-003` |
| CICD-SEC-6 Insufficient Credential Hygiene | `DSB-SCAN-004`, `DSB-ID-001`, `DSB-ID-003`, `DSB-SRC-003`, `DSB-IAC-003`, `DSB-EVD-002` |
| CICD-SEC-7 Insecure System Configuration | `DSB-BUILD-004`, `DSB-SCAN-006`, `DSB-SCAN-007`, `DSB-SCAN-008`, `DSB-IAC-002`, `DSB-IAC-003` |
| CICD-SEC-8 Ungoverned Usage of Third Party Services | `DSB-BUILD-002`, `DSB-SC-002`, `DSB-SCAN-010` |
| CICD-SEC-9 Improper Artifact Integrity Validation | `DSB-BUILD-003`, `DSB-SCAN-005`, `DSB-SC-003`, `DSB-ART-001`, `DSB-ART-002`, `DSB-ART-003`, `DSB-DEPLOY-002` |
| CICD-SEC-10 Insufficient Logging and Visibility | `DSB-EVD-001`, `DSB-EVD-002`, `DSB-EVD-003`, `DSB-ART-004`, `DSB-EXC-002` |

Every one of the ten has at least one owning DSB rule. This is deliberate — Principle 16
holds that the pipeline is production infrastructure and in scope for its own security.

---

## OWASP SAMM

Mapped to business functions and security practices rather than specific activities,
because SAMM describes organizational maturity rather than pipeline mechanics.

| SAMM practice | DSB families |
|---|---|
| Governance — Strategy and Metrics | `DSB-SCAN-010`, `DSB-EVD-001` |
| Governance — Policy and Compliance | `DSB-SRC-003`, `DSB-EVD-003`, `DSB-EXC-001`, `DSB-EXC-002` |
| Implementation — Secure Build | `DSB-BUILD-*`, `DSB-SC-*`, `DSB-SRC-001`, `DSB-SRC-002` |
| Implementation — Secure Deployment | `DSB-DEPLOY-*`, `DSB-ART-*`, `DSB-IAC-002` |
| Verification — Requirements-driven Testing | `DSB-TEST-001`, `DSB-TEST-003` |
| Verification — Security Testing | `DSB-SCAN-001`–`DSB-SCAN-009`, `DSB-TEST-002` |
| Verification — Defect Management | `DSB-EXC-001`, `DSB-EXC-002` |
| Operations — Environment Management | `DSB-BUILD-004`, `DSB-ID-*`, `DSB-SCAN-006`, `DSB-SCAN-007`, `DSB-IAC-*` |
| Operations — Operational Management | `DSB-DEPLOY-003`, `DSB-DEPLOY-004`, `DSB-ART-004`, `DSB-EVD-001`, `DSB-EVD-002` |

---

## CNCF Software Supply Chain Security

Mapped to the guidance's five stages.

| Stage | DSB rules |
|---|---|
| Securing the Source Code | `DSB-SRC-001`, `DSB-SRC-002`, `DSB-SRC-003`, `DSB-SCAN-002`, `DSB-SCAN-004`, `DSB-SCAN-006` |
| Securing Materials | `DSB-BUILD-002`, `DSB-SCAN-003`, `DSB-SC-001`, `DSB-SC-002` |
| Securing Build Pipelines | `DSB-BUILD-001`, `DSB-BUILD-004`, `DSB-SCAN-001`, `DSB-SCAN-008`, `DSB-ID-*`, `DSB-SC-002`, `DSB-SC-003`, `DSB-EVD-001`, `DSB-EVD-002` |
| Securing Artefacts | `DSB-BUILD-003`, `DSB-SCAN-005`, `DSB-SC-001`, `DSB-SC-003`, `DSB-ART-001`, `DSB-ART-002`, `DSB-ART-003`, `DSB-ART-004`, `DSB-DEPLOY-002` |
| Securing Deployments | `DSB-DEPLOY-001`, `DSB-DEPLOY-003`, `DSB-DEPLOY-004`, `DSB-SCAN-007`, `DSB-SCAN-009`, `DSB-ART-003`, `DSB-IAC-001`, `DSB-IAC-002`, `DSB-IAC-003` |

---

## Using mappings in output

Cite a mapping when it helps the reader connect DSB guidance to an obligation they
already carry:

> `DSB-SC-002` (pin third-party actions to commit SHAs) addresses **CICD-SEC-3
> Dependency Chain Abuse** and **CICD-SEC-4 Poisoned Pipeline Execution**, and is a
> prerequisite for **SLSA Build L3**.

Do not lead with the framework. The engineering reason comes first; the mapping is
supporting evidence for a reader who needs it. A recommendation whose only justification
is "a framework says so" has failed Principle 20.
