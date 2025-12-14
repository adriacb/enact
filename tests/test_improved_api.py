import pytest
from enact import (
    govern, governance_context,
    GovernanceEngine, RuleBasedPolicy, Rule
)

# Mock class to govern
class Calculator:
    def add(self, a, b):
        return a + b

def test_govern_as_function():
    """Test using govern() as a function with existing engine."""
    engine = GovernanceEngine()
    calc = Calculator()
    
    # Wrap it
    governed_calc = govern(calc, engine=engine)
    
    # Should work
    assert governed_calc.add(1, 2) == 3

def test_govern_as_decorator():
    """Test using @govern as a decorator on a function."""
    
    @govern(agent_id="decorator-agent")
    def my_func(x):
        return x * 2
        
    # my_func should now be a ToolProxy that is callable
    assert my_func(5) == 10

def test_governance_context_usage():
    """Test passing justification via context."""
    # Policy that requires justification
    # We need a validator for this, or check context in audit logs.
    # Let's inspect the request in a mock engine.
    
    captured_requests = []
    
    class MockEngine(GovernanceEngine):
        def evaluate(self, request):
            captured_requests.append(request)
            return super().evaluate(request)
            
    engine = MockEngine()
    calc = Calculator()
    governed_calc = govern(calc, engine=engine)
    
    with governance_context(justification="Official Business", correlation_id="cid-1"):
        governed_calc.add(5, 5)
        
    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.context["justification"] == "Official Business"
    assert req.correlation_id == "cid-1"

# TODO: Fix ToolProxy to support wrapping standalone functions and callable classes
