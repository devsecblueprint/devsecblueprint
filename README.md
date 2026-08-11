# The DevSec Blueprint

![Build Status](https://img.shields.io/github/actions/workflow/status/devsecblueprint/devsecblueprint/deploy.yml?branch=main&style=for-the-badge)
![GitHub Stars](https://img.shields.io/github/stars/devsecblueprint/devsecblueprint?style=for-the-badge)
![Built with Kiro](https://img.shields.io/badge/Built%20with-Kiro-6366f1?style=for-the-badge)
![Hosted on AWS](https://img.shields.io/badge/Hosted%20on-AWS-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![License](https://img.shields.io/github/license/devsecblueprint/devsecblueprint?style=for-the-badge)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](https://makeapullrequest.com)
[![Join the Community](https://img.shields.io/badge/Join-Discord-blueviolet?style=for-the-badge&logo=discord)](https://discord.gg/enMmUNq8jc)

## Project Structure

```
.
├── frontend/          # Next.js application (UI, pages, components)
├── backend/           # FastAPI application (API, services, auth)
├── infra/             # Infrastructure-as-Code (AWS CDK / Terraform)
├── scripts/           # Utility and automation scripts
├── docs/              # Internal documentation and legal
└── .github/           # CI/CD workflows and issue templates
```

## Prerequisites

- Node.js 20+
- Python 3.12+
- AWS CLI (configured)
- Docker (optional, for local services)

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:3001`.

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Runs on `http://localhost:8000`.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run build` | Full production build (frontend) |
| `npm run lint` | ESLint check (frontend) |
| `npm run test` | Run Jest tests (frontend) |
| `pytest` | Run Python tests (backend) |

## Deployment

The application is deployed to AWS via GitHub Actions. See `.github/workflows/deploy.yml` for the pipeline configuration.

## Licensing

The software in this repository is made publicly available under the PolyForm Noncommercial License 1.0.0. Commercial use requires prior written authorization from The DevSec Blueprint LLC.

This license applies only to the software in this repository. It does not grant rights to curriculum, walkthroughs, training materials, premium resources, name, logos, or other branded assets.

See:

- [License](./LICENSE.md)
- [Commercial Licensing](./docs/legal/COMMERCIAL-LICENSING.md)
- [Trademark Policy](./docs/legal/TRADEMARKS.md)

## Contributing

Please review the [Contributing Guidelines](./CONTRIBUTING.md) before opening a pull request.

Join the [Discord Server](https://discord.gg/enMmUNq8jc) to connect with maintainers and contributors.

## Contributors

[Contributors Graph](https://github.com/devsecblueprint/devsecblueprint/graphs/contributors)
