# SocialForge Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate SocialForge AI agent squads into Claude Office Visualizer, creating a chat-first product where non-technical users visually manage social media content pipelines.

**Architecture:** SocialForge is an internal module within the Claude Office monorepo. A new Squad Engine reads YAML squad definitions, orchestrates pipelines via Claude API, and emits events to the existing state machine. The frontend gains a ChatPanel for interaction and a pipeline whiteboard mode for visual progress tracking.

**Tech Stack:** Python/FastAPI (backend), Next.js/PixiJS/React (frontend), Claude API (agent execution), SQLite (persistence), Zustand (state), WebSocket (real-time sync)

**Spec:** `docs/superpowers/specs/2026-04-02-socialforge-integration-design.md`

---

## File Structure

### New Files - Backend

| File | Responsibility |
|------|---------------|
| `backend/app/core/squad_engine.py` | Pipeline orchestrator: loads YAMLs, executes steps, manages context, retries |
| `backend/app/core/squad_loader.py` | Reads and validates squad.yaml + pipeline.yaml files at startup |
| `backend/app/core/agent_registry.py` | Maps squad agent IDs to fixed visual identity (color, name, sprite_key) |
| `backend/app/core/chat_router.py` | Uses Claude API to detect which squad matches user's free-text input |
| `backend/app/core/queue_manager.py` | Squad execution queue: one active, FIFO for pending |
| `backend/app/models/squads.py` | Pydantic models: Squad, Pipeline, PipelineStep, PipelineState, AgentIdentity |
| `backend/app/api/routes/squads.py` | REST endpoints: start, queue, approve, status, chat |
| `backend/tests/test_squad_loader.py` | Tests for YAML loading and validation |
| `backend/tests/test_squad_engine.py` | Tests for pipeline execution, retries, checkpoints |
| `backend/tests/test_agent_registry.py` | Tests for agent identity mapping |
| `backend/tests/test_chat_router.py` | Tests for squad detection from free text |
| `backend/tests/test_queue_manager.py` | Tests for queue FIFO, auto-start next |
| `backend/tests/test_squad_routes.py` | Tests for API endpoints |

### New Files - Frontend

| File | Responsibility |
|------|---------------|
| `frontend/src/components/chat/ChatPanel.tsx` | Main chat interface: messages, squad cards, checkpoint approval |
| `frontend/src/components/chat/ChatMessage.tsx` | Individual message component (user, agent, system) |
| `frontend/src/components/chat/CheckpointMessage.tsx` | Checkpoint message with approve/adjust buttons + sound |
| `frontend/src/components/chat/SquadCard.tsx` | Clickable squad suggestion card |
| `frontend/src/components/chat/ChatInput.tsx` | Message input with send button |
| `frontend/src/components/chat/QueueIndicator.tsx` | Shows queued squads below chat |
| `frontend/src/components/game/whiteboard/PipelineMode.tsx` | Whiteboard mode showing pipeline steps visually |
| `frontend/src/stores/chatStore.ts` | Zustand store for chat messages, active squad, checkpoint state |
| `frontend/src/stores/squadStore.ts` | Zustand store for squad definitions, queue, pipeline progress |
| `frontend/src/hooks/useSquadWebSocket.ts` | WebSocket handler for squad-specific events |
| `frontend/src/types/squads.ts` | TypeScript types for squads, pipeline, chat |
| `frontend/src/constants/agentIdentities.ts` | Fixed visual identities for all 11 agents |
| `frontend/src/sounds/checkpoint.mp3` | Checkpoint notification sound |

### Modified Files

| File | Changes |
|------|---------|
| `backend/app/main.py` | Mount squad routes, initialize squad loader on startup |
| `backend/app/core/state_machine.py` | Accept squad agent metadata (display_name, color, sprite_key) in `_create_agent()` |
| `backend/app/models/events.py` | Add squad-related fields to EventData (squad_id, squad_agent_id, display_name, sprite_key, pipeline_step) |
| `backend/app/models/sessions.py` | Add pipeline_state to GameState |
| `frontend/src/components/game/OfficeGame.tsx` | Import ChatPanel, adjust layout (40/60 split) |
| `frontend/src/components/game/Whiteboard.tsx` | Add pipeline mode (mode 11) |
| `frontend/src/components/game/AgentSprite.tsx` | Use fixed color from agent identity when sprite_key present |
| `frontend/src/stores/gameStore.ts` | Add squad pipeline state, expose to selectors |
| `frontend/src/hooks/useWebSocketEvents.ts` | Handle squad events (pipeline_update, checkpoint) |
| `frontend/src/app/page.tsx` | Responsive layout: chat left, office right |
| `socialforge/` | Copy squad definitions from zip |

---

## Chunk 1: Foundation — Models, Loader, and Squad Data

### Task 1: Copy SocialForge Squad Definitions

**Files:**
- Create: `socialforge/squads/` (entire directory tree from zip)
- Create: `socialforge/_socialforge/`

- [ ] **Step 1: Copy squad data from extracted zip**

```bash
cp -r /tmp/socialforge-inspect/socialforge/squads /root/claude-office/socialforge/squads
cp -r /tmp/socialforge-inspect/socialforge/_socialforge /root/claude-office/socialforge/_socialforge
mkdir -p /root/claude-office/socialforge/squads/fabrica-de-conteudo/output
mkdir -p /root/claude-office/socialforge/squads/diagnostico-perfil/output
mkdir -p /root/claude-office/socialforge/squads/maquina-clientes/output
```

- [ ] **Step 2: Verify directory structure**

```bash
find /root/claude-office/socialforge -type f | wc -l
# Expected: ~60+ files
ls /root/claude-office/socialforge/squads/
# Expected: diagnostico-perfil  fabrica-de-conteudo  maquina-clientes
```

- [ ] **Step 3: Commit**

```bash
git add socialforge/
git commit -m "feat: add SocialForge squad definitions (3 squads, 11 agents)"
```

---

### Task 2: Squad Pydantic Models

**Files:**
- Create: `backend/app/models/squads.py`
- Test: `backend/tests/test_squad_models.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_squad_models.py
import pytest
from app.models.squads import (
    AgentDefinition,
    AgentIdentity,
    CheckpointState,
    PipelineState,
    PipelineStep,
    PipelineStepStatus,
    PipelineStepType,
    Squad,
    SquadPipeline,
    SquadQueueItem,
    SquadStatus,
)


def test_agent_definition_from_yaml_dict():
    data = {"id": "estrategista", "name": "Sol Estratégia", "icon": "🧠"}
    agent = AgentDefinition(**data)
    assert agent.id == "estrategista"
    assert agent.name == "Sol Estratégia"
    assert agent.icon == "🧠"


def test_pipeline_step_agent_type():
    step = PipelineStep(
        id="step-02",
        name="Pesquisa de Datas",
        type=PipelineStepType.AGENT,
        agent="pesquisador",
        tasks=["pesquisar-datas-nicho", "identificar-tendencias"],
        file="steps/step-02-pesquisa-datas.md",
        depends_on="step-01",
    )
    assert step.type == PipelineStepType.AGENT
    assert step.agent == "pesquisador"
    assert len(step.tasks) == 2


def test_pipeline_step_checkpoint_type():
    step = PipelineStep(
        id="step-01",
        name="Briefing do Cliente",
        type=PipelineStepType.CHECKPOINT,
        file="steps/step-01-briefing.md",
    )
    assert step.type == PipelineStepType.CHECKPOINT
    assert step.agent is None


def test_squad_model():
    squad = Squad(
        name="Fábrica de Conteúdo",
        code="fabrica-de-conteudo",
        description="Transforms briefing into content",
        icon="🔥",
        version="1.0.0",
        agents=[
            AgentDefinition(id="estrategista", name="Sol Estratégia", icon="🧠"),
        ],
        pipeline=SquadPipeline(
            name="Pipeline Test",
            steps=[
                PipelineStep(
                    id="step-01",
                    name="Briefing",
                    type=PipelineStepType.CHECKPOINT,
                    file="steps/step-01.md",
                ),
            ],
        ),
        data_files=["pipeline/data/briefing-coleta.md"],
        squad_dir="/path/to/squad",
    )
    assert squad.code == "fabrica-de-conteudo"
    assert len(squad.agents) == 1
    assert len(squad.pipeline.steps) == 1


def test_pipeline_state_initial():
    state = PipelineState(
        squad_code="fabrica-de-conteudo",
        session_id="test-session",
        total_steps=12,
    )
    assert state.current_step_index == 0
    assert state.status == SquadStatus.PENDING
    assert state.step_states == {}
    assert state.outputs == {}


def test_pipeline_state_progress():
    state = PipelineState(
        squad_code="fabrica-de-conteudo",
        session_id="test-session",
        total_steps=12,
        current_step_index=3,
        status=SquadStatus.RUNNING,
        step_states={"step-01": PipelineStepStatus.COMPLETED, "step-02": PipelineStepStatus.COMPLETED},
    )
    assert state.current_step_index == 3
    assert state.status == SquadStatus.RUNNING


def test_checkpoint_state():
    cs = CheckpointState(
        step_id="step-03",
        step_name="Aprovação das Datas",
        content="Datas encontradas: ...",
        awaiting_approval=True,
    )
    assert cs.awaiting_approval is True
    assert cs.approved is None


def test_agent_identity():
    identity = AgentIdentity(
        squad_agent_id="estrategista",
        display_name="Sol Estratégia",
        color="#FFD700",
        sprite_key="sol-estrategia",
        icon="🧠",
    )
    assert identity.color == "#FFD700"
    assert identity.sprite_key == "sol-estrategia"


def test_squad_queue_item():
    item = SquadQueueItem(
        id="queue-1",
        squad_code="diagnostico-perfil",
        squad_name="Diagnóstico de Perfil",
        position=2,
    )
    assert item.position == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_squad_models.py -v
```
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write the models**

