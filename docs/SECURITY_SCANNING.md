# Security Scanning

This document describes the security-scanning integration for this
repository, which tool owns which class of finding, the failure model the
workflows enforce, and the policy under which findings are either
remediated or explicitly ignored.

## Overview

| Item | Value |
|---|---|
| Workflow file | `.github/workflows/security-scan.yml` |
| Tools in this workflow | Trivy (`aquasecurity/trivy-action@v0.36.0`) and CodeQL (`github/codeql-action@v4`) |
| Trivy jobs | `trivy-iac` (Terraform misconfiguration), `trivy-image` (backend production container image) |
| Triggered on | `push` to `main`, `pull_request` to `main` (`opened`, `synchronize`, `reopened`), manual `workflow_dispatch`, weekly `schedule` (`0 6 * * 1`) |
| Path filters | `paths-ignore: ['docs/**', '**/*.md']` on both `push` and `pull_request` |
| Concurrency | `security-scan-${{ github.ref }}`, `cancel-in-progress: true` |
| Required permissions | `contents: read`, `security-events: write`, `pull-requests: read`, `actions: read` |

## Security-tool ownership

Each class of finding has exactly one primary owner. Trivy answers two
questions and only two: **is our infrastructure configuration secure**,
and **is the container image we actually ship free of unacceptable known
vulnerabilities**.

| Category | Primary owner | Covers |
|---|---|---|
| IaC misconfiguration | **Trivy** — `trivy-iac` job | Terraform under `terraform/`, root module and the modules it calls |
| Container image vulnerabilities | **Trivy** — `trivy-image` job | OS packages and Python libraries present in the built backend image |
| Dependency vulnerabilities | **Dependabot** — *partially implemented* | Today: GitHub Actions only. Intended: `backend/requirements.txt`, `pyproject.toml` / `uv.lock`, `frontend/package-lock.json`. See *Known limitations*. |
| Static analysis / SAST | **CodeQL**, Semgrep, SonarQube | `python` and `javascript-typescript`; see also `semgrep.yml`, `sonarqube.yml` |
| Checked-in secrets | **Not currently owned** | See *Known limitations* below |

### Why the image scan is not duplicate dependency scanning

Dependabot reads dependency *manifests*. `trivy-image` reads the *artifact
we ship*. These are not the same set, and the difference is not academic:

- The image is built from `backend/requirements.txt` only. `pyproject.toml`
  and `uv.lock` describe the local development and tooling environment and
  are **not** installed into the runtime image.
- The base image (`python:3.13-slim`) contributes packages that appear in
  no manifest at all — `setuptools` being the clearest example.

A manifest can therefore be clean while the shipped image is not, and vice
versa. The image scan is the authority on what actually runs in
production.

## What each job does

### `trivy-iac` — Terraform misconfiguration

```
scan-type: config
scan-ref:  terraform/
severity:  HIGH,CRITICAL
exit-code: 1
skip-dirs: **/.terraform
format:    sarif
limit-severities-for-sarif: true
```

#### `limit-severities-for-sarif` is not optional

`trivy-action`'s `entrypoint.sh` contains:

```bash
if [ "${TRIVY_FORMAT:-}" = "sarif" ]; then
  if [ "${INPUT_LIMIT_SEVERITIES_FOR_SARIF:-false,,}" != "true" ]; then
    unset TRIVY_SEVERITY
  fi
fi
```

Any step that sets `format: sarif` and omits `limit-severities-for-sarif`
silently loses its `severity` filter. On this repository that changes the
IaC scan from 11 findings to 31 (11 HIGH/CRITICAL, 1 MEDIUM, 19 LOW), and
because `exit-code: 1` fires on *any* reported finding, the gate stops
being a HIGH/CRITICAL gate and becomes an any-severity gate — while the
workflow still reads as though `severity: HIGH,CRITICAL` were in force.
Code Scanning is flooded with LOW alerts at the same time.

Both Trivy steps therefore set `limit-severities-for-sarif: true`. **Do
not remove it**, and add it to any future Trivy step that emits SARIF.

`scan-type: config` invokes `trivy config`, which is structurally limited
to misconfiguration analysis — it cannot read a dependency manifest even
if pointed at one. This is preferred over `scan-type: fs` with
`scanners: misconfig`, because the restriction is a property of the
command rather than a flag that could later be widened by accident.

`ignore-unfixed` is deliberately **not** set on this job. It expresses
"no upstream fix is available yet", which is a vulnerability-scanner
concept and a no-op for IaC rules — every misconfiguration is fixable by
changing the configuration.

