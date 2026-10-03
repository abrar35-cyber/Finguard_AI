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


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Finguard AI",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #f6f8fc;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        color: #172033 !important;
        font-weight: 700 !important;
    }

    p, span, label {
        color: #596579;
    }


    /* ---------- SIDEBAR ---------- */

    section[data-testid="stSidebar"] {
        background: #111827;
        border-right: none;
    }

    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }

    section[data-testid="stSidebar"] .stRadio label {
        padding: 10px 12px;
        border-radius: 10px;
        margin-bottom: 4px;
    }

    section[data-testid="stSidebar"] .stRadio label:hover {
        background: #1f2937;
    }

    .sidebar-logo {
        font-size: 25px;
        font-weight: 800;
        color: white !important;
        margin-bottom: 2px;
    }

    .sidebar-subtitle {
        font-size: 12px;
        color: #9ca3af !important;
        margin-bottom: 30px;
    }


    /* ---------- TOP BAR ---------- */

    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }

    .welcome-text {
        font-size: 14px;
        color: #7b8494;
        margin-bottom: 3px;
    }

    .page-title {
        font-size: 30px;
        font-weight: 800;
        color: #172033;
    }


    /* ---------- CARDS ---------- */

    .metric-card {
        background: white;
        border: 1px solid #e7ebf2;
        border-radius: 18px;
        padding: 22px;
        min-height: 130px;
        box-shadow: 0 4px 16px rgba(17, 24, 39, 0.04);
    }

    .metric-label {
        font-size: 13px;
        color: #7b8494;
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 29px;
        font-weight: 800;
        color: #172033;
    }

    .metric-small {
        font-size: 12px;
        color: #7b8494;
        margin-top: 7px;
    }


    /* ---------- BILL CARD ---------- */

    .bill-card {
        background: white;
        border: 1px solid #e7ebf2;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(17, 24, 39, 0.035);
    }

    .bill-provider {
        font-size: 17px;
        font-weight: 750;
        color: #172033;
    }

    .bill-type {
        font-size: 12px;
        color: #8a94a6;
        margin-top: 3px;
    }

    .bill-amount {
        font-size: 22px;
        font-weight: 800;
        color: #172033;
    }

    .bill-meta {
        font-size: 13px;
        color: #697386;
        margin-top: 5px;
    }


    /* ---------- STATUS ---------- */

    .status-paid {
        display: inline-block;
        background: #e9f9f0;
        color: #16834b;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    .status-pending {
        display: inline-block;
        background: #fff5dc;
        color: #a66a00;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }


    /* ---------- HERO ---------- */

    .hero {
        background: linear-gradient(
            135deg,
            #111827 0%,
            #1e293b 55%,
            #263b67 100%
        );
        border-radius: 24px;
        padding: 30px;
        margin-bottom: 25px;
        color: white;
        box-shadow: 0 12px 35px rgba(17, 24, 39, 0.15);
    }

    .hero-small {
        color: #aeb9ca;
        font-size: 13px;
        margin-bottom: 10px;
    }

    .hero-title {
        color: white !important;
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .hero-description {
        color: #c8d1df !important;
        font-size: 14px;
        max-width: 650px;
        line-height: 1.6;
    }


    /* ---------- SECTION ---------- */

    .section-title {
        font-size: 19px;
        font-weight: 750;
        color: #172033;
        margin-top: 25px;
        margin-bottom: 14px;
    }


    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 10px;
        border: none;
        font-weight: 650;
        min-height: 42px;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(17, 24, 39, 0.10);
    }


    /* ---------- INPUTS ---------- */

    .stTextInput input,
    .stTextArea textarea,
    .stFileUploader {
        border-radius: 12px !important;
    }


    /* ---------- DIVIDER ---------- */

    hr {
        border-color: #e8ebf1 !important;
    }


    /* ---------- INFO BOX ---------- */

    .info-card {
        background: #eef4ff;
        border: 1px solid #d9e6ff;
        border-radius: 15px;
        padding: 17px;
        color: #34517f;
        font-size: 13px;
        line-height: 1.6;
        margin-bottom: 20px;
    }


    /* ---------- PAYMENT CARD ---------- */

    .payment-card {
        background: white;
        border: 1px solid #e7ebf2;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 18px;
        box-shadow: 0 5px 18px rgba(17, 24, 39, 0.05);
    }


    /* ---------- HIDE STREAMLIT DEFAULT ---------- */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-logo">Finguard AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-subtitle">'
        'Smart Bill Management'
        '</div>',
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "My Bills",
            "AI Assistant",
            "Upload Bill",
            "Payments",
            "History"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown(
        """
        <div style="
            background:#1f2937;
            border-radius:14px;
            padding:15px;
            margin-top:20px;
        ">
            <div style="
                color:#9ca3af;
                font-size:11px;
                margin-bottom:5px;
            ">
                AI ENGINE
            </div>

            <div style="
                color:white;
                font-weight:700;
                font-size:13px;
            ">
                GPT-OSS 120B
            </div>

            <div style="
                color:#9ca3af;
                font-size:11px;
                margin-top:4px;
            ">
                Powered by Groq
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.markdown(
        """
        <div class="topbar">
            <div>
                <div class="welcome-text">
                    Welcome back
                </div>
                <div class="page-title">
                    Your financial overview
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

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

    total_pending_amount = sum(
        float(bill.get("amount") or 0)
        for bill in bills
        if bill.get("status") != "paid"
    )

    # ---------------------------------------------
    # HERO
    # ---------------------------------------------

    st.markdown(
        """
        <div class="hero">

            <div class="hero-small">
                FINGUARD AI
            </div>

            <div class="hero-title">
                Your bills, managed intelligently.
            </div>

            <div class="hero-description">
                Automatically discover bills, understand their
                amounts and due dates, receive reminders and
                authorize payments from one place.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------
    # METRICS
    # ---------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    TOTAL BILLS
                </div>
                <div class="metric-value">
                    {total_bills}
                </div>
                <div class="metric-small">
                    Bills discovered
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    PENDING
                </div>
                <div class="metric-value">
                    {unpaid_bills}
                </div>
                <div class="metric-small">
                    Awaiting payment
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    PAID
                </div>
                <div class="metric-value">
                    {paid_bills}
                </div>
                <div class="metric-small">
                    Successfully completed
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    PENDING AMOUNT
                </div>
                <div class="metric-value">
                    Rs. {total_pending_amount:,.0f}
                </div>
                <div class="metric-small">
                    Total outstanding
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------------------------------------------
    # SCAN
    # ---------------------------------------------

    st.markdown(
        '<div class="section-title">Bill Discovery</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="info-card">
            Finguard AI can scan connected sources, identify
            bills and use AI to extract important information
            such as provider, amount, account number and due date.
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "Scan Connected Sources",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Scanning connected sources..."
        ):

            found_bills = find_bills()

        if not found_bills:

            st.info(
                "No new bills were found."
            )

        else:

            found_count = len(found_bills)

            analyzed_count = 0
            failed_count = 0

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
                    f"{analyzed_count} analyzed successfully, "
                    f"{failed_count} failed."
                )

    # ---------------------------------------------
    # RECENT BILLS
    # ---------------------------------------------

    st.markdown(
        '<div class="section-title">Recent Bills</div>',
        unsafe_allow_html=True
    )

    bills = get_bills()

    if not bills:

        st.info(
            "No bills yet. Scan your connected sources to get started."
        )

    else:

        for bill in bills[:5]:

            provider = bill.get(
                "provider",
                "Unknown Provider"
            )

            amount = bill.get(
                "amount",
                0
            )

            due_date = bill.get(
                "due_date",
                "N/A"
            )

            status = bill.get(
                "status",
                "pending"
            )

            if status == "paid":

                status_html = (
                    '<span class="status-paid">'
                    'PAID'
                    '</span>'
                )

            else:

                status_html = (
                    '<span class="status-pending">'
                    'PENDING'
                    '</span>'
                )

            st.markdown(
                f"""
                <div class="bill-card">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                    ">

                        <div>

                            <div class="bill-provider">
                                {provider}
                            </div>

                            <div class="bill-type">
                                {bill.get('bill_type', 'Utility Bill')}
                            </div>

                        </div>

                        <div style="text-align:right">

                            <div class="bill-amount">
                                Rs. {amount}
                            </div>

                            <div style="margin-top:5px">
                                {status_html}
                            </div>

                        </div>

                    </div>

                    <div class="bill-meta">
                        Due date: {due_date}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# MY BILLS
# =========================================================

elif page == "My Bills":

    st.markdown(
        """
        <div class="welcome-text">
            FINGUARD AI
        </div>

        <div class="page-title">
            My Bills
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "All bills discovered and analyzed by Finguard AI."
    )

    bills = get_bills()

    if not bills:

        st.info(
            "No bills found yet."
        )

    else:

        for bill in bills:

            provider = bill.get(
                "provider",
                "Unknown Provider"
            )

            amount = bill.get(
                "amount",
                0
            )

            status = bill.get(
                "status",
                "pending"
            )

            if status == "paid":

                badge = (
                    '<span class="status-paid">'
                    'PAID'
                    '</span>'
                )

            else:

                badge = (
                    '<span class="status-pending">'
                    'PENDING'
                    '</span>'
                )

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.markdown(
                    f"""
                    <div class="bill-card">

                        <div class="bill-provider">
                            {provider}
                        </div>

                        <div class="bill-type">
                            {bill.get(
                                'bill_type',
                                'Utility Bill'
                            )}
                        </div>

                        <div class="bill-meta">
                            Account:
                            {bill.get(
                                'account_number',
                                'N/A'
                            )}
                        </div>

                        <div class="bill-meta">
                            Due:
                            {bill.get(
                                'due_date',
                                'N/A'
                            )}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:

                st.markdown(
                    f"""
                    <div style="
                        background:white;
                        border:1px solid #e7ebf2;
                        border-radius:18px;
                        padding:20px;
                        text-align:center;
                        min-height:120px;
                    ">

                        <div class="metric-label">
                            AMOUNT
                        </div>

                        <div class="bill-amount">
                            Rs. {amount}
                        </div>

                        <div style="
                            margin-top:10px;
                        ">
                            {badge}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


# =========================================================
# AI ASSISTANT
# =========================================================

elif page == "AI Assistant":

    st.markdown(
        """
        <div class="welcome-text">
            FINGUARD AI
        </div>

        <div class="page-title">
            AI Assistant
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "Ask questions about your bills and upcoming payments."
    )

    bills = get_bills()

    question = st.text_input(
        "Ask Finguard AI",
        placeholder="Which bill is due soon?"
    )

    if st.button(
        "Ask AI",
        type="primary"
    ):

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        elif not bills:

            st.info(
                "You don't have any bills yet."
            )

        else:

            question_lower = question.lower()

            if "due" in question_lower:

                st.subheader(
                    "Upcoming Bill Status"
                )

                for bill in bills:

                    status = get_reminder_status(
                        bill.get("due_date")
                    )

                    st.markdown(
                        f"""
                        <div class="bill-card">

                            <div class="bill-provider">
                                {bill.get(
                                    'provider',
                                    'Unknown'
                                )}
                            </div>

                            <div class="bill-meta">
                                Rs. {bill.get(
                                    'amount',
                                    0
                                )}
                                &nbsp; • &nbsp;
                                Due:
                                {bill.get(
                                    'due_date',
                                    'N/A'
                                )}
                            </div>

                            <div style="
                                margin-top:10px;
                                font-weight:600;
                                color:#4f46e5;
                            ">
                                {status}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
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

                        st.markdown(
                            f"""
                            <div class="bill-card">

                                <div class="bill-provider">
                                    {bill.get(
                                        'provider',
                                        'Unknown'
                                    )}
                                </div>

                                <div class="bill-amount">
                                    Rs. {bill.get(
                                        'amount',
                                        0
                                    )}
                                </div>

                                <div class="bill-meta">
                                    Due:
                                    {bill.get(
                                        'due_date',
                                        'N/A'
                                    )}
                                </div>

                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                else:

                    st.success(
                        "You have no pending bills."
                    )

            else:

                st.info(
                    "Try asking: "
                    "\"Which bill is due soon?\" "
                    "or "
                    "\"Show my pending bills.\""
                )


# =========================================================
# UPLOAD BILL
# =========================================================

elif page == "Upload Bill":

    st.markdown(
        """
        <div class="welcome-text">
            FINGUARD AI
        </div>

        <div class="page-title">
            Upload a Bill
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "Have a physical bill? Upload an image and "
        "Finguard AI can extract its text."
    )

    uploaded_file = st.file_uploader(
        "Upload bill image",
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
            "Extract Bill Information",
            type="primary"
        ):

            with st.spinner(
                "Reading your bill..."
            ):

                try:

                    image_text = (
                        extract_text_from_image(
                            uploaded_file
                        )
                    )

                    if image_text:

                        st.success(
                            "Bill text extracted successfully."
                        )

                        st.subheader(
                            "Extracted Information"
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


# =========================================================
# PAYMENTS
# =========================================================

elif page == "Payments":

    st.markdown(
        """
        <div class="welcome-text">
            FINGUARD AI
        </div>

        <div class="page-title">
            Payments
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        "Review and authorize your pending bills."
    )

    bills = get_bills()

    pending_bills = [
        bill
        for bill in bills
        if bill.get("status")
        != "paid"
    ]

    if not pending_bills:

        st.success(
            "You're all caught up. No pending payments."
        )

    else:

        for bill in pending_bills:

            provider = bill.get(
                "provider",
                "Unknown Provider"
            )

            amount = bill.get(
                "amount",
                0
            )

            due_date = bill.get(
                "due_date",
                "N/A"
            )

            st.markdown(
                f"""
                <div class="payment-card">

                    <div class="bill-type">
                        PAYMENT REQUEST
                    </div>

                    <div class="bill-provider"
                         style="font-size:21px;
                                margin-top:5px;">
                        {provider}
                    </div>

                    <div style="
                        font-size:30px;
                        font-weight:800;
                        color:#172033;
                        margin-top:12px;
                    ">
                        Rs. {amount}
                    </div>

                    <div class="bill-meta">
                        Due date: {due_date}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            confirm = st.checkbox(
                f"I authorize Finguard AI to process "
                f"the payment of Rs. {amount}.",
                key=f"confirm_{bill.get('id')}"
            )

            if st.button(
                "Authorize & Pay",
                key=f"pay_{bill.get('id')}",
                type="primary",
                use_container_width=True
            ):

                if not confirm:

                    st.warning(
                        "Please confirm the payment authorization first."
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
                            "Payment successful."
                        )

                        st.info(
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

            st.divider()


# =========================================================
# HISTORY
# =========================================================

elif page == "History":

    st.markdown(
        """
        <div class="welcome-text">
            FINGUARD AI
        </div>

        <div class="page-title">
            Payment History
        </div>
        """,
        unsafe_allow_html=True
    )

    history = get_payment_history()

    if not history:

        st.info(
            "No payment history available yet."
        )

    else:

        for payment in history:

            st.markdown(
                f"""
                <div class="bill-card">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                    ">

                        <div>

                            <div class="bill-provider">
                                {payment.get(
                                    'provider',
                                    'Unknown'
                                )}
                            </div>

                            <div class="bill-meta">
                                Payment completed
                            </div>

                        </div>

                        <div style="
                            text-align:right;
                        ">

                            <div class="bill-amount">
                                Rs. {payment.get(
                                    'amount',
                                    0
                                )}
                            </div>

                            <div style="
                                color:#16834b;
                                font-size:12px;
                                font-weight:700;
                                margin-top:5px;
                            ">
                                COMPLETED
                            </div>

                        </div>

                    </div>

                    <div class="bill-meta"
                         style="margin-top:15px;">

                        Transaction ID:
                        {payment.get(
                            'transaction_id',
                            'N/A'
                        )}

                    </div>

                    <div class="bill-meta">

                        {payment.get(
                            'payment_date',
                            ''
                        )}

                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )
