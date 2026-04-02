# SocialForge Integration Design

**Date:** 2026-04-02
**Status:** Approved
**Author:** Claude + João Victor Mendes

## Overview

SocialForge is an AI agent framework for social media and digital marketing, built on top of Claude Office Visualizer. It transforms squad-based agent pipelines into a real-time pixel art office simulation where non-technical users can visually manage content creation, profile diagnostics, and client operations through a chat-first interface.

**Goal:** Any non-technical user can open the browser, see agents working in the office, type what they need, and follow everything visually.

## Architecture

### Approach: SocialForge as Internal Module

SocialForge lives as a module inside the Claude Office monorepo (renamed to `socialforge`). The backend gains a Squad Engine that reads YAML squad definitions, orchestrates pipelines, and emits events to the existing WebSocket/state machine infrastructure. A single `make dev` runs everything.

### System Components

```
User (Browser)
    ↓
Frontend (Next.js + PixiJS)
  ├── ChatPanel (NEW) — Chat-first UI, squad cards, checkpoints
  ├── OfficeGame (existing) — PixiJS canvas, agents, boss
  └── PipelineWhiteboard (NEW) — Pipeline progress on whiteboard
    ↓ WebSocket
Backend (FastAPI)
  ├── Squad Engine (NEW) — Reads YAMLs, orchestrates pipelines, calls Claude API
  ├── Chat Router (NEW) — NLP to detect which squad to run
  ├── Queue Manager (NEW) — Squad queue, one active at a time
  ├── State Machine (existing) — Transforms events into visual state
  └── WebSocket + API (existing) — State broadcast
    ↓
Claude API | SQLite | Squad YAMLs
```

### Data Flow

1. User sends message via ChatPanel
2. Chat Router (via Claude) identifies the squad
3. Squad Engine loads squad.yaml + pipeline.yaml
4. Boss receives work, delegates to first agent
5. Agent enters via elevator with unique visual identity
6. Agent executes tasks via Claude API, whiteboard updates
7. Checkpoint: agent walks to boss, bubble "Ready to review!"
8. Chat shows result + Approve/Adjust buttons
9. User approves, next agent enters...
10. Pipeline complete: output saved, delivered in chat

## Squad Engine

### Location
`backend/app/core/squad_engine.py`

### Loading
- Reads all `squad.yaml` files from `socialforge/squads/` at startup
- Registers available squads with their agents, pipelines, and data
- Validates step dependencies

### Pipeline Execution

Two step types:

| Type | Behavior |
|------|----------|
| `checkpoint` | Pauses pipeline. Shows content in chat. Waits for user approval. If adjustment requested, re-executes previous step with feedback. |
| `agent` | Emits `subagent_start` to state machine (agent enters office). Builds prompt from: agent.md (persona) + task files + pipeline data + output from previous steps. Calls Claude API. On completion, emits `subagent_stop`. Saves output. |

### Context Between Steps
- Each step receives accumulated output from all previous steps
- Squad Engine maintains a `PipelineState` with full context
- Persisted to SQLite to survive restarts

### Claude API Execution
- Each agent is a Claude API call with a prompt assembled by the engine
- Prompt includes: agent persona (agent.md), squad data (pipeline/data/), previous step outputs, and the specific task
- Uses Claude API directly (not Claude Code CLI) for full control

### Retry Policy
- Agent steps retry automatically up to 3 times on Claude API failure
- Exponential backoff between retries
- After 3 failures, escalates to user via chat with error details

### Queue Manager

- `POST /api/v1/squads/start` — start or enqueue a squad
- `GET /api/v1/squads/queue` — list current queue
- `DELETE /api/v1/squads/queue/{id}` — remove from queue
- When a squad finishes, Queue Manager starts the next one automatically
- Queued squads show bubble: "Aguardando - Xº na fila"

## Agent Visual Identity

### Agent Registry
`backend/app/core/agent_registry.py` — maps squad agent IDs to fixed visuals.

| Squad | Agent | Fixed Color | Visual Trait |
|-------|-------|-------------|-------------|
| Fábrica de Conteúdo | Sol Estratégia | Gold yellow | Blonde hair, sunglasses on head |
| | Luna Pesquisa | Light blue | Round glasses, magnifying glass |
| | Davi Copy | Green | Beret, notebook in hand |
| | Bia Stories | Pink | Headphones, phone |
| | Léo Revisão | Orange | Clipboard, red pen |
| Diagnóstico | Sherlock Social | Brown | Detective hat, magnifying glass |
| | Nina Números | Purple | Square glasses, tablet with charts |
| | Max Plano | Dark blue | Tie, pointing up |
| Máq. Clientes | Rafa Preço | Dark green | Calculator, tie |
| | Clara Contrato | Wine | Document folder, glasses |
| | Dani Welcome | Turquoise | Big smile, badge |

### How It Works
- When Squad Engine emits `subagent_start`, it includes metadata: `squad_agent_id`, `display_name`, `color`, `sprite_key`
- State Machine creates Agent with these values instead of random color
- Frontend loads specific sprite sheets from `public/sprites/socialforge/` by `sprite_key`
- **Fallback:** If custom sprite doesn't exist yet, uses generic sprite with the agent's fixed color

