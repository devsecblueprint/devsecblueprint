# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) — with the
Pre-1.0 caveat stated under v0.1.0 below.

---

## [Unreleased]

### Planned

- Direct links from individual rules to the DSB curriculum modules they correspond to
- Additional examples across further platforms and stacks (Azure DevOps, serverless)
- Evaluation prompts exercising each operating mode

---

## [0.1.0] — 2026-08-16

Initial release.

### Added

- **Skill definition** (`SKILL.md`) — the Build → Test → Scan → Deploy methodology, three
  operating modes (Advise, Design/Generate, Review), the 20 Baseline DSB Engineering
  Principles, the workload context checklist, the control selection algorithm, and the
  output contract
- **Rule catalog** — 42 rules across 11 families, each carrying the full schema:
  `id`, `title`, `phase`, `requirement`, `rationale`, `applicability`,
  `framework_mappings`, `enforcement.level`, `enforcement.automatable`,
  `tooling.examples`, `tooling.prefer_existing_tool`

  | Family | Rules | Scope |
  |---|---:|---|
  | `DSB-BUILD-*` | 4 | Build and artifact creation |
  | `DSB-TEST-*` | 3 | Testing |
  | `DSB-SCAN-*` | 10 | Security scanning and validation |
  | `DSB-DEPLOY-*` | 4 | Deployment and promotion |
  | `DSB-ID-*` | 3 | Workload identity, authentication, authorization |
  | `DSB-SRC-*` | 3 | Source control and repository security |
  | `DSB-SC-*` | 3 | Software supply chain security |
  | `DSB-ART-*` | 4 | Artifacts, provenance, signing, registries |
  | `DSB-IAC-*` | 3 | Infrastructure-as-code security |
  | `DSB-EVD-*` | 3 | Evidence, logging, observability |
  | `DSB-EXC-*` | 2 | Exceptions and risk acceptance |

- **Command entry points** — `/devsecops-engineer:advise`, `:design`, `:assess`, plus
  `.claude-plugin/plugin.json`. Commands are thin wrappers over the skill; a
  commands-stay-thin policy is documented in `CONTRIBUTING.md` to prevent drift
- **Reference documentation** — `applicability.md` (five-step selection flow),
  `capability-catalog.md` (capability → condition → placement → owning rule),
  `enforcement-model.md` (BLOCK / WARN / REPORT / N/A and the exception path),
  `framework-mappings.md` (NIST SSDF, SLSA, OWASP CI/CD, OWASP SAMM, CNCF)
- **Worked examples** — Advise (Jenkins/Java/OpenShift enterprise), Generate (GitHub
  Actions/Node/container to EKS; GitLab CI/Terraform), Review (Jenkinsfile assessment
  with compliant, non-compliant, and Not Applicable findings)
- **Validation** — `scripts/validate_rules.py` checking required schema fields, family
  ID prefixes, ID uniqueness, allowed phases, enforcement levels, framework mapping keys,
  tooling flags, and per-family rule counts
- **CI** — `.github/workflows/validate.yml` running catalog validation, secret scanning
  (`DSB-SCAN-004`), and workflow configuration scanning (`DSB-SCAN-008`) on every push
  and pull request
- **Project documentation** — README as a product-oriented front door, `CONTRIBUTING.md`,
  `MAINTAINERS.md`, `SECURITY.md`, MIT `LICENSE`, and `docs/legal/TRADEMARKS.md`

### Pre-1.0 notice

This is an **initial release and the catalog's shape is not final.** Before 1.0, expect:

- New rules and new families as the taxonomy is refined
- Changes to enforcement defaults and applicability conditions
- Restructuring of reference documentation

**Rule IDs are stable from this release onward.** A withdrawn rule is deprecated, never
renumbered, and its ID is never reused — so a pipeline annotated with `DSB-SCAN-003`
means the same thing in every future version. This is the compatibility guarantee that
matters, because rule IDs travel into other organizations' pipelines, review findings,
and exception records.

Compliance framework mapping (SOC 2, PCI DSS, FedRAMP, HIPAA) is deferred by design.
Compliance is not this methodology's driver.

### Licensing

Released under the **MIT License**. No commercial authorization is required to use,
modify, or distribute this implementation. DSB branding, trademarks, and curriculum
remain outside the MIT grant — see `docs/legal/TRADEMARKS.md`.

[Unreleased]: https://github.com/devsecblueprint/devsecops-claude-skill/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/devsecblueprint/devsecops-claude-skill/releases/tag/v0.1.0
