# AI Assistant With Memory

An intelligent assistant platform that persists, organizes, and retrieves contextual memories across conversations and multi-agent workflows using Mem0, OpenMemory MCP, FastAPI, and React.

---

## Key Capabilities

- **Turn-Level Memory Extraction**: Automatically extracts durable facts, user preferences, project context, and communication style from natural conversations using an LLM classifier.
- **Categorized & Scoped Memory Bank**: Organizes memories into preferences, iographical, projects, and communication_style with provenance tracking (which agent/session added it).
- **Semantic Retrieval with Recency Boost**: Injects the most relevant memories into future conversations and agent prompts without duplicating context.
- **OpenMemory MCP Server**: Shares the memory bank across multiple agents (e.g. CrewAI Researcher & Writer agents) or external MCP clients (Claude, Cursor, ChatGPT).
- **User Governance UI**: ChatGPT-style memory management with view, search, inline edit, delete, pause memory learning, and full purge capabilities.

---

## Monorepo Architecture

`
ai-assistant-memory/
├── backend/          # FastAPI: chat endpoints, memory CRUD, session management
├── memory/           # Mem0 integration, extraction pipeline, OpenMemory MCP server
├── agents/           # CrewAI multi-agent workflows (shared memory pool)
├── frontend/         # React + Vite + TypeScript + Tailwind CSS UI
├── scripts/          # Automated commit and workflow helpers
└── docker-compose.yml
`

---

## Quick Start Guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.14)
- **Node.js 18+** & npm (Tested on Node v24)
- Git

### Backend Setup
`ash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
`
Interactive API docs will be available at http://localhost:8000/docs.

### Frontend Setup
`ash
cd frontend
npm install
npm run dev
`
The application interface will be live at http://localhost:5173.

---

## Development Roadmap

- [x] **Phase 0: Project Scaffolding** — Monorepo layout, FastAPI skeleton, React UI shell, commit helpers.
- [ ] **Phase 1: Memory Extraction Pipeline** — Mem0 extraction engine & category classification.
- [ ] **Phase 2: Storage & Retrieval** — Vector store wiring (Qdrant) & semantic search.
- [ ] **Phase 3: Context Injection** — Cross-session context merging & prompt enrichment.
- [ ] **Phase 4: Personalization Layer** — Style steering & memory provenance logging.
- [ ] **Phase 5: Multi-Agent Workflows** — OpenMemory MCP server & CrewAI shared memory demo.
- [ ] **Phase 6: Frontend UI** — Refined Chat & Memory Bank panels.
- [ ] **Phase 7: End-to-End Hardening** — Full lifecycle tests, privacy deletion verification.
