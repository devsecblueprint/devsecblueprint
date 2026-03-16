# Contributing to DevSec Blueprint

Thanks for your interest in contributing to DevSec Blueprint.

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

- Python 3.11+
- Node.js 20+
- npm
- `uv` (recommended for Python dependency management)

### Clone and install

```bash
git clone https://github.com/devsecblueprint/devsecblueprint.git
cd devsecblueprint
```

Backend dependencies:

```bash
uv sync
```

Frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

## Run tests

Backend tests:

```bash
uv run pytest
```

Frontend tests:

```bash
cd frontend
npm test
```

## Coding expectations

- Prefer clear, maintainable code over clever code.
- Add or update tests for behavioral changes.
- Keep security and least-privilege in mind for infrastructure/auth changes.
- Update docs when behavior, setup, or workflows change.

## Pull request guidelines

1. Fork the repo and create a branch from `main`.
2. Use a clear branch name, for example:
   - `fix/auth-timeout`
   - `docs/contributing-guide`
3. Ensure tests pass locally.
4. Open a PR with:
   - Summary of what changed
   - Why it changed
   - Test evidence (commands and results)
   - Screenshots for UI changes (if applicable)
5. Link related issue(s), for example `Closes #123`.

## Commit message guidance

Use concise, descriptive commits. Example formats:

- `fix: extend auth session handling`
- `docs: add contributing guide`
- `test: add regression coverage for logout flow`

## Reporting bugs

Use the bug template in `.github/ISSUE_TEMPLATE/bug_report.md` and include:

- Reproduction steps
- Expected vs. actual behavior
- Environment details
- Logs/screenshots when possible

## Proposing documentation

Use `.github/ISSUE_TEMPLATE/new_document.md` for new content proposals.

## Community and support

- GitHub Issues: bug reports and feature requests
- Discord: <https://discord.gg/enMmUNq8jc>

Thanks for helping improve DevSec Blueprint.
