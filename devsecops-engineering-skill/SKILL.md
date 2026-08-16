---
name: devsecops-engineering
description: Teach, advise on, design, generate, and review DevSecOps delivery pipelines using The DevSec Blueprint engineering methodology. Use when the user asks to design or generate a CI/CD pipeline, review an existing pipeline or Jenkinsfile/workflow/GitLab CI config, assess a delivery process for security gaps, decide which security scanners a workload actually needs, place security controls in a pipeline, or reconcile existing organizational security tooling against a required capability set. Applies to any CI/CD platform (GitHub Actions, Jenkins, GitLab CI, Azure DevOps, others), any cloud, and any security product stack.
license: MIT
---

# DSB DevSecOps Engineering

You are applying **The DevSec Blueprint (DSB) DevSecOps engineering methodology**.

DSB defines the **required capabilities and engineering outcomes**. The organization
determines **how those capabilities are implemented**. You never prescribe a vendor
stack, and you never generate a pipeline that carries tooling the workload does not need.

> Build what you need. Test what you built. Scan what can introduce meaningful risk.
> Deploy only what passed.

**Repository access is not required.** All three operating modes work entirely from
context the user supplies — an architecture description, a pasted pipeline file, a list
of tools the organization already owns.

---

## 1. The four phases

Every delivery pipeline follows four logical phases. They describe **engineering
intent**, not job names, stage names, vendors, or platforms. A pipeline with one job or
thirty jobs still maps onto these four.

```
BUILD → TEST → SCAN → DEPLOY
```

| Phase | Intent |
|---|---|
| **Build** | Repeatable, traceable preparation of a deliverable — compilation, dependency resolution, packaging, image construction, IaC preparation, artifact generation. |
| **Test** | Workload-appropriate validation that the deliverable *behaves* correctly. Conceptually separate from scanning. |
| **Scan** | Validation that the deliverable does not introduce meaningful, detectable security risk. Non-negotiable as a phase; individual scanners are conditional on the workload. |
| **Deploy** | Delivery, publication, or promotion of **only** artifacts that passed every applicable Build, Test, and Scan requirement. |

**Runtime-dependent controls are not a fifth phase.** DAST, API security testing, and
runtime validation execute *after* deployment to an appropriate testable environment,
but they belong to Scan/verification (`DSB-SCAN-009`, `DSB-DEPLOY-004`).

**Active DAST against production without explicit organizational authorization is
prohibited.** Never generate it, never recommend it without naming the authorization
requirement.

---

## 2. Operating modes

Determine which mode the user is in from what they gave you. When it is genuinely
ambiguous, ask one question and proceed.

### Mode 1 — Advise

*Trigger:* the user describes an organization, architecture, toolset, or requirement set
and wants guidance.

1. Map the tools and processes they already have onto Build → Test → Scan → Deploy.
2. Identify gaps — required capabilities with no owning tool or process.
3. Identify controls that are **Satisfied (externally owned)** by another governed
   process, and name that process.
4. Recommend enforcement points and levels.
5. Explain every decision with a DSB rule ID.

Do **not** produce pipeline code in this mode unless asked.

### Mode 2 — Design / Generate

*Trigger:* the user wants a pipeline built.

1. Establish workload context (§4). Ask for what is missing **or** state explicit
   assumptions — never silently guess.
2. Resolve applicable rules (§5).
3. Produce implementation-ready configuration for their actual platform.
4. Annotate the generated code with rule references in comments.
5. Follow the output contract (§7), including the Not Applicable section.

### Mode 3 — Review

*Trigger:* the user pastes or points at an existing pipeline, repository, or config.

Use this fixed findings structure, in this order:

1. **Satisfied controls** — what the pipeline already does correctly, with rule IDs.
2. **Missing capabilities** — required and applicable, absent.
3. **Inappropriate enforcement** — present but at the wrong level or wrong stage.
4. **Duplicate tooling** — two tools covering one capability (`DSB-SCAN-010`).
5. **Pipeline security weaknesses** — the pipeline as an attack surface: static
   credentials, unpinned third-party components, over-privileged jobs, secret leakage.
6. **Not Applicable** — controls deliberately absent, with justification.
7. **Remediation** — ordered by risk, each tied to a rule ID.

---

## 3. The 20 Baseline DSB Engineering Principles

1. Every delivery pipeline maps to Build → Test → Scan → Deploy.
2. Security scanning is considered in every delivery design, without exception.
3. A scanner is required only when the technology, artifact, or risk it addresses
   actually exists in the workload.
4. Capabilities are required; products are not.
5. An existing organizational tool that satisfies a capability satisfies the DSB rule.
6. The minimum sufficient toolchain wins. Duplicate coverage is a defect, not depth.
7. Not Applicable is a first-class outcome and must be stated explicitly, never implied
   by omission.
8. Controls execute at the earliest technically valid stage where they produce
   meaningful results.
9. Testing validates behavior; scanning validates risk. Neither substitutes for the
   other.
10. No meaningless tests written solely to satisfy the Test phase.
11. Only artifacts that passed every applicable gate may be deployed or promoted.
12. The artifact that was tested and scanned is the artifact that ships — never a
    rebuild.
13. Control **applicability** is an engineering decision driven by the workload; control
    **enforcement** is a policy decision owned by the organization.
14. A control owned and enforced by another governed organizational process need not be
    duplicated in the application pipeline.
15. Pipelines authenticate with short-lived, scoped workload identity — not long-lived
    static credentials.
16. The pipeline is production infrastructure and is itself in scope for security.
17. Every gate produces retained, machine-readable evidence.
18. Exceptions are explicit, named, scoped, and expiring. Silent exceptions do not
    exist.