Scoping to `terraform/` rather than `.` narrows the scan away from
`backend/Dockerfile`, which Trivy's Dockerfile checks would otherwise
also evaluate. That file currently produces zero findings, so nothing is
lost today; if Dockerfile misconfiguration analysis is wanted later it
should be added as an explicit, separately-owned control rather than as a
side effect of the Terraform scan.

#### SARIF path re-rooting

Scoping the scan to `terraform/` has one non-obvious consequence: Trivy
emits SARIF artifact URIs **relative to `scan-ref`**, and records an
absolute `originalUriBaseIds.ROOTPATH` pointing at the runner's checkout
of that directory. A finding in `terraform/modules/alb/main.tf` therefore
arrives as `modules/alb/main.tf`.

GitHub Code Scanning resolves artifact URIs against the *repository*
root. Left uncorrected, the alerts upload successfully but anchor to no
file: no source links, no line-level annotations, and the runner's
absolute filesystem path is published into the repository's security data.

The `Re-root SARIF paths at the repository root` step therefore rewrites
each `artifactLocation.uri` to be repository-root-relative and removes the
now-meaningless `uriBaseId` / `originalUriBaseIds`. It is idempotent and
runs under `if: always()`, because the Trivy step exits non-zero whenever
there are findings and every subsequent step would otherwise be skipped.

If the IaC scan is ever re-scoped to the repository root, this step
becomes unnecessary and should be removed rather than left in place.

### `trivy-image` — backend production image

```
scan-type:      image
scanners:       vuln
vuln-type:      os,library
severity:       HIGH,CRITICAL
ignore-unfixed: true
exit-code:      1
format:         sarif
limit-severities-for-sarif: true
```

The job builds the image with `docker build -t dsb-platform:<sha> backend/`,
mirroring `tasks.py::build_image` — the same path `deploy.yml` uses via
`invoke deploy-all`. **These two must stay in sync**; if the production
build command changes, this job's build step changes with it.

`scanners: vuln` is set explicitly because Trivy's default for image
scanning is `vuln,secret`. Secret scanning is no longer Trivy's
responsibility in this repository, in the filesystem or in the image.

`vuln-type: os,library` is the default, stated explicitly to document
that both the Debian base layer and the installed Python packages are in
scope.

`--platform` is not passed. `tasks.py` adds `--platform linux/amd64` only
on macOS hosts; GitHub's `ubuntu-latest` runners are already `linux/amd64`.

## Pass / fail behavior

The job is the source of truth for pass / fail. SARIF upload to Code
Scanning is a secondary view and is best-effort.

| Outcome | Cause | What to do |
|---|---|---|
| ❌ `Trivy IaC (Terraform misconfig)` | At least one HIGH or CRITICAL Terraform misconfiguration exists anywhere under `terraform/`. | Fix the configuration. **Do not** silence it by widening `severity`, adding `ignore-unfixed`, or expanding `skip-dirs`. If the finding is an accepted design decision, it requires a documented `.trivyignore` entry per the policy below. |
| ❌ `Trivy Image (backend production)` | At least one HIGH or CRITICAL vulnerability **with an available fix** is present in the built image. | Bump the offending package in `backend/requirements.txt`, or upgrade the base image. Check whether the package is a direct dependency, a transitive one, or supplied by the base image — the remediation differs. |
| ❌ `CodeQL (python)` or `CodeQL (javascript-typescript)` | A new SAST finding in the changed code, or a pre-existing finding the suite flags. | Address the finding in code. Genuine false positives can be dismissed via the Security → Code Scanning UI with a recorded reason. |
| ✅ All checks | No gated findings. | Nothing required. |

The PR-scoped Code Scanning re-summary checks report on findings
**introduced by the PR diff**. The workflows' own job checks report on
findings **anywhere in the tree or image**. Both are intentional: the diff
view keeps PR reviews focused, while the tree view forces baseline
cleanup.

## Image gating policy: `ignore-unfixed`

`trivy-image` sets `ignore-unfixed: true`, so the gate fires only on
vulnerabilities that have a released fix. The reasoning:

- A gate that cannot be turned green teaches contributors to ignore red
  builds. Unfixed CVEs in a distribution base layer are, by definition,
  not remediable by this repository at the time of the scan.
- The weekly `schedule` re-scan means an unfixed CVE is re-evaluated every
  Monday and starts gating the moment upstream ships a patch.

The trade-off is accepted knowingly: **unfixed-but-present vulnerabilities
are real risk that this gate does not surface.** The mitigation is the
base-image strategy rather than the scanner configuration — see issue #173
(migrate the backend runtime image to Chainguard Python), which
substantially reduces the unpatched surface by shrinking the base image
rather than by filtering the report.

Contributors who want the unfiltered picture should run the local command
in the *Running locally* section without `--ignore-unfixed`.

## Where results are visible

