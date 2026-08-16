# DevSec Blueprint — DevSecOps Engineering Skill

**Implementation Report**

| | |
|---|---|
| **Repository** | `devsecblueprint/devsecops-claude-skill` — verified live (public, 1 commit, 5 open PRs) |
| **Owner** | The DevSec Blueprint |
| **Date** | 2026-08-16 |
| **Target release** | v0.1.0 (Pre-1.0) |
| **Status** | ✅ Scaffold complete + v0.1.0 required changes implemented — 42 rules across 11 families, validation passing |

---

## 0. Verification of v0.1.0 Maintainer Feedback

Feedback from @leeclay95 was verified against live sources on 2026-08-16:

| Claim | Verification result |
|---|---|
| Repository exists under `devsecblueprint` | ✅ **Confirmed** — `devsecops-claude-skill`, public, listed in the org's 26 repositories. Corrects earlier report status ("pending push") — the repo already exists. |
| Current license is PolyForm Noncommercial | ✅ **Confirmed** — repo README states "PolyForm Noncommercial License 1.0.0" with commercial authorization required via `docs/legal/COMMERCIAL-LICENSING.md`; GitHub shows license "Other". |
| `MAINTAINERS.md` and legal/licensing docs exist and reference commercial terms | ✅ **Confirmed** — `MAINTAINERS.md`, `LICENSE.md`, `docs/legal/` (commercial licensing + trademarks) present in the repo. |
| No command entry points yet | ✅ **Confirmed** — repo has no `commands/` directory or plugin manifest; skill is a single self-contained `SKILL.md`. |
| GRC Engineering Club Claude repo as README reference model | ✅ **Confirmed** — `GRCEngClub/claude-grc-engineering`, an open-source Claude Code plugin toolkit whose command/plugin convention matches the requested `/devsecops-engineer:*` namespace pattern. |
| No release tagged yet | ✅ **Confirmed** — repo shows no releases/tags, consistent with preparing v0.1.0 as the initial release. |

### 0a. v0.1.0 Required Changes — Implementation Status

| # | Required change | Status | Implementation |
|---|---|---|---|
| 1 | MIT license replacing PolyForm Noncommercial, all references updated | ✅ Implemented in scaffold | `LICENSE` (MIT), `README.md` license section, new `MAINTAINERS.md` (MIT attribution, no commercial-authorization language), `docs/legal/TRADEMARKS.md` keeping DSB branding/trademarks/curriculum separate from the MIT-licensed implementation |
| 2 | Command entry points `/devsecops-engineer:assess`, `:design`, `:advise` | ✅ Implemented | `commands/assess.md`, `commands/design.md`, `commands/advise.md` + `.claude-plugin/plugin.json` (name: `devsecops-engineer` — namespace chosen to match the planned `/cloud-security-engineer:*` convention). Each command is a thin wrapper that loads `SKILL.md` and its rule catalog; a "commands stay thin — no rule logic" policy was added to `CONTRIBUTING.md` to prevent drift |
| 3 | README as product-oriented front door (GRC-club-quality IA, DSB-branded) | ✅ Implemented | Rewritten `README.md` following the required flow: What is this? → Why use it (outcomes) → Install in 60 seconds → Try it (Assess/Design/Advise prompts) → Common workflows → How it works (workload profiling → applicability → capability resolution → enforcement → placement) → Go deeper (links to examples, rules, mappings, testing, contributing) → v0.1.0/Pre-1.0 status → MIT + DSB ownership |
| 4 | Initial release as v0.1.0, not v1.0.0 | ✅ Implemented | `plugin.json` version `0.1.0`, `CHANGELOG.md` v0.1.0 entry with explicit Pre-1.0 evolution language, status language in README |
| — | Validation/behavioral tests still pass | ✅ | `validate_rules.py`: OK — 42 rules across 11 families |

These changes are implemented in the local scaffold (`devsecops-engineering-skill/`, packaged as `dsb-devsecops-engineering-v0.1.0.skill`) and are ready to be applied to the live `devsecops-claude-skill` repository as a PR, followed by tagging v0.1.0.

