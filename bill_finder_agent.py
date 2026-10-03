import json
import os

from database import get_bills, save_bill

EMAILS_FILE = "demo_emails.json"


def _load_emails():
    if not os.path.exists(EMAILS_FILE):
        return []
    try:
        with open(EMAILS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []


def find_bills():
    """
    Finds bills from the demo connected inbox.
    Keeps the structured fields and skips emails that are not bills.
    """
    bills = []

    for email in _load_emails():
        if email.get("is_bill") is False:
            continue

        content = email.get("content", email.get("body", ""))

        bills.append(
            {
                "source": "demo_email",
                "sender": email.get("sender", ""),
                "subject": email.get("subject", ""),
                "content": content,
                "text": content,
                "provider": email.get("provider", ""),
                "bill_type": email.get("bill_type", ""),
                "amount": email.get("amount", 0),
                "due_date": email.get("due_date", ""),
                "account_number": email.get("reference_number", ""),
            }
        )

    return bills


def find_bills_from_inbox():
    """
    Full pipeline used by the app button:
    inbox -> structured bill -> database (skipping duplicates).
    Returns the number of NEW bills saved.
    """
    # bills table columns: id, type, provider, consumer, amount, due_date, status, created
    existing = {
        (str(b[2]).lower(), str(b[5]), float(b[4] or 0)) for b in get_bills()
    }

    added = 0
    for item in find_bills():
        provider = item.get("provider", "")
        amount = float(item.get("amount") or 0)
        due_date = item.get("due_date", "")

        if not provider or amount <= 0:
            continue

        key = (provider.lower(), str(due_date), amount)
        if key in existing:
            continue

        save_bill(
            {
                "bill_type": item.get("bill_type") or "Other",
                "provider": provider,
                "account_number": item.get("account_number", ""),
                "amount": amount,
                "due_date": due_date,
                "extracted_text": item.get("subject", ""),
            }
        )
        existing.add(key)
        added += 1

    return added
