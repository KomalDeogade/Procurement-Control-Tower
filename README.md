# SCM Procurement Control Tower

AI-enabled Supply Chain Management Procurement Control Tower for manufacturing procurement workflows.

## Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Python + FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL 16
- **Mock SAP**: Separate FastAPI service simulating SAP ERP
- **Future**: n8n orchestration, provider-agnostic AI services

See [docs/architecture.md](docs/architecture.md) for full details.

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose)
- [Node.js 18+](https://nodejs.org/) (for frontend development)

### 1. Clone and configure

```bash
git clone <repo-url>
cd scm-procurement-control-tower
cp .env.example .env
```

### 2. Start backend services

```bash
docker compose up --build
```

This starts:
| Service | URL | Description |
|---------|-----|-------------|
| PostgreSQL | `localhost:5432` | Database |
| Backend API | `http://localhost:8000` | FastAPI + Swagger |
| Mock SAP | `http://localhost:8001` | Simulated SAP ERP |

### 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

### 4. Login

Use any of the demo credentials:

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin |
| `scm_user` | `scm123` | SCM User |
| `proc_manager` | `manager123` | Procurement Manager |
| `finance_user` | `finance123` | Finance User |

## Health Checks

```bash
# Backend
curl http://localhost:8000/api/health

# Mock SAP
curl http://localhost:8001/health
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API Contracts: [docs/api-contracts.md](docs/api-contracts.md)

## Optional: Start n8n

```bash
docker compose --profile n8n up
```

n8n will be available at: http://localhost:5678

## Project Structure

```
scm-procurement-control-tower/
├── frontend/          # React + Vite + Tailwind CSS
├── backend/           # FastAPI + SQLAlchemy
├── mock-sap/          # Mock SAP FastAPI service
├── database/          # DB initialization scripts
├── docs/              # Architecture & process docs
├── n8n/               # n8n workflows (future)
├── scripts/           # Utility scripts
├── docker-compose.yml
├── .env.example
└── README.md
```

## Documentation

- [Architecture](docs/architecture.md)
- [As-Is Process](docs/as-is-process.md)
- [To-Be Process](docs/to-be-process.md)
- [API Contracts](docs/api-contracts.md)

## Phase Status

- ✅ **Phase 1**: Foundation & Architecture (current)
- ⬜ Phase 2: Core procurement workflow
- ⬜ Phase 3: AI integration
- ⬜ Phase 4: n8n orchestration
- ⬜ Phase 5: Polish & production readiness
