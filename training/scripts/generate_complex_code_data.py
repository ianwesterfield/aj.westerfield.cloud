#!/usr/bin/env python3
"""
Generate complex code implementation training examples.

Full implementations: class systems, CLI tools, API handlers,
repository patterns, state machines, and design patterns.
Boosts the 'provide_code' response type with substantial code.
"""

import json
from pathlib import Path
from typing import List, Dict

# Output path
OUTPUT_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, a technical AI assistant created by AJ Westerfield. You provide complete, production-ready code implementations with proper error handling, type hints, and documentation. Your code follows best practices and industry patterns."""

# Complex implementation examples
COMPLEX_CODE_EXAMPLES: List[Dict] = [
    # Full class implementation - Repository Pattern
    {
        "instruction": "Implement a generic repository pattern in Python with SQLAlchemy for basic CRUD operations",
        "response": {
            "action": "provide_code",
            "language": "python",
            "code": '''from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=DeclarativeBase)


class Repository(Generic[T]):
    """
    Generic repository for common CRUD operations.
    
    Usage:
        class UserRepository(Repository[User]):
            def __init__(self, session: Session):
                super().__init__(User, session)
            
            def find_by_email(self, email: str) -> Optional[User]:
                return self.session.scalar(
                    select(User).where(User.email == email)
                )
    """
    
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session
    
    def get(self, id: int) -> Optional[T]:
        """Get entity by primary key."""
        return self.session.get(self.model, id)
    
    def get_or_raise(self, id: int) -> T:
        """Get entity by primary key or raise exception."""
        entity = self.get(id)
        if entity is None:
            raise ValueError(f"{self.model.__name__} with id {id} not found")
        return entity
    
    def get_all(self, *, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination."""
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self.session.scalars(stmt))
    
    def find_by(self, **filters) -> List[T]:
        """Find entities matching filter criteria."""
        stmt = select(self.model).filter_by(**filters)
        return list(self.session.scalars(stmt))
    
    def find_one_by(self, **filters) -> Optional[T]:
        """Find single entity matching criteria."""
        stmt = select(self.model).filter_by(**filters)
        return self.session.scalar(stmt)
    
    def exists(self, id: int) -> bool:
        """Check if entity exists."""
        return self.get(id) is not None
    
    def count(self, **filters) -> int:
        """Count entities matching criteria."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        return self.session.scalar(stmt) or 0
    
    def add(self, entity: T) -> T:
        """Add new entity."""
        self.session.add(entity)
        self.session.flush()  # Get ID without committing
        return entity
    
    def add_all(self, entities: List[T]) -> List[T]:
        """Add multiple entities."""
        self.session.add_all(entities)
        self.session.flush()
        return entities
    
    def update(self, entity: T, **values) -> T:
        """Update entity with given values."""
        for key, value in values.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity
    
    def delete(self, entity: T) -> None:
        """Delete entity."""
        self.session.delete(entity)
        self.session.flush()
    
    def delete_by_id(self, id: int) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        entity = self.get(id)
        if entity:
            self.delete(entity)
            return True
        return False


class UnitOfWork:
    """
    Unit of Work pattern - manages transaction scope.
    
    Usage:
        with UnitOfWork(session_factory) as uow:
            user = uow.users.find_by_email("test@example.com")
            uow.users.update(user, name="New Name")
            uow.commit()
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: Optional[Session] = None
    
    def __enter__(self):
        self.session = self.session_factory()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        self.session.close()
    
    def commit(self):
        """Commit current transaction."""
        self.session.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        self.session.rollback()
    
    @property
    def users(self) -> 'UserRepository':
        """Lazy-load user repository."""
        if not hasattr(self, '_users'):
            self._users = UserRepository(self.session)
        return self._users''',
            "explanation": "Generic repository with Unit of Work for clean data access. Supports CRUD, pagination, filtering, and transaction management."
        }
    },
    
    # CLI Tool with Click
    {
        "instruction": "Create a CLI tool for managing a todo list using Click with commands to add, list, complete, and delete tasks",
        "response": {
            "action": "provide_code",
            "language": "python",
            "code": '''#!/usr/bin/env python3
"""
Todo CLI - Simple task management from the command line.

Usage:
    todo add "Buy groceries" --priority high
    todo list --filter pending
    todo complete 1
    todo delete 1
"""

import click
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, asdict
from enum import Enum


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass
class Todo:
    id: int
    title: str
    priority: Priority
    status: Status
    created_at: str
    completed_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Todo':
        return cls(
            id=data['id'],
            title=data['title'],
            priority=Priority(data['priority']),
            status=Status(data['status']),
            created_at=data['created_at'],
            completed_at=data.get('completed_at')
        )


class TodoStore:
    """Persistent storage for todos."""
    
    def __init__(self, path: Path):
        self.path = path
        self._todos: List[Todo] = []
        self._load()
    
    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self._todos = [Todo.from_dict(t) for t in data]
    
    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [t.to_dict() for t in self._todos]
        self.path.write_text(json.dumps(data, indent=2, default=str))
    
    def _next_id(self) -> int:
        return max((t.id for t in self._todos), default=0) + 1
    
    def add(self, title: str, priority: Priority) -> Todo:
        todo = Todo(
            id=self._next_id(),
            title=title,
            priority=priority,
            status=Status.PENDING,
            created_at=datetime.now().isoformat()
        )
        self._todos.append(todo)
        self._save()
        return todo
    
    def get(self, id: int) -> Optional[Todo]:
        return next((t for t in self._todos if t.id == id), None)
    
    def list(self, status: Optional[Status] = None) -> List[Todo]:
        todos = self._todos
        if status:
            todos = [t for t in todos if t.status == status]
        return sorted(todos, key=lambda t: (
            t.status == Status.COMPLETED,  # Pending first
            {'high': 0, 'medium': 1, 'low': 2}[t.priority.value]
        ))
    
    def complete(self, id: int) -> Optional[Todo]:
        todo = self.get(id)
        if todo:
            todo.status = Status.COMPLETED
            todo.completed_at = datetime.now().isoformat()
            self._save()
        return todo
    
    def delete(self, id: int) -> bool:
        todo = self.get(id)
        if todo:
            self._todos.remove(todo)
            self._save()
            return True
        return False


# CLI Application
pass_store = click.make_pass_decorator(TodoStore)


@click.group()
@click.option('--data-file', 
              default=Path.home() / '.todo' / 'todos.json',
              type=click.Path(path_type=Path),
              help='Path to todo data file')
@click.pass_context
def cli(ctx, data_file: Path):
    """Simple todo list manager."""
    ctx.obj = TodoStore(data_file)


@cli.command()
@click.argument('title')
@click.option('-p', '--priority', 
              type=click.Choice(['low', 'medium', 'high']),
              default='medium',
              help='Task priority')
