from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime, timedelta

@dataclass
class QuotaConfig:
    """Configuration for action quotas."""
    max_actions: int
    window_hours: int = 24  # Rolling window in hours

class QuotaManager:
    """
    Manage action quotas per agent.
    
    Tracks total actions within a rolling time window and enforces limits.
    """
    
    def __init__(self, default_quota: Optional[QuotaConfig] = None):
        """
        Args:
            default_quota: Default quota for all agents
        """
        self.default_quota = default_quota or QuotaConfig(max_actions=1000, window_hours=24)
        
        # Per-agent quotas
        self.agent_quotas: Dict[str, QuotaConfig] = {}
        
        # Usage tracking: {agent_id: [(timestamp, tool_name), ...]}
        self.usage: Dict[str, list] = {}
    
    def set_quota(self, agent_id: str, quota: QuotaConfig):
        """Set custom quota for an agent."""
        self.agent_quotas[agent_id] = quota
    
    def _get_quota(self, agent_id: str) -> QuotaConfig:
        """Get quota config for agent."""
        return self.agent_quotas.get(agent_id, self.default_quota)
    
    def _clean_old_entries(self, agent_id: str, window_hours: int):
        """Remove entries outside the rolling window."""
        if agent_id not in self.usage:
            return
        
        cutoff = datetime.now() - timedelta(hours=window_hours)
        self.usage[agent_id] = [
            (ts, tool) for ts, tool in self.usage[agent_id]
            if ts > cutoff
        ]
    
    def check_quota(self, agent_id: str, tool_name: str) -> bool:
        """
        Check if agent is within quota.
        
        Args:
            agent_id: Agent making the request
            tool_name: Tool being accessed
            
        Returns:
            True if within quota, False if quota exceeded
        """
        quota = self._get_quota(agent_id)
        self._clean_old_entries(agent_id, quota.window_hours)
        
        current_usage = len(self.usage.get(agent_id, []))
        return current_usage < quota.max_actions
    
    def consume(self, agent_id: str, tool_name: str) -> bool:
        """
        Consume one action from quota.
        
        Returns:
            True if consumed successfully, False if quota exceeded
        """
        if not self.check_quota(agent_id, tool_name):
            return False
        
        if agent_id not in self.usage:
            self.usage[agent_id] = []
        
        self.usage[agent_id].append((datetime.now(), tool_name))
        return True
    
    def get_remaining(self, agent_id: str) -> int:
        """Get remaining actions for agent."""
        quota = self._get_quota(agent_id)
        self._clean_old_entries(agent_id, quota.window_hours)
        
        current_usage = len(self.usage.get(agent_id, []))
        return max(0, quota.max_actions - current_usage)
    
    def reset(self, agent_id: str):
        """Reset quota for agent."""
        if agent_id in self.usage:
            del self.usage[agent_id]