```python
# backend/app/models/squads.py
"""Pydantic models for SocialForge squad definitions and pipeline state."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PipelineStepType(StrEnum):
    AGENT = "agent"
    CHECKPOINT = "checkpoint"


class PipelineStepStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    RETRY = "retry"
    ERROR = "error"


class SquadStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"  # At checkpoint
    COMPLETED = "completed"
    ERROR = "error"


class AgentDefinition(BaseModel):
    """Agent definition from squad.yaml."""

    id: str
    name: str
    icon: str


class PipelineStep(BaseModel):
    """A single step in a squad pipeline."""

    id: str
    name: str
    type: PipelineStepType
    file: str
    agent: str | None = None
    tasks: list[str] = Field(default_factory=list)
    depends_on: str | None = None


class SquadPipeline(BaseModel):
    """Pipeline definition from pipeline.yaml."""

    name: str
    steps: list[PipelineStep]
    checkpoints: list[str] = Field(default_factory=list)


class Squad(BaseModel):
    """Complete squad definition loaded from YAML files."""

    name: str
    code: str
    description: str
    icon: str
    version: str
    agents: list[AgentDefinition]
    pipeline: SquadPipeline
    data_files: list[str] = Field(default_factory=list)
    squad_dir: str  # Absolute path to squad directory


class AgentIdentity(BaseModel):
    """Fixed visual identity for a squad agent."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    squad_agent_id: str
    display_name: str
    color: str  # Hex color
    sprite_key: str
    icon: str


class CheckpointState(BaseModel):
    """State of a checkpoint awaiting approval."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    step_id: str
    step_name: str
    content: str
    awaiting_approval: bool = True
    approved: bool | None = None
    feedback: str | None = None


class PipelineState(BaseModel):
    """Runtime state of an executing pipeline."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    squad_code: str
    session_id: str
    total_steps: int
    current_step_index: int = 0
    status: SquadStatus = SquadStatus.PENDING
    step_states: dict[str, PipelineStepStatus] = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)  # step_id -> output text
    checkpoint: CheckpointState | None = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None


class SquadQueueItem(BaseModel):
    """A squad waiting in the execution queue."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    squad_code: str
    squad_name: str
    position: int
    user_input: str | None = None  # Original user message that triggered this
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_squad_models.py -v
```
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/squads.py backend/tests/test_squad_models.py
git commit -m "feat: add SocialForge Pydantic models for squads, pipelines, and agent identities"
```

---

### Task 3: Squad Loader

**Files:**
- Create: `backend/app/core/squad_loader.py`
- Test: `backend/tests/test_squad_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_squad_loader.py
import pytest
from pathlib import Path

from app.core.squad_loader import SquadLoader
from app.models.squads import PipelineStepType

SQUADS_DIR = Path(__file__).resolve().parents[2] / "socialforge" / "squads"


class TestSquadLoader:
    def setup_method(self):
        self.loader = SquadLoader(squads_dir=SQUADS_DIR)

    def test_load_all_squads(self):
        squads = self.loader.load_all()
        assert len(squads) == 3
        codes = {s.code for s in squads.values()}
        assert codes == {"fabrica-de-conteudo", "diagnostico-perfil", "maquina-clientes"}

    def test_fabrica_has_5_agents(self):
        squads = self.loader.load_all()
        fabrica = squads["fabrica-de-conteudo"]
        assert len(fabrica.agents) == 5
        agent_ids = {a.id for a in fabrica.agents}
        assert "estrategista" in agent_ids
        assert "pesquisador" in agent_ids
        assert "copywriter" in agent_ids
        assert "roteirista-stories" in agent_ids
        assert "revisor" in agent_ids

    def test_fabrica_pipeline_has_12_steps(self):
        squads = self.loader.load_all()
        fabrica = squads["fabrica-de-conteudo"]
        assert len(fabrica.pipeline.steps) == 12

    def test_pipeline_step_types(self):
        squads = self.loader.load_all()
        fabrica = squads["fabrica-de-conteudo"]
        checkpoints = [s for s in fabrica.pipeline.steps if s.type == PipelineStepType.CHECKPOINT]
        agent_steps = [s for s in fabrica.pipeline.steps if s.type == PipelineStepType.AGENT]
        assert len(checkpoints) == 6
        assert len(agent_steps) == 6

    def test_diagnostico_has_3_agents(self):
        squads = self.loader.load_all()
        diag = squads["diagnostico-perfil"]
        assert len(diag.agents) == 3

    def test_maquina_has_3_agents(self):
        squads = self.loader.load_all()
        maq = squads["maquina-clientes"]
        assert len(maq.agents) == 3

    def test_get_squad_by_code(self):
        squads = self.loader.load_all()
        assert self.loader.get("fabrica-de-conteudo") is not None
        assert self.loader.get("nonexistent") is None

    def test_squad_dir_is_set(self):
        squads = self.loader.load_all()
        fabrica = squads["fabrica-de-conteudo"]
        assert "fabrica-de-conteudo" in fabrica.squad_dir

    def test_data_files_loaded(self):
        squads = self.loader.load_all()
        fabrica = squads["fabrica-de-conteudo"]
        assert len(fabrica.data_files) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_squad_loader.py -v
```
Expected: FAIL

- [ ] **Step 3: Write the loader**

```python
# backend/app/core/squad_loader.py
"""Loads and validates SocialForge squad definitions from YAML files."""

import logging
from pathlib import Path

import yaml

from app.models.squads import (
    AgentDefinition,
    PipelineStep,
    PipelineStepType,
    Squad,
    SquadPipeline,
)

logger = logging.getLogger(__name__)


class SquadLoader:
    """Reads squad.yaml and pipeline.yaml files from the squads directory."""

    def __init__(self, squads_dir: str | Path):
        self.squads_dir = Path(squads_dir)
        self._squads: dict[str, Squad] = {}

    def load_all(self) -> dict[str, Squad]:
        """Load all squad definitions. Returns dict of code -> Squad."""
        if self._squads:
            return self._squads

        if not self.squads_dir.exists():
            logger.warning("Squads directory not found: %s", self.squads_dir)
            return {}

        for squad_dir in sorted(self.squads_dir.iterdir()):
            if not squad_dir.is_dir() or squad_dir.name.startswith("_"):
                continue
            squad_yaml = squad_dir / "squad.yaml"
            if not squad_yaml.exists():
                continue
            try:
                squad = self._load_squad(squad_dir)
                self._squads[squad.code] = squad
                logger.info("Loaded squad: %s (%d agents, %d steps)",
                            squad.name, len(squad.agents), len(squad.pipeline.steps))
            except Exception:
                logger.exception("Failed to load squad from %s", squad_dir)

        return self._squads

    def get(self, code: str) -> Squad | None:
        """Get a squad by code. Loads all if not yet loaded."""
        if not self._squads:
            self.load_all()
        return self._squads.get(code)

    def list_squads(self) -> list[dict]:
        """Return summary list of available squads."""
        if not self._squads:
            self.load_all()
        return [
            {
                "code": s.code,
                "name": s.name,
                "description": s.description,
                "icon": s.icon,
                "agent_count": len(s.agents),
                "step_count": len(s.pipeline.steps),
            }
            for s in self._squads.values()
        ]

    def _load_squad(self, squad_dir: Path) -> Squad:
        """Load a single squad from its directory."""
        with open(squad_dir / "squad.yaml") as f:
            raw = yaml.safe_load(f)

        agents = [AgentDefinition(**a) for a in raw.get("agents", [])]

        # Load pipeline
        pipeline_ref = raw.get("pipeline", {}).get("entry", "pipeline/pipeline.yaml")
        pipeline_path = squad_dir / pipeline_ref
        pipeline = self._load_pipeline(pipeline_path)

        data_files = raw.get("data", [])

        return Squad(
            name=raw["name"],
            code=raw["code"],
            description=raw.get("description", ""),
            icon=raw.get("icon", ""),
            version=raw.get("version", "1.0.0"),
            agents=agents,
            pipeline=pipeline,
            data_files=data_files,
            squad_dir=str(squad_dir),
        )

    def _load_pipeline(self, pipeline_path: Path) -> SquadPipeline:
        """Load pipeline definition from YAML."""
        with open(pipeline_path) as f:
            raw = yaml.safe_load(f)

        steps = []
        for step_raw in raw.get("steps", []):
            step_type = PipelineStepType(step_raw.get("type", "checkpoint"))
            steps.append(PipelineStep(
                id=step_raw["id"],
                name=step_raw["name"],
                type=step_type,
                file=step_raw.get("file", ""),
                agent=step_raw.get("agent"),
                tasks=step_raw.get("tasks", []),
                depends_on=step_raw.get("depends_on"),
            ))

        return SquadPipeline(
            name=raw.get("name", "Pipeline"),
            steps=steps,
            checkpoints=raw.get("checkpoints", []),
        )
```

- [ ] **Step 4: Run tests**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_squad_loader.py -v
```
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/squad_loader.py backend/tests/test_squad_loader.py
git commit -m "feat: add SquadLoader to read and validate YAML squad definitions"
```

---

### Task 4: Agent Registry (Visual Identity)

**Files:**
- Create: `backend/app/core/agent_registry.py`
- Test: `backend/tests/test_agent_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_agent_registry.py
import pytest
from app.core.agent_registry import AgentRegistry


