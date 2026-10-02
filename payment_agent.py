from services.payment_service import simulate_payment


def prepare_payment(bill):

    if bill.get("status") == "Paid":

        return {
            "approved": False,
            "message": "Bill is already paid."
        }

    return simulate_payment(
        bill
    )
