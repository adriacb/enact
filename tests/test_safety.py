import pytest
import time
from datetime import datetime, timedelta
from enact.safety import RateLimiter, QuotaManager, QuotaConfig, DryRunProxy
from enact.reliability import CircuitBreaker, CircuitState, CircuitBreakerOpen, CircuitBreakerConfig

# Rate Limiter Tests
def test_rate_limiter_allows_within_limit():
    """Test that requests within limit are allowed."""
    limiter = RateLimiter(max_calls_per_minute=10)
    
    # First 10 calls should succeed
    for i in range(10):
        assert limiter.check_limit("agent1", "tool1") is True

def test_rate_limiter_blocks_over_limit():
    """Test that requests over limit are blocked."""
    limiter = RateLimiter(max_calls_per_minute=5, burst_size=5)
    
    # Consume all tokens
    for i in range(5):
        limiter.check_limit("agent1", "tool1")
    
    # Next call should be blocked
    assert limiter.check_limit("agent1", "tool1") is False

def test_rate_limiter_refills_tokens():
    """Test that tokens refill over time."""
    limiter = RateLimiter(max_calls_per_minute=60, burst_size=2)
    
    # Consume all tokens
    assert limiter.check_limit("agent1", "tool1") is True
    assert limiter.check_limit("agent1", "tool1") is True
    assert limiter.check_limit("agent1", "tool1") is False
    
    # Wait for refill (1 token per second at 60/min)
    time.sleep(1.1)
    
    # Should have one token now
    assert limiter.check_limit("agent1", "tool1") is True

def test_rate_limiter_per_agent_tool():
    """Test that limits are per agent-tool combination."""
    limiter = RateLimiter(max_calls_per_minute=2, burst_size=2)
    
    # agent1-tool1
    assert limiter.check_limit("agent1", "tool1") is True
    assert limiter.check_limit("agent1", "tool1") is True
    assert limiter.check_limit("agent1", "tool1") is False
    
    # agent1-tool2 should have separate limit
    assert limiter.check_limit("agent1", "tool2") is True
    
    # agent2-tool1 should have separate limit
    assert limiter.check_limit("agent2", "tool1") is True

# Quota Manager Tests
def test_quota_manager_allows_within_quota():
    """Test that actions within quota are allowed."""
    manager = QuotaManager(QuotaConfig(max_actions=10, window_hours=1))
    
    for i in range(10):
        assert manager.consume("agent1", "tool1") is True

def test_quota_manager_blocks_over_quota():
    """Test that actions over quota are blocked."""
    manager = QuotaManager(QuotaConfig(max_actions=5, window_hours=1))
    
    # Consume all quota
    for i in range(5):
        manager.consume("agent1", "tool1")
    
    # Next action should be blocked
    assert manager.consume("agent1", "tool1") is False

def test_quota_manager_get_remaining():
    """Test getting remaining quota."""
    manager = QuotaManager(QuotaConfig(max_actions=10, window_hours=1))
    
    assert manager.get_remaining("agent1") == 10
    
    manager.consume("agent1", "tool1")
    assert manager.get_remaining("agent1") == 9

# Circuit Breaker Tests
def test_circuit_breaker_closed_initially():
    """Test that circuit starts in closed state."""
    breaker = CircuitBreaker()
    assert breaker.get_state("tool1") == CircuitState.CLOSED
    assert breaker.is_open("tool1") is False

def test_circuit_breaker_opens_on_failures():
    """Test that circuit opens after threshold failures."""
    breaker = CircuitBreaker()
    
    # Record failures
    for i in range(5):
        breaker.record_failure("tool1")
    
    assert breaker.get_state("tool1") == CircuitState.OPEN
    assert breaker.is_open("tool1") is True

def test_circuit_breaker_resets_on_success():
    """Test that failures reset on success in closed state."""
    breaker = CircuitBreaker()
    
    # Record some failures
    breaker.record_failure("tool1")
    breaker.record_failure("tool1")
    
    # Success should reset
    breaker.record_success("tool1")
    
    # Should still be closed
    assert breaker.get_state("tool1") == CircuitState.CLOSED

