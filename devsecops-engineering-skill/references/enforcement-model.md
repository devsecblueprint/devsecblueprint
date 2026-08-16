# Enforcement Model

## The four outcomes

| Outcome | Pipeline behavior | Use when |
|---|---|---|
| **BLOCK** | Cannot continue without satisfaction or an approved exception | The finding represents risk the organization has decided not to ship |
| **WARN** | Surfaced to the team, pipeline continues | The signal is valuable but the false-positive rate or remediation cost does not justify stopping delivery |
| **REPORT** | Evidence collected, no signal on the result | The output's value is trend, inventory, or audit rather than a per-run decision |
| **N/A** | Control does not execute | The workload lacks the technology, artifact, or risk the control addresses |

---

## Applicability is not enforcement

This distinction is the one most often collapsed, and collapsing it produces both of the
common failures — pipelines carrying controls they do not need, and pipelines quietly
dropping controls they do.

| | Applicability | Enforcement |
|---|---|---|
| **Question** | Does this control make sense for this workload? | What happens when this control fails? |
| **Driven by** | Engineering facts about the workload | Organizational risk policy |
| **Decided by** | The engineer designing the pipeline | The organization |
| **Negotiable?** | No — it is a factual determination | Yes — it is a policy position |
| **Recorded as** | Applicable / N/A / Satisfied (externally owned) | BLOCK / WARN / REPORT |

Two consequences follow:

1. **You cannot make an applicable control disappear by lowering enforcement.** A
   container scanner set to REPORT is still an applicable control; it is a control the
   organization has chosen not to gate on. That is a legitimate, recorded decision — and
   a different thing from N/A.
2. **You cannot make an inapplicable control meaningful by raising enforcement.** A
   BLOCK-level IaC scan on a repository with no IaC blocks nothing and teaches the team
   that the gates are theatre.

---

## DSB defaults are recommendations

Every rule's `enforcement.level` is the DSB default. The organization's policy may adjust
it. When it does, say what is being traded:

> DSB default for `DSB-SCAN-003` is BLOCK. You have set it to WARN for transitive
> findings with no available fix. That is a defensible position given your patch cadence
> — the trade is that a fix becoming available does not itself stop delivery, so you need
> the review cadence in `DSB-EXC-002` to catch it.

Never present a default as immovable, and never silently accept a downgrade without
naming its cost.

---

## Choosing a level

Escalate toward BLOCK as these become true:

- The finding is **confirmed** rather than probabilistic
- The finding is **reachable** in the deployed configuration
- Remediation is **available** and proportionate
- The control's false-positive rate is **low** in this codebase
- The consequence of shipping it is **severe or irreversible**

Descend toward WARN or REPORT as they become false. A high-noise BLOCK gate is not a
strong control — it is a control the team will route around, and the routing becomes
permanent.

### Standard starting position

| Class of finding | Default |
|---|---|
| Verified secret in source | BLOCK |
| Critical/High vulnerability with an available fix | BLOCK |
| Critical/High vulnerability with no available fix | WARN + tracked exception |
| Medium/Low vulnerability | WARN |
| Informational / inventory / SBOM | REPORT |
| Insecure IaC that provisions public exposure | BLOCK |
| Insecure IaC hardening recommendation | WARN |
| Pipeline configuration weakness | WARN, escalating to BLOCK for credential exposure |

---

## Placement and enforcement interact

The same control can carry different levels at different points:

```
Pull request         → SAST on changed code            WARN   (fast feedback)
Merge to main        → SAST full scan                  BLOCK  (gate before build)
Post-deploy to test  → DAST                            WARN   (noisy, slow)
Promotion to prod    → Signature verification          BLOCK  (cheap, decisive)
```

This is deliberate. Feedback-stage controls optimize for speed and tolerance;
gate-stage controls optimize for decisiveness.

---

## The exception path

An exception is the **only** legitimate way past a BLOCK gate. It is governed by
`DSB-EXC-001` and `DSB-EXC-002`.

Every exception carries five fields. An exception missing any of them is invalid:

| Field | Why it exists |
|---|---|
| **Rule** | Which requirement is being deviated from |
| **Approver** | A named person or role accepting the risk — never "the team" |
| **Scope** | The exact repository, workload, and finding — so it cannot widen silently |
| **Justification** | Why remediation is not being done now |
| **Expiry** | A fixed date — so "temporary" cannot become the architecture |

### Anti-patterns

| Pattern | Why it fails |
|---|---|
| Inline suppression comments with no expiry | Invisible to review, permanent by default |
| `continue-on-error` on a BLOCK gate | An undocumented, unapproved, unlimited exception |
| Removing the scanner instead of accepting the finding | Destroys the record that the risk was ever known |
| Blanket exceptions across a whole repository | Unscoped — covers findings nobody has seen yet |
| Auto-renewal on expiry | Defeats the only mechanism forcing reassessment |

Suppressing a finding without an exception record is not risk acceptance. It is an
unmanaged vulnerability with a paper trail pointing away from it.

---

## Reporting enforcement in output

State the level, the placement, and the reason together:

```
DSB-SCAN-003  Software Composition Analysis
  Tool:        Black Duck (existing organizational capability)
  Placement:   After dependency resolution, before image build
  Enforcement: BLOCK on Critical/High with an available fix
               WARN on Critical/High with no fix, tracked under DSB-EXC-001
  DSB default: BLOCK — retained
```
