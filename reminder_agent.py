import re
from datetime import datetime, date

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Asia/Karachi")
except Exception:  # tzdata missing (some Windows setups)
    _TZ = None


def _today():
    return datetime.now(_TZ).date() if _TZ else date.today()


def parse_date(date_str):
    """
    Tries multiple common date formats extracted from OCR or user input.
    """
    if not date_str:
        return None

    cleaned_str = str(date_str).strip()
    
    # Common date formats in utility bills
    date_formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d %B %Y",       # e.g., 15 October 2026
        "%d %b %Y",       # e.g., 15 Oct 2026
        "%B %d, %Y",      # e.g., October 15, 2026
        "%b %d, %Y",      # e.g., Oct 15, 2026
        "%d-%b-%Y",       # e.g., 15-Oct-2026
        "%d-%B-%Y",       # e.g., 15-October-2026
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(cleaned_str, fmt).date()
        except ValueError:
            continue

    return None


def get_reminder_status(due_date):
    """
    Returns a human-readable reminder message.
    """
    info = get_reminder_details(due_date)
    return info["message"]


def get_reminder_details(due_date):
    """
    Returns rich reminder data including urgency level and days remaining.
    Urgency levels: 'critical', 'warning', 'upcoming', 'normal', 'unknown'
    """
    if not due_date:
        return {
            "message": "Due date unavailable",
            "days_left": None,
            "urgency": "unknown",
            "color": "#64748b"
        }

    parsed_due = parse_date(due_date)

    if not parsed_due:
        return {
            "message": "Invalid due date",
            "days_left": None,
            "urgency": "unknown",
            "color": "#ef4444"
        }

    today = _today()
    days_left = (parsed_due - today).days

    if days_left < 0:
        return {
            "message": f"Overdue by {abs(days_left)} day(s)",
            "days_left": days_left,
            "urgency": "critical",
            "color": "#ef4444"
        }
    elif days_left == 0:
        return {
            "message": "Due today",
            "days_left": 0,
            "urgency": "critical",
            "color": "#f97316"
        }
    elif days_left == 1:
        return {
            "message": "Due tomorrow",
            "days_left": 1,
            "urgency": "warning",
            "color": "#f59e0b"
        }
    elif days_left <= 3:
        return {
            "message": f"Due in {days_left} day(s)",
            "days_left": days_left,
            "urgency": "warning",
            "color": "#eab308"
        }
    elif days_left <= 7:
        return {
            "message": f"Due next week ({days_left} days left)",
            "days_left": days_left,
            "urgency": "upcoming",
            "color": "#38bdf8"
        }
    else:
        return {
            "message": f"{days_left} day(s) remaining",
            "days_left": days_left,
            "urgency": "normal",
            "color": "#10b981"
        }


def get_active_reminders_from_bills(bills):
    """
    Filters pending bills and sorts them by nearest due date.
    Assumes bill tuple format: (id, bill_type, provider, consumer, amount, due_date, status, ...)
    """
    reminders = []

    for bill in bills:
        # Ignore already paid bills
        status = bill[6]
        if str(status).lower() == "paid":
            continue

        b_id = bill[0]
        b_type = bill[1]
        provider = bill[2]
        amount = bill[4]
        due_date = bill[5]

        details = get_reminder_details(due_date)
        reminders.append({
            "bill_id": b_id,
            "title": provider or b_type or "Utility Bill",
            "amount": amount,
            "due_date": due_date,
            "message": details["message"],
            "urgency": details["urgency"],
            "color": details["color"],
            "days_left": details["days_left"] if details["days_left"] is not None else 9999
        })

    # Sort so overdue and imminent bills appear first
    reminders.sort(key=lambda x: x["days_left"])
    return reminders
