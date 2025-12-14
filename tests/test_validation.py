import pytest
from enact.core.intent import ToolIntent, ValidationPipeline, ValidationResult
from enact.validation import JustificationValidator, SchemaValidator
from enact import GovernanceEngine, GovernanceRequest
from enact.core.domain import AllowAllPolicy

# Intent Tests
def test_tool_intent_creation():
    """Test creating a ToolIntent."""
    intent = ToolIntent(
        agent_id="agent1",
        tool_name="tool",
        function_name="func",
        arguments={},
        justification="reason"
    )
    assert intent.agent_id == "agent1"
    assert intent.confidence == 1.0  # default

# Validator Tests
def test_justification_validator_success():
    """Test justification checks pass."""
    validator = JustificationValidator(min_length=5)
    intent = ToolIntent(
        agent_id="a", tool_name="t", function_name="f", arguments={},
        justification="This is long enough"
    )
    result = validator.validate(intent)
    assert result.valid is True

def test_justification_validator_failure_missing():
    """Test missing justification fails."""
    validator = JustificationValidator()
    intent = ToolIntent(
        agent_id="a", tool_name="t", function_name="f", arguments={},
        justification=None
    )
    result = validator.validate(intent)
    assert result.valid is False
    assert "Missing" in result.reason

def test_justification_validator_failure_short():
    """Test short justification fails."""
    validator = JustificationValidator(min_length=10)
    intent = ToolIntent(
        agent_id="a", tool_name="t", function_name="f", arguments={},
        justification="short"
    )
    result = validator.validate(intent)
    assert result.valid is False
    assert "too short" in result.reason

def test_justification_validator_keywords():
    """Test keyword requirements."""
    validator = JustificationValidator(
        required_keywords={"database": {"backup", "cleanup"}}
    )
    
    # Missing required keyword
    intent = ToolIntent(
        agent_id="a", tool_name="database", function_name="f", arguments={},
        justification="I am doing safe things"
    )
    result = validator.validate(intent)
    assert result.valid is False
    assert "must contain at least one of" in result.reason
    
    # Containing required keyword
    intent.justification = "Performing database backup"
    result = validator.validate(intent)
    assert result.valid is True

def test_schema_validator():
    """Test schema validation (basic required args check)."""
    schemas = {
        "calculator": {
            "required": ["x", "y"]
        }
    }
    validator = SchemaValidator(schemas)
    
    # Pass
    intent = ToolIntent(
        agent_id="a", tool_name="calculator", function_name="add",
        arguments={"x": 1, "y": 2}, justification="math"
    )
    assert validator.validate(intent).valid is True
    
    # Fail
    intent.arguments = {"x": 1}
    result = validator.validate(intent)
    assert result.valid is False
    assert "Missing required" in result.reason

# Integration Tests
def test_governance_engine_with_validation_success():
    """Test engine allows valid intent."""
    pipeline = ValidationPipeline()
    pipeline.add_validator(JustificationValidator(min_length=3))
    
    engine = GovernanceEngine(
        policy=AllowAllPolicy(),
        validator=pipeline
    )
    
    request = GovernanceRequest(
        agent_id="a", tool_name="t", function_name="f", arguments={},
        context={"justification": "Valid Reason"}
    )
    
    decision = engine.evaluate(request)
    assert decision.allow is True

def test_governance_engine_with_validation_failure():
    """Test engine blocks invalid intent."""
    pipeline = ValidationPipeline()
    pipeline.add_validator(JustificationValidator(min_length=100)) # strict
    
    engine = GovernanceEngine(
        policy=AllowAllPolicy(),
        validator=pipeline
    )
    
    request = GovernanceRequest(
        agent_id="a", tool_name="t", function_name="f", arguments={},
        context={"justification": "Too short"}
    )
    
    decision = engine.evaluate(request)
    assert decision.allow is False
    assert "Validation failed" in decision.reason
