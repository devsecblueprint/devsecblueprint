# Contributing

Thanks for wanting to improve this. Read the two policies below before opening a PR —
they are the ones that get contributions sent back.

---

## Policy 1 — Curriculum first

**The DSB curriculum is the source of truth. This skill is an implementation of it.**

A change to engineering guidance belongs in the curriculum before it lands here. If you
believe a rule is wrong, the discussion is about the methodology, not about the YAML.

| Change | Where it starts |
|---|---|
| New engineering guidance, or a change to existing guidance | Curriculum, then here |
| A rule's requirement text is unclear or ambiguous | Here — that is an implementation defect |
| Framework mapping is wrong or missing | Here |
| An example is wrong, outdated, or misleading | Here |
| A tool named in `tooling.examples` no longer exists | Here |

Open an issue before a large rule change. A PR adding six new rules will be asked what
curriculum change it implements.

---

## Policy 2 — Commands stay thin

`commands/*.md` load the skill and set the operating mode. **No rule logic lives there.**

Every command is a thin wrapper over `SKILL.md` and `rules/*.yaml`. This exists to
prevent drift: if a command file starts explaining applicability, or listing which
scanners a Node project needs, there are now two sources of truth and they will disagree
within a release.

If a command needs behavior the skill does not provide, add it to the skill.

---

## Rule IDs are permanent

**Deprecate, never renumber. Never reuse.**

Rule IDs appear in generated pipeline comments, review findings, and exception records
across every organization using this skill. An ID that changes meaning silently
invalidates all of it.

To withdraw a rule:

1. Leave the rule in place
2. Add `deprecated: true` and `deprecated_reason` and `superseded_by` where applicable
3. Note it in `CHANGELOG.md`
4. Never assign that ID again

To add a rule: take the next number in the family. Gaps are fine — they are evidence of
history, not defects.

---

## Adding or changing a rule

Every rule carries the full schema. `scripts/validate_rules.py` enforces it.

```yaml
- id: DSB-<FAMILY>-<NNN>       # family prefix must match the file's `family`
  title: <short imperative statement>
  phase: build | test | scan | deploy | cross-cutting
  requirement: >-              # what must be true. Testable. No vendor names.
  rationale: >-                # WHY. What fails without it. This is the teaching.
  applicability:
    always: <bool>
    conditions: []             # required if always: false
    not_applicable_when: []
  framework_mappings:          # all five keys required; empty list is valid
    nist_ssdf: []
    slsa: []
    owasp_cicd: []
    owasp_samm: []
    cncf_supply_chain: []
  enforcement:
    level: block | warn | report   # DSB default, not a mandate
    automatable: <bool>
  tooling:
    examples: []               # ILLUSTRATIVE ONLY
    prefer_existing_tool: true # always true — this is not optional
```

### What makes a good rule

- **Capability, not product.** "Software composition analysis", never "run Snyk".
- **Testable.** Someone must be able to look at a pipeline and say yes or no.
- **Honest applicability.** If it does not apply to some workloads, say which — a rule
  marked `always: true` that is not always true teaches engineers to ignore N/A.
- **A rationale that teaches.** Explain what actually goes wrong. "It is a best practice"
  is not a rationale and fails Principle 20.
- **Correct enforcement default.** Do not default everything to BLOCK. A high-noise BLOCK
  gate is how pipelines acquire `continue-on-error`.

### What gets rejected

- Requiring a specific vendor or product
- A rule that duplicates an existing rule's capability
- Enforcement defaults with no stated reasoning
- Rules that only make sense for one organization's setup
- `prefer_existing_tool: false`

---

## Testing

```bash
uv run --with pyyaml python scripts/validate_rules.py
```

The validator checks required fields, family prefixes, ID uniqueness, allowed phases and
enforcement levels, framework mapping keys, tooling flags, and per-family rule counts.

**Changing a rule count means updating `EXPECTED_FAMILIES` in the validator.** That is
deliberate friction — adding or removing a rule should be a conscious act with a
`CHANGELOG.md` entry, not a side effect.

CI runs the same validation plus secret scanning (`DSB-SCAN-004`) and workflow config
scanning (`DSB-SCAN-008`). This repository practices the methodology it teaches; a
contribution that would fail its own catalog will not merge.

---

## Contributing an example

Examples carry disproportionate weight — they are what people copy. An example must:

- Follow the output contract in `SKILL.md` §7 completely
- Include a **Not Applicable** section with real determinations and real reasons
- Annotate generated code with rule IDs in comments
- Pin third-party components by immutable reference (`DSB-SC-002`) — and if you cannot
  verify a digest, say so in the example rather than leaving an unverified pin looking
  authoritative
- Show a workload that genuinely excludes some controls. An example where everything
  applies teaches nothing about selection.

---

## Pull requests

1. Branch from `main`
2. Run the validator
3. Update `CHANGELOG.md` under Unreleased
4. Describe **what engineering problem** the change solves, not just what it changes
5. For rule changes, link the curriculum material it implements

---

## Code of conduct

Be decent. Assume good faith. Argue about engineering, not about people. Maintainers may
remove contributions or contributors that make this a worse place to work.