class TestAgentRegistry:
    def setup_method(self):
        self.registry = AgentRegistry()

    def test_get_identity_fabrica_sol(self):
        identity = self.registry.get_identity("fabrica-de-conteudo", "estrategista")
        assert identity is not None
        assert identity.display_name == "Sol Estratégia"
        assert identity.color == "#FFD700"
        assert identity.sprite_key == "sol-estrategia"
        assert identity.icon == "🧠"

    def test_get_identity_fabrica_luna(self):
        identity = self.registry.get_identity("fabrica-de-conteudo", "pesquisador")
        assert identity.display_name == "Luna Pesquisa"
        assert identity.color == "#87CEEB"

    def test_get_identity_fabrica_davi(self):
        identity = self.registry.get_identity("fabrica-de-conteudo", "copywriter")
        assert identity.display_name == "Davi Copy"
        assert identity.color == "#4CAF50"

    def test_get_identity_fabrica_bia(self):
        identity = self.registry.get_identity("fabrica-de-conteudo", "roteirista-stories")
        assert identity.display_name == "Bia Stories"
        assert identity.color == "#FF69B4"

    def test_get_identity_fabrica_leo(self):
        identity = self.registry.get_identity("fabrica-de-conteudo", "revisor")
        assert identity.display_name == "Léo Revisão"
        assert identity.color == "#FF8C00"

    def test_get_identity_diagnostico_sherlock(self):
        identity = self.registry.get_identity("diagnostico-perfil", "investigador")
        assert identity.display_name == "Sherlock Social"
        assert identity.color == "#8B4513"

    def test_get_identity_diagnostico_nina(self):
        identity = self.registry.get_identity("diagnostico-perfil", "analista")
        assert identity.display_name == "Nina Números"
        assert identity.color == "#9C27B0"

    def test_get_identity_diagnostico_max(self):
        identity = self.registry.get_identity("diagnostico-perfil", "estrategista-perfil")
        assert identity.display_name == "Max Plano"
        assert identity.color == "#1A237E"

    def test_get_identity_maquina_rafa(self):
        identity = self.registry.get_identity("maquina-clientes", "consultor")
        assert identity.display_name == "Rafa Preço"
        assert identity.color == "#2E7D32"

    def test_get_identity_maquina_clara(self):
        identity = self.registry.get_identity("maquina-clientes", "juridico")
        assert identity.display_name == "Clara Contrato"
        assert identity.color == "#880E4F"

    def test_get_identity_maquina_dani(self):
        identity = self.registry.get_identity("maquina-clientes", "onboarding")
        assert identity.display_name == "Dani Welcome"
        assert identity.color == "#00BCD4"

    def test_unknown_agent_returns_none(self):
        identity = self.registry.get_identity("fabrica-de-conteudo", "nonexistent")
        assert identity is None

    def test_unknown_squad_returns_none(self):
        identity = self.registry.get_identity("nonexistent", "estrategista")
        assert identity is None

    def test_all_11_agents_registered(self):
        count = self.registry.total_agents()
        assert count == 11
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_agent_registry.py -v
```

- [ ] **Step 3: Write the registry**

```python
# backend/app/core/agent_registry.py
"""Fixed visual identities for all SocialForge agents."""

from app.models.squads import AgentIdentity

# All 11 agents with fixed visual identity
_IDENTITIES: dict[str, dict[str, AgentIdentity]] = {
    "fabrica-de-conteudo": {
        "estrategista": AgentIdentity(
            squad_agent_id="estrategista",
            display_name="Sol Estratégia",
            color="#FFD700",
            sprite_key="sol-estrategia",
            icon="🧠",
        ),
        "pesquisador": AgentIdentity(
            squad_agent_id="pesquisador",
            display_name="Luna Pesquisa",
            color="#87CEEB",
            sprite_key="luna-pesquisa",
            icon="🔍",
        ),
        "copywriter": AgentIdentity(
            squad_agent_id="copywriter",
            display_name="Davi Copy",
            color="#4CAF50",
            sprite_key="davi-copy",
            icon="✍️",
        ),
        "roteirista-stories": AgentIdentity(
            squad_agent_id="roteirista-stories",
            display_name="Bia Stories",
            color="#FF69B4",
            sprite_key="bia-stories",
            icon="📱",
        ),
        "revisor": AgentIdentity(
            squad_agent_id="revisor",
            display_name="Léo Revisão",
            color="#FF8C00",
            sprite_key="leo-revisao",
            icon="✅",
        ),
    },
    "diagnostico-perfil": {
        "investigador": AgentIdentity(
            squad_agent_id="investigador",
            display_name="Sherlock Social",
            color="#8B4513",
            sprite_key="sherlock-social",
            icon="🕵️",
        ),
        "analista": AgentIdentity(
            squad_agent_id="analista",
            display_name="Nina Números",
            color="#9C27B0",
            sprite_key="nina-numeros",
            icon="📊",
        ),
        "estrategista-perfil": AgentIdentity(
            squad_agent_id="estrategista-perfil",
            display_name="Max Plano",
            color="#1A237E",
            sprite_key="max-plano",
            icon="🎯",
        ),
    },
    "maquina-clientes": {
        "consultor": AgentIdentity(
            squad_agent_id="consultor",
            display_name="Rafa Preço",
            color="#2E7D32",
            sprite_key="rafa-preco",
            icon="💰",
        ),
        "juridico": AgentIdentity(
            squad_agent_id="juridico",
            display_name="Clara Contrato",
            color="#880E4F",
            sprite_key="clara-contrato",
            icon="📋",
        ),
        "onboarding": AgentIdentity(
            squad_agent_id="onboarding",
            display_name="Dani Welcome",
            color="#00BCD4",
            sprite_key="dani-welcome",
            icon="🤝",
        ),
    },
}


class AgentRegistry:
    """Provides fixed visual identities for SocialForge agents."""

    def get_identity(self, squad_code: str, agent_id: str) -> AgentIdentity | None:
        """Get the fixed identity for a squad agent."""
        squad_agents = _IDENTITIES.get(squad_code)
        if not squad_agents:
            return None
        return squad_agents.get(agent_id)

    def total_agents(self) -> int:
        """Total number of registered agent identities."""
        return sum(len(agents) for agents in _IDENTITIES.values())
```

- [ ] **Step 4: Run tests**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_agent_registry.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/agent_registry.py backend/tests/test_agent_registry.py
git commit -m "feat: add AgentRegistry with fixed visual identities for all 11 agents"
```

---

## Chunk 2: Squad Engine — Pipeline Orchestration

### Task 5: Add Squad Fields to EventData

**Files:**
- Modify: `backend/app/models/events.py`
- Modify: `backend/app/models/sessions.py`

- [ ] **Step 1: Add squad fields to EventData**

In `backend/app/models/events.py`, add these fields to the `EventData` class:

```python
# Squad-related fields
squad_id: str | None = None
squad_agent_id: str | None = None
display_name: str | None = None
sprite_key: str | None = None
agent_color: str | None = None
pipeline_step: str | None = None
pipeline_step_name: str | None = None
```

- [ ] **Step 2: Add PipelineState to GameState**

In `backend/app/models/sessions.py`, import and add:

```python
from app.models.squads import PipelineState, SquadQueueItem

# Add to GameState class:
pipeline_state: PipelineState | None = None
squad_queue: list[SquadQueueItem] = Field(default_factory=list)
```

- [ ] **Step 3: Run existing tests to verify no breakage**

```bash
cd /root/claude-office && uv run pytest backend/tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/events.py backend/app/models/sessions.py
git commit -m "feat: add squad-related fields to EventData and GameState models"
```

---

### Task 6: Modify State Machine for Squad Agents

**Files:**
- Modify: `backend/app/core/state_machine.py`
- Test: `backend/tests/test_state_machine_squad.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_state_machine_squad.py
"""Tests for state machine handling squad agent metadata."""
import pytest
from datetime import datetime

from app.core.state_machine import StateMachine
from app.models.events import Event, EventData, EventType


def make_event(event_type: EventType, **kwargs) -> Event:
    return Event(
        event_type=event_type,
        session_id="test-session",
        timestamp=datetime.now(),
        data=EventData(**kwargs),
    )


class TestStateMachineSquadAgents:
    def setup_method(self):
        self.sm = StateMachine()
        # Start a session first
        self.sm.transition(make_event(
            EventType.SESSION_START,
            project_name="test",
        ))

    def test_create_agent_with_squad_metadata(self):
        """When subagent_start has squad fields, agent uses them."""
        event = make_event(
            EventType.SUBAGENT_START,
            agent_id="subagent_sol",
            task_description="Criar macroplano",
            squad_id="fabrica-de-conteudo",
            squad_agent_id="estrategista",
            display_name="Sol Estratégia",
            agent_color="#FFD700",
            sprite_key="sol-estrategia",
        )
        self.sm.transition(event)
        agent = self.sm.agents.get("subagent_sol")
        assert agent is not None
        assert agent.name == "Sol Estratégia"
        assert agent.color == "#FFD700"

    def test_create_agent_without_squad_metadata_uses_defaults(self):
        """Normal subagents still work with random colors."""
        event = make_event(
            EventType.SUBAGENT_START,
            agent_id="subagent_normal",
            task_description="Run tests",
        )
        self.sm.transition(event)
        agent = self.sm.agents.get("subagent_normal")
        assert agent is not None
        assert agent.name is not None  # Auto-generated
        assert agent.color is not None  # Random color
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_state_machine_squad.py -v
```

- [ ] **Step 3: Modify `_create_agent()` in state_machine.py**

Find the `_create_agent` method and modify it to check for squad metadata in EventData. If `display_name` and `agent_color` are present, use them instead of random values:

```python
# In _create_agent method, after building the agent:
# If squad metadata is provided, override name and color
if event_data.display_name:
    agent.name = event_data.display_name
if event_data.agent_color:
    agent.color = event_data.agent_color
```

- [ ] **Step 4: Run tests**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_state_machine_squad.py -v
cd /root/claude-office && uv run pytest backend/tests/ -v  # Ensure no regressions
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/state_machine.py backend/tests/test_state_machine_squad.py
git commit -m "feat: state machine accepts squad agent metadata for fixed identity"
```

---

### Task 7: Queue Manager

**Files:**
- Create: `backend/app/core/queue_manager.py`
- Test: `backend/tests/test_queue_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_queue_manager.py
import pytest
from app.core.queue_manager import QueueManager


