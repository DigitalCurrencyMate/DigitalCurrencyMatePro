# DigitalCurrencyMatePro

DigitalCurrencyMatePro — a professional-grade toolkit for tracking, analyzing, and managing cryptocurrency portfolios and trading workflows.

This repository contains a full-stack application:
- Backend: Node.js + TypeScript (Express / Fastify-compatible structure)
- Frontend: Next.js (React) for the web admin dashboard
- Worker: background job processors (Bull / worker queue) for exchange polling, reconciliations, and notifications
- Database: PostgreSQL (configurable via DATABASE_URL)
- Containerized: Docker + Docker Compose for quick local environments

If your project uses different languages or frameworks, tell me and I'll update this file before committing.

Table of contents
- Features
- Quick start (Docker)
- Local development (frontend & backend)
- Configuration
- Testing
- Database migrations & seeds
- Deployments & CI
- Contributing
- License
- Contact

---

## Features

- Portfolio aggregation across exchanges and wallets
- Real-time and historical price data and charts
- PnL and performance reports (time-weighted, dollar-weighted)
- Trade simulation and backtesting engine
- Alerts & notifications (email, webhook, SMS)
- Multi-exchange adapters with API key management
- Role-based access and audit logs
- REST API + Next.js web UI and CLI tools

---

## Quick start (recommended — Docker Compose)

1. Copy example env:
   cp .env.example .env

2. Edit `.env` and set required secrets (DATABASE_URL, JWT_SECRET, exchange keys).

3. Start everything:
   docker compose up --build

4. Apply migrations and seed (inside backend container or via CLI):
   # Example (adjust to your stack)
   docker compose exec backend npm run migrate
   docker compose exec backend npm run seed

5. Visit the web UI at http://localhost:3000 (adjust port from .env if needed).

---

## Local development (no Docker)

Prerequisites
- Node.js 18+ (or LTS)
- PostgreSQL running locally (or use Docker)
- Yarn or npm

Backend
1. cd backend
2. cp .env.example .env && edit .env
3. npm install
4. npm run dev
5. API served at http://localhost:4000 (default — check .env)

Frontend
1. cd web
2. cp .env.example .env && edit .env
3. npm install
4. npm run dev
5. Open http://localhost:3000

Worker
1. cd worker
2. cp .env.example .env && edit .env
3. npm install
4. npm run dev

Adjust `npm` commands to `yarn` or `pnpm` depending on your package manager.

---

## Configuration

Create `.env` from `.env.example` and set values:

- NODE_ENV=development
- PORT=4000 (backend)
- NEXT_PUBLIC_API_URL=http://localhost:4000 (frontend)
- DATABASE_URL=postgresql://user:pass@db:5432/dcmate
- REDIS_URL=redis://redis:6379
- JWT_SECRET=<secure random string>
- EXCHANGE_API_KEY, EXCHANGE_API_SECRET (per exchange)
- SMTP_* (for email alerts)
- SENTRY_DSN (optional)

Keep secrets out of git. Use a vault (AWS Secrets Manager, HashiCorp Vault) for production.

---

## Database migrations & seeds

This repo uses a migration tool (Prisma / Knex / TypeORM). Example commands:

- Run migrations:
  npm run migrate

- Create a migration:
  npm run migrate:generate -- -n add-example-table

- Seed:
  npm run seed

Replace with appropriate commands for Prisma (`prisma migrate deploy`), TypeORM, Alembic, etc.

---

## Testing

- Unit tests:
  cd backend && npm test
- Integration tests:
  npm run test:integration
- E2E tests (if present):
  npm run e2e

CI should run lint, tests, and type checks on each PR.

Suggested scripts in package.json (example)
- "dev": "ts-node-dev --respawn src/index.ts"
- "build": "tsc"
- "start": "node dist/index.js"
- "migrate": "prisma migrate deploy"
- "test": "jest --runInBand"
- "lint": "eslint . --ext .ts,.tsx"

---

## Observability

- Metrics: Prometheus + Grafana
- Tracing: OpenTelemetry / Jaeger
- Logging: Structured JSON logs (winston/pino) to centralized collector
- Error reporting: Sentry

---

## Security & operational notes

- Use read-only exchange keys where possible for reporting
- Rate-limit API requests and implement exponential backoff
- Rotate secrets and use least privilege on service accounts
- Run automated dependency scans (Dependabot, Snyk)

---

## Deployment

Example Docker Compose + production setup:
- Build images: docker compose -f docker-compose.prod.yml build
- Apply migrations: docker compose -f docker-compose.prod.yml run --rm backend npm run migrate
- Bring up services: docker compose -f docker-compose.prod.yml up -d

For Kubernetes, create manifests/helm charts and a CI pipeline to build/push images.

---

## Contributing

1. Fork the repo
2. Create a branch: feat/short-description or fix/short-description
3. Add tests and update docs
4. Open a pull request describing the change and run CI

See CONTRIBUTING.md and CODE_OF_CONDUCT.md if present.

---

## Roadmap & Issues

See the repository Issues for planned features and priorities. If you want to prioritize something, open or vote on an issue.

---

## License

MIT. See LICENSE.

---

## Contact

Repository: https://github.com/DigitalCurrencyMate/DigitalCurrencyMatePro  

