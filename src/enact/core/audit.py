from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Protocol, Any, Dict
import json
import os
from .domain import GovernanceRequest, GovernanceDecision

@dataclass
class AuditLog:
    """Represents a single audit entry."""
    timestamp: datetime
    agent_id: str
    tool: str
    function: str
    arguments: Dict[str, Any]
    allow: bool
    reason: str
    duration_ms: float

class Auditor(Protocol):
    """Protocol for audit loggers."""
    def log(self, entry: AuditLog) -> None:
        ...

class JsonLineAuditor:
    """
    Appends audit logs to a file in JSON Lines format.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath

    def log(self, entry: AuditLog) -> None:
        # Convert dataclass to dict
        data = asdict(entry)
        
        # Serialize datetime
        data['timestamp'] = entry.timestamp.isoformat()
        
        # Write to file
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')