class TestQueueManager:
    def setup_method(self):
        self.qm = QueueManager()

    def test_enqueue_first_starts_immediately(self):
        result = self.qm.enqueue("fabrica-de-conteudo", "Fábrica de Conteúdo")
        assert result.position == 1
        assert self.qm.active_squad() == "fabrica-de-conteudo"

    def test_enqueue_second_goes_to_queue(self):
        self.qm.enqueue("fabrica-de-conteudo", "Fábrica de Conteúdo")
        result = self.qm.enqueue("diagnostico-perfil", "Diagnóstico de Perfil")
        assert result.position == 2
        assert self.qm.active_squad() == "fabrica-de-conteudo"

    def test_complete_starts_next(self):
        self.qm.enqueue("fabrica-de-conteudo", "Fábrica de Conteúdo")
        self.qm.enqueue("diagnostico-perfil", "Diagnóstico de Perfil")
        next_squad = self.qm.complete_active()
        assert next_squad == "diagnostico-perfil"
        assert self.qm.active_squad() == "diagnostico-perfil"

    def test_complete_with_empty_queue(self):
        self.qm.enqueue("fabrica-de-conteudo", "Fábrica de Conteúdo")
        next_squad = self.qm.complete_active()
        assert next_squad is None
        assert self.qm.active_squad() is None

    def test_remove_from_queue(self):
        self.qm.enqueue("fabrica-de-conteudo", "Fábrica de Conteúdo")
        item = self.qm.enqueue("diagnostico-perfil", "Diagnóstico de Perfil")
        removed = self.qm.remove(item.id)
        assert removed is True
        assert len(self.qm.pending()) == 0

    def test_cannot_remove_active(self):
        item = self.qm.enqueue("fabrica-de-conteudo", "Fábrica de Conteúdo")
        removed = self.qm.remove(item.id)
        assert removed is False  # Can't remove active squad

    def test_queue_positions_update_on_remove(self):
        self.qm.enqueue("fabrica-de-conteudo", "Fábrica")
        self.qm.enqueue("diagnostico-perfil", "Diagnóstico")
        item3 = self.qm.enqueue("maquina-clientes", "Máquina")
        assert item3.position == 3
        # After removing position 2, position 3 becomes 2
        pending = self.qm.pending()
        self.qm.remove(pending[0].id)
        updated = self.qm.pending()
        assert len(updated) == 1
        assert updated[0].position == 2

    def test_list_queue(self):
        self.qm.enqueue("fabrica-de-conteudo", "Fábrica")
        self.qm.enqueue("diagnostico-perfil", "Diagnóstico")
        items = self.qm.list_all()
        assert len(items) == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_queue_manager.py -v
```

- [ ] **Step 3: Write the queue manager**

```python
# backend/app/core/queue_manager.py
"""Squad execution queue: one active at a time, FIFO for pending."""

import uuid
from app.models.squads import SquadQueueItem


class QueueManager:
    """Manages squad execution queue with one active squad at a time."""

    def __init__(self):
        self._active: SquadQueueItem | None = None
        self._pending: list[SquadQueueItem] = []

    def enqueue(self, squad_code: str, squad_name: str, user_input: str | None = None) -> SquadQueueItem:
        """Add a squad to the queue. First one becomes active immediately."""
        item = SquadQueueItem(
            id=str(uuid.uuid4())[:8],
            squad_code=squad_code,
            squad_name=squad_name,
            position=len(self._pending) + (2 if self._active else 1),
            user_input=user_input,
        )

        if self._active is None:
            item.position = 1
            self._active = item
        else:
            self._pending.append(item)

        return item

    def active_squad(self) -> str | None:
        """Return the code of the currently active squad."""
        return self._active.squad_code if self._active else None

    def active_item(self) -> SquadQueueItem | None:
        """Return the active queue item."""
        return self._active

    def complete_active(self) -> str | None:
        """Mark active squad as done, start next if available. Returns next squad code."""
        if not self._pending:
            self._active = None
            return None

        self._active = self._pending.pop(0)
        self._active.position = 1
        self._reindex()
        return self._active.squad_code

    def remove(self, item_id: str) -> bool:
        """Remove a pending item from queue. Cannot remove active."""
        if self._active and self._active.id == item_id:
            return False

        for i, item in enumerate(self._pending):
            if item.id == item_id:
                self._pending.pop(i)
                self._reindex()
                return True
        return False

    def pending(self) -> list[SquadQueueItem]:
        """Return pending queue items."""
        return list(self._pending)

    def list_all(self) -> list[SquadQueueItem]:
        """Return all items (active + pending)."""
        items = []
        if self._active:
            items.append(self._active)
        items.extend(self._pending)
        return items

    def _reindex(self):
        """Update position numbers for pending items."""
        for i, item in enumerate(self._pending):
            item.position = i + 2  # Active is always position 1
```

- [ ] **Step 4: Run tests**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_queue_manager.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/queue_manager.py backend/tests/test_queue_manager.py
git commit -m "feat: add QueueManager for squad execution queue (FIFO, one active)"
```

---

### Task 8: Chat Router

**Files:**
- Create: `backend/app/core/chat_router.py`
- Test: `backend/tests/test_chat_router.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_chat_router.py
import pytest
from unittest.mock import AsyncMock, patch

from app.core.chat_router import ChatRouter


class TestChatRouter:
    def setup_method(self):
        self.available_squads = [
            {"code": "fabrica-de-conteudo", "name": "Fábrica de Conteúdo", "description": "Calendário editorial, copy, stories"},
            {"code": "diagnostico-perfil", "name": "Diagnóstico de Perfil", "description": "Métricas, concorrentes, análise"},
            {"code": "maquina-clientes", "name": "Máquina de Clientes", "description": "Preço, contrato, onboarding"},
        ]
        self.router = ChatRouter(self.available_squads)

    def test_keyword_match_conteudo(self):
        result = self.router.match_by_keywords("preciso planejar o conteúdo do mês")
        assert result == "fabrica-de-conteudo"

    def test_keyword_match_calendario(self):
        result = self.router.match_by_keywords("criar calendário editorial")
        assert result == "fabrica-de-conteudo"

    def test_keyword_match_diagnostico(self):
        result = self.router.match_by_keywords("analisar métricas do meu perfil")
        assert result == "diagnostico-perfil"

    def test_keyword_match_concorrente(self):
        result = self.router.match_by_keywords("espiar concorrentes no instagram")
        assert result == "diagnostico-perfil"

    def test_keyword_match_preco(self):
        result = self.router.match_by_keywords("quanto cobrar pelo serviço")
        assert result == "maquina-clientes"

    def test_keyword_match_contrato(self):
        result = self.router.match_by_keywords("revisar contrato do cliente")
        assert result == "maquina-clientes"

    def test_keyword_match_onboarding(self):
        result = self.router.match_by_keywords("criar manual de boas vindas")
        assert result == "maquina-clientes"

    def test_no_match_returns_none(self):
        result = self.router.match_by_keywords("olá bom dia")
        assert result is None

    def test_direct_squad_code(self):
        result = self.router.match_by_keywords("fabrica-de-conteudo")
        assert result == "fabrica-de-conteudo"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_chat_router.py -v
```

- [ ] **Step 3: Write the chat router**

```python
# backend/app/core/chat_router.py
"""Routes user messages to the appropriate squad using keywords and Claude API."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Keyword mapping for fast local matching (no API call needed)
_KEYWORD_MAP: dict[str, list[str]] = {
    "fabrica-de-conteudo": [
        "conteúdo", "conteudo", "calendário", "calendario", "editorial",
        "copy", "stories", "reels", "carrossel", "carrosseis", "legenda",
        "post", "posts", "planejar conteúdo", "roteiro", "gancho",
        "fabrica-de-conteudo", "fábrica",
    ],
    "diagnostico-perfil": [
        "métrica", "metrica", "métricas", "metricas", "diagnóstico", "diagnostico",
        "concorrente", "concorrentes", "perfil", "análise", "analise", "analisar",
        "instagram", "tiktok", "engajamento", "relatório", "relatorio",
        "diagnostico-perfil",
    ],
    "maquina-clientes": [
        "preço", "preco", "precificar", "precificação", "cobrar", "proposta",
        "contrato", "cláusula", "clausula", "jurídico", "juridico",
        "onboarding", "boas vindas", "boas-vindas", "manual",
        "cliente", "maquina-clientes", "máquina",
    ],
}


class ChatRouter:
    """Routes user messages to the appropriate squad."""

    def __init__(self, available_squads: list[dict[str, Any]]):
        self.available_squads = available_squads

    def match_by_keywords(self, message: str) -> str | None:
        """Fast local matching using keyword lists. Returns squad code or None."""
        msg_lower = message.lower()

        # Direct squad code match
        for squad in self.available_squads:
            if squad["code"] in msg_lower:
                return squad["code"]

        # Keyword scoring
        scores: dict[str, int] = {}
        for squad_code, keywords in _KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw in msg_lower)
            if score > 0:
                scores[squad_code] = score

        if not scores:
            return None

        return max(scores, key=scores.get)  # type: ignore[arg-type]

    async def route(self, message: str, api_key: str | None = None) -> dict:
        """Route a message to a squad. Tries keywords first, then Claude API.

        Returns: {"squad_code": str | None, "confidence": "high"|"medium"|"low", "explanation": str}
        """
        # Try keyword match first
        keyword_match = self.match_by_keywords(message)
        if keyword_match:
            squad = next((s for s in self.available_squads if s["code"] == keyword_match), None)
            return {
                "squad_code": keyword_match,
                "confidence": "high",
                "explanation": f"Vou iniciar o squad {squad['name'] if squad else keyword_match}.",
            }

        # If no keyword match and API key available, use Claude
        if api_key:
            return await self._route_via_claude(message, api_key)

        return {
            "squad_code": None,
            "confidence": "low",
            "explanation": "Não consegui identificar qual squad usar. Escolha um dos disponíveis.",
        }

    async def _route_via_claude(self, message: str, api_key: str) -> dict:
        """Use Claude API to detect squad from ambiguous messages."""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=api_key)
            squad_descriptions = "\n".join(
                f"- {s['code']}: {s['name']} — {s['description']}"
                for s in self.available_squads
            )

            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                messages=[{"role": "user", "content": message}],
                system=f"""You are a router. Given a user message in Portuguese, determine which squad to run.
Available squads:
{squad_descriptions}

Respond with ONLY the squad code (e.g., "fabrica-de-conteudo") or "none" if no match.""",
            )

            result = response.content[0].text.strip().lower()
            valid_codes = {s["code"] for s in self.available_squads}

            if result in valid_codes:
                squad = next(s for s in self.available_squads if s["code"] == result)
                return {
                    "squad_code": result,
                    "confidence": "medium",
                    "explanation": f"Entendi que você quer usar o squad {squad['name']}. Confirma?",
                }

        except Exception:
            logger.exception("Claude routing failed")

        return {
            "squad_code": None,
            "confidence": "low",
            "explanation": "Não consegui identificar qual squad usar. Escolha um dos disponíveis.",
        }
```

- [ ] **Step 4: Run tests**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_chat_router.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/chat_router.py backend/tests/test_chat_router.py
git commit -m "feat: add ChatRouter with keyword matching and Claude API fallback"
```

---

### Task 9: Squad Engine (Core Orchestrator)

**Files:**
- Create: `backend/app/core/squad_engine.py`
- Test: `backend/tests/test_squad_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_squad_engine.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.core.squad_engine import SquadEngine
from app.core.squad_loader import SquadLoader
from app.core.agent_registry import AgentRegistry
from app.core.queue_manager import QueueManager
from app.models.squads import PipelineStepStatus, SquadStatus