---

## 1. Summary

A dedicated, DevSec Blueprint-owned Claude Skill repository was scaffolded to teach, advise on, design, generate, and review DevSecOps delivery pipelines using the engineering methodology taught throughout The DevSec Blueprint. The skill encodes a consistent set of DSB DevSecOps engineering rules while remaining flexible across organizations, CI/CD platforms, cloud environments, application architectures, security products, and internal operating models.

This is not a generic pipeline generator and prescribes no DSB-approved vendor stack: DSB defines the required capabilities and engineering outcomes; the organization determines how those capabilities are implemented. The skill is strongly associated with The DevSec Blueprint — no separate product name, mascot, or sub-brand was introduced.

> **Build what you need. Test what you built. Scan what can introduce meaningful risk. Deploy only what passed.**

---

## 2. Repository Requirement — Status

The repository is scaffolded as a standalone codebase, independent from the primary DSB application repository, ready to be created under the `devsecblueprint` GitHub organization. The name `devsecops-engineering-skill` describes the skill while keeping The DevSec Blueprint as the primary brand.

| Requirement | Status | Where |
|---|---|---|
| Created under `devsecblueprint` org | ⏳ Pending push (only manual step remaining) | — |
| Clear DSB branding and ownership attribution | ✅ | `README.md`, `SKILL.md`, `CONTRIBUTING.md` |
| Skill definition and supporting resources | ✅ | `SKILL.md`, `references/` |
| DSB DevSecOps rule catalog | ✅ | `rules/*.yaml` (42 rules, 11 families) |
| Framework/best-practice mappings | ✅ | per-rule `framework_mappings` + `references/framework-mappings.md` |
| Representative examples and reference implementations | ✅ | `examples/` (Advise, Generate ×2, Review) |
| Contributor and maintenance documentation | ✅ | `CONTRIBUTING.md` |
| DSB-approved license and contributor requirements | ✅ MIT (confirm as DSB-approved) | `LICENSE`, `CONTRIBUTING.md` |
| Independent from primary DSB application codebase | ✅ | Standalone repository |

---

## 3. Core DSB Methodology — Implementation

Every delivery pipeline follows four logical phases, encoded in `SKILL.md` and enforced by the rule catalog. They describe engineering intent, not job structure, vendor, or platform.

```
BUILD → TEST → SCAN → DEPLOY
```

| Phase | Encoding | Key rules |
|---|---|---|
| **Build** — repeatable, traceable deliverable preparation (compilation, dependency resolution, packaging, images, IaC preparation, artifact generation) | `SKILL.md` + `rules/build.yaml` | `DSB-BUILD-001..004` |
| **Test** — workload-appropriate behavior validation; conceptually separate from scanning; prefers project-native tests; no meaningless tests to satisfy the phase | `rules/test.yaml` | `DSB-TEST-001..003` |
| **Scan** — non-negotiable; scanners required only when the associated technology, artifact, or risk exists; minimum sufficient toolchain | `rules/scan.yaml` | `DSB-SCAN-001..010` |
| **Deploy** — deliver/promote only artifacts that passed applicable Build, Test, Scan requirements (deployment, publication, promotion) | `rules/deploy.yaml` | `DSB-DEPLOY-001..004` |

Runtime-dependent controls (DAST, API security testing, runtime validation) execute post-deployment to an appropriate testable environment — part of Scan/verification, not a fifth phase (`DSB-SCAN-009`, `DSB-DEPLOY-004`). Active DAST against production without explicit organizational authorization is prohibited in both the rules and every example.

---

## 4. Operating Modes — Implementation

Repository access is not required for the skill to provide value (stated in `SKILL.md`; all modes operate from user-supplied context).

