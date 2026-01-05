#!/usr/bin/env python3
"""
Generate code review training examples.

Focuses on "concepts" response type - providing constructive code review
feedback with specific suggestions for improvement.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple

# Output path
OUTPUT_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, a technical AI assistant created by AJ Westerfield. You specialize in thorough, constructive code reviews. When reviewing code, you identify issues, explain why they matter, and suggest specific improvements while maintaining a respectful, educational tone."""

# Code review examples: (code_to_review, review_feedback)
CODE_REVIEW_EXAMPLES: List[Tuple[str, str]] = [
    # Security Issues
    (
        '''def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    if result:
        session['user'] = username
        return redirect('/dashboard')
    return "Login failed"''',
        """**Security Review: Critical Issues Found**

🔴 **SQL Injection Vulnerability (Critical)**
The query uses f-string formatting with user input, making it vulnerable to SQL injection.

```python
# Vulnerable
query = f"SELECT * FROM users WHERE username='{username}'"

# Fixed - use parameterized queries
query = "SELECT * FROM users WHERE username = %s AND password = %s"
result = db.execute(query, (username, hashed_password))
```

🔴 **Plain Text Password Storage (Critical)**
Passwords should never be stored or compared in plain text.

```python
# Use a proper password hashing library
from werkzeug.security import check_password_hash

user = db.execute("SELECT * FROM users WHERE username = %s", (username,))
if user and check_password_hash(user.password_hash, password):
    # Login successful
```

🟡 **Information Disclosure (Medium)**
Returning "Login failed" for all failures is good, but also ensure timing attacks aren't possible.

🟡 **Missing Rate Limiting (Medium)**
Consider adding rate limiting to prevent brute force attacks.

**Recommendation**: This code should not be deployed until SQL injection and password handling are fixed."""
    ),
    
    (
        '''import pickle
import os

def load_user_data(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def run_command(cmd):
    os.system(cmd)

def process_upload(file_data):
    path = f"/uploads/{file_data['name']}"
    with open(path, 'wb') as f:
        f.write(file_data['content'])''',
        """**Security Review: Multiple Critical Vulnerabilities**

🔴 **Unsafe Deserialization (Critical)**
`pickle.load()` can execute arbitrary code if given malicious data.

```python
# Never unpickle untrusted data! Use safer alternatives:
import json
def load_user_data(filename):
    with open(filename, 'r') as f:
        return json.load(f)
```

🔴 **Command Injection (Critical)**
`os.system()` with unvalidated input allows arbitrary command execution.

```python
# Use subprocess with shell=False and validate inputs
import subprocess
import shlex

def run_command(cmd, allowed_commands):
    if cmd.split()[0] not in allowed_commands:
        raise ValueError("Command not allowed")
    subprocess.run(shlex.split(cmd), shell=False, check=True)
```

🔴 **Path Traversal (Critical)**
The filename could contain `../` to write outside the uploads directory.

```python
import os
from pathlib import Path

UPLOAD_DIR = Path("/uploads")

def process_upload(file_data):
    # Sanitize filename
    safe_name = os.path.basename(file_data['name'])
    path = UPLOAD_DIR / safe_name
    
    # Verify it's still within upload directory
    if not path.resolve().is_relative_to(UPLOAD_DIR):
        raise ValueError("Invalid filename")
    
    with open(path, 'wb') as f:
        f.write(file_data['content'])
```

**Severity**: All three vulnerabilities are critical and exploitable. Do not deploy."""
    ),
    
    # Performance Issues
    (
        '''def get_user_orders(user_ids):
    orders = []
    for user_id in user_ids:
        user = User.query.get(user_id)
        for order in user.orders:
            order_data = {
                'id': order.id,
                'user': user.name,
                'items': []
            }
            for item in order.items:
                product = Product.query.get(item.product_id)
                order_data['items'].append({
                    'name': product.name,
                    'price': product.price,
                    'quantity': item.quantity
                })
            orders.append(order_data)
    return orders''',
        """**Performance Review: N+1 Query Problem**

🔴 **N+1 Query Anti-Pattern (Critical Performance)**
This code generates hundreds or thousands of database queries:
- 1 query per user (N)
- 1 query per order per user (N×M)
- 1 query per item per order (N×M×K)

For 100 users with 10 orders and 5 items each = 5,000+ queries!

```python
# Fixed with eager loading and batch queries
def get_user_orders(user_ids):
    # Single query with joins
    users = (User.query
        .filter(User.id.in_(user_ids))
        .options(
            joinedload(User.orders)
            .joinedload(Order.items)
            .joinedload(OrderItem.product)
        )
        .all())
    
    return [
        {
            'id': order.id,
            'user': user.name,
            'items': [
                {
                    'name': item.product.name,
                    'price': item.product.price,
                    'quantity': item.quantity
                }
                for item in order.items
            ]
        }
        for user in users
        for order in user.orders
    ]
```

**Additional Suggestions**:
- Add pagination for large result sets
- Consider caching for frequently accessed data
- Add database indexes on foreign keys

**Impact**: This fix could reduce page load from 10+ seconds to under 100ms."""
    ),
    
    (
        '''def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                if items[i] not in duplicates:
                    duplicates.append(items[i])
    return duplicates

def process_large_file(filepath):
    with open(filepath) as f:
        content = f.read()  # Load entire file
    lines = content.split('\\n')
    results = []
    for line in lines:
        if 'ERROR' in line:
            results.append(line)
    return results''',
        """**Performance Review: Inefficient Algorithms**

🔴 **O(n²) Algorithm (High Impact)**
The `find_duplicates` function has O(n²) time complexity. For 10,000 items, that's 100 million comparisons!

```python
# O(n) solution using Counter
from collections import Counter

def find_duplicates(items):
    counts = Counter(items)
    return [item for item, count in counts.items() if count > 1]

# Or using set for just detecting duplicates:
def find_duplicates(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
```

🟡 **Memory Issue with Large Files (Medium)**
Reading the entire file into memory will fail for large files.

```python
def process_large_file(filepath):
    results = []
    with open(filepath) as f:
        for line in f:  # Iterate line by line
            if 'ERROR' in line:
                results.append(line.rstrip())
    return results

# For very large files, use a generator:
def process_large_file(filepath):
    with open(filepath) as f:
        for line in f:
            if 'ERROR' in line:
                yield line.rstrip()
```

**Benchmarks** (estimated for 100,000 items):
- Original find_duplicates: ~30 seconds
- Fixed version: ~0.01 seconds"""
    ),
    
    # Error Handling
    (
        '''def process_payment(order_id):
    order = Order.query.get(order_id)
    customer = Customer.query.get(order.customer_id)
    
    response = payment_gateway.charge(
        amount=order.total,
        card=customer.card_token
    )
    
    order.status = 'paid'
    order.payment_id = response['id']
    db.session.commit()
    
    send_confirmation_email(customer.email, order)
    
    return {'success': True}''',
        """**Error Handling Review: Missing Exception Handling**

🔴 **No Null Checks (Critical)**
If `order` or `customer` is None, this will crash with AttributeError.

🔴 **No Payment Error Handling (Critical)**
Payment gateway failures aren't handled - money could be charged but order not updated.

🔴 **No Transaction Rollback (Critical)**
If email fails after commit, the user won't know their order succeeded.

```python
def process_payment(order_id):
    # Validate inputs
    order = Order.query.get(order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    
    if order.status == 'paid':
        raise ValueError("Order already paid")
    
    customer = Customer.query.get(order.customer_id)
    if not customer or not customer.card_token:
        raise ValueError("Customer payment method not found")
    
    try:
        # Attempt payment
        response = payment_gateway.charge(
            amount=order.total,
            card=customer.card_token
        )
        
        if not response.get('success'):
            return {
                'success': False,
                'error': response.get('error', 'Payment failed')
            }
        
        # Update order in transaction
        order.status = 'paid'
        order.payment_id = response['id']
        db.session.commit()
        
    except PaymentGatewayError as e:
        db.session.rollback()
        logger.error(f"Payment failed for order {order_id}: {e}")
        return {'success': False, 'error': 'Payment processing failed'}
    
    # Send email outside transaction (non-critical)
    try:
        send_confirmation_email(customer.email, order)
    except EmailError as e:
        logger.warning(f"Failed to send confirmation for order {order_id}: {e}")
        # Don't fail the payment for email issues
    
    return {'success': True, 'payment_id': response['id']}
```

**Key Principles Applied**:
- Validate early, fail fast
- Use specific exception types
- Separate critical and non-critical operations
- Always log errors with context"""
    ),
    
    (
        '''async def fetch_all_data(urls):
    results = []
    for url in urls:
        try:
            response = await http_client.get(url)
            results.append(response.json())
        except:
            pass
    return results''',
        """**Error Handling Review: Silent Failures**

🔴 **Bare Except Clause (Critical)**
`except: pass` silently swallows ALL exceptions, including:
- KeyboardInterrupt (can't Ctrl+C)
- SystemExit (can't stop the program)
- Memory errors

🔴 **Silent Failures (High)**
When a URL fails, there's no indication which one or why.

🟡 **Sequential Fetching (Medium)**
Async function but fetching URLs sequentially, not in parallel.

```python
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class FetchResult:
    url: str
    success: bool
    data: Any = None
    error: str = None

async def fetch_url(url: str, timeout: float = 30) -> FetchResult:
    \"\"\"Fetch a single URL with proper error handling.\"\"\"
    try:
        response = await asyncio.wait_for(
            http_client.get(url),
            timeout=timeout
        )
        response.raise_for_status()
        return FetchResult(url=url, success=True, data=response.json())
    
    except asyncio.TimeoutError:
        return FetchResult(url=url, success=False, error="Request timed out")
    except httpx.HTTPStatusError as e:
        return FetchResult(url=url, success=False, error=f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        return FetchResult(url=url, success=False, error=str(e))
    except json.JSONDecodeError:
        return FetchResult(url=url, success=False, error="Invalid JSON response")

async def fetch_all_data(urls: List[str]) -> List[FetchResult]:
    \"\"\"Fetch all URLs concurrently with error tracking.\"\"\"
    tasks = [fetch_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log failures for debugging
    for result in results:
        if isinstance(result, FetchResult) and not result.success:
            logger.warning(f"Failed to fetch {result.url}: {result.error}")
    
    return results
```

**Benefits**:
- Specific exceptions caught and handled
- Errors are logged with context
- Results indicate success/failure per URL
- URLs fetched in parallel (10x faster for many URLs)"""
    ),
    
    # Code Style and Maintainability
    (
        '''def calc(d):
    t = 0
    for i in d:
        if i['t'] == 'a':
            t += i['v']
        elif i['t'] == 's':
            t -= i['v']
        elif i['t'] == 'm':
            t *= i['v']
        elif i['t'] == 'd':
            t /= i['v']
    return t''',
        """**Code Style Review: Readability Issues**

🔴 **Cryptic Names (High Impact)**
Single-letter variables make code impossible to understand.

🟡 **Magic Strings (Medium)**
Type codes 'a', 's', 'm', 'd' are not self-documenting.

🟡 **No Type Hints (Medium)**
Function signature doesn't indicate expected types.

```python
from enum import Enum
from typing import List
from dataclasses import dataclass

class OperationType(Enum):
    ADD = 'add'
    SUBTRACT = 'subtract'
    MULTIPLY = 'multiply'
    DIVIDE = 'divide'

@dataclass
class Operation:
    type: OperationType
    value: float

def calculate_total(operations: List[Operation]) -> float:
    \"\"\"Apply a sequence of operations to compute a total.
    
    Args:
        operations: List of operations to apply sequentially.
        
    Returns:
        The computed total after all operations.
    \"\"\"
    total = 0.0
    
    for operation in operations:
        match operation.type:
            case OperationType.ADD:
                total += operation.value
            case OperationType.SUBTRACT:
                total -= operation.value
            case OperationType.MULTIPLY:
                total *= operation.value
            case OperationType.DIVIDE:
                if operation.value == 0:
                    raise ValueError("Division by zero")
                total /= operation.value
    
    return total
```

**Improvements Made**:
- Descriptive function and variable names
- Enum for operation types (IDE autocomplete, typo prevention)
- Type hints for clarity
- Docstring explaining purpose
- Division by zero protection"""
    ),
    
    (
        '''class UserManager:
    def __init__(self):
        self.db = Database()
        self.cache = Redis()
        self.email = EmailService()
        self.logger = Logger()
        self.validator = Validator()
        self.encryptor = Encryptor()
    
    def create_user(self, data):
        # 200 lines of code doing validation, db ops, caching, emailing...
        pass
    
    def update_user(self, id, data):
        # Another 150 lines...
        pass
    
    def delete_user(self, id):
        # 100 more lines...
        pass
    
    def send_password_reset(self, email):
        # 80 lines...
        pass
    
    def verify_email(self, token):
        # 60 lines...
        pass
    
    # ... 20 more methods''',
        """**Architecture Review: God Class Anti-Pattern**

🔴 **Single Responsibility Violation (Critical)**
`UserManager` does too many things:
- User CRUD operations
- Password management
- Email verification
- Caching
- Logging
- Validation
- Encryption

🔴 **High Coupling (Critical)**
6 direct dependencies make this class hard to test and modify.

🟡 **Low Cohesion (High)**
Methods are loosely related, indicating multiple responsibilities.

**Suggested Refactoring**:

```python
# Split into focused classes
class UserRepository:
    \"\"\"Handles user persistence only.\"\"\"
    def __init__(self, db: Database):
        self._db = db
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    def save(self, user: User) -> User:
        pass
    
    def delete(self, user_id: int) -> None:
        pass

class UserService:
    \"\"\"Orchestrates user operations.\"\"\"
    def __init__(
        self,
        repository: UserRepository,
        validator: UserValidator,
        events: EventBus
    ):
        self._repository = repository
        self._validator = validator
        self._events = events
    
    def create_user(self, data: CreateUserDTO) -> User:
        self._validator.validate_create(data)
        user = User.from_dto(data)
        saved = self._repository.save(user)
        self._events.publish(UserCreated(saved))
        return saved

class PasswordService:
    \"\"\"Handles password operations.\"\"\"
    def __init__(self, repository: UserRepository, email: EmailService):
        pass
    
    def request_reset(self, email: str) -> None:
        pass
    
    def reset_password(self, token: str, new_password: str) -> None:
        pass

class EmailVerificationService:
    \"\"\"Handles email verification.\"\"\"
    pass
```

**Benefits**:
- Each class has one reason to change
- Easy to test in isolation
- Dependencies are explicit and injectable
- Can modify email logic without touching user CRUD"""
    ),
    
    # Testing Issues
    (
        '''def test_user_creation():
    db = Database()
    db.connect()
    db.execute("DELETE FROM users")
    
    user = create_user("john@example.com", "password123")
    
    assert user.id is not None
    assert user.email == "john@example.com"
    
    db.execute("DELETE FROM users")
    db.close()''',
        """**Test Quality Review: Fragile Tests**

🔴 **Real Database Usage (Critical)**
Tests using real database are slow, flaky, and can affect other tests.

🔴 **No Isolation (Critical)**
Deleting all users affects parallel tests and shared environments.

🔴 **Manual Cleanup (High)**
If assertion fails, cleanup code won't run, leaving dirty state.

🟡 **Hardcoded Test Data (Medium)**
Email and password could be extracted for clarity.

```python
import pytest
from unittest.mock import Mock, patch

class TestUserCreation:
    @pytest.fixture
    def mock_db(self):
        \"\"\"Provide mock database for each test.\"\"\"
        with patch('myapp.database.Database') as mock:
            mock.return_value.save.return_value = User(
                id=1,
                email="test@example.com"
            )
            yield mock.return_value
    
    @pytest.fixture
    def user_data(self):
        \"\"\"Standard test user data.\"\"\"
        return {
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        }
    
    def test_creates_user_with_valid_data(self, mock_db, user_data):
        user = create_user(**user_data)
        
        assert user.id is not None
        assert user.email == user_data['email']
        mock_db.save.assert_called_once()
    
    def test_raises_on_duplicate_email(self, mock_db, user_data):
        mock_db.save.side_effect = DuplicateKeyError()
        
        with pytest.raises(DuplicateEmailError):
            create_user(**user_data)
    
    def test_hashes_password_before_saving(self, mock_db, user_data):
        create_user(**user_data)
        
        saved_user = mock_db.save.call_args[0][0]
        assert saved_user.password != user_data['password']
        assert saved_user.password.startswith('$2b$')  # bcrypt

# For integration tests, use a test database with proper isolation:
@pytest.fixture
def test_db():
    db = Database(os.environ['TEST_DATABASE_URL'])
    db.begin_transaction()
    yield db
    db.rollback()  # Always clean up, even on failure
```

**Test Principles Applied**:
- Unit tests use mocks (fast, isolated)
- Fixtures handle setup/teardown
- Each test verifies one behavior
- Integration tests use transactions for isolation"""
    ),
    
    (
        '''def test_everything():
    # Test user creation
    user = create_user("test@test.com", "pass")
    assert user is not None
    
    # Test login
    result = login("test@test.com", "pass")
    assert result['success']
    
    # Test update
    update_user(user.id, {"name": "Test"})
    user = get_user(user.id)
    assert user.name == "Test"
    
    # Test order creation
    order = create_order(user.id, [{"product": 1, "qty": 2}])
    assert order.total > 0
    
    # Test payment
    pay_order(order.id, "card_token")
    order = get_order(order.id)
    assert order.status == "paid"
    
    # Test refund
    refund_order(order.id)
    assert get_order(order.id).status == "refunded"''',
        """**Test Quality Review: Test Design Issues**

🔴 **Multiple Tests in One (Critical)**
This tests 7 different features - if one fails, you don't know which.

🔴 **Test Interdependence (Critical)**
Each step depends on the previous. Can't run in isolation or parallel.

🔴 **No Edge Cases (High)**
Only tests the happy path. What about:
- Invalid email format?
- Wrong password?
- Order with zero items?
- Payment failure?
- Double refund?

🟡 **No Descriptive Names (Medium)**
`test_everything` doesn't describe what's being tested.

```python
class TestUserRegistration:
    def test_creates_user_with_valid_email_and_password(self):
        user = create_user("valid@example.com", "SecurePass1!")
        
        assert user.id is not None
        assert user.email == "valid@example.com"
    
    def test_rejects_invalid_email_format(self):
        with pytest.raises(ValidationError, match="invalid email"):
            create_user("not-an-email", "SecurePass1!")
    
    def test_rejects_weak_password(self):
        with pytest.raises(ValidationError, match="password"):
            create_user("test@example.com", "weak")


class TestAuthentication:
    def test_login_succeeds_with_correct_credentials(self, existing_user):
        result = login(existing_user.email, "correct_password")
        
        assert result['success'] is True
        assert 'token' in result
    
    def test_login_fails_with_wrong_password(self, existing_user):
        result = login(existing_user.email, "wrong_password")
        
        assert result['success'] is False
        assert 'token' not in result
    
    def test_login_fails_for_nonexistent_user(self):
        result = login("nobody@example.com", "any_password")
        
        assert result['success'] is False


class TestOrderPayment:
    def test_successful_payment_marks_order_paid(self, unpaid_order, valid_card):
        pay_order(unpaid_order.id, valid_card)
        
        order = get_order(unpaid_order.id)
        assert order.status == "paid"
    
    def test_payment_failure_keeps_order_unpaid(self, unpaid_order, invalid_card):
        with pytest.raises(PaymentError):
            pay_order(unpaid_order.id, invalid_card)
        
        order = get_order(unpaid_order.id)
        assert order.status == "pending"
    
    def test_cannot_pay_already_paid_order(self, paid_order, valid_card):
        with pytest.raises(InvalidOrderState):
            pay_order(paid_order.id, valid_card)
```

**Key Improvements**:
- One assertion concept per test
- Tests can run independently
- Descriptive names explain what's tested
- Both happy and error paths covered
- Fixtures provide test data isolation"""
    ),
    
    # API Design
    (
        '''# API endpoint
@app.route('/api/data', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_data():
    if request.method == 'GET':
        id = request.args.get('id')
        type = request.args.get('type')
        if id:
            return jsonify(get_item(id))
        elif type:
            return jsonify(get_items_by_type(type))
        else:
            return jsonify(get_all_items())
    elif request.method == 'POST':
        return jsonify(create_item(request.json))
    elif request.method == 'PUT':
        return jsonify(update_item(request.args.get('id'), request.json))
    elif request.method == 'DELETE':
        delete_item(request.args.get('id'))
        return '', 204''',
        """**API Design Review: RESTful Issues**

🔴 **Ambiguous Endpoint (High)**
Single `/api/data` endpoint for all operations violates REST principles.

🟡 **Inconsistent ID Handling (Medium)**
- GET uses query param: `?id=123`
- PUT/DELETE should use path param: `/items/123`

🟡 **Missing Error Handling (Medium)**
No validation or error responses.

🟡 **No HTTP Status Codes (Medium)**
POST should return 201, missing item should return 404.

```python
from flask import Blueprint, request, jsonify, abort

items_bp = Blueprint('items', __name__, url_prefix='/api/items')

@items_bp.route('', methods=['GET'])
def list_items():
    \"\"\"GET /api/items - List all items with optional filtering.\"\"\"
    type_filter = request.args.get('type')
    
    if type_filter:
        items = get_items_by_type(type_filter)
    else:
        items = get_all_items()
    
    return jsonify({
        'items': items,
        'count': len(items)
    })

@items_bp.route('/<int:item_id>', methods=['GET'])
def get_item(item_id: int):
    \"\"\"GET /api/items/:id - Get single item.\"\"\"
    item = find_item(item_id)
    if not item:
        abort(404, description=f"Item {item_id} not found")
    return jsonify(item)

@items_bp.route('', methods=['POST'])
def create_item():
    \"\"\"POST /api/items - Create new item.\"\"\"
    data = request.get_json()
    if not data:
        abort(400, description="Request body required")
    
    errors = validate_item(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    item = save_item(data)
    return jsonify(item), 201

@items_bp.route('/<int:item_id>', methods=['PUT'])
def update_item(item_id: int):
    \"\"\"PUT /api/items/:id - Update existing item.\"\"\"
    item = find_item(item_id)
    if not item:
        abort(404, description=f"Item {item_id} not found")
    
    data = request.get_json()
    updated = save_item({**item, **data, 'id': item_id})
    return jsonify(updated)

@items_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_item(item_id: int):
    \"\"\"DELETE /api/items/:id - Delete item.\"\"\"
    item = find_item(item_id)
    if not item:
        abort(404, description=f"Item {item_id} not found")
    
    remove_item(item_id)
    return '', 204

@items_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': str(error.description)}), 404
```

**REST Best Practices Applied**:
- Resource-based URLs (`/items`, `/items/:id`)
- Proper HTTP methods for each operation
- Appropriate status codes (200, 201, 204, 400, 404)
- Consistent error response format
- Input validation with helpful messages"""
    ),
    
    # Async/Concurrency Issues
    (
        '''shared_counter = 0

async def increment():
    global shared_counter
    current = shared_counter
    await asyncio.sleep(0.001)  # Simulate async work
    shared_counter = current + 1

async def main():
    await asyncio.gather(*[increment() for _ in range(100)])
    print(f"Counter: {shared_counter}")  # Expected 100, actual ~10-20''',
        """**Concurrency Review: Race Condition**

🔴 **Race Condition (Critical)**
Multiple coroutines read `shared_counter`, then all write back the same value.

The sequence:
1. Task A reads counter (0)
2. Task B reads counter (0)
3. Task A writes counter (1)
4. Task B writes counter (1)  <- Lost update!

```python
import asyncio

# Solution 1: Use asyncio.Lock
counter_lock = asyncio.Lock()
shared_counter = 0

async def increment():
    global shared_counter
    async with counter_lock:
        current = shared_counter
        await asyncio.sleep(0.001)
        shared_counter = current + 1

# Solution 2: Use atomic operations with Queue
async def counter_worker(queue: asyncio.Queue, result: dict):
    while True:
        try:
            _ = queue.get_nowait()
            result['count'] += 1
        except asyncio.QueueEmpty:
            break

# Solution 3: Avoid shared state - use reduce pattern
async def increment_and_return():
    await asyncio.sleep(0.001)
    return 1

async def main():
    results = await asyncio.gather(*[
        increment_and_return() 
        for _ in range(100)
    ])
    total = sum(results)  # No shared state!
    print(f"Counter: {total}")  # Always 100

# Best Practice: Prefer message passing over shared state
```

**Key Principles**:
- Avoid shared mutable state in concurrent code
- If sharing is necessary, use locks or atomic operations
- Consider functional patterns (map/reduce) that avoid mutation"""
    ),
    
    # Type Safety
    (
        '''def process_data(data):
    result = {}
    
    if data.get('user'):
        result['name'] = data['user']['profile']['name']
        result['age'] = data['user']['profile']['age']
    
    if data.get('items'):
        result['total'] = sum(i['price'] for i in data['items'])
    
    return result''',
        """**Type Safety Review: Potential Runtime Errors**

🔴 **Missing Null Checks (High)**
Accessing nested properties without checking can raise KeyError or TypeError:
- `data['user']['profile']` - what if profile is None?
- `data['user']['profile']['name']` - what if name is missing?

🟡 **No Type Hints (Medium)**
Can't tell what structure `data` should have.

🟡 **No Default Values (Medium)**
Function behavior with partial data is undefined.

```python
from typing import TypedDict, List, Optional
from dataclasses import dataclass

class Profile(TypedDict, total=False):
    name: str
    age: int

class User(TypedDict, total=False):
    profile: Profile

class Item(TypedDict):
    price: float
    name: str

class InputData(TypedDict, total=False):
    user: User
    items: List[Item]

@dataclass
class ProcessedResult:
    name: Optional[str] = None
    age: Optional[int] = None
    total: float = 0.0

def process_data(data: InputData) -> ProcessedResult:
    \"\"\"Process input data safely with proper null handling.\"\"\"
    result = ProcessedResult()
    
    # Safe nested access with .get() chains
    user = data.get('user')
    if user:
        profile = user.get('profile')
        if profile:
            result.name = profile.get('name')
            result.age = profile.get('age')
    
    # Safe iteration with default empty list
    items = data.get('items', [])
    result.total = sum(item.get('price', 0) for item in items)
    
    return result

# Or use a helper for deep access:
def safe_get(data: dict, *keys, default=None):
    \"\"\"Safely get nested dictionary value.\"\"\"
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
        if data is None:
            return default
    return data

# Usage:
name = safe_get(data, 'user', 'profile', 'name', default='Unknown')
```

**Benefits**:
- Type hints document expected structure
- Runtime errors prevented with safe access
- IDE provides autocomplete and error detection"""
    ),
    
    # Logging Issues
    (
        '''def process_order(order_id, user_id):
    print(f"Processing order {order_id}")
    order = get_order(order_id)
    print(f"Got order: {order}")
    
    try:
        result = charge_payment(order)
        print(f"Payment result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    print("Done!")
    return result''',
        """**Logging Review: Production Issues**

🔴 **Using Print Statements (Critical)**
`print()` is not suitable for production:
- No log levels (can't filter by severity)
- No timestamps
- Can't route to files or monitoring systems
- Synchronous (can slow down application)

🔴 **Logging Sensitive Data (Critical)**
`print(f"Got order: {order}")` may expose PII, payment info, etc.

🟡 **No Structured Data (Medium)**
String formatting loses queryability in log aggregation systems.

```python
import logging
import structlog
from functools import wraps

# Configure structured logging
logger = structlog.get_logger(__name__)

def log_operation(operation_name: str):
    \"\"\"Decorator for consistent operation logging.\"\"\"
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(
                f"{operation_name}_started",
                operation=operation_name,
                args=str(args)[:100]  # Truncate to avoid large logs
            )
            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"{operation_name}_completed",
                    operation=operation_name,
                    success=True
                )
                return result
            except Exception as e:
                logger.error(
                    f"{operation_name}_failed",
                    operation=operation_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True  # Include stack trace
                )
                raise
        return wrapper
    return decorator

@log_operation("process_order")
def process_order(order_id: int, user_id: int):
    logger.info(
        "fetching_order",
        order_id=order_id,
        user_id=user_id
    )
    order = get_order(order_id)
    
    logger.info(
        "charging_payment",
        order_id=order_id,
        amount=order.total  # Log amount, not full order object
    )
    result = charge_payment(order)
    
    logger.info(
        "payment_charged",
        order_id=order_id,
        transaction_id=result.transaction_id
    )
    return result
```

**Logging Best Practices**:
- Use proper logging library with levels (DEBUG, INFO, WARN, ERROR)
- Structure logs as key-value pairs for searchability
- Never log passwords, tokens, or full credit card numbers
- Include correlation IDs for request tracing
- Log at operation boundaries, not every line"""
    ),
    
    # Configuration Issues
    (
        '''# config.py
DATABASE_URL = "postgresql://admin:supersecret123@prod-db.example.com/myapp"
API_KEY = "sk_live_abc123xyz789"
SECRET_KEY = "my-super-secret-key-dont-share"

AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

DEBUG = True''',
        """**Configuration Review: Security & Operations Issues**

🔴 **Hardcoded Secrets (Critical)**
Secrets in source code will be:
- Committed to git history (forever!)
- Visible to anyone with repo access
- Impossible to rotate without code deploy

🔴 **Production Credentials in Code (Critical)**
Live database credentials and API keys exposed.

🔴 **Debug Mode Enabled (High)**
`DEBUG = True` in production exposes stack traces and sensitive info.

```python
# config.py - Load from environment
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            host=os.environ['DB_HOST'],
            port=int(os.environ.get('DB_PORT', '5432')),
            name=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
        )

@dataclass  
class AppConfig:
    debug: bool
    secret_key: str
    api_key: str
    database: DatabaseConfig
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        return cls(
            debug=os.environ.get('DEBUG', 'false').lower() == 'true',
            secret_key=os.environ['SECRET_KEY'],
            api_key=os.environ['API_KEY'],
            database=DatabaseConfig.from_env(),
        )

# Load config
config = AppConfig.from_env()

# .env.example (commit this, not .env!)
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=myapp_dev
# DB_USER=myapp
# DB_PASSWORD=<set-in-env>
# SECRET_KEY=<generate-with-secrets-module>
# API_KEY=<get-from-provider>
# DEBUG=false
```

**Production Checklist**:
- [ ] No secrets in code or git history
- [ ] Use environment variables or secret manager
- [ ] Different credentials per environment
- [ ] DEBUG=false in production
- [ ] Secrets rotated regularly
- [ ] Principle of least privilege for DB users"""
    ),
    
    # Memory Management
    (
        '''class DataProcessor:
    def __init__(self):
        self.cache = {}
        self.history = []
    
    def process(self, data):
        result = expensive_computation(data)
        self.cache[data['id']] = result
        self.history.append({'data': data, 'result': result})
        return result
    
    def get_all_history(self):
        return self.history''',
        """**Memory Management Review: Memory Leak Risk**

🔴 **Unbounded Cache Growth (High)**
`self.cache` grows without limit - memory leak in long-running processes.

🔴 **Unbounded History (High)**
`self.history` stores every processed item forever.

🟡 **Storing Full Objects (Medium)**
Keeping references to `data` and `result` prevents garbage collection.

```python
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import weakref

class LRUCache:
    \"\"\"Bounded cache with LRU eviction.\"\"\"
    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
    
    def get(self, key) -> Optional[Any]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    
    def set(self, key, value) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

@dataclass
class HistoryEntry:
    \"\"\"Lightweight history entry - only store IDs, not full objects.\"\"\"
    data_id: str
    timestamp: datetime
    success: bool

class DataProcessor:
    MAX_CACHE_SIZE = 10000
    MAX_HISTORY_SIZE = 1000
    
    def __init__(self):
        self._cache = LRUCache(max_size=self.MAX_CACHE_SIZE)
        self._history: list[HistoryEntry] = []
    
    def process(self, data: dict) -> Any:
        # Check cache first
        cached = self._cache.get(data['id'])
        if cached is not None:
            return cached
        
        result = expensive_computation(data)
        self._cache.set(data['id'], result)
        
        # Store minimal history
        self._add_history(HistoryEntry(
            data_id=data['id'],
            timestamp=datetime.now(),
            success=True
        ))
        
        return result
    
    def _add_history(self, entry: HistoryEntry) -> None:
        self._history.append(entry)
        # Trim old history
        if len(self._history) > self.MAX_HISTORY_SIZE:
            self._history = self._history[-self.MAX_HISTORY_SIZE:]
    
    def get_recent_history(self, count: int = 100) -> list[HistoryEntry]:
        return self._history[-count:]
    
    def clear_cache(self) -> None:
        \"\"\"Allow manual cache clearing if needed.\"\"\"
        self._cache = LRUCache(max_size=self.MAX_CACHE_SIZE)
```

**Memory Best Practices**:
- Bound all caches and collections
- Use LRU eviction for caches
- Store IDs/references instead of full objects when possible
- Provide methods to clear caches
- Monitor memory usage in production"""
    ),
    
    # Documentation Issues
    (
        '''def transform(d, k, m, f=None, s=True):
    r = {}
    for i in d:
        if k in i:
            v = i[k]
            if f:
                v = f(v)
            if m.get(v):
                r[v] = m[v](i) if s else i
    return r''',
        """**Documentation Review: Incomprehensible Code**

🔴 **No Documentation (Critical)**
Without docs or clear names, this code requires reverse engineering to understand.

🔴 **Single Letter Names (Critical)**
`d`, `k`, `m`, `f`, `s`, `r`, `i`, `v` - impossible to understand purpose.

🔴 **Complex Logic Undocumented (High)**
Multiple conditionals with unclear purpose.

```python
from typing import TypeVar, Callable, Dict, List, Any, Optional

T = TypeVar('T')
K = TypeVar('K')

def group_and_transform(
    items: List[Dict[str, Any]],
    group_key: str,
    transformers: Dict[K, Callable[[Dict], T]],
    key_transform: Optional[Callable[[Any], K]] = None,
    apply_transformer: bool = True
) -> Dict[K, T]:
    \"\"\"Group items by a key and apply transformations.
    
    Takes a list of dictionaries, groups them by a specified key,
    and optionally transforms each group using provided transformer functions.
    
    Args:
        items: List of dictionaries to process.
        group_key: The key in each dict to group by.
        transformers: Dict mapping group values to transformer functions.
            Each transformer receives the original dict and returns
            the transformed value.
        key_transform: Optional function to transform the group key value
            before looking up the transformer. Useful for normalizing keys.
        apply_transformer: If True, apply the transformer function.
            If False, return the original dict unchanged.
    
    Returns:
        Dictionary mapping group keys to transformed values.
        Only includes items whose group key has a matching transformer.
    
    Example:
        >>> items = [
        ...     {'type': 'user', 'name': 'Alice', 'age': 30},
        ...     {'type': 'user', 'name': 'Bob', 'age': 25},
        ...     {'type': 'admin', 'name': 'Charlie', 'level': 5},
        ... ]
        >>> transformers = {
        ...     'user': lambda d: {'name': d['name'], 'adult': d['age'] >= 18},
        ...     'admin': lambda d: {'name': d['name'], 'admin_level': d['level']},
        ... }
        >>> group_and_transform(items, 'type', transformers)
        {'user': {'name': 'Bob', 'adult': True}, 'admin': {'name': 'Charlie', 'admin_level': 5}}
    
    Note:
        If multiple items have the same group key, only the last one
        is included in the result. Consider using group_all() if you
        need to preserve all items.
    \"\"\"
    result: Dict[K, T] = {}
    
    for item in items:
        if group_key not in item:
            continue
            
        key_value = item[group_key]
        
        if key_transform:
            key_value = key_transform(key_value)
        
        transformer = transformers.get(key_value)
        if transformer:
            if apply_transformer:
                result[key_value] = transformer(item)
            else:
                result[key_value] = item
    
    return result
```

**Documentation Checklist**:
- [ ] Descriptive function/variable names
- [ ] Type hints for all parameters and return
- [ ] Docstring with purpose, args, returns
- [ ] Example usage
- [ ] Note any non-obvious behavior"""
    ),
    
    # Dependency Injection Issues
    (
        '''class OrderService:
    def __init__(self):
        self.db = PostgresDatabase()
        self.payment = StripePaymentGateway()
        self.email = SendGridEmailService()
        self.inventory = WarehouseInventoryService()
    
    def create_order(self, items, customer_id):
        order = Order(items=items, customer_id=customer_id)
        self.db.save(order)
        self.inventory.reserve(items)
        return order''',
        """**Architecture Review: Tight Coupling**

🔴 **Hard-Coded Dependencies (High)**
Concrete implementations are instantiated directly, making:
- Unit testing impossible (can't mock)
- Switching implementations requires code changes
- Circular dependency risks

🟡 **No Interface Abstraction (Medium)**
No contracts defining what services need to do.

```python
from abc import ABC, abstractmethod
from typing import List, Protocol

# Define interfaces (contracts)
class OrderRepository(Protocol):
    def save(self, order: Order) -> Order: ...
    def find_by_id(self, order_id: int) -> Optional[Order]: ...

class PaymentGateway(Protocol):
    def charge(self, amount: float, payment_method: str) -> PaymentResult: ...

class EmailService(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...

class InventoryService(Protocol):
    def reserve(self, items: List[OrderItem]) -> bool: ...
    def release(self, items: List[OrderItem]) -> None: ...

class OrderService:
    \"\"\"Order service with injected dependencies.\"\"\"
    
    def __init__(
        self,
        repository: OrderRepository,
        payment: PaymentGateway,
        email: EmailService,
        inventory: InventoryService,
    ):
        self._repository = repository
        self._payment = payment
        self._email = email
        self._inventory = inventory
    
    def create_order(self, items: List[OrderItem], customer_id: int) -> Order:
        order = Order(items=items, customer_id=customer_id)
        self._repository.save(order)
        self._inventory.reserve(items)
        return order

# Composition root - wire up dependencies
def create_order_service() -> OrderService:
    return OrderService(
        repository=PostgresOrderRepository(get_db_connection()),
        payment=StripePaymentGateway(os.environ['STRIPE_KEY']),
        email=SendGridEmailService(os.environ['SENDGRID_KEY']),
        inventory=WarehouseInventoryService(warehouse_url),
    )

# For testing - inject mocks
def test_create_order():
    mock_repo = Mock(spec=OrderRepository)
    mock_inventory = Mock(spec=InventoryService)
    
    service = OrderService(
        repository=mock_repo,
        payment=Mock(),
        email=Mock(),
        inventory=mock_inventory,
    )
    
    order = service.create_order([item], customer_id=1)
    
    mock_repo.save.assert_called_once()
    mock_inventory.reserve.assert_called_once()
```

**Benefits**:
- Testable: inject mocks for unit tests
- Flexible: swap implementations without code changes
- Clear contracts: interfaces document expectations
- Loose coupling: services don't know implementation details"""
    ),
    
    # Input Validation
    (
        '''@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    user = User(
        name=data['name'],
        email=data['email'],
        age=data['age'],
        role=data.get('role', 'user')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201''',
        """**Input Validation Review: Missing Validation**

🔴 **No Input Validation (Critical)**
User input goes directly to the database. Potential issues:
- Missing required fields crash with KeyError
- Invalid email formats stored
- Negative ages accepted
- SQL injection if ORM is bypassed
- XSS if name contains scripts

🔴 **No Type Checking (High)**
`age` could be a string, causing type errors later.

🟡 **Privilege Escalation Risk (Medium)**
Users can set their own role - could create admin accounts!

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    USER = 'user'
    MODERATOR = 'moderator'
    # Note: admin cannot be self-assigned

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)
    role: UserRole = UserRole.USER  # Default, not from input
    
    @validator('name')
    def sanitize_name(cls, v):
        # Remove potential XSS
        import html
        return html.escape(v.strip())
    
    @validator('role', pre=True, always=True)
    def force_default_role(cls, v):
        # Users cannot set their own role on creation
        return UserRole.USER
    
    class Config:
        extra = 'forbid'  # Reject unknown fields

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = CreateUserRequest(**request.json)
    except ValidationError as e:
        return jsonify({'errors': e.errors()}), 400
    
    # Check for duplicate email
    if User.query.filter_by(email=data.email).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    user = User(
        name=data.name,
        email=data.email,
        age=data.age,
        role=data.role.value
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201
```

**Validation Checklist**:
- [ ] Required fields validated
- [ ] Types checked (int, string, etc.)
- [ ] Ranges/lengths enforced
- [ ] Email format validated
- [ ] XSS prevention (escape HTML)
- [ ] Privilege fields protected
- [ ] Duplicate checks performed"""
    ),
    
    # Resource Management
    (
        '''def process_files(file_paths):
    results = []
    for path in file_paths:
        f = open(path, 'r')
        content = f.read()
        results.append(process_content(content))
    return results

def download_data(urls):
    for url in urls:
        conn = http.client.HTTPSConnection(urlparse(url).netloc)
        conn.request('GET', urlparse(url).path)
        response = conn.getresponse()
        yield response.read()''',
        """**Resource Management Review: Resource Leaks**

🔴 **Unclosed File Handles (Critical)**
Files are opened but never closed. In long-running processes:
- File handles exhausted (OS limit)
- Data not flushed to disk
- Files locked on Windows

🔴 **Unclosed Connections (Critical)**
HTTP connections left open, exhausting connection pool.

```python
from contextlib import contextmanager
from typing import Iterator, List
import httpx

# Solution 1: Context managers (recommended)
def process_files(file_paths: List[str]) -> List[Any]:
    results = []
    for path in file_paths:
        with open(path, 'r') as f:  # Auto-closes
            content = f.read()
            results.append(process_content(content))
    return results

# Solution 2: For generators, use try/finally
def download_data(urls: List[str]) -> Iterator[bytes]:
    with httpx.Client() as client:  # Connection pooling + auto-close
        for url in urls:
            response = client.get(url)
            response.raise_for_status()
            yield response.content

# Solution 3: Custom context manager for complex resources
@contextmanager
def managed_resource(config):
    \"\"\"Context manager for resource with setup/teardown.\"\"\"
    resource = Resource(config)
    resource.connect()
    try:
        yield resource
    finally:
        resource.disconnect()

# Solution 4: Use pathlib for cleaner file operations
from pathlib import Path

def process_files(file_paths: List[str]) -> List[Any]:
    return [
        process_content(Path(path).read_text())
        for path in file_paths
    ]

# Solution 5: Async with proper cleanup
async def download_data_async(urls: List[str]) -> List[bytes]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.content for r in responses]
```

**Resource Management Rules**:
- Always use `with` statements for files, connections, locks
- Use `try/finally` in generators
- Use connection pools for HTTP clients
- Set timeouts on all network operations
- Consider using `atexit` for application-level cleanup"""
    ),
    
    # Code Duplication in React
    (
        '''function UserList() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        fetch('/api/users')
            .then(res => res.json())
            .then(data => { setUsers(data); setLoading(false); })
            .catch(err => { setError(err); setLoading(false); });
    }, []);
    
    if (loading) return <Spinner />;
    if (error) return <Error message={error.message} />;
    return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}

function ProductList() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        fetch('/api/products')
            .then(res => res.json())
            .then(data => { setProducts(data); setLoading(false); })
            .catch(err => { setError(err); setLoading(false); });
    }, []);
    
    if (loading) return <Spinner />;
    if (error) return <Error message={error.message} />;
    return <ul>{products.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
}''',
        """**Code Duplication Review: DRY Violation**

🔴 **Duplicated Fetch Logic (High)**
Same loading/error/data pattern repeated in every component.

🟡 **No Error Handling Details (Medium)**
Generic error handling doesn't distinguish error types.

🟡 **No Retry or Caching (Low)**
Each mount triggers a new fetch.

```typescript
// Custom hook for data fetching
function useFetch<T>(url: string) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    
    useEffect(() => {
        const controller = new AbortController();
        
        async function fetchData() {
            try {
                setLoading(true);
                setError(null);
                
                const response = await fetch(url, {
                    signal: controller.signal
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const json = await response.json();
                setData(json);
            } catch (err) {
                if (err instanceof Error && err.name !== 'AbortError') {
                    setError(err);
                }
            } finally {
                setLoading(false);
            }
        }
        
        fetchData();
        
        return () => controller.abort(); // Cleanup on unmount
    }, [url]);
    
    return { data, loading, error, refetch: () => setLoading(true) };
}

// Generic list component
interface ListProps<T> {
    items: T[];
    renderItem: (item: T) => React.ReactNode;
    keyExtractor: (item: T) => string;
}

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
    return (
        <ul>
            {items.map(item => (
                <li key={keyExtractor(item)}>{renderItem(item)}</li>
            ))}
        </ul>
    );
}

// Clean, DRY components
function UserList() {
    const { data: users, loading, error } = useFetch<User[]>('/api/users');
    
    if (loading) return <Spinner />;
    if (error) return <Error message={error.message} />;
    
    return (
        <List
            items={users ?? []}
            keyExtractor={u => u.id}
            renderItem={u => u.name}
        />
    );
}

function ProductList() {
    const { data: products, loading, error } = useFetch<Product[]>('/api/products');
    
    if (loading) return <Spinner />;
    if (error) return <Error message={error.message} />;
    
    return (
        <List
            items={products ?? []}
            keyExtractor={p => p.id}
            renderItem={p => <>{p.name} - ${p.price}</>}
        />
    );
}
```

**For production, consider using TanStack Query (React Query)**:
- Built-in caching
- Automatic refetching
- Deduplication
- Optimistic updates"""
    ),
    
    # Thread Safety Issues
    (
        '''class Counter:
    def __init__(self):
        self.value = 0
    
    def increment(self):
        self.value += 1
    
    def decrement(self):
        self.value -= 1

# Shared across threads
counter = Counter()

def worker():
    for _ in range(1000):
        counter.increment()

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
print(counter.value)  # Expected: 10000, Actual: 6000-9000 (varies!)''',
        """**Thread Safety Review: Race Conditions**

🔴 **Non-Atomic Operations (Critical)**
`self.value += 1` is NOT atomic in Python. It's actually:
1. Read value
2. Add 1
3. Write value

Multiple threads can read the same value before any writes.

🔴 **No Synchronization (Critical)**
Shared mutable state accessed without locks.

```python
import threading
from typing import Optional

# Solution 1: Use Lock
class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    @property
    def value(self) -> int:
        with self._lock:
            return self._value
    
    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value
    
    def decrement(self) -> int:
        with self._lock:
            self._value -= 1
            return self._value

# Solution 2: Use RLock for reentrant locking
class ReentrantCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.RLock()
    
    def add(self, amount: int) -> int:
        with self._lock:
            self._value += amount
            return self._value
    
    def increment_twice(self) -> int:
        with self._lock:
            self.add(1)  # Can acquire same lock again
            return self.add(1)

# Solution 3: Use queue for producer/consumer
from queue import Queue

def counter_with_queue():
    results = Queue()
    
    def worker(work_queue, result_queue):
        count = 0
        while True:
            item = work_queue.get()
            if item is None:
                break
            count += 1
        result_queue.put(count)
    
    work_queue = Queue()
    # ... dispatch work

# Solution 4: Use concurrent.futures
from concurrent.futures import ThreadPoolExecutor

def parallel_count(items):
    def count_batch(batch):
        return sum(1 for item in batch if process(item))
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        batches = [items[i::4] for i in range(4)]
        counts = executor.map(count_batch, batches)
        return sum(counts)
```

**Thread Safety Principles**:
- Immutable data is always thread-safe
- Minimize shared mutable state
- Use locks/synchronization for shared state
- Consider thread-local storage for per-thread data
- Use higher-level abstractions (Queue, concurrent.futures)"""
    ),
    
    # Hardcoded Values
    (
        '''def send_notification(user_id, message):
    user = get_user(user_id)
    
    # Send email
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.login('notifications@mycompany.com', 'password123')
    smtp.sendmail(
        'notifications@mycompany.com',
        user.email,
        message
    )
    
    # Send SMS for important users
    if user.plan == 'premium':
        requests.post(
            'https://api.twilio.com/2010-04-01/Accounts/AC123/Messages.json',
            auth=('AC123', 'auth_token_456'),
            data={
                'From': '+15551234567',
                'To': user.phone,
                'Body': message[:160]
            }
        )
    
    # Retry up to 3 times with 5 second delay
    for i in range(3):
        try:
            log_notification(user_id, message)
            break
        except:
            time.sleep(5)''',
        """**Configuration Review: Hardcoded Values Everywhere**

🔴 **Hardcoded Credentials (Critical)**
Email password and Twilio auth token in source code.

🔴 **Hardcoded URLs/IDs (High)**
API endpoints, account IDs, phone numbers should be configurable.

🟡 **Magic Numbers (Medium)**
`3`, `5`, `160` without context.

🟡 **Business Logic Hardcoded (Medium)**
`'premium'` plan name embedded in code.

```python
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class EmailConfig:
    host: str = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    port: int = int(os.getenv('SMTP_PORT', '587'))
    username: str = os.getenv('SMTP_USERNAME', '')
    password: str = os.getenv('SMTP_PASSWORD', '')
    from_address: str = os.getenv('SMTP_FROM', '')

@dataclass
class SMSConfig:
    account_sid: str = os.getenv('TWILIO_ACCOUNT_SID', '')
    auth_token: str = os.getenv('TWILIO_AUTH_TOKEN', '')
    from_number: str = os.getenv('TWILIO_FROM_NUMBER', '')
    max_length: int = 160
    api_url: str = 'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'

@dataclass
class RetryConfig:
    max_attempts: int = 3
    delay_seconds: int = 5

@dataclass
class NotificationConfig:
    email: EmailConfig
    sms: SMSConfig
    retry: RetryConfig
    sms_eligible_plans: tuple = ('premium', 'enterprise')

class NotificationService:
    def __init__(self, config: NotificationConfig):
        self.config = config
    
    def send(self, user_id: int, message: str) -> None:
        user = get_user(user_id)
        
        self._send_email(user.email, message)
        
        if self._is_sms_eligible(user):
            self._send_sms(user.phone, message)
        
        self._log_with_retry(user_id, message)
    
    def _is_sms_eligible(self, user) -> bool:
        return user.plan in self.config.sms_eligible_plans
    
    def _send_email(self, to: str, message: str) -> None:
        cfg = self.config.email
        smtp = smtplib.SMTP(cfg.host, cfg.port)
        smtp.login(cfg.username, cfg.password)
        smtp.sendmail(cfg.from_address, to, message)
    
    def _send_sms(self, to: str, message: str) -> None:
        cfg = self.config.sms
        truncated = message[:cfg.max_length]
        requests.post(
            cfg.api_url.format(sid=cfg.account_sid),
            auth=(cfg.account_sid, cfg.auth_token),
            data={'From': cfg.from_number, 'To': to, 'Body': truncated}
        )
    
    def _log_with_retry(self, user_id: int, message: str) -> None:
        cfg = self.config.retry
        for attempt in range(cfg.max_attempts):
            try:
                log_notification(user_id, message)
                return
            except Exception as e:
                if attempt < cfg.max_attempts - 1:
                    time.sleep(cfg.delay_seconds)
                else:
                    raise
```

**Configuration Best Practices**:
- All configurable values from environment/config files
- Sensible defaults where appropriate
- Group related config into dataclasses
- Document what each config does
- Never commit secrets to source control"""
    ),
    
    # Premature Optimization
    (
        '''# "Optimized" string concatenation
def build_report(items):
    parts = []
    for item in items:
        parts.append(str(item.id))
        parts.append(',')
        parts.append(item.name)
        parts.append(',')
        parts.append(str(item.value))
        parts.append('\\n')
    return ''.join(parts)

# "Optimized" with bitwise operations
def is_even(n):
    return not (n & 1)

def multiply_by_two(n):
    return n << 1

# "Optimized" early exit everywhere
def process(data):
    if not data: return None
    if len(data) == 0: return None
    if data[0] is None: return None
    result = data[0]
    if result == 0: return 0
    return result * 2''',
        """**Code Review: Premature Optimization**

🟡 **Unnecessary Micro-Optimizations (Medium)**
These "optimizations" hurt readability with negligible performance benefit.

**String Building** - Python's `join` is fast, but this is overkill for most cases:
```python
# Original is harder to read and maintain
# For simple cases, f-strings are fine and readable:
def build_report(items):
    lines = [f"{item.id},{item.name},{item.value}" for item in items]
    return '\\n'.join(lines)

# Or use csv module for proper CSV:
import csv
import io

def build_report(items):
    output = io.StringIO()
    writer = csv.writer(output)
    for item in items:
        writer.writerow([item.id, item.name, item.value])
    return output.getvalue()
```

**Bitwise Operations** - Cute but obscures intent:
```python
# Clever but confusing
def is_even(n): return not (n & 1)
def multiply_by_two(n): return n << 1

# Clear and just as fast (compiler optimizes these)
def is_even(n): return n % 2 == 0
def double(n): return n * 2
```

**Excessive Guard Clauses**:
```python
# Over-engineered guards
def process(data):
    if not data: return None
    if len(data) == 0: return None  # Redundant!
    if data[0] is None: return None
    result = data[0]
    if result == 0: return 0  # Unnecessary special case
    return result * 2

# Simplified - clearer intent
def process(data):
    if not data or data[0] is None:
        return None
    return data[0] * 2
```

**Optimization Guidelines**:
1. Measure before optimizing
2. Optimize algorithms, not micro-operations
3. Readability > tiny performance gains
4. Trust the compiler/interpreter
5. Profile production code to find real bottlenecks"""
    ),
    
    # Missing Abstractions
    (
        '''def create_invoice(order):
    # Calculate totals
    subtotal = 0
    for item in order.items:
        subtotal += item.price * item.quantity
    
    # Apply discounts
    discount = 0
    if order.coupon:
        if order.coupon.type == 'percentage':
            discount = subtotal * (order.coupon.value / 100)
        elif order.coupon.type == 'fixed':
            discount = min(order.coupon.value, subtotal)
    
    # Calculate tax
    taxable = subtotal - discount
    if order.shipping_address.state == 'CA':
        tax_rate = 0.0725
    elif order.shipping_address.state == 'NY':
        tax_rate = 0.08
    elif order.shipping_address.state == 'TX':
        tax_rate = 0.0625
    else:
        tax_rate = 0
    tax = taxable * tax_rate
    
    # Calculate shipping
    if subtotal > 100:
        shipping = 0
    elif order.shipping_method == 'express':
        shipping = 15.99
    else:
        shipping = 5.99
    
    return {
        'subtotal': subtotal,
        'discount': discount,
        'tax': tax,
        'shipping': shipping,
        'total': taxable + tax + shipping
    }''',
        """**Architecture Review: Missing Abstractions**

🟡 **Primitive Obsession (High)**
Complex domain concepts represented as raw calculations.

🟡 **Mixed Concerns (High)**
Pricing, tax, shipping, discounts all mixed in one function.

🟡 **Hardcoded Business Rules (Medium)**
Tax rates, shipping thresholds embedded in code.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

# Value Objects
@dataclass(frozen=True)
class Money:
    amount: Decimal
    
    def __add__(self, other: 'Money') -> 'Money':
        return Money(self.amount + other.amount)
    
    def __sub__(self, other: 'Money') -> 'Money':
        return Money(self.amount - other.amount)
    
    def __mul__(self, factor: Decimal) -> 'Money':
        return Money(self.amount * factor)
    
    @classmethod
    def zero(cls) -> 'Money':
        return cls(Decimal('0'))

# Domain Services
class DiscountCalculator(ABC):
    @abstractmethod
    def calculate(self, subtotal: Money, coupon: Optional['Coupon']) -> Money:
        pass

class PercentageDiscount(DiscountCalculator):
    def calculate(self, subtotal: Money, coupon: Optional['Coupon']) -> Money:
        if not coupon or coupon.type != 'percentage':
            return Money.zero()
        return subtotal * (coupon.value / 100)

class TaxCalculator:
    TAX_RATES = {
        'CA': Decimal('0.0725'),
        'NY': Decimal('0.08'),
        'TX': Decimal('0.0625'),
    }
    
    def calculate(self, amount: Money, state: str) -> Money:
        rate = self.TAX_RATES.get(state, Decimal('0'))
        return amount * rate

class ShippingCalculator:
    FREE_SHIPPING_THRESHOLD = Money(Decimal('100'))
    STANDARD_RATE = Money(Decimal('5.99'))
    EXPRESS_RATE = Money(Decimal('15.99'))
    
    def calculate(self, subtotal: Money, method: str) -> Money:
        if subtotal.amount >= self.FREE_SHIPPING_THRESHOLD.amount:
            return Money.zero()
        return self.EXPRESS_RATE if method == 'express' else self.STANDARD_RATE

# Invoice Builder
@dataclass
class Invoice:
    subtotal: Money
    discount: Money
    tax: Money
    shipping: Money
    
    @property
    def total(self) -> Money:
        return self.subtotal - self.discount + self.tax + self.shipping

class InvoiceBuilder:
    def __init__(
        self,
        discount_calc: DiscountCalculator,
        tax_calc: TaxCalculator,
        shipping_calc: ShippingCalculator,
    ):
        self._discount = discount_calc
        self._tax = tax_calc
        self._shipping = shipping_calc
    
    def build(self, order: 'Order') -> Invoice:
        subtotal = self._calculate_subtotal(order.items)
        discount = self._discount.calculate(subtotal, order.coupon)
        taxable = subtotal - discount
        tax = self._tax.calculate(taxable, order.shipping_address.state)
        shipping = self._shipping.calculate(subtotal, order.shipping_method)
        
        return Invoice(subtotal, discount, tax, shipping)
    
    def _calculate_subtotal(self, items: List['OrderItem']) -> Money:
        return sum(
            (Money(item.price) * item.quantity for item in items),
            Money.zero()
        )
```

**Benefits of Abstractions**:
- Each concept is testable in isolation
- Business rules are configurable
- Easy to add new discount/tax/shipping types
- Code reads like business language"""
    ),
]


def generate_examples() -> List[Dict]:
    """Generate training examples from code review data."""
    examples = []
    
    for code_to_review, review_feedback in CODE_REVIEW_EXAMPLES:
        response = {
            "action": "concepts",
            "review_type": "code_review",
            "feedback": review_feedback
        }
        
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": f"Please review this code and provide feedback:\n\n```\n{code_to_review}\n```",
            "response": json.dumps(response, indent=2)
        })
    
    return examples


def save_examples(examples: List[Dict], filename: str = "code_review.jsonl"):
    """Save examples to JSONL file."""
    output_file = OUTPUT_DIR / filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"Saved {len(examples)} examples to {output_file}")


if __name__ == "__main__":
    examples = generate_examples()
    save_examples(examples)