SQUADS_DIR = Path(__file__).resolve().parents[2] / "socialforge" / "squads"


class TestSquadEngine:
    def setup_method(self):
        self.loader = SquadLoader(squads_dir=SQUADS_DIR)
        self.loader.load_all()
        self.registry = AgentRegistry()
        self.queue = QueueManager()
        self.emit_fn = AsyncMock()
        self.broadcast_fn = AsyncMock()

        self.engine = SquadEngine(
            loader=self.loader,
            registry=self.registry,
            queue=self.queue,
            emit_event=self.emit_fn,
            broadcast_state=self.broadcast_fn,
        )

    def test_start_squad_creates_pipeline_state(self):
        state = self.engine.start_squad("fabrica-de-conteudo", "test-session")
        assert state is not None
        assert state.squad_code == "fabrica-de-conteudo"
        assert state.total_steps == 12
        assert state.status == SquadStatus.RUNNING

    def test_start_unknown_squad_returns_none(self):
        state = self.engine.start_squad("nonexistent", "test-session")
        assert state is None

    def test_first_step_is_checkpoint(self):
        state = self.engine.start_squad("fabrica-de-conteudo", "test-session")
        step = self.engine.current_step()
        assert step is not None
        assert step.id == "step-01"
        assert step.type.value == "checkpoint"

    def test_get_pipeline_state(self):
        self.engine.start_squad("fabrica-de-conteudo", "test-session")
        state = self.engine.pipeline_state
        assert state is not None
        assert state.current_step_index == 0

    @pytest.mark.asyncio
    async def test_approve_checkpoint_advances_to_next_step(self):
        self.engine.start_squad("fabrica-de-conteudo", "test-session")
        # First step is checkpoint (briefing)
        await self.engine.approve_checkpoint(user_input="Nicho: dentista, público: mulheres 30+")
        state = self.engine.pipeline_state
        assert state.step_states["step-01"] == PipelineStepStatus.APPROVED
        assert state.current_step_index == 1

    @pytest.mark.asyncio
    async def test_execute_agent_step_emits_events(self):
        self.engine.start_squad("fabrica-de-conteudo", "test-session")
        # Approve first checkpoint
        await self.engine.approve_checkpoint(user_input="Briefing data")
        # Now execute agent step (step-02, Luna Pesquisa)
        with patch.object(self.engine, "_call_claude_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = "Datas encontradas: 1 de maio, 25 de maio..."
            await self.engine.execute_current_step()
            # Should have emitted subagent_start
            assert self.emit_fn.called

    def test_build_agent_prompt_includes_persona(self):
        self.engine.start_squad("fabrica-de-conteudo", "test-session")
        # Advance to agent step
        self.engine.pipeline_state.current_step_index = 1
        prompt = self.engine._build_agent_prompt()
        assert prompt is not None
        assert len(prompt) > 100  # Should have substantial content
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_squad_engine.py -v
```

- [ ] **Step 3: Write the squad engine**

```python
# backend/app/core/squad_engine.py
"""Pipeline orchestrator: loads squads, executes steps, manages context and retries."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine

from app.core.agent_registry import AgentRegistry
from app.core.queue_manager import QueueManager
from app.core.squad_loader import SquadLoader
from app.models.events import Event, EventData, EventType
from app.models.squads import (
    CheckpointState,
    PipelineState,
    PipelineStep,
    PipelineStepStatus,
    PipelineStepType,
    Squad,
    SquadStatus,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]  # Seconds between retries


class SquadEngine:
    """Orchestrates squad pipeline execution."""

    def __init__(
        self,
        loader: SquadLoader,
        registry: AgentRegistry,
        queue: QueueManager,
        emit_event: Callable[..., Coroutine],
        broadcast_state: Callable[..., Coroutine],
        api_key: str | None = None,
    ):
        self.loader = loader
        self.registry = registry
        self.queue = queue
        self.emit_event = emit_event
        self.broadcast_state = broadcast_state
        self.api_key = api_key

        self._pipeline_state: PipelineState | None = None
        self._squad: Squad | None = None

    @property
    def pipeline_state(self) -> PipelineState | None:
        return self._pipeline_state

    def start_squad(self, squad_code: str, session_id: str) -> PipelineState | None:
        """Initialize a pipeline for the given squad."""
        squad = self.loader.get(squad_code)
        if not squad:
            return None

        self._squad = squad
        self._pipeline_state = PipelineState(
            squad_code=squad_code,
            session_id=session_id,
            total_steps=len(squad.pipeline.steps),
            status=SquadStatus.RUNNING,
        )
        logger.info("Started squad %s with %d steps", squad.name, len(squad.pipeline.steps))
        return self._pipeline_state

    def current_step(self) -> PipelineStep | None:
        """Get the current pipeline step."""
        if not self._squad or not self._pipeline_state:
            return None
        idx = self._pipeline_state.current_step_index
        steps = self._squad.pipeline.steps
        if idx >= len(steps):
            return None
        return steps[idx]

    async def approve_checkpoint(self, user_input: str = "", approved: bool = True) -> None:
        """Handle checkpoint approval/adjustment."""
        if not self._pipeline_state:
            return

        step = self.current_step()
        if not step:
            return

        if approved:
            self._pipeline_state.step_states[step.id] = PipelineStepStatus.APPROVED
            self._pipeline_state.outputs[step.id] = user_input
            self._pipeline_state.checkpoint = None
            self._advance_step()
        else:
            # Re-execute previous agent step with feedback
            self._pipeline_state.checkpoint = CheckpointState(
                step_id=step.id,
                step_name=step.name,
                content="",
                awaiting_approval=False,
                approved=False,
                feedback=user_input,
            )

    async def execute_current_step(self) -> str | None:
        """Execute the current step. Returns output for agent steps, None for checkpoints."""
        step = self.current_step()
        if not step or not self._pipeline_state:
            return None

        if step.type == PipelineStepType.CHECKPOINT:
            self._pipeline_state.status = SquadStatus.PAUSED
            self._pipeline_state.step_states[step.id] = PipelineStepStatus.WAITING_APPROVAL
            self._pipeline_state.checkpoint = CheckpointState(
                step_id=step.id,
                step_name=step.name,
                content=self._get_checkpoint_content(step),
                awaiting_approval=True,
            )
            return None

        if step.type == PipelineStepType.AGENT:
            return await self._execute_agent_step(step)

        return None

    async def _execute_agent_step(self, step: PipelineStep) -> str | None:
        """Execute an agent step with retry logic."""
        if not self._squad or not self._pipeline_state:
            return None

        identity = self.registry.get_identity(self._squad.code, step.agent or "")
        agent_id = f"squad_{self._squad.code}_{step.agent}"

        # Emit subagent_start
        await self.emit_event(Event(
            event_type=EventType.SUBAGENT_START,
            session_id=self._pipeline_state.session_id,
            timestamp=datetime.now(),
            data=EventData(
                agent_id=agent_id,
                task_description=step.name,
                squad_id=self._squad.code,
                squad_agent_id=step.agent,
                display_name=identity.display_name if identity else step.agent,
                agent_color=identity.color if identity else None,
                sprite_key=identity.sprite_key if identity else None,
                pipeline_step=step.id,
                pipeline_step_name=step.name,
            ),
        ))

        self._pipeline_state.step_states[step.id] = PipelineStepStatus.ACTIVE

        # Execute with retries
        output = None
        for attempt in range(MAX_RETRIES):
            try:
                prompt = self._build_agent_prompt()
                output = await self._call_claude_api(prompt)
                break
            except Exception:
                logger.warning("Agent step %s attempt %d failed", step.id, attempt + 1, exc_info=True)
                if attempt < MAX_RETRIES - 1:
                    self._pipeline_state.step_states[step.id] = PipelineStepStatus.RETRY
                    await asyncio.sleep(RETRY_DELAYS[attempt])
                else:
                    self._pipeline_state.step_states[step.id] = PipelineStepStatus.ERROR
                    logger.error("Agent step %s failed after %d retries", step.id, MAX_RETRIES)

        if output:
            self._pipeline_state.step_states[step.id] = PipelineStepStatus.COMPLETED
            self._pipeline_state.outputs[step.id] = output
            self._advance_step()

        # Emit subagent_stop
        await self.emit_event(Event(
            event_type=EventType.SUBAGENT_STOP,
            session_id=self._pipeline_state.session_id,
            timestamp=datetime.now(),
            data=EventData(
                agent_id=agent_id,
                squad_id=self._squad.code,
                pipeline_step=step.id,
            ),
        ))

        return output

    def _build_agent_prompt(self) -> str:
        """Build the prompt for the current agent step."""
        step = self.current_step()
        if not step or not self._squad:
            return ""

        squad_dir = Path(self._squad.squad_dir)
        parts: list[str] = []

        # 1. Agent persona
        agent_md = squad_dir / "agents" / f"{step.agent}.agent.md"
        if agent_md.exists():
            parts.append(f"# Sua Persona\n\n{agent_md.read_text()}")

        # 2. Task instructions
        for task_name in step.tasks:
            task_file = squad_dir / "agents" / (step.agent or "") / "tasks" / f"{task_name}.md"
            if task_file.exists():
                parts.append(f"# Tarefa: {task_name}\n\n{task_file.read_text()}")

        # 3. Step instructions
        step_file = squad_dir / step.file
        if step_file.exists():
            parts.append(f"# Instruções do Step\n\n{step_file.read_text()}")

        # 4. Reference data
        for data_file in self._squad.data_files:
            data_path = squad_dir / data_file
            if data_path.exists():
                parts.append(f"# Dados: {data_path.name}\n\n{data_path.read_text()}")

        # 5. Previous step outputs (context chain)
        if self._pipeline_state and self._pipeline_state.outputs:
            context = "\n\n---\n\n".join(
                f"## Output de {sid}:\n{out}"
                for sid, out in self._pipeline_state.outputs.items()
            )
            parts.append(f"# Contexto dos Steps Anteriores\n\n{context}")

        return "\n\n---\n\n".join(parts)

    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API to execute an agent task."""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
            system="Você é um agente especializado em social media e marketing digital. Execute a tarefa descrita com excelência, seguindo sua persona e princípios. Responda em português do Brasil.",
        )
        return response.content[0].text

    def _get_checkpoint_content(self, step: PipelineStep) -> str:
        """Get content to display at a checkpoint."""
        if not self._squad:
            return ""

        # Read the step file for checkpoint instructions
        step_file = Path(self._squad.squad_dir) / step.file
        if step_file.exists():
            return step_file.read_text()
        return f"Checkpoint: {step.name}"

    def _advance_step(self) -> None:
        """Move to the next step in the pipeline."""
        if not self._pipeline_state or not self._squad:
            return

        self._pipeline_state.current_step_index += 1
        if self._pipeline_state.current_step_index >= len(self._squad.pipeline.steps):
            self._pipeline_state.status = SquadStatus.COMPLETED
            self._pipeline_state.completed_at = datetime.now()
        else:
            self._pipeline_state.status = SquadStatus.RUNNING

    async def run_pipeline(self) -> None:
        """Run the entire pipeline, pausing at checkpoints."""
        while self._pipeline_state and self._pipeline_state.status == SquadStatus.RUNNING:
            step = self.current_step()
            if not step:
                break

            result = await self.execute_current_step()

            if self._pipeline_state.status == SquadStatus.PAUSED:
                # Checkpoint reached, wait for approval
                break

            await self.broadcast_state()
