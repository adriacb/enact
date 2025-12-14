from datetime import datetime
from typing import Optional, Callable
import threading

class KillSwitch:
    """
    Emergency stop mechanism for agent operations.
    
    Provides a global kill-switch that can immediately halt all
    agent actions. Thread-safe singleton implementation.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern - only one kill-switch instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize kill-switch (only once)."""
        if self._initialized:
            return
        
        self._enabled = False
        self._activated_at: Optional[datetime] = None
        self._activated_by: Optional[str] = None
        self._reason: Optional[str] = None
        self._callback: Optional[Callable] = None
        self._initialized = True
    
    def activate(
        self,
        activated_by: str,
        reason: str,
        callback: Optional[Callable] = None
    ):
        """
        Activate the kill-switch to stop all operations.
        
        Args:
            activated_by: ID of person/system activating
            reason: Reason for activation
            callback: Optional callback to trigger on activation
        """
        with self._lock:
            if not self._enabled:
                self._enabled = True
                self._activated_at = datetime.now()
                self._activated_by = activated_by
                self._reason = reason
                
                if callback:
                    callback(self)
    
    def deactivate(self, deactivated_by: str):
        """
        Deactivate the kill-switch to resume operations.
        
        Args:
            deactivated_by: ID of person deactivating
        """
        with self._lock:
            self._enabled = False
            # Keep history for audit
    
    def is_active(self) -> bool:
        """Check if kill-switch is currently active."""
        return self._enabled
    
    def check(self) -> bool:
        """
        Check if operations should proceed.
        
        Returns:
            True if operations allowed, False if kill-switch active
        """
        return not self._enabled
    
    def get_status(self) -> dict:
        """Get current kill-switch status."""
        return {
            "active": self._enabled,
            "activated_at": self._activated_at.isoformat() if self._activated_at else None,
            "activated_by": self._activated_by,
            "reason": self._reason
        }
    
    def reset(self):
        """Reset kill-switch state (for testing)."""
        with self._lock:
            self._enabled = False
            self._activated_at = None
            self._activated_by = None
            self._reason = None

class KillSwitchActive(Exception):
    """Exception raised when kill-switch is active."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Kill-switch active: {reason}")
