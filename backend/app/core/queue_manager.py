"""Queue manager for squad execution - FIFO, one active at a time."""

import uuid
from typing import Optional

from app.models.squads import SquadQueueItem

__all__ = ["QueueManager"]


class QueueManager:
    """Manages a FIFO execution queue for squads with one active item at a time."""

    def __init__(self) -> None:
        self._active: Optional[SquadQueueItem] = None
        self._pending: list[SquadQueueItem] = []

    def enqueue(
        self, squad_code: str, squad_name: str, user_input: Optional[str] = None
    ) -> SquadQueueItem:
        """Add a squad to the queue.

        If no active item exists, the new item becomes active (position=1).
        Otherwise it is appended to the pending list.
        """
        item_id = str(uuid.uuid4())[:8]

        if self._active is None:
            item = SquadQueueItem(
                id=item_id,
                squad_code=squad_code,
                squad_name=squad_name,
                position=1,
                user_input=user_input,
            )
            self._active = item
        else:
            position = len(self._pending) + 2  # active is 1, pending starts at 2
            item = SquadQueueItem(
                id=item_id,
                squad_code=squad_code,
                squad_name=squad_name,
                position=position,
                user_input=user_input,
            )
            self._pending.append(item)

        return item

    def active_squad(self) -> Optional[str]:
        """Return the squad code of the active item, or None."""
        return self._active.squad_code if self._active else None

    def active_item(self) -> Optional[SquadQueueItem]:
        """Return the active queue item, or None."""
        return self._active

    def complete_active(self) -> Optional[str]:
        """Mark the active item as done and promote the next pending item.

        Returns the new active squad code, or None if the queue is now empty.
        """
        if self._pending:
            self._active = self._pending.pop(0)
            self._reindex()
            return self._active.squad_code
        else:
            self._active = None
            return None

    def remove(self, item_id: str) -> bool:
        """Remove an item from the pending list by ID.

        Cannot remove the active item. Returns True if removed, False otherwise.
        """
        for i, item in enumerate(self._pending):
            if item.id == item_id:
                self._pending.pop(i)
                self._reindex()
                return True
        return False

    def pending(self) -> list[SquadQueueItem]:
        """Return a copy of the pending items list."""
        return list(self._pending)

    def list_all(self) -> list[SquadQueueItem]:
        """Return all items: active first, then pending in order."""
        result: list[SquadQueueItem] = []
        if self._active is not None:
            result.append(self._active)
        result.extend(self._pending)
        return result

    def _reindex(self) -> None:
        """Update position numbers: active=1, pending=2,3,..."""
        if self._active is not None:
            self._active = self._active.model_copy(update={"position": 1})
        for i, item in enumerate(self._pending):
            self._pending[i] = item.model_copy(update={"position": i + 2})
