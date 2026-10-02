from datetime import datetime
import uuid


def simulate_payment(bill):

    transaction_id = (
        "DEMO-"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )
        + "-"
        + uuid.uuid4().hex[:6].upper()
    )

    return {

        "approved": True,

        "transaction_id":
            transaction_id,

        "message":
            "Demo payment successful"
    }
