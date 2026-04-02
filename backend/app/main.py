import importlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from rich.logging import RichHandler

from app.api.routes import events, preferences, sessions
from app.api.websocket import manager
from app.config import get_settings
from app.core.event_processor import event_processor
from app.core.summary_service import get_summary_service
from app.db.database import Base, get_engine
from app.services.git_service import git_service

STATIC_DIR = Path(__file__).parent.parent / "static"


logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[RichHandler(rich_tracebacks=True)]
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    importlib.import_module("app.db.models")
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    git_service.start()

    from pathlib import Path
    from app.core.squad_loader import SquadLoader
    from app.core.chat_router import ChatRouter
    from app.core.queue_manager import QueueManager
    from app.core.squad_engine import SquadEngine
    from app.core.agent_registry import AgentRegistry
    from app.core.event_processor import event_processor
    from app.api.routes.squads import init_squad_services

    squads_dir = Path(__file__).resolve().parents[2] / "socialforge" / "squads"
    squad_loader = SquadLoader(squads_dir=squads_dir)
    squad_loader.load_all()
    chat_router_instance = ChatRouter(squad_loader.list_squads())
    queue_manager = QueueManager()
    registry = AgentRegistry()

    async def emit_event(event):
        await event_processor.process_event(event)

    async def broadcast_state(state):
        pass  # Broadcasting handled in route handlers

    squad_engine = SquadEngine(
        loader=squad_loader,
        registry=registry,
        queue=queue_manager,
        emit_event=emit_event,
        broadcast_state=broadcast_state,
    )
    init_squad_services(squad_loader, chat_router_instance, queue_manager, squad_engine)

    yield

    await git_service.stop()
    await get_engine().dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix=f"{settings.API_V1_STR}")
app.include_router(preferences.router, prefix=f"{settings.API_V1_STR}")
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}")

from app.api.routes.squads import router as squad_router  # noqa: E402
app.include_router(squad_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/status")
async def get_status() -> dict[str, bool | str | None]:
    """Get server status including AI summary availability."""
    summary_service = get_summary_service()
    return {
        "aiSummaryEnabled": summary_service.enabled,
        "aiSummaryModel": summary_service.model if summary_service.enabled else None,
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    await manager.connect(websocket, session_id)

    current_state = await event_processor.get_current_state(session_id)
    if current_state:
        await manager.send_personal_message(
            {
                "type": "state_update",
                "timestamp": current_state.last_updated.isoformat(),
                "state": current_state.model_dump(mode="json", by_alias=True),
            },
            websocket,
        )

    project_root = await event_processor.get_project_root(session_id)
    if project_root:
        git_service.configure(session_id=session_id, project_root=project_root)

    git_status = git_service.get_status()
    if git_status:
        await manager.send_personal_message(
            {
                "type": "git_status",
                "timestamp": git_status.last_updated.isoformat(),
                "gitStatus": git_status.model_dump(mode="json"),
            },
            websocket,
        )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)


if STATIC_DIR.exists():
    app.mount("/_next", StaticFiles(directory=STATIC_DIR / "_next"), name="next_static")

    @app.get("/{path:path}")
    async def serve_frontend(path: str) -> FileResponse:
        """Serve static frontend files with SPA fallback routing."""
        file_path = STATIC_DIR / path
        if file_path.is_file():
            return FileResponse(file_path)

        html_path = STATIC_DIR / f"{path}.html"
        if html_path.is_file():
            return FileResponse(html_path)

        index_path = STATIC_DIR / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)

        not_found_path = STATIC_DIR / "404.html"
        if not_found_path.is_file():
            return FileResponse(not_found_path, status_code=404)
        return FileResponse(index_path)

    @app.get("/")
    async def serve_index() -> FileResponse:
        """Serve the index page."""
        return FileResponse(STATIC_DIR / "index.html")