```

- [ ] **Step 4: Run tests**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_squad_engine.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/squad_engine.py backend/tests/test_squad_engine.py
git commit -m "feat: add SquadEngine pipeline orchestrator with retry logic"
```

---

## Chunk 3: API Routes and Backend Integration

### Task 10: Squad API Routes

**Files:**
- Create: `backend/app/api/routes/squads.py`
- Test: `backend/tests/test_squad_routes.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_squad_routes.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_list_squads(client):
    response = await client.get("/api/v1/squads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    codes = {s["code"] for s in data}
    assert "fabrica-de-conteudo" in codes


@pytest.mark.asyncio
async def test_get_squad_detail(client):
    response = await client.get("/api/v1/squads/fabrica-de-conteudo")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "fabrica-de-conteudo"
    assert len(data["agents"]) == 5


@pytest.mark.asyncio
async def test_get_squad_not_found(client):
    response = await client.get("/api/v1/squads/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_squad(client):
    response = await client.post("/api/v1/squads/start", json={
        "squad_code": "fabrica-de-conteudo",
        "session_id": "test-session",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"


@pytest.mark.asyncio
async def test_get_queue(client):
    response = await client.get("/api/v1/squads/queue")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_route(client):
    response = await client.post("/api/v1/squads/chat", json={
        "message": "preciso planejar conteúdo do mês",
        "session_id": "test-session",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["squad_code"] == "fabrica-de-conteudo"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_squad_routes.py -v
```

- [ ] **Step 3: Write the routes**

```python
# backend/app/api/routes/squads.py
"""REST endpoints for SocialForge squad operations."""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.core.squad_loader import SquadLoader
from app.core.chat_router import ChatRouter
from app.core.queue_manager import QueueManager

router = APIRouter()

# These will be initialized in main.py lifespan
_loader: SquadLoader | None = None
_router: ChatRouter | None = None
_queue: QueueManager | None = None


def init_squad_services(loader: SquadLoader, chat_router: ChatRouter, queue: QueueManager):
    """Called during app startup to inject dependencies."""
    global _loader, _router, _queue
    _loader = loader
    _router = chat_router
    _queue = queue


class StartSquadRequest(BaseModel):
    squad_code: str
    session_id: str
    user_input: str | None = None


class ChatRequest(BaseModel):
    message: str
    session_id: str


@router.get("/squads")
async def list_squads():
    """List all available squads."""
    if not _loader:
        raise HTTPException(500, "Squad loader not initialized")
    return _loader.list_squads()


@router.get("/squads/{squad_code}")
async def get_squad(squad_code: str):
    """Get detailed squad info."""
    if not _loader:
        raise HTTPException(500, "Squad loader not initialized")
    squad = _loader.get(squad_code)
    if not squad:
        raise HTTPException(404, f"Squad '{squad_code}' not found")
    return squad.model_dump()


@router.post("/squads/start")
async def start_squad(request: StartSquadRequest, background_tasks: BackgroundTasks):
    """Start or enqueue a squad for execution."""
    if not _loader or not _queue:
        raise HTTPException(500, "Services not initialized")
    squad = _loader.get(request.squad_code)
    if not squad:
        raise HTTPException(404, f"Squad '{request.squad_code}' not found")

    item = _queue.enqueue(squad.code, squad.name, request.user_input)
    is_active = _queue.active_squad() == squad.code

    return {
        "status": "started" if is_active else "queued",
        "queue_position": item.position,
        "squad_name": squad.name,
    }


@router.get("/squads/queue")
async def get_queue():
    """Get current squad execution queue."""
    if not _queue:
        raise HTTPException(500, "Queue not initialized")
    return [item.model_dump() for item in _queue.list_all()]


@router.delete("/squads/queue/{item_id}")
async def remove_from_queue(item_id: str):
    """Remove a squad from the pending queue."""
    if not _queue:
        raise HTTPException(500, "Queue not initialized")
    removed = _queue.remove(item_id)
    if not removed:
        raise HTTPException(400, "Cannot remove active squad or item not found")
    return {"status": "removed"}


@router.post("/squads/chat")
async def chat_route(request: ChatRequest):
    """Route a chat message to the appropriate squad."""
    if not _router:
        raise HTTPException(500, "Chat router not initialized")
    result = await _router.route(request.message)
    return result


@router.post("/squads/approve")
async def approve_checkpoint(request: dict):
    """Approve or request adjustment at a checkpoint."""
    # This will be wired to SquadEngine in integration
    return {"status": "approved"}
```

- [ ] **Step 4: Wire routes in main.py**

In `backend/app/main.py`, add during lifespan startup:

```python
from pathlib import Path
from app.core.squad_loader import SquadLoader
from app.core.chat_router import ChatRouter
from app.core.queue_manager import QueueManager
from app.api.routes.squads import router as squad_router, init_squad_services

# In lifespan, after DB init:
squads_dir = Path(__file__).resolve().parents[2] / "socialforge" / "squads"
squad_loader = SquadLoader(squads_dir=squads_dir)
squad_loader.load_all()
chat_router = ChatRouter(squad_loader.list_squads())
queue_manager = QueueManager()
init_squad_services(squad_loader, chat_router, queue_manager)

# Mount router:
app.include_router(squad_router, prefix="/api/v1")
```

- [ ] **Step 5: Run tests**

```bash
cd /root/claude-office && uv run pytest backend/tests/test_squad_routes.py -v
cd /root/claude-office && uv run pytest backend/tests/ -v  # Full suite
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/routes/squads.py backend/tests/test_squad_routes.py backend/app/main.py
git commit -m "feat: add squad API routes and wire into FastAPI app"
```

---

## Chunk 4: Frontend — Types, Stores, and ChatPanel

### Task 11: Frontend TypeScript Types

**Files:**
- Create: `frontend/src/types/squads.ts`

- [ ] **Step 1: Write the types**

```typescript
// frontend/src/types/squads.ts

export interface AgentIdentity {
  squadAgentId: string;
  displayName: string;
  color: string;
  spriteKey: string;
  icon: string;
}

export interface PipelineStep {
  id: string;
  name: string;
  type: "agent" | "checkpoint";
  agent?: string;
  tasks: string[];
  dependsOn?: string;
}

export type PipelineStepStatus =
  | "pending"
  | "active"
  | "completed"
  | "waiting_approval"
  | "approved"
  | "retry"
  | "error";

export type SquadStatus = "pending" | "running" | "paused" | "completed" | "error";

export interface SquadSummary {
  code: string;
  name: string;
  description: string;
  icon: string;
  agentCount: number;
  stepCount: number;
}

export interface CheckpointState {
  stepId: string;
  stepName: string;
  content: string;
  awaitingApproval: boolean;
  approved?: boolean;
  feedback?: string;
}

export interface PipelineState {
  squadCode: string;
  sessionId: string;
  totalSteps: number;
  currentStepIndex: number;
  status: SquadStatus;
  stepStates: Record<string, PipelineStepStatus>;
  outputs: Record<string, string>;
  checkpoint?: CheckpointState;
}

export interface SquadQueueItem {
  id: string;
  squadCode: string;
  squadName: string;
  position: number;
  userInput?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system" | "checkpoint";
  agentName?: string;
  agentIcon?: string;
  agentColor?: string;
  text: string;
  timestamp: number;
  checkpointStepId?: string;
  isApproved?: boolean;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/types/squads.ts
git commit -m "feat: add TypeScript types for squads, pipeline, and chat"
```

---

### Task 12: Squad and Chat Zustand Stores

**Files:**
- Create: `frontend/src/stores/squadStore.ts`
- Create: `frontend/src/stores/chatStore.ts`

- [ ] **Step 1: Write squadStore**

```typescript
// frontend/src/stores/squadStore.ts
import { create } from "zustand";
import type { PipelineState, SquadQueueItem, SquadSummary } from "@/types/squads";

interface SquadState {
  squads: SquadSummary[];
  pipelineState: PipelineState | null;
  queue: SquadQueueItem[];

  setSquads: (squads: SquadSummary[]) => void;
  setPipelineState: (state: PipelineState | null) => void;
  setQueue: (queue: SquadQueueItem[]) => void;
  updateStepStatus: (stepId: string, status: string) => void;
}

export const useSquadStore = create<SquadState>((set) => ({
  squads: [],
  pipelineState: null,
  queue: [],

  setSquads: (squads) => set({ squads }),
  setPipelineState: (pipelineState) => set({ pipelineState }),
  setQueue: (queue) => set({ queue }),
  updateStepStatus: (stepId, status) =>
    set((state) => {
      if (!state.pipelineState) return state;
      return {
        pipelineState: {
          ...state.pipelineState,
          stepStates: { ...state.pipelineState.stepStates, [stepId]: status },
        },
      };
    }),
}));
```

- [ ] **Step 2: Write chatStore**