@pass_store
def add(store: TodoStore, title: str, priority: str):
    """Add a new todo."""
    todo = store.add(title, Priority(priority))
    click.echo(f"✓ Added todo #{todo.id}: {todo.title}")


@cli.command('list')
@click.option('-f', '--filter',
              type=click.Choice(['all', 'pending', 'completed']),
              default='all',
              help='Filter by status')
@pass_store
def list_todos(store: TodoStore, filter: str):
    """List all todos."""
    status = None if filter == 'all' else Status(filter)
    todos = store.list(status)
    
    if not todos:
        click.echo("No todos found.")
        return
    
    # Priority symbols
    priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
    
    for todo in todos:
        icon = priority_icons[todo.priority.value]
        status_mark = '✓' if todo.status == Status.COMPLETED else '○'
        style = {'dim': True} if todo.status == Status.COMPLETED else {}
        click.echo(click.style(
            f"{status_mark} [{todo.id}] {icon} {todo.title}",
            **style
        ))


@cli.command()
@click.argument('id', type=int)
@pass_store
def complete(store: TodoStore, id: int):
    """Mark a todo as completed."""
    todo = store.complete(id)
    if todo:
        click.echo(f"✓ Completed: {todo.title}")
    else:
        click.echo(f"Todo #{id} not found.", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument('id', type=int)
@click.confirmation_option(prompt='Are you sure?')
@pass_store
def delete(store: TodoStore, id: int):
    """Delete a todo."""
    if store.delete(id):
        click.echo(f"✓ Deleted todo #{id}")
    else:
        click.echo(f"Todo #{id} not found.", err=True)
        raise SystemExit(1)


if __name__ == '__main__':
    cli()''',
            "explanation": "Full CLI with Click: command groups, options, arguments, persistent JSON storage, colored output, and confirmation prompts."
        }
    },
    
    # State Machine Implementation
    {
        "instruction": "Implement a state machine for an order processing workflow in Python",
        "response": {
            "action": "provide_code",
            "language": "python",
            "code": '''from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


class OrderState(Enum):
    """Order states in the workflow."""
    DRAFT = auto()
    SUBMITTED = auto()
    PAYMENT_PENDING = auto()
    PAID = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()
    REFUNDED = auto()


class OrderEvent(Enum):
    """Events that trigger state transitions."""
    SUBMIT = auto()
    REQUEST_PAYMENT = auto()
    PAYMENT_RECEIVED = auto()
    PAYMENT_FAILED = auto()
    START_PROCESSING = auto()
    SHIP = auto()
    DELIVER = auto()
    CANCEL = auto()
    REFUND = auto()


@dataclass
class Transition:
    """Defines a valid state transition."""
    from_state: OrderState
    event: OrderEvent
    to_state: OrderState
    guard: Optional[Callable[['Order'], bool]] = None
    action: Optional[Callable[['Order'], None]] = None


@dataclass
class StateHistory:
    """Record of a state change."""
    from_state: OrderState
    to_state: OrderState
    event: OrderEvent
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)


class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition."""
    pass


class OrderStateMachine:
    """
    State machine for order processing workflow.
    
    Defines valid transitions between states and executes
    guard conditions and actions during transitions.
    """
    
    def __init__(self):
        self._transitions: Dict[tuple, Transition] = {}
        self._on_enter: Dict[OrderState, List[Callable]] = {}
        self._on_exit: Dict[OrderState, List[Callable]] = {}
        self._setup_transitions()
    
    def _setup_transitions(self):
        """Define all valid state transitions."""
        transitions = [
            # Draft -> Submitted
            Transition(
                OrderState.DRAFT,
                OrderEvent.SUBMIT,
                OrderState.SUBMITTED,
                guard=lambda o: len(o.items) > 0,
                action=lambda o: o.set_submitted_at()
            ),
            
            # Submitted -> Payment Pending
            Transition(
                OrderState.SUBMITTED,
                OrderEvent.REQUEST_PAYMENT,
                OrderState.PAYMENT_PENDING
            ),
            
            # Payment Pending -> Paid
            Transition(
                OrderState.PAYMENT_PENDING,
                OrderEvent.PAYMENT_RECEIVED,
                OrderState.PAID,
                action=lambda o: o.set_paid_at()
            ),
            
            # Payment Pending -> Submitted (retry)
            Transition(
                OrderState.PAYMENT_PENDING,
                OrderEvent.PAYMENT_FAILED,
                OrderState.SUBMITTED
            ),
            
            # Paid -> Processing
            Transition(
                OrderState.PAID,
                OrderEvent.START_PROCESSING,
                OrderState.PROCESSING
            ),
            
            # Processing -> Shipped
            Transition(
                OrderState.PROCESSING,
                OrderEvent.SHIP,
                OrderState.SHIPPED,
                guard=lambda o: o.tracking_number is not None,
                action=lambda o: o.set_shipped_at()
            ),
            
            # Shipped -> Delivered
            Transition(
                OrderState.SHIPPED,
                OrderEvent.DELIVER,
                OrderState.DELIVERED,
                action=lambda o: o.set_delivered_at()
            ),
            
            # Cancellation from multiple states
            *[Transition(state, OrderEvent.CANCEL, OrderState.CANCELLED)
              for state in [OrderState.DRAFT, OrderState.SUBMITTED, 
                           OrderState.PAYMENT_PENDING]],
            
            # Paid orders need refund
            Transition(
                OrderState.PAID,
                OrderEvent.CANCEL,
                OrderState.CANCELLED,
                action=lambda o: o.initiate_refund()
            ),
            
            # Refund from delivered
            Transition(
                OrderState.DELIVERED,
                OrderEvent.REFUND,
                OrderState.REFUNDED,
                guard=lambda o: o.is_within_refund_window(),
                action=lambda o: o.process_refund()
            ),
        ]
        
        for t in transitions:
            key = (t.from_state, t.event)
            self._transitions[key] = t
    
    def can_transition(self, order: 'Order', event: OrderEvent) -> bool:
        """Check if transition is valid for current state."""
        key = (order.state, event)
        if key not in self._transitions:
            return False
        
        transition = self._transitions[key]
        if transition.guard and not transition.guard(order):
            return False
        
        return True
    
    def get_available_events(self, state: OrderState) -> Set[OrderEvent]:
        """Get events available from current state."""
        return {event for (s, event) in self._transitions.keys() if s == state}
    
    def transition(self, order: 'Order', event: OrderEvent, 
                   metadata: Dict = None) -> OrderState:
        """
        Execute state transition.
        
        Raises InvalidTransitionError if transition is not valid.
        """
        key = (order.state, event)
        
        if key not in self._transitions:
            raise InvalidTransitionError(
                f"No transition defined for {order.state} + {event}"
            )
        
        transition = self._transitions[key]
        
        # Check guard condition
        if transition.guard and not transition.guard(order):
            raise InvalidTransitionError(
                f"Guard condition failed for {order.state} -> {event}"
            )
        
        # Execute on_exit callbacks
        for callback in self._on_exit.get(order.state, []):
            callback(order)
        
        # Record history
        history = StateHistory(
            from_state=order.state,
            to_state=transition.to_state,
            event=event,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        order.history.append(history)
        
        # Execute transition action
        if transition.action:
            transition.action(order)
        
        # Update state
        old_state = order.state
        order.state = transition.to_state
        
        # Execute on_enter callbacks
        for callback in self._on_enter.get(order.state, []):
            callback(order)
        
        return order.state
    
    def on_enter(self, state: OrderState, callback: Callable[['Order'], None]):
        """Register callback for entering a state."""
        if state not in self._on_enter:
            self._on_enter[state] = []
        self._on_enter[state].append(callback)
    
    def on_exit(self, state: OrderState, callback: Callable[['Order'], None]):
        """Register callback for exiting a state."""
        if state not in self._on_exit:
            self._on_exit[state] = []
        self._on_exit[state].append(callback)


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    price: float


@dataclass
class Order:
    """Order entity with state machine integration."""
    id: str
    customer_id: str
    items: List[OrderItem] = field(default_factory=list)
    state: OrderState = OrderState.DRAFT
    tracking_number: Optional[str] = None
    history: List[StateHistory] = field(default_factory=list)
    
    submitted_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    def set_submitted_at(self):
        self.submitted_at = datetime.now()
    
    def set_paid_at(self):
        self.paid_at = datetime.now()
    
    def set_shipped_at(self):
        self.shipped_at = datetime.now()
    
    def set_delivered_at(self):
        self.delivered_at = datetime.now()
    
    def is_within_refund_window(self) -> bool:
        if not self.delivered_at:
            return False
        days_since_delivery = (datetime.now() - self.delivered_at).days
        return days_since_delivery <= 30
    
    def initiate_refund(self):
        print(f"Initiating refund for order {self.id}")
    
    def process_refund(self):
        print(f"Processing refund for order {self.id}")
    
    @property
    def total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)


# Usage example
if __name__ == "__main__":
    sm = OrderStateMachine()
    
    # Register callbacks
    sm.on_enter(OrderState.SHIPPED, lambda o: print(f"📦 Order {o.id} shipped!"))
    sm.on_enter(OrderState.DELIVERED, lambda o: print(f"✓ Order {o.id} delivered!"))
    
    # Create and process order
    order = Order(id="ORD-001", customer_id="CUST-123")
    order.items.append(OrderItem("PROD-1", 2, 29.99))
    
    print(f"Available events: {sm.get_available_events(order.state)}")
    
    sm.transition(order, OrderEvent.SUBMIT)
    sm.transition(order, OrderEvent.REQUEST_PAYMENT)
    sm.transition(order, OrderEvent.PAYMENT_RECEIVED)
    sm.transition(order, OrderEvent.START_PROCESSING)
    
    order.tracking_number = "TRK123456"
    sm.transition(order, OrderEvent.SHIP)
    sm.transition(order, OrderEvent.DELIVER)
    
    print(f"\\nOrder history:")
    for h in order.history:
        print(f"  {h.from_state.name} -> {h.to_state.name} ({h.event.name})")''',
            "explanation": "Full state machine with transitions, guards, actions, callbacks, and history tracking. Models a realistic order workflow."
        }
    },
    
    # FastAPI CRUD API
    {
        "instruction": "Create a complete FastAPI REST API for a blog with posts and comments, including authentication",
        "response": {
            "action": "provide_code",
            "language": "python",
            "code": '''"""
