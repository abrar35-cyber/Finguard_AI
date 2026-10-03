import json
import streamlit as st
from groq import Groq


def get_groq_client():

    api_key = st.secrets.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    return Groq(
        api_key=api_key
    )


def extract_bill_with_groq(text):

    client = get_groq_client()

    prompt = f"""
You are a bill information extraction assistant.

Extract information from the bill text below.

Return ONLY valid JSON with exactly these fields:

provider
bill_type
amount
due_date
account_number

Rules:
- If a value is unavailable, use null.
- Keep amount as a number when possible.
- Use YYYY-MM-DD for due_date when the date is clear.
- Do not invent information.

Bill text:

{text}
"""

    response = client.chat.completions.create(

        model="openai/gpt-oss-120b",

        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured information from bills. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0,

        response_format={
            "type": "json_object"
        }
    )

    content = response.choices[0].message.content

    try:

        return json.loads(content)

    except json.JSONDecodeError:

        content = content.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

        try:
            return json.loads(content)

        except Exception:

            return None
