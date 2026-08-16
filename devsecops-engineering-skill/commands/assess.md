---
description: Assess an existing pipeline, repository, or CI/CD config against the DSB rule catalog and return structured findings with remediation.
argument-hint: [path to a pipeline file or repo, or paste the config]
---

Load the `devsecops-engineering` skill (`SKILL.md`) and its rule catalog (`rules/*.yaml`)
before responding. This command is a thin entry point; all rule logic lives in the skill.

Operate in **Mode 3 — Review** (`SKILL.md` §2).

Target supplied by the user:

$ARGUMENTS

If a path is given, read it — and read the surrounding repository far enough to
determine what the workload actually builds, since applicability depends on that and not
on the pipeline's own claims. If the config was pasted with no repository access, work
from it and state every assumption you had to make about the workload.

Return findings in the fixed structure from `SKILL.md` §2, in this order:

1. Satisfied controls
2. Missing capabilities
3. Inappropriate enforcement
4. Duplicate tooling (`DSB-SCAN-010`)
5. Pipeline security weaknesses — the pipeline as an attack surface
6. Not Applicable, with justification (`DSB-EVD-003`)
7. Remediation, ordered by risk, each tied to a rule ID

Assess what the workload needs, not what a maximal pipeline would contain. A control the
workload does not need is not a finding — it belongs in section 6. A control present but
unnecessary belongs in section 4.