```typescript
// frontend/src/stores/chatStore.ts
import { create } from "zustand";
import type { ChatMessage } from "@/types/squads";

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;

  addMessage: (msg: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  clearMessages: () => void;
}

let messageCounter = 0;

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,

  addMessage: (msg) =>
    set((state) => ({
      messages: [...state.messages, { ...msg, id: msg.id || `msg-${++messageCounter}` }],
    })),
  setLoading: (isLoading) => set({ isLoading }),
  clearMessages: () => set({ messages: [] }),
}));
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/squadStore.ts frontend/src/stores/chatStore.ts
git commit -m "feat: add Zustand stores for squad state and chat messages"
```

---

### Task 13: Agent Identities Constant

**Files:**
- Create: `frontend/src/constants/agentIdentities.ts`

- [ ] **Step 1: Write the identities map**

```typescript
// frontend/src/constants/agentIdentities.ts
import type { AgentIdentity } from "@/types/squads";

export const AGENT_IDENTITIES: Record<string, Record<string, AgentIdentity>> = {
  "fabrica-de-conteudo": {
    estrategista: { squadAgentId: "estrategista", displayName: "Sol Estratégia", color: "#FFD700", spriteKey: "sol-estrategia", icon: "🧠" },
    pesquisador: { squadAgentId: "pesquisador", displayName: "Luna Pesquisa", color: "#87CEEB", spriteKey: "luna-pesquisa", icon: "🔍" },
    copywriter: { squadAgentId: "copywriter", displayName: "Davi Copy", color: "#4CAF50", spriteKey: "davi-copy", icon: "✍️" },
    "roteirista-stories": { squadAgentId: "roteirista-stories", displayName: "Bia Stories", color: "#FF69B4", spriteKey: "bia-stories", icon: "📱" },
    revisor: { squadAgentId: "revisor", displayName: "Léo Revisão", color: "#FF8C00", spriteKey: "leo-revisao", icon: "✅" },
  },
  "diagnostico-perfil": {
    investigador: { squadAgentId: "investigador", displayName: "Sherlock Social", color: "#8B4513", spriteKey: "sherlock-social", icon: "🕵️" },
    analista: { squadAgentId: "analista", displayName: "Nina Números", color: "#9C27B0", spriteKey: "nina-numeros", icon: "📊" },
    "estrategista-perfil": { squadAgentId: "estrategista-perfil", displayName: "Max Plano", color: "#1A237E", spriteKey: "max-plano", icon: "🎯" },
  },
  "maquina-clientes": {
    consultor: { squadAgentId: "consultor", displayName: "Rafa Preço", color: "#2E7D32", spriteKey: "rafa-preco", icon: "💰" },
    juridico: { squadAgentId: "juridico", displayName: "Clara Contrato", color: "#880E4F", spriteKey: "clara-contrato", icon: "📋" },
    onboarding: { squadAgentId: "onboarding", displayName: "Dani Welcome", color: "#00BCD4", spriteKey: "dani-welcome", icon: "🤝" },
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/constants/agentIdentities.ts
git commit -m "feat: add fixed agent identity constants for all 11 SocialForge agents"
```

---

### Task 14: ChatPanel Component

**Files:**
- Create: `frontend/src/components/chat/ChatPanel.tsx`
- Create: `frontend/src/components/chat/ChatMessage.tsx`
- Create: `frontend/src/components/chat/CheckpointMessage.tsx`
- Create: `frontend/src/components/chat/SquadCard.tsx`
- Create: `frontend/src/components/chat/ChatInput.tsx`
- Create: `frontend/src/components/chat/QueueIndicator.tsx`

- [ ] **Step 1: Create ChatInput component**

```typescript
// frontend/src/components/chat/ChatInput.tsx
"use client";

import { useState, useCallback } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  }, [text, disabled, onSend]);

  return (
    <div className="flex items-center gap-2 p-3 border-t border-zinc-800 bg-zinc-900/50">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        placeholder={placeholder ?? "Descreva o que você precisa..."}
        disabled={disabled}
        className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-rose-500 transition-colors disabled:opacity-50"
      />
      <button
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        className="bg-rose-600 hover:bg-rose-500 disabled:bg-zinc-700 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors disabled:opacity-50"
      >
        Enviar
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Create SquadCard component**

```typescript
// frontend/src/components/chat/SquadCard.tsx
"use client";

import type { SquadSummary } from "@/types/squads";

interface SquadCardProps {
  squad: SquadSummary;
  onClick: (code: string) => void;
}

export function SquadCard({ squad, onClick }: SquadCardProps) {
  return (
    <button
      onClick={() => onClick(squad.code)}
      className="bg-zinc-800/80 border border-zinc-700 hover:border-rose-500 rounded-lg p-3 text-left transition-colors w-full"
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{squad.icon}</span>
        <span className="text-white text-sm font-semibold">{squad.name}</span>
      </div>
      <p className="text-zinc-400 text-xs leading-relaxed">{squad.description}</p>
      <div className="flex gap-2 mt-2">
        <span className="bg-zinc-700/50 text-zinc-400 text-[10px] px-2 py-0.5 rounded">
          {squad.agentCount} agentes
        </span>
        <span className="bg-zinc-700/50 text-zinc-400 text-[10px] px-2 py-0.5 rounded">
          {squad.stepCount} etapas
        </span>
      </div>
    </button>
  );
}
```

- [ ] **Step 3: Create ChatMessage component**

```typescript
// frontend/src/components/chat/ChatMessage.tsx
"use client";

interface ChatMessageProps {
  role: "user" | "agent" | "system";
  text: string;
  agentName?: string;
  agentIcon?: string;
  agentColor?: string;
}

