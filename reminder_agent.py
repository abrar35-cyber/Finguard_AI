from datetime import datetime


def get_reminder_status(due_date):

    if not due_date:
        return "Due date unavailable"

    try:

        due = datetime.strptime(
            str(due_date),
            "%Y-%m-%d"
        ).date()

        today = datetime.today().date()

        days_left = (
            due - today
        ).days

        if days_left < 0:

            return f"Overdue by {abs(days_left)} day(s)"

        elif days_left == 0:

            return "Due today"

        elif days_left == 1:

            return "Due tomorrow"

        elif days_left <= 3:

            return f"Due in {days_left} day(s)"

        else:

            return f"{days_left} day(s) remaining"

    except Exception:

        return "Invalid due date"
