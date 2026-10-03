import os
import streamlit as st

# =========================================================
# IMPORT INTERNAL MODULES & AGENTS
# =========================================================
try:
    from database import init_db, get_bills, get_payments, add_bill, add_payment
except ImportError:
    st.error("Missing database.py module.")

try:
    from groq_service import ask_groq
except ImportError:
    def ask_groq(prompt):
        return "groq_service.py not found or configured."

try:
    from ocr_service import (
        extract_text_from_image,
        extract_amount,
        detect_provider,
        extract_consumer_number,
    )
except ImportError:
    extract_text_from_image = None

# Optional Agent Imports
try:
    from bill_finder_agent import find_bills_from_inbox
except ImportError:
    find_bills_from_inbox = None

try:
    from reminder_agent import get_reminder_status
except ImportError:
    get_reminder_status = None


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Finguard AI",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize Database
try:
    init_db()
except Exception:
    pass


# =========================================================
# CSS STYLING
# =========================================================
st.markdown(
"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(16,185,129,0.08), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(99,102,241,0.07), transparent 28%),
        #080b12;
    color: #f8fafc;
}

section[data-testid="stSidebar"] {
    display: none;
}

header[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    max-width: 1250px;
    padding-top: 40px;
    padding-bottom: 60px;
}

.hero-small {
    color: #10b981;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 6px;
}

.main-title {
    color: white;
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -1.5px;
    margin-bottom: 4px;
}

.main-subtitle {
    color: #8b95a7;
    font-size: 14px;
    margin-bottom: 25px;
}

.ai-engine-card {
    background: linear-gradient(145deg, rgba(17,24,39,0.98), rgba(10,15,23,0.98));
    border: 1px solid #243044;
    border-radius: 16px;
    padding: 18px 22px;
    margin-bottom: 25px;
}

.ai-engine-label {
    color: #64748b;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.4px;
}

.ai-engine-model {
    color: white;
    font-size: 17px;
    font-weight: 700;
    margin-top: 4px;
}

.ai-engine-provider {
    color: #9ca3af;
    font-size: 11px;
    margin-top: 2px;
}

.ai-online {
    color: #10b981;
    font-size: 11px;
    font-weight: 700;
}

.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    margin-right: 6px;
}

