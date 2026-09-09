# Threadline: Advanced AI Assistant with Cognitive Memory Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-indigo.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![Version](https://img.shields.io/badge/Version-1.2.0-emerald.svg)]()

**Threadline** is an enterprise-grade, memory-augmented AI platform designed for persistent, multi-agent contextual intelligence. Moving beyond ephemeral chat sessions and simple vector storage, Threadline implements a full cognitive lifecycle: knowledge graphing, temporal longevity decay, immutable versioning with contradiction auditing, sliding-window semantic drift tracking, and cryptographic multi-agent federation.

---

## 5 Advanced Architectural Features

### 1. Dynamic Knowledge Graph Extraction (`/api/v1/graph`)
- **Entity & Relation Parsing**: Extracts semantic triples `(Subject, Relation, Object)` alongside vector embeddings.
- **Graph Visualizer**: Interactive network canvas displaying interconnected entities, clusters, and edge weights.
- **Transitive Query Expansion**: Traverses multi-hop entity relationships to retrieve contextually linked memories.

### 2. Temporal Longevity & Exponential Decay (`/api/v1/temporal`)
- **3-Tier Longevity Architecture**:
  - `Permanent`: Foundational facts and preferences with zero temporal decay.
  - `Project-Bound`: Context tied to ongoing workflows with a 30-day half-life.
  - `Ephemeral`: High-frequency, temporary instructions expiring automatically within 24 hours.
- **Half-Life Decay Sweeper**: Automated background worker attenuating relevance scores and archiving expired memories.

### 3. Memory Versioning & Contradiction Audit Trail (`/api/v1/versioning`)
- **Immutable Snapshots**: Every write operation generates an immutable version record preserving historical states.
- **Contradiction Confidence Scorer**: Heuristic and NLP engine detecting factual and preference conflicts between new statements and historical memories.
- **Audit Timeline & 1-Click Rollback**: Visual diff modal comparing historical changes with instant restoration capabilities.

### 4. Semantic Drift & Topic Clustering (`/api/v1/analytics`)
- **Sliding-Window Centroid Trajectory**: Monitors cosine distance displacement across temporal windows to compute drift velocity and acceleration.
- **Unsupervised Density Clustering**: Groups memory vectors into dynamic topic taxonomies with cohesion scoring.
- **Preference Divergence Alerts**: Notifies users when their technical stacks, communication tones, or workflows diverge from previous baselines.

### 5. Cross-Agent Memory Federation Hub (`/api/v1/federation`)
- **Threadline Memory Exchange Format (TMEF v1.0)**: Standardized, portable memory exchange schema.
- **Cryptographic HMAC-SHA256 Seals**: Tamper-proof digital signatures protecting memory payloads during cross-agent federation.
- **Selective Privacy Scrubber**: Automated regex and NER pipeline redacting API keys, bearer tokens, emails, phone numbers, and IPs before export.
- **3-Way Reconciliation Engine**: Reconciles incoming federated bundles, preventing duplication and resolving multi-agent conflicts.

---

## Monorepo Layout

```
Threadline/
├── backend/                  # FastAPI Application Core
│   ├── app/
│   │   ├── api/             # REST Routers (Chat, Memories, Graph, Temporal, Versioning, Analytics, Federation)
│   │   ├── core/            # Configuration & Settings (v1.2.0)
│   │   └── main.py          # Application Entrypoint & OpenAPI schema
├── memory/                   # Cognitive Engine & Storage Core
│   ├── src/
│   │   ├── knowledge_graph.py       # Knowledge Graph Extraction
│   │   ├── temporal_longevity.py    # Temporal Decay Engine
│   │   ├── versioned_store.py       # Immutable Snapshot Store
│   │   ├── contradiction_scorer.py  # Contradiction Confidence Scorer
│   │   ├── rollback_service.py      # Rollback Orchestration
│   │   ├── drift_calculator.py      # Centroid Drift Engine
│   │   ├── topic_clustering.py      # Topic Clustering Engine
│   │   ├── divergence_alerter.py    # Preference Shift Detection
│   │   ├── federation_crypto.py     # HMAC-SHA256 Signatures
│   │   ├── privacy_scrubber.py      # PII Redaction
│   │   └── federation_merger.py     # 3-Way Merge Resolver
│   └── tests/                       # Comprehensive Automated Test Suites
├── agents/                   # Autonomous Multi-Agent Collaborative Workflows
├── frontend/                 # Modern React 19 + TypeScript + Tailwind UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── Analytics/           # Semantic Drift & Topic Cluster Views
│   │   │   ├── Federation/          # TMEF Export/Import Wizard
│   │   │   ├── Graph/               # Interactive Knowledge Graph
│   │   │   ├── MemoryPanel/         # Memory Bank & Version History Modal
│   │   │   ├── Chat/                # Conversation Interface
│   │   │   └── Layout/              # Navigation Sidebar
```

---

## Getting Started Locally

### Prerequisites
- **Python 3.10+** (Fully compatible with Python 3.14)
- **Node.js 18+** & npm
- Git

### Backend Setup
```bash
# Navigate to backend and install dependencies
cd backend
pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
Interactive documentation is available at `http://localhost:8000/docs`.

### Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd frontend
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running the Automated Test Suite

Run the full suite of unit and integration tests across all modules:
```bash
# Run all tests
python -m pytest memory/tests/ backend/tests/ -v

# Run feature-specific test suites
python -m pytest memory/tests/test_graph.py -v
python -m pytest memory/tests/test_temporal.py -v
python -m pytest memory/tests/test_versioning.py -v
python -m pytest memory/tests/test_drift.py -v
python -m pytest memory/tests/test_federation.py -v
```

---

## API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/chat` | `POST` | Natural chat turn with memory recall & extraction |
| `/api/v1/memories` | `GET`, `POST`, `DELETE` | CRUD operations on memory store |
| `/api/v1/graph` | `GET` | Knowledge graph nodes and edges |
| `/api/v1/temporal/decay` | `POST` | Trigger temporal decay evaluation & sweep |
| `/api/v1/versioning/{id}/history` | `GET` | Memory version snapshots & contradiction diffs |
| `/api/v1/versioning/rollback` | `POST` | Restore memory to prior historical version |
| `/api/v1/analytics/drift` | `GET` | Sliding-window semantic drift & divergence alerts |
| `/api/v1/analytics/clusters` | `GET` | Topic cluster taxonomy and member memories |
| `/api/v1/federation/export` | `POST` | Export signed TMEF v1.0 memory bundle |
| `/api/v1/federation/import` | `POST` | Reconcile and import federated memory bundle |

---

## License

MIT License © 2026 Threadline Contributors
