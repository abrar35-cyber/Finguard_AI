from datetime import date, datetime


def get_reminder(bill):

    try:

        due_date = datetime.strptime(
            bill["due_date"],
            "%Y-%m-%d"
        ).date()

        days = (
            due_date - date.today()
        ).days

    except Exception:

        return {
            "level": "normal",
            "message": "Due date unavailable",
            "days": None
        }

    if bill.get("status") == "Paid":

        return {
            "level": "paid",
            "message": "Paid",
            "days": days
        }

    if days < 0:

        return {
            "level": "urgent",
            "message": f"Overdue by {abs(days)} day(s)",
            "days": days
        }

    if days == 0:

        return {
            "level": "urgent",
            "message": "Due today",
            "days": days
        }

    if days <= 2:

        return {
            "level": "urgent",
            "message": f"Due in {days} day(s)",
            "days": days
        }

    if days <= 5:

        return {
            "level": "warning",
            "message": f"Due in {days} day(s)",
            "days": days
        }

    return {
        "level": "normal",
        "message": f"Due in {days} day(s)",
        "days": days
    }
