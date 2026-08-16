---
description: Design and generate an implementation-ready DevSecOps pipeline for a stated workload, applying the DSB rule catalog with no unnecessary tooling.
argument-hint: [platform, language, artifact type, deployment target]
---

Load the `devsecops-engineering` skill (`SKILL.md`) and its rule catalog (`rules/*.yaml`)
before responding. This command is a thin entry point; all rule logic lives in the skill.

Operate in **Mode 2 — Design / Generate** (`SKILL.md` §2).

Context supplied by the user:

$ARGUMENTS

Before generating anything, resolve the workload context checklist (`SKILL.md` §4). Ask
for what is missing and materially changes the design; for anything else, state an
explicit assumption. Never silently guess.

Then run the control selection algorithm (`SKILL.md` §5) and generate configuration for
the user's **actual** platform. Annotate the generated code with rule IDs in comments so
each control's justification travels with it.

Hard constraints:

- No scanner for a technology, artifact, or risk the workload does not have.
- No second tool for a capability an existing organizational tool already covers
  (`DSB-SCAN-010`).
- No active DAST against production without explicit organizational authorization
  (`DSB-SCAN-009`).
- Pin third-party pipeline components to immutable references (`DSB-SC-002`).

Follow the output contract in `SKILL.md` §7 in full, including the Not Applicable
section (`DSB-EVD-003`).
