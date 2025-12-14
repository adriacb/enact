from dataclasses import dataclass
from typing import Optional, Set
from datetime import datetime, time
from ..core.domain import Policy, GovernanceRequest, GovernanceDecision

@dataclass
class TimeWindow:
    """Defines a time window for access."""
    start_time: time
    end_time: time
    days_of_week: Optional[Set[int]] = None  # 0=Monday, 6=Sunday. None means all days.

class TemporalPolicy(Policy):
    """
    Policy that restricts access based on time windows.
    """
    
    def __init__(self, allowed_windows: list[TimeWindow], timezone=None):
        self.allowed_windows = allowed_windows
        self.timezone = timezone  # TODO: Implement timezone handling
        
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        now = datetime.now()
        current_time = now.time()
        current_day = now.weekday()
        
        for window in self.allowed_windows:
            # Check day
            if window.days_of_week and current_day not in window.days_of_week:
                continue
                
            # Check time
            if window.start_time <= current_time <= window.end_time:
                return GovernanceDecision(allow=True, reason="Within allowed time window")
                
        return GovernanceDecision(
            allow=False, 
            reason=f"Access denied: Outside allowed time windows. Current time: {current_time}, Day: {current_day}"
        )
