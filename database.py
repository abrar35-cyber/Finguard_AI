import sqlite3


DB_NAME = "billpay.db"


def get_connection():

    return sqlite3.connect(
        DB_NAME
    )


def init_db():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            bill_type TEXT,
            amount REAL,
            due_date TEXT,
            account_number TEXT,
            status TEXT DEFAULT 'pending'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            amount REAL,
            transaction_id TEXT,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()

    connection.close()


def save_bill(bill):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO bills
        (
            provider,
            bill_type,
            amount,
            due_date,
            account_number,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            bill.get("provider"),
            bill.get("bill_type"),
            bill.get("amount"),
            bill.get("due_date"),
            bill.get("account_number"),
            "pending"
        )
    )

    connection.commit()

    connection.close()


def get_bills():

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM bills
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def mark_bill_paid(bill_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE bills
        SET status = 'paid'
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

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO payments
        (
            provider,
            amount,
            transaction_id
        )
        VALUES (?, ?, ?)
        """,
        (
            bill.get("provider"),
            bill.get("amount"),
            transaction_id
        )
    )

    connection.commit()

    connection.close()


def get_payment_history():

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM payments
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]
