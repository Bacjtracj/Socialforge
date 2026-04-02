"""Squad API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.chat_router import ChatRouter
from app.core.queue_manager import QueueManager
from app.core.squad_loader import SquadLoader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/squads", tags=["squads"])

# Module-level service references, initialized during app startup
_squad_loader: Optional[SquadLoader] = None
_chat_router: Optional[ChatRouter] = None
_queue_manager: Optional[QueueManager] = None


def init_squad_services(
    loader: SquadLoader,
    chat_router: ChatRouter,
    queue: QueueManager,
) -> None:
    """Initialize module-level service instances. Called during app lifespan startup."""
    global _squad_loader, _chat_router, _queue_manager
    _squad_loader = loader
    _chat_router = chat_router
    _queue_manager = queue


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class StartSquadRequest(BaseModel):
    """Body for POST /squads/start."""

    squad_code: str
    session_id: str
    user_input: Optional[str] = None


class ChatRequest(BaseModel):
    """Body for POST /squads/chat."""

    message: str
    session_id: str


class ApproveRequest(BaseModel):
    """Body for POST /squads/approve."""

    approved: bool
    feedback: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("")
async def list_squads() -> list[dict]:
    """Return a summary list of all loaded squads."""
    assert _squad_loader is not None, "Squad services not initialised"
    return _squad_loader.list_squads()


# IMPORTANT: /queue must be declared BEFORE /{squad_code} to avoid route conflict.
@router.get("/queue")
async def list_queue() -> list[dict]:
    """Return all items currently in the execution queue."""
    assert _queue_manager is not None, "Squad services not initialised"
    return [item.model_dump(by_alias=False) for item in _queue_manager.list_all()]


@router.get("/{squad_code}")
async def get_squad(squad_code: str) -> dict:
    """Return full detail for a single squad by its code."""
    assert _squad_loader is not None, "Squad services not initialised"
    squad = _squad_loader.get(squad_code)
    if squad is None:
        raise HTTPException(status_code=404, detail=f"Squad '{squad_code}' not found")
    return squad.model_dump()


@router.post("/start")
async def start_squad(body: StartSquadRequest) -> dict:
    """Enqueue a squad for execution.

    Returns whether the squad was started immediately or queued behind
    an active squad, along with its queue position and name.
    """
    assert _squad_loader is not None, "Squad services not initialised"
    assert _queue_manager is not None, "Squad services not initialised"

    squad = _squad_loader.get(body.squad_code)
    if squad is None:
        raise HTTPException(status_code=404, detail=f"Squad '{body.squad_code}' not found")

    was_active_before = _queue_manager.active_item() is not None
    item = _queue_manager.enqueue(
        squad_code=body.squad_code,
        squad_name=squad.name,
        user_input=body.user_input,
    )

    status = "queued" if was_active_before else "started"
    return {
        "status": status,
        "queue_position": item.position,
        "squad_name": squad.name,
    }


@router.delete("/queue/{item_id}")
async def remove_from_queue(item_id: str) -> dict:
    """Remove a pending item from the execution queue.

    Returns 400 if the item is currently active (cannot be removed while running).
    """
    assert _queue_manager is not None, "Squad services not initialised"

    active = _queue_manager.active_item()
    if active is not None and active.id == item_id:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove active queue item '{item_id}'",
        )

    removed = _queue_manager.remove(item_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found")

    return {"status": "removed", "item_id": item_id}


@router.post("/chat")
async def chat(body: ChatRequest) -> dict:
    """Route a user message to the appropriate squad using keyword matching."""
    assert _chat_router is not None, "Squad services not initialised"
    result = await _chat_router.route(body.message)
    return result


@router.post("/approve")
async def approve_checkpoint(body: ApproveRequest) -> dict:
    """Approve or adjust a pending checkpoint.

    Returns the resolved status based on whether the checkpoint was approved.
    """
    status = "approved" if body.approved else "adjusted"
    return {"status": status}
