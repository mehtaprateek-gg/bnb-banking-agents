"""Generate mock banking data with Indian names and ₹ context."""

import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

from backend.shared.models.banking import (
    Customer, Transaction, Account, Language
)

fake = Faker("en_IN")

# Fixed personas from architecture doc
PERSONAS = {
    "CUST-001-ANANYA": {
        "name": "Ananya Deshmukh",
        "phone": "+919876543210",
        "email": "ananya.deshmukh@gmail.com",
        "segment": "retail",
        "account_type": "savings",
        "language": Language.HINDI,
        "rm": "Sunita Nair",
        "city": "Pune",
    },
    "CUST-002-PRIYA": {
        "name": "Priya Sharma",
        "phone": "+919812345678",
        "email": "priya.sharma@tcs.com",
        "segment": "retail",
        "account_type": "savings",
        "language": Language.HINGLISH,
        "rm": "Vikram Mehta",
        "city": "Delhi",
    },
    "CUST-003-RAJESH": {
        "name": "Rajesh Iyer",
        "phone": "+919898765432",
        "email": "rajesh.iyer@business.com",
        "segment": "business",
        "account_type": "current",
        "language": Language.ENGLISH,
        "rm": "Vikram Mehta",
        "city": "Mumbai",
    },
}

MERCHANTS = [
    ("Swiggy Order", "Food"),
    ("Zomato Delivery", "Food"),
    ("Amazon India", "Shopping"),
    ("Flipkart", "Shopping"),
    ("QuickMart Delhi", "Shopping"),
    ("BigBazaar", "Groceries"),
    ("DMart", "Groceries"),
    ("Reliance Fresh", "Groceries"),
    ("BSES Electricity", "Utilities"),
    ("Airtel Broadband", "Utilities"),
    ("Jio Recharge", "Utilities"),
    ("Indian Oil Petrol", "Transport"),
    ("Uber India", "Transport"),
    ("Ola Ride", "Transport"),
    ("IRCTC Train", "Travel"),
    ("MakeMyTrip", "Travel"),
    ("Apollo Pharmacy", "Health"),
    ("Netflix India", "Entertainment"),
    ("Hotstar", "Entertainment"),
    ("GST Payment", "Tax"),
]

IFSC_CODES = ["BNBN0001234", "BNBN0005678", "BNBN0009012"]
BRANCHES = ["Connaught Place, Delhi", "Andheri West, Mumbai", "Koregaon Park, Pune"]


def generate_aadhaar_masked() -> str:
    return f"XXXX XXXX {random.randint(1000, 9999)}"


def generate_pan_masked() -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"{''.join(random.choices(letters, k=5))}{random.randint(1000, 9999)}{''.join(random.choices(letters, k=1))}"


def generate_account_number() -> str:
    return f"XXXX{random.randint(1000, 9999)}"


def generate_customers() -> list[Customer]:
    """Generate the 3 fixed customer personas."""
    customers = []
    for cust_id, data in PERSONAS.items():
        customers.append(Customer(
            customer_id=cust_id,
            name=data["name"],
            phone=data["phone"],
            email=data["email"],
            aadhaar_masked=generate_aadhaar_masked(),
            pan_masked=generate_pan_masked(),
            account_number=generate_account_number(),
            account_type=data["account_type"],
            segment=data["segment"],
            rm_name=data["rm"],
            language_preference=data["language"],
        ))
    return customers


def generate_accounts(customers: list[Customer]) -> list[Account]:
    """Generate accounts for each customer."""
    accounts = []
    for i, customer in enumerate(customers):
        accounts.append(Account(
            account_id=f"ACC-{uuid.uuid4().hex[:8].upper()}",
            customer_id=customer.customer_id,
            account_number=customer.account_number or generate_account_number(),
            account_type=customer.account_type or "savings",
            balance=random.uniform(15000, 500000),
            ifsc_code=IFSC_CODES[i % len(IFSC_CODES)],
            branch=BRANCHES[i % len(BRANCHES)],
        ))
    return accounts


