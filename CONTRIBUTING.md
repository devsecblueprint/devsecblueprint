# Contributing to The DevSec Blueprint

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

This guide explains how to set up the project locally, make changes safely, and submit work in a way that supports the project’s engineering and security standards.

## Project Expectations

Contributors are expected to:

- Build the project locally before submitting changes.
- Test changes before opening a pull request.
- Keep pull requests focused and reviewable.
- Avoid committing secrets, credentials, private keys, or sensitive local files.
- Document security-sensitive changes clearly.
- Follow the existing project structure, naming patterns, and tooling.

The goal is not to make contribution difficult. The goal is to make contribution predictable, safe, and maintainable.

## Repository Structure

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | latest |
| `uv` | recommended for Python dependency management |

Common areas may include:

```text
.
├── src/                 # Application source code
├── app/                 # App routes or framework-specific application files
├── components/          # Reusable UI components
├── public/              # Static assets
├── tests/               # Automated tests
├── docs/                # Project documentation
├── infra/               # Infrastructure as code, if included
├── scripts/             # Utility scripts
├── .env.example         # Example environment variables
└── README.md            # Project overview and usage notes
```

Install backend dependencies:

```bash
uv sync
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

## Run tests

Backend:

```bash
pnpm install
```

Frontend:

```bash
npm test
```

For pnpm:

- Prefer clear, maintainable code over clever code.
- Add or update tests for any behavioral change.
- Keep security and least-privilege in mind for infrastructure and auth changes.
- Update docs when behavior, setup, or workflows change.

For yarn:

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

## Linting and Formatting

Use the bug template at `.github/ISSUE_TEMPLATE/bug_report.md` and include:

- Step-by-step reproduction instructions
- Expected vs. actual behavior
- Environment details (OS, browser, versions)
- Logs or screenshots where applicable

```bash
npm run lint
npm run format
```

For pnpm:

```bash
pnpm lint
pnpm format
```

| Channel | Purpose |
|---------|---------|
| GitHub Issues | Bug reports and feature requests |
| Discord | Questions, discussion, community | 

Discord invite: <https://discord.gg/enMmUNq8jc>

---

```bash
yarn lint
yarn format
```

If the repository uses automatic formatting, keep formatting changes separate from feature changes when possible. This makes reviews easier.

## Security Expectations

Security matters in every contribution.

Do not commit:

- API keys
- Cloud credentials
- Access tokens
- Private keys
- Passwords
- Sensitive environment files
- Unnecessary personal information
- Internal-only configuration values

Before opening a pull request, review your changes for secrets or sensitive data.

The repository may use automated security scanning. Contributors are expected to address scan failures or explain why a finding is a false positive.

Security-sensitive changes should be clearly documented in the pull request. This includes changes involving:

- Authentication
- Authorization
- Secrets handling
- Environment variables
- Infrastructure permissions
- CI/CD workflows
- Dependency updates
- Logging of user or system data
- External service integrations

## Infrastructure Changes

If the repository includes infrastructure as code, keep infrastructure changes focused and easy to review.

When changing infrastructure:

- Explain what resource is being added, changed, or removed.
- Document permission changes clearly.
- Avoid broad permissions when narrow permissions are possible.
- Validate Terraform or infrastructure syntax before submitting.
- Include plan output or a summary if the project expects it.
- Consider security, cost, and operational impact.

Example Terraform validation commands:

```bash
terraform fmt
terraform validate
```

Only run deployment or apply commands if you are authorized to do so.

## Pull Request Guidelines

Keep pull requests focused. A pull request should solve one clear problem or deliver one clear improvement.

Recommended pull request format:

```markdown
## Summary

Briefly explain what changed.

## Why

Explain why this change is needed.

## Testing

Explain how this was tested.

## Security Considerations

Mention any security impact, new permissions, sensitive data handling, or scan results.

## Screenshots

Include screenshots for UI changes if applicable.
```

Good pull requests usually include:

- A clear title
- A short explanation of the change
- Linked issue or context when available
- Testing notes
- Security considerations
- Screenshots for UI changes
- Small, focused commits

Avoid large pull requests that mix unrelated changes. If your work includes multiple concerns, split it into separate pull requests when practical.

## Commit Guidance

Use clear commit messages that explain what changed.

Good examples:

```text
Add security scanning workflow
Update contributor setup instructions
Fix the broken capstone link
Add Trivy scan for IaC files
```

Less helpful examples:

```text
update
fix stuff
changes
work in progress
```

A good commit message should help a maintainer understand the purpose of the change without opening the full diff.

## Branch Naming

Use short, descriptive branch names.

Examples:

```text
feature/security-scanning
docs/contributing-guide
fix/capstone-link
chore/update-workflow
```

Recommended prefixes:

- `feature/` for new functionality
- `fix/` for bug fixes
- `docs/` for documentation changes
- `chore/` for maintenance tasks
- `test/` for test-related changes
- `refactor/` for code restructuring without behavior changes

## Reporting Issues

When reporting an issue, include enough information for maintainers to understand and reproduce the problem.

Helpful issue details include:

- What happened
- What you expected to happen
- Steps to reproduce
- Screenshots or logs, if useful
- Browser, operating system, or runtime version, if relevant
- Related files, pages, workflows, or commands

Avoid including secrets, tokens, credentials, or private information in issue reports.

## Reporting Security Concerns

Do not report security vulnerabilities in public issues if the details could put users, systems, credentials, or infrastructure at risk.

For security concerns:

- Use the project’s documented private security reporting process, if available.
- If a `SECURITY.md` file exists, follow the instructions in that file.
- Include a clear description of the concern.
- Include reproduction steps when safe to share.
- Avoid including real secrets, production data, or unnecessary personal information.

If you are unsure whether something is security-sensitive, treat it as sensitive and avoid posting details publicly.

## Final Note

The DevSec Blueprint is designed to teach and model strong engineering habits. Contributions should reflect that mission: build locally, test your work, protect sensitive data, document security impact, and make changes that are easy for others to understand.

Thank you for helping improve DSB.
