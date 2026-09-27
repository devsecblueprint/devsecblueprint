# The DevSec Blueprint

A full-stack learning platform for DevSecOps, built with a Next.js frontend and a FastAPI backend, deployed to AWS.

## Project Structure

```
.
├── frontend/     # Next.js application (UI, pages, components)
├── backend/      # FastAPI application (API, services, auth)
├── terraform/    # Infrastructure-as-Code (Terraform)
├── scripts/      # Python utility scripts
├── tests/        # Backend test suite
├── docs/         # Internal documentation and legal
├── tasks.py      # Invoke tasks for build & deployment
└── .github/      # CI/CD workflows and issue templates
```

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- AWS CLI (configured)
- Docker (optional, for local services)

### Frontend

```bash
cd frontend
npm install
npm run dev      # runs on http://localhost:3001
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   # runs on http://localhost:8000
```

### Common Tasks

| Command | Description |
|---------|-------------|
| `npm run build` | Full production build (from `frontend/`) |
| `npm run lint` | ESLint check (from `frontend/`) |
| `npm run test` | Run Jest tests (from `frontend/`) |
| `pytest` | Run Python tests (from repo root) |
| `invoke --list` | List all build & deployment tasks |

## Deployment

The application is deployed to AWS via GitHub Actions (`.github/workflows/ci-cd.yml`), which orchestrates the `invoke` tasks defined in `tasks.py` (Docker image build/push to ECR, Terraform apply, and frontend deploy to S3/CloudFront).

## Licensing

The software in this repository is made publicly available under the PolyForm Noncommercial License 1.0.0. Commercial use requires prior written authorization from The DevSec Blueprint LLC.

This license applies only to the software in this repository. It does not grant rights to curriculum, walkthroughs, training materials, premium resources, name, logos, or other branded assets.

See:

- [License](./LICENSE.md)
- [Commercial Licensing](./docs/legal/COMMERCIAL-LICENSING.md)
- [Trademark Policy](./docs/legal/TRADEMARKS.md)

## Contributing

Please review the [Contributing Guidelines](./CONTRIBUTING.md) before opening a pull request, then join the [Discord Server](https://discord.gg/enMmUNq8jc) to connect with maintainers and contributors.

[View the Contributors Graph](https://github.com/devsecblueprint/devsecblueprint/graphs/contributors).
