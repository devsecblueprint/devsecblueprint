# DSB DevSecOps Engineering Skill

**A Claude Skill that designs, reviews, and explains DevSecOps delivery pipelines using
the engineering methodology taught throughout [The DevSec Blueprint](https://github.com/devsecblueprint).**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
![Status](https://img.shields.io/badge/status-v0.1.0%20Pre--1.0-orange?style=for-the-badge)
![Rules](https://img.shields.io/badge/rules-42%20across%2011%20families-blue?style=for-the-badge)

---

## What is this?

A packaged set of instructions that teaches Claude how a DevSecOps engineer actually
reasons about a delivery pipeline: which security controls a workload genuinely needs,
where each one belongs, what should block a release, and what should not be there at all.

It encodes **42 rules across 11 families** and a control-selection algorithm. It is
**capability-based, never vendor-based** — DSB defines the required capabilities and
engineering outcomes; your organization decides how to implement them.

**This is not a generic pipeline generator.** It will not hand you a template with every
scanner switched on. It works out what your workload is, and tells you what that workload
actually requires — including what it does not.

> Build what you need. Test what you built. Scan what can introduce meaningful risk.
> Deploy only what passed.

---

## Why use it

| Outcome | What that means in practice |
|---|---|
| **No tooling bloat** | No container scanner without a container. No IaC scanner without IaC. No second SCA tool when you already own one. |
| **Your existing tools count** | Own Checkmarx, Black Duck, Prisma? Those satisfy the rules. Built something internal? That satisfies them identically. |
| **Explicit Not Applicable** | Every excluded control is named with its reason. Silence is never an answer. |
| **Right control, right place** | Controls run at the earliest stage where they produce *meaningful* results — not the earliest stage possible. |
| **Enforcement you chose** | BLOCK / WARN / REPORT recommended per control, with the trade-off stated so you can overrule it deliberately. |
| **Decisions, not just YAML** | Every recommendation carries a rule ID and a rationale you can defend in a design review. |

---

## Install in 60 seconds

**As a Claude Code plugin** — adds the `/devsecops-engineer:*` commands:

```bash
git clone https://github.com/devsecblueprint/devsecops-claude-skill.git
claude plugin install ./devsecops-claude-skill
```

**As a personal skill** — available in every session, no commands:

```bash
git clone https://github.com/devsecblueprint/devsecops-claude-skill.git \
  ~/.claude/skills/devsecops-engineering
```

**For one project** — commit it so the whole team gets it:

```bash
git clone https://github.com/devsecblueprint/devsecops-claude-skill.git \
  .claude/skills/devsecops-engineering
```

---

## Try it

**Advise** — you have tools and an architecture, and want to know what you are missing:

```
/devsecops-engineer:advise We run Jenkins, Java/Maven, artifacts in Artifactory,
deploy to OpenShift. We own Checkmarx, Black Duck, and Prisma Cloud.
```

**Design** — you want a pipeline built for your actual stack:

```
/devsecops-engineer:design Node.js API, TypeScript, container image to ECR,
deployed to EKS via GitHub Actions. Greenfield, no security tooling yet.
```

**Assess** — you have a pipeline and want it reviewed:

```
/devsecops-engineer:assess .github/workflows/deploy.yml
```

Without the plugin installed, describe the task in plain language — the skill activates
on its own.

---

## Common workflows

| Situation | Start with | You get |
|---|---|---|
| Inherited a pipeline nobody understands | `assess` | Findings by category, remediation ranked by risk |
| New service, no pipeline yet | `design` | Implementation-ready config, annotated with rule IDs |
| "Do we need to buy another scanner?" | `advise` | Usually no — a mapping of what you own to what you need |
| Audit asked which frameworks you cover | `advise` | NIST SSDF / SLSA / OWASP CI/CD / SAMM / CNCF mappings |
| Pipeline is slow and teams route around it | `assess` | Duplicate tooling and mis-levelled gates identified |
| Onboarding an engineer to DevSecOps | any mode | Every answer teaches the decision, not just the config |

---

## How it works

```
1. WORKLOAD PROFILING     What does this actually build, produce, and deploy?
          ↓
2. APPLICABILITY          Does the triggering technology or risk exist?
          ↓               NO → Not Applicable, reason recorded. Stop.
3. CAPABILITY RESOLUTION  Does an existing tool already cover this?
          ↓               YES → Satisfied. Do not add a second.
4. OWNERSHIP BOUNDARY     Does another governed process own it?
          ↓               YES → Satisfied (externally owned), process named.
5. ENFORCEMENT            BLOCK, WARN, or REPORT — and what you trade either way.
          ↓
6. PLACEMENT              Earliest technically valid stage producing meaningful results.
```

Every delivery pipeline maps to four logical phases — **Build → Test → Scan → Deploy**.
They describe engineering intent, not job names. Runtime-dependent controls (DAST, API
security testing) run after deployment but belong to Scan/verification, not a fifth
phase.

---

## Go deeper

| | |
|---|---|
| [`SKILL.md`](SKILL.md) | The methodology, operating modes, 20 baseline principles, and output contract |
| [`rules/`](rules/) | The 42-rule catalog — the authoritative requirement text |
| [`references/applicability.md`](references/applicability.md) | The control selection flow in full |
| [`references/capability-catalog.md`](references/capability-catalog.md) | Capability → condition → placement → owning rule |
| [`references/enforcement-model.md`](references/enforcement-model.md) | BLOCK / WARN / REPORT / N/A and the exception path |
| [`references/framework-mappings.md`](references/framework-mappings.md) | NIST SSDF, SLSA, OWASP CI/CD, OWASP SAMM, CNCF |
| [`examples/`](examples/) | Four worked outputs — Advise, two Generate, and a Review |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Rule change policy, testing, and the curriculum-first requirement |

**Validate the catalog:**

```bash
uv run --with pyyaml python scripts/validate_rules.py
# OK — 42 rules across 11 families
```

---

## Status — v0.1.0 (Pre-1.0)

This is an **initial release**. The methodology is settled; the catalog's shape is not
finished.

Expect during Pre-1.0:

- New rules and new families as the taxonomy is refined
- Changes to enforcement defaults and applicability conditions
- Additional examples across more platforms and stacks
- Direct links from rules to the DSB curriculum modules they correspond to

**Rule IDs are stable once merged.** A rule that is withdrawn is deprecated, never
renumbered, and its ID is never reused — so any pipeline annotated with a DSB rule ID
stays meaningful.

Compliance framework mapping (SOC 2, PCI DSS, FedRAMP, HIPAA) is **deferred by design**.
Compliance is not this methodology's driver.

---

## Contributing

Contributions are welcome — read [`CONTRIBUTING.md`](CONTRIBUTING.md) first. Two rules
matter most:

1. **Curriculum first.** The DSB curriculum is the source of truth; this skill is an
   implementation of it. A change in engineering guidance belongs in the curriculum
   before it lands here.
2. **Commands stay thin.** No rule logic in `commands/` — they load the skill and set the
   mode, nothing more.

---

## License and ownership

Licensed under the [MIT License](LICENSE).

The **DevSec Blueprint** name, branding, and curriculum are owned by The DevSec Blueprint
and are **not** covered by the MIT grant — see [`docs/legal/TRADEMARKS.md`](docs/legal/TRADEMARKS.md).
The MIT license covers this implementation: the rule catalog, skill definition,
references, examples, and scripts.

---

*Owned and maintained by The DevSec Blueprint. This skill is an implementation of DSB
knowledge and standards, not the source of those standards.*
