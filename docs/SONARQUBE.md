# SonarQube Integration

This document describes the SonarQube static-analysis integration for the
`devsecblueprint` repository and tracks known issues with the current
deployment.

## Overview

| Item | Value |
|---|---|
| Workflow file | `.github/workflows/sonarqube.yml` |
| Project config | `sonar-project.properties` (repo root) |
| Scan action | `SonarSource/sonarqube-scan-action@v6` |
| Scanner CLI | `sonar-scanner-cli` 7.2.0.5079 (provided by the action) |
| JDK | Temurin 17 (`actions/setup-java@v4`) |
| Triggered on | `push` to `main`, `pull_request` to `main` (`opened`, `synchronize`, `reopened`) |
| Path filters | `paths-ignore: ['docs/**', '**/*.md']` on both triggers (docs-only changes skip the scan) |
| Concurrency | `sonarqube-${{ github.ref }}`, `cancel-in-progress: true` |
| Quality gate | `sonar.qualitygate.wait=true` (job fails if gate fails) |

## Project configuration

`sonar-project.properties` at the repo root:

```properties
sonar.projectKey=devsecblueprint_devsecblueprint_4b382cb2-090e-4a59-821f-d7cd711d1705
sonar.sources=backend,frontend,terraform,tests
sonar.sourceEncoding=UTF-8
sonar.exclusions=frontend/lib/curriculum-data.ts,**/node_modules/**,**/.terraform/**,**/*.tfstate,**/*.tfstate.*,**/dist/**,**/build/**,**/__pycache__/**,**/*.pyc
sonar.python.version=3.12
```

Notes:

- `sonar.projectKey` is the auto-generated key issued by the SonarQube
  server when the project was provisioned. The UUID suffix
  (`4b382cb2-...`) is part of the key as stored on the server and must
  match exactly.
- `sonar.sources` is scoped to the four directories that hold
  first-party code in this repo (`backend`, `frontend`, `terraform`,
  `tests`); other top-level files (`tasks.py`, lockfiles, etc.) are
  not analyzed.
- `frontend/lib/curriculum-data.ts` is excluded because it is a
  large generated data file rather than hand-written source.
- `**/.terraform/**` and `*.tfstate*` are excluded to avoid scanning
  provider plugins and state files.
- `sonar.python.version=3.12` matches `requires-python = ">=3.12"` in
  `pyproject.toml`.
- `sonar.organization` and `sonar.projectName` are intentionally
  **not** set: this repo's project lives on a self-hosted SonarQube
  Community server, where `sonar.organization` is a SonarCloud-only
  parameter and `sonar.projectName` is managed server-side.

## Required GitHub secrets

| Secret | Purpose |
|---|---|
| `SONAR_TOKEN` | User token with **Execute Analysis** permission on the `devsecblueprint_devsecblueprint_4b382cb2-...` project on the SonarQube server |
| `SONAR_HOST_URL` | Base URL of the SonarQube server |

Both are referenced as `${{ secrets.* }}` in the workflow's `Run SonarQube
Scan` step. `SONAR_HOST_URL` is also surfaced in the job summary.

Secrets set in *Settings → Secrets and variables → Actions* are **not**
automatically available to Dependabot-triggered workflow runs. If
Dependabot-driven scans are desired, mirror the same secrets into
*Settings → Secrets and variables → Dependabot*. See the *Known issues*
section below for the current behavior.

## Detected languages / sensors

The configured sources span the following language sensors:

- **Python** — `backend/`, `tests/` (Lambda handlers, services, tests)
- **TypeScript / JavaScript** — `frontend/` (Next.js app, components,
  Jest tests)
- **Terraform / HCL** — `terraform/` (infrastructure modules)
- **YAML, JSON, Markdown** — picked up across all sources
- Plus the global Text & Secrets sensor

A successful end-to-end scan with concrete per-language file counts
has not yet been produced for this repo (see *Known issues*).

## Known issues

### 1. Workflow fails on PRs without secret access (mitigated; pending merge)

**Status:** Mitigated by PR
[#129](https://github.com/devsecblueprint/devsecblueprint/pull/129) —
pending merge as of 2026-05-12.

**Symptom:**

```
Warning: Running this GitHub Action without SONAR_TOKEN
ERROR Failed to query server version: Expected URL scheme 'http' or
'https' but no scheme was found for /api/v...
```

**Cause:** GitHub does not expose `secrets.*` to `pull_request`
workflow runs in two situations:

1. The head repository is a **fork** (deliberate exfiltration
   prevention).
2. The PR was opened by **Dependabot** (since Sept 2021 Dependabot has
   its own separate secret store at *Settings → Secrets and variables
   → Dependabot*).

In both cases `SONAR_TOKEN` and `SONAR_HOST_URL` evaluate to empty
strings, the scan action defaults `SONAR_HOST_URL` to `/api/v...` with
no scheme, and `sonar-scanner` exits with code 1.

**Fix:** PR #129 adds a job-level `if:` guard so the SonarQube job is
**skipped** (not failed) for fork PRs and Dependabot PRs. It also adds
a `workflow_dispatch` trigger with a `ref` input, giving maintainers a
controlled path to scan such commits manually under the upstream
repo's context.

### 2. End-to-end scan against the SonarQube server not yet verified (open)

**Status:** Open — once #129 is merged and a `push`-triggered run on
`main` executes with secrets available, this should resolve or surface
a more specific server-side error.

**Background:** A previous deployment of this workflow on the sibling
`devsecops-pipeline` repo hit a server-side authorization failure of
the form:

```
ERROR You're not authorized to analyze this project or the project
doesn't exist on SonarQube and you're not authorized to create it.
Please contact an administrator.
```

That class of error has three possible causes:

1. The project key (currently
   `devsecblueprint_devsecblueprint_4b382cb2-...`) does not exist on
   the SonarQube server.
2. The user owning `SONAR_TOKEN` lacks **Execute Analysis** on the
   project.
3. The user lacks the global **Create Projects** permission required
   for auto-provisioning.

If a post-#129 run on `main` surfaces this same error, resolve
server-side via one of:

- *Projects → Create Project → Manually*, setting **Project key** to
  the value in `sonar-project.properties`.
- *Project Settings → Permissions*, granting **Execute Analysis** to
  the token's user/group.
- *Administration → Security → Global Permissions*, granting **Create
  Projects** to the token's user.

After resolving, re-run the latest failed workflow:

```bash
gh run rerun <run-id> --repo devsecblueprint/devsecblueprint --failed
```

## Change history

| Date | Change | Commit / PR |
|---|---|---|
| 2026-05-12 | Initial `.github/workflows/sonarqube.yml` and `sonar-project.properties` added; action pinned to `@v6`, Temurin 17, quality-gate wait enabled, `paths-ignore` for `docs/**` and `**/*.md` | [#126](https://github.com/devsecblueprint/devsecblueprint/pull/126) / `b7afd6f` |
| 2026-05-12 | `sonar.projectKey` updated to the auto-generated server-side key `devsecblueprint_devsecblueprint_4b382cb2-...`; removed `sonar.projectName` and `sonar.organization` (self-hosted SonarQube, not SonarCloud) | `54cc949` |
| 2026-05-12 | (pending) Guard against fork PRs and Dependabot PRs that cannot access secrets; add `workflow_dispatch` with a `ref` input for on-demand scans | [#129](https://github.com/devsecblueprint/devsecblueprint/pull/129) |