### Sprite Specifications
- Each agent: sprite sheet with 4 states (idle, walking, typing, waiting)
- 32x32 pixels, 45-degree front/top-down perspective
- Located in `frontend/public/sprites/socialforge/`

### Status Bubbles

| Situation | Bubble |
|-----------|--------|
| Executing task | Gear icon + task name |
| Checkpoint pending | Clock icon + "Aguardando aprovação" |
| Approved | Green check icon |
| Retry in progress | Refresh icon + "Tentando novamente..." |
| Error (3 retries exhausted) | Red alert icon |
| In queue | Hourglass icon + "Aguardando - Xº na fila" |

### Checkpoint Animation
1. Agent changes to `reporting` state
2. Walks to boss (existing pathfinding)
3. Speech bubble: "Pronto pra revisar!" with delivery type icon
4. Boss changes to `reviewing` state
5. After approval in chat, agent returns to desk or exits via elevator

## ChatPanel

### Location
`frontend/src/components/chat/ChatPanel.tsx`

### Initial Screen (no active squad)
- Welcome message from SocialForge "boss"
- 3 squad cards as clickable suggestions inside the chat
- Input field with placeholder: "Descreva o que você precisa..."
- Card click: starts squad directly
- Free text: Chat Router identifies squad and confirms before starting

### During Squad Execution
- Each step appears in real-time as chat messages with agent avatar
- Checkpoints appear as special messages with:
  - Generated content (expandable if long)
  - Two buttons: **Aprovar** (green) and **Pedir Ajuste** (yellow)
  - Adjustment opens text field for feedback
- Subtle progress bar at top showing current step / total

### Checkpoint Notification
- Audio "pling" sound via Web Audio API when checkpoint needs approval
- Helps if user switched to another browser tab

### Final Output
- Pipeline completion shows summary with all generated artifacts
- "Baixar tudo" button exports outputs as ZIP
- Outputs saved in `socialforge/squads/{squad}/output/`

### Queue Display
- If squads are queued, shows discreet section below chat: "Próximo: Diagnóstico de Perfil (2º na fila)"
- Clickable to remove from queue

### Responsive Layout
- Desktop: chat left (40%), office right (60%)
- Mobile: chat fullscreen, office accessible via tab/swipe

## Pipeline Whiteboard

### New Whiteboard Mode
The existing whiteboard gains a `pipeline` mode that activates when a squad is running. Reverts to existing modes when no squad is active.

### Visual Layout
- Vertical column with pipeline steps
- Each step: rectangle with name, agent icon, status
- Active step pulses with soft glow
- Completed steps show green check
- Checkpoints have hand/pause icon
- Future steps dimmed
- Line connecting steps (simple flowchart style)

### Step Status Visuals

| Status | Visual |
|--------|--------|
| Pending | Gray, low opacity |
| Active | Agent's color, pulsing |
| Completed | Green, check |
| Checkpoint waiting | Yellow, clock icon |
| Approved | Green, double check |
| Error/retry | Red, alert icon |

### Agent-Whiteboard Animation
- When agent finishes a task, walks to whiteboard
- "Writing" animation for 1 second
- Step status updates visually
- Agent returns to desk or walks to boss (if checkpoint)

## Repository Structure

```
socialforge/
├── backend/                    # FastAPI (existing + Squad Engine)
│   └── app/
│       └── core/
│           ├── squad_engine.py     # NEW: Pipeline orchestrator
│           ├── agent_registry.py   # NEW: Agent visual identity
│           ├── chat_router.py      # NEW: NLP squad detection
│           ├── queue_manager.py    # NEW: Squad queue
│           ├── state_machine.py    # MODIFIED: Accept squad agent metadata
│           └── ...existing...
├── frontend/                   # Next.js + PixiJS (existing + ChatPanel)
│   └── src/
│       ├── components/
│       │   ├── chat/
│       │   │   └── ChatPanel.tsx       # NEW
│       │   └── game/
│       │       └── whiteboard/
│       │           └── PipelineMode.tsx # NEW
│       └── ...existing...
├── hooks/                      # Claude Office hooks (kept)
├── socialforge/                # Squad definitions
│   ├── squads/
│   │   ├── fabrica-de-conteudo/
│   │   ├── diagnostico-perfil/
│   │   └── maquina-clientes/
│   └── _socialforge/
├── docs/
├── Makefile
├── pyproject.toml
├── docker-compose.yml          # NEW: One-command deploy
├── Dockerfile                  # NEW
├── README.md                   # NEW: Non-technical focused
└── .github/
    └── workflows/              # CI
```

## Deployment

### Local Development
```bash
make install
make dev          # or make dev-tmux
# Open http://localhost:3333
```

### VPS / Production
```bash
docker compose up
# Open http://VPS-IP:3333
```

### Environment Variables
- `ANTHROPIC_API_KEY` — required, Claude API key
- `SOCIALFORGE_PORT` — optional, default 3333

## README Strategy
- "O que é o SocialForge" in 2 sentences
- Animated GIF of office with agents working
- Installation in 3 commands
- "Como usar" with screenshots
- No technical jargon

## Future (v2)
- Multiple simultaneous squads (Approach B from brainstorming)
- Custom squad creation via UI
- Custom agent sprite creation via /character-sprite skill
- Analytics dashboard (how many pipelines ran, average time, etc.)
