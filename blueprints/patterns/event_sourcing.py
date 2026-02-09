"""
Event Sourcing Pattern
Expert architecture pattern - store state as events.

Instead of: UPDATE account SET balance = 100
Event source: AccountCredited(50), AccountDebited(25), AccountCredited(75)

Benefits:
- Complete audit trail
- Time travel (replay to any point)
- Event-driven architecture
- No data loss from updates
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod
import json


# ============================================================================
# EVENTS
# ============================================================================

@dataclass
class Event:
    """Base class for all events"""
    event_id: str
    aggregate_id: str
    timestamp: datetime
    version: int
    
    def to_dict(self) -> dict:
        return {
            'event_type': self.__class__.__name__,
            'event_id': self.event_id,
            'aggregate_id': self.aggregate_id,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version,
            'data': self._get_data()
        }
    
    def _get_data(self) -> dict:
        return {}


@dataclass
class AccountCreated(Event):
    owner_name: str
    initial_balance: float = 0.0
    
    def _get_data(self) -> dict:
        return {'owner_name': self.owner_name, 'initial_balance': self.initial_balance}


@dataclass  
class MoneyDeposited(Event):
    amount: float
    description: str = ""
    
    def _get_data(self) -> dict:
        return {'amount': self.amount, 'description': self.description}


@dataclass
class MoneyWithdrawn(Event):
    amount: float
    description: str = ""
    
    def _get_data(self) -> dict:
        return {'amount': self.amount, 'description': self.description}


@dataclass
class AccountClosed(Event):
    reason: str = ""
    
    def _get_data(self) -> dict:
        return {'reason': self.reason}


# ============================================================================
# EVENT STORE
# ============================================================================

class EventStore:
    """
    Append-only store for events.
    In production: use EventStoreDB, Kafka, or PostgreSQL with event table.
    """
    
    def __init__(self):
        self._events: List[Event] = []
        self._event_counter = 0
    
    def append(self, event: Event):
        """Append event to store"""
        self._events.append(event)
        print(f"  [EventStore] Stored: {event.__class__.__name__}")
    
    def get_events(self, aggregate_id: str, 
                   from_version: int = 0) -> List[Event]:
        """Get all events for an aggregate"""
        return [
            e for e in self._events
            if e.aggregate_id == aggregate_id and e.version >= from_version
        ]
    
    def get_all_events(self) -> List[Event]:
        """Get all events (for projections)"""
        return self._events.copy()


# ============================================================================
# AGGREGATE (Domain Model)
# ============================================================================

class BankAccount:
    """
    Aggregate that builds state from events.
    Never stores current state - always replays events.
    """
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.owner_name: str = ""
        self.balance: float = 0.0
        self.is_closed: bool = False
        self._version: int = 0
        self._pending_events: List[Event] = []
    
    def apply(self, event: Event):
        """Apply event to update state"""
        if isinstance(event, AccountCreated):
            self.owner_name = event.owner_name
            self.balance = event.initial_balance
        elif isinstance(event, MoneyDeposited):
            self.balance += event.amount
        elif isinstance(event, MoneyWithdrawn):
            self.balance -= event.amount
        elif isinstance(event, AccountClosed):
            self.is_closed = True
        
        self._version = event.version
    
    def _raise_event(self, event_class, **kwargs):
        """Create and apply a new event"""
        import uuid
        event = event_class(
            event_id=str(uuid.uuid4())[:8],
            aggregate_id=self.account_id,
            timestamp=datetime.now(),
            version=self._version + 1,
            **kwargs
        )
        self.apply(event)
        self._pending_events.append(event)
        return event
    
    # Commands (business operations)
    
    def create(self, owner_name: str, initial_balance: float = 0.0):
        """Create a new account"""
        if self._version > 0:
            raise ValueError("Account already exists")
        self._raise_event(AccountCreated, 
                         owner_name=owner_name, 
                         initial_balance=initial_balance)
    
    def deposit(self, amount: float, description: str = ""):
        """Deposit money"""
        if self.is_closed:
            raise ValueError("Account is closed")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self._raise_event(MoneyDeposited, amount=amount, description=description)
    
    def withdraw(self, amount: float, description: str = ""):
        """Withdraw money"""
        if self.is_closed:
            raise ValueError("Account is closed")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self._raise_event(MoneyWithdrawn, amount=amount, description=description)
    
    def close(self, reason: str = ""):
        """Close the account"""
        if self.is_closed:
            raise ValueError("Already closed")
        if self.balance != 0:
            raise ValueError("Balance must be zero to close")
        self._raise_event(AccountClosed, reason=reason)
    
    def get_pending_events(self) -> List[Event]:
        """Get events not yet persisted"""
        events = self._pending_events
        self._pending_events = []
        return events
    
    @classmethod
    def load(cls, account_id: str, events: List[Event]) -> 'BankAccount':
        """Reconstruct account from event history"""
        account = cls(account_id)
        for event in events:
            account.apply(event)
        return account


# ============================================================================
# PROJECTION (Read Model)
# ============================================================================

class AccountBalanceProjection:
    """
    Read model built from events.
    Optimized for queries, can be rebuilt anytime.
    """
    
    def __init__(self):
        self.balances: Dict[str, float] = {}
        self.owners: Dict[str, str] = {}
    
    def apply(self, event: Event):
        """Update projection from event"""
        if isinstance(event, AccountCreated):
            self.balances[event.aggregate_id] = event.initial_balance
            self.owners[event.aggregate_id] = event.owner_name
        elif isinstance(event, MoneyDeposited):
            self.balances[event.aggregate_id] += event.amount
        elif isinstance(event, MoneyWithdrawn):
            self.balances[event.aggregate_id] -= event.amount
    
    def get_balance(self, account_id: str) -> Optional[float]:
        return self.balances.get(account_id)
    
    def get_total_deposits(self) -> float:
        return sum(self.balances.values())


def demo():
    print("=== Event Sourcing Demo ===\n")
    
    store = EventStore()
    
    # Create and use an account
    print("Creating account and performing operations:")
    account = BankAccount("ACC-001")
    account.create("Alice", 100.0)
    account.deposit(50.0, "Birthday gift")
    account.withdraw(30.0, "Coffee")
    account.deposit(200.0, "Salary")
    
    # Persist events
    for event in account.get_pending_events():
        store.append(event)
    
    print(f"\nCurrent balance: ${account.balance:.2f}")
    
    # Time travel: replay to specific point
    print("\n--- Time Travel: State after each event ---")
    replay = BankAccount("ACC-001")
    for event in store.get_events("ACC-001"):
        replay.apply(event)
        print(f"  After {event.__class__.__name__}: ${replay.balance:.2f}")
    
    # Build projection
    print("\n--- Building Read Model ---")
    projection = AccountBalanceProjection()
    for event in store.get_all_events():
        projection.apply(event)
    print(f"Projection shows balance: ${projection.get_balance('ACC-001'):.2f}")
    
    # Event log (audit trail)
    print("\n--- Complete Audit Trail ---")
    for event in store.get_all_events():
        print(f"  {event.timestamp.strftime('%H:%M:%S')} | "
              f"{event.__class__.__name__} | "
              f"v{event.version}")
    
    print("\n=== Key Concepts ===")
    print("1. Events are immutable facts")
    print("2. Current state = replay all events")
    print("3. Projections = read-optimized views")
    print("4. Time travel = replay to any version")


if __name__ == "__main__":
    demo()