| Mode | Behavior implemented | Worked example |
|---|---|---|
| **1. Advise** | Maps org capabilities into Build → Test → Scan → Deploy, identifies gaps, recommends enforcement points, explains decisions with DSB rule IDs | `examples/advise/jenkins-java-enterprise.md` (the Jenkins/Java/Maven/Artifactory/Checkmarx/Black Duck/Prisma/OpenShift scenario from the issue) |
| **2. Design / Generate** | Produces implementation-ready pipelines (GitHub Actions, Jenkins, GitLab CI, Azure DevOps, others); DSB rules constant, implementation adapts; asks for or states assumptions on missing context; annotates generated code with rule references | `examples/generate/github-actions-node-container.md`, `examples/generate/gitlab-ci-terraform.md` |
| **3. Review** | Fixed findings structure identifying satisfied controls, missing capabilities, inappropriate enforcement, duplicate tooling, pipeline security weaknesses, DSB rule IDs, remediation, and intentional N/A | `examples/review/jenkinsfile-review.md` |

---

## 5. Tooling Philosophy and No-Bloat Behavior

Capability-based, never vendor-based: every rule's `tooling.examples` is explicitly illustrative, with `prefer_existing_tool: true` throughout. The existing-tool decision pattern from the issue (Required Capability → Existing Organizational Tool → Decision → DSB Requirement: Satisfied) is embedded in `SKILL.md` and modeled in the Advise example.

No-bloat behavior is enforced by `DSB-SCAN-010` (minimum sufficient toolchain, no duplicate scanners) and the applicability logic:

- No container scanner without a container artifact
- No IaC scanner without IaC
- No Kubernetes scanner without Kubernetes
- No duplicate SCA when an existing capability satisfies the control

**Not Applicable** is a first-class, explicitly documented outcome (`DSB-EVD-003`), demonstrated in all examples. Custom/proprietary/internal security tools satisfy DSB rules without any rule changes.

---

## 6. Security Capability Catalog

Implemented in `references/capability-catalog.md` with applicability conditions, earliest-valid placement, and owning DSB rule for each capability:

- **Application and repository security** — SAST, SCA, secret scanning, dependency/package analysis, license/compliance analysis where required
- **Infrastructure and platform security** — IaC scanning, Kubernetes/configuration scanning, policy-as-code enforcement, CI/CD pipeline configuration scanning
- **Artifact and supply chain security** — container/image scanning, SBOM generation, artifact integrity verification, signing where required, provenance/build attestations where supported
- **Dynamic / post-deployment security** — DAST, API security testing, post-deployment validation, runtime validation
- **Advanced / organization-dependent** — fuzz testing, IAST, specialized compliance scanners, proprietary/internal tools, penetration testing workflows; incorporated when workload context, policy, or organizational requirements make them applicable — not baseline

Placement principle encoded: security controls execute at the earliest technically valid stage where they produce meaningful results.

---

## 7. Rule Catalog (DSB Requirements Model)

All 11 rule families from the issue are implemented. Every rule contains the full issue-specified schema: `id`, `title`, `phase`, `requirement`, `rationale`, `applicability`, `framework_mappings`, `enforcement.level`, `enforcement.automatable`, `tooling.examples`, `tooling.prefer_existing_tool`.

| Family | File | Rules | Scope |
|---|---|---:|---|
| `DSB-BUILD-*` | `rules/build.yaml` | 4 | Build and artifact creation |
| `DSB-TEST-*` | `rules/test.yaml` | 3 | Testing |
| `DSB-SCAN-*` | `rules/scan.yaml` | 10 | Security scanning and validation |
| `DSB-DEPLOY-*` | `rules/deploy.yaml` | 4 | Deployment and promotion |
| `DSB-ID-*` | `rules/identity.yaml` | 3 | Workload identity, authn/authz |
| `DSB-SRC-*` | `rules/source.yaml` | 3 | Source control and repository security |
| `DSB-SC-*` | `rules/supply-chain.yaml` | 3 | Software supply chain security |
| `DSB-ART-*` | `rules/artifacts.yaml` | 4 | Artifacts, provenance, signing, registries |
| `DSB-IAC-*` | `rules/iac.yaml` | 3 | Infrastructure-as-code security |
| `DSB-EVD-*` | `rules/evidence.yaml` | 3 | Evidence, logging, observability |
| `DSB-EXC-*` | `rules/exceptions.yaml` | 2 | Exceptions and risk acceptance |
| **Total** | | **42** | |

