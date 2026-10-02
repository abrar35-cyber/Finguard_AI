import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "demo_emails.json"
)


def find_bills():

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        emails = json.load(file)

    bills = []

    for email in emails:

        if email.get("is_bill"):

            bills.append({

                "provider": email["provider"],

                "bill_type": email["bill_type"],

                "amount": float(
                    email["amount"]
                ),

                "due_date": email["due_date"],

                "reference_number":
                    email["reference_number"],

                "status": "Pending",

                "source": "Demo Gmail"
            })

    return bills
