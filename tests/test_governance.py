import pytest
from enact import govern, Policy, GovernanceRequest, GovernanceDecision

# --- Dummy Tool ---
class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance

# --- Dummy Policies ---
class AllowAll(Policy):
    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        return GovernanceDecision(allow=True, reason="Allowed")

class LimitWithdrawal(Policy):
    def __init__(self, limit=100):
        self.limit = limit

    def evaluate(self, request: GovernanceRequest) -> GovernanceDecision:
        if request.function_name == "withdraw":
            amount = request.arguments["args"][0]
            if amount > self.limit:
                return GovernanceDecision(allow=False, reason=f"Withdrawal limit of {self.limit} exceeded")
        return GovernanceDecision(allow=True, reason="Allowed")

# --- Tests ---

def test_governance_allow_all():
    # Setup
    real_account = BankAccount(1000)
    governed_account = govern(real_account, policy=AllowAll())
    
    # Action & Assert
    assert governed_account.deposit(100) == 1100
    assert governed_account.withdraw(50) == 1050

def test_governance_block_policy():
    # Setup
    real_account = BankAccount(1000)
    # Policy: max withdraw 100
    governed_account = govern(real_account, policy=LimitWithdrawal(limit=100))
    
    # Action: Allowed withdrawal
    assert governed_account.withdraw(50) == 950
    
    # Action: Blocked withdrawal
    with pytest.raises(PermissionError) as excinfo:
        governed_account.withdraw(150)
    
    assert "Withdrawal limit of 100 exceeded" in str(excinfo.value)

def test_governance_does_not_affect_allowed_methods():
    real_account = BankAccount(100)
    governed_account = govern(real_account, policy=LimitWithdrawal(limit=10))
    
    # deposit is not checked by LimitWithdrawal, should pass
    governed_account.deposit(500)
    assert real_account.balance == 600

def test_original_object_not_modified():
    real_account = BankAccount(100)
    policy = LimitWithdrawal(limit=10)
    governed_account = govern(real_account, policy)
    
    # The original object should function normally without governance if accessed directly
    # (Though in a real agent loop, they wouldn't have access to 'real_account')
    real_account.withdraw(50) 
    assert real_account.balance == 50
    
    # The governed one is the one that restricts
    with pytest.raises(PermissionError):
        governed_account.withdraw(50)
