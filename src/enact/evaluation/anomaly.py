from typing import List
from dataclasses import dataclass
from .metrics import UsageTracker

@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    type: str
    severity: str  # LOW, MEDIUM, HIGH
    description: str
    metric: str
    value: float
    threshold: float

class AnomalyDetector:
    """
    Detects anomalies in usage patterns.
    Currently implements simple threshold-based detection.
    """
    
    def __init__(self, tracker: UsageTracker):
        self.tracker = tracker
        
        # Baselines (could be learned dynamically in future)
        self.max_error_rate = 0.1
        self.max_denial_rate = 0.2
        self.max_duration_ms = 5000.0
        
    def detect_anomalies(self) -> List[Anomaly]:
        """Scan current metrics for anomalies."""
        anomalies = []
        
        # Check Tool Anomalies
        for tool_name in self.tracker._tool_stats:
            metrics = self.tracker.get_tool_metrics(tool_name)
            
            # High Error Rate
            if metrics.get("error_rate", 0) > self.max_error_rate and metrics["call_count"] > 5:
                anomalies.append(Anomaly(
                    type="high_error_rate",
                    severity="HIGH",
                    description=f"Tool {tool_name} has high error rate",
                    metric="error_rate",
                    value=metrics["error_rate"],
                    threshold=self.max_error_rate
                ))
                
            # slow performance
            if metrics.get("avg_duration_ms", 0) > self.max_duration_ms:
                anomalies.append(Anomaly(
                    type="high_latency",
                    severity="MEDIUM",
                    description=f"Tool {tool_name} is slow",
                    metric="avg_duration_ms",
                    value=metrics["avg_duration_ms"],
                    threshold=self.max_duration_ms
                ))

        # Check Agent Anomalies
        for agent_id in self.tracker._agent_stats:
            metrics = self.tracker.get_agent_metrics(agent_id)
            
            # High Denial Rate (Suspicious)
            if metrics.get("denial_rate", 0) > self.max_denial_rate and metrics["request_count"] > 5:
                anomalies.append(Anomaly(
                    type="suspicious_activity",
                    severity="HIGH",
                    description=f"Agent {agent_id} has high denial rate",
                    metric="denial_rate",
                    value=metrics["denial_rate"],
                    threshold=self.max_denial_rate
                ))
                
        return anomalies