def test_circuit_breaker_half_open_transition():
    """Test transition to half-open after timeout."""
    config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=1)
    breaker = CircuitBreaker(config)
    
    # Open the circuit
    breaker.record_failure("tool1")
    breaker.record_failure("tool1")
    assert breaker.get_state("tool1") == CircuitState.OPEN
    
    # Wait for timeout
    time.sleep(1.1)
    
    # Check should transition to half-open
    breaker.is_open("tool1")
    assert breaker.get_state("tool1") == CircuitState.HALF_OPEN

def test_circuit_breaker_closes_from_half_open():
    """Test that circuit closes after successes in half-open."""
    config = CircuitBreakerConfig(success_threshold=2, timeout_seconds=1)
    breaker = CircuitBreaker(config)
    
    # Open the circuit
    for i in range(5):
        breaker.record_failure("tool1")
    
    # Wait and transition to half-open
    time.sleep(1.1)
    breaker.is_open("tool1")
    
    # Record successes
    breaker.record_success("tool1")
    breaker.record_success("tool1")
    
    assert breaker.get_state("tool1") == CircuitState.CLOSED

# Dry Run Tests
def test_dry_run_simulates_execution():
    """Test that dry-run simulates without executing."""
    class TestTool:
        def dangerous_operation(self, data):
            raise Exception("This should not execute!")
    
    tool = TestTool()
    dry_run = DryRunProxy(tool, "test_tool")
    
    # Should not raise exception
    result = dry_run.dangerous_operation("test_data")
    
    assert result.tool_name == "test_tool"
    assert result.function_name == "dangerous_operation"
    assert "dangerous_operation" in result.would_execute

def test_dry_run_estimates_impact():
    """Test that dry-run estimates operation impact."""
    class TestTool:
        def delete_data(self): pass
        def read_data(self): pass
        def update_data(self): pass
    
    tool = TestTool()
    dry_run = DryRunProxy(tool, "test_tool")
    
    delete_result = dry_run.delete_data()
    assert "HIGH" in delete_result.estimated_impact
    
    read_result = dry_run.read_data()
    assert "LOW" in read_result.estimated_impact
    
    update_result = dry_run.update_data()
    assert "MEDIUM" in update_result.estimated_impact

def test_dry_run_tracks_executions():
    """Test that dry-run tracks all simulated executions."""
    class TestTool:
        def func1(self): pass
        def func2(self): pass
    
    tool = TestTool()
    dry_run = DryRunProxy(tool, "test_tool")
    
    dry_run.func1()
    dry_run.func2()
    
    executions = dry_run.get_executions()
    assert len(executions) == 2
    assert executions[0].function_name == "func1"
    assert executions[1].function_name == "func2"

# Resilience Tests
def test_retry_succeeds_on_second_attempt():
    """Test that retry succeeds after initial failure."""
    from enact.reliability import with_retry, RetryConfig
    
    attempts = []
    
    @with_retry(RetryConfig(max_attempts=3, initial_delay=0.1, jitter=False))
    def flaky_function():
        attempts.append(1)
        if len(attempts) < 2:
            raise ValueError("First attempt fails")
        return "success"
    
    result = flaky_function()
    assert result == "success"
    assert len(attempts) == 2

def test_retry_raises_after_max_attempts():
    """Test that retry raises after max attempts exceeded."""
    from enact.reliability import with_retry, RetryConfig, MaxRetriesExceeded
    
    @with_retry(RetryConfig(max_attempts=2, initial_delay=0.1))
    def always_fails():
        raise ValueError("Always fails")
    
    with pytest.raises(MaxRetriesExceeded):
        always_fails()

def test_reliable_tool_proxy():
    """Test ReliableToolProxy wraps tools with resilience."""
    from enact.reliability import ReliableToolProxy, RetryConfig
    
    class TestTool:
        def __init__(self):
            self.attempts = 0
        
        def flaky_method(self):
            self.attempts += 1
            if self.attempts < 2:
                raise ValueError("Flaky")
            return "success"
    
    tool = TestTool()
    reliable = ReliableToolProxy(
        tool,
        timeout_seconds=5,
        retry_config=RetryConfig(max_attempts=3, initial_delay=0.1)
    )
    
    result = reliable.flaky_method()
    assert result == "success"
    assert tool.attempts == 2
