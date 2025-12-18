"""
DOM Event model for type hints and utilities.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class DOMEventData:
    """Data class representing a DOM event."""
    event_type: str
    timestamp: float
    selector: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    viewport: Optional[Dict[str, float]] = None
    target: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "DOMEventData":
        """Create DOMEventData from dictionary."""
        return cls(
            event_type=data.get("type", "unknown"),
            timestamp=data.get("timestamp", 0),
            selector=data.get("selector"),
            coordinates=data.get("coordinates"),
            viewport=data.get("viewport"),
            target=data.get("target"),
        )
    
    def to_instruction_context(self) -> str:
        """Convert event to context string for LLM prompt."""
        context_parts = [f"[{self.event_type.upper()}]"]
        
        if self.selector:
            context_parts.append(f"Element: {self.selector}")
        
        if self.target:
            if self.target.get("text"):
                context_parts.append(f"Text: {self.target['text'][:50]}")
            if self.target.get("tagName"):
                context_parts.append(f"Tag: {self.target['tagName']}")
        
        return " | ".join(context_parts)


def format_events_for_prompt(events: list) -> str:
    """Format DOM events as context for LLM prompt."""
    if not events:
        return "No DOM events recorded."
    
    formatted = []
    for i, event in enumerate(events[:20], 1):  # Limit to 20 events
        if isinstance(event, dict):
            event_data = DOMEventData.from_dict(event)
        else:
            event_data = DOMEventData(
                event_type=getattr(event, "type", "unknown"),
                timestamp=getattr(event, "timestamp", 0),
                selector=getattr(event, "selector", None),
                target=getattr(event, "target", None),
            )
        formatted.append(f"{i}. {event_data.to_instruction_context()}")
    
    return "\n".join(formatted)
