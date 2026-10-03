import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st
from groq import Groq

# Optional OCR
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Finguard AI",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CONFIG
# =========================================================

APP_NAME = "FINGUARD AI"
DB_FILE = "finguard.db"

DEFAULT_MODEL = "openai/gpt-oss-120b"

# Streamlit secrets first, environment variable second
try:
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
    GROQ_MODEL = st.secrets.get("GROQ_MODEL", DEFAULT_MODEL)
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

if not GROQ_API_KEY:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

client = None

if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception:
        client = None


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 20% 0%, rgba(99,102,241,0.08), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(16,185,129,0.06), transparent 25%),
        #080b12;
    color: #f8fafc;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: #0b0f17;
    border-right: 1px solid #1d2430;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

.sidebar-brand {
    padding: 4px 8px 20px 8px;
}

.sidebar-brand .brand {
    color: white;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

.sidebar-brand .brand span {
    color: #10b981;
}

.sidebar-brand .sub {
    color: #6b7280;
    font-size: 11px;
    margin-top: 5px;
}

.nav-title {
    color: #4b5563;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    margin: 22px 8px 8px 8px;
}

.ai-engine {
    margin: 20px 4px 8px 4px;
    padding: 14px;
    border-radius: 12px;
    border: 1px solid #202938;
    background: #0f141e;
}

.ai-engine-title {
    color: #6b7280;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.4px;
    margin-bottom: 8px;
}

.ai-engine-model {
    color: white;
    font-size: 13px;
    font-weight: 700;
}

.ai-engine-provider {
    color: #9ca3af;
    font-size: 11px;
    margin-top: 4px;
}

.status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10b981;
    margin-right: 5px;
}

.status-dot.offline {
    background: #ef4444;
}

/* Main */

.main-title {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -1.3px;
    color: white;
    margin-bottom: 2px;
}

.main-subtitle {
    color: #8b95a7;
    font-size: 14px;
    margin-bottom: 26px;
}

.hero-small {
    color: #10b981;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 7px;
}

/* Cards */

.metric-card {
    background: linear-gradient(145deg, #111722, #0c1119);
    border: 1px solid #202938;
    border-radius: 14px;
    padding: 18px;
    min-height: 115px;
}

.metric-label {
    color: #7d8798;
    font-size: 12px;
    font-weight: 600;
}

.metric-value {
    color: white;
    font-size: 27px;
    font-weight: 800;
    margin-top: 8px;
}

.metric-small {
    color: #64748b;
    font-size: 11px;
    margin-top: 4px;
}

/* Sections */

.section-card {
    background: #0d131c;
    border: 1px solid #202938;
    border-radius: 15px;
    padding: 20px;
    margin-top: 18px;
}

.section-title {
    color: white;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 5px;
}

.section-subtitle {
    color: #6b7280;
    font-size: 12px;
    margin-bottom: 16px;
}

/* Buttons */

.stButton > button {
    border-radius: 9px;
    border: 1px solid #273244;
    background: #121925;
    color: white;
    font-weight: 600;
    transition: 0.2s;
}

.stButton > button:hover {
    border-color: #10b981;
    color: #10b981;
}

/* Primary button */

button[kind="primary"] {
    background: #10b981 !important;
    border-color: #10b981 !important;
    color: #06130f !important;
}

/* Inputs */

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] {
    background: #0d131c !important;
    color: white !important;
    border-color: #273244 !important;
    border-radius: 9px !important;
}

/* File uploader */

[data-testid="stFileUploader"] {
    background: #0d131c;
    border: 1px dashed #334155;
    border-radius: 12px;
    padding: 10px;
}

/* Alerts */

