import streamlit as st

from bill_finder_agent import find_bills
from bill_intelligence_agent import analyze_bill
from reminder_agent import get_reminder_status
from payment_agent import make_payment
from ocr_service import extract_text_from_image
from database import (
    init_db,
    save_bill,
    get_bills,
    mark_bill_paid,
    save_payment,
    get_payment_history,
)


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Finguard AI",
    page_icon="💳",
    layout="wide"
)

init_db()


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("Finguard AI")

st.caption(
    "AI-powered bill discovery, intelligence, reminders and payments"
)


# --------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------

st.sidebar.title("Finguard AI")

st.sidebar.caption(
    "Smart Bill Management Assistant"
)

page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "My Bills",
        "AI Assistant",
        "Upload Bill",
        "Payments",
        "History"
    ]
)


# ==================================================
# DASHBOARD
# ==================================================

if page == "Dashboard":

    st.header("Dashboard")

    bills = get_bills()

    total_bills = len(bills)

    unpaid_bills = sum(
        1
        for bill in bills
        if bill.get("status") != "paid"
    )

    paid_bills = sum(
        1
        for bill in bills
        if bill.get("status") == "paid"
    )

    # Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Bills",
            total_bills
        )

    with col2:
        st.metric(
            "Pending Bills",
            unpaid_bills
        )

    with col3:
        st.metric(
            "Paid Bills",
            paid_bills
        )

    st.divider()

    # ----------------------------------------------
    # Find New Bills
    # ----------------------------------------------

    st.subheader("Find New Bills")

    st.write(
        "Finguard AI scans connected sources to find "
        "and understand your bills automatically."
    )

    if st.button(
        "Scan Connected Sources",
        type="primary"
    ):

        with st.spinner(
            "Searching connected sources..."
        ):

            found_bills = find_bills()

        if not found_bills:

            st.info(
                "No new bills found."
            )

        else:

            found_count = len(found_bills)

            analyzed_count = 0
            failed_count = 0

            # Show number of discovered bills
            st.info(
                f"{found_count} bill(s) found"
            )

            progress = st.progress(0)

            for index, raw_bill in enumerate(
                found_bills
            ):

                try:

                    analyzed_bill = analyze_bill(
                        raw_bill
                    )

                    if analyzed_bill:

                        save_bill(
                            analyzed_bill
                        )

                        analyzed_count += 1

                    else:

                        failed_count += 1

                except Exception as e:

                    failed_count += 1

                    st.error(
                        f"Could not analyze bill: {e}"
                    )

                progress.progress(
                    (index + 1) / found_count
                )

            # --------------------------------------
            # Final Result
            # --------------------------------------

            if analyzed_count == found_count:

                st.success(
                    f"{found_count} bill(s) found"
                )

                st.success(
                    f"{analyzed_count} bill(s) analyzed successfully"
                )

            else:

                st.success(
                    f"{found_count} bill(s) found"
                )

                st.warning(
                    f"{analyzed_count} bill(s) analyzed successfully, "
                    f"{failed_count} bill(s) failed."
                )

    st.divider()

    # ----------------------------------------------
    # Recent Bills
    # ----------------------------------------------

    st.subheader("Recent Bills")

    bills = get_bills()

    if bills:

        for bill in bills[:5]:

            status = bill.get(
                "status",
                "pending"
            )

            st.write(
                f"**{bill.get('provider', 'Unknown Provider')}** — "
                f"Rs. {bill.get('amount', 0)} — "
                f"Due: {bill.get('due_date', 'N/A')} — "
                f"Status: {status}"
            )

    else:

        st.info(
            "No bills available yet. "
            "Scan your connected sources."
        )


# ==================================================
# MY BILLS
# ==================================================

elif page == "My Bills":

    st.header("My Bills")

    bills = get_bills()

    if not bills:

        st.info(
            "No bills found yet."
        )

    else:

        for bill in bills:

            st.subheader(
                bill.get(
                    "provider",
                    "Unknown Provider"
                )
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    f"**Amount:** "
                    f"Rs. {bill.get('amount', 0)}"
                )

            with col2:

                st.write(
                    f"**Due Date:** "
                    f"{bill.get('due_date', 'N/A')}"
                )

            with col3:

                st.write(
                    f"**Status:** "
                    f"{bill.get('status', 'pending')}"
                )

            if bill.get("account_number"):

                st.write(
                    f"**Account:** "
                    f"{bill.get('account_number')}"
                )

            if bill.get("bill_type"):

                st.write(
                    f"**Type:** "
                    f"{bill.get('bill_type')}"
                )

            st.divider()


# ==================================================
# AI ASSISTANT
# ==================================================

