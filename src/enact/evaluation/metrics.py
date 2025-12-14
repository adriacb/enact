from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

@dataclass
class ToolStats:
    """Statistics for a specific tool."""
    call_count: int = 0
    failure_count: int = 0
    total_duration_ms: float = 0.0
    last_used: Optional[datetime] = None

@dataclass
class AgentStats:
    """Statistics for a specific agent."""
    request_count: int = 0
    denials: int = 0
    tool_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

class UsageTracker:
    """
    Tracks usage statistics for agents and tools.
    """
    
    def __init__(self):
        self._tool_stats: Dict[str, ToolStats] = defaultdict(ToolStats)
        self._agent_stats: Dict[str, AgentStats] = defaultdict(AgentStats)
        self._durations: Dict[str, List[float]] = defaultdict(list)
        
    def record_usage(
        self,
        agent_id: str,
        tool_name: str,
        success: bool,
        duration_ms: float,
        allowed: bool
    ):
        """Record a single usage event."""
        # Update tool stats
        tool_stats = self._tool_stats[tool_name]
        tool_stats.call_count += 1
        if not success:
            tool_stats.failure_count += 1
        tool_stats.total_duration_ms += duration_ms
        tool_stats.last_used = datetime.now()
        
        # Keep duration history for analysis (limit size in prod)
        self._durations[tool_name].append(duration_ms)
        
        # Update agent stats
        agent_stats = self._agent_stats[agent_id]
        agent_stats.request_count += 1
        if not allowed:
            agent_stats.denials += 1
        agent_stats.tool_usage[tool_name] += 1
        
    def get_tool_metrics(self, tool_name: str) -> Dict[str, float]:
        """Get performance metrics for a tool."""
        if tool_name not in self._tool_stats:
            return {}
            
        stats = self._tool_stats[tool_name]
        durations = self._durations[tool_name]
        
        avg_duration = stats.total_duration_ms / stats.call_count if stats.call_count > 0 else 0
        error_rate = stats.failure_count / stats.call_count if stats.call_count > 0 else 0
        
        return {
            "call_count": stats.call_count,
            "error_rate": error_rate,
            "avg_duration_ms": avg_duration,
            "p95_duration_ms": self._calculate_percentile(durations, 95)
        }
    
    def get_agent_metrics(self, agent_id: str) -> Dict[str, float]:
        """Get behavior metrics for an agent."""
        if agent_id not in self._agent_stats:
            return {}
            
        stats = self._agent_stats[agent_id]
        denial_rate = stats.denials / stats.request_count if stats.request_count > 0 else 0
        
        return {
            "request_count": stats.request_count,
            "denial_rate": denial_rate,
            "unique_tools_used": len(stats.tool_usage)
        }

    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        if not data:
            return 0.0
        
        # Simple nearest-rank method
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        # Clamp index
        index = min(max(index, 0), len(sorted_data) - 1)
        
        return sorted_data[index]