div[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Tables */

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Hide Streamlit menu/footer */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_type TEXT,
            provider TEXT,
            consumer_number TEXT,
            amount REAL,
            due_date TEXT,
            status TEXT DEFAULT 'Pending',
            extracted_text TEXT,
            created_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER,
            amount REAL,
            payment_method TEXT,
            status TEXT,
            paid_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


# =========================================================
# DATABASE HELPERS
# =========================================================

def get_bills():
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            id,
            bill_type,
            provider,
            consumer_number,
            amount,
            due_date,
            status,
            created_at
        FROM bills
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return rows


def get_payments():
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            payments.id,
            bills.provider,
            payments.amount,
            payments.payment_method,
            payments.status,
            payments.paid_at
        FROM payments
        LEFT JOIN bills
        ON payments.bill_id = bills.id
        ORDER BY payments.id DESC
        """
    ).fetchall()

    conn.close()

    return rows


def add_bill(
    bill_type,
    provider,
    consumer_number,
    amount,
    due_date,
    extracted_text,
):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO bills
        (
            bill_type,
            provider,
            consumer_number,
            amount,
            due_date,
            status,
            extracted_text,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bill_type,
            provider,
            consumer_number,
            amount,
            due_date,
            "Pending",
            extracted_text,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    bill_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return bill_id


def add_payment(bill_id, amount, method):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO payments
        (
            bill_id,
            amount,
            payment_method,
            status,
            paid_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            bill_id,
            amount,
            method,
            "Successful",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.execute(
        """
        UPDATE bills
        SET status = 'Paid'
        WHERE id = ?
        """,
        (bill_id,),
    )

    conn.commit()
    conn.close()


# =========================================================
# OCR
# =========================================================

def extract_text_from_image(uploaded_file):
    if not OCR_AVAILABLE:
        return ""

    try:
        image = Image.open(uploaded_file)

        text = pytesseract.image_to_string(image)

        return text.strip()

    except Exception:
        return ""


# =========================================================
# BILL INFORMATION EXTRACTION
# =========================================================

def extract_amount(text):
    if not text:
        return 0.0

    patterns = [
        r"(?:total|amount|payable|bill amount|net payable)[^\d]{0,20}([\d,]+(?:\.\d{1,2})?)",
        r"Rs\.?\s*([\d,]+(?:\.\d{1,2})?)",
        r"PKR\s*([\d,]+(?:\.\d{1,2})?)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        if matches:
            try:
                value = matches[-1].replace(",", "")
                return float(value)
            except Exception:
                pass

    return 0.0


def extract_consumer_number(text):
    if not text:
        return ""

    patterns = [
        r"(?:consumer|customer|reference|account)\s*(?:no|number|#)?\s*[:\-]?\s*([A-Za-z0-9\-]{6,30})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            return match.group(1)

    return ""


def detect_provider(text):
    text_lower = text.lower()

    providers = {
        "KE": ["k-electric", "k electric", "k-electricity"],
        "LESCO": ["lesco"],
        "FESCO": ["fesco"],
        "IESCO": ["iesco"],
        "MEPCO": ["mepco"],
        "PESCO": ["pesco"],
        "SNGPL": ["sngpl"],
        "SSGC": ["ssgc"],
        "PTCL": ["ptcl"],
    }

    for provider, keywords in providers.items():
        for keyword in keywords:
            if keyword in text_lower:
                return provider

    return "Unknown"


# =========================================================
# GROQ AI
# =========================================================

def ask_groq(prompt):
    if client is None:
        return (
            "AI service is not connected. "
            "Please add GROQ_API_KEY to Streamlit Secrets."
        )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Finguard AI, an AI financial assistant "
                        "for bill management and payment assistance. "
                        "Give concise, practical and clear answers. "
                        "Do not claim to have completed a real payment "
                        "unless the application actually confirms it."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=700,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI request failed: {str(e)}"


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand">FIN<span>GUARD</span> AI</div>
            <div class="sub">Intelligent Bill Management</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Scan Bill",
            "My Bills",
            "Payments",
            "AI Assistant",
        ],
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="nav-title">AI ENGINE</div>',
        unsafe_allow_html=True,
    )

    if client:
        status_html = (
            '<span class="status-dot"></span>'
            '<span style="color:#10b981;font-size:10px;">ONLINE</span>'
        )
    else:
        status_html = (
            '<span class="status-dot offline"></span>'
            '<span style="color:#ef4444;font-size:10px;">OFFLINE</span>'
        )

    st.markdown(
        f"""
        <div class="ai-engine">

            <div class="ai-engine-title">
                AI ENGINE
            </div>

            <div class="ai-engine-model">
                GPT-OSS 120B
            </div>

            <div class="ai-engine-provider">
                Powered by Groq
            </div>

            <div style="margin-top:10px;">
                {status_html}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.markdown(
        '<div class="hero-small">FINANCIAL CONTROL CENTER</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">Welcome to Finguard AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        'Manage, analyze and track your bills with AI-powered assistance.'
        '</div>',
        unsafe_allow_html=True,
    )

    bills = get_bills()
    payments = get_payments()

    total_bills = len(bills)
    paid_bills = len([b for b in bills if b[6] == "Paid"])
    pending_bills = len([b for b in bills if b[6] != "Paid"])

    total_amount = sum(float(b[4] or 0) for b in bills)
    paid_amount = sum(float(p[2] or 0) for p in payments)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">TOTAL BILLS</div>
                <div class="metric-value">{total_bills}</div>
                <div class="metric-small">Tracked bills</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">PENDING</div>
                <div class="metric-value">{pending_bills}</div>
                <div class="metric-small">Require attention</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">TOTAL VALUE</div>
                <div class="metric-value">PKR {total_amount:,.0f}</div>
                <div class="metric-small">Bills tracked</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">PAID</div>
                <div class="metric-value">PKR {paid_amount:,.0f}</div>
                <div class="metric-small">{paid_bills} completed payments</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Recent Bills</div>
            <div class="section-subtitle">
                Your latest bill activity
            </div>
        """,
        unsafe_allow_html=True,
    )

    if bills:

        for bill in bills[:5]:

            bill_id, bill_type, provider, consumer, amount, due_date, status, created = bill

            status_text = status

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:12px 0;
                    border-bottom:1px solid #1c2532;
                ">
                    <div>
                        <div style="color:white;font-weight:600;">
                            {provider or bill_type or "Bill"}
                        </div>
                        <div style="color:#667085;font-size:11px;margin-top:4px;">
                            {consumer or "No consumer number"}
                        </div>
                    </div>

                    <div style="text-align:right;">
                        <div style="color:white;font-weight:700;">
                            PKR {float(amount or 0):,.0f}
                        </div>
                        <div style="color:#8b95a7;font-size:11px;">
                            {status_text}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info("No bills have been added yet. Go to Scan Bill to get started.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# SCAN BILL
# =========================================================

elif page == "Scan Bill":

    st.markdown(
        '<div class="hero-small">SMART BILL SCANNER</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">Scan a Bill</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        'Upload a bill image and let Finguard AI extract useful information.'
        '</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload bill image",
        type=["png", "jpg", "jpeg"],
    )

    if uploaded_file:

        st.image(
            uploaded_file,
            caption="Uploaded bill",
            use_container_width=True,
        )

        if st.button("Scan & Extract Bill", type="primary"):

            with st.spinner("Analyzing bill..."):

                extracted_text = extract_text_from_image(uploaded_file)

                if extracted_text:

                    provider = detect_provider(extracted_text)
                    amount = extract_amount(extracted_text)
                    consumer_number = extract_consumer_number(extracted_text)

                    st.session_state["scan_text"] = extracted_text
                    st.session_state["scan_provider"] = provider
                    st.session_state["scan_amount"] = amount
                    st.session_state["scan_consumer"] = consumer_number

                    st.success("Bill information extracted.")

                else:

                    st.warning(
                        "OCR could not extract readable text from this image. "
                        "You can enter the bill information manually below."
                    )

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Bill Information</div>
            <div class="section-subtitle">
                Review the extracted information before saving.
            </div>
        """,
        unsafe_allow_html=True,
    )

    provider = st.text_input(
        "Provider",
        value=st.session_state.get("scan_provider", ""),
        placeholder="e.g. KE, LESCO, SSGC",
    )

    bill_type = st.selectbox(
        "Bill Type",
        [
            "Electricity",
            "Gas",
            "Internet",
            "Mobile",
            "Water",
            "Other",
        ],
    )

    consumer_number = st.text_input(
        "Consumer / Account Number",
        value=st.session_state.get("scan_consumer", ""),
    )

    amount = st.number_input(
        "Amount",
        min_value=0.0,
        value=float(st.session_state.get("scan_amount", 0.0)),
        step=100.0,
    )

    due_date = st.text_input(
        "Due Date",
        placeholder="e.g. 15 October 2026",
    )

    if st.button("Save Bill", type="primary"):

        extracted_text = st.session_state.get("scan_text", "")

        bill_id = add_bill(
            bill_type=bill_type,
            provider=provider,
            consumer_number=consumer_number,
            amount=amount,
            due_date=due_date,
            extracted_text=extracted_text,
        )

        st.success(f"Bill #{bill_id} saved successfully.")

        st.session_state["scan_text"] = ""
        st.session_state["scan_provider"] = ""
        st.session_state["scan_amount"] = 0.0
        st.session_state["scan_consumer"] = ""

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# MY BILLS
# =========================================================

