"""Squad API routes — wired to SquadEngine for real pipeline execution."""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.api.websocket import manager
from app.core.agent_registry import AgentRegistry
from app.core.chat_router import ChatRouter
from app.core.queue_manager import QueueManager
from app.core.squad_engine import SquadEngine
from app.core.squad_loader import SquadLoader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/squads", tags=["squads"])

# Module-level service references
_squad_loader: Optional[SquadLoader] = None
_chat_router: Optional[ChatRouter] = None
_queue_manager: Optional[QueueManager] = None
_squad_engine: Optional[SquadEngine] = None


def init_squad_services(
    loader: SquadLoader,
    chat_router: ChatRouter,
    queue: QueueManager,
    engine: SquadEngine,
) -> None:
    """Initialize module-level service instances. Called during app lifespan startup."""
    global _squad_loader, _chat_router, _queue_manager, _squad_engine
    _squad_loader = loader
    _chat_router = chat_router
    _queue_manager = queue
    _squad_engine = engine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _broadcast_squad_state(session_id: str) -> None:
    """Broadcast current pipeline state and queue to all WebSocket clients."""
    if not _squad_engine or not _queue_manager:
        return

    state = _squad_engine.pipeline_state
    await manager.broadcast_all({
        "type": "squad_update",
        "pipeline_state": state.model_dump(by_alias=True) if state else None,
        "squad_queue": [item.model_dump(by_alias=True) for item in _queue_manager.list_all()],
    })


async def _broadcast_checkpoint(step_id: str, step_name: str, content: str) -> None:
    """Broadcast checkpoint event to chat."""
    await manager.broadcast_all({
        "type": "squad_checkpoint",
        "step_id": step_id,
        "step_name": step_name,
        "content": content,
    })


async def _broadcast_agent_message(
    text: str, agent_name: str = "", agent_icon: str = "", agent_color: str = ""
) -> None:
    """Broadcast agent output message to chat."""
    await manager.broadcast_all({
        "type": "squad_agent_message",
        "text": text,
        "agent_name": agent_name,
        "agent_icon": agent_icon,
        "agent_color": agent_color,
    })


async def _run_pipeline_loop(session_id: str) -> None:
    """Run the pipeline, broadcasting state at each step and pausing at checkpoints."""
    if not _squad_engine or not _queue_manager:
        return

    engine = _squad_engine
    registry = AgentRegistry()

    while True:
        state = engine.pipeline_state
        if not state or state.status in ("completed", "error"):
            break
        if state.status == "paused":
            # Broadcast checkpoint to chat
            if state.checkpoint and state.checkpoint.awaiting_approval:
                await _broadcast_checkpoint(
                    state.checkpoint.step_id,
                    state.checkpoint.step_name,
                    state.checkpoint.content,
                )
            await _broadcast_squad_state(session_id)
            break

        step = engine.current_step()
        if not step:
            break

        # Broadcast that agent is starting
        if step.type.value == "agent" and step.agent:
            identity = registry.get_identity(state.squad_code, step.agent)
            if identity:
                await _broadcast_agent_message(
                    f"Trabalhando em: {step.name}...",
                    agent_name=identity.display_name,
                    agent_icon=identity.icon,
                    agent_color=identity.color,
                )

        # Execute the step
        result = await engine.execute_current_step()

        # If agent step completed, broadcast the output
        if result and step.type.value == "agent" and step.agent:
            identity = registry.get_identity(state.squad_code, step.agent)
            if identity:
                # Truncate long outputs for chat display
                display_text = result if len(result) < 2000 else result[:2000] + "\n\n... (resultado completo salvo)"
                await _broadcast_agent_message(
                    display_text,
                    agent_name=identity.display_name,
                    agent_icon=identity.icon,
                    agent_color=identity.color,
                )

        await _broadcast_squad_state(session_id)

        # If we just hit a checkpoint, stop
        new_state = engine.pipeline_state
        if new_state and new_state.status == "paused":
            if new_state.checkpoint and new_state.checkpoint.awaiting_approval:
                await _broadcast_checkpoint(
                    new_state.checkpoint.step_id,
                    new_state.checkpoint.step_name,
                    new_state.checkpoint.content,
                )
            break

    # Check if pipeline completed — start next in queue
    final_state = engine.pipeline_state
    if final_state and final_state.status == "completed":
        await _broadcast_agent_message(
            "Pipeline concluído! Todos os artefatos foram gerados.",
            agent_name="SocialForge",
            agent_icon="✅",
            agent_color="#4CAF50",
        )
        next_code = _queue_manager.complete_active()
        if next_code:
            engine.start_squad(next_code, session_id)
            await _broadcast_squad_state(session_id)
            await _run_pipeline_loop(session_id)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class StartSquadRequest(BaseModel):
    squad_code: str
    session_id: str = "default"
    user_input: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ApproveRequest(BaseModel):
    approved: bool = True
    feedback: Optional[str] = None
    session_id: str = "default"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("")
