# 🚀 Fuse Backend: High-Performance Automation Engine

The **Fuse Backend** is the high-concurrency, asynchronous heartbeat of the Fuse platform. It is a sophisticated REST and WebSocket API designed using a modular, "package-first" philosophy to enable secure, scalable, and intelligent workflow orchestration.

---

## 🛠️ Core Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **ORM & Database**: [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic)
- **Task Orchestration**: [Celery](https://docs.celeryq.dev/) with [Redis](https://redis.io/)
- **Security**: JWT-based Authentication, Argon2 Hashing, and AES-256 Credential Encryption
- **Communication**: WebSockets for real-time log streaming and execution feedback
- **Versioning**: Distributed as an installable package via [PyPI](https://pypi.org/project/fuse-io/)

---

## 🏗️ Architectural Pillars

### 1. The Workflow Engine
The engine parses directed acyclic graphs (DAGs) defined in JSON and manages their execution lifecycle. 
- **Atomic Execution**: Each node is an isolated execution context.
- **State Propagation**: Seamless data flow between nodes with support for complex mapping and variables.
- **Error Handling**: Built-in circuit breakers, retry logic, and fallback paths.

### 2. Modular Node System (`node_packages/`)
Every capability in Fuse is a standalone package. This ensures that the core engine remains lean while the node library can grow infinitely.
- **Isolated Runtimes**: Nodes can specify their own requirements and logic.
- **GUI Editor**: Users can create brand-new nodes via the dashboard, which are automatically scaffolded into the `node_packages/` directory.

### 3. Dynamic Plugin System (`plugin_packages/`)
Plugins allow for heavy-duty extension of the platform.
- **Manifest-Driven**: Automatic discovery and registration based on `manifest.json`.
- **Integrated Auth**: Plugins can register their own OAuth configurations and API routes.

---

## 📦 Professional Installation

### Production (via PyPI)
We recommend using **[uv](https://github.com/astral-sh/uv)** for near-instant installation and isolated environment management.

```bash
uv pip install fuse-io
fuse init
fuse start
```

### Development Environment

```bash
# Clone and enter the backend directory
cd fuse_backend

# Create and synchronize environment
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Synchronize database
fuse start --skip-browser
```

---

## ⚙️ Advanced Configuration

Configuration is managed via environment variables (loading from `.env` by default).

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./fuse.db` | Connection string (PostgreSQL recommended for production). |
| `REDIS_URL` | `None` | Required for Celery task queuing and heavy caching. |
| `SECRET_KEY` | `dev-secret` | Cryptographic key for JWTs and encryption. **Change this.** |
| `FIRST_USER_EMAIL` | `admin@fuse.io` | Default administrative account email. |
| `SERVER_HOST` | `http://localhost:5678` | Public-facing URL for OAuth callback resolution. |

---

## 🎮 Command Line Interface (CLI)

The `fuse` command is a powerful utility for managing your instance.

- **`fuse init`**: Scaffolds the `.env` configuration and initializes the database.
- **`fuse start`**: Launches the FastAPI server, runs pending migrations, and starts the UI.
- **`fuse version`**: Displays detailed version info for the engine and system environment.
- **`fuse --help`**: Comprehensive list of all available commands and flags.

---

## 🤝 Technical Contribution

Fuse Backend follows strict **Ruff** formatting and **MyPy** type-checking standards.

1. **Format Check**: `ruff check .`
2. **Type Check**: `mypy .`
3. **Run Tests**: `pytest`

### Branching Strategy
- `main`: Stable production releases.
- `develop`: Integration branch for upcoming features.
- `feature/*`: Specific feature developments.

---

**Built with Precision by [Bibek Timilsina](https://github.com/bibektimilsina)**
*Scalable. Secure. Unified.* 🌊