elif page == "My Bills":

    st.markdown(
        '<div class="hero-small">BILL MANAGEMENT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">My Bills</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        'View and manage your saved bills.'
        '</div>',
        unsafe_allow_html=True,
    )

    bills = get_bills()

    if not bills:

        st.info("No bills found.")

    else:

        for bill in bills:

            (
                bill_id,
                bill_type,
                provider,
                consumer,
                amount,
                due_date,
                status,
                created,
            ) = bill

            with st.expander(
                f"{provider or bill_type}  •  PKR {float(amount or 0):,.0f}"
            ):

                c1, c2 = st.columns(2)

                with c1:

                    st.write(f"**Bill Type:** {bill_type}")
                    st.write(f"**Provider:** {provider}")
                    st.write(f"**Consumer Number:** {consumer}")

                with c2:

                    st.write(f"**Amount:** PKR {float(amount or 0):,.2f}")
                    st.write(f"**Due Date:** {due_date or 'Not provided'}")
                    st.write(f"**Status:** {status}")

                if status != "Paid":

                    if st.button(
                        f"Pay PKR {float(amount or 0):,.0f}",
                        key=f"pay_{bill_id}",
                    ):

                        st.session_state["selected_bill"] = bill_id
                        st.session_state["selected_amount"] = float(
                            amount or 0
                        )

                        st.rerun()