def generate_transactions(customer_id: str, days: int = 30, count: int = 25) -> list[Transaction]:
    """Generate realistic transactions for a customer."""
    transactions = []
    now = datetime.utcnow()

    # Add salary credit
    transactions.append(Transaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer_id,
        date=now - timedelta(days=4),
        description="Salary Credit - TCS" if customer_id == "CUST-002-PRIYA" else "Business Income",
        amount=85000.0 if customer_id == "CUST-002-PRIYA" else 150000.0,
        category="Income",
        is_credit=True,
    ))

    # Add disputed transaction for Priya
    if customer_id == "CUST-002-PRIYA":
        transactions.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:8].upper()}",
            customer_id=customer_id,
            date=now - timedelta(days=1),
            description="QuickMart Delhi",
            amount=15000.0,
            category="Shopping",
            merchant="QuickMart Delhi",
            is_disputed=True,
        ))

    # Generate random transactions
    for _ in range(count - 2):
        merchant_name, category = random.choice(MERCHANTS)
        amount = round(random.uniform(100, 8000), 2)
        if category == "Tax":
            amount = round(random.uniform(5000, 25000), 2)

        transactions.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:8].upper()}",
            customer_id=customer_id,
            date=now - timedelta(days=random.randint(0, days), hours=random.randint(0, 23)),
            description=merchant_name,
            amount=amount,
            category=category,
            merchant=merchant_name,
        ))

    transactions.sort(key=lambda t: t.date, reverse=True)
    return transactions


def create_demo_customer(name: str, phone: str) -> tuple[Customer, Account]:
    """Create a new demo customer with auto-generated mock data.

    Only name and phone are real; everything else is simulated.
    Returns (customer, account) tuple.
    Raises ValueError if phone is already registered.
    """
    phone = phone.strip().replace(" ", "")
    if not phone.startswith("+"):
        # If already has country code 91, just add +
        if phone.startswith("91") and len(phone) > 10:
            phone = "+" + phone
        else:
            phone = "+91" + phone.lstrip("0")

    # Check for duplicate phone number
    for c in get_all_customers():
        if c.phone == phone:
            raise ValueError(f"Phone {phone} is already registered to {c.name} ({c.customer_id})")

    # Generate a sequential customer ID
    seq = len(_dynamic_customers) + 4  # 1-3 are fixed personas
    slug = name.upper().split()[0][:8] if name else "DEMO"
    customer_id = f"CUST-{seq:03d}-{slug}"

    first_name = name.split()[0] if name else "Demo"
    last_name = name.split()[-1] if len(name.split()) > 1 else "User"
    email = f"{first_name.lower()}.{last_name.lower()}@demo.com"

    customer = Customer(
        customer_id=customer_id,
        name=name,
        phone=phone,
        email=email,
        aadhaar_masked=generate_aadhaar_masked(),
        pan_masked=generate_pan_masked(),
        account_number=generate_account_number(),
        account_type="savings",
        segment="retail",
        rm_name=random.choice(["Vikram Mehta", "Sunita Nair"]),
        language_preference=Language.HINGLISH,
    )

    account = Account(
        account_id=f"ACC-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer_id,
        account_number=customer.account_number or generate_account_number(),
        account_type="savings",
        balance=round(random.uniform(25000, 300000), 2),
        ifsc_code=random.choice(IFSC_CODES),
        branch=random.choice(BRANCHES),
    )

    _dynamic_customers.append(customer)
    _dynamic_accounts.append(account)

    return customer, account


# In-memory store for dynamically added demo customers
_dynamic_customers: list[Customer] = []
_dynamic_accounts: list[Account] = []


def delete_dynamic_customer(customer_id: str) -> bool:
    """Remove a dynamically added customer. Returns True if found and deleted."""
    global _dynamic_customers, _dynamic_accounts
    for i, c in enumerate(_dynamic_customers):
        if c.customer_id == customer_id:
            _dynamic_customers.pop(i)
            # Also remove the matching account
            _dynamic_accounts = [a for a in _dynamic_accounts if a.customer_id != customer_id]
            return True
    return False


def get_all_customers() -> list[Customer]:
    """Return fixed personas + any dynamically added demo customers."""
    return generate_customers() + _dynamic_customers


def get_all_accounts() -> list[Account]:
    """Return accounts for all customers (fixed + dynamic)."""
    return generate_accounts(generate_customers()) + _dynamic_accounts


def generate_all_mock_data() -> dict:
    """Generate complete mock banking dataset (includes dynamic customers)."""
    customers = get_all_customers()
    accounts = get_all_accounts()
    all_transactions = {}
    for customer in customers:
        all_transactions[customer.customer_id] = generate_transactions(customer.customer_id)

    return {
        "customers": customers,
        "accounts": accounts,
        "transactions": all_transactions,
    }