.metric-card {
    background: linear-gradient(145deg, #111722, #0c1119);
    border: 1px solid #202938;
    border-radius: 14px;
    padding: 18px;
    min-height: 115px;
}

.metric-label {
    color: #7d8798;
    font-size: 11px;
    font-weight: 600;
}

.metric-value {
    color: white;
    font-size: 24px;
    font-weight: 800;
    margin-top: 8px;
}

.metric-small {
    color: #64748b;
    font-size: 11px;
    margin-top: 4px;
}

.section-title {
    color: white;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 3px;
}

.section-subtitle {
    color: #6b7280;
    font-size: 12px;
    margin-bottom: 16px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #0d131c;
    border: 1px solid #202938 !important;
    border-radius: 14px;
    padding: 18px;
    margin-top: 15px;
    margin-bottom: 15px;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] {
    background: #0d131c !important;
    color: white !important;
    border-color: #273244 !important;
    border-radius: 9px !important;
}

[data-testid="stFileUploader"] {
    background: #0d131c;
    border: 1px dashed #334155;
    border-radius: 12px;
    padding: 10px;
}

.stButton > button {
    border-radius: 9px;
    border: 1px solid #273244;
    background: #121925;
    color: white;
    font-weight: 600;
}

.stButton > button:hover {
    border-color: #10b981;
    color: #10b981;
}

button[kind="primary"] {
    background: #10b981 !important;
    border-color: #10b981 !important;
    color: #06130f !important;
}

[data-testid="stChatMessage"] {
    background: #0d131c;
    border: 1px solid #202938;
    border-radius: 12px;
}

[data-testid="stExpander"] {
    background: #0d131c;
    border: 1px solid #202938;
    border-radius: 10px;
}
</style>""",
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="hero-small">FINANCIAL CONTROL CENTER</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">FINGUARD AI</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Intelligent multi-agent bill management, scanning & payment tracking.</div>', unsafe_allow_html=True)


# =========================================================
# AI STATUS BAR
# =========================================================
st.markdown(
"""<div class="ai-engine-card">
<div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
        <div class="ai-engine-label">AI MULTI-AGENT ENGINE</div>
        <div class="ai-engine-model">LLaMA 3.3 / Groq Cloud</div>
        <div class="ai-engine-provider">Autonomous Financial Agents Connected</div>
    </div>
    <div>
        <span class="status-dot"></span>
        <span class="ai-online">ONLINE</span>
    </div>
</div>
</div>""",
    unsafe_allow_html=True,
)


# =========================================================
# STATS METRICS
# =========================================================
bills = get_bills() if "get_bills" in globals() else []
payments = get_payments() if "get_payments" in globals() else []

total_bills = len(bills)
paid_bills = len([b for b in bills if b[6] == "Paid"])
pending_bills = len([b for b in bills if b[6] != "Paid"])
total_amount = sum(float(b[4] or 0) for b in bills)
paid_amount = sum(float(p[2] or 0) for p in payments)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL BILLS</div><div class="metric-value">{total_bills}</div><div class="metric-small">Tracked bills</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">PENDING</div><div class="metric-value">{pending_bills}</div><div class="metric-small">Require attention</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL VALUE</div><div class="metric-value">PKR {total_amount:,.0f}</div><div class="metric-small">All bills tracked</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">PAID</div><div class="metric-value">PKR {paid_amount:,.0f}</div><div class="metric-small">{paid_bills} cleared transactions</div></div>', unsafe_allow_html=True)


# =========================================================
# AGENT: EMAIL BILL FINDER (IF AVAILABLE)
# =========================================================
if find_bills_from_inbox:
    with st.container(border=True):
        st.markdown('<div class="section-title">📬 Bill Finder Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Autonomous agent that scans email invoices from demo_emails.json</div>', unsafe_allow_html=True)
        
        if st.button("Scan Inbox for Invoices", key="scan_inbox_btn"):
            with st.spinner("Agent scanning mail data..."):
                found = find_bills_from_inbox()
                st.success(f"Agent finished scanning: {found if found else 'Completed'}")
                st.rerun()


# =========================================================
# RECENT BILLS
# =========================================================
with st.container(border=True):
    st.markdown('<div class="section-title">Recent Bills</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Your latest bill tracking history</div>', unsafe_allow_html=True)

    if bills:
        for bill in bills[:5]:
            b_id, b_type, prov, cons, amt, due, status, created = bill
            st.markdown(
f"""<div style="display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid #1c2532;">
    <div>
        <div style="color:white; font-weight:600;">{prov or b_type or "Utility Bill"}</div>
        <div style="color:#667085; font-size:11px; margin-top:3px;">Account: {cons or "N/A"}</div>
    </div>
    <div style="text-align:right;">
        <div style="color:white; font-weight:700;">PKR {float(amt or 0):,.0f}</div>
        <div style="color:#10b981; font-size:11px;">{status}</div>
    </div>
</div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("No bills recorded yet. Use the OCR Scanner below to add one.")


# =========================================================
# SCAN BILL (OCR SERVICE)
# =========================================================
with st.container(border=True):
    st.markdown('<div class="section-title">Scan Bill (OCR Agent)</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Upload bill receipt to extract provider, due date, and amount</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload utility bill", type=["png", "jpg", "jpeg"], key="bill_upload")

    if uploaded_file:
        st.image(uploaded_file, caption="Receipt Preview", use_container_width=True)

        if st.button("Extract Data from Image", type="primary", key="ocr_btn"):
            if extract_text_from_image:
                with st.spinner("Extracting with OCR..."):
                    extracted_text = extract_text_from_image(uploaded_file)
                    if extracted_text:
                        st.session_state["scan_text"] = extracted_text
                        st.session_state["scan_provider"] = detect_provider(extracted_text) if detect_provider else ""
                        st.session_state["scan_amount"] = extract_amount(extracted_text) if extract_amount else 0.0
                        st.session_state["scan_consumer"] = extract_consumer_number(extracted_text) if extract_consumer_number else ""
                        st.success("Extracted bill parameters successfully.")
                    else:
                        st.warning("Could not extract readable text. Enter values manually below.")
            else:
                st.warning("OCR Service not installed. Please input manually.")

    # Bill Input Fields
    col_a, col_b = st.columns(2)
    with col_a:
        provider = st.text_input("Provider", value=st.session_state.get("scan_provider", ""), placeholder="KE, LESCO, SSGC, PTCL")
        bill_type = st.selectbox("Bill Type", ["Electricity", "Gas", "Internet", "Water", "Mobile", "Other"])
        consumer_number = st.text_input("Consumer #", value=st.session_state.get("scan_consumer", ""))
    
    with col_b:
        amount = st.number_input("Amount (PKR)", min_value=0.0, value=float(st.session_state.get("scan_amount", 0.0)), step=100.0)
        due_date = st.text_input("Due Date", placeholder="e.g. 15 Oct 2026")

    if st.button("Save Extracted Bill", type="primary", key="save_bill_btn"):
        if add_bill:
            b_id = add_bill(
                bill_type=bill_type,
                provider=provider,
                consumer_number=consumer_number,
                amount=amount,
                due_date=due_date,
                extracted_text=st.session_state.get("scan_text", "")
            )
            st.success(f"Bill #{b_id} added successfully.")
            for key in ["scan_text", "scan_provider", "scan_amount", "scan_consumer"]:
                st.session_state.pop(key, None)
            st.rerun()


# =========================================================
# BILLS & PAYMENT ACTION
# =========================================================
with st.container(border=True):
    st.markdown('<div class="section-title">My Bills & Settlements</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Pay and manage active balances</div>', unsafe_allow_html=True)

    if bills:
        for bill in bills:
            b_id, b_type, prov, cons, amt, due, status, created = bill
            with st.expander(f"{prov or b_type} • PKR {float(amt or 0):,.0f} ({status})"):
                col_x, col_y = st.columns(2)
                with col_x:
                    st.write(f"**Provider:** {prov}")
                    st.write(f"**Type:** {b_type}")
                    st.write(f"**Account/Consumer:** {cons}")
                with col_y:
                    st.write(f"**Due Date:** {due or 'N/A'}")
                    st.write(f"**Amount:** PKR {float(amt or 0):,.2f}")
                    st.write(f"**Status:** {status}")

                if status != "Paid":
                    if st.button(f"Pay PKR {float(amt or 0):,.0f}", key=f"pay_{b_id}"):
                        st.session_state["selected_bill"] = b_id
                        st.session_state["selected_amount"] = float(amt or 0)
                        st.session_state["show_payment"] = True
                        st.rerun()
    else:
        st.info("No bills saved yet.")


# =========================================================
# PAYMENT GATEWAY MODAL
# =========================================================
if st.session_state.get("show_payment", False):
    with st.container(border=True):
        st.markdown('<div class="section-title">Payment Settlement Gateway</div>', unsafe_allow_html=True)
        s_bill = st.session_state.get("selected_bill")
        s_amt = st.session_state.get("selected_amount", 0.0)

        st.write(f"#### Amount to Pay: PKR {s_amt:,.2f}")
        method = st.selectbox("Payment Channel", ["JazzCash", "EasyPaisa", "Bank Transfer", "Raast Pay"], key="pay_method_select")

        c_pay1, c_pay2 = st.columns(2)
        with c_pay1:
            if st.button("Confirm Payment", type="primary", key="confirm_pay_btn"):
                if add_payment:
                    add_payment(bill_id=s_bill, amount=s_amt, method=method)
                st.session_state["show_payment"] = False
                st.session_state.pop("selected_bill", None)
                st.session_state.pop("selected_amount", None)
                st.success("Payment settlement recorded.")
                st.rerun()
        with c_pay2:
            if st.button("Cancel", key="cancel_pay_btn"):
                st.session_state["show_payment"] = False
                st.rerun()


# =========================================================
# AI ASSISTANT (CHAT)
# =========================================================
with st.container(border=True):
    st.markdown('<div class="section-title">Finguard AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Real-time LLM financial advisor querying your bills and balances</div>', unsafe_allow_html=True)

    bill_context = "\n".join([f"- {b[1]} ({b[2]}): PKR {float(b[4] or 0):,.2f}, Due: {b[5]}, Status: {b[6]}" for b in bills]) if bills else "No bills recorded."

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_query = st.chat_input("Ask about your pending utility bills, payments, or due dates...")

    if user_query:
        st.session_state.chat_history.append(("user", user_query))
        with st.chat_message("user"):
            st.markdown(user_query)

        full_prompt = f"""You are Finguard AI assistant.
Current User Database:
{bill_context}

User question: {user_query}
Provide a crisp, clear, and helpful response regarding their financial bills."""

        with st.chat_message("assistant"):
            with st.spinner("Finguard AI checking data..."):
                response = ask_groq(full_prompt)
                st.markdown(response)

        st.session_state.chat_history.append(("assistant", response))


# =========================================================
# FOOTER
# =========================================================
st.markdown(
"""<div style="text-align:center; color:#475569; font-size:11px; margin-top:40px; padding-top:20px; border-top:1px solid #18202c;">
    FINGUARD AI • Intelligent Multi-Agent Financial Assistant • Groq
</div>""",
    unsafe_allow_html=True,
)
