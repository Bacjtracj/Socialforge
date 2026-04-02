"""Tests for state machine squad agent metadata handling."""

from datetime import datetime

from app.core.state_machine import StateMachine
from app.models.events import Event, EventData, EventType


def make_subagent_start_event(
    agent_id: str = "agent-abc123",
    display_name: str | None = None,
    agent_color: str | None = None,
    squad_id: str | None = None,
    squad_agent_id: str | None = None,
) -> Event:
    """Helper to create a SUBAGENT_START event."""
    return Event(
        event_type=EventType.SUBAGENT_START,
        session_id="test-session",
        timestamp=datetime.now(),
        data=EventData(
            agent_id=agent_id,
            task_description="Test task",
            display_name=display_name,
            agent_color=agent_color,
            squad_id=squad_id,
            squad_agent_id=squad_agent_id,
        ),
    )


class TestSquadAgentMetadata:
    """Tests that squad metadata overrides default agent values."""

    def test_display_name_overrides_auto_name(self) -> None:
        """When display_name is provided, agent uses it instead of auto-generated name."""
        sm = StateMachine()
        event = make_subagent_start_event(
            agent_id="agent-001",
            display_name="Alice",
        )
        sm.transition(event)

        assert "agent-001" in sm.agents
        assert sm.agents["agent-001"].name == "Alice"

    def test_agent_color_overrides_default_color(self) -> None:
        """When agent_color is provided, agent uses it instead of the palette color."""
        sm = StateMachine()
        event = make_subagent_start_event(
            agent_id="agent-002",
            agent_color="#FF0000",
        )
        sm.transition(event)

        assert "agent-002" in sm.agents
        assert sm.agents["agent-002"].color == "#FF0000"

    def test_both_display_name_and_color_overridden(self) -> None:
        """Both display_name and agent_color can be set together."""
        sm = StateMachine()
        event = make_subagent_start_event(
            agent_id="agent-003",
            display_name="Bob",
            agent_color="#00FF00",
            squad_id="squad-1",
            squad_agent_id="bob",
        )
        sm.transition(event)

        assert "agent-003" in sm.agents
        agent = sm.agents["agent-003"]
        assert agent.name == "Bob"
        assert agent.color == "#00FF00"

    def test_no_squad_metadata_uses_defaults(self) -> None:
        """When no squad metadata is provided, agent still works with auto-generated defaults."""
        sm = StateMachine()
        event = make_subagent_start_event(agent_id="agent-004")
        sm.transition(event)

        assert "agent-004" in sm.agents
        agent = sm.agents["agent-004"]
        # Name should be a non-empty string (auto-generated)
        assert agent.name is not None
        assert len(agent.name) > 0
        # Color should be one of the default palette colors (non-empty)
        assert agent.color is not None
        assert len(agent.color) > 0

    def test_empty_display_name_uses_auto_name(self) -> None:
        """An empty display_name string does not override the auto-generated name."""
        sm = StateMachine()
        event = make_subagent_start_event(
            agent_id="agent-005",
            display_name="",  # empty string is falsy, should not override
        )
        sm.transition(event)

        assert "agent-005" in sm.agents
        agent = sm.agents["agent-005"]
        # Auto-generated name should still be present
        assert agent.name is not None
        assert len(agent.name) > 0
