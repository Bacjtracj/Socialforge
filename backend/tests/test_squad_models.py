"""Tests for squad Pydantic models."""

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


class TestEnums:
    def test_pipeline_step_type_values(self):
        assert PipelineStepType.AGENT == "agent"
        assert PipelineStepType.CHECKPOINT == "checkpoint"

    def test_pipeline_step_status_values(self):
        assert PipelineStepStatus.PENDING == "pending"
        assert PipelineStepStatus.ACTIVE == "active"
        assert PipelineStepStatus.COMPLETED == "completed"
        assert PipelineStepStatus.WAITING_APPROVAL == "waiting_approval"
        assert PipelineStepStatus.APPROVED == "approved"
        assert PipelineStepStatus.RETRY == "retry"
        assert PipelineStepStatus.ERROR == "error"

    def test_squad_status_values(self):
        assert SquadStatus.PENDING == "pending"
        assert SquadStatus.RUNNING == "running"
        assert SquadStatus.PAUSED == "paused"
        assert SquadStatus.COMPLETED == "completed"
        assert SquadStatus.ERROR == "error"


class TestAgentDefinition:
    def test_instantiation(self):
        agent = AgentDefinition(id="writer", name="Writer Agent", icon="✍️")
        assert agent.id == "writer"
        assert agent.name == "Writer Agent"
        assert agent.icon == "✍️"


class TestPipelineStep:
    def test_agent_step(self):
        step = PipelineStep(
            id="step-1",
            name="Research",
            type=PipelineStepType.AGENT,
            file="research.md",
            agent="researcher",
            tasks=["task1", "task2"],
            depends_on=None,
        )
        assert step.id == "step-1"
        assert step.type == PipelineStepType.AGENT
        assert step.tasks == ["task1", "task2"]
        assert step.agent == "researcher"
        assert step.depends_on is None

    def test_checkpoint_step_defaults(self):
        step = PipelineStep(
            id="cp-1",
            name="Review",
            type=PipelineStepType.CHECKPOINT,
            file="review.md",
        )
        assert step.type == PipelineStepType.CHECKPOINT
        assert step.tasks == []
        assert step.agent is None
        assert step.depends_on is None

    def test_step_with_depends_on(self):
        step = PipelineStep(
            id="step-2",
            name="Write",
            type=PipelineStepType.AGENT,
            file="write.md",
            depends_on="step-1",
        )
        assert step.depends_on == "step-1"


class TestSquadPipeline:
    def test_instantiation(self):
        step = PipelineStep(
            id="s1", name="Step 1", type=PipelineStepType.AGENT, file="s1.md"
        )
        pipeline = SquadPipeline(
            name="My Pipeline",
            steps=[step],
            checkpoints=["cp-1"],
        )
        assert pipeline.name == "My Pipeline"
        assert len(pipeline.steps) == 1
        assert pipeline.checkpoints == ["cp-1"]

    def test_empty_defaults(self):
        pipeline = SquadPipeline(name="Empty Pipeline")
        assert pipeline.steps == []
        assert pipeline.checkpoints == []


class TestSquad:
    def test_instantiation(self):
        agent_def = AgentDefinition(id="a1", name="Agent One", icon="🤖")
        pipeline = SquadPipeline(name="Main Pipeline")
        squad = Squad(
            name="Social Squad",
            code="social",
            description="Social media squad",
            icon="📱",
            version="1.0.0",
            agents=[agent_def],
            pipeline=pipeline,
            data_files=["input.json"],
            squad_dir="/squads/social",
        )
        assert squad.name == "Social Squad"
        assert squad.code == "social"
        assert len(squad.agents) == 1
        assert squad.data_files == ["input.json"]
        assert squad.squad_dir == "/squads/social"

    def test_empty_defaults(self):
        pipeline = SquadPipeline(name="Pipeline")
        squad = Squad(
            name="Minimal Squad",
            code="minimal",
            description="Minimal",
            icon="🔧",
            version="0.1.0",
            pipeline=pipeline,
            squad_dir="/squads/minimal",
        )
        assert squad.agents == []
        assert squad.data_files == []


