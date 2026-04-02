from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

__all__ = [
    "PipelineStepType",
    "PipelineStepStatus",
    "SquadStatus",
    "AgentDefinition",
    "PipelineStep",
    "SquadPipeline",
    "Squad",
    "AgentIdentity",
    "CheckpointState",
    "PipelineState",
    "SquadQueueItem",
]


class PipelineStepType(StrEnum):
    """Type of pipeline step."""

    AGENT = "agent"
    CHECKPOINT = "checkpoint"


class PipelineStepStatus(StrEnum):
    """Status of an individual pipeline step."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    RETRY = "retry"
    ERROR = "error"


class SquadStatus(StrEnum):
    """Overall status of a squad run."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class AgentDefinition(BaseModel):
    """An agent entry from squad.yaml."""

    id: str
    name: str
    icon: str


class PipelineStep(BaseModel):
    """A single step in the squad pipeline."""

    id: str
    name: str
    type: PipelineStepType
    file: str
    agent: str | None = None
    tasks: list[str] = []
    depends_on: str | None = None


class SquadPipeline(BaseModel):
    """The pipeline definition for a squad."""

    name: str
    steps: list[PipelineStep] = []
    checkpoints: list[str] = []


class Squad(BaseModel):
    """A squad definition loaded from squad.yaml."""

    name: str
    code: str
    description: str
    icon: str
    version: str
    agents: list[AgentDefinition] = []
    pipeline: SquadPipeline
    data_files: list[str] = []
    squad_dir: str


class AgentIdentity(BaseModel):
    """Identity information for a squad agent."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    squad_agent_id: str
    display_name: str
    color: str  # hex color
    sprite_key: str
    icon: str


class CheckpointState(BaseModel):
    """State of a checkpoint step requiring human approval."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    step_id: str
    step_name: str
    content: str
    awaiting_approval: bool
    approved: bool | None = None
    feedback: str | None = None


class PipelineState(BaseModel):
    """Runtime state of a squad pipeline execution."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    squad_code: str
    session_id: str
    total_steps: int
    current_step_index: int = 0
    status: SquadStatus = SquadStatus.PENDING
    step_states: dict[str, Any] = {}
    outputs: dict[str, Any] = {}
    checkpoint: CheckpointState | None = None
    started_at: str | None = None
    completed_at: str | None = None


class SquadQueueItem(BaseModel):
    """An item in the squad execution queue."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    squad_code: str
    squad_name: str
    position: int
    user_input: str | None = None
