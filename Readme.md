src/
main.py              # FastAPI entrypoint
db.py                # SQLModel engine/session
models/              # Project, File, Artifact schemas
routes/              # REST/WebSocket endpoints
services/            # Agent + task orchestration
agents/              # Role contracts, model router
tasks/               # Celery jobs
utils/               # Logging, state machine, helpers
native/              # PyO3 Rust crates (indexer, diff, fsops)
tests/                 # pytest suites

frontend/                # React UI (separate repo)

````

# 🤖 Autonomous Multi-Agent Software Engineer

An **AI-powered, autonomous software engineering platform** that takes a user’s goal and delivers working software through a full **Software Development Life Cycle (SDLC)** — planning, design, implementation, testing, deployment, and monitoring — without manual intervention.  
Performance-critical work is powered by native **Rust modules**; multi-agent coordination uses the **right LLM for each stage**, with provider routing across OpenAI, Anthropic, Google, Groq, and OpenRouter.

---

## 🚀 Features

- **Multi-Agent SDLC** — Planner, Designer, Implementer, Tester, Reviewer, Deployer, and Critic agents, each with specialized roles.
- **Model Routing** — Per-role model policies with fallbacks, cost/latency budgets, and multi-provider support.
- **Rust-Powered Core Ops** — High-speed indexing, diffing, and file ops via PyO3 bindings.
- **Background Execution** — Celery + Redis task queue with progress streaming over WebSocket.
- **Tool Access** — Git, Docker, shell, browser automation, cloud CLIs for real-world delivery.
- **Artifact-Driven** — All requirements, plans, designs, tests, and runbooks stored as Markdown or JSON artifacts.
- **State Machine Governance** — Prevents invalid transitions; enables loop-backs on failure.
- **Transparent UX** — Real-time project/job state, logs, diffs, and test results in the UI.

---

## 🧩 Architecture Overview

```
User Goal
│
▼
Planner Agent ──► Plan Artifact (DAG)
│
▼
Designer Agent ──► Design Specs, OpenAPI, ADRs
│
▼
Implementer Agent ──► Git Branches + Commits
│
▼
Tester Agent ──► Test Reports
│
▼
Reviewer Agent ──► Approvals / Change Requests
│
▼
Deployer Agent ──► Deployments + Runbooks
│
▼
Monitor Agent ──► Observability, Logs, Feedback
```

**Execution Model**
- **Lifecycle State Machine**: `NEW → PLANNING → DESIGN → BUILD → TEST → REVIEW → DEPLOY → MONITOR → DONE`.
- **Plan DAG Runner**: Executes planned tasks in parallel where safe, checkpoints long jobs, resumes on crash.
- **Multi-Provider Model Router**: Picks optimal LLM per role; logs cost/tokens/latency.

---

## ⚙️ Technology Stack

**Backend**
- Python 3.12, FastAPI (REST + WebSocket)
- Celery + Redis (async job queue)
- SQLModel + PostgreSQL (metadata & artifacts)
- PyO3 + Rust (indexer, diff, fsops)
- structlog (structured logging)
- Docker, GitPython, Playwright (tooling)

**Frontend (companion repo)**
- React 18 + Vite + TypeScript
- Zustand (state), TanStack Query (data fetching)
- Monaco Editor, xterm.js (code + terminal)
- TailwindCSS + shadcn/ui (UI components)
- socket.io-client (real-time events)

**AI Providers**
- OpenAI, Anthropic, Google, Groq, OpenRouter
- LiteLLM router for unified API calls

---

## 📂 Repository Structure

```
backend/
	src/
		main.py              # FastAPI entrypoint
		db.py                # SQLModel engine/session
		models/              # Project, File, Artifact schemas
		routes/              # REST/WebSocket endpoints
		services/            # Agent + task orchestration
		agents/              # Role contracts, model router
		tasks/               # Celery jobs
		utils/               # Logging, state machine, helpers
		native/              # PyO3 Rust crates (indexer, diff, fsops)
		tests/               # pytest suites

frontend/                # React UI (separate repo)
```

---

## 🔄 Workflow

1. **Discovery** — User describes the goal; system captures requirements.
2. **Planning** — Planner agent produces Plan DAG; optional human review.
3. **Design** — Designer generates architecture docs, contracts, ADRs.
4. **Build** — Implementer edits code; Reviewer + Critic enforce quality.
5. **Test** — Tester runs and expands tests; failures loop back to Build.
6. **Review** — Final approval before deploy.
7. **Deploy** — Deployer prepares and applies deployment artifacts.
8. **Monitor** — Observes deployed system; raises issues as new tasks.

---

## 📡 Real-Time Feedback

- **WebSocket events** for state changes, job progress, logs, diffs, test results.
- **UI** shows a project/job timeline, live terminal output, and PR previews.

---

## 🔐 Safety & Governance

- Sandboxed shell/Docker execution
- Secrets vault integration
- Repo boundary enforcement
- Model usage caps (cost/latency/tokens)
- Audit logs for all actions

---

## 🛠 Development

### Prerequisites
- Python 3.12+
- Rust (nightly recommended)
- Docker + Docker Compose
- Redis, PostgreSQL
- API keys for any LLM providers you intend to use

### Setup

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install Rust crates (via maturin)
cd src/native/indexer-rs && maturin develop
cd ../diff-rs && maturin develop
cd ../fsops-rs && maturin develop

# Start backend
uvicorn src.main:app --reload

# Start Celery worker
celery -A src.tasks.task_queue worker --loglevel=info
```

---

## 📜 License

MIT

---

## 📧 Contact

For questions or contributions, please open an issue or PR in this repository.
```
