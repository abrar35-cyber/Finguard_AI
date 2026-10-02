import sqlite3

from pathlib import Path
from datetime import datetime


DB_FILE = (
    Path(__file__).resolve().parent.parent
    / "billpay.db"
)


def connect():

    return sqlite3.connect(
        DB_FILE
    )


def init_db():

    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            provider TEXT,

            bill_type TEXT,

            amount REAL,

            due_date TEXT,

            reference_number TEXT UNIQUE,

            status TEXT,

            source TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            bill_id INTEGER,

            provider TEXT,

            amount REAL,

            payment_date TEXT,

            transaction_id TEXT,

            status TEXT
        )
    """)

    connection.commit()

    connection.close()


def save_bill(bill):

    connection = connect()

    try:

        connection.execute(
            """
            INSERT INTO bills
            (
                provider,
                bill_type,
                amount,
                due_date,
                reference_number,
                status,
                source
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,

            (
                bill["provider"],
                bill["bill_type"],
                bill["amount"],
                bill["due_date"],
                bill["reference_number"],
                bill.get(
                    "status",
                    "Pending"
                ),
                bill.get(
                    "source",
                    "Upload"
                )
            )
        )

        connection.commit()

    except sqlite3.IntegrityError:

        pass

    connection.close()


def get_bills():

    connection = connect()

    rows = connection.execute(
        """
        SELECT
            id,
            provider,
            bill_type,
            amount,
            due_date,
            reference_number,
            status,
            source

        FROM bills

        ORDER BY due_date ASC
        """
    ).fetchall()

    connection.close()

    keys = [
        "id",
        "provider",
        "bill_type",
        "amount",
        "due_date",
        "reference_number",
        "status",
        "source"
    ]

    return [
        dict(zip(keys, row))
        for row in rows
    ]


def mark_bill_paid(
    bill_id
):

    connection = connect()

    connection.execute(
        """
        UPDATE bills
        SET status = 'Paid'
        WHERE id = ?
        """,
        (bill_id,)
    )

    connection.commit()

    connection.close()


def save_payment(
    bill,
    transaction_id
):

    connection = connect()

    connection.execute(
        """
        INSERT INTO payments
        (
            bill_id,
            provider,
            amount,
            payment_date,
            transaction_id,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,

        (
            bill["id"],
            bill["provider"],
            bill["amount"],
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            transaction_id,
            "Paid"
        )
    )

    connection.commit()

    connection.close()


def get_payments():

    connection = connect()

    rows = connection.execute(
        """
        SELECT
            provider,
            amount,
            payment_date,
            transaction_id,
            status

        FROM payments

        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    keys = [
        "provider",
        "amount",
        "payment_date",
        "transaction_id",
        "status"
    ]

    return [
        dict(zip(keys, row))
        for row in rows
    ]
