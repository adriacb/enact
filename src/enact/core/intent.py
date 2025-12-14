from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Protocol, List
from datetime import datetime
import uuid

@dataclass
class ToolIntent:
    """
    Represents an agent's intent to execute a tool action.
    
    Contains not just the what (tool/function/args) but also the why (justification)
    and confidence level, separating reasoning from execution.
    """
    agent_id: str
    tool_name: str
    function_name: str
    arguments: Dict[str, Any]
    justification: str
    confidence: float = 1.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Result of an intent validation check."""
    valid: bool
    reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class IntentValidator(Protocol):
    """Protocol for intent validators."""
    
    def validate(self, intent: ToolIntent) -> ValidationResult:
        """
        Validate the intent before execution.
        
        Args:
            intent: The tool intent to validate
            
        Returns:
            ValidationResult indicating validity
        """
        ...

class ValidationPipeline:
    """
    Chain of validators that all must pass for an intent to be valid.
    """
    
    def __init__(self, validators: Optional[List[IntentValidator]] = None):
        self.validators = validators or []
        
    def add_validator(self, validator: IntentValidator):
        """Add a validator to the pipeline."""
        self.validators.append(validator)
        
    def validate(self, intent: ToolIntent) -> ValidationResult:
        """
        Run all validators in sequence.
        
        Returns:
            Success if all pass, failure on first error.
        """
        all_warnings = []
        
        for validator in self.validators:
            result = validator.validate(intent)
            all_warnings.extend(result.warnings)
            
            if not result.valid:
                return ValidationResult(
                    valid=False,
                    reason=f"{validator.__class__.__name__}: {result.reason}",
                    warnings=all_warnings,
                    metadata=result.metadata
                )
        
        return ValidationResult(
            valid=True,
            warnings=all_warnings
        )