async def list_squads() -> list[dict]:
    """Return a summary list of all loaded squads."""
    assert _squad_loader is not None
    return _squad_loader.list_squads()


@router.get("/queue")
async def list_queue() -> list[dict]:
    """Return all items currently in the execution queue."""
    assert _queue_manager is not None
    return [item.model_dump(by_alias=False) for item in _queue_manager.list_all()]


@router.get("/{squad_code}")
async def get_squad(squad_code: str) -> dict:
    """Return full detail for a single squad."""
    assert _squad_loader is not None
    squad = _squad_loader.get(squad_code)
    if squad is None:
        raise HTTPException(status_code=404, detail=f"Squad '{squad_code}' not found")
    return squad.model_dump()


@router.post("/start")
async def start_squad(body: StartSquadRequest, background_tasks: BackgroundTasks) -> dict:
    """Start or enqueue a squad. If it's the active one, begin pipeline execution."""
    assert _squad_loader is not None
    assert _queue_manager is not None
    assert _squad_engine is not None

    squad = _squad_loader.get(body.squad_code)
    if squad is None:
        raise HTTPException(status_code=404, detail=f"Squad '{body.squad_code}' not found")

    was_active_before = _queue_manager.active_item() is not None
    item = _queue_manager.enqueue(squad.code, squad.name, body.user_input)
    status = "queued" if was_active_before else "started"

    # If this squad is now active, start the pipeline
    if not was_active_before:
        _squad_engine.start_squad(body.squad_code, body.session_id)
        # Store user input as first checkpoint output if provided
        if body.user_input:
            state = _squad_engine.pipeline_state
            if state:
                state.outputs["user_input"] = body.user_input

        # Run pipeline in background so the HTTP response returns immediately
        background_tasks.add_task(_run_pipeline_loop, body.session_id)

    return {
        "status": status,
        "queue_position": item.position,
        "squad_name": squad.name,
    }


@router.delete("/queue/{item_id}")
async def remove_from_queue(item_id: str) -> dict:
    """Remove a pending item from the queue."""
    assert _queue_manager is not None

    active = _queue_manager.active_item()
    if active is not None and active.id == item_id:
        raise HTTPException(status_code=400, detail="Cannot remove active squad")

    removed = _queue_manager.remove(item_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found")
    return {"status": "removed"}


@router.post("/chat")
async def chat(body: ChatRequest, background_tasks: BackgroundTasks) -> dict:
    """Route a user message to a squad. Auto-starts if high confidence match."""
    assert _chat_router is not None
    assert _squad_engine is not None
    assert _queue_manager is not None

    result = await _chat_router.route(body.message)

    # Auto-start if high confidence and no active squad
    if result.get("squad_code") and result.get("confidence") == "high":
        if _queue_manager.active_item() is None:
            squad = _squad_loader.get(result["squad_code"]) if _squad_loader else None
            if squad:
                _queue_manager.enqueue(squad.code, squad.name, body.message)
                _squad_engine.start_squad(squad.code, body.session_id)
                state = _squad_engine.pipeline_state
                if state:
                    state.outputs["user_input"] = body.message
                background_tasks.add_task(_run_pipeline_loop, body.session_id)
                result["auto_started"] = True

    return result


@router.post("/approve")
async def approve_checkpoint(body: ApproveRequest, background_tasks: BackgroundTasks) -> dict:
    """Approve or adjust a checkpoint, then resume pipeline."""
    assert _squad_engine is not None

    state = _squad_engine.pipeline_state
    if not state or not state.checkpoint:
        raise HTTPException(status_code=400, detail="No checkpoint awaiting approval")

    await _squad_engine.approve_checkpoint(
        user_input=body.feedback or "",
        approved=body.approved,
    )

    status = "approved" if body.approved else "adjusted"

    if body.approved:
        # Resume pipeline execution in background
        background_tasks.add_task(_run_pipeline_loop, body.session_id)

    await _broadcast_squad_state(body.session_id)

    return {"status": status}