Blog API - FastAPI REST API with authentication.

Features:
- JWT authentication
- Posts CRUD
- Comments CRUD
- Pagination
- Error handling
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Session, relationship, sessionmaker, declarative_base

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:///./blog.db")
SessionLocal = sessionmaker(bind=engine)


# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    post_id = Column(Integer, ForeignKey("posts.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")


Base.metadata.create_all(bind=engine)


# Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: UserResponse
    created_at: datetime
    updated_at: datetime
    comment_count: int = 0
    
    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    id: int
    content: str
    author: UserResponse
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    per_page: int
    pages: int


# Auth utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


# App
app = FastAPI(title="Blog API", version="1.0.0")


# Auth endpoints
@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(400, "Username already taken")
    
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate and get access token."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect username or password")
    
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


# Posts endpoints
@app.get("/posts", response_model=PaginatedResponse)
def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all posts with pagination."""
    total = db.query(Post).count()
    posts = db.query(Post).order_by(Post.created_at.desc()) \
        .offset((page - 1) * per_page).limit(per_page).all()
    
    items = []
    for post in posts:
        post_dict = PostResponse.from_orm(post).dict()
        post_dict['comment_count'] = len(post.comments)
        items.append(post_dict)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new post."""
    post = Post(**post_in.dict(), author_id=current_user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    return post


@app.patch("/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post_in: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a post (author only)."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(403, "Not authorized to edit this post")
    
    update_data = post_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
    
    db.commit()
    db.refresh(post)
    return post


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post (author only)."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(403, "Not authorized to delete this post")
    
    db.delete(post)
    db.commit()


# Comments endpoints
@app.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    """List comments for a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    return post.comments


@app.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    
    comment = Comment(
        content=comment_in.content,
        post_id=post_id,
        author_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.delete("/posts/{post_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a comment (author only)."""
    comment = db.query(Comment).filter(
        Comment.id == comment_id, Comment.post_id == post_id
    ).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(403, "Not authorized to delete this comment")
    
    db.delete(comment)
    db.commit()''',
            "explanation": "Complete REST API with JWT auth, SQLAlchemy models, Pydantic schemas, CRUD operations, authorization checks, and pagination."
        }
    },
    
    # Event System Implementation
    {
        "instruction": "Implement a type-safe event bus system in TypeScript with subscribe, unsubscribe, and emit functionality",
        "response": {
            "action": "provide_code",
            "language": "typescript",
            "code": '''/**
 * Type-safe Event Bus implementation.
 * 
 * Provides compile-time type checking for event names and payloads.
 */

// Define your application events
interface AppEvents {
  'user:login': { userId: string; email: string; timestamp: Date };
  'user:logout': { userId: string };
  'order:created': { orderId: string; items: string[]; total: number };
  'order:shipped': { orderId: string; trackingNumber: string };
  'notification:send': { type: 'email' | 'sms' | 'push'; message: string };
}

type EventCallback<T> = (payload: T) => void | Promise<void>;

interface Subscription {
  unsubscribe: () => void;
}

class EventBus<Events extends Record<string, unknown>> {
  private listeners = new Map<keyof Events, Set<EventCallback<unknown>>>();
  private onceListeners = new Map<keyof Events, Set<EventCallback<unknown>>>();

  /**
   * Subscribe to an event.
   * Returns a subscription object with unsubscribe method.
   */
  on<K extends keyof Events>(
    event: K,
    callback: EventCallback<Events[K]>
  ): Subscription {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    
    this.listeners.get(event)!.add(callback as EventCallback<unknown>);
    
    return {
      unsubscribe: () => {
        this.listeners.get(event)?.delete(callback as EventCallback<unknown>);
      }
    };
  }

  /**
   * Subscribe to an event once.
   * Callback is automatically removed after first invocation.
   */
  once<K extends keyof Events>(
    event: K,
    callback: EventCallback<Events[K]>
  ): Subscription {
    if (!this.onceListeners.has(event)) {
      this.onceListeners.set(event, new Set());
    }
    
    this.onceListeners.get(event)!.add(callback as EventCallback<unknown>);
    
    return {
      unsubscribe: () => {
        this.onceListeners.get(event)?.delete(callback as EventCallback<unknown>);
      }
    };
  }

  /**
   * Remove a specific callback from an event.
   */
  off<K extends keyof Events>(
    event: K,
    callback: EventCallback<Events[K]>
  ): void {
    this.listeners.get(event)?.delete(callback as EventCallback<unknown>);
    this.onceListeners.get(event)?.delete(callback as EventCallback<unknown>);
  }

  /**
   * Remove all listeners for an event, or all events.
   */
  removeAllListeners(event?: keyof Events): void {
    if (event) {
      this.listeners.delete(event);
      this.onceListeners.delete(event);
    } else {
      this.listeners.clear();
      this.onceListeners.clear();
    }
  }

  /**
   * Emit an event with payload.
   * Returns a promise that resolves when all handlers complete.
   */
  async emit<K extends keyof Events>(
    event: K,
    payload: Events[K]
  ): Promise<void> {
    const callbacks = this.listeners.get(event);
    const onceCallbacks = this.onceListeners.get(event);

    const promises: Promise<void>[] = [];

    // Execute regular listeners
    if (callbacks) {
      for (const callback of callbacks) {
        const result = callback(payload);
        if (result instanceof Promise) {
          promises.push(result);
        }
      }
    }

    // Execute once listeners and remove them
    if (onceCallbacks) {
      for (const callback of onceCallbacks) {
        const result = callback(payload);
        if (result instanceof Promise) {
          promises.push(result);
        }
      }
      this.onceListeners.delete(event);
    }

    await Promise.all(promises);
  }

  /**
   * Emit an event synchronously (don't wait for async handlers).
   */
  emitSync<K extends keyof Events>(event: K, payload: Events[K]): void {
    const callbacks = this.listeners.get(event);
    const onceCallbacks = this.onceListeners.get(event);

    if (callbacks) {
      for (const callback of callbacks) {
        callback(payload);
      }
    }

    if (onceCallbacks) {
      for (const callback of onceCallbacks) {
        callback(payload);
      }
      this.onceListeners.delete(event);
    }
  }

  /**
   * Get number of listeners for an event.
   */
  listenerCount(event: keyof Events): number {
    const regular = this.listeners.get(event)?.size ?? 0;
    const once = this.onceListeners.get(event)?.size ?? 0;
    return regular + once;
  }

  /**
   * Check if event has any listeners.
   */
  hasListeners(event: keyof Events): boolean {
    return this.listenerCount(event) > 0;
  }
}

// Create typed event bus instance
const eventBus = new EventBus<AppEvents>();

// Usage examples with full type safety:

// Subscribe to user login
const loginSubscription = eventBus.on('user:login', (payload) => {
  // TypeScript knows payload is { userId: string; email: string; timestamp: Date }
  console.log(`User ${payload.userId} logged in at ${payload.timestamp}`);
});

// Subscribe to orders (async handler)
eventBus.on('order:created', async (payload) => {
  // TypeScript knows payload is { orderId: string; items: string[]; total: number }
  await sendOrderConfirmation(payload.orderId);
  console.log(`Order ${payload.orderId} created: $${payload.total}`);
});

// Subscribe once
eventBus.once('order:shipped', (payload) => {
  console.log(`Order shipped with tracking: ${payload.trackingNumber}`);
});

// Emit events
async function handleUserLogin(userId: string, email: string) {
  await eventBus.emit('user:login', {
    userId,
    email,
    timestamp: new Date()
    // TypeScript will error if you miss or misspell a property
  });
}

// This would cause a TypeScript error:
// eventBus.emit('user:login', { userId: '123' }); // Error: missing email and timestamp

// Unsubscribe
loginSubscription.unsubscribe();

// Helper function for demo
async function sendOrderConfirmation(orderId: string): Promise<void> {
  // Simulate async operation
  await new Promise(resolve => setTimeout(resolve, 100));
}

export { EventBus, eventBus };
export type { AppEvents, EventCallback, Subscription };''',
            "explanation": "Type-safe event bus with generics. Compile-time checking ensures event names match payloads. Supports sync/async handlers, once listeners, and automatic cleanup."
        }
    },
    
    # React Hook with State Machine
    {
        "instruction": "Create a custom React hook for managing async data fetching with loading, error, and refresh states",
        "response": {
            "action": "provide_code",
            "language": "typescript",
            "code": '''import { useReducer, useCallback, useEffect, useRef } from 'react';

/**
 * Async data fetching hook with comprehensive state management.
 * 
 * Features:
 * - Loading, error, success states
 * - Automatic refetch
 * - Manual refresh
 * - Request cancellation
 * - Optimistic updates
 * - Cache support
 */

// State types
type AsyncState<T> =
  | { status: 'idle'; data: null; error: null }
  | { status: 'loading'; data: T | null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: T | null; error: Error };

type AsyncAction<T> =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: T }
  | { type: 'FETCH_ERROR'; payload: Error }
  | { type: 'RESET' }
  | { type: 'SET_DATA'; payload: T };

function asyncReducer<T>(
  state: AsyncState<T>,
  action: AsyncAction<T>
): AsyncState<T> {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, status: 'loading', error: null };
    case 'FETCH_SUCCESS':
      return { status: 'success', data: action.payload, error: null };
    case 'FETCH_ERROR':
      return { ...state, status: 'error', error: action.payload };
    case 'RESET':
      return { status: 'idle', data: null, error: null };
    case 'SET_DATA':
      return { ...state, data: action.payload };
    default:
      return state;
  }
}

