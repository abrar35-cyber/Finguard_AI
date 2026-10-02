from services.groq_service import extract_bill_with_groq


def analyze_bill(text):

    result = extract_bill_with_groq(text)

    if result:

        required = [
            "provider",
            "amount",
            "due_date",
            "reference_number"
        ]

        result["valid"] = all(
            result.get(field)
            for field in required
        )

        if result.get("status") is None:
            result["status"] = "Pending"

        if result.get("source") is None:
            result["source"] = "Physical Bill"

        return result

    return {
        "valid": False,
        "message": (
            "Groq could not extract enough "
            "information from this bill."
        )
    }
