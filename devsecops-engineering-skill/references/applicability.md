# Applicability — The Control Selection Flow

This is the five-step flow referenced by `SKILL.md` §5. Run it in order. Steps 2, 3, and
4 can each end the evaluation for a rule; only rules that survive all three reach
enforcement and placement.

---

## Step 1 — Workload inventory

Establish what actually exists. Do not infer from the repository name or the team's
description of itself — infer from what the build produces.

| Question | Determines |
|---|---|
| Is there first-party source code, and in what languages? | `DSB-SCAN-002` |
| Are third-party dependencies resolved? | `DSB-BUILD-002`, `DSB-SCAN-003`, `DSB-SC-001` |
| Is a container image produced? | `DSB-SCAN-005` |
| Is there infrastructure-as-code? | `DSB-SCAN-006`, `DSB-IAC-*` |
| Are there Kubernetes manifests or charts? | `DSB-SCAN-007` |
| Are pipeline definitions in the repository? | `DSB-SCAN-008` |
| Is a network-reachable interface exposed? | `DSB-SCAN-009` |
| Is an artifact published or promoted? | `DSB-ART-*`, `DSB-DEPLOY-002` |
| Is there a deployable environment? | `DSB-DEPLOY-003`, `DSB-DEPLOY-004` |

**Failure mode:** assuming a container scanner is needed because the org "uses
Kubernetes". The question is whether *this pipeline* builds an image.

---

## Step 2 — Applicability test

For each rule, read its `applicability` block:

- `always: true` → the rule applies. Proceed to step 3.
- `always: false` → the rule applies only if at least one `conditions` entry is true of
  this workload and no `not_applicable_when` entry is true.

If the rule does not apply, **stop** and record:

```
DSB-SCAN-005 — Not Applicable
Reason: This workload publishes a Python package to an internal index.
        No container image is produced.
```

That record is required by `DSB-EVD-003`. Omission is not an option.

**Applicability is an engineering determination about the workload.** It is not a risk
decision, not a budget decision, and not negotiable by preference. "We don't want to run
SAST" is an exception (`DSB-EXC-001`), not a Not Applicable.

---

## Step 3 — Existing-capability check

Before proposing any tool, ask what the organization already runs.

```
Required Capability:      <the capability the rule demands>
Existing Organizational
Tool:                     <the tool that already covers it>
Decision:                 Use existing tool. Do not introduce a second.
DSB Requirement:          <RULE-ID> — Satisfied
```

Every rule carries `tooling.prefer_existing_tool: true`. The `tooling.examples` list is
**illustrative only** — naming a product there confers no DSB endorsement and creates no
requirement to adopt it.

A custom, proprietary, or internal tool satisfies a DSB rule exactly as well as a
commercial one. The rule asks for a capability; it does not ask who wrote the scanner.

Introducing a second tool for a capability already covered is a `DSB-SCAN-010` finding.

---

## Step 4 — Ownership-boundary check

A control need not execute in the application pipeline when another governed
organizational process legitimately owns and enforces it.

Record it as:

```
DSB-SCAN-007 — Satisfied (externally owned)
Owning process: Platform team's Kyverno admission policy on the shared EKS clusters.
Enforcement:    Deployments violating baseline policy are rejected at admission.
```

Three conditions must all hold before you may use this outcome:

1. The owning process is **named** — not "the platform team handles it".
2. It is **enforced**, not merely available.
3. It covers **this workload**, not a superset the workload might fall outside.

If any of the three is unproven, it is a gap, not an external satisfaction. This is the
determination most often claimed and least often verifiable — check it.

---

## Step 5 — Organizational context

Apply the remaining factors to choose enforcement level and placement:

| Factor | Typical effect |
|---|---|
| CI/CD platform | Available primitives, identity model, syntax |
| Application architecture | Which test and scan surfaces are meaningful |
| Language and package manager | SAST and SCA selection, pinning strategy |
| Cloud and deployment platform | Federation, registry, admission control |
| Registries in use | Immutability and signing capability |
| Existing products and licences | Step 3 outcomes |
| Existing governed processes | Step 4 outcomes |
| Environment strategy | Whether `DSB-SCAN-009` has anywhere legal to run |
| Responsibility separation | Platform vs. application ownership |
| Risk tolerance | BLOCK vs. WARN on non-critical findings |
| Compliance obligations | Added controls, longer evidence retention |

---

## Step 6 — Placement

> Security controls execute at the **earliest technically valid stage where they produce
> meaningful results**.

"Earliest" is bounded by "meaningful". Both halves matter:

- Secret scanning and SAST need only source → run them first, on the change itself.
- SCA needs resolved dependencies → run it after resolution, not before.
- Image scanning needs a built image → run it after build, before publication.
- DAST needs a running system → run it after deployment to an authorized environment.

Shifting a control earlier than its inputs exist does not make it faster; it makes it
wrong. A container scan against a Dockerfile is not a container scan.

See `references/capability-catalog.md` for the earliest-valid placement of every
capability.

---

## Worked example

**Workload:** Terraform module repository. No application code, no container, publishes
to a private module registry, applied to AWS by a separate pipeline.

| Rule | Outcome | Reason |
|---|---|---|
| `DSB-SCAN-001` | Applicable | Always applicable |
| `DSB-SCAN-002` | **N/A** | No first-party application source code |
| `DSB-SCAN-003` | Applicable | Provider and module dependencies are resolved |
| `DSB-SCAN-004` | Applicable | Always applicable to source repositories |
| `DSB-SCAN-005` | **N/A** | No container image produced |
| `DSB-SCAN-006` | Applicable | The repository is entirely IaC |
| `DSB-SCAN-007` | **N/A** | No Kubernetes resources |
| `DSB-SCAN-008` | Applicable | Pipeline definitions are committed |
| `DSB-SCAN-009` | **N/A** | Module repository exposes no runtime interface |
| `DSB-IAC-002` | **Satisfied (externally owned)** | Plan review and gated apply are enforced by the platform team's environment pipeline, which is the only identity permitted to apply |
| `DSB-TEST-001` | Applicable | Module has meaningful contract tests |

Five of eleven controls do not execute here — and every one of them is written down.