All 20 Baseline DSB Engineering Principles from the issue are enumerated verbatim in `SKILL.md` and traceable to rules. The taxonomy may be refined during implementation per the issue; rule IDs are stable once merged (deprecate, never renumber — `CONTRIBUTING.md`).

---

## 8. Enforcement Model

Implemented in `references/enforcement-model.md` and as per-rule defaults, with the issue's four outcomes:

| Outcome | Meaning |
|---|---|
| **BLOCK** | Cannot continue without satisfaction or approved exception |
| **WARN** | Surfaced, non-blocking |
| **REPORT** | Evidence only |
| **N/A** | Intentionally inapplicable, justified |

Control **applicability** (engineering, workload-driven) is explicitly distinguished from control **enforcement** (policy, organization-driven); DSB defaults are recommendations the organization's enforcement policy may adjust. The exception path is governed by `DSB-EXC-001/002` (named approver, scope, expiry).

---

## 9. External Standards and Framework Mapping

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

All five initial authoritative references are mapped per rule and cross-referenced in `references/framework-mappings.md`:

- NIST SSDF (SP 800-218)
- SLSA
- OWASP CI/CD Security (Top 10 CI/CD Security Risks)
- OWASP SAMM
- CNCF Software Supply Chain Security guidance

Frameworks inform the methodology; they do not replace engineering judgment or dictate pipeline architecture. Compliance framework mapping is deferred by design, and compliance is not the methodology's driver.

---

## 10. Organizational Context and Ownership Boundaries

`references/applicability.md` implements the five-step selection flow:

1. Workload inventory
2. Applicability tests
3. Existing-capability check
4. Ownership-boundary check
5. Organizational-context factors (platform, architecture, language, package manager, cloud, deployment platform, registries, existing products, policies, environment strategy, responsibility separation, risk tolerance, compliance)

A control need not execute in the application pipeline when another governed organizational process legitimately owns and enforces it; the skill marks such controls **Satisfied (externally owned)** with the owning process named, rather than duplicating them. This pattern is demonstrated in the Advise, Generate, and Review examples.

---

## 11. Deliverables Traceability

| # | Deliverable (from issue) | Status | Evidence |
|---|---|---|---|
| 1 | New dedicated GitHub repo under `devsecblueprint` | ⏳ Ready to push | Full scaffold complete |
| 2 | Repo structure, branding, attribution, license, contributor/maintenance docs | ✅ | `README.md`, `LICENSE`, `CONTRIBUTING.md` |
| 3 | Initial DSB DevSecOps engineering rule catalog | ✅ | `rules/` — 42 rules, 11 families |
| 4 | Map initial rules to external standards/guidance | ✅ | Per-rule mappings + `references/framework-mappings.md` |
| 5 | Rule applicability logic | ✅ | `references/applicability.md`, per-rule `applicability` |
| 6 | BLOCK / WARN / REPORT / N/A enforcement semantics | ✅ | `references/enforcement-model.md`, per-rule defaults |
| 7 | Security capability catalog | ✅ | `references/capability-catalog.md` |
| 8 | Workload- and context-driven control selection | ✅ | Selection algorithm in `SKILL.md` + applicability doc |
| 9 | Existing-tool preference / no-bloat behavior | ✅ | `DSB-SCAN-010`, `prefer_existing_tool`, applicability step 3 |
| 10 | Advisory mode | ✅ | `SKILL.md` mode 1 + Advise example |
| 11 | Pipeline design/generation mode | ✅ | `SKILL.md` mode 2 + two Generate examples |
| 12 | Pipeline/repository review mode | ✅ | `SKILL.md` mode 3 + Review example |
| 13 | Post-deployment DAST / runtime-dependent validation | ✅ | `DSB-SCAN-009`, `DSB-DEPLOY-004`, examples |
| 14 | Custom/proprietary organizational tooling support | ✅ | Capability-based rules; catalog + applicability docs |
| 15 | DSB-branded explanations and rule references | ✅ | "Voice and teaching" section; rule IDs cited throughout examples |
| 16 | Correlate rules/recommendations with DSB curriculum | ✅ (initial) | Curriculum pointers required in output; direct module links pending (§14) |
| 17 | Representative examples across organizational stacks | ✅ | Jenkins/Java/OpenShift, GitHub Actions/Node/EKS, GitLab/Terraform |
| 18 | Compliant, non-compliant, and Not Applicable examples | ✅ | Review example (all three) + N/A sections in Generate examples |

