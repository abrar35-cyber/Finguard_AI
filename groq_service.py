import json
import streamlit as st


def extract_bill_with_groq(text):

    try:

        from groq import Groq

        api_key = st.secrets.get(
            "GROQ_API_KEY"
        )

        if not api_key:
            return None

        client = Groq(
            api_key=api_key
        )

        prompt = f"""
Extract bill information from the following bill text.

Return ONLY valid JSON.

Required keys:

provider
bill_type
amount
due_date
reference_number
status
source

Use YYYY-MM-DD for due_date.

If information is missing, use null.

Bill text:

{text[:12000]}
"""

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[

                {
                    "role": "system",
                    "content":
                    "You extract structured billing information accurately. Return JSON only."
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0
        )

        content = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        if content.startswith("```"):

            content = (
                content
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        return json.loads(
            content
        )

    except Exception:

        return None
