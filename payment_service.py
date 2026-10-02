import uuid


def process_payment(bill):

    transaction_id = (
        "TXN-"
        + uuid.uuid4().hex[:10].upper()
    )

    return {
        "success": True,
        "transaction_id": transaction_id,
        "message": "Demo payment successful."
    }