1. **GitHub Actions** — each job's status and full log under the workflow run.
2. **Security → Code Scanning** — SARIF results under distinct categories:
   - `trivy-iac` — Terraform misconfigurations
   - `trivy-image` — container image vulnerabilities
   - `/language:python`, `/language:javascript-typescript` — CodeQL

   The categories must remain distinct. Two uploads sharing a category
   overwrite each other, and one job's results silently disappear.
3. **Pull-request annotations** — CodeQL adds inline annotations on changed lines.

## Ignore / baseline policy

**No `.trivyignore` exists in the repo today, by design.** The policy is
*remediate, do not ignore*. The intent of failing the check is to force
baseline cleanup rather than entomb existing findings.

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

Widening Trivy's `severity` filter, adding or flipping `ignore-unfixed`,
or expanding `skip-dirs` to make a finding go away is **not** an
acceptable substitute for a documented `.trivyignore` entry.

## Known limitations

- **Secret scanning is currently unowned.** Trivy's `secret` scanner was
  removed from this workflow as part of separating security-control
  responsibilities. No dedicated replacement control exists yet. This is a
  known coverage gap, not an oversight, and should be closed by a
  purpose-built secret-scanning control.
- **Dependabot coverage is incomplete.** `.github/dependabot.yml` currently
  covers `github-actions` only. `npm`, `uv`/`pip` coverage is tracked by
  issue #174. Until that lands, dependency vulnerabilities surface only
  when they reach the built image (via `trivy-image`) — manifests that do
  not feed the image are not currently watched by any tool.
- **Terraform variables are unresolved during the IaC scan.** Trivy emits
  `Variable values were not found in the environment or variable files` for
  the `TFC_*` workspace variables, which are Terraform Cloud secrets. Trivy
  evaluates the configuration with those values unknown. Supplying dummy
  values via `--tf-vars` was considered and rejected: fabricated values
  would make the evaluation *look* authoritative while being wrong. The
  affected variables flow into the `secrets`, `ssm_parameter` and `ecs`
  modules; none of the current findings depend on their values, so the
  practical impact today is nil. This warning is expected in every run.
- **Fork-PR SARIF upload.** `security-events: write` is not granted to
  workflow runs triggered by `pull_request` from forked head repositories.
  Both Trivy SARIF upload steps are marked `continue-on-error: true` and
  `if: always()` so the *job's exit code* remains the source of truth even
  when the upload is denied. CodeQL's own actions handle this internally.
- **Only the backend image is scanned.** The frontend is a static export
  and ships no container image.
- **License / SBOM compliance is not in scope** for this workflow.

## Running locally

Reproduce what each job does:

```bash
# trivy-iac — Terraform misconfiguration
trivy config terraform/ \
  --severity HIGH,CRITICAL \
  --skip-dirs '**/.terraform'

# trivy-image — build the production image, then scan it
docker build -t dsb-platform:local backend/
trivy image dsb-platform:local \
  --scanners vuln \
  --pkg-types os,library \
  --severity HIGH,CRITICAL \
  --ignore-unfixed

# The unfiltered picture, including vulnerabilities with no available fix:
trivy image dsb-platform:local --scanners vuln --severity HIGH,CRITICAL
```

Note that the local `trivy` binary is independent of the version the
GitHub Action downloads: `aquasecurity/trivy-action@v0.36.0` installs
Trivy **v0.70.0** by default. Small differences between local and CI
results are expected when the local binary is newer — checks and
advisories are added over time. Compare `trivy --version` before
concluding that a result has genuinely changed.

The local commands above scan the working tree directly and so do not
exercise the SARIF re-rooting step. To reproduce that:

```bash
trivy config terraform/ --severity HIGH,CRITICAL -f sarif -o trivy-iac.sarif
python3 -c "
import json
d = json.load(open('trivy-iac.sarif'))
print(d['runs'][0].get('originalUriBaseIds'))
print({r['locations'][0]['physicalLocation']['artifactLocation']['uri'] for r in d['runs'][0]['results']})
"
```

CodeQL is most easily reproduced by re-running the workflow against a
branch via the **Run workflow** button (`workflow_dispatch`).

## Change history

| Date | Change | Reference |
|---|---|---|
| 2026-05-12 | Initial workflow added (Trivy + CodeQL); 15 HIGH baseline findings tracked. | PR #131, issue #132 |
| 2026-08-13 | Trivy filesystem scan (`vuln,secret,misconfig` over `.`) split into `trivy-iac` and `trivy-image`. Dependency and secret scanning removed from Trivy's responsibility. Baseline at time of change: 11 IaC findings (9 HIGH, 2 CRITICAL), 6 image findings (5 HIGH, 1 CRITICAL). | issue #175 |
