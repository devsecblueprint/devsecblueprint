# Security Scanning

This document describes the baseline security-scanning integration for this
repository, the failure model the workflow enforces, and the policy under
which findings are either remediated or explicitly ignored.

## Overview

| Item | Value |
|---|---|
| Workflow file | `.github/workflows/security-scan.yml` |
| Tools | Trivy (`aquasecurity/trivy-action@v0.36.0`) and CodeQL (`github/codeql-action@v3`) |
| Triggered on | `push` to `main`, `pull_request` to `main` (`opened`, `synchronize`, `reopened`), manual `workflow_dispatch`, weekly `schedule` (`0 6 * * 1`) |
| Path filters | `paths-ignore: ['docs/**', '**/*.md']` on both `push` and `pull_request` |
| Concurrency | `security-scan-${{ github.ref }}`, `cancel-in-progress: true` |
| Required permissions | `contents: read`, `security-events: write`, `pull-requests: read`, `actions: read` |

## What is scanned

A single Trivy filesystem scan covers three of the four required categories,
and CodeQL provides the fourth.

| Category | Tool | Covers |
|---|---|---|
| Dependency vulnerabilities | Trivy (`vuln`) | CVEs in `uv.lock`, `frontend/package-lock.json`, Terraform provider lockfiles |
| Checked-in secrets | Trivy (`secret`) | API keys, tokens, private keys, credentials in tracked files |
| IaC misconfigurations | Trivy (`misconfig`) | Terraform under `terraform/modules/**` |
| Static analysis / SAST | CodeQL | `python` and `javascript-typescript` matrices, default security query suite, `build-mode: none` |

Trivy noise controls:

- `severity: HIGH,CRITICAL` — drops `LOW`, `MEDIUM`, and `UNKNOWN`.
- `ignore-unfixed: true` — suppresses CVEs without an available fix; these are unactionable and re-evaluated on the weekly cron.
- `skip-dirs: node_modules, .terraform, .next, dist, build` — excludes vendored or generated trees.

CodeQL intentionally uses the default `security` query suite rather than
`security-extended`. The extended suite has a substantially higher
false-positive rate and is inappropriate for a baseline scan.

## Pass / fail behavior

The job is the source of truth for pass / fail. SARIF upload to Code
Scanning is a secondary view and is best-effort.

| Outcome | Cause | What to do |
|---|---|---|
| ❌ `Trivy (deps + IaC + secrets)` | At least one HIGH or CRITICAL finding with an available fix exists somewhere in the tree (not just in the PR diff). | Remediate the finding by version-bumping the dependency, fixing the IaC, or removing the secret. **Do not** silence the finding by widening the `severity` filter, flipping `ignore-unfixed`, or expanding `skip-dirs`. |
| ❌ `CodeQL (python)` or `CodeQL (javascript-typescript)` | A new SAST finding in the changed code, or a pre-existing finding the suite flags. | Address the finding in code. Genuine false positives can be dismissed via the Security → Code Scanning UI with a recorded reason. |
| ✅ All checks | No fixable HIGH/CRITICAL Trivy findings and no CodeQL findings. | Nothing required. |

The PR-scoped Code Scanning re-summary checks (`Trivy` and `CodeQL`,
without a job name suffix) report on findings **introduced by the PR
diff**. The workflow's own job checks report on findings **anywhere in
the tree**. Both are intentional: the diff view keeps PR reviews
focused, while the tree view forces baseline cleanup.

## Where results are visible

1. **GitHub Actions** — each job's status and full log under the workflow run.
2. **Security → Code Scanning** — SARIF results from Trivy (category: `trivy`) and CodeQL (categories: `/language:python`, `/language:javascript-typescript`).
3. **Pull-request annotations** — CodeQL adds inline annotations on changed lines for findings introduced by the PR.

## Ignore / baseline policy

**No `.trivyignore` exists in the repo today, by design.** The current
policy is *remediate, do not ignore*. The intent of failing the check on
day one is to force baseline cleanup rather than entomb existing
findings.

A `.trivyignore` file may be added in the future, but every entry must
satisfy all of the following:

1. The CVE / GHSA / IaC rule ID on its own line.
2. An adjacent comment containing:
   - The reason the finding is acceptable here (compensating control, scope mismatch, false positive against this codebase, etc.),
   - The owner accountable for the decision,
   - A re-evaluation date or trigger (e.g. "re-evaluate when upstream issues a fix").
3. A link to the issue or PR where the decision was made.

Example of the required format:

```
# AWS-0132 — terraform/modules/s3_frontend
# Bucket serves only public, non-sensitive static assets; SSE-S3 is
# appropriate and SSE-KMS would add cost without security benefit.
# Owner: @<maintainer>. Re-evaluate if the bucket starts holding
# user-uploaded or otherwise sensitive content.
# See: https://github.com/devsecblueprint/devsecblueprint/issues/132
AVD-AWS-0132
```

Widening Trivy's `severity` filter, flipping `ignore-unfixed`, or
expanding `skip-dirs` to make a finding go away is **not** an acceptable
substitute for a documented `.trivyignore` entry.

## Known limitations

- **Fork-PR SARIF upload.** `security-events: write` is not granted to workflow runs triggered by `pull_request` events from forked head repositories. The Trivy SARIF upload step is marked `continue-on-error: true` and `if: always()` so the *job's exit code* (from Trivy itself) remains the source of truth even when the upload step is denied by GitHub. CodeQL's own actions handle this gracefully and skip the upload internally.
- **Container images are not scanned** — no `Dockerfile`s are in scope. When one lands, add `trivy image` against the produced image as a separate job.
- **License / SBOM compliance is not in scope** for this workflow.

## Running locally

Reproduce the same scan the workflow performs:

```bash
# Dependencies + secrets + IaC, mirroring the workflow config:
trivy fs . \
  --scanners vuln,secret,misconfig \
  --severity HIGH,CRITICAL \
  --ignore-unfixed \
  --skip-dirs '**/node_modules' \
  --skip-dirs '**/.terraform' \
  --skip-dirs '**/.next' \
  --skip-dirs '**/dist' \
  --skip-dirs '**/build'
```

CodeQL is most easily reproduced by re-running the workflow against a
branch via the **Run workflow** button (`workflow_dispatch`).

## Change history

| Date | Change | Reference |
|---|---|---|
| 2026-05-12 | Initial workflow added (Trivy + CodeQL); 15 HIGH baseline findings tracked. | PR #131, issue #132 |
