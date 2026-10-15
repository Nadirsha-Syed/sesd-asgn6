from abc import ABC, abstractmethod
from typing import List


# ============================================================
# 1. OBSERVER PATTERN: NOTIFICATION SYSTEM
# OO Concepts: Polymorphism & Loose Coupling
# ============================================================

class TransactionObserver(ABC):
    """Observer Interface declaring the contract for alert services."""
    @abstractmethod
    def update(self, account_id: str, tx_type: str, amount: float, current_balance: float) -> None:
        pass


class SMSAlertService(TransactionObserver):
    """Concrete Observer: Sends text alerts to registered mobile numbers."""
    def __init__(self, phone_number: str):
        self._phone_number = phone_number

    def update(self, account_id: str, tx_type: str, amount: float, current_balance: float) -> None:
        print(f"[SMS to {self._phone_number}] Alert: {tx_type} of ₹{amount:.2f} on Account {account_id}. "
              f"Available Balance: ₹{current_balance:.2f}")


class EmailAlertService(TransactionObserver):
    """Concrete Observer: Dispatches formatted statements via email."""
    def __init__(self, email: str):
        self._email = email

    def update(self, account_id: str, tx_type: str, amount: float, current_balance: float) -> None:
        print(f"[EMAIL to {self._email}] Statement: Transaction '{tx_type}' of ₹{amount:.2f} processed. "
              f"Current Balance: ₹{current_balance:.2f}")


# ============================================================
# 2. STRATEGY PATTERN: INTEREST CALCULATION ENGINE
# OO Concepts: Composition & Polymorphism
# ============================================================

class InterestCalculationStrategy(ABC):
    """Strategy Interface defining dynamic interest calculation."""
    @abstractmethod
    def calculate_interest(self, balance: float, tenure_years: int) -> float:
        pass


class SavingsInterestStrategy(InterestCalculationStrategy):
    """Concrete Strategy: Computes 4.0% p.a. standard savings rate."""
    ANNUAL_RATE = 0.04

    def calculate_interest(self, balance: float, tenure_years: int) -> float:
        return balance * self.ANNUAL_RATE * tenure_years


class FixedDepositInterestStrategy(InterestCalculationStrategy):
    """Concrete Strategy: Computes compound interest at 7.5% p.a."""
    FD_RATE = 0.075

    def calculate_interest(self, balance: float, tenure_years: int) -> float:
        return balance * ((1 + self.FD_RATE) ** tenure_years) - balance


class CurrentAccountInterestStrategy(InterestCalculationStrategy):
    """Concrete Strategy: Zero interest for commercial current accounts."""
    def calculate_interest(self, balance: float, tenure_years: int) -> float:
        return 0.0


# ============================================================
# RECEIVER & SUBJECT: BANK ACCOUNT
# OO Concepts: Encapsulation & Abstraction
# ============================================================

class BankAccount:
    """Receiver for Commands & Subject for Observers."""
    def __init__(self, account_number: str, initial_balance: float, strategy: InterestCalculationStrategy):
        self._account_number = account_number
        self._balance = initial_balance
        self._strategy = strategy
        self._observers: List[TransactionObserver] = []

    # --- Observer Management ---
    def attach_observer(self, observer: TransactionObserver) -> None:
        self._observers.append(observer)

    def detach_observer(self, observer: TransactionObserver) -> None:
        self._observers.remove(observer)

    def _notify(self, tx_type: str, amount: float) -> None:
        for observer in self._observers:
            observer.update(self._account_number, tx_type, amount, self._balance)

    # --- Receiver Actions (Core Banking Logic) ---
    def credit(self, amount: float) -> None:
        self._balance += amount
        self._notify("DEPOSIT", amount)

    def debit(self, amount: float) -> bool:
        if amount > self._balance:
            print(f"[REJECTED] Account {self._account_number}: Insufficient funds for withdrawal of ₹{amount:.2f}")
            return False
        self._balance -= amount
        self._notify("WITHDRAWAL", amount)
        return True

    # --- Strategy Delegation ---
    def compute_and_display_interest(self, tenure_years: int) -> None:
        interest = self._strategy.calculate_interest(self._balance, tenure_years)
        print(f"[Account {self._account_number}] Projected interest for {tenure_years} year(s): ₹{interest:.2f}")

    def set_interest_strategy(self, strategy: InterestCalculationStrategy) -> None:
        self._strategy = strategy

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def balance(self) -> float:
        return self._balance


# ============================================================
# 3. COMMAND PATTERN: TRANSACTIONS & UNDO SUPPORT
# OO Concepts: Encapsulation (Request as Object) & Decoupling
# ============================================================

class TransactionCommand(ABC):
    """Command Interface declaring execution and rollback contracts."""
    @abstractmethod
    def execute(self) -> bool:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass


class DepositCommand(TransactionCommand):
    """Concrete Command for processing deposits."""
    def __init__(self, account: BankAccount, amount: float):
        self._account = account
        self._amount = amount
        self._executed = False

    def execute(self) -> bool:
        if self._amount <= 0:
            return False
        self._account.credit(self._amount)
        self._executed = True
        return True

    def undo(self) -> None:
        if self._executed:
            print(f"\n[ROLLBACK] Reversing deposit of ₹{self._amount:.2f} on Account {self._account.account_number}")
            self._account.debit(self._amount)


class WithdrawCommand(TransactionCommand):
    """Concrete Command for processing withdrawals."""
    def __init__(self, account: BankAccount, amount: float):
        self._account = account
        self._amount = amount
        self._executed = False

    def execute(self) -> bool:
        if self._amount <= 0:
            return False
        self._executed = self._account.debit(self._amount)
        return self._executed

    def undo(self) -> None:
        if self._executed:
            print(f"\n[ROLLBACK] Reversing withdrawal of ₹{self._amount:.2f} on Account {self._account.account_number}")
            self._account.credit(self._amount)


class TransactionManager:
    """Invoker: Triggers commands and maintains execution history for undo."""
    def __init__(self):
        self._history: List[TransactionCommand] = []

    def execute_transaction(self, command: TransactionCommand) -> None:
        if command.execute():
            self._history.append(command)

    def undo_last_transaction(self) -> None:
        if self._history:
            last_command = self._history.pop()
            last_command.undo()
        else:
            print("[INFO] No transactions remaining to undo.")


# ============================================================
# EXECUTION / DRIVER SCRIPT
# ============================================================

if __name__ == "__main__":
    # 1. Instantiate Account with a Default Strategy (Savings)
    account = BankAccount("SB-SRU-2026", 5000.0, SavingsInterestStrategy())

    # 2. Attach Observers (SMS & Email alerts)
    account.attach_observer(SMSAlertService("+91-9876543210"))
    account.attach_observer(EmailAlertService("student@sru.edu.in"))

    # 3. Invoker setup
    manager = TransactionManager()

    print("--- 1. Testing Commands (Deposit & Withdraw) ---")
    manager.execute_transaction(DepositCommand(account, 2500.0))
    manager.execute_transaction(WithdrawCommand(account, 1200.0))

    print("\n--- 2. Testing Rollback / Undo Functionality ---")
    # Rollback last transaction (Withdrawal of ₹1200)
    manager.undo_last_transaction()

    print("\n--- 3. Testing Strategy Pattern (Interest Calculations) ---")
    account.compute_and_display_interest(tenure_years=3)

    print("\nSwitching to Fixed Deposit Strategy at runtime:")
    account.set_interest_strategy(FixedDepositInterestStrategy())
    account.compute_and_display_interest(tenure_years=3)