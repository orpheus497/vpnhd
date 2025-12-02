"""Event bus for pub/sub communication between components."""

import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Set

from ..utils.logging import get_logger
from .types import Event, EventType

logger = get_logger(__name__)


# Type alias for event handlers
EventHandler = Callable[[Event], None]


class EventBus:
    """Simple event bus for pub/sub communication.

    Allows components to communicate without tight coupling.
    Components can subscribe to event types and publish events.
    """

    _instance: Optional["EventBus"] = None
    _initialized: bool = False

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the event bus."""
        # Only initialize once
        if EventBus._initialized:
            return

        self.logger = logger
        self._subscribers: Dict[EventType, Set[EventHandler]] = defaultdict(set)
        self._async_subscribers: Dict[EventType, Set[Callable]] = defaultdict(set)
        self._event_history: List[Event] = []
        self._max_history = 1000  # Keep last 1000 events

        EventBus._initialized = True
        self.logger.info("Event bus initialized")

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function(event) -> None
        """
        self._subscribers[event_type].add(handler)
        self.logger.debug(f"Subscribed handler to {event_type.value}")

    def subscribe_async(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe to an event type with async handler.

        Args:
            event_type: Type of event to subscribe to
            handler: Async callback function(event) -> None
        """
        self._async_subscribers[event_type].add(handler)
        self.logger.debug(f"Subscribed async handler to {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            self.logger.debug(f"Unsubscribed handler from {event_type.value}")

    def unsubscribe_async(self, event_type: EventType, handler: Callable) -> None:
        """Unsubscribe async handler from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Async handler to remove
        """
        if handler in self._async_subscribers[event_type]:
            self._async_subscribers[event_type].remove(handler)
            self.logger.debug(f"Unsubscribed async handler from {event_type.value}")

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        self.logger.debug(
            f"Publishing event {event.event_type.value} from {event.source}"
        )

        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Notify synchronous subscribers
        for handler in self._subscribers[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                self.logger.exception(
                    f"Error in event handler for {event.event_type.value}: {e}"
                )

        # Notify async subscribers
        for handler in self._async_subscribers[event.event_type]:
            try:
                asyncio.create_task(handler(event))
            except Exception as e:
                self.logger.exception(
                    f"Error in async event handler for {event.event_type.value}: {e}"
                )

    def get_subscribers_count(self, event_type: EventType) -> int:
        """Get number of subscribers for an event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of subscribers (sync + async)
        """
        return len(self._subscribers[event_type]) + len(
            self._async_subscribers[event_type]
        )

    def get_event_history(
        self, event_type: Optional[EventType] = None, limit: int = 100
    ) -> List[Event]:
        """Get recent event history.

        Args:
            event_type: Filter by event type (None for all)
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        if event_type:
            events = [e for e in self._event_history if e.event_type == event_type]
        else:
            events = self._event_history

        return events[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        self.logger.debug("Event history cleared")

    def reset(self) -> None:
        """Reset the event bus (mainly for testing)."""
        self._subscribers.clear()
        self._async_subscribers.clear()
        self._event_history.clear()
        self.logger.info("Event bus reset")


# Global event bus instance
event_bus = EventBus()