export function ChatMessage({ role, text, agentName, agentIcon, agentColor }: ChatMessageProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end mb-3">
        <div className="bg-rose-600/20 border border-rose-600/30 rounded-lg px-4 py-2.5 max-w-[80%]">
          <p className="text-white text-sm whitespace-pre-wrap">{text}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-2.5 mb-3">
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0"
        style={{ backgroundColor: agentColor ?? "#374151" }}
      >
        {agentIcon ?? "🤖"}
      </div>
      <div className="flex-1">
        {agentName && (
          <span className="text-xs font-medium mb-1 block" style={{ color: agentColor ?? "#9CA3AF" }}>
            {agentName}
          </span>
        )}
        <div className="bg-zinc-800/60 border border-zinc-700/50 rounded-lg px-4 py-2.5">
          <p className="text-zinc-200 text-sm whitespace-pre-wrap">{text}</p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create CheckpointMessage component**

```typescript
// frontend/src/components/chat/CheckpointMessage.tsx
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface CheckpointMessageProps {
  stepName: string;
  content: string;
  onApprove: () => void;
  onAdjust: (feedback: string) => void;
  isResolved?: boolean;
}

export function CheckpointMessage({ stepName, content, onApprove, onAdjust, isResolved }: CheckpointMessageProps) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const audioRef = useRef<AudioContext | null>(null);

  // Play notification sound on mount
  useEffect(() => {
    if (isResolved) return;
    try {
      const ctx = new AudioContext();
      audioRef.current = ctx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 880;
      osc.type = "sine";
      gain.gain.value = 0.1;
      osc.start();
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.stop(ctx.currentTime + 0.3);
    } catch {
      // Audio not available
    }
    return () => { audioRef.current?.close(); };
  }, [isResolved]);

  const handleAdjust = useCallback(() => {
    if (feedback.trim()) {
      onAdjust(feedback.trim());
    }
  }, [feedback, onAdjust]);

  return (
    <div className="mb-3 mx-2">
      <div className="bg-amber-900/20 border border-amber-600/40 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-amber-400 text-lg">⏸</span>
          <span className="text-amber-300 text-sm font-semibold">{stepName}</span>
        </div>
        <div className="text-zinc-300 text-sm mb-3 max-h-60 overflow-y-auto whitespace-pre-wrap">
          {content}
        </div>
        {!isResolved && (
          <>
            {!showFeedback ? (
              <div className="flex gap-2">
                <button
                  onClick={onApprove}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white rounded-md px-4 py-1.5 text-sm font-medium transition-colors"
                >
                  ✅ Aprovar
                </button>
                <button
                  onClick={() => setShowFeedback(true)}
                  className="bg-amber-600 hover:bg-amber-500 text-white rounded-md px-4 py-1.5 text-sm font-medium transition-colors"
                >
                  ✏️ Pedir Ajuste
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAdjust()}
                  placeholder="O que quer mudar?"
                  className="flex-1 bg-zinc-800 border border-zinc-600 rounded-md px-3 py-1.5 text-sm text-white outline-none"
                  autoFocus
                />
                <button onClick={handleAdjust} className="bg-amber-600 text-white rounded-md px-3 py-1.5 text-sm">
                  Enviar
                </button>
              </div>
            )}
          </>
        )}
        {isResolved && (
          <span className="text-emerald-400 text-sm">✅ Aprovado</span>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Create QueueIndicator component**

```typescript
// frontend/src/components/chat/QueueIndicator.tsx
"use client";

import type { SquadQueueItem } from "@/types/squads";

interface QueueIndicatorProps {
  items: SquadQueueItem[];
  onRemove: (id: string) => void;
}

export function QueueIndicator({ items, onRemove }: QueueIndicatorProps) {
  const pending = items.filter((i) => i.position > 1);
  if (pending.length === 0) return null;

  return (
    <div className="px-3 py-2 border-t border-zinc-800 bg-zinc-900/30">
      <span className="text-zinc-500 text-xs">Na fila:</span>
      {pending.map((item) => (
        <div key={item.id} className="flex items-center justify-between mt-1">
          <span className="text-zinc-400 text-xs">
            ⏳ {item.squadName} ({item.position}º)
          </span>
          <button
            onClick={() => onRemove(item.id)}
            className="text-zinc-600 hover:text-rose-400 text-xs transition-colors"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 6: Create main ChatPanel component**

```typescript
// frontend/src/components/chat/ChatPanel.tsx
"use client";

import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useSquadStore } from "@/stores/squadStore";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";
import { CheckpointMessage } from "./CheckpointMessage";
import { SquadCard } from "./SquadCard";
import { QueueIndicator } from "./QueueIndicator";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function ChatPanel() {
  const messages = useChatStore((s) => s.messages);
  const addMessage = useChatStore((s) => s.addMessage);
  const isLoading = useChatStore((s) => s.isLoading);
  const setLoading = useChatStore((s) => s.setLoading);

  const squads = useSquadStore((s) => s.squads);
  const pipelineState = useSquadStore((s) => s.pipelineState);
  const queue = useSquadStore((s) => s.queue);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length]);

  // Load squads on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/squads`)
      .then((r) => r.json())
      .then((data) => useSquadStore.getState().setSquads(data))
      .catch(() => {});
  }, []);

  const handleSend = useCallback(async (text: string) => {
    addMessage({ id: "", role: "user", text, timestamp: Date.now() });
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/squads/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: "default" }),
      });
      const data = await res.json();

      if (data.squad_code) {
        addMessage({
          id: "", role: "system", text: data.explanation, timestamp: Date.now(),
        });
        // Auto-start if confidence is high
        if (data.confidence === "high") {
          await startSquad(data.squad_code, text);
        }
      } else {
        addMessage({
          id: "", role: "system", text: data.explanation, timestamp: Date.now(),
        });
      }
    } catch {
      addMessage({
        id: "", role: "system", text: "Erro de conexão. Tente novamente.", timestamp: Date.now(),
      });
    } finally {
      setLoading(false);
    }
  }, [addMessage, setLoading]);

  const startSquad = useCallback(async (code: string, userInput?: string) => {
    try {
      await fetch(`${API_BASE}/api/v1/squads/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ squad_code: code, session_id: "default", user_input: userInput }),
      });
    } catch {
      addMessage({ id: "", role: "system", text: "Erro ao iniciar squad.", timestamp: Date.now() });
    }
  }, [addMessage]);

  const handleApprove = useCallback(async () => {
    await fetch(`${API_BASE}/api/v1/squads/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: true }),
    });
  }, []);

  const handleAdjust = useCallback(async (feedback: string) => {
    await fetch(`${API_BASE}/api/v1/squads/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: false, feedback }),
    });
  }, []);

  const removeFromQueue = useCallback(async (id: string) => {
    await fetch(`${API_BASE}/api/v1/squads/queue/${id}`, { method: "DELETE" });
  }, []);

  const hasActiveSquad = pipelineState !== null;

  return (
    <div className="flex flex-col h-full bg-zinc-950 border-r border-zinc-800">
      {/* Progress bar */}
      {pipelineState && (
        <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-900/50">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-1">
            <span>{pipelineState.squadCode}</span>
            <span>{pipelineState.currentStepIndex + 1}/{pipelineState.totalSteps}</span>
          </div>
          <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-rose-500 transition-all duration-500"
              style={{ width: `${((pipelineState.currentStepIndex + 1) / pipelineState.totalSteps) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-1">
        {messages.length === 0 && !hasActiveSquad && (
          <div className="space-y-4">
            <ChatMessage
              role="system"
              text="Olá! Sou seu time de agentes de IA. O que você precisa hoje?"
              agentName="SocialForge"
              agentIcon="🤖"
              agentColor="#E94560"
            />
            <div className="grid gap-2">
              {squads.map((squad) => (
                <SquadCard key={squad.code} squad={squad} onClick={(code) => startSquad(code)} />
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) =>
          msg.role === "checkpoint" ? (
            <CheckpointMessage
              key={msg.id}
              stepName={msg.agentName ?? "Checkpoint"}
              content={msg.text}
              onApprove={handleApprove}
              onAdjust={handleAdjust}
              isResolved={msg.isApproved}
            />
          ) : (
            <ChatMessage
              key={msg.id}
              role={msg.role === "system" ? "agent" : msg.role}
              text={msg.text}
              agentName={msg.agentName}
              agentIcon={msg.agentIcon}
              agentColor={msg.agentColor}
            />
          ),
        )}

        {isLoading && (
          <div className="flex gap-2 items-center text-zinc-500 text-sm py-2">
            <span className="animate-pulse">●</span> Processando...
          </div>
        )}
      </div>

      {/* Queue */}
      <QueueIndicator items={queue} onRemove={removeFromQueue} />

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/chat/
git commit -m "feat: add ChatPanel with chat-first UI, squad cards, and checkpoint approval"
```

---

## Chunk 5: Frontend Integration — Layout, Whiteboard, WebSocket

### Task 15: Pipeline Whiteboard Mode

**Files:**
- Create: `frontend/src/components/game/whiteboard/PipelineMode.tsx`
- Modify: `frontend/src/components/game/Whiteboard.tsx`

- [ ] **Step 1: Create PipelineMode component**

Create `frontend/src/components/game/whiteboard/PipelineMode.tsx` that renders a vertical list of pipeline steps on the whiteboard canvas using PixiJS Graphics and Text. Each step shows: status icon (colored circle), step name, and agent icon. Active step pulses. Use the existing whiteboard patterns from other modes in the `whiteboard/` directory.

- [ ] **Step 2: Add pipeline mode to Whiteboard.tsx**

Add mode 11 (`pipeline`) to the whiteboard mode cycle. When `pipelineState` is available in the game store, auto-switch to pipeline mode. When no squad is active, allow normal mode cycling.

- [ ] **Step 3: Test visually**

```bash
cd /root/claude-office && make dev-tmux
```
Open browser, verify whiteboard shows pipeline mode when a squad is active.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/game/whiteboard/PipelineMode.tsx frontend/src/components/game/Whiteboard.tsx
git commit -m "feat: add pipeline whiteboard mode showing squad progress"
```

---

### Task 16: Modify Page Layout (Chat + Office)

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Add ChatPanel to layout**

Modify `page.tsx` to add ChatPanel on the left side. Desktop: chat takes 40% width, office takes 60%. Mobile: chat fullscreen with tab to switch to office.

Import ChatPanel and add it to the layout alongside the existing OfficeGame component. Use CSS grid or flex for the split.

- [ ] **Step 2: Test responsive layout**

Open in browser, verify:
- Desktop: chat left, office right
- Resize to mobile: chat takes full screen
- Office still renders properly

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat: add chat-first layout with 40/60 split (chat + office)"
```

---

### Task 17: Squad WebSocket Events

**Files:**
- Modify: `frontend/src/hooks/useWebSocketEvents.ts`
- Modify: `frontend/src/stores/gameStore.ts`

- [ ] **Step 1: Add squad event handling to useWebSocketEvents**

Handle new WebSocket message types:
- `squad_update`: Update squadStore with pipeline state, queue
- `squad_checkpoint`: Add checkpoint message to chatStore
- `squad_agent_message`: Add agent output message to chatStore

- [ ] **Step 2: Add pipeline state to gameStore**

Add `pipelineState` field to gameStore so whiteboard can read it.

- [ ] **Step 3: Test with simulated events**

```bash
# Send a test event to the backend
curl -X POST http://localhost:8000/api/v1/squads/start \
  -H "Content-Type: application/json" \
  -d '{"squad_code": "fabrica-de-conteudo", "session_id": "test"}'
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useWebSocketEvents.ts frontend/src/stores/gameStore.ts
git commit -m "feat: handle squad WebSocket events for real-time pipeline updates"
```

---

## Chunk 6: Docker, README, and GitHub

### Task 18: Docker Compose Setup

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create Dockerfile**

Multi-stage build: Python backend + Node frontend. Final image serves both.

```dockerfile
# Dockerfile
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/bun.lockb* ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.13-slim AS backend
WORKDIR /app
RUN pip install uv
COPY backend/pyproject.toml backend/uv.lock* ./backend/
RUN cd backend && uv sync --frozen
COPY backend/ ./backend/
COPY socialforge/ ./socialforge/
COPY --from=frontend-build /app/frontend/.next ./frontend/.next
COPY --from=frontend-build /app/frontend/public ./frontend/public
COPY --from=frontend-build /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-build /app/frontend/package.json ./frontend/

EXPOSE 8000 3333
CMD ["sh", "-c", "cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 & cd /app/frontend && npx next start -p 3333 & wait"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
# docker-compose.yml
version: "3.8"
services:
  socialforge:
    build: .
    ports:
      - "3333:3333"
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

- [ ] **Step 3: Test build**

```bash
docker compose build
```

- [ ] **Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: add Docker and docker-compose for one-command deployment"
```

---

### Task 19: README for Non-Technical Users

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write new README**

Replace current README with SocialForge-focused content:
- Title: "SocialForge — Seu Time de IA para Social Media"
- 2-sentence description
- Screenshot placeholder
- Installation in 3 commands
- "Como Usar" section with examples
- Squad descriptions (non-technical)
- Environment variables (just ANTHROPIC_API_KEY)
- No jargon

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add user-friendly README for SocialForge"
```

---

### Task 20: Create GitHub Repository and Push

- [ ] **Step 1: Create repo**

```bash
gh repo create socialforge --public --description "Seu time de IA para social media — agentes especializados em conteúdo, diagnóstico e gestão de clientes" --source=. --remote=origin
```

- [ ] **Step 2: Push**

```bash
git push -u origin main
```

- [ ] **Step 3: Verify**

```bash
gh repo view socialforge --web
```

---

## Execution Order and Dependencies

```
Task 1 (copy squads) → no deps
Task 2 (models) → no deps
Task 3 (loader) → depends on Task 1, 2
Task 4 (registry) → depends on Task 2
Task 5 (EventData) → no deps
Task 6 (state machine) → depends on Task 5
Task 7 (queue) → depends on Task 2
Task 8 (chat router) → no deps
Task 9 (squad engine) → depends on Task 2, 3, 4, 7
Task 10 (API routes) → depends on Task 3, 7, 8, 9
Task 11 (TS types) → no deps
Task 12 (stores) → depends on Task 11
Task 13 (identities) → depends on Task 11
Task 14 (ChatPanel) → depends on Task 12, 13
Task 15 (whiteboard) → depends on Task 11
Task 16 (layout) → depends on Task 14
Task 17 (websocket) → depends on Task 12, 15
Task 18 (Docker) → depends on all above
Task 19 (README) → no deps
Task 20 (GitHub) → depends on all above
```

**Parallelizable groups:**
- Group A: Tasks 1, 2, 5, 8, 11, 19 (no dependencies)
- Group B: Tasks 3, 4, 6, 7, 12, 13, 15 (after Group A)
- Group C: Tasks 9, 14 (after Group B)
- Group D: Tasks 10, 16, 17 (after Group C)
- Group E: Tasks 18, 20 (final)
