# Intent Validation Guide

This guide covers the **Intent Validation** framework, which separates *reasoning* from *execution* by validating the "why" and "what" of a tool call before it reaches the policy engine.

## Overview

Traditional access control checks *who* (agent) is accessing *what* (tool). Intent validation adds:
- **Justification**: *Why* does the agent need this tool?
- **Confidence**: How certain is the agent?
- **Schema Validation**: Are the arguments correct?

## Basic Usage

### 1. Configure Validators

```python
from enact import ValidationPipeline, JustificationValidator, SchemaValidator

pipeline = ValidationPipeline()

# Require justification with at least 10 chars
pipeline.add_validator(JustificationValidator(min_length=10))

# Require specific keywords for sensitive tools
pipeline.add_validator(JustificationValidator(
    required_keywords={
        "database": {"backup", "cleanup", "restore"},
        "payment": {"refund", "charge"}
    }
))
```

### 2. Integrate with GovernanceEngine

```python
from enact import GovernanceEngine, AllowAllPolicy

engine = GovernanceEngine(
    policy=AllowAllPolicy(),
    validator=pipeline
)
```

### 3. Provide Context in Requests

When making a `GovernanceRequest`, pass `justification` and `confidence` in the context:

```python
request = GovernanceRequest(
    agent_id="agent-1",
    tool_name="database",
    function_name="delete_all",
    arguments={},
    context={
        "justification": "Cleaning up test environment post-CI run",
        "confidence": 0.95
    }
)

decision = engine.evaluate(request)
```

## Available Validators

### JustificationValidator

Ensures the agent provides a valid reason for the action.

```python
JustificationValidator(
    min_length=10,
    required_keywords={"tool_name": {"required_keyword"}}
)
```

- **min_length**: Minimum length of justification string.
- **required_keywords**: Map of tool names to sets of keywords. At least one keyword must be present if the tool is listed.

### SchemaValidator

Validates arguments against a JSON schema (or basic structure).

```python
SchemaValidator(schemas={
    "calculator": {
        "required": ["x", "y"]
    }
})
```

## Custom Validators

Implement the `IntentValidator` protocol to create custom checks:

```python
from enact import IntentValidator, ToolIntent, ValidationResult

class BusinessHoursValidator(IntentValidator):
    def validate(self, intent: ToolIntent) -> ValidationResult:
        import datetime
        now = datetime.datetime.now()
        if 9 <= now.hour < 17:
            return ValidationResult(True)
        return ValidationResult(False, "Outside business hours")
```

## Best Practices

1. **Always Require Justification**: Force agents to "think" before acting.
2. **Context-Aware Validation**: Use custom validators to check business logic state.
3. **Audit Validation Failures**: Validation failures are audited just like policy denials, helping you debug agent reasoning.
