import yaml
import json
import os

from ..core.policies import Rule, RuleBasedPolicy
from ..core.domain import Policy

class PolicyLoader:
    """
    Loads policies from configuration files.
    """
    
    @staticmethod
    def load(path: str) -> Policy:
        """
        Loads a policy from a YAML or JSON file.
        
        Args:
            path: Absolute path to the config file.
            
        Returns:
            A RuleBasedPolicy instance configured with the rules from the file.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Policy file not found: {path}")
            
        _, ext = os.path.splitext(path)
        
        with open(path, 'r', encoding='utf-8') as f:
            if ext.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif ext.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported policy format: {ext}")
                
        return PolicyLoader._parse_data(data)

    @staticmethod
    def _parse_data(data: dict) -> RuleBasedPolicy:
        """Parses the raw dictionary into a RuleBasedPolicy."""
        # Validation checks could go here
        
        rules_data = data.get("rules", [])
        rules = []
        
        for r in rules_data:
            rules.append(Rule(
                tool=r.get("tool", "*"),
                function=r.get("function", "*"),
                action=r.get("action", "deny"),
                reason=r.get("reason", "No reason provided"),
                agent_id=r.get("agent_id", "*")
            ))
            
        default_allow = data.get("default_allow", False)
        
        return RuleBasedPolicy(rules=rules, default_allow=default_allow)
