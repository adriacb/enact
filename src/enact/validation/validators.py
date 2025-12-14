from typing import Dict, Any, Optional, Set
from enact.core.intent import IntentValidator, ToolIntent, ValidationResult

class JustificationValidator(IntentValidator):
    """
    Validates that a proper justification is provided for tool usage.
    """
    
    def __init__(
        self,
        min_length: int = 10,
        required_keywords: Optional[Dict[str, Set[str]]] = None
    ):
        """
        Args:
            min_length: Minimum length of justification string
            required_keywords: Map of tool_name -> set of keywords required in justification
        """
        self.min_length = min_length
        self.required_keywords = required_keywords or {}
        
    def validate(self, intent: ToolIntent) -> ValidationResult:
        # Check basic existence and length
        if not intent.justification:
            return ValidationResult(False, "Missing justification")
            
        if len(intent.justification.strip()) < self.min_length:
            return ValidationResult(
                False, 
                f"Justification too short (min {self.min_length} chars)"
            )
            
        # Check tool-specific keywords if configured
        if intent.tool_name in self.required_keywords:
            keywords = self.required_keywords[intent.tool_name]
            justification_lower = intent.justification.lower()
            
            # Check if ANY of the required keywords are present
            any_present = any(
                kw.lower() in justification_lower 
                for kw in keywords
            )
            
            if not any_present:
                return ValidationResult(
                    False,
                    f"Justification for '{intent.tool_name}' must contain at least one of: {keywords}"
                )
                
        return ValidationResult(True)

class SchemaValidator(IntentValidator):
    """
    Validates tool arguments against a schema (if available).
    
    Note: Full JSON schema validation would typically happen at the MCP/Tool level,
    but this provides a governance-layer check.
    """
    
    def __init__(self, schemas: Dict[str, Dict[str, Any]]):
        """
        Args:
            schemas: Map of tool_name -> JSON schema
        """
        self.schemas = schemas
        
    def validate(self, intent: ToolIntent) -> ValidationResult:
        if intent.tool_name not in self.schemas:
            # No schema defined, pass with warning
            return ValidationResult(
                True, 
                warnings=[f"No schema defined for tool '{intent.tool_name}'"]
            )
            
        # TODO: Implement full JSON schema validation here if needed
        # For now, we'll do a basic check that required args exist
        schema = self.schemas[intent.tool_name]
        required = schema.get("required", [])
        
        missing = [arg for arg in required if arg not in intent.arguments]
        
        if missing:
            return ValidationResult(False, f"Missing required arguments: {missing}")
            
        return ValidationResult(True)
