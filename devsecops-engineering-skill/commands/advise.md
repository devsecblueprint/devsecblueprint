---
description: Advise on a delivery pipeline using the DSB DevSecOps methodology — map existing capabilities to Build → Test → Scan → Deploy, find gaps, recommend enforcement.
argument-hint: [architecture, toolset, or requirements — or leave blank to be asked]
---

Load the `devsecops-engineering` skill (`SKILL.md`) and its rule catalog (`rules/*.yaml`)
before responding. This command is a thin entry point; all rule logic lives in the skill.

Operate in **Mode 1 — Advise** (`SKILL.md` §2).

Context supplied by the user:

$ARGUMENTS

If that is empty or too thin to work from, ask for the workload context checklist items
in `SKILL.md` §4 that actually change the answer — not all of them.

Do **not** produce pipeline code in this mode unless the user asks for it. If they want
an implementation, direct them to `/devsecops-engineer:design`.

Follow the output contract in `SKILL.md` §7 in full, including the Not Applicable
section (`DSB-EVD-003`) and the Satisfied (externally owned) section. Cite rule IDs
inline.
