# Contributing to The DevSec Blueprint

Thank you for contributing to The DevSec Blueprint. DSB is both a learning platform and an open-source project, so contributions should be clear, tested, secure, and easy for maintainers to review.

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

The exact structure of the repository may change over time. Before making changes, review the current folders and follow the patterns already used in the project.

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

If you add a new folder, make sure its purpose is clear and consistent with the rest of the repository.

## Local Development Requirements

Install the tools required by the repository before contributing.

Recommended baseline tools:

- Git
- Node.js LTS
- npm, pnpm, or yarn, depending on the lockfile used by the repository
- Python 3.12 or newer, if backend services are included
- Docker, if containerized services are included
- Terraform, if infrastructure code is included

Use the package manager already defined by the repository. For example:

- Use `npm` if the repo includes `package-lock.json`.
- Use `pnpm` if the repo includes `pnpm-lock.yaml`.
- Use `yarn` if the repo includes `yarn.lock`.

Do not switch package managers unless the change is intentional, discussed, and approved.

## Getting Started

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd <repository-name>
npm install
```

If the repository uses pnpm:

```bash
pnpm install
```

If the repository uses yarn:

```bash
yarn install
```

After installing dependencies, review the `README.md` and `.env.example` files for project-specific setup steps.

## Environment Variables

Environment variables should be documented in `.env.example`.

Create a local environment file from the example file if needed:

```bash
cp .env.example .env.local
```

Do not commit:

- `.env`
- `.env.local`
- Credentials
- API keys
- Access tokens
- Private keys
- Passwords
- Sensitive local configuration files

If your change requires a new environment variable, add it to `.env.example` with a safe placeholder value and a clear description when appropriate.

Example:

```bash
NEXT_PUBLIC_APP_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
```

Never place real secrets in `.env.example`.

## Running the Project Locally

Start the local development server with the command used by the repository.

For npm:

```bash
npm run dev
```

For pnpm:

```bash
pnpm dev
```

For yarn:

```bash
yarn dev
```

After the project starts, check the terminal output for the local URL and verify the app loads successfully in the browser.

## Building the Project

Before opening a pull request, confirm the project builds successfully.

For npm:

```bash
npm run build
```

For pnpm:

```bash
pnpm build
```

For yarn:

```bash
yarn build
```

If the build fails, fix the issue before submitting your pull request or clearly explain why the failure is unrelated to your change.

## Running Tests

Run the repository's test command before opening a pull request.

For npm:

```bash
npm test
```

For pnpm:

```bash
pnpm test
```

For yarn:

```bash
yarn test
```

If you change an area that does not have automated tests, explain how you manually validated the change in your pull request.

Manual validation examples:

- Verified the page loads locally.
- Checked the updated workflow in the browser.
- Confirmed the form handles expected input.
- Confirmed that an error state displays correctly.
- Confirmed documentation links work.

## Linting and Formatting

Run linting and formatting checks before submitting your work.

For npm:

```bash
npm run lint
npm run format
```

For pnpm:

```bash
pnpm lint
pnpm format
```

For yarn:

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