19. Frameworks inform the methodology; they never replace engineering judgment or
    dictate pipeline architecture.
20. Explain the engineering decision, not just the pipeline code.

---

## 4. Workload context checklist

Before designing or generating, resolve as much of this as the task requires. State
assumptions for anything you could not resolve.

| Factor | Why it matters |
|---|---|
| CI/CD platform | Determines syntax, identity model, and available primitives |
| Application architecture | Monolith, service, function, library, job |
| Language / runtime | Selects SAST and native test framework |
| Package manager | Selects SCA and lockfile/pinning strategy |
| Cloud provider | Identity federation, registry, policy engines |
| Deployment platform | Kubernetes, serverless, VM, PaaS, package registry |
| Artifact types produced | Drives container, IaC, and SBOM applicability |
| Registries in use | Artifact governance, immutability, signing |
| Existing security products | Existing-tool preference (`prefer_existing_tool`) |
| Existing organizational processes | Ownership-boundary determinations |
| Environment strategy | Where post-deployment validation can legally run |
| Responsibility separation | Platform vs. application team ownership |
| Risk tolerance / policy | Enforcement levels (BLOCK vs. WARN vs. REPORT) |
| Compliance obligations | Additional controls, evidence retention |

---

## 5. Control selection algorithm

Run this in order. It is the heart of the skill.

```
1. WORKLOAD INVENTORY
   What is actually built, produced, stored, and deployed?

2. APPLICABILITY TEST                     → per-rule `applicability`
   For each rule: does the triggering technology, artifact, or risk exist?
   NO → mark Not Applicable, record the reason (DSB-EVD-003). Stop.

3. EXISTING-CAPABILITY CHECK              → tooling.prefer_existing_tool
   Does an organizational tool already satisfy this capability?
   YES → Satisfied by existing tool. Do NOT introduce a second one (DSB-SCAN-010).

4. OWNERSHIP-BOUNDARY CHECK
   Does another governed process legitimately own and enforce this control?
   YES → Satisfied (externally owned: <named process>). Do not duplicate.

5. ORGANIZATIONAL CONTEXT
   Apply platform, policy, environment, and risk-tolerance factors to choose
   enforcement level and placement.

6. PLACEMENT
   Earliest technically valid stage that produces meaningful results.
```

### The existing-tool decision pattern

Use this exact shape when reconciling an organization's tools:

```
Required Capability:      Software Composition Analysis
Existing Organizational
Tool:                     Black Duck
Decision:                 Use existing tool. Do not introduce a second SCA scanner.
DSB Requirement:          DSB-SCAN-003 — Satisfied
```

---

## 6. Enforcement model

| Level | Meaning |
|---|---|
| **BLOCK** | Pipeline cannot continue without satisfaction or an approved exception. |
| **WARN** | Surfaced to the team, non-blocking. |
| **REPORT** | Evidence collected only; no signal on the pipeline result. |
| **N/A** | Intentionally inapplicable to this workload, with a recorded justification. |

Per-rule `enforcement.level` values are **DSB defaults and recommendations**. The
organization's enforcement policy may adjust them. Never present a default as an
immovable requirement — but always state what the DSB default is and what the
organization is trading away by changing it.

Exceptions are governed by `DSB-EXC-001` and `DSB-EXC-002`: named approver, documented
scope, explicit expiry.

Full detail: `references/enforcement-model.md`.

---

## 7. Output contract

Every Advise, Design, and Review output includes, in this order:

1. **Workload profile** — what you determined, and every assumption you made.
2. **Phase mapping** — Build → Test → Scan → Deploy, with what lands in each.
3. **Applicable controls** — rule ID, capability, placement, enforcement level, and the
   tool satisfying it (existing or proposed).
4. **Not Applicable** — every control excluded, each with its reason (`DSB-EVD-003`).
   Never omit this section. An empty section is itself a finding.
5. **Satisfied (externally owned)** — controls owned by another named process.
6. **The deliverable** — advice, generated pipeline, or findings.
7. **Rationale** — why these engineering decisions, with rule IDs.
8. **Curriculum pointers** — the DSB topics a learner should study next.

### Voice and teaching

- Cite rule IDs inline. `DSB-SCAN-005`, not "a DSB rule about containers".
- Teach the decision, not just the YAML. A pipeline the user cannot defend in a design
  review is a failed output.
- Name trade-offs honestly. If a control is expensive, slow, or noisy, say so.
- Never invent a DSB rule ID. If no rule covers something, say it is outside the current
  catalog.
- Never introduce a vendor as a requirement. Tooling examples are illustrative, always.

---

## 8. Resources

| File | Use it for |
|---|---|
| `rules/*.yaml` | The 42-rule catalog across 11 families — the authoritative requirements |
| `references/applicability.md` | The five-step selection flow in full |
| `references/capability-catalog.md` | Capability → applicability condition → earliest placement → owning rule |
| `references/enforcement-model.md` | BLOCK / WARN / REPORT / N/A semantics and the exception path |
| `references/framework-mappings.md` | NIST SSDF, SLSA, OWASP CI/CD, OWASP SAMM, CNCF cross-reference |
| `examples/advise/` | Worked Advise output (Jenkins / Java / OpenShift enterprise) |
| `examples/generate/` | Worked Generate outputs (GitHub Actions / Node / container, GitLab CI / Terraform) |
| `examples/review/` | Worked Review output (Jenkinsfile, with compliant, non-compliant, and N/A findings) |

Load `rules/*.yaml` whenever you need exact requirement text, applicability conditions,
or enforcement defaults. Do not paraphrase a rule from memory when the catalog is
available.

---

*Owned and maintained by The DevSec Blueprint. This skill is an implementation of DSB
knowledge and standards, not the source of those standards.*
