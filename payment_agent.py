from payment_service import process_payment


def make_payment(bill):

    """
    Payment agent.
    Actual payment is simulated for the MVP.
    """

    if not bill:
        return {
            "success": False,
            "message": "Invalid bill."
        }

    amount = bill.get("amount")

    if not amount:
        return {
            "success": False,
            "message": "Bill amount is missing."
        }

    return process_payment(bill)
