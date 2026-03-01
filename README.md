# Banking REST Service

A full-stack banking application with a FastAPI backend and React frontend. Supports account management, transactions, transfers, card issuance, and statement generation.

## Requirements

### Backend
- Python 3.12+
- pip

### Frontend
- Node.js 20+
- npm

### Docker (optional)
- Docker 24+
- Docker Compose v2

## Setup

### Option 1: Quick start (setup script)

Clone the repo and run the setup script. It creates `.env` with a generated JWT secret and starts Docker automatically.

**Linux / macOS / Git Bash:**

```bash
git clone <repository-url>
cd "Banking App Project"
./setup.sh
```

**Windows (Command Prompt):**

```cmd
git clone <repository-url>
cd "Banking App Project"
setup.bat
```

The app will be available at `http://localhost:8000`.

### Option 2: Docker (manual)

```bash
git clone <repository-url>
cd "Banking App Project"
cp .env.example .env
```

Edit `.env` and replace `JWT_SECRET_KEY` with a secure value:

```bash
openssl rand -hex 32
```

Build and start:

```bash
docker compose up --build -d
```

The app will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

```bash
# Stop
docker compose down

# View logs
docker compose logs -f
```

### Option 3: Local development (no Docker)

**1. Clone and configure environment**

```bash
git clone <repository-url>
cd "Banking App Project"
cp .env.example .env
```

Edit `.env` and replace `JWT_SECRET_KEY` with a secure value (`openssl rand -hex 32`).

**2. Backend**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**3. Frontend**

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and proxies API requests to the backend.

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

90 tests across 10 files (87 integration, 3 unit). All tests use an isolated file-based SQLite database that is created and destroyed per session.

```bash
# With coverage report
pytest --cov=app --cov-report=html

# Run a specific test file
pytest tests/integration/test_transfers.py

# Verbose output
pytest -v
```

## Documentation

See [docs/project-info.md](docs/project-info.md) for project structure, API endpoints, architecture, and environment variables.
