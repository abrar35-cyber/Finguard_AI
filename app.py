import streamlit as st

from bill_finder_agent import find_bills
from bill_intelligence_agent import analyze_bill
from agents.reminder_agent import get_reminder
from agents.payment_agent import prepare_payment

from services.ocr_service import extract_text_from_image

from database.database import (
    init_db,
    save_bill,
    get_bills,
    save_payment,
    get_payments,
    mark_bill_paid
)


st.set_page_config(
    page_title="BillPay AI",
    page_icon="💳",
    layout="wide"
)

init_db()


# -----------------------------
# Styling
# -----------------------------

st.markdown("""
<style>

.block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

.bill-card {
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    background: white;
    margin-bottom: 12px;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# Sidebar
# -----------------------------

st.title("BillPay AI")

st.caption(
    "Find bills automatically, understand them, track due dates "
    "and pay only after user approval."
)

with st.sidebar:

    st.header("Navigation")

    page = st.radio(
        "Go to",
        [
            "Dashboard",
            "My Bills",
            "AI Assistant",
            "Payments",
            "History"
        ]
    )

    st.divider()

    st.caption("BillPay AI — Hackathon MVP")
    st.caption("Zero-cost demo architecture")


# -----------------------------
# Helper
# -----------------------------

def scan_demo_inbox():

    bills = find_bills()

    existing = get_bills()

    existing_refs = {
        bill["reference_number"]
        for bill in existing
    }

    added = 0

    for bill in bills:

        if bill["reference_number"] not in existing_refs:

            save_bill(bill)
            added += 1

    return added


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    bills = get_bills()

    paid = [
        b for b in bills
        if b["status"] == "Paid"
    ]

    pending = [
        b for b in bills
        if b["status"] != "Paid"
    ]

    st.subheader("Dashboard")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Bills",
        len(bills)
    )

    c2.metric(
        "Pending",
        len(pending)
    )

    c3.metric(
        "Paid",
        len(paid)
    )

    due_soon = 0

    for bill in pending:

        reminder = get_reminder(bill)

        if reminder["level"] in ["warning", "urgent"]:
            due_soon += 1

    c4.metric(
        "Due Soon",
        due_soon
    )

    st.divider()

    st.subheader("Bills Needing Attention")

    if not bills:

        st.info(
            "No bills found yet. Go to My Bills and scan the demo inbox."
        )

    for bill in bills[:5]:

        reminder = get_reminder(bill)

        with st.container(border=True):

            col1, col2, col3 = st.columns([2, 2, 2])

            col1.markdown(
                f"### {bill['provider']}"
            )

            col1.write(
                bill["bill_type"]
            )

            col2.write(
                f"**Rs. {bill['amount']:,.0f}**"
            )

            col2.write(
                f"Due: {bill['due_date']}"
            )

            if bill["status"] == "Paid":

                col3.success("Paid")

            else:

                col3.warning(
                    reminder["message"]
                )


# =========================================================
# MY BILLS
# =========================================================

elif page == "My Bills":

    st.subheader("My Bills")

    st.write(
        "BillPay AI can discover bills from connected sources "
        "or extract information from a physical bill."
    )

    # --------------------------------
    # Demo inbox
    # --------------------------------

    if st.button(
        "🔎 Scan Connected Inbox",
        type="primary"
    ):

        added = scan_demo_inbox()

        st.success(
            f"Bill Finder Agent found {added} new bill(s)."
        )

    st.divider()

    # --------------------------------
    # OCR
    # --------------------------------

    st.subheader("Scan Physical Bill")

    uploaded = st.file_uploader(
        "Upload bill image",
        type=[
            "png",
            "jpg",
            "jpeg"
        ]
    )

    if uploaded:

        if st.button("Extract Bill Information"):

            text = extract_text_from_image(
                uploaded
            )

            if not text.strip():

                st.warning(
                    "No readable text found. "
                    "Try a clearer bill image."
                )

            else:

                st.text_area(
                    "Extracted Text",
                    text,
                    height=180
                )

                result = analyze_bill(
                    text
                )

                if result.get("valid"):

                    save_bill(result)

                    st.success(
                        "Bill successfully extracted and saved."
                    )

                else:

                    st.warning(
                        result.get(
                            "message",
                            "Could not verify the bill."
                        )
                    )

    st.divider()

    # --------------------------------
    # Existing bills
    # --------------------------------

    st.subheader("Saved Bills")

    bills = get_bills()

    if not bills:

        st.info(
            "No bills saved yet."
        )

    for bill in bills:

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [2, 2, 2, 1]
            )

            col1.markdown(
                f"**{bill['provider']}**"
            )

            col1.caption(
                bill["bill_type"]
            )

            col2.write(
                f"Rs. {bill['amount']:,.0f}"
            )

            col2.caption(
                f"Due: {bill['due_date']}"
            )

            col3.write(
                f"Ref: ••••{bill['reference_number'][-4:]}"
            )

            col3.caption(
                bill["status"]
            )

            if bill["status"] == "Paid":

                col4.success("Paid")

            else:

                col4.warning("Pending")


# =========================================================
# AI ASSISTANT
# =========================================================

elif page == "AI Assistant":

    st.subheader("AI Assistant")

    st.caption(
        "Ask BillPay AI about your bills."
    )

    question = st.chat_input(
        "Example: Which bills are due soon?"
    )

    if question:

        st.chat_message(
            "user"
        ).write(question)

        bills = get_bills()

        if not bills:

            st.chat_message(
                "assistant"
            ).write(
                "I don't have any bills yet. "
                "Please scan your connected inbox first."
            )

        else:

            q = question.lower()

            # -------------------------
            # Payment request
            # -------------------------

            if "pay" in q:

                found = None

                for bill in bills:

                    if bill["status"] == "Paid":
                        continue

                    if (
                        "electric" in q
                        and "electric" in bill["bill_type"].lower()
                    ):

                        found = bill
                        break

                    if (
                        "internet" in q
                        and "internet" in bill["bill_type"].lower()
                    ):

                        found = bill
                        break

                    if (
                        "gas" in q
                        and "gas" in bill["bill_type"].lower()
                    ):

                        found = bill
                        break

                if found:

                    st.chat_message(
                        "assistant"
                    ).write(
                        f"I found your {found['provider']} bill "
                        f"for Rs. {found['amount']:,.0f}, "
                        f"due on {found['due_date']}."
                    )

                    st.info(
                        "Go to Payments to explicitly confirm the payment."
                    )

                else:

                    st.chat_message(
                        "assistant"
                    ).write(
                        "I couldn't find a matching unpaid bill."
                    )

            # -------------------------
            # Bill information
            # -------------------------

            else:

                response = "Here are your current bills:\n\n"

                for bill in bills:

                    response += (
                        f"- {bill['provider']}: "
                        f"Rs. {bill['amount']:,.0f} — "
                        f"due {bill['due_date']} "
                        f"({bill['status']})\n"
                    )

                st.chat_message(
                    "assistant"
                ).write(response)


# =========================================================
# PAYMENTS
# =========================================================

elif page == "Payments":

    st.subheader("Payments")

    bills = [
        b for b in get_bills()
        if b["status"] != "Paid"
    ]

    if not bills:

        st.success(
            "No pending payments."
        )

    for bill in bills:

        with st.container(border=True):

            st.markdown(
                f"### {bill['provider']}"
            )

            st.write(
                f"Amount: **Rs. {bill['amount']:,.0f}**"
            )

            st.write(
                f"Due date: **{bill['due_date']}**"
            )

            st.caption(
                f"Reference: {bill['reference_number']}"
            )

            confirm = st.checkbox(
                f"I confirm payment of Rs. {bill['amount']:,.0f}",
                key=f"confirm_{bill['id']}"
            )

            if st.button(
                "Pay Now — Demo",
                key=f"pay_{bill['id']}",
                disabled=not confirm
            ):

                result = prepare_payment(
                    bill
                )

                if result["approved"]:

                    save_payment(
                        bill,
                        result["transaction_id"]
                    )

                    mark_bill_paid(
                        bill["id"]
                    )

                    st.success(
                        "Payment successful!"
                    )

                    st.code(
                        result["transaction_id"]
                    )

                    st.rerun()


# =========================================================
# HISTORY
# =========================================================

elif page == "History":

    st.subheader("Payment History")

    payments = get_payments()

    if not payments:

        st.info(
            "No payments yet."
        )

    for payment in payments:

        with st.container(border=True):

            col1, col2, col3 = st.columns(3)

            col1.write(
                f"**{payment['provider']}**"
            )

            col2.write(
                f"Rs. {payment['amount']:,.0f}"
            )

            col3.success(
                payment["status"]
            )

            st.caption(
                f"{payment['payment_date']} • "
                f"{payment['transaction_id']}"
            )
