import json
import os


def find_bills():

    """
    Finds bills from the demo connected inbox.
    """

    file_path = "demo_emails.json"

    if not os.path.exists(file_path):
        return []

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            emails = json.load(file)

    except Exception:
        return []

    bills = []

    for email in emails:

        content = email.get(
            "content",
            email.get("body", "")
        )

        subject = email.get(
            "subject",
            ""
        )

        bills.append(
            {
                "source": "demo_email",
                "sender": email.get("sender", ""),
                "subject": subject,
                "content": content,
                "text": content
            }
        )

    return bills