# =========================================================
# PAYMENTS
# =========================================================

elif page == "Payments":

    st.markdown(
        '<div class="hero-small">PAYMENT CENTER</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">Payments</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        'Review payment activity and complete bill payments.'
        '</div>',
        unsafe_allow_html=True,
    )

    if "selected_bill" in st.session_state:

        bill_id = st.session_state["selected_bill"]
        amount = st.session_state["selected_amount"]

        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Complete Payment</div>
                <div class="section-subtitle">
                    Confirm the payment details below.
                </div>
            """,
            unsafe_allow_html=True,
        )

        st.metric(
            "Payment Amount",
            f"PKR {amount:,.2f}",
        )

        payment_method = st.selectbox(
            "Payment Method",
            [
                "JazzCash",
                "EasyPaisa",
                "Bank Transfer",
                "Debit / Credit Card",
            ],
        )

        if st.button("Confirm Payment", type="primary"):

            add_payment(
                bill_id=bill_id,
                amount=amount,
                method=payment_method,
            )

            del st.session_state["selected_bill"]
            del st.session_state["selected_amount"]

            st.success(
                "Payment recorded successfully in Finguard AI."
            )

            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Payment History</div>
            <div class="section-subtitle">
                Your previous payment records
            </div>
        """,
        unsafe_allow_html=True,
    )

    payments = get_payments()

    if payments:

        for payment in payments:

            (
                payment_id,
                provider,
                amount,
                method,
                status,
                paid_at,
            ) = payment

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    padding:13px 0;
                    border-bottom:1px solid #1c2532;
                ">
                    <div>
                        <div style="color:white;font-weight:600;">
                            {provider or "Bill Payment"}
                        </div>
                        <div style="color:#687386;font-size:11px;margin-top:4px;">
                            {method} • {paid_at}
                        </div>
                    </div>

                    <div style="text-align:right;">
                        <div style="color:white;font-weight:700;">
                            PKR {float(amount or 0):,.0f}
                        </div>
                        <div style="color:#10b981;font-size:11px;">
                            {status}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info("No payments recorded yet.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# AI ASSISTANT
# =========================================================

elif page == "AI Assistant":

    st.markdown(
        '<div class="hero-small">FINGUARD INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">AI Assistant</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        'Ask Finguard AI about your bills, payments and financial organization.'
        '</div>',
        unsafe_allow_html=True,
    )

    bills = get_bills()

    bill_context = ""

    if bills:

        bill_context = "\n".join(
            [
                (
                    f"- {b[1]} | Provider: {b[2]} | "
                    f"Amount: PKR {float(b[4] or 0):,.2f} | "
                    f"Due: {b[5]} | Status: {b[6]}"
                )
                for b in bills
            ]
        )

    else:

        bill_context = "No bills are currently saved."

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, message in st.session_state.chat_history:

        with st.chat_message(role):
            st.markdown(message)

    prompt = st.chat_input(
        "Ask Finguard AI about your bills..."
    )

    if prompt:

        st.session_state.chat_history.append(
            ("user", prompt)
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        system_context = f"""
User's current bill information:

{bill_context}

User question:
{prompt}

Provide a concise and useful response based on the available bill
information. If the required information is unavailable, clearly say so.
Do not claim that a payment was made unless the database shows it.
"""

        with st.chat_message("assistant"):

            with st.spinner("Finguard AI is thinking..."):

                answer = ask_groq(system_context)

                st.markdown(answer)

        st.session_state.chat_history.append(
            ("assistant", answer)
        )
