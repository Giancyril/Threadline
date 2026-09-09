# AI Assistant With Memory

An intelligent, context-aware assistant platform that persists, organizes, and retrieves memories across conversations and multi-agent workflows using Mem0, OpenMemory MCP, Qdrant, FastAPI, and React.

---

## Key Capabilities

- **Turn-Level Memory Extraction**: Automatically extracts durable facts, user preferences, project context, and communication styles from natural conversation turns using an LLM/heuristic classifier.
- **Categorized & Scoped Memory Bank**: Organizes memories into `preferences`, `biographical`, `projects`, and `communication_style` with provenance tracking (which agent/session added it).
- **Semantic Retrieval with Recency Boost**: Injects relevant memories into future conversations and agent prompts with temporal decay weighting without duplicating context.
- **OpenMemory MCP Server**: Shares the unified memory bank across external MCP clients (Cursor, Claude Desktop, ChatGPT) and autonomous agent teams.
- **Collaborative Multi-Agent Workflow**: Researcher and Writer agents communicate through a shared memory pool to discover technical facts and produce tailored deliverables.
- **User Governance & Privacy Suite**: View, search, inline edit, delete, pause memory learning, and execute full GDPR right-to-be-forgotten purges.

---

## Monorepo Architecture

```
ai-assistant-memory/
├── backend/          # FastAPI: chat endpoints, memory REST CRUD, session management
├── memory/           # Memory extraction pipeline, Qdrant vector index, OpenMemory MCP server
├── agents/           # Multi-agent workflows with shared memory pool
├── frontend/         # React + Vite + TypeScript + Tailwind CSS UI
└── scripts/          # Automated commit and workflow helpers
```

---

## Quick Start Guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.14)
- **Node.js 18+** & npm (Tested on Node v24)
- Git

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Interactive API docs are live at `http://localhost:8000/docs`.

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The application interface is live at `http://localhost:5173`.

---

## Verification & Testing

To run the complete automated test suite across all monorepo layers:
```bash
python -m pytest memory/tests/ backend/tests/ agents/tests/ -v
```

To validate the frontend build:
```bash
cd frontend && npm run build
```

---

## Development Roadmap Status

- [x] **Phase 0: Project Scaffolding** — Monorepo layout, FastAPI skeleton, React UI shell.
- [x] **Phase 1: Memory Extraction Pipeline** — Extraction engine & category classification.
- [x] **Phase 2: Storage & Retrieval Layer** — Vector store wiring (Qdrant) & semantic search with recency decay.
- [x] **Phase 3: Context Injection Engine** — Cross-session context merging & prompt enrichment.
- [x] **Phase 4: Memory Management REST API** — Governance endpoints, inline editing, privacy learning toggle.
- [x] **Phase 5: OpenMemory MCP Server & Multi-Agent** — Model Context Protocol server & shared memory agent demo.
- [x] **Phase 6: Frontend UI Integration** — Real-time chat citations, live memory bank browser, pause toggle.
- [x] **Phase 7: End-to-End Hardening** — Full multi-session user lifecycle tests & verification.
