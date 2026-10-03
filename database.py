import sqlite3
from datetime import datetime

DB_NAME = "finguard.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def _add_column(cursor, table, column, ddl):
    cols = [r[1] for r in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            wallet_provider TEXT,
            wallet_number TEXT,
            created_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_type TEXT,
            provider TEXT,
            consumer_number TEXT,
            amount REAL,
            due_date TEXT,
            status TEXT DEFAULT 'Pending',
            extracted_text TEXT,
            created_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER,
            amount REAL,
            payment_method TEXT,
            status TEXT DEFAULT 'Successful',
            paid_at TEXT
        )
        """
    )

    # Upgrade older databases so each bill and payment belongs to a user
    _add_column(cursor, "bills", "user_email", "TEXT")
    _add_column(cursor, "payments", "user_email", "TEXT")

    connection.commit()
    connection.close()


# ---------------------------------------------------------
# USERS
# ---------------------------------------------------------
def register_user(email, name, wallet_provider, wallet_number):
    email = (email or "").strip().lower()
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO users (email, name, wallet_provider, wallet_number, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            name = excluded.name,
            wallet_provider = excluded.wallet_provider,
            wallet_number = excluded.wallet_number
        """,
        (email, name, wallet_provider, wallet_number, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    connection.commit()
    connection.close()
    return get_user(email)


def get_user(email):
    email = (email or "").strip().lower()
    connection = get_connection()
    row = connection.execute(
        "SELECT email, name, wallet_provider, wallet_number FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    connection.close()
    if not row:
        return None
    return {"email": row[0], "name": row[1], "wallet_provider": row[2], "wallet_number": row[3]}


# ---------------------------------------------------------
# BILLS
# ---------------------------------------------------------
def add_bill(
    bill_type="Other",
    provider="",
    consumer_number="",
    amount=0.0,
    due_date="",
    extracted_text="",
    user_email="",
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO bills (
            bill_type, provider, consumer_number, amount, due_date,
            status, extracted_text, created_at, user_email
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bill_type,
            provider,
            consumer_number,
            float(amount or 0.0),
            due_date,
            "Pending",
            extracted_text,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            (user_email or "").strip().lower(),
        ),
    )

    bill_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return bill_id


# Backward compatibility for agents passing dict
def save_bill(bill, user_email=""):
    return add_bill(
        bill_type=bill.get("bill_type", "Other"),
        provider=bill.get("provider", ""),
        consumer_number=bill.get("account_number") or bill.get("consumer_number", ""),
        amount=bill.get("amount", 0.0),
        due_date=bill.get("due_date", ""),
        extracted_text=bill.get("extracted_text", ""),
        user_email=user_email,
    )


def get_bills(user_email=None):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT id, bill_type, provider, consumer_number, amount, due_date, status, created_at
        FROM bills
    """
    params = ()
    if user_email is not None:
        query += " WHERE user_email = ?"
        params = ((user_email or "").strip().lower(),)
    query += " ORDER BY id DESC"

    rows = cursor.execute(query, params).fetchall()
    connection.close()
    return rows


def get_payments(user_email=None):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            payments.id,
            COALESCE(bills.provider, 'Utility Bill') as provider,
            payments.amount,
            payments.payment_method,
            payments.status,
            payments.paid_at
        FROM payments
        LEFT JOIN bills ON payments.bill_id = bills.id
    """
    params = ()
    if user_email is not None:
        query += " WHERE payments.user_email = ?"
        params = ((user_email or "").strip().lower(),)
    query += " ORDER BY payments.id DESC"

    rows = cursor.execute(query, params).fetchall()
    connection.close()
    return rows


def add_payment(bill_id, amount, method="Online", user_email=""):
    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Do not record a second payment for a bill that is already paid
    if bill_id:
        already = cursor.execute(
            "SELECT status FROM bills WHERE id = ?", (bill_id,)
        ).fetchone()
        if already and str(already[0]).lower() == "paid":
            connection.close()
            return False

    cursor.execute(
        """
        INSERT INTO payments (bill_id, amount, payment_method, status, paid_at, user_email)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (bill_id, float(amount or 0.0), method, "Successful", now, (user_email or "").strip().lower()),
    )

    if bill_id:
        cursor.execute("UPDATE bills SET status = 'Paid' WHERE id = ?", (bill_id,))

    connection.commit()
    connection.close()
    return True


def mark_bill_paid(bill_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE bills SET status = 'Paid' WHERE id = ?", (bill_id,))
    connection.commit()
    connection.close()


# Backward compatibility alias
def get_payment_history(user_email=None):
    return get_payments(user_email)