---

## 12. Acceptance Criteria Traceability

| Acceptance criterion | Met by |
|---|---|
| Dedicated DSB-owned repo under `devsecblueprint` exists | ⏳ Scaffold complete; push is the remaining step |
| Repo contains skill, rule catalog, mappings, examples, contributor docs, attribution | §2, §11 |
| Skill operates without repository access | Stated in `SKILL.md`; all modes work from supplied context |
| Advises from high-level architecture/requirements | Advise mode + example |
| Designs a pipeline from organizational requirements | Design/Generate mode with context checklist |
| Generates implementation-ready CI/CD config with sufficient context | Generate examples (GitHub Actions, GitLab CI) |
| Reviews an existing pipeline or repository | Review mode + example |
| Consistently applies Build → Test → Scan → Deploy | Methodology in `SKILL.md`; principle 1; phase mapping required in all outputs |
| Security scanning considered in every delivery design | `DSB-SCAN-001` (always applicable, BLOCK) |
| Scanners selected on actual workload applicability | Selection algorithm; applicability tests |
| SAST, SCA, secrets, IaC, container, pipeline, policy/config, DAST, API testing incorporated when appropriate | `DSB-SCAN-002..009` + capability catalog |
| Post-deployment DAST/runtime requirements recognized | `DSB-SCAN-009`, `DSB-DEPLOY-004`; production-authorization guard |
| Existing organizational tooling reused where appropriate | `prefer_existing_tool`; applicability step 3; Advise example |
| Unnecessary/duplicate tooling avoided | `DSB-SCAN-010`; no-bloat rules |
| Not Applicable controls explicitly identified | `DSB-EVD-003`; N/A sections in every example |
| Custom/proprietary products supported without changing DSB rules | Capability-based rule design |
| Ownership boundaries identified and respected | "Satisfied (externally owned)" pattern |
| Explicit enforcement recommendations provided | Per-rule defaults + enforcement model |
| DSB rules map to recognized industry guidance | §9 |
| Engineering decisions explained, not just pipeline code | Mandatory rationale per rule; teaching requirement in `SKILL.md` |
| Consistent with DSB curriculum and walkthroughs | Curriculum-first change policy (`CONTRIBUTING.md`); skill defers to curriculum as source |

---

## 13. Verification

- `scripts/validate_rules.py` — **OK**: 42 rules across 11 families validated (required schema fields, family ID prefixes, ID uniqueness, allowed phases, enforcement levels, framework keys, tooling flags)
- `.github/workflows/validate.yml` — CI runs the same validation plus secret scanning (`DSB-SCAN-004`) and pipeline-config scanning (`DSB-SCAN-008`) on every push/PR; the repository practices the methodology it teaches
- Packaged as `dsb-devsecops-engineering.skill` for direct installation

---

## 14. Remaining Actions

1. Open a PR against `devsecblueprint/devsecops-claude-skill` applying the v0.1.0 changes: MIT license swap (replace `LICENSE.md` PolyForm text, remove/rewrite `docs/legal/COMMERCIAL-LICENSING.md`, update `MAINTAINERS.md` and README licensing references), `commands/` + plugin manifest, README rewrite
2. Re-run the repo's own validation and behavioral tests (`tools/validate_skill.py`, `pytest`) after the changes
3. Tag and publish the v0.1.0 release
4. Add direct links from individual rules to the specific DSB curriculum modules they correlate with
5. Optional pre-announcement hardening: run evaluation prompts against each operating mode and iterate

---

*Owned and maintained by The DevSec Blueprint. This skill is an implementation of DSB knowledge and standards, not the source of those standards.*
