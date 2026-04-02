"""Tests for QueueManager."""

import pytest

from app.core.queue_manager import QueueManager


def test_first_enqueue_becomes_active():
    """First enqueued item starts immediately as active at position 1."""
    qm = QueueManager()
    item = qm.enqueue("squad-a", "Squad A")
    assert item.position == 1
    assert qm.active_squad() == "squad-a"
    assert qm.active_item() == item
    assert qm.pending() == []


def test_second_enqueue_goes_to_pending():
    """Second item is queued as pending at position 2."""
    qm = QueueManager()
    qm.enqueue("squad-a", "Squad A")
    item2 = qm.enqueue("squad-b", "Squad B")
    assert item2.position == 2
    assert qm.active_squad() == "squad-a"
    assert len(qm.pending()) == 1
    assert qm.pending()[0].squad_code == "squad-b"


def test_complete_active_promotes_next():
    """Completing the active item promotes the first pending item."""
    qm = QueueManager()
    qm.enqueue("squad-a", "Squad A")
    qm.enqueue("squad-b", "Squad B")
    new_code = qm.complete_active()
    assert new_code == "squad-b"
    assert qm.active_squad() == "squad-b"
    assert qm.active_item() is not None
    assert qm.active_item().position == 1
    assert qm.pending() == []


def test_complete_active_empty_queue_returns_none():
    """Completing when no pending items returns None."""
    qm = QueueManager()
    qm.enqueue("squad-a", "Squad A")
    result = qm.complete_active()
    assert result is None
    assert qm.active_squad() is None
    assert qm.active_item() is None


def test_remove_from_pending():
    """Can remove a pending item by ID."""
    qm = QueueManager()
    qm.enqueue("squad-a", "Squad A")
    item2 = qm.enqueue("squad-b", "Squad B")
    qm.enqueue("squad-c", "Squad C")
    success = qm.remove(item2.id)
    assert success is True
    pending = qm.pending()
    assert len(pending) == 1
    assert pending[0].squad_code == "squad-c"


def test_cannot_remove_active():
    """Attempting to remove the active item returns False."""
    qm = QueueManager()
    active = qm.enqueue("squad-a", "Squad A")
    result = qm.remove(active.id)
    assert result is False
    assert qm.active_squad() == "squad-a"


def test_positions_update_after_remove():
    """Positions are reindexed after a pending item is removed."""
    qm = QueueManager()
    qm.enqueue("squad-a", "Squad A")
    item2 = qm.enqueue("squad-b", "Squad B")
    qm.enqueue("squad-c", "Squad C")
    qm.enqueue("squad-d", "Squad D")
    # Remove squad-b (position 2); squad-c and squad-d should shift
    qm.remove(item2.id)
    pending = qm.pending()
    assert pending[0].squad_code == "squad-c"
    assert pending[0].position == 2
    assert pending[1].squad_code == "squad-d"
    assert pending[1].position == 3


def test_list_all_returns_all():
    """list_all returns active item followed by all pending items."""
    qm = QueueManager()
    a = qm.enqueue("squad-a", "Squad A")
    b = qm.enqueue("squad-b", "Squad B")
    c = qm.enqueue("squad-c", "Squad C")
    all_items = qm.list_all()
    assert len(all_items) == 3
    assert all_items[0].squad_code == "squad-a"
    assert all_items[1].squad_code == "squad-b"
    assert all_items[2].squad_code == "squad-c"


def test_list_all_empty():
    """list_all returns empty list when nothing is queued."""
    qm = QueueManager()
    assert qm.list_all() == []


def test_enqueue_with_user_input():
    """user_input is stored correctly."""
    qm = QueueManager()
    item = qm.enqueue("squad-a", "Squad A", user_input="some input")
    assert item.user_input == "some input"


def test_remove_nonexistent_returns_false():
    """Removing a non-existent ID returns False."""
    qm = QueueManager()
    qm.enqueue("squad-a", "Squad A")
    assert qm.remove("nonexistent") is False


def test_item_ids_are_8_chars():
    """Item IDs are 8 characters long."""
    qm = QueueManager()
    item = qm.enqueue("squad-a", "Squad A")
    assert len(item.id) == 8
