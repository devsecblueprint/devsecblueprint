# Contributing to DevSec Blueprint

Thanks for your interest in contributing. This guide covers everything you need to get started.

## Table of contents

- [Ways to contribute](#ways-to-contribute)
- [Before you start](#before-you-start)
- [Development setup](#development-setup)
- [Run tests](#run-tests)
- [Coding expectations](#coding-expectations)
- [Pull request guidelines](#pull-request-guidelines)
- [PR title format](#pr-title-format)
- [Commit messages](#commit-messages)
- [Reporting bugs](#reporting-bugs)
- [Proposing documentation](#proposing-documentation)
- [Community and support](#community-and-support)

---

## Ways to contribute

- Report bugs
- Improve documentation
- Propose and implement platform improvements
- Add tests and fix regressions

## Before you start

1. Check open issues and pull requests to avoid duplicate work.
2. Open an issue first for larger changes so maintainers can confirm scope.
3. Keep pull requests focused and small when possible.

## Development setup

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | latest |
| `uv` | recommended for Python dependency management |

### Clone and install

```bash
git clone https://github.com/devsecblueprint/devsecblueprint.git
cd devsecblueprint
```

Install backend dependencies:

```bash
uv sync
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

## Run tests

Backend:

```bash
uv run pytest
```

Frontend:

```bash
cd frontend
npm test
```

## Coding expectations

- Prefer clear, maintainable code over clever code.
- Add or update tests for any behavioral change.
- Keep security and least-privilege in mind for infrastructure and auth changes.
- Update docs when behavior, setup, or workflows change.

## Pull request guidelines

1. Fork the repo and create a branch from `main`.
2. Use a descriptive branch name:
   - `fix/auth-timeout`
   - `docs/contributing-guide`
3. Ensure tests pass locally before opening the PR.
4. Fill out the PR description with:
   - What changed
   - Why it changed
   - Test evidence (commands run and their output)
   - Screenshots for UI changes
5. Link related issues using `Closes #123`.

## PR title format

**PR titles are automatically validated.** They must follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<optional scope>): <short description>
```

### Allowed types

| Type | When to use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation changes only |
| `ci` | CI/CD workflow changes |
| `build` | Build system or dependency changes |

### Allowed scopes (optional)

`projects` · `typo` · `workflow` · `blueprint` · `security` · `misc`

### Examples

```
feat(blueprint): add zero trust network module
fix(security): resolve token expiry edge case
docs: update contributing guidelines
ci(workflow): add PR title linting
```

> A PR that fails this check will receive an automated comment with the error. Rename the PR title to fix it — the check re-runs automatically.

## Commit messages

Use the same `type: description` format as PR titles for individual commits:

```
fix: extend auth session handling
docs: add contributing guide
test: add regression coverage for logout flow
```

## Reporting bugs

Use the bug template at `.github/ISSUE_TEMPLATE/bug_report.md` and include:

- Step-by-step reproduction instructions
- Expected vs. actual behavior
- Environment details (OS, browser, versions)
- Logs or screenshots where applicable

## Proposing documentation

Use `.github/ISSUE_TEMPLATE/new_document.md` for new content proposals.

## Community and support

| Channel | Purpose |
|---------|---------|
| GitHub Issues | Bug reports and feature requests |
| Discord | Questions, discussion, community | 

Discord invite: <https://discord.gg/enMmUNq8jc>

---

Thanks for helping improve DevSec Blueprint.
