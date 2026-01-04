#!/usr/bin/env python3
"""
Generate code refactoring training examples.

Focuses on "provide_code" response types - showing before/after
refactoring patterns that AJ should be able to apply.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple

# Output path
OUTPUT_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, a technical AI assistant created by AJ Westerfield. You specialize in code refactoring and improvement. When asked to refactor code, you analyze the issues, explain the improvements, and provide clean, refactored code following best practices."""

# Refactoring examples: (instruction, before_code, after_code, explanation)
REFACTORING_EXAMPLES: List[Tuple[str, str, str, str]] = [
    # Extract Method
    (
        "Refactor this function to extract the validation logic into a separate method",
        '''def process_user_data(data):
    # Validate email
    if not data.get('email'):
        raise ValueError("Email is required")
    if '@' not in data['email']:
        raise ValueError("Invalid email format")
    if len(data['email']) > 255:
        raise ValueError("Email too long")
    
    # Validate name
    if not data.get('name'):
        raise ValueError("Name is required")
    if len(data['name']) < 2:
        raise ValueError("Name too short")
    if len(data['name']) > 100:
        raise ValueError("Name too long")
    
    # Process
    return {
        'email': data['email'].lower().strip(),
        'name': data['name'].strip().title()
    }''',
        '''def validate_email(email: str) -> None:
    """Validate email format and length."""
    if not email:
        raise ValueError("Email is required")
    if '@' not in email:
        raise ValueError("Invalid email format")
    if len(email) > 255:
        raise ValueError("Email too long")

def validate_name(name: str) -> None:
    """Validate name length."""
    if not name:
        raise ValueError("Name is required")
    if len(name) < 2:
        raise ValueError("Name too short")
    if len(name) > 100:
        raise ValueError("Name too long")

def process_user_data(data: dict) -> dict:
    """Process and normalize user data."""
    validate_email(data.get('email', ''))
    validate_name(data.get('name', ''))
    
    return {
        'email': data['email'].lower().strip(),
        'name': data['name'].strip().title()
    }''',
        "Extracted validation into separate functions for single responsibility, reusability, and easier testing."
    ),
    
    # Replace Magic Numbers
    (
        "Refactor this code to replace magic numbers with named constants",
        '''def calculate_shipping(weight, distance):
    if weight <= 1:
        base_cost = 5.99
    elif weight <= 5:
        base_cost = 9.99
    elif weight <= 20:
        base_cost = 14.99
    else:
        base_cost = 24.99
    
    if distance > 500:
        base_cost *= 1.5
    elif distance > 100:
        base_cost *= 1.2
    
    if weight > 50:
        base_cost += 25.00
    
    return round(base_cost, 2)''',
        '''# Weight thresholds (kg)
WEIGHT_LIGHT = 1
WEIGHT_MEDIUM = 5
WEIGHT_HEAVY = 20
WEIGHT_OVERSIZED = 50

# Base shipping costs ($)
COST_LIGHT = 5.99
COST_MEDIUM = 9.99
COST_HEAVY = 14.99
COST_EXTRA_HEAVY = 24.99
OVERSIZED_SURCHARGE = 25.00

# Distance thresholds (miles)
DISTANCE_LONG = 500
DISTANCE_MEDIUM = 100

# Distance multipliers
MULTIPLIER_LONG = 1.5
MULTIPLIER_MEDIUM = 1.2

def calculate_shipping(weight: float, distance: float) -> float:
    """Calculate shipping cost based on weight and distance."""
    if weight <= WEIGHT_LIGHT:
        base_cost = COST_LIGHT
    elif weight <= WEIGHT_MEDIUM:
        base_cost = COST_MEDIUM
    elif weight <= WEIGHT_HEAVY:
        base_cost = COST_HEAVY
    else:
        base_cost = COST_EXTRA_HEAVY
    
    if distance > DISTANCE_LONG:
        base_cost *= MULTIPLIER_LONG
    elif distance > DISTANCE_MEDIUM:
        base_cost *= MULTIPLIER_MEDIUM
    
    if weight > WEIGHT_OVERSIZED:
        base_cost += OVERSIZED_SURCHARGE
    
    return round(base_cost, 2)''',
        "Named constants make the business rules clear, easy to modify, and self-documenting."
    ),
    
    # Guard Clauses / Early Return
    (
        "Refactor this deeply nested function using guard clauses",
        '''def process_order(order):
    result = None
    if order is not None:
        if order.get('items'):
            if len(order['items']) > 0:
                if order.get('customer_id'):
                    if order.get('payment_method'):
                        total = sum(item['price'] * item['quantity'] for item in order['items'])
                        if total > 0:
                            result = {
                                'order_id': generate_id(),
                                'customer_id': order['customer_id'],
                                'total': total,
                                'status': 'pending'
                            }
                        else:
                            result = {'error': 'Invalid total'}
                    else:
                        result = {'error': 'Payment method required'}
                else:
                    result = {'error': 'Customer ID required'}
            else:
                result = {'error': 'No items in order'}
        else:
            result = {'error': 'Items required'}
    else:
        result = {'error': 'Order is required'}
    return result''',
        '''def process_order(order: dict) -> dict:
    """Process an order with early validation returns."""
    if order is None:
        return {'error': 'Order is required'}
    
    if not order.get('items'):
        return {'error': 'Items required'}
    
    if len(order['items']) == 0:
        return {'error': 'No items in order'}
    
    if not order.get('customer_id'):
        return {'error': 'Customer ID required'}
    
    if not order.get('payment_method'):
        return {'error': 'Payment method required'}
    
    total = sum(item['price'] * item['quantity'] for item in order['items'])
    
    if total <= 0:
        return {'error': 'Invalid total'}
    
    return {
        'order_id': generate_id(),
        'customer_id': order['customer_id'],
        'total': total,
        'status': 'pending'
    }''',
        "Guard clauses eliminate nesting, making the happy path clear and code much more readable."
    ),
    
    # Simplify Conditionals
    (
        "Simplify these complex conditional expressions",
        '''def get_discount(user, cart_total, is_holiday):
    discount = 0
    if user is not None:
        if user.membership == 'gold':
            if cart_total >= 100:
                discount = 0.20
            else:
                discount = 0.15
        elif user.membership == 'silver':
            if cart_total >= 100:
                discount = 0.10
            else:
                discount = 0.05
        else:
            if cart_total >= 100:
                discount = 0.05
            else:
                discount = 0
    
    if is_holiday == True:
        discount = discount + 0.05
    
    return discount''',
        '''# Discount rates by membership level
DISCOUNT_RATES = {
    'gold': {'high_value': 0.20, 'standard': 0.15},
    'silver': {'high_value': 0.10, 'standard': 0.05},
    'basic': {'high_value': 0.05, 'standard': 0.00},
}
HIGH_VALUE_THRESHOLD = 100
HOLIDAY_BONUS = 0.05

def get_discount(user, cart_total: float, is_holiday: bool) -> float:
    """Calculate discount based on membership, cart value, and holidays."""
    if user is None:
        return 0.0
    
    membership = getattr(user, 'membership', 'basic')
    rates = DISCOUNT_RATES.get(membership, DISCOUNT_RATES['basic'])
    
    tier = 'high_value' if cart_total >= HIGH_VALUE_THRESHOLD else 'standard'
    discount = rates[tier]
    
    if is_holiday:
        discount += HOLIDAY_BONUS
    
    return discount''',
        "Used a lookup table to replace nested conditionals, making rates easily configurable."
    ),
    
    # Remove Duplicate Code (DRY)
    (
        "Refactor to remove the duplicate code in these handlers",
        '''def handle_create_user(request):
    try:
        data = json.loads(request.body)
        if not data.get('email'):
            return JsonResponse({'error': 'Email required'}, status=400)
        if not data.get('name'):
            return JsonResponse({'error': 'Name required'}, status=400)
        user = User.objects.create(**data)
        logger.info(f"Created user {user.id}")
        return JsonResponse({'id': user.id, 'status': 'created'}, status=201)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def handle_create_product(request):
    try:
        data = json.loads(request.body)
        if not data.get('name'):
            return JsonResponse({'error': 'Name required'}, status=400)
        if not data.get('price'):
            return JsonResponse({'error': 'Price required'}, status=400)
        product = Product.objects.create(**data)
        logger.info(f"Created product {product.id}")
        return JsonResponse({'id': product.id, 'status': 'created'}, status=201)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return JsonResponse({'error': str(e)}, status=500)''',
        '''from functools import wraps
from typing import List, Type

def require_fields(*fields: str):
    """Decorator to validate required fields in request body."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in request")
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            
            for field in fields:
                if not data.get(field):
                    return JsonResponse({'error': f'{field.title()} required'}, status=400)
            
            request.parsed_data = data
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

def handle_create(model: Type, entity_name: str):
    """Generic create handler factory."""
    def handler(request):
        try:
            obj = model.objects.create(**request.parsed_data)
            logger.info(f"Created {entity_name} {obj.id}")
            return JsonResponse({'id': obj.id, 'status': 'created'}, status=201)
        except Exception as e:
            logger.error(f"Error creating {entity_name}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    return handler

@require_fields('email', 'name')
def handle_create_user(request):
    return handle_create(User, 'user')(request)

@require_fields('name', 'price')
def handle_create_product(request):
    return handle_create(Product, 'product')(request)''',
        "Extracted common patterns into a decorator and factory function, eliminating duplication."
    ),
    
    # Convert Callback to Async/Await
    (
        "Refactor this callback-based JavaScript to use async/await",
        '''function fetchUserData(userId, callback) {
    fetch('/api/users/' + userId)
        .then(function(response) {
            if (!response.ok) {
                callback(new Error('User not found'), null);
                return;
            }
            response.json().then(function(user) {
                fetch('/api/orders?userId=' + userId)
                    .then(function(orderResponse) {
                        orderResponse.json().then(function(orders) {
                            fetch('/api/preferences/' + userId)
                                .then(function(prefResponse) {
                                    prefResponse.json().then(function(prefs) {
                                        callback(null, {
                                            user: user,
                                            orders: orders,
                                            preferences: prefs
                                        });
                                    });
                                })
                                .catch(function(err) {
                                    callback(err, null);
                                });
                        });
                    })
                    .catch(function(err) {
                        callback(err, null);
                    });
            });
        })
        .catch(function(err) {
            callback(err, null);
        });
}''',
        '''async function fetchUserData(userId) {
    const userResponse = await fetch(`/api/users/${userId}`);
    if (!userResponse.ok) {
        throw new Error('User not found');
    }
    const user = await userResponse.json();
    
    // Fetch orders and preferences in parallel
    const [ordersResponse, prefsResponse] = await Promise.all([
        fetch(`/api/orders?userId=${userId}`),
        fetch(`/api/preferences/${userId}`)
    ]);
    
    const [orders, preferences] = await Promise.all([
        ordersResponse.json(),
        prefsResponse.json()
    ]);
    
    return { user, orders, preferences };
}

// Usage:
// try {
//     const data = await fetchUserData(123);
// } catch (error) {
//     console.error('Failed to fetch user data:', error);
// }''',
        "Async/await flattens callback hell, and Promise.all parallelizes independent requests."
    ),
    
    # Replace Conditionals with Polymorphism
    (
        "Refactor this switch statement using polymorphism",
        '''class PaymentProcessor:
    def process(self, payment_type, amount, details):
        if payment_type == 'credit_card':
            card_number = details['card_number']
            expiry = details['expiry']
            cvv = details['cvv']
            # Validate card
            if len(card_number) != 16:
                raise ValueError("Invalid card number")
            # Process credit card
            return self._charge_credit_card(card_number, expiry, cvv, amount)
        
        elif payment_type == 'paypal':
            email = details['email']
            # Validate PayPal
            if '@' not in email:
                raise ValueError("Invalid PayPal email")
            # Process PayPal
            return self._charge_paypal(email, amount)
        
        elif payment_type == 'bank_transfer':
            account = details['account_number']
            routing = details['routing_number']
            # Validate bank
            if len(routing) != 9:
                raise ValueError("Invalid routing number")
            # Process bank transfer
            return self._initiate_bank_transfer(account, routing, amount)
        
        else:
            raise ValueError(f"Unknown payment type: {payment_type}")''',
        '''from abc import ABC, abstractmethod
from typing import Dict, Any

class PaymentMethod(ABC):
    """Base class for payment methods."""
    
    @abstractmethod
    def validate(self, details: Dict[str, Any]) -> None:
        """Validate payment details."""
        pass
    
    @abstractmethod
    def process(self, amount: float, details: Dict[str, Any]) -> str:
        """Process the payment."""
        pass

class CreditCardPayment(PaymentMethod):
    def validate(self, details: Dict[str, Any]) -> None:
        if len(details.get('card_number', '')) != 16:
            raise ValueError("Invalid card number")
    
    def process(self, amount: float, details: Dict[str, Any]) -> str:
        self.validate(details)
        return charge_credit_card(
            details['card_number'],
            details['expiry'],
            details['cvv'],
            amount
        )

class PayPalPayment(PaymentMethod):
    def validate(self, details: Dict[str, Any]) -> None:
        if '@' not in details.get('email', ''):
            raise ValueError("Invalid PayPal email")
    
    def process(self, amount: float, details: Dict[str, Any]) -> str:
        self.validate(details)
        return charge_paypal(details['email'], amount)

class BankTransferPayment(PaymentMethod):
    def validate(self, details: Dict[str, Any]) -> None:
        if len(details.get('routing_number', '')) != 9:
            raise ValueError("Invalid routing number")
    
    def process(self, amount: float, details: Dict[str, Any]) -> str:
        self.validate(details)
        return initiate_bank_transfer(
            details['account_number'],
            details['routing_number'],
            amount
        )

# Payment method registry
PAYMENT_METHODS: Dict[str, PaymentMethod] = {
    'credit_card': CreditCardPayment(),
    'paypal': PayPalPayment(),
    'bank_transfer': BankTransferPayment(),
}

class PaymentProcessor:
    def process(self, payment_type: str, amount: float, details: Dict[str, Any]) -> str:
        method = PAYMENT_METHODS.get(payment_type)
        if not method:
            raise ValueError(f"Unknown payment type: {payment_type}")
        return method.process(amount, details)''',
        "Polymorphism makes adding new payment types trivial - just add a new class."
    ),
    
    # Decompose Large Function
    (
        "Break down this large function into smaller, focused functions",
        '''def generate_report(data, report_type, output_format):
    # Parse and validate data
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, list):
        data = [data]
    cleaned_data = []
    for item in data:
        if item.get('value') is not None and item.get('date'):
            cleaned_data.append({
                'value': float(item['value']),
                'date': parse_date(item['date']),
                'category': item.get('category', 'unknown')
            })
    
    # Calculate statistics
    values = [d['value'] for d in cleaned_data]
    total = sum(values)
    average = total / len(values) if values else 0
    minimum = min(values) if values else 0
    maximum = max(values) if values else 0
    
    # Group by category
    by_category = {}
    for item in cleaned_data:
        cat = item['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item['value'])
    
    category_stats = {}
    for cat, vals in by_category.items():
        category_stats[cat] = {
            'total': sum(vals),
            'average': sum(vals) / len(vals),
            'count': len(vals)
        }
    
    # Build report
    report = {
        'type': report_type,
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total': total,
            'average': average,
            'min': minimum,
            'max': maximum,
            'count': len(cleaned_data)
        },
        'by_category': category_stats
    }
    
    # Format output
    if output_format == 'json':
        return json.dumps(report, indent=2)
    elif output_format == 'csv':
        lines = ['category,total,average,count']
        for cat, stats in category_stats.items():
            lines.append(f"{cat},{stats['total']},{stats['average']},{stats['count']}")
        return '\\n'.join(lines)
    else:
        return str(report)''',
        '''from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

@dataclass
class DataPoint:
    value: float
    date: datetime
    category: str

@dataclass
class Statistics:
    total: float
    average: float
    minimum: float
    maximum: float
    count: int

def parse_input_data(data: Any) -> List[dict]:
    """Normalize input data to a list of dictionaries."""
    if isinstance(data, str):
        data = json.loads(data)
    return [data] if not isinstance(data, list) else data

def clean_data(raw_data: List[dict]) -> List[DataPoint]:
    """Filter and transform raw data into DataPoint objects."""
    cleaned = []
    for item in raw_data:
        if item.get('value') is not None and item.get('date'):
            cleaned.append(DataPoint(
                value=float(item['value']),
                date=parse_date(item['date']),
                category=item.get('category', 'unknown')
            ))
    return cleaned

def calculate_statistics(data: List[DataPoint]) -> Statistics:
    """Calculate summary statistics for data points."""
    if not data:
        return Statistics(0, 0, 0, 0, 0)
    
    values = [d.value for d in data]
    return Statistics(
        total=sum(values),
        average=sum(values) / len(values),
        minimum=min(values),
        maximum=max(values),
        count=len(values)
    )

def group_by_category(data: List[DataPoint]) -> Dict[str, Statistics]:
    """Group data by category and calculate per-category statistics."""
    groups = defaultdict(list)
    for item in data:
        groups[item.category].append(item)
    
    return {
        cat: calculate_statistics(items)
        for cat, items in groups.items()
    }

def build_report(report_type: str, stats: Statistics, category_stats: Dict[str, Statistics]) -> dict:
    """Build the report structure."""
    return {
        'type': report_type,
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total': stats.total,
            'average': stats.average,
            'min': stats.minimum,
            'max': stats.maximum,
            'count': stats.count
        },
        'by_category': {
            cat: {'total': s.total, 'average': s.average, 'count': s.count}
            for cat, s in category_stats.items()
        }
    }

def format_as_csv(category_stats: Dict[str, Statistics]) -> str:
    """Format category statistics as CSV."""
    lines = ['category,total,average,count']
    for cat, stats in category_stats.items():
        lines.append(f"{cat},{stats.total},{stats.average},{stats.count}")
    return '\\n'.join(lines)

def generate_report(data: Any, report_type: str, output_format: str) -> str:
    """Generate a report from data in the specified format."""
    raw_data = parse_input_data(data)
    cleaned = clean_data(raw_data)
    stats = calculate_statistics(cleaned)
    category_stats = group_by_category(cleaned)
    report = build_report(report_type, stats, category_stats)
    
    if output_format == 'json':
        return json.dumps(report, indent=2)
    elif output_format == 'csv':
        return format_as_csv(category_stats)
    return str(report)''',
        "Each function now has a single responsibility, is testable in isolation, and the main function reads like documentation."
    ),
    
    # Introduce Parameter Object
    (
        "Refactor to use a parameter object instead of many parameters",
        '''def create_user(
    email,
    password,
    first_name,
    last_name,
    phone=None,
    address_line1=None,
    address_line2=None,
    city=None,
    state=None,
    zip_code=None,
    country='US',
    newsletter=False,
    marketing=False,
    terms_accepted=False
):
    if not terms_accepted:
        raise ValueError("Must accept terms")
    
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )
    user.set_password(password)
    
    if address_line1:
        user.address = Address(
            line1=address_line1,
            line2=address_line2,
            city=city,
            state=state,
            zip_code=zip_code,
            country=country
        )
    
    user.preferences = Preferences(
        newsletter=newsletter,
        marketing=marketing
    )
    
    return user''',
        '''from dataclasses import dataclass, field
from typing import Optional

@dataclass
class AddressInfo:
    line1: str
    city: str
    state: str
    zip_code: str
    line2: Optional[str] = None
    country: str = 'US'

@dataclass
class MarketingPreferences:
    newsletter: bool = False
    marketing: bool = False

@dataclass
class UserRegistration:
    email: str
    password: str
    first_name: str
    last_name: str
    terms_accepted: bool
    phone: Optional[str] = None
    address: Optional[AddressInfo] = None
    preferences: MarketingPreferences = field(default_factory=MarketingPreferences)
    
    def __post_init__(self):
        if not self.terms_accepted:
            raise ValueError("Must accept terms")

def create_user(registration: UserRegistration) -> User:
    """Create a user from registration data."""
    user = User(
        email=registration.email,
        first_name=registration.first_name,
        last_name=registration.last_name,
        phone=registration.phone
    )
    user.set_password(registration.password)
    
    if registration.address:
        user.address = Address(
            line1=registration.address.line1,
            line2=registration.address.line2,
            city=registration.address.city,
            state=registration.address.state,
            zip_code=registration.address.zip_code,
            country=registration.address.country
        )
    
    user.preferences = Preferences(
        newsletter=registration.preferences.newsletter,
        marketing=registration.preferences.marketing
    )
    
    return user

# Usage:
# reg = UserRegistration(
#     email="user@example.com",
#     password="secure123",
#     first_name="John",
#     last_name="Doe",
#     terms_accepted=True,
#     address=AddressInfo(line1="123 Main St", city="NYC", state="NY", zip_code="10001")
# )
# user = create_user(reg)''',
        "Parameter objects group related data, provide validation, and make the API cleaner."
    ),
    
    # Replace Temp Variables with Query
    (
        "Refactor to replace temporary variables with methods",
        '''class Order:
    def __init__(self, items, customer):
        self.items = items
        self.customer = customer
    
    def get_invoice(self):
        # Calculate subtotal
        subtotal = 0
        for item in self.items:
            subtotal += item.price * item.quantity
        
        # Calculate discount
        discount = 0
        if self.customer.is_premium:
            discount = subtotal * 0.1
        elif subtotal > 100:
            discount = subtotal * 0.05
        
        # Calculate tax
        taxable = subtotal - discount
        tax = taxable * 0.08
        
        # Calculate total
        total = taxable + tax
        
        # Calculate shipping
        if total > 50:
            shipping = 0
        else:
            shipping = 5.99
        
        final_total = total + shipping
        
        return {
            'subtotal': subtotal,
            'discount': discount,
            'tax': tax,
            'shipping': shipping,
            'total': final_total
        }''',
        '''class Order:
    TAX_RATE = 0.08
    PREMIUM_DISCOUNT = 0.10
    BULK_DISCOUNT = 0.05
    BULK_THRESHOLD = 100
    FREE_SHIPPING_THRESHOLD = 50
    SHIPPING_COST = 5.99
    
    def __init__(self, items, customer):
        self.items = items
        self.customer = customer
    
    @property
    def subtotal(self) -> float:
        """Calculate subtotal from all items."""
        return sum(item.price * item.quantity for item in self.items)
    
    @property
    def discount(self) -> float:
        """Calculate applicable discount."""
        if self.customer.is_premium:
            return self.subtotal * self.PREMIUM_DISCOUNT
        if self.subtotal > self.BULK_THRESHOLD:
            return self.subtotal * self.BULK_DISCOUNT
        return 0
    
    @property
    def taxable_amount(self) -> float:
        """Amount subject to tax after discount."""
        return self.subtotal - self.discount
    
    @property
    def tax(self) -> float:
        """Calculate tax on taxable amount."""
        return self.taxable_amount * self.TAX_RATE
    
    @property
    def pre_shipping_total(self) -> float:
        """Total before shipping."""
        return self.taxable_amount + self.tax
    
    @property
    def shipping(self) -> float:
        """Calculate shipping cost."""
        return 0 if self.pre_shipping_total > self.FREE_SHIPPING_THRESHOLD else self.SHIPPING_COST
    
    @property
    def total(self) -> float:
        """Final total including shipping."""
        return self.pre_shipping_total + self.shipping
    
    def get_invoice(self) -> dict:
        """Generate invoice breakdown."""
        return {
            'subtotal': self.subtotal,
            'discount': self.discount,
            'tax': self.tax,
            'shipping': self.shipping,
            'total': self.total
        }''',
        "Properties make calculations reusable, testable, and the logic self-documenting."
    ),
    
    # Introduce Null Object
    (
        "Refactor to use the Null Object pattern instead of null checks",
        '''class UserService:
    def get_user_display_name(self, user_id):
        user = self.repository.find(user_id)
        if user is not None:
            if user.display_name is not None:
                return user.display_name
            else:
                return user.email
        else:
            return "Guest"
    
    def get_user_permissions(self, user_id):
        user = self.repository.find(user_id)
        if user is not None:
            if user.role is not None:
                return user.role.permissions
            else:
                return []
        else:
            return []
    
    def can_user_edit(self, user_id, resource):
        user = self.repository.find(user_id)
        if user is not None:
            if user.role is not None:
                return 'edit' in user.role.permissions
            else:
                return False
        else:
            return False''',
        '''class NullUser:
    """Null object representing an anonymous/guest user."""
    display_name = "Guest"
    email = "guest@example.com"
    role = None
    
    @property
    def permissions(self):
        return []
    
    def has_permission(self, permission: str) -> bool:
        return False

class NullRole:
    """Null object for users without a role."""
    name = "none"
    permissions = []
    
    def has_permission(self, permission: str) -> bool:
        return False

class User:
    def __init__(self, email, display_name=None, role=None):
        self.email = email
        self._display_name = display_name
        self._role = role
    
    @property
    def display_name(self) -> str:
        return self._display_name or self.email
    
    @property
    def role(self):
        return self._role or NullRole()
    
    @property
    def permissions(self):
        return self.role.permissions
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

class UserService:
    def _get_user(self, user_id) -> User:
        """Get user or return NullUser if not found."""
        user = self.repository.find(user_id)
        return user if user is not None else NullUser()
    
    def get_user_display_name(self, user_id) -> str:
        return self._get_user(user_id).display_name
    
    def get_user_permissions(self, user_id) -> list:
        return self._get_user(user_id).permissions
    
    def can_user_edit(self, user_id, resource) -> bool:
        return self._get_user(user_id).has_permission('edit')''',
        "Null Objects eliminate repetitive null checks and provide sensible default behavior."
    ),
    
    # Replace Inheritance with Composition
    (
        "Refactor this inheritance hierarchy to use composition",
        '''class Animal:
    def __init__(self, name):
        self.name = name

class FlyingAnimal(Animal):
    def fly(self):
        return f"{self.name} is flying"

class SwimmingAnimal(Animal):
    def swim(self):
        return f"{self.name} is swimming"

class WalkingAnimal(Animal):
    def walk(self):
        return f"{self.name} is walking"

# Problem: Duck can fly, swim, AND walk - can't inherit from all three
class Duck(FlyingAnimal):  # But what about swimming and walking?
    def swim(self):  # Have to duplicate
        return f"{self.name} is swimming"
    def walk(self):  # Have to duplicate
        return f"{self.name} is walking"

class Penguin(SwimmingAnimal):  # Can swim and walk, but not fly
    def walk(self):
        return f"{self.name} is walking"''',
        '''from abc import ABC, abstractmethod
from typing import List

# Ability interfaces
class Ability(ABC):
    @abstractmethod
    def perform(self, actor_name: str) -> str:
        pass

class Flying(Ability):
    def perform(self, actor_name: str) -> str:
        return f"{actor_name} is flying"

class Swimming(Ability):
    def perform(self, actor_name: str) -> str:
        return f"{actor_name} is swimming"

class Walking(Ability):
    def perform(self, actor_name: str) -> str:
        return f"{actor_name} is walking"

# Animal with composable abilities
class Animal:
    def __init__(self, name: str, abilities: List[Ability] = None):
        self.name = name
        self._abilities = {type(a).__name__: a for a in (abilities or [])}
    
    def can(self, ability_type: type) -> bool:
        return ability_type.__name__ in self._abilities
    
    def perform(self, ability_type: type) -> str:
        ability = self._abilities.get(ability_type.__name__)
        if not ability:
            return f"{self.name} cannot {ability_type.__name__.lower()}"
        return ability.perform(self.name)

# Now animals can have any combination of abilities
duck = Animal("Donald", [Flying(), Swimming(), Walking()])
penguin = Animal("Pingu", [Swimming(), Walking()])
fish = Animal("Nemo", [Swimming()])

# Usage:
# duck.perform(Flying)    # "Donald is flying"
# duck.perform(Swimming)  # "Donald is swimming"
# penguin.perform(Flying) # "Pingu cannot flying"
# penguin.can(Swimming)   # True''',
        "Composition allows flexible combination of behaviors without multiple inheritance issues."
    ),
    
    # TypeScript: Extract Interface
    (
        "Refactor to extract a common interface from these classes",
        '''class EmailNotifier {
    constructor(private apiKey: string) {}
    
    async send(to: string, subject: string, body: string): Promise<boolean> {
        console.log(`Sending email to ${to}`);
        // Email sending logic
        return true;
    }
    
    getType(): string {
        return 'email';
    }
}

class SMSNotifier {
    constructor(private accountSid: string, private authToken: string) {}
    
    async send(to: string, subject: string, body: string): Promise<boolean> {
        console.log(`Sending SMS to ${to}`);
        // SMS sending logic
        return true;
    }
    
    getType(): string {
        return 'sms';
    }
}

class PushNotifier {
    constructor(private serverKey: string) {}
    
    async send(to: string, subject: string, body: string): Promise<boolean> {
        console.log(`Sending push to ${to}`);
        // Push notification logic
        return true;
    }
    
    getType(): string {
        return 'push';
    }
}''',
        '''interface Notifier {
    send(to: string, subject: string, body: string): Promise<boolean>;
    getType(): string;
}

interface NotificationMessage {
    to: string;
    subject: string;
    body: string;
}

class EmailNotifier implements Notifier {
    constructor(private readonly apiKey: string) {}
    
    async send(to: string, subject: string, body: string): Promise<boolean> {
        console.log(`Sending email to ${to}`);
        return true;
    }
    
    getType(): string {
        return 'email';
    }
}

class SMSNotifier implements Notifier {
    constructor(
        private readonly accountSid: string,
        private readonly authToken: string
    ) {}
    
    async send(to: string, subject: string, body: string): Promise<boolean> {
        console.log(`Sending SMS to ${to}`);
        return true;
    }
    
    getType(): string {
        return 'sms';
    }
}

class PushNotifier implements Notifier {
    constructor(private readonly serverKey: string) {}
    
    async send(to: string, subject: string, body: string): Promise<boolean> {
        console.log(`Sending push to ${to}`);
        return true;
    }
    
    getType(): string {
        return 'push';
    }
}

// Now can use polymorphically
class NotificationService {
    constructor(private notifiers: Notifier[]) {}
    
    async broadcast(message: NotificationMessage): Promise<void> {
        await Promise.all(
            this.notifiers.map(n => n.send(message.to, message.subject, message.body))
        );
    }
}''',
        "Extracted common interface enables polymorphism and makes adding new notifiers trivial."
    ),
    
    # Consolidate Duplicate Conditional Fragments
    (
        "Refactor to remove duplicate code from conditional branches",
        '''def process_payment(payment):
    if payment.type == 'credit':
        logger.info(f"Processing payment {payment.id}")
        validate_payment(payment)
        result = charge_credit_card(payment)
        logger.info(f"Payment {payment.id} completed")
        send_receipt(payment)
        return result
    elif payment.type == 'debit':
        logger.info(f"Processing payment {payment.id}")
        validate_payment(payment)
        result = charge_debit_card(payment)
        logger.info(f"Payment {payment.id} completed")
        send_receipt(payment)
        return result
    elif payment.type == 'ach':
        logger.info(f"Processing payment {payment.id}")
        validate_payment(payment)
        result = process_ach(payment)
        logger.info(f"Payment {payment.id} completed")
        send_receipt(payment)
        return result''',
        '''PAYMENT_PROCESSORS = {
    'credit': charge_credit_card,
    'debit': charge_debit_card,
    'ach': process_ach,
}

def process_payment(payment):
    processor = PAYMENT_PROCESSORS.get(payment.type)
    if not processor:
        raise ValueError(f"Unknown payment type: {payment.type}")
    
    logger.info(f"Processing payment {payment.id}")
    validate_payment(payment)
    
    result = processor(payment)
    
    logger.info(f"Payment {payment.id} completed")
    send_receipt(payment)
    return result''',
        "Moved common code outside the conditional; only the varying part is selected."
    ),
    
    # Replace Constructor with Factory Method
    (
        "Refactor to use a factory method instead of complex constructor logic",
        '''class Connection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        
        # Parse connection string to determine type
        if connection_string.startswith('postgresql://'):
            self.type = 'postgres'
            self.driver = PostgresDriver()
            self.port = 5432
        elif connection_string.startswith('mysql://'):
            self.type = 'mysql'
            self.driver = MySQLDriver()
            self.port = 3306
        elif connection_string.startswith('mongodb://'):
            self.type = 'mongodb'
            self.driver = MongoDriver()
            self.port = 27017
        elif connection_string.startswith('redis://'):
            self.type = 'redis'
            self.driver = RedisDriver()
            self.port = 6379
        else:
            raise ValueError(f"Unknown database type")
        
        # Parse host from connection string
        self.host = self._parse_host(connection_string)''',
        '''from dataclasses import dataclass
from typing import ClassVar, Dict, Type
from abc import ABC, abstractmethod

@dataclass
class ConnectionConfig:
    host: str
    port: int
    database: str
    username: str = None
    password: str = None

class Connection(ABC):
    """Base connection class."""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.driver = self._create_driver()
    
    @abstractmethod
    def _create_driver(self):
        pass
    
    @classmethod
    def from_string(cls, connection_string: str) -> 'Connection':
        """Factory method to create appropriate connection from string."""
        for prefix, connection_class in CONNECTION_TYPES.items():
            if connection_string.startswith(prefix):
                config = connection_class.parse_connection_string(connection_string)
                return connection_class(config)
        raise ValueError(f"Unknown database type in: {connection_string}")
    
    @staticmethod
    @abstractmethod
    def parse_connection_string(conn_str: str) -> ConnectionConfig:
        pass

class PostgresConnection(Connection):
    DEFAULT_PORT = 5432
    
    def _create_driver(self):
        return PostgresDriver()
    
    @staticmethod
    def parse_connection_string(conn_str: str) -> ConnectionConfig:
        # Parse postgresql://user:pass@host:port/db
        return ConnectionConfig(...)  # parsing logic

class MySQLConnection(Connection):
    DEFAULT_PORT = 3306
    
    def _create_driver(self):
        return MySQLDriver()
    
    @staticmethod
    def parse_connection_string(conn_str: str) -> ConnectionConfig:
        return ConnectionConfig(...)

# Registry of connection types
CONNECTION_TYPES: Dict[str, Type[Connection]] = {
    'postgresql://': PostgresConnection,
    'mysql://': MySQLConnection,
    'mongodb://': MongoConnection,
    'redis://': RedisConnection,
}

# Usage:
# conn = Connection.from_string("postgresql://localhost/mydb")''',
        "Factory method encapsulates creation logic and makes adding new database types easy."
    ),
    
    # Replace Nested Loops with Comprehensions
    (
        "Refactor these nested loops to use comprehensions and functional style",
        '''def get_active_user_emails(departments):
    result = []
    for dept in departments:
        if dept.is_active:
            for team in dept.teams:
                for user in team.members:
                    if user.is_active and user.has_verified_email:
                        result.append(user.email.lower())
    
    # Remove duplicates
    unique_emails = []
    for email in result:
        if email not in unique_emails:
            unique_emails.append(email)
    
    # Sort alphabetically
    unique_emails.sort()
    
    return unique_emails''',
        '''def get_active_user_emails(departments):
    """Get sorted unique emails of active users in active departments."""
    emails = (
        user.email.lower()
        for dept in departments if dept.is_active
        for team in dept.teams
        for user in team.members
        if user.is_active and user.has_verified_email
    )
    return sorted(set(emails))''',
        "Generator expression with set for deduplication - more Pythonic and efficient."
    ),
    
    # Extract Class
    (
        "Extract the address handling into its own class",
        '''class Customer:
    def __init__(self, name, email, street, city, state, zip_code, country):
        self.name = name
        self.email = email
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.country = country
    
    def get_full_address(self):
        parts = [self.street]
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)
        if self.country and self.country != 'US':
            parts.append(self.country)
        return ', '.join(parts)
    
    def validate_address(self):
        if not self.street:
            return False, "Street is required"
        if not self.city:
            return False, "City is required"
        if not self.zip_code:
            return False, "ZIP code is required"
        if self.country == 'US' and len(self.zip_code) != 5:
            return False, "US ZIP code must be 5 digits"
        return True, None
    
    def is_domestic(self):
        return self.country in ('US', 'USA', 'United States', None)''',
        '''from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Address:
    """Represents a physical address."""
    street: str
    city: str
    state: Optional[str]
    zip_code: str
    country: str = 'US'
    
    def format(self) -> str:
        """Format address as a single string."""
        parts = [self.street, self.city]
        if self.state:
            parts.append(self.state)
        parts.append(self.zip_code)
        if not self.is_domestic:
            parts.append(self.country)
        return ', '.join(parts)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate address fields."""
        if not self.street:
            return False, "Street is required"
        if not self.city:
            return False, "City is required"
        if not self.zip_code:
            return False, "ZIP code is required"
        if self.is_domestic and len(self.zip_code) != 5:
            return False, "US ZIP code must be 5 digits"
        return True, None
    
    @property
    def is_domestic(self) -> bool:
        """Check if this is a US address."""
        return self.country.upper() in ('US', 'USA', 'UNITED STATES')

@dataclass
class Customer:
    """Represents a customer with contact and address info."""
    name: str
    email: str
    address: Address
    
    def get_full_address(self) -> str:
        return self.address.format()
    
    def validate_address(self) -> Tuple[bool, Optional[str]]:
        return self.address.validate()
    
    def is_domestic(self) -> bool:
        return self.address.is_domestic

# Usage:
# addr = Address("123 Main St", "Springfield", "IL", "62701")
# customer = Customer("John Doe", "john@example.com", addr)''',
        "Address is now reusable for Orders, Vendors, etc., and has focused responsibility."
    ),
    
    # Simplify Method Calls
    (
        "Refactor to simplify these repetitive method calls",
        '''class FormValidator:
    def validate(self, data):
        errors = []
        
        # Validate name
        if 'name' not in data:
            errors.append({'field': 'name', 'error': 'required'})
        elif len(data['name']) < 2:
            errors.append({'field': 'name', 'error': 'too_short', 'min': 2})
        elif len(data['name']) > 100:
            errors.append({'field': 'name', 'error': 'too_long', 'max': 100})
        
        # Validate email
        if 'email' not in data:
            errors.append({'field': 'email', 'error': 'required'})
        elif '@' not in data['email']:
            errors.append({'field': 'email', 'error': 'invalid_format'})
        elif len(data['email']) > 255:
            errors.append({'field': 'email', 'error': 'too_long', 'max': 255})
        
        # Validate age
        if 'age' not in data:
            errors.append({'field': 'age', 'error': 'required'})
        elif not isinstance(data['age'], int):
            errors.append({'field': 'age', 'error': 'invalid_type'})
        elif data['age'] < 18:
            errors.append({'field': 'age', 'error': 'too_small', 'min': 18})
        elif data['age'] > 150:
            errors.append({'field': 'age', 'error': 'too_large', 'max': 150})
        
        return errors''',
        '''from dataclasses import dataclass
from typing import Any, Callable, List, Optional

@dataclass
class ValidationRule:
    check: Callable[[Any], bool]
    error: str
    params: dict = None

@dataclass
class FieldValidator:
    name: str
    rules: List[ValidationRule]
    
    def validate(self, value: Any) -> Optional[dict]:
        for rule in self.rules:
            if not rule.check(value):
                error = {'field': self.name, 'error': rule.error}
                if rule.params:
                    error.update(rule.params)
                return error
        return None

class FormValidator:
    def __init__(self):
        self.fields = [
            FieldValidator('name', [
                ValidationRule(lambda v: v is not None, 'required'),
                ValidationRule(lambda v: len(v) >= 2, 'too_short', {'min': 2}),
                ValidationRule(lambda v: len(v) <= 100, 'too_long', {'max': 100}),
            ]),
            FieldValidator('email', [
                ValidationRule(lambda v: v is not None, 'required'),
                ValidationRule(lambda v: '@' in str(v), 'invalid_format'),
                ValidationRule(lambda v: len(v) <= 255, 'too_long', {'max': 255}),
            ]),
            FieldValidator('age', [
                ValidationRule(lambda v: v is not None, 'required'),
                ValidationRule(lambda v: isinstance(v, int), 'invalid_type'),
                ValidationRule(lambda v: v >= 18, 'too_small', {'min': 18}),
                ValidationRule(lambda v: v <= 150, 'too_large', {'max': 150}),
            ]),
        ]
    
    def validate(self, data: dict) -> List[dict]:
        errors = []
        for field in self.fields:
            value = data.get(field.name)
            if error := field.validate(value):
                errors.append(error)
        return errors''',
        "Declarative validation rules are easier to read, maintain, and extend."
    ),
    
    # Convert to Method Chaining / Fluent Interface
    (
        "Refactor to use method chaining for a fluent interface",
        '''class QueryBuilder:
    def __init__(self, table):
        self.table = table
        self.columns = ['*']
        self.where_clauses = []
        self.order_column = None
        self.order_dir = 'ASC'
        self.limit_val = None
        self.offset_val = None
    
    def set_columns(self, columns):
        self.columns = columns
    
    def add_where(self, condition):
        self.where_clauses.append(condition)
    
    def set_order(self, column, direction='ASC'):
        self.order_column = column
        self.order_dir = direction
    
    def set_limit(self, limit):
        self.limit_val = limit
    
    def set_offset(self, offset):
        self.offset_val = offset

# Usage:
# builder = QueryBuilder('users')
# builder.set_columns(['id', 'name', 'email'])
# builder.add_where('active = true')
# builder.add_where('age >= 18')
# builder.set_order('name')
# builder.set_limit(10)
# query = builder.build()''',
        '''from typing import List, Self

class QueryBuilder:
    def __init__(self, table: str):
        self._table = table
        self._columns: List[str] = ['*']
        self._where_clauses: List[str] = []
        self._order_by: str = None
        self._order_dir: str = 'ASC'
        self._limit: int = None
        self._offset: int = None
    
    def select(self, *columns: str) -> Self:
        """Set columns to select."""
        self._columns = list(columns) if columns else ['*']
        return self
    
    def where(self, condition: str) -> Self:
        """Add a WHERE condition."""
        self._where_clauses.append(condition)
        return self
    
    def order_by(self, column: str, direction: str = 'ASC') -> Self:
        """Set ORDER BY clause."""
        self._order_by = column
        self._order_dir = direction.upper()
        return self
    
    def limit(self, count: int) -> Self:
        """Set LIMIT clause."""
        self._limit = count
        return self
    
    def offset(self, count: int) -> Self:
        """Set OFFSET clause."""
        self._offset = count
        return self
    
    def build(self) -> str:
        """Build the SQL query string."""
        query = f"SELECT {', '.join(self._columns)} FROM {self._table}"
        
        if self._where_clauses:
            query += f" WHERE {' AND '.join(self._where_clauses)}"
        
        if self._order_by:
            query += f" ORDER BY {self._order_by} {self._order_dir}"
        
        if self._limit is not None:
            query += f" LIMIT {self._limit}"
        
        if self._offset is not None:
            query += f" OFFSET {self._offset}"
        
        return query

# Usage:
# query = (QueryBuilder('users')
#     .select('id', 'name', 'email')
#     .where('active = true')
#     .where('age >= 18')
#     .order_by('name')
#     .limit(10)
#     .build())''',
        "Fluent interface with method chaining is more readable and discoverable."
    ),
    
    # Replace Exception with Test
    (
        "Refactor to check conditions instead of catching exceptions",
        '''def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return 0

def get_first_element(lst):
    try:
        return lst[0]
    except (IndexError, TypeError):
        return None

def parse_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def get_nested_value(data, keys):
    try:
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError, IndexError):
        return None''',
        '''from typing import Any, List, Optional

def safe_divide(a: float, b: float, default: float = 0) -> float:
    """Divide a by b, returning default if b is zero."""
    return a / b if b != 0 else default

def get_first_element(lst: list, default: Any = None) -> Any:
    """Get first element or default if empty/invalid."""
    if lst and hasattr(lst, '__getitem__'):
        return lst[0]
    return default

def parse_int(value: Any, default: int = 0) -> int:
    """Parse integer from value, returning default on failure."""
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.lstrip('-').isdigit():
        return int(value)
    return default

def get_nested_value(data: Any, keys: List[str], default: Any = None) -> Any:
    """Safely traverse nested dict/list structure."""
    result = data
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        elif isinstance(result, (list, tuple)) and isinstance(key, int) and 0 <= key < len(result):
            result = result[key]
        else:
            return default
    return result''',
        "Explicit checks are faster than exception handling for expected conditions."
    ),
    
    # Split Loop
    (
        "Refactor to split this loop that does too many things",
        '''def process_orders(orders):
    total_revenue = 0
    total_items = 0
    customers_served = set()
    failed_orders = []
    successful_orders = []
    high_value_orders = []
    
    for order in orders:
        # Calculate totals
        order_total = sum(item.price * item.quantity for item in order.items)
        total_revenue += order_total
        total_items += sum(item.quantity for item in order.items)
        
        # Track customers
        customers_served.add(order.customer_id)
        
        # Categorize orders
        if order.status == 'failed':
            failed_orders.append(order)
        else:
            successful_orders.append(order)
            if order_total > 1000:
                high_value_orders.append(order)
    
    return {
        'total_revenue': total_revenue,
        'total_items': total_items,
        'unique_customers': len(customers_served),
        'failed_count': len(failed_orders),
        'success_count': len(successful_orders),
        'high_value_count': len(high_value_orders)
    }''',
        '''from dataclasses import dataclass
from typing import List

@dataclass
class OrderMetrics:
    total_revenue: float
    total_items: int
    unique_customers: int
    failed_count: int
    success_count: int
    high_value_count: int

def calculate_order_total(order) -> float:
    """Calculate total value of an order."""
    return sum(item.price * item.quantity for item in order.items)

def calculate_order_items(order) -> int:
    """Count total items in an order."""
    return sum(item.quantity for item in order.items)

def calculate_revenue_metrics(orders) -> tuple[float, int]:
    """Calculate revenue and item totals."""
    totals = [(calculate_order_total(o), calculate_order_items(o)) for o in orders]
    return (
        sum(t[0] for t in totals),
        sum(t[1] for t in totals)
    )

def count_unique_customers(orders) -> int:
    """Count unique customers."""
    return len({o.customer_id for o in orders})

def categorize_orders(orders) -> dict:
    """Categorize orders by status and value."""
    successful = [o for o in orders if o.status != 'failed']
    return {
        'failed': len(orders) - len(successful),
        'successful': len(successful),
        'high_value': sum(1 for o in successful if calculate_order_total(o) > 1000)
    }

def process_orders(orders) -> OrderMetrics:
    """Process orders and return metrics."""
    revenue, items = calculate_revenue_metrics(orders)
    categories = categorize_orders(orders)
    
    return OrderMetrics(
        total_revenue=revenue,
        total_items=items,
        unique_customers=count_unique_customers(orders),
        failed_count=categories['failed'],
        success_count=categories['successful'],
        high_value_count=categories['high_value']
    )''',
        "Split into focused functions - each does one thing and can be tested independently."
    ),
    
    # Replace Type Code with Subclasses
    (
        "Refactor to use subclasses instead of type codes",
        '''class Employee:
    ENGINEER = 'engineer'
    MANAGER = 'manager'
    SALESPERSON = 'sales'
    
    def __init__(self, name, type_code, base_salary):
        self.name = name
        self.type_code = type_code
        self.base_salary = base_salary
        self.sales = 0  # Only for salespeople
        self.team_size = 0  # Only for managers
    
    def calculate_bonus(self):
        if self.type_code == self.ENGINEER:
            return self.base_salary * 0.1
        elif self.type_code == self.MANAGER:
            return self.base_salary * 0.15 + (self.team_size * 500)
        elif self.type_code == self.SALESPERSON:
            return self.sales * 0.05
        else:
            return 0
    
    def get_title(self):
        if self.type_code == self.ENGINEER:
            return f"Engineer {self.name}"
        elif self.type_code == self.MANAGER:
            return f"Manager {self.name}"
        elif self.type_code == self.SALESPERSON:
            return f"Sales Rep {self.name}"''',
        '''from abc import ABC, abstractmethod

class Employee(ABC):
    """Base employee class."""
    
    def __init__(self, name: str, base_salary: float):
        self.name = name
        self.base_salary = base_salary
    
    @abstractmethod
    def calculate_bonus(self) -> float:
        """Calculate employee bonus."""
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """Get formatted title."""
        pass

class Engineer(Employee):
    BONUS_RATE = 0.10
    
    def calculate_bonus(self) -> float:
        return self.base_salary * self.BONUS_RATE
    
    def get_title(self) -> str:
        return f"Engineer {self.name}"

class Manager(Employee):
    BONUS_RATE = 0.15
    TEAM_BONUS = 500
    
    def __init__(self, name: str, base_salary: float, team_size: int = 0):
        super().__init__(name, base_salary)
        self.team_size = team_size
    
    def calculate_bonus(self) -> float:
        return self.base_salary * self.BONUS_RATE + (self.team_size * self.TEAM_BONUS)
    
    def get_title(self) -> str:
        return f"Manager {self.name}"

class Salesperson(Employee):
    COMMISSION_RATE = 0.05
    
    def __init__(self, name: str, base_salary: float, sales: float = 0):
        super().__init__(name, base_salary)
        self.sales = sales
    
    def calculate_bonus(self) -> float:
        return self.sales * self.COMMISSION_RATE
    
    def get_title(self) -> str:
        return f"Sales Rep {self.name}"

# Factory for creating employees
def create_employee(type_code: str, name: str, base_salary: float, **kwargs) -> Employee:
    employee_types = {
        'engineer': Engineer,
        'manager': Manager,
        'sales': Salesperson,
    }
    cls = employee_types.get(type_code)
    if not cls:
        raise ValueError(f"Unknown employee type: {type_code}")
    return cls(name, base_salary, **kwargs)''',
        "Subclasses eliminate conditionals and each type has only its relevant attributes."
    ),
    
    # Inline Temp
    (
        "Refactor to inline unnecessary temporary variables",
        '''def get_discounted_price(product, user):
    base_price = product.price
    discount_rate = user.discount_rate
    discount_amount = base_price * discount_rate
    discounted_price = base_price - discount_amount
    tax_rate = 0.08
    tax_amount = discounted_price * tax_rate
    final_price = discounted_price + tax_amount
    rounded_price = round(final_price, 2)
    return rounded_price''',
        '''TAX_RATE = 0.08

def get_discounted_price(product, user) -> float:
    """Calculate final price with discount and tax."""
    discounted = product.price * (1 - user.discount_rate)
    return round(discounted * (1 + TAX_RATE), 2)''',
        "Eliminated trivial temps that added no clarity; combined into readable expressions."
    ),
    
    # Preserve Whole Object
    (
        "Refactor to pass the whole object instead of individual properties",
        '''def check_room_availability(room_id, check_in_year, check_in_month, check_in_day,
                               check_out_year, check_out_month, check_out_day):
    check_in = date(check_in_year, check_in_month, check_in_day)
    check_out = date(check_out_year, check_out_month, check_out_day)
    
    reservations = get_reservations(room_id)
    for res in reservations:
        if check_in < res.end_date and check_out > res.start_date:
            return False
    return True

def create_reservation(guest_name, guest_email, guest_phone,
                      room_id, check_in_year, check_in_month, check_in_day,
                      check_out_year, check_out_month, check_out_day,
                      num_guests, special_requests):
    # ... lots of date construction and validation ...''',
        '''from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class DateRange:
    start: date
    end: date
    
    def overlaps(self, other: 'DateRange') -> bool:
        """Check if this range overlaps with another."""
        return self.start < other.end and self.end > other.start
    
    @property
    def nights(self) -> int:
        return (self.end - self.start).days

@dataclass
class Guest:
    name: str
    email: str
    phone: str

@dataclass
class ReservationRequest:
    guest: Guest
    room_id: int
    dates: DateRange
    num_guests: int
    special_requests: Optional[str] = None

def check_room_availability(room_id: int, dates: DateRange) -> bool:
    """Check if room is available for the given date range."""
    reservations = get_reservations(room_id)
    return not any(dates.overlaps(DateRange(r.start_date, r.end_date)) 
                   for r in reservations)

def create_reservation(request: ReservationRequest) -> Reservation:
    """Create a reservation from a request."""
    if not check_room_availability(request.room_id, request.dates):
        raise ValueError("Room not available for selected dates")
    
    return Reservation(
        guest=request.guest,
        room_id=request.room_id,
        start_date=request.dates.start,
        end_date=request.dates.end,
        num_guests=request.num_guests,
        special_requests=request.special_requests
    )''',
        "Data classes group related parameters and methods operating on them."
    ),
    
    # TypeScript: Use Discriminated Unions
    (
        "Refactor to use discriminated unions instead of optional properties",
        '''interface ApiResponse {
    success: boolean;
    data?: any;
    error?: string;
    errorCode?: number;
    validationErrors?: string[];
}

function handleResponse(response: ApiResponse) {
    if (response.success) {
        if (response.data) {
            console.log(response.data);
        }
    } else {
        if (response.error) {
            console.error(response.error);
        }
        if (response.validationErrors) {
            response.validationErrors.forEach(e => console.error(e));
        }
    }
}''',
        '''interface SuccessResponse<T> {
    success: true;
    data: T;
}

interface ErrorResponse {
    success: false;
    error: string;
    errorCode: number;
}

interface ValidationErrorResponse {
    success: false;
    error: 'validation_failed';
    errorCode: 400;
    validationErrors: string[];
}

type ApiResponse<T> = SuccessResponse<T> | ErrorResponse | ValidationErrorResponse;

function isValidationError(response: ApiResponse<unknown>): response is ValidationErrorResponse {
    return !response.success && 'validationErrors' in response;
}

function handleResponse<T>(response: ApiResponse<T>): void {
    if (response.success) {
        // TypeScript knows response.data exists and is type T
        console.log(response.data);
    } else if (isValidationError(response)) {
        // TypeScript knows validationErrors exists
        response.validationErrors.forEach(e => console.error(e));
    } else {
        // TypeScript knows error and errorCode exist
        console.error(`Error ${response.errorCode}: ${response.error}`);
    }
}''',
        "Discriminated unions provide compile-time exhaustiveness checking and eliminate optional property checks."
    ),
    
    # Replace State-Altering Conditionals with State Pattern
    (
        "Refactor to use the State pattern instead of conditionals",
        '''class Document:
    def __init__(self):
        self.state = 'draft'
    
    def publish(self):
        if self.state == 'draft':
            if self.current_user.is_admin:
                self.state = 'published'
            else:
                self.state = 'pending_review'
        elif self.state == 'pending_review':
            if self.current_user.is_admin:
                self.state = 'published'
            else:
                raise ValueError("Only admins can publish from review")
        elif self.state == 'published':
            raise ValueError("Already published")
    
    def reject(self):
        if self.state == 'pending_review':
            self.state = 'draft'
        else:
            raise ValueError(f"Cannot reject from {self.state}")
    
    def archive(self):
        if self.state == 'published':
            self.state = 'archived'
        elif self.state == 'archived':
            raise ValueError("Already archived")
        else:
            raise ValueError(f"Cannot archive from {self.state}")''',
        '''from abc import ABC, abstractmethod

class DocumentState(ABC):
    @abstractmethod
    def publish(self, doc: 'Document', user) -> 'DocumentState':
        pass
    
    @abstractmethod
    def reject(self, doc: 'Document') -> 'DocumentState':
        pass
    
    @abstractmethod
    def archive(self, doc: 'Document') -> 'DocumentState':
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

class DraftState(DocumentState):
    name = 'draft'
    
    def publish(self, doc, user):
        return PublishedState() if user.is_admin else PendingReviewState()
    
    def reject(self, doc):
        raise ValueError("Cannot reject a draft")
    
    def archive(self, doc):
        raise ValueError("Cannot archive a draft")

class PendingReviewState(DocumentState):
    name = 'pending_review'
    
    def publish(self, doc, user):
        if not user.is_admin:
            raise ValueError("Only admins can publish from review")
        return PublishedState()
    
    def reject(self, doc):
        return DraftState()
    
    def archive(self, doc):
        raise ValueError("Cannot archive from pending review")

class PublishedState(DocumentState):
    name = 'published'
    
    def publish(self, doc, user):
        raise ValueError("Already published")
    
    def reject(self, doc):
        raise ValueError("Cannot reject published document")
    
    def archive(self, doc):
        return ArchivedState()

class ArchivedState(DocumentState):
    name = 'archived'
    
    def publish(self, doc, user):
        raise ValueError("Cannot publish archived document")
    
    def reject(self, doc):
        raise ValueError("Cannot reject archived document")
    
    def archive(self, doc):
        raise ValueError("Already archived")

class Document:
    def __init__(self):
        self._state: DocumentState = DraftState()
    
    @property
    def state(self) -> str:
        return self._state.name
    
    def publish(self, user):
        self._state = self._state.publish(self, user)
    
    def reject(self):
        self._state = self._state.reject(self)
    
    def archive(self):
        self._state = self._state.archive(self)''',
        "State pattern makes transitions explicit and easy to add new states without modifying existing code."
    ),
    
    # Consolidate Conditional Expression
    (
        "Consolidate these separate conditions into a single expression",
        '''def calculate_disability_amount(employee):
    if employee.seniority < 2:
        return 0
    if employee.months_disabled > 12:
        return 0
    if employee.is_part_time:
        return 0
    
    return employee.base_disability_amount''',
        '''def is_eligible_for_disability(employee) -> bool:
    """Check if employee is eligible for disability benefits."""
    return (
        employee.seniority >= 2 and
        employee.months_disabled <= 12 and
        not employee.is_part_time
    )

def calculate_disability_amount(employee) -> float:
    """Calculate disability amount for eligible employees."""
    if not is_eligible_for_disability(employee):
        return 0
    return employee.base_disability_amount''',
        "Extracted eligibility check clarifies the business rule and makes it reusable."
    ),
    
    # Replace Hard-Coded Notifications with Observer
    (
        "Refactor to use the Observer pattern for notifications",
        '''class OrderService:
    def __init__(self, email_service, sms_service, analytics):
        self.email_service = email_service
        self.sms_service = sms_service
        self.analytics = analytics
    
    def complete_order(self, order):
        # Process the order
        order.status = 'completed'
        order.completed_at = datetime.now()
        self.repository.save(order)
        
        # Send notifications - tightly coupled!
        self.email_service.send_order_confirmation(order)
        self.sms_service.send_order_sms(order)
        self.analytics.track_order_completed(order)
        
        # What if we need to add Slack notification?
        # Have to modify this class every time!''',
        '''from abc import ABC, abstractmethod
from typing import List

class OrderEvent:
    """Event emitted when order changes."""
    def __init__(self, order, event_type: str):
        self.order = order
        self.event_type = event_type
        self.timestamp = datetime.now()

class OrderObserver(ABC):
    """Base class for order observers."""
    @abstractmethod
    def on_order_event(self, event: OrderEvent) -> None:
        pass

class EmailNotificationObserver(OrderObserver):
    def __init__(self, email_service):
        self.email_service = email_service
    
    def on_order_event(self, event: OrderEvent) -> None:
        if event.event_type == 'completed':
            self.email_service.send_order_confirmation(event.order)

class SMSNotificationObserver(OrderObserver):
    def __init__(self, sms_service):
        self.sms_service = sms_service
    
    def on_order_event(self, event: OrderEvent) -> None:
        if event.event_type == 'completed':
            self.sms_service.send_order_sms(event.order)

class AnalyticsObserver(OrderObserver):
    def __init__(self, analytics):
        self.analytics = analytics
    
    def on_order_event(self, event: OrderEvent) -> None:
        if event.event_type == 'completed':
            self.analytics.track_order_completed(event.order)

class OrderService:
    def __init__(self, repository):
        self.repository = repository
        self._observers: List[OrderObserver] = []
    
    def add_observer(self, observer: OrderObserver) -> None:
        self._observers.append(observer)
    
    def remove_observer(self, observer: OrderObserver) -> None:
        self._observers.remove(observer)
    
    def _notify(self, event: OrderEvent) -> None:
        for observer in self._observers:
            observer.on_order_event(event)
    
    def complete_order(self, order):
        order.status = 'completed'
        order.completed_at = datetime.now()
        self.repository.save(order)
        
        # Notify all observers - decoupled!
        self._notify(OrderEvent(order, 'completed'))

# Setup:
# service = OrderService(repo)
# service.add_observer(EmailNotificationObserver(email_svc))
# service.add_observer(SMSNotificationObserver(sms_svc))
# service.add_observer(SlackObserver(slack_svc))  # Easy to add!''',
        "Observer pattern decouples the order service from notification implementations."
    ),
    
    # JavaScript: Convert Class to Hooks
    (
        "Refactor this React class component to use hooks",
        '''class UserProfile extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            user: null,
            loading: true,
            error: null
        };
    }
    
    componentDidMount() {
        this.fetchUser();
    }
    
    componentDidUpdate(prevProps) {
        if (prevProps.userId !== this.props.userId) {
            this.fetchUser();
        }
    }
    
    async fetchUser() {
        this.setState({ loading: true, error: null });
        try {
            const response = await fetch(`/api/users/${this.props.userId}`);
            const user = await response.json();
            this.setState({ user, loading: false });
        } catch (error) {
            this.setState({ error: error.message, loading: false });
        }
    }
    
    render() {
        const { user, loading, error } = this.state;
        
        if (loading) return <div>Loading...</div>;
        if (error) return <div>Error: {error}</div>;
        if (!user) return null;
        
        return (
            <div>
                <h1>{user.name}</h1>
                <p>{user.email}</p>
            </div>
        );
    }
}''',
        '''import { useState, useEffect } from 'react';

// Custom hook for data fetching
function useUser(userId) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        let cancelled = false;
        
        async function fetchUser() {
            setLoading(true);
            setError(null);
            
            try {
                const response = await fetch(`/api/users/${userId}`);
                if (!response.ok) throw new Error('Failed to fetch user');
                const data = await response.json();
                
                if (!cancelled) {
                    setUser(data);
                    setLoading(false);
                }
            } catch (err) {
                if (!cancelled) {
                    setError(err.message);
                    setLoading(false);
                }
            }
        }
        
        fetchUser();
        
        return () => {
            cancelled = true;
        };
    }, [userId]);
    
    return { user, loading, error };
}

// Clean functional component
function UserProfile({ userId }) {
    const { user, loading, error } = useUser(userId);
    
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!user) return null;
    
    return (
        <div>
            <h1>{user.name}</h1>
            <p>{user.email}</p>
        </div>
    );
}

export { UserProfile, useUser };''',
        "Custom hook extracts reusable logic, component is simpler, and includes proper cleanup."
    ),
    
    # Simplify Complex Boolean Logic
    (
        "Simplify this complex boolean expression",
        '''def can_access_resource(user, resource, action):
    if user is None:
        return False
    
    if user.is_admin:
        return True
    
    if resource.owner_id == user.id:
        return True
    
    if action == 'read':
        if resource.is_public:
            return True
        if user.id in resource.shared_with:
            return True
        for group in user.groups:
            if group.id in resource.shared_with_groups:
                return True
    
    if action == 'write':
        if user.id in resource.editors:
            return True
        for group in user.groups:
            if group.id in resource.editor_groups:
                return True
    
    return False''',
        '''def can_access_resource(user, resource, action: str) -> bool:
    """Check if user can perform action on resource."""
    if user is None:
        return False
    
    # Quick checks for full access
    if user.is_admin or resource.owner_id == user.id:
        return True
    
    # Get user's group IDs for permission checks
    user_group_ids = {g.id for g in user.groups}
    
    # Check read permissions
    if action == 'read':
        return (
            resource.is_public or
            user.id in resource.shared_with or
            bool(user_group_ids & set(resource.shared_with_groups))
        )
    
    # Check write permissions
    if action == 'write':
        return (
            user.id in resource.editors or
            bool(user_group_ids & set(resource.editor_groups))
        )
    
    return False''',
        "Used set intersection for group checks and consolidated related conditions."
    ),
    
    # Replace Constructor with Builder
    (
        "Refactor to use the Builder pattern for this complex object",
        '''class HttpRequest:
    def __init__(self, method, url, headers=None, body=None, timeout=30,
                 auth=None, params=None, json_body=None, follow_redirects=True,
                 verify_ssl=True, cert=None, proxy=None, retry_count=0,
                 retry_delay=1, hooks=None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.body = body
        self.timeout = timeout
        self.auth = auth
        self.params = params or {}
        self.json_body = json_body
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.cert = cert
        self.proxy = proxy
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.hooks = hooks or {}

# Hard to read and easy to make mistakes:
request = HttpRequest('POST', 'https://api.example.com/users', 
    {'Content-Type': 'application/json'}, None, 60, ('user', 'pass'),
    None, {'name': 'John'}, True, True, None, None, 3, 2, None)''',
        '''from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, Self

@dataclass
class HttpRequest:
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    timeout: int = 30
    auth: Optional[Tuple[str, str]] = None
    params: Dict[str, str] = field(default_factory=dict)
    json_body: Optional[Any] = None
    follow_redirects: bool = True
    verify_ssl: bool = True
    cert: Optional[str] = None
    proxy: Optional[str] = None
    retry_count: int = 0
    retry_delay: int = 1
    hooks: Dict[str, callable] = field(default_factory=dict)

class HttpRequestBuilder:
    """Fluent builder for HTTP requests."""
    
    def __init__(self, method: str, url: str):
        self._method = method
        self._url = url
        self._headers: Dict[str, str] = {}
        self._body: Optional[bytes] = None
        self._timeout: int = 30
        self._auth: Optional[Tuple[str, str]] = None
        self._params: Dict[str, str] = {}
        self._json_body: Optional[Any] = None
        self._follow_redirects: bool = True
        self._verify_ssl: bool = True
        self._cert: Optional[str] = None
        self._proxy: Optional[str] = None
        self._retry_count: int = 0
        self._retry_delay: int = 1
        self._hooks: Dict[str, callable] = {}
    
    def header(self, key: str, value: str) -> Self:
        self._headers[key] = value
        return self
    
    def headers(self, headers: Dict[str, str]) -> Self:
        self._headers.update(headers)
        return self
    
    def timeout(self, seconds: int) -> Self:
        self._timeout = seconds
        return self
    
    def auth(self, username: str, password: str) -> Self:
        self._auth = (username, password)
        return self
    
    def param(self, key: str, value: str) -> Self:
        self._params[key] = value
        return self
    
    def json(self, data: Any) -> Self:
        self._json_body = data
        self._headers['Content-Type'] = 'application/json'
        return self
    
    def body(self, data: bytes) -> Self:
        self._body = data
        return self
    
    def no_redirects(self) -> Self:
        self._follow_redirects = False
        return self
    
    def skip_ssl_verify(self) -> Self:
        self._verify_ssl = False
        return self
    
    def with_retry(self, count: int = 3, delay: int = 1) -> Self:
        self._retry_count = count
        self._retry_delay = delay
        return self
    
    def proxy(self, proxy_url: str) -> Self:
        self._proxy = proxy_url
        return self
    
    def build(self) -> HttpRequest:
        return HttpRequest(
            method=self._method,
            url=self._url,
            headers=self._headers,
            body=self._body,
            timeout=self._timeout,
            auth=self._auth,
            params=self._params,
            json_body=self._json_body,
            follow_redirects=self._follow_redirects,
            verify_ssl=self._verify_ssl,
            cert=self._cert,
            proxy=self._proxy,
            retry_count=self._retry_count,
            retry_delay=self._retry_delay,
            hooks=self._hooks
        )

# Convenience factory methods
class Http:
    @staticmethod
    def get(url: str) -> HttpRequestBuilder:
        return HttpRequestBuilder('GET', url)
    
    @staticmethod
    def post(url: str) -> HttpRequestBuilder:
        return HttpRequestBuilder('POST', url)
    
    @staticmethod
    def put(url: str) -> HttpRequestBuilder:
        return HttpRequestBuilder('PUT', url)
    
    @staticmethod
    def delete(url: str) -> HttpRequestBuilder:
        return HttpRequestBuilder('DELETE', url)

# Much clearer usage:
# request = (Http.post('https://api.example.com/users')
#     .json({'name': 'John'})
#     .auth('user', 'pass')
#     .timeout(60)
#     .with_retry(3, 2)
#     .build())''',
        "Builder pattern with fluent interface makes complex object construction readable and self-documenting."
    ),
    
    # Replace Procedural Design with Objects
    (
        "Refactor this procedural code to use objects",
        '''def calculate_area(shape_type, dimensions):
    if shape_type == 'circle':
        radius = dimensions['radius']
        return 3.14159 * radius * radius
    elif shape_type == 'rectangle':
        return dimensions['width'] * dimensions['height']
    elif shape_type == 'triangle':
        return 0.5 * dimensions['base'] * dimensions['height']
    else:
        raise ValueError(f"Unknown shape: {shape_type}")

def calculate_perimeter(shape_type, dimensions):
    if shape_type == 'circle':
        return 2 * 3.14159 * dimensions['radius']
    elif shape_type == 'rectangle':
        return 2 * (dimensions['width'] + dimensions['height'])
    elif shape_type == 'triangle':
        return dimensions['a'] + dimensions['b'] + dimensions['c']
    else:
        raise ValueError(f"Unknown shape: {shape_type}")

# Usage:
# area = calculate_area('rectangle', {'width': 10, 'height': 5})''',
        '''from abc import ABC, abstractmethod
from dataclasses import dataclass
import math

class Shape(ABC):
    """Abstract base for all shapes."""
    
    @abstractmethod
    def area(self) -> float:
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        pass

@dataclass
class Circle(Shape):
    radius: float
    
    def area(self) -> float:
        return math.pi * self.radius ** 2
    
    def perimeter(self) -> float:
        return 2 * math.pi * self.radius

@dataclass
class Rectangle(Shape):
    width: float
    height: float
    
    def area(self) -> float:
        return self.width * self.height
    
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

@dataclass
class Triangle(Shape):
    base: float
    height: float
    side_a: float
    side_b: float
    side_c: float
    
    def area(self) -> float:
        return 0.5 * self.base * self.height
    
    def perimeter(self) -> float:
        return self.side_a + self.side_b + self.side_c
    
    @classmethod
    def equilateral(cls, side: float) -> 'Triangle':
        """Create equilateral triangle."""
        height = (math.sqrt(3) / 2) * side
        return cls(side, height, side, side, side)

# Usage:
# rect = Rectangle(10, 5)
# print(rect.area())       # 50
# print(rect.perimeter())  # 30''',
        "Objects encapsulate data and behavior together, making it easy to add new shapes."
    ),
    
    # Encapsulate Collection
    (
        "Refactor to encapsulate the collection",
        '''class Course:
    def __init__(self, name):
        self.name = name
        self.students = []  # Exposed list - anyone can modify!

# Usage - problematic:
course = Course("Python 101")
course.students.append(student1)  # Direct modification
course.students.remove(student2)  # No validation
course.students = []  # Can replace entire list!
external_list = course.students  # Reference leak
external_list.append(bad_student)  # Modifies course.students!''',
        '''from typing import Iterator, List

class Course:
    def __init__(self, name: str, max_students: int = 30):
        self.name = name
        self._max_students = max_students
        self._students: List[Student] = []
    
    @property
    def students(self) -> tuple:
        """Return immutable view of students."""
        return tuple(self._students)
    
    @property
    def student_count(self) -> int:
        return len(self._students)
    
    @property
    def is_full(self) -> bool:
        return self.student_count >= self._max_students
    
    def enroll(self, student: Student) -> None:
        """Enroll a student with validation."""
        if self.is_full:
            raise ValueError(f"Course {self.name} is full")
        if student in self._students:
            raise ValueError(f"{student.name} is already enrolled")
        if not student.is_eligible:
            raise ValueError(f"{student.name} is not eligible")
        self._students.append(student)
    
    def unenroll(self, student: Student) -> None:
        """Remove a student from the course."""
        if student not in self._students:
            raise ValueError(f"{student.name} is not enrolled")
        self._students.remove(student)
    
    def __iter__(self) -> Iterator[Student]:
        """Allow iteration over students."""
        return iter(self._students)
    
    def __contains__(self, student: Student) -> bool:
        """Check if student is enrolled."""
        return student in self._students

# Usage - controlled:
# course.enroll(student1)  # Validates before adding
# course.unenroll(student2)  # Validates before removing
# for student in course:  # Safe iteration
#     print(student.name)''',
        "Encapsulation prevents unauthorized modifications and enforces business rules."
    ),
    
    # Replace Nested Conditionals with Guard Clauses (TypeScript)
    (
        "Refactor this TypeScript function using guard clauses",
        '''function processPayment(order: Order | null, user: User | null): PaymentResult {
    let result: PaymentResult;
    
    if (order !== null) {
        if (user !== null) {
            if (order.items.length > 0) {
                if (order.total > 0) {
                    if (user.paymentMethod !== null) {
                        if (user.paymentMethod.isValid) {
                            // Finally, process the payment
                            const charge = chargePaymentMethod(user.paymentMethod, order.total);
                            if (charge.success) {
                                result = { success: true, transactionId: charge.id };
                            } else {
                                result = { success: false, error: charge.error };
                            }
                        } else {
                            result = { success: false, error: 'Payment method expired' };
                        }
                    } else {
                        result = { success: false, error: 'No payment method' };
                    }
                } else {
                    result = { success: false, error: 'Invalid order total' };
                }
            } else {
                result = { success: false, error: 'Order has no items' };
            }
        } else {
            result = { success: false, error: 'User required' };
        }
    } else {
        result = { success: false, error: 'Order required' };
    }
    
    return result;
}''',
        '''interface PaymentResult {
    success: boolean;
    transactionId?: string;
    error?: string;
}

function fail(error: string): PaymentResult {
    return { success: false, error };
}

function succeed(transactionId: string): PaymentResult {
    return { success: true, transactionId };
}

function processPayment(order: Order | null, user: User | null): PaymentResult {
    // Guard clauses - exit early for invalid states
    if (!order) {
        return fail('Order required');
    }
    
    if (!user) {
        return fail('User required');
    }
    
    if (order.items.length === 0) {
        return fail('Order has no items');
    }
    
    if (order.total <= 0) {
        return fail('Invalid order total');
    }
    
    if (!user.paymentMethod) {
        return fail('No payment method');
    }
    
    if (!user.paymentMethod.isValid) {
        return fail('Payment method expired');
    }
    
    // Happy path - all validations passed
    const charge = chargePaymentMethod(user.paymentMethod, order.total);
    
    return charge.success 
        ? succeed(charge.id)
        : fail(charge.error);
}''',
        "Guard clauses flatten the code and make the happy path obvious at the end."
    ),
    
    # Replace Primitive Obsession with Value Objects
    (
        "Refactor to use value objects instead of primitive types",
        '''def create_user(email: str, phone: str, zip_code: str) -> User:
    # Validation scattered throughout
    if '@' not in email or '.' not in email.split('@')[1]:
        raise ValueError("Invalid email")
    
    # Phone validation - inconsistent format
    phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    if len(phone) != 10 or not phone.isdigit():
        raise ValueError("Invalid phone")
    
    # ZIP code validation
    if len(zip_code) != 5 or not zip_code.isdigit():
        raise ValueError("Invalid ZIP code")
    
    return User(email=email.lower(), phone=phone, zip_code=zip_code)

# Later, validation needs to be repeated:
def send_email(email: str):
    if '@' not in email:  # Duplicated validation
        raise ValueError("Invalid email")
    # ...''',
        '''import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Email:
    """Value object for email addresses."""
    value: str
    
    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError(f"Invalid email: {self.value}")
        # Normalize on creation
        object.__setattr__(self, 'value', self.value.lower().strip())
    
    @staticmethod
    def _is_valid(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class PhoneNumber:
    """Value object for US phone numbers."""
    value: str
    
    def __post_init__(self):
        # Normalize: strip non-digits
        digits = re.sub(r'\\D', '', self.value)
        if len(digits) == 11 and digits[0] == '1':
            digits = digits[1:]  # Remove country code
        if len(digits) != 10:
            raise ValueError(f"Invalid phone number: {self.value}")
        object.__setattr__(self, 'value', digits)
    
    @property
    def formatted(self) -> str:
        return f"({self.value[:3]}) {self.value[3:6]}-{self.value[6:]}"
    
    def __str__(self) -> str:
        return self.formatted

@dataclass(frozen=True)
class ZipCode:
    """Value object for US ZIP codes."""
    value: str
    
    def __post_init__(self):
        digits = self.value.replace('-', '')[:5]
        if len(digits) != 5 or not digits.isdigit():
            raise ValueError(f"Invalid ZIP code: {self.value}")
        object.__setattr__(self, 'value', digits)
    
    def __str__(self) -> str:
        return self.value

def create_user(email: Email, phone: PhoneNumber, zip_code: ZipCode) -> User:
    # Validation already done by value objects!
    return User(email=email, phone=phone, zip_code=zip_code)

def send_email(email: Email):
    # Type guarantees it's valid - no check needed!
    send_to(str(email))

# Usage:
# user = create_user(
#     Email("John@Example.COM"),  # Normalized to lowercase
#     PhoneNumber("(555) 123-4567"),  # Normalized
#     ZipCode("12345")
# )''',
        "Value objects encapsulate validation and normalization, making invalid states unrepresentable."
    ),
    
    # Replace Setters with Builder in Tests
    (
        "Refactor test setup to use a builder pattern",
        '''def test_order_total_calculation():
    # Tedious setup with many setters
    user = User()
    user.id = 1
    user.name = "John"
    user.email = "john@example.com"
    user.membership = "gold"
    user.discount_rate = 0.1
    
    item1 = OrderItem()
    item1.id = 1
    item1.name = "Widget"
    item1.price = 10.00
    item1.quantity = 2
    
    item2 = OrderItem()
    item2.id = 2
    item2.name = "Gadget"
    item2.price = 25.00
    item2.quantity = 1
    
    order = Order()
    order.id = 1
    order.user = user
    order.items = [item1, item2]
    order.status = "pending"
    
    assert order.calculate_total() == 40.50  # With 10% discount''',
        '''# Test builders for clean, readable test setup
class UserBuilder:
    def __init__(self):
        self._user = User()
        # Sensible defaults
        self._user.id = 1
        self._user.name = "Test User"
        self._user.email = "test@example.com"
        self._user.membership = "basic"
        self._user.discount_rate = 0
    
    def with_id(self, id: int) -> 'UserBuilder':
        self._user.id = id
        return self
    
    def with_name(self, name: str) -> 'UserBuilder':
        self._user.name = name
        return self
    
    def as_gold_member(self) -> 'UserBuilder':
        self._user.membership = "gold"
        self._user.discount_rate = 0.1
        return self
    
    def as_silver_member(self) -> 'UserBuilder':
        self._user.membership = "silver"
        self._user.discount_rate = 0.05
        return self
    
    def build(self) -> User:
        return self._user

class OrderItemBuilder:
    def __init__(self):
        self._item = OrderItem()
        self._item.id = 1
        self._item.name = "Test Item"
        self._item.price = 10.00
        self._item.quantity = 1
    
    def with_price(self, price: float) -> 'OrderItemBuilder':
        self._item.price = price
        return self
    
    def with_quantity(self, qty: int) -> 'OrderItemBuilder':
        self._item.quantity = qty
        return self
    
    def named(self, name: str) -> 'OrderItemBuilder':
        self._item.name = name
        return self
    
    def build(self) -> OrderItem:
        return self._item

class OrderBuilder:
    def __init__(self):
        self._order = Order()
        self._order.id = 1
        self._order.status = "pending"
        self._order.items = []
        self._order.user = UserBuilder().build()
    
    def for_user(self, user: User) -> 'OrderBuilder':
        self._order.user = user
        return self
    
    def with_item(self, item: OrderItem) -> 'OrderBuilder':
        self._order.items.append(item)
        return self
    
    def with_items(self, *items: OrderItem) -> 'OrderBuilder':
        self._order.items.extend(items)
        return self
    
    def build(self) -> Order:
        return self._order

# Clean, readable tests:
def test_order_total_with_gold_discount():
    user = UserBuilder().as_gold_member().build()
    
    order = (OrderBuilder()
        .for_user(user)
        .with_item(OrderItemBuilder().with_price(10).with_quantity(2).build())
        .with_item(OrderItemBuilder().with_price(25).with_quantity(1).build())
        .build())
    
    assert order.calculate_total() == 40.50

def test_order_total_without_discount():
    order = (OrderBuilder()
        .with_item(OrderItemBuilder().with_price(10).with_quantity(2).build())
        .build())
    
    assert order.calculate_total() == 20.00''',
        "Test builders make tests readable, provide good defaults, and reduce setup duplication."
    ),
    
    # Separate Query from Modifier
    (
        "Refactor to separate query methods from modifier methods",
        '''class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_and_get_total(self, item, quantity):
        """Add item and return new total - does two things!"""
        self.items.append({'item': item, 'quantity': quantity})
        return sum(i['item'].price * i['quantity'] for i in self.items)
    
    def remove_and_check_empty(self, item_id):
        """Remove item and return if cart is now empty - does two things!"""
        self.items = [i for i in self.items if i['item'].id != item_id]
        return len(self.items) == 0
    
    def apply_coupon_and_get_discount(self, coupon_code):
        """Apply coupon and return discount amount - does two things!"""
        coupon = lookup_coupon(coupon_code)
        if coupon and coupon.is_valid:
            self.applied_coupon = coupon
            return self.total * coupon.discount_rate
        return 0''',
        '''class ShoppingCart:
    def __init__(self):
        self._items: list = []
        self._applied_coupon = None
    
    # --- Query Methods (no side effects) ---
    
    @property
    def total(self) -> float:
        """Get cart total before discounts."""
        return sum(i['item'].price * i['quantity'] for i in self._items)
    
    @property
    def discount_amount(self) -> float:
        """Get discount amount from applied coupon."""
        if not self._applied_coupon:
            return 0
        return self.total * self._applied_coupon.discount_rate
    
    @property
    def final_total(self) -> float:
        """Get total after discounts."""
        return self.total - self.discount_amount
    
    @property
    def is_empty(self) -> bool:
        """Check if cart has no items."""
        return len(self._items) == 0
    
    @property
    def item_count(self) -> int:
        """Get number of unique items."""
        return len(self._items)
    
    def has_item(self, item_id: int) -> bool:
        """Check if item is in cart."""
        return any(i['item'].id == item_id for i in self._items)
    
    # --- Modifier Methods (change state, return nothing or self) ---
    
    def add_item(self, item, quantity: int = 1) -> 'ShoppingCart':
        """Add item to cart."""
        existing = next((i for i in self._items if i['item'].id == item.id), None)
        if existing:
            existing['quantity'] += quantity
        else:
            self._items.append({'item': item, 'quantity': quantity})
        return self
    
    def remove_item(self, item_id: int) -> 'ShoppingCart':
        """Remove item from cart."""
        self._items = [i for i in self._items if i['item'].id != item_id]
        return self
    
    def apply_coupon(self, coupon_code: str) -> bool:
        """Apply coupon code. Returns True if valid."""
        coupon = lookup_coupon(coupon_code)
        if coupon and coupon.is_valid:
            self._applied_coupon = coupon
            return True
        return False
    
    def clear(self) -> 'ShoppingCart':
        """Remove all items."""
        self._items = []
        self._applied_coupon = None
        return self

# Usage - clear separation:
# cart.add_item(widget, 2)
# cart.add_item(gadget, 1)
# print(f"Total: ${cart.total}")  # Query
# 
# cart.apply_coupon("SAVE10")     # Modifier
# print(f"Discount: ${cart.discount_amount}")  # Query
# print(f"Final: ${cart.final_total}")  # Query''',
        "Command-Query Separation makes code predictable - queries are safe to call anywhere."
    ),
    
    # Remove Middle Man
    (
        "Refactor to remove the middle man delegation",
        '''class Department:
    def __init__(self, manager):
        self._manager = manager
    
    # All these just delegate to manager - middle man!
    def get_manager_name(self):
        return self._manager.name
    
    def get_manager_email(self):
        return self._manager.email
    
    def get_manager_phone(self):
        return self._manager.phone
    
    def get_manager_office(self):
        return self._manager.office
    
    def is_manager_available(self):
        return self._manager.is_available()
    
    def schedule_with_manager(self, time):
        return self._manager.schedule_meeting(time)

# Caller has to go through department for everything:
name = department.get_manager_name()
email = department.get_manager_email()
department.schedule_with_manager(meeting_time)''',
        '''class Department:
    def __init__(self, manager: 'Manager'):
        self._manager = manager
        self.name = ""
        self.budget = 0
    
    @property
    def manager(self) -> 'Manager':
        """Expose manager directly - no middle man."""
        return self._manager
    
    @manager.setter
    def manager(self, new_manager: 'Manager'):
        self._manager = new_manager
    
    # Only keep delegation for department-level operations
    def get_department_info(self) -> dict:
        """Get department summary including manager info."""
        return {
            'name': self.name,
            'budget': self.budget,
            'manager': self.manager.name,
            'manager_email': self.manager.email
        }

# Caller accesses manager directly when needed:
name = department.manager.name
email = department.manager.email
department.manager.schedule_meeting(meeting_time)

# Or use department-level methods for aggregate operations:
info = department.get_department_info()''',
        "Expose the delegate directly instead of creating passthrough methods for everything."
    ),
]


def generate_examples() -> List[Dict]:
    """Generate training examples from refactoring data."""
    examples = []
    
    for instruction, before, after, explanation in REFACTORING_EXAMPLES:
        response = {
            "action": "provide_code",
            "analysis": f"The original code has issues that can be improved through refactoring.",
            "before_code": before,
            "after_code": after,
            "explanation": explanation
        }
        
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": f"{instruction}\n\nOriginal code:\n```\n{before}\n```",
            "response": json.dumps(response, indent=2)
        })
    
    return examples


def save_examples(examples: List[Dict], filename: str = "refactoring.jsonl"):
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