class TestAgentIdentity:
    def test_instantiation_by_name(self):
        identity = AgentIdentity(
            squad_agent_id="agent-1",
            display_name="Alice",
            color="#ff6600",
            sprite_key="worker_1",
            icon="👩",
        )
        assert identity.squad_agent_id == "agent-1"
        assert identity.display_name == "Alice"
        assert identity.color == "#ff6600"

    def test_camel_case_alias(self):
        identity = AgentIdentity(
            squadAgentId="agent-2",
            displayName="Bob",
            color="#0066ff",
            spriteKey="worker_2",
            icon="👨",
        )
        assert identity.squad_agent_id == "agent-2"
        assert identity.display_name == "Bob"
        assert identity.sprite_key == "worker_2"

    def test_serialization_uses_camel_case(self):
        identity = AgentIdentity(
            squad_agent_id="agent-3",
            display_name="Carol",
            color="#00ff66",
            sprite_key="worker_3",
            icon="🧑",
        )
        data = identity.model_dump(by_alias=True)
        assert "squadAgentId" in data
        assert "displayName" in data
        assert "spriteKey" in data


class TestCheckpointState:
    def test_instantiation(self):
        cp = CheckpointState(
            step_id="cp-1",
            step_name="Review Output",
            content="Please review this content.",
            awaiting_approval=True,
        )
        assert cp.step_id == "cp-1"
        assert cp.awaiting_approval is True
        assert cp.approved is None
        assert cp.feedback is None

    def test_with_approval(self):
        cp = CheckpointState(
            step_id="cp-2",
            step_name="Final Review",
            content="Looks good.",
            awaiting_approval=False,
            approved=True,
            feedback="Approved with minor changes.",
        )
        assert cp.approved is True
        assert cp.feedback == "Approved with minor changes."

    def test_camel_case_alias(self):
        cp = CheckpointState(
            stepId="cp-3",
            stepName="Check",
            content="Content here.",
            awaitingApproval=True,
        )
        assert cp.step_id == "cp-3"
        assert cp.step_name == "Check"
        assert cp.awaiting_approval is True


class TestPipelineState:
    def test_instantiation_with_defaults(self):
        state = PipelineState(
            squad_code="social",
            session_id="sess-abc",
            total_steps=5,
        )
        assert state.squad_code == "social"
        assert state.session_id == "sess-abc"
        assert state.total_steps == 5
        assert state.current_step_index == 0
        assert state.status == SquadStatus.PENDING
        assert state.step_states == {}
        assert state.outputs == {}
        assert state.checkpoint is None
        assert state.started_at is None
        assert state.completed_at is None

    def test_instantiation_full(self):
        cp = CheckpointState(
            step_id="cp-1",
            step_name="Review",
            content="Check this.",
            awaiting_approval=True,
        )
        state = PipelineState(
            squad_code="blog",
            session_id="sess-xyz",
            total_steps=3,
            current_step_index=2,
            status=SquadStatus.PAUSED,
            step_states={"step-1": "completed"},
            outputs={"step-1": "output text"},
            checkpoint=cp,
            started_at="2026-04-02T10:00:00Z",
        )
        assert state.current_step_index == 2
        assert state.status == SquadStatus.PAUSED
        assert state.checkpoint is not None
        assert state.checkpoint.step_id == "cp-1"

    def test_camel_case_alias(self):
        state = PipelineState(
            squadCode="social",
            sessionId="sess-123",
            totalSteps=4,
        )
        assert state.squad_code == "social"
        assert state.session_id == "sess-123"
        assert state.total_steps == 4

    def test_serialization_uses_camel_case(self):
        state = PipelineState(
            squad_code="social",
            session_id="sess-456",
            total_steps=2,
        )
        data = state.model_dump(by_alias=True)
        assert "squadCode" in data
        assert "sessionId" in data
        assert "totalSteps" in data
        assert "currentStepIndex" in data


class TestSquadQueueItem:
    def test_instantiation(self):
        item = SquadQueueItem(
            id="q-1",
            squad_code="social",
            squad_name="Social Squad",
            position=1,
        )
        assert item.id == "q-1"
        assert item.squad_code == "social"
        assert item.position == 1
        assert item.user_input is None

    def test_with_user_input(self):
        item = SquadQueueItem(
            id="q-2",
            squad_code="blog",
            squad_name="Blog Squad",
            position=2,
            user_input="Write about AI trends",
        )
        assert item.user_input == "Write about AI trends"

    def test_camel_case_alias(self):
        item = SquadQueueItem(
            id="q-3",
            squadCode="social",
            squadName="Social Squad",
            position=3,
        )
        assert item.squad_code == "social"
        assert item.squad_name == "Social Squad"

    def test_serialization_uses_camel_case(self):
        item = SquadQueueItem(
            id="q-4",
            squad_code="social",
            squad_name="Social Squad",
            position=4,
        )
        data = item.model_dump(by_alias=True)
        assert "squadCode" in data
        assert "squadName" in data
        assert "userInput" in data