interface UseAsyncOptions<T> {
  /** Initial data value */
  initialData?: T;
  /** Fetch on mount */
  immediate?: boolean;
  /** Refetch interval in ms */
  refetchInterval?: number;
  /** Cache key for storing result */
  cacheKey?: string;
  /** Called on successful fetch */
  onSuccess?: (data: T) => void;
  /** Called on error */
  onError?: (error: Error) => void;
}

interface UseAsyncResult<T> {
  // State
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  isIdle: boolean;
  
  // Actions
  execute: () => Promise<T | null>;
  refresh: () => Promise<T | null>;
  reset: () => void;
  setData: (data: T) => void;
}

// Simple in-memory cache
const cache = new Map<string, { data: unknown; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export function useAsync<T>(
  asyncFn: (signal: AbortSignal) => Promise<T>,
  options: UseAsyncOptions<T> = {}
): UseAsyncResult<T> {
  const {
    initialData,
    immediate = true,
    refetchInterval,
    cacheKey,
    onSuccess,
    onError,
  } = options;

  const initialState: AsyncState<T> = initialData
    ? { status: 'success', data: initialData, error: null }
    : { status: 'idle', data: null, error: null };

  const [state, dispatch] = useReducer(asyncReducer<T>, initialState);
  
  // Track if component is mounted
  const mountedRef = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check cache
  const getCached = useCallback((): T | null => {
    if (!cacheKey) return null;
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.data as T;
    }
    return null;
  }, [cacheKey]);

  // Set cache
  const setCache = useCallback((data: T) => {
    if (cacheKey) {
      cache.set(cacheKey, { data, timestamp: Date.now() });
    }
  }, [cacheKey]);

  // Execute the async function
  const execute = useCallback(async (): Promise<T | null> => {
    // Check cache first
    const cached = getCached();
    if (cached) {
      dispatch({ type: 'FETCH_SUCCESS', payload: cached });
      return cached;
    }

    // Cancel any pending request
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    dispatch({ type: 'FETCH_START' });

    try {
      const result = await asyncFn(abortControllerRef.current.signal);
      
      if (mountedRef.current) {
        dispatch({ type: 'FETCH_SUCCESS', payload: result });
        setCache(result);
        onSuccess?.(result);
      }
      
      return result;
    } catch (error) {
      // Ignore abort errors
      if (error instanceof Error && error.name === 'AbortError') {
        return null;
      }
      
      if (mountedRef.current) {
        const err = error instanceof Error ? error : new Error(String(error));
        dispatch({ type: 'FETCH_ERROR', payload: err });
        onError?.(err);
      }
      
      return null;
    }
  }, [asyncFn, getCached, setCache, onSuccess, onError]);

  // Refresh (invalidate cache and refetch)
  const refresh = useCallback(async (): Promise<T | null> => {
    if (cacheKey) {
      cache.delete(cacheKey);
    }
    return execute();
  }, [execute, cacheKey]);

  // Reset to initial state
  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    dispatch({ type: 'RESET' });
  }, []);

  // Optimistic update
  const setData = useCallback((data: T) => {
    dispatch({ type: 'SET_DATA', payload: data });
    setCache(data);
  }, [setCache]);

  // Fetch on mount if immediate
  useEffect(() => {
    if (immediate) {
      execute();
    }
    
    return () => {
      mountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Refetch interval
  useEffect(() => {
    if (!refetchInterval) return;
    
    const interval = setInterval(() => {
      if (mountedRef.current) {
        execute();
      }
    }, refetchInterval);
    
    return () => clearInterval(interval);
  }, [refetchInterval, execute]);

  return {
    data: state.data,
    error: state.error,
    isLoading: state.status === 'loading',
    isError: state.status === 'error',
    isSuccess: state.status === 'success',
    isIdle: state.status === 'idle',
    execute,
    refresh,
    reset,
    setData,
  };
}

// Convenience wrapper for simple fetches
export function useFetch<T>(
  url: string,
  options?: UseAsyncOptions<T> & RequestInit
): UseAsyncResult<T> {
  const { initialData, immediate, refetchInterval, cacheKey, onSuccess, onError, ...fetchOptions } = options || {};
  
  const asyncFn = useCallback(
    async (signal: AbortSignal): Promise<T> => {
      const response = await fetch(url, { ...fetchOptions, signal });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    },
    [url, JSON.stringify(fetchOptions)]
  );

  return useAsync(asyncFn, {
    initialData,
    immediate,
    refetchInterval,
    cacheKey: cacheKey ?? url,
    onSuccess,
    onError,
  });
}

// Usage example:
/*
function UserProfile({ userId }: { userId: string }) {
  const { data: user, isLoading, isError, error, refresh } = useFetch<User>(
    `/api/users/${userId}`,
    {
      cacheKey: `user-${userId}`,
      onSuccess: (user) => console.log('Loaded user:', user.name),
      refetchInterval: 60000, // Refetch every minute
    }
  );

  if (isLoading) return <Spinner />;
  if (isError) return <Error message={error.message} onRetry={refresh} />;
  if (!user) return null;

  return (
    <div>
      <h1>{user.name}</h1>
      <button onClick={refresh}>Refresh</button>
    </div>
  );
}
*/''',
            "explanation": "Full-featured async hook with discriminated union state, abort controller for cancellation, caching, optimistic updates, and refetch interval. Type-safe throughout."
        }
    },
    
    # Dependency Injection Container
    {
        "instruction": "Create a simple dependency injection container in Python with singleton and transient lifetimes",
        "response": {
            "action": "provide_code",
            "language": "python",
            "code": '''"""
Simple Dependency Injection Container.

Supports:
- Singleton lifetime (one instance per container)
- Transient lifetime (new instance per request)
- Factory functions
- Constructor injection
- Interface binding
"""

from typing import TypeVar, Type, Callable, Dict, Any, Optional, Union
from enum import Enum
from functools import wraps
import inspect


class Lifetime(Enum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"


T = TypeVar('T')


class ServiceDescriptor:
    """Describes how to create a service."""
    
    def __init__(
        self,
        service_type: Type,
        implementation: Union[Type, Callable, Any],
        lifetime: Lifetime
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance: Optional[Any] = None  # For singletons


class Container:
    """
    Dependency Injection Container.
    
    Usage:
        container = Container()
        container.register(IRepository, SqlRepository, Lifetime.SINGLETON)
        container.register(UserService)  # Auto-registers with own type
        
        service = container.resolve(UserService)
    """
    
    def __init__(self, parent: Optional['Container'] = None):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._parent = parent
    
    def register(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T], T] = None,
        lifetime: Lifetime = Lifetime.TRANSIENT
    ) -> 'Container':
        """
        Register a service.
        
        Args:
            service_type: The type to register (interface or class)
            implementation: The implementation (class, factory, or instance)
            lifetime: SINGLETON or TRANSIENT
        
        Returns:
            Self for method chaining
        """
        impl = implementation or service_type
        
        # If it's an instance (not a type or callable), make it a singleton
        if not isinstance(impl, type) and not callable(impl):
            self._services[service_type] = ServiceDescriptor(
                service_type, lambda: impl, Lifetime.SINGLETON
            )
            self._services[service_type].instance = impl
        else:
            self._services[service_type] = ServiceDescriptor(
                service_type, impl, lifetime
            )
        
        return self
    
    def register_singleton(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T]] = None
    ) -> 'Container':
        """Convenience method for singleton registration."""
        return self.register(service_type, implementation, Lifetime.SINGLETON)
    
    def register_transient(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T]] = None
    ) -> 'Container':
        """Convenience method for transient registration."""
        return self.register(service_type, implementation, Lifetime.TRANSIENT)
    
    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        lifetime: Lifetime = Lifetime.TRANSIENT
    ) -> 'Container':
        """Register a factory function."""
        return self.register(service_type, factory, lifetime)
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service, creating it if necessary.
        
        Automatically resolves constructor dependencies.
        """
        descriptor = self._get_descriptor(service_type)
        
        if descriptor is None:
            raise KeyError(f"Service {service_type.__name__} is not registered")
        
        # Return existing singleton
        if descriptor.lifetime == Lifetime.SINGLETON and descriptor.instance:
            return descriptor.instance
        
        # Create instance
        instance = self._create_instance(descriptor)
        
        # Cache singleton
        if descriptor.lifetime == Lifetime.SINGLETON:
            descriptor.instance = instance
        
        return instance
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Resolve a service, returning None if not registered."""
        try:
            return self.resolve(service_type)
        except KeyError:
            return None
    
    def _get_descriptor(self, service_type: Type) -> Optional[ServiceDescriptor]:
        """Get descriptor from this container or parent."""
        if service_type in self._services:
            return self._services[service_type]
        if self._parent:
            return self._parent._get_descriptor(service_type)
        return None
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance, resolving dependencies."""
        impl = descriptor.implementation
        
        # If it's a simple callable/factory, check if it needs dependencies
        if callable(impl):
            sig = inspect.signature(impl)
            params = sig.parameters
            
            # Get type hints for parameters
            hints = {}
            if hasattr(impl, '__init__') and impl.__init__ is not object.__init__:
                hints = getattr(impl.__init__, '__annotations__', {})
            elif hasattr(impl, '__call__'):
                hints = getattr(impl, '__annotations__', {})
            else:
                hints = getattr(impl, '__annotations__', {})
            
            # Resolve dependencies
            kwargs = {}
            for name, param in params.items():
                if name == 'self':
                    continue
                if name in hints:
                    dep_type = hints[name]
                    if self._get_descriptor(dep_type):
                        kwargs[name] = self.resolve(dep_type)
            
            return impl(**kwargs) if kwargs else impl()
        
        return impl
    
    def create_scope(self) -> 'Container':
        """Create a scoped container (child container)."""
        return Container(parent=self)
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service is registered."""
        return self._get_descriptor(service_type) is not None


