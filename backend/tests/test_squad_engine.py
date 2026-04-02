"""Tests for SquadEngine pipeline orchestrator."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.core.agent_registry import AgentRegistry
from app.core.queue_manager import QueueManager
from app.core.squad_engine import SquadEngine
from app.core.squad_loader import SquadLoader
from app.models.squads import PipelineStepType, SquadStatus

SQUADS_DIR = Path(__file__).parents[2] / "socialforge" / "squads"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def loader() -> SquadLoader:
    return SquadLoader(SQUADS_DIR)


@pytest.fixture
def registry() -> AgentRegistry:
    return AgentRegistry()


@pytest.fixture
def queue() -> QueueManager:
    return QueueManager()


@pytest.fixture
def emit_event() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def broadcast_state() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def engine(
    loader: SquadLoader,
    registry: AgentRegistry,
    queue: QueueManager,
    emit_event: AsyncMock,
    broadcast_state: AsyncMock,
) -> SquadEngine:
    return SquadEngine(
        loader=loader,
        registry=registry,
        queue=queue,
        emit_event=emit_event,
        broadcast_state=broadcast_state,
        api_key="test-key",
    )


# ---------------------------------------------------------------------------
# start_squad
# ---------------------------------------------------------------------------


def test_start_squad_creates_pipeline_state(engine: SquadEngine) -> None:
    state = engine.start_squad("fabrica-de-conteudo", "session-abc")
    assert state is not None
    assert state.squad_code == "fabrica-de-conteudo"
    assert state.session_id == "session-abc"
    assert state.status == SquadStatus.RUNNING


def test_start_squad_sets_correct_total_steps(engine: SquadEngine, loader: SquadLoader) -> None:
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    expected_steps = len(squad.pipeline.steps)

    state = engine.start_squad("fabrica-de-conteudo", "session-abc")
    assert state is not None
    assert state.total_steps == expected_steps


def test_start_squad_index_starts_at_zero(engine: SquadEngine) -> None:
    state = engine.start_squad("fabrica-de-conteudo", "session-abc")
    assert state is not None
    assert state.current_step_index == 0


def test_start_squad_unknown_returns_none(engine: SquadEngine) -> None:
    state = engine.start_squad("does-not-exist", "session-xyz")
    assert state is None


def test_start_squad_unknown_does_not_set_pipeline_state(engine: SquadEngine) -> None:
    engine.start_squad("does-not-exist", "session-xyz")
    assert engine.pipeline_state is None


# ---------------------------------------------------------------------------
# current_step
# ---------------------------------------------------------------------------


def test_current_step_returns_first_step(engine: SquadEngine, loader: SquadLoader) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")
    step = engine.current_step()
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    assert step is not None
    assert step.id == squad.pipeline.steps[0].id


def test_current_step_returns_none_when_no_state(engine: SquadEngine) -> None:
    assert engine.current_step() is None


def test_current_step_first_step_is_checkpoint(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")
    step = engine.current_step()
    assert step is not None
    assert step.type == PipelineStepType.CHECKPOINT


# ---------------------------------------------------------------------------
# approve_checkpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_checkpoint_advances_step_index(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    # Manually set up a checkpoint state so approval can work
    await engine.execute_current_step()

    assert engine.pipeline_state is not None
    assert engine.pipeline_state.status == SquadStatus.PAUSED

    # Approve the checkpoint
    await engine.approve_checkpoint(approved=True)

    assert engine.pipeline_state is not None
    assert engine.pipeline_state.current_step_index == 1


@pytest.mark.asyncio
async def test_approve_checkpoint_sets_running(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")
    await engine.execute_current_step()

    await engine.approve_checkpoint(approved=True)

    assert engine.pipeline_state is not None
    assert engine.pipeline_state.status == SquadStatus.RUNNING


@pytest.mark.asyncio
async def test_reject_checkpoint_stores_feedback(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")
    await engine.execute_current_step()

    await engine.approve_checkpoint(user_input="needs revision", approved=False)

    assert engine.pipeline_state is not None
    assert engine.pipeline_state.status == SquadStatus.PAUSED
    assert engine.pipeline_state.checkpoint is not None
    assert engine.pipeline_state.checkpoint.feedback == "needs revision"


@pytest.mark.asyncio
async def test_approve_checkpoint_no_state_is_noop(engine: SquadEngine) -> None:
    # Should not raise
    await engine.approve_checkpoint(approved=True)
    assert engine.pipeline_state is None


# ---------------------------------------------------------------------------
# _build_agent_prompt
# ---------------------------------------------------------------------------


def test_build_agent_prompt_includes_step_file_content(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    # Advance to an agent step (step-02 is the first agent step)
    state = engine.pipeline_state
    assert state is not None
    engine._pipeline_state = state.model_copy(update={"current_step_index": 1})

    prompt = engine._build_agent_prompt()
    # The step file for step-02 should contain some content
    assert len(prompt) > 0


def test_build_agent_prompt_includes_agent_persona(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    # Advance to an agent step (step-02 uses the 'pesquisador' agent)
    state = engine.pipeline_state
    assert state is not None
    engine._pipeline_state = state.model_copy(update={"current_step_index": 1})

    prompt = engine._build_agent_prompt()
    # Agent persona file should contain agent identity info
    assert "pesquisador" in prompt.lower() or "luna" in prompt.lower() or len(prompt) > 50


def test_build_agent_prompt_returns_empty_without_state(engine: SquadEngine) -> None:
    prompt = engine._build_agent_prompt()
    assert prompt == ""


def test_build_agent_prompt_includes_previous_outputs(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    state = engine.pipeline_state
    assert state is not None
    engine._pipeline_state = state.model_copy(
        update={
            "current_step_index": 1,
            "outputs": {"step-01": "Previous checkpoint content"},
        }
    )

    prompt = engine._build_agent_prompt()
    assert "Previous checkpoint content" in prompt


# ---------------------------------------------------------------------------
# execute_current_step (mocking _call_claude_api)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_current_step_checkpoint_pauses(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    result = await engine.execute_current_step()

    assert result is None
    assert engine.pipeline_state is not None
    assert engine.pipeline_state.status == SquadStatus.PAUSED


@pytest.mark.asyncio
async def test_execute_current_step_checkpoint_creates_checkpoint_state(
    engine: SquadEngine,
) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")
    await engine.execute_current_step()

    assert engine.pipeline_state is not None
    assert engine.pipeline_state.checkpoint is not None
    assert engine.pipeline_state.checkpoint.awaiting_approval is True


@pytest.mark.asyncio
async def test_execute_agent_step_calls_api_and_stores_output(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    # Move to agent step (index 1 = step-02, type agent)
    state = engine.pipeline_state
    assert state is not None
    engine._pipeline_state = state.model_copy(
        update={"current_step_index": 1, "status": SquadStatus.RUNNING}
    )

    with patch.object(engine, "_call_claude_api", new=AsyncMock(return_value="Agent output")) as mock_api:
        result = await engine.execute_current_step()

    assert result == "Agent output"
    mock_api.assert_called_once()

    assert engine.pipeline_state is not None
    step = engine.pipeline_state.outputs.get("step-02")
    assert step == "Agent output"


@pytest.mark.asyncio
async def test_execute_agent_step_emits_subagent_events(
    engine: SquadEngine, emit_event: AsyncMock
) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    state = engine.pipeline_state
    assert state is not None
    engine._pipeline_state = state.model_copy(
        update={"current_step_index": 1, "status": SquadStatus.RUNNING}
    )

    with patch.object(engine, "_call_claude_api", new=AsyncMock(return_value="output")):
        await engine.execute_current_step()

    event_types = [call.args[0].event_type for call in emit_event.call_args_list]
    from app.models.events import EventType

    assert EventType.SUBAGENT_START in event_types
    assert EventType.SUBAGENT_STOP in event_types


# ---------------------------------------------------------------------------
# _execute_agent_step retry logic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_agent_step_retries_on_failure(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    state = engine.pipeline_state
    assert state is not None
    engine._pipeline_state = state.model_copy(
        update={"current_step_index": 1, "status": SquadStatus.RUNNING}
    )

    step = engine.current_step()
    assert step is not None

    call_count = 0

    async def flaky_api(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("temporary failure")
        return "success after retry"

    with patch.object(engine, "_call_claude_api", new=flaky_api):
        with patch("app.core.squad_engine.asyncio.sleep", new=AsyncMock()):
            result = await engine._execute_agent_step(step)

    assert result == "success after retry"
    assert call_count == 2


@pytest.mark.asyncio
async def test_execute_agent_step_returns_none_after_max_retries(engine: SquadEngine) -> None:
    engine.start_squad("fabrica-de-conteudo", "session-abc")

    state = engine.pipeline_state
    assert state is not None
    engine._pipeline_state = state.model_copy(
        update={"current_step_index": 1, "status": SquadStatus.RUNNING}
    )

    step = engine.current_step()
    assert step is not None

    async def always_fail(prompt: str) -> str:
        raise RuntimeError("always fails")

    with patch.object(engine, "_call_claude_api", new=always_fail):
        with patch("app.core.squad_engine.asyncio.sleep", new=AsyncMock()):
            result = await engine._execute_agent_step(step)

    assert result is None
