# Security Policy

## Reporting a vulnerability

Report security issues **privately**. Do not open a public issue.

- Use [GitHub private vulnerability reporting](https://docs.github.com/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
  on this repository, or
- Contact The DevSec Blueprint maintainers through the channels in
  [`MAINTAINERS.md`](MAINTAINERS.md)

Please include what you found, how to reproduce it, and what you think the impact is.

---

## Scope

This repository contains documentation, YAML rule definitions, and a validation script.
It ships no runtime service. The security-relevant surface is smaller than a typical
project's, and specific:

**In scope:**

| Concern | Why it matters |
|---|---|
| **Incorrect security guidance** | A rule or example that leads someone to build an insecure pipeline is the highest-impact defect this project can have — report it as a security issue, not a bug |
| **Insecure example configuration** | Generated pipeline examples that would leak credentials, over-privilege a job, or expose an environment |
| **Unpinned or malicious third-party actions** | In this repository's own workflows (`DSB-SC-002`) |
| **Supply chain issues** | In `scripts/` dependencies |
| **Credentials committed to this repository** | `DSB-SCAN-004` — CI scans for this, but report anything CI missed |

**Out of scope:**

- Disagreement with a rule's enforcement default — open a normal issue
- Requests for new rules — open a normal issue
- Vulnerabilities in tools merely *named* in `tooling.examples` — those lists are
  illustrative and confer no endorsement; report to the tool's own maintainers

---

## Guidance defects are security defects

This is the unusual part of this project's threat model, and it is worth stating plainly.

The output of this skill becomes other organizations' delivery pipelines. A rule with a
wrong applicability condition can cause a control to be skipped across every consumer at
once — quietly, and with a written justification that makes it look deliberate. That is a
larger blast radius than most code vulnerabilities.

So: if you find guidance here that would cause someone to omit a control they need, place
one where it cannot work, or accept risk they did not understand they were accepting,
report it through this policy.

---

## Supported versions

During Pre-1.0, only the latest release is supported. Fixes land on `main` and ship in
the next release.

| Version | Supported |
|---|---|
| 0.1.x | ✅ |
| < 0.1 | ❌ (no such releases) |

---

## This repository's own controls

Enforced in [`.github/workflows/validate.yml`](.github/workflows/validate.yml):

- Rule catalog validation (`DSB-TEST-001`)
- Secret scanning, full history (`DSB-SCAN-004`)
- Workflow configuration scanning (`DSB-SCAN-008`)
- All third-party actions pinned to commit SHAs (`DSB-SC-002`)
- Least-privilege workflow permissions (`DSB-ID-002`)

If you can find a way past any of these, that is exactly the kind of report this policy
is for.
