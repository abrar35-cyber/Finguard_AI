import sqlite3
from datetime import datetime

DB_NAME = "finguard.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

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

    connection.commit()
    connection.close()


def add_bill(
    bill_type="Other",
    provider="",
    consumer_number="",
    amount=0.0,
    due_date="",
    extracted_text="",
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO bills (
            bill_type,
            provider,
            consumer_number,
            amount,
            due_date,
            status,
            extracted_text,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        ),
    )

    bill_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return bill_id


# Backward compatibility for agents passing dict
def save_bill(bill):
    return add_bill(
        bill_type=bill.get("bill_type", "Other"),
        provider=bill.get("provider", ""),
        consumer_number=bill.get("account_number") or bill.get("consumer_number", ""),
        amount=bill.get("amount", 0.0),
        due_date=bill.get("due_date", ""),
        extracted_text=bill.get("extracted_text", ""),
    )


def get_bills():
    connection = get_connection()
    cursor = connection.cursor()

    rows = cursor.execute(
        """
        SELECT
            id,
            bill_type,
            provider,
            consumer_number,
            amount,
            due_date,
            status,
            created_at
        FROM bills
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()
    return rows


def get_payments():
    connection = get_connection()
    cursor = connection.cursor()

    rows = cursor.execute(
        """
        SELECT
            payments.id,
            COALESCE(bills.provider, 'Utility Bill') as provider,
            payments.amount,
            payments.payment_method,
            payments.status,
            payments.paid_at
        FROM payments
        LEFT JOIN bills ON payments.bill_id = bills.id
        ORDER BY payments.id DESC
        """
    ).fetchall()

    connection.close()
    return rows


def add_payment(bill_id, amount, method="Online"):
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
        INSERT INTO payments (bill_id, amount, payment_method, status, paid_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (bill_id, float(amount or 0.0), method, "Successful", now),
    )

    if bill_id:
        cursor.execute(
            """
            UPDATE bills
            SET status = 'Paid'
            WHERE id = ?
            """,
            (bill_id,),
        )

    connection.commit()
    connection.close()
    return True


def mark_bill_paid(bill_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE bills
        SET status = 'Paid'
        WHERE id = ?
        """,
        (bill_id,),
    )

    connection.commit()
    connection.close()


# Backward compatibility alias
def get_payment_history():
    return get_payments()