# Decorator for auto-registration
def injectable(
    lifetime: Lifetime = Lifetime.TRANSIENT,
    interface: Type = None
):
    """
    Decorator to mark a class as injectable.
    
    Usage:
        @injectable(lifetime=Lifetime.SINGLETON)
        class UserService:
            def __init__(self, repo: UserRepository):
                self.repo = repo
    """
    def decorator(cls: Type[T]) -> Type[T]:
        cls._di_lifetime = lifetime
        cls._di_interface = interface or cls
        return cls
    return decorator


def auto_register(container: Container, *classes: Type):
    """Auto-register classes decorated with @injectable."""
    for cls in classes:
        lifetime = getattr(cls, '_di_lifetime', Lifetime.TRANSIENT)
        interface = getattr(cls, '_di_interface', cls)
        container.register(interface, cls, lifetime)


# Example usage
if __name__ == "__main__":
    from abc import ABC, abstractmethod
    
    # Define interfaces
    class IUserRepository(ABC):
        @abstractmethod
        def get(self, id: int) -> dict: pass
    
    class IEmailService(ABC):
        @abstractmethod
        def send(self, to: str, message: str): pass
    
    # Implementations
    @injectable(Lifetime.SINGLETON, interface=IUserRepository)
    class SqlUserRepository(IUserRepository):
        def get(self, id: int) -> dict:
            return {"id": id, "name": "John"}
    
    @injectable(Lifetime.TRANSIENT, interface=IEmailService)
    class SmtpEmailService(IEmailService):
        def send(self, to: str, message: str):
            print(f"Sending email to {to}: {message}")
    
    @injectable(Lifetime.TRANSIENT)
    class UserService:
        def __init__(self, repo: IUserRepository, email: IEmailService):
            self.repo = repo
            self.email = email
        
        def notify_user(self, user_id: int, message: str):
            user = self.repo.get(user_id)
            self.email.send(user["name"], message)
    
    # Setup container
    container = Container()
    auto_register(
        container,
        SqlUserRepository,
        SmtpEmailService,
        UserService
    )
    
    # Resolve and use
    service = container.resolve(UserService)
    service.notify_user(1, "Hello!")
    
    # Verify singleton behavior
    repo1 = container.resolve(IUserRepository)
    repo2 = container.resolve(IUserRepository)
    print(f"Same instance: {repo1 is repo2}")  # True''',
            "explanation": "Full DI container with lifetime management, constructor injection via introspection, decorators for auto-registration, and scoped containers."
        }
    },
    
    # Rate Limiter Implementation
    {
        "instruction": "Implement a rate limiter with sliding window algorithm in Python, usable as a decorator",
        "response": {
            "action": "provide_code",
            "language": "python",
            "code": '''"""
Rate Limiter with Sliding Window Algorithm.

Features:
- Sliding window for accurate rate limiting
- Token bucket for burst handling
- Decorator support
- Async support
- Redis backend option
"""

import time
import asyncio
from collections import deque
from functools import wraps
from typing import Callable, Deque, Optional, Dict, Any
from dataclasses import dataclass
from threading import Lock
from abc import ABC, abstractmethod


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.2f}s")


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests: int        # Number of requests allowed
    window_seconds: int  # Time window in seconds
    burst: int = 0       # Additional burst capacity


class RateLimiterBackend(ABC):
    """Abstract backend for rate limiter storage."""
    
    @abstractmethod
    def get_window(self, key: str) -> Deque[float]:
        """Get the sliding window for a key."""
        pass
    
    @abstractmethod
    def add_request(self, key: str, timestamp: float) -> None:
        """Add a request timestamp to the window."""
        pass
    
    @abstractmethod
    def cleanup_window(self, key: str, cutoff: float) -> None:
        """Remove timestamps older than cutoff."""
        pass


class InMemoryBackend(RateLimiterBackend):
    """In-memory backend using deque."""
    
    def __init__(self):
        self._windows: Dict[str, Deque[float]] = {}
        self._lock = Lock()
    
    def get_window(self, key: str) -> Deque[float]:
        with self._lock:
            if key not in self._windows:
                self._windows[key] = deque()
            return self._windows[key]
    
    def add_request(self, key: str, timestamp: float) -> None:
        with self._lock:
            if key not in self._windows:
                self._windows[key] = deque()
            self._windows[key].append(timestamp)
    
    def cleanup_window(self, key: str, cutoff: float) -> None:
        with self._lock:
            if key in self._windows:
                window = self._windows[key]
                while window and window[0] < cutoff:
                    window.popleft()


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.
    
    More accurate than fixed window - prevents burst at window boundaries.
    
    Usage:
        limiter = SlidingWindowRateLimiter(requests=100, window_seconds=60)
        
        if limiter.allow("user:123"):
            process_request()
        else:
            raise RateLimitExceeded(limiter.retry_after("user:123"))
    """
    
    def __init__(
        self,
        requests: int,
        window_seconds: int,
        burst: int = 0,
        backend: Optional[RateLimiterBackend] = None
    ):
        self.requests = requests
        self.window_seconds = window_seconds
        self.burst = burst
        self.backend = backend or InMemoryBackend()
    
    def allow(self, key: str) -> bool:
        """Check if request is allowed and record it if so."""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean up old requests
        self.backend.cleanup_window(key, cutoff)
        
        # Check current count
        window = self.backend.get_window(key)
        current_count = len(window)
        limit = self.requests + self.burst
        
        if current_count < limit:
            self.backend.add_request(key, now)
            return True
        
        return False
    
    def retry_after(self, key: str) -> float:
        """Get seconds until next request is allowed."""
        window = self.backend.get_window(key)
        if not window:
            return 0.0
        
        # Time until oldest request expires
        oldest = window[0]
        return max(0, oldest + self.window_seconds - time.time())
    
    def remaining(self, key: str) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        cutoff = now - self.window_seconds
        self.backend.cleanup_window(key, cutoff)
        
        window = self.backend.get_window(key)
        limit = self.requests + self.burst
        return max(0, limit - len(window))
    
    def reset_time(self, key: str) -> float:
        """Get timestamp when window resets."""
        window = self.backend.get_window(key)
        if not window:
            return time.time()
        return window[0] + self.window_seconds


def rate_limit(
    requests: int,
    window_seconds: int,
    key_func: Callable[..., str] = None,
    burst: int = 0
):
    """
    Decorator for rate limiting functions.
    
    Args:
        requests: Number of requests allowed per window
        window_seconds: Window size in seconds
        key_func: Function to extract rate limit key from args
        burst: Additional burst capacity
    
    Usage:
        @rate_limit(requests=10, window_seconds=60)
        def api_endpoint(user_id: str, data: dict):
            ...
        
        @rate_limit(
            requests=100,
            window_seconds=60,
            key_func=lambda user_id, **kw: f"user:{user_id}"
        )
        def user_action(user_id: str, action: str):
            ...
    """
    limiter = SlidingWindowRateLimiter(requests, window_seconds, burst)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default: use first argument or "default"
                key = str(args[0]) if args else "default"
            
            if not limiter.allow(key):
                raise RateLimitExceeded(limiter.retry_after(key))
            
            return func(*args, **kwargs)
        
        # Attach limiter for inspection
        wrapper.limiter = limiter
        return wrapper
    
    return decorator


def async_rate_limit(
    requests: int,
    window_seconds: int,
    key_func: Callable[..., str] = None,
    burst: int = 0
):
    """Async version of rate_limit decorator."""
    limiter = SlidingWindowRateLimiter(requests, window_seconds, burst)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = str(args[0]) if args else "default"
            
            if not limiter.allow(key):
                raise RateLimitExceeded(limiter.retry_after(key))
            
            return await func(*args, **kwargs)
        
        wrapper.limiter = limiter
        return wrapper
    
    return decorator


# FastAPI middleware integration
class RateLimitMiddleware:
    """FastAPI/Starlette middleware for rate limiting."""
    
    def __init__(
        self,
        app,
        requests: int = 100,
        window_seconds: int = 60,
        key_func: Callable = None
    ):
        self.app = app
        self.limiter = SlidingWindowRateLimiter(requests, window_seconds)
        self.key_func = key_func or (lambda req: req.client.host)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        
        request = Request(scope, receive)
        key = self.key_func(request)
        
        if not self.limiter.allow(key):
            response = JSONResponse(
                {"error": "Rate limit exceeded"},
                status_code=429,
                headers={
                    "Retry-After": str(int(self.limiter.retry_after(key))),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(self.limiter.reset_time(key)))
                }
            )
            await response(scope, receive, send)
            return
        
        # Add rate limit headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"X-RateLimit-Remaining"] = str(self.limiter.remaining(key)).encode()
                headers[b"X-RateLimit-Limit"] = str(self.limiter.requests).encode()
                message["headers"] = list(headers.items())
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Example usage
if __name__ == "__main__":
    # Basic usage
    limiter = SlidingWindowRateLimiter(requests=5, window_seconds=10)
    
    for i in range(7):
        key = "test"
        if limiter.allow(key):
            print(f"Request {i+1}: Allowed (remaining: {limiter.remaining(key)})")
        else:
            print(f"Request {i+1}: Blocked (retry after: {limiter.retry_after(key):.2f}s)")
    
    # Decorator usage
    @rate_limit(requests=3, window_seconds=5)
    def process_request(user_id: str, data: str) -> str:
        return f"Processed {data} for {user_id}"
    
    try:
        for i in range(5):
            result = process_request("user123", f"data{i}")
            print(result)
    except RateLimitExceeded as e:
        print(f"Rate limited: {e}")''',
            "explanation": "Production-ready rate limiter with sliding window algorithm, decorator support, async support, FastAPI middleware, and extensible backend for Redis integration."
        }
    },
    
    # WebSocket Manager
    {
        "instruction": "Create a WebSocket connection manager for real-time features in Python with rooms and broadcasting",
        "response": {
            "action": "provide_code",
            "language": "python",
            "code": '''"""
WebSocket Connection Manager for real-time features.

Features:
- Connection lifecycle management
- Room/channel support
- Broadcasting to all/room/specific users
- Heartbeat/ping-pong
- Reconnection handling
- Message history
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from fastapi import WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MESSAGE = "message"
    BROADCAST = "broadcast"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


@dataclass
class Message:
    type: MessageType
    data: Any = None
    room: Optional[str] = None
    sender_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "data": self.data,
            "room": self.room,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class Connection:
    websocket: WebSocket
    user_id: str
    rooms: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionManager:
    """
    Manages WebSocket connections with room support.
    
    Usage:
        manager = ConnectionManager()
        
        @app.websocket("/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            await manager.connect(websocket, user_id)
            try:
                while True:
                    data = await websocket.receive_json()
                    await manager.handle_message(user_id, data)
            except WebSocketDisconnect:
                await manager.disconnect(user_id)
    """
    
    def __init__(
        self,
        ping_interval: int = 30,
        ping_timeout: int = 10,
        max_connections_per_user: int = 5
    ):
        self._connections: Dict[str, Connection] = {}
        self._rooms: Dict[str, Set[str]] = {}  # room -> user_ids
        self._handlers: Dict[str, Callable] = {}
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._max_connections = max_connections_per_user
        self._message_history: Dict[str, list] = {}  # room -> messages
        self._history_limit = 100
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Accept and register a new connection."""
        await websocket.accept()
        
        # Create connection
        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            metadata=metadata or {}
        )
        self._connections[user_id] = connection
        
        # Send connect confirmation
        await self._send_to_connection(
            connection,
            Message(type=MessageType.CONNECT, data={"user_id": user_id})
        )
        
        logger.info(f"User {user_id} connected. Total: {len(self._connections)}")
        return True
    
    async def disconnect(self, user_id: str):
        """Handle disconnection."""
        if user_id not in self._connections:
            return
        
        connection = self._connections[user_id]
        
        # Leave all rooms
        for room in list(connection.rooms):
            await self.leave_room(user_id, room)
        
        # Remove connection
        del self._connections[user_id]
        
        logger.info(f"User {user_id} disconnected. Total: {len(self._connections)}")
    
    async def join_room(self, user_id: str, room: str):
        """Add user to a room."""
        if user_id not in self._connections:
            return
        
        if room not in self._rooms:
            self._rooms[room] = set()
        
        self._rooms[room].add(user_id)
        self._connections[user_id].rooms.add(room)
        
        # Notify room
        await self.broadcast_to_room(
            room,
            Message(
                type=MessageType.JOIN_ROOM,
                data={"user_id": user_id},
                room=room
            ),
            exclude={user_id}
        )
        
        # Send room history to user
        if room in self._message_history:
            for msg in self._message_history[room][-20:]:  # Last 20 messages
                await self.send_to_user(user_id, msg)
        
        logger.info(f"User {user_id} joined room {room}")
    
    async def leave_room(self, user_id: str, room: str):
        """Remove user from a room."""
        if room not in self._rooms:
            return
        
        self._rooms[room].discard(user_id)
        
        if user_id in self._connections:
            self._connections[user_id].rooms.discard(room)
        
        # Notify room
        await self.broadcast_to_room(
            room,
            Message(
                type=MessageType.LEAVE_ROOM,
                data={"user_id": user_id},
                room=room
            )
        )
        
        # Clean up empty rooms
        if not self._rooms[room]:
            del self._rooms[room]
        
        logger.info(f"User {user_id} left room {room}")
    
    async def send_to_user(self, user_id: str, message: Message):
        """Send message to specific user."""
        if user_id not in self._connections:
            return False
        
        connection = self._connections[user_id]
        return await self._send_to_connection(connection, message)
    
    async def broadcast_to_room(
        self,
        room: str,
        message: Message,
        exclude: Set[str] = None
    ):
        """Broadcast message to all users in a room."""
        if room not in self._rooms:
            return
        
        exclude = exclude or set()
        message.room = room
        
        # Store in history
        self._add_to_history(room, message)
        
        # Send to all room members
        tasks = []
        for user_id in self._rooms[room]:
            if user_id not in exclude:
                tasks.append(self.send_to_user(user_id, message))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_all(self, message: Message, exclude: Set[str] = None):
        """Broadcast message to all connected users."""
        exclude = exclude or set()
        
        tasks = []
        for user_id in self._connections:
            if user_id not in exclude:
                tasks.append(self.send_to_user(user_id, message))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_message(self, user_id: str, data: dict):
        """Handle incoming message from client."""
        msg_type = data.get("type", "message")
        
        if msg_type == "ping":
            await self.send_to_user(
                user_id,
                Message(type=MessageType.PONG)
            )
            if user_id in self._connections:
                self._connections[user_id].last_ping = datetime.utcnow()
            return
        
        if msg_type == "join_room":
            await self.join_room(user_id, data.get("room"))
            return
        
        if msg_type == "leave_room":
            await self.leave_room(user_id, data.get("room"))
            return
        
        # Custom handler
        if msg_type in self._handlers:
            await self._handlers[msg_type](user_id, data)
            return
        
        # Default: broadcast to room or all
        message = Message(
            type=MessageType.MESSAGE,
            data=data.get("data"),
            room=data.get("room"),
            sender_id=user_id
        )
        
        if message.room:
            await self.broadcast_to_room(message.room, message, exclude={user_id})
        else:
            await self.broadcast_all(message, exclude={user_id})
    
    def on(self, message_type: str):
        """Decorator to register message handler."""
        def decorator(func: Callable[[str, dict], Awaitable[None]]):
            self._handlers[message_type] = func
            return func
        return decorator
    
    async def _send_to_connection(
        self,
        connection: Connection,
        message: Message
    ) -> bool:
        """Send message to a connection."""
        try:
            await connection.websocket.send_text(message.to_json())
            return True
        except Exception as e:
            logger.error(f"Failed to send to {connection.user_id}: {e}")
            return False
    
    def _add_to_history(self, room: str, message: Message):
        """Add message to room history."""
        if room not in self._message_history:
            self._message_history[room] = []
        
        self._message_history[room].append(message)
        
        # Trim history
        if len(self._message_history[room]) > self._history_limit:
            self._message_history[room] = self._message_history[room][-self._history_limit:]
    
    def get_room_users(self, room: str) -> Set[str]:
        """Get all users in a room."""
        return self._rooms.get(room, set()).copy()
    
    def get_user_rooms(self, user_id: str) -> Set[str]:
        """Get all rooms a user is in."""
        if user_id not in self._connections:
            return set()
        return self._connections[user_id].rooms.copy()
    
    @property
    def connection_count(self) -> int:
        """Total number of connections."""
        return len(self._connections)
    
    def is_connected(self, user_id: str) -> bool:
        """Check if user is connected."""
        return user_id in self._connections


# FastAPI integration example
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
manager = ConnectionManager()

# Custom handler
@manager.on("typing")
async def handle_typing(user_id: str, data: dict):
    room = data.get("room")
    if room:
        await manager.broadcast_to_room(
            room,
            Message(type="typing", data={"user_id": user_id}, room=room),
            exclude={user_id}
        )

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.handle_message(user_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
"""''',
            "explanation": "Full WebSocket manager with connection tracking, room support, broadcasting, message history, custom handlers, and FastAPI integration."
        }
    },
]


def generate_examples() -> List[Dict]:
    """Generate all complex code training examples."""
    examples = []
    
    for example in COMPLEX_CODE_EXAMPLES:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": example["instruction"],
            "response": json.dumps(example["response"], indent=2)
        })
    
    return examples


def save_examples(examples: List[Dict], filename: str = "complex_code.jsonl"):
    """Save examples to JSONL file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"Generated {len(examples)} complex code examples -> {output_path}")
    return examples


if __name__ == "__main__":
    examples = generate_examples()
    save_examples(examples)
