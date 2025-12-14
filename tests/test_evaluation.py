import pytest
from enact import UsageTracker, AnomalyDetector

def test_usage_tracker_metrics():
    """Test metrics collection and calculation."""
    tracker = UsageTracker()
    
    # Record some data
    # 2 successes, 1 failure, 1 denial
    tracker.record_usage("a1", "t1", True, 100, True)
    tracker.record_usage("a1", "t1", True, 100, True)
    tracker.record_usage("a1", "t1", False, 100, True)
    tracker.record_usage("a1", "t1", False, 100, False) # Denied
    
    tool_metrics = tracker.get_tool_metrics("t1")
    agent_metrics = tracker.get_agent_metrics("a1")
    
    assert tool_metrics["call_count"] == 4
    assert tool_metrics["error_rate"] == 0.5  # 2 failures / 4 calls
    assert tool_metrics["avg_duration_ms"] == 100.0
    
    assert agent_metrics["request_count"] == 4
    assert agent_metrics["denial_rate"] == 0.25 # 1 denial / 4 requests

def test_anomaly_detection():
    """Test detection of high error rates."""
    tracker = UsageTracker()
    detector = AnomalyDetector(tracker)
    
    # Simulate high failure rate
    for _ in range(10):
        tracker.record_usage("a1", "broken_tool", False, 50, True)
        
    anomalies = detector.detect_anomalies()
    
    assert len(anomalies) > 0
    assert anomalies[0].type == "high_error_rate"
    assert anomalies[0].metric == "error_rate"

def test_anomaly_detection_denial():
    """Test detection of suspicious agent activity."""
    tracker = UsageTracker()
    detector = AnomalyDetector(tracker)
    
    # Simulate high denial rate
    for _ in range(10):
        tracker.record_usage("bad_agent", "t1", True, 50, False) # Denied
        
    anomalies = detector.detect_anomalies()
    
    # Filter for agent anomalies
    agent_anomalies = [a for a in anomalies if a.type == "suspicious_activity"]
    
    assert len(agent_anomalies) > 0
    assert agent_anomalies[0].description.startswith("Agent bad_agent")