elif page == "AI Assistant":

    st.header("Finguard AI Assistant")

    st.write(
        "Ask Finguard AI about your bills, "
        "pending payments and due dates."
    )

    question = st.text_input(
        "Ask something about your bills",
        placeholder="Which bill is due soon?"
    )

    if st.button("Ask AI"):

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            bills = get_bills()

            question_lower = (
                question.lower()
            )

            if not bills:

                st.info(
                    "You don't have any bills yet."
                )

            elif "due" in question_lower:

                statuses = []

                for bill in bills:

                    status = get_reminder_status(
                        bill.get("due_date")
                    )

                    statuses.append(
                        (
                            bill.get(
                                "provider",
                                "Unknown"
                            ),
                            bill.get(
                                "amount",
                                0
                            ),
                            bill.get(
                                "due_date",
                                "N/A"
                            ),
                            status
                        )
                    )

                st.subheader(
                    "Bill Due Status"
                )

                for (
                    provider,
                    amount,
                    due_date,
                    status
                ) in statuses:

                    st.write(
                        f"**{provider}** — "
                        f"Rs. {amount} — "
                        f"Due: {due_date} — "
                        f"{status}"
                    )

            elif (
                "unpaid" in question_lower
                or "pending" in question_lower
            ):

                pending = [
                    bill
                    for bill in bills
                    if bill.get("status")
                    != "paid"
                ]

                if pending:

                    for bill in pending:

                        st.write(
                            f"**{bill.get('provider')}** — "
                            f"Rs. {bill.get('amount')} — "
                            f"Due: {bill.get('due_date')}"
                        )

                else:

                    st.success(
                        "You have no pending bills."
                    )

            else:

                st.write(
                    "I can currently help you check "
                    "pending bills and upcoming due dates."
                )


# ==================================================
# UPLOAD BILL
# ==================================================

elif page == "Upload Bill":

    st.header("Upload a Bill")

    st.write(
        "Upload a bill image and Finguard AI will "
        "extract the available information using OCR."
    )

    uploaded_file = st.file_uploader(
        "Choose bill image",
        type=[
            "png",
            "jpg",
            "jpeg"
        ]
    )

    if uploaded_file:

        st.image(
            uploaded_file,
            caption="Uploaded Bill",
            use_container_width=True
        )

        if st.button(
            "Extract Bill Information"
        ):

            with st.spinner(
                "Reading bill..."
            ):

                try:

                    image_text = (
                        extract_text_from_image(
                            uploaded_file
                        )
                    )

                    if image_text:

                        st.subheader(
                            "Extracted Text"
                        )

                        st.text_area(
                            "OCR Result",
                            image_text,
                            height=250
                        )

                    else:

                        st.warning(
                            "Could not extract readable text."
                        )

                except Exception as e:

                    st.error(
                        f"OCR failed: {e}"
                    )


# ==================================================
# PAYMENTS
# ==================================================

elif page == "Payments":

    st.header("Bill Payments")

    st.write(
        "Review your bill and explicitly authorize "
        "the payment before processing."
    )

    bills = get_bills()

    pending_bills = [
        bill
        for bill in bills
        if bill.get("status") != "paid"
    ]

    if not pending_bills:

        st.success(
            "No pending payments."
        )

    else:

        for bill in pending_bills:

            st.subheader(
                bill.get(
                    "provider",
                    "Unknown Provider"
                )
            )

            st.write(
                f"**Amount:** "
                f"Rs. {bill.get('amount', 0)}"
            )

            st.write(
                f"**Due Date:** "
                f"{bill.get('due_date', 'N/A')}"
            )

            confirm = st.checkbox(
                f"I authorize payment of "
                f"Rs. {bill.get('amount', 0)}",
                key=f"confirm_{bill.get('id')}"
            )

            if st.button(
                "Pay Bill",
                key=f"pay_{bill.get('id')}"
            ):

                if not confirm:

                    st.warning(
                        "Please confirm the payment first."
                    )

                else:

                    with st.spinner(
                        "Processing payment..."
                    ):

                        result = make_payment(
                            bill
                        )

                    if result.get(
                        "success"
                    ):

                        mark_bill_paid(
                            bill.get("id")
                        )

                        save_payment(
                            bill,
                            result.get(
                                "transaction_id"
                            )
                        )

                        st.success(
                            "Payment successful!"
                        )

                        st.write(
                            f"Transaction ID: "
                            f"{result.get('transaction_id')}"
                        )

                    else:

                        st.error(
                            result.get(
                                "message",
                                "Payment failed."
                            )
                        )


# ==================================================
# HISTORY
# ==================================================

elif page == "History":

    st.header("Payment History")

    history = get_payment_history()

    if not history:

        st.info(
            "No payment history available."
        )

    else:

        for payment in history:

            st.write(
                f"**{payment.get('provider', 'Unknown')}** — "
                f"Rs. {payment.get('amount', 0)} — "
                f"Transaction: "
                f"{payment.get('transaction_id', 'N/A')}"
            )

            st.divider()
