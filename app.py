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

try:
    from bill_finder_agent import find_bills_from_inbox
except ImportError:
    find_bills_from_inbox = None

try:
    from reminder_agent import get_reminder_status, get_active_reminders_from_bills
except ImportError:
    get_reminder_status = None
    get_active_reminders_from_bills = None


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="FinGuard AI • Autonomous Financial Operations",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    init_db()
except Exception:
    pass


# =========================================================
# PRO FINTECH CSS (LIGHT SAAS DESIGN SYSTEM)
# =========================================================
st.markdown(
"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    background: #f8fafc !important;
    color: #0f172a !important;
}

section[data-testid="stSidebar"], header[data-testid="stHeader"], #MainMenu, footer {
    display: none !important;
    visibility: hidden !important;
}

.block-container {
    max-width: 1280px;
    padding-top: 25px;
    padding-bottom: 60px;
}

/* TOP NAVBAR */
.top-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 14px 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04);
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-logo {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #10b981, #047857);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 18px;
    box-shadow: 0 4px 10px rgba(16, 185, 129, 0.25);
}

.brand-text {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.8px;
    color: #0f172a;
}

.brand-badge {
    background: #ecfdf5;
    color: #059669;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    border: 1px solid #a7f3d0;
}

.nav-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 600;
    color: #475569;
    background: #f1f5f9;
    padding: 6px 14px;
    border-radius: 30px;
}

.status-pulse {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

/* PRO METRIC CARDS */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin-bottom: 24px;
}

.pro-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
}

.pro-card:hover {
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.06);
    border-color: #cbd5e1;
}

.card-header-flex {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.card-title {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #64748b;
    text-transform: uppercase;
}

.card-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}

.card-val {
    font-size: 26px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.8px;
    margin-bottom: 4px;
}

.card-sub {
    font-size: 12px;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* TAB NAVIGATION STYLING */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: #ffffff;
    padding: 6px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    margin-bottom: 20px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
    color: #64748b;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background: #ecfdf5 !important;
    color: #047857 !important;
}

/* CONTAINER ELEVATION */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
}

/* INPUTS REFINEMENT */
.stTextInput input, .stNumberInput input {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
}

.stTextInput input:focus, .stNumberInput input:focus {
    background-color: #ffffff !important;
    border-color: #10b981 !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12) !important;
}

div[data-baseweb="select"], div[data-baseweb="select"] * {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    border-color: #e2e8f0 !important;
    border-radius: 10px !important;
}

/* BUTTONS */
button[kind="primary"] {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
}

button[kind="primary"]:hover {
    box-shadow: 0 6px 18px rgba(16, 185, 129, 0.35) !important;
}

.stButton > button {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    font-weight: 600 !important;
}

/* STATUS BADGES */
.status-pill {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    display: inline-block;
}
.status-paid { background: #d1fae5; color: #047857; }
.status-pending { background: #fef3c7; color: #b45309; }
</style>""",
    unsafe_allow_html=True,
)


# =========================================================
# TOP NAVIGATION BAR
# =========================================================
st.markdown(
"""<div class="top-navbar">
    <div class="nav-brand">
        <div class="brand-logo">⚡</div>
        <div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="brand-text">FinGuard AI</span>
                <span class="brand-badge">SaaS v2.4</span>
            </div>
        </div>
    </div>
    <div class="nav-status">
        <span class="status-pulse"></span>
        <span>Groq LLaMA-3.3 • Active</span>
    </div>
</div>""",
    unsafe_allow_html=True,
)


# =========================================================
# DATA FETCHING & STATS
# =========================================================
bills = get_bills() if "get_bills" in globals() else []
payments = get_payments() if "get_payments" in globals() else []

total_bills = len(bills)
paid_bills = len([b for b in bills if str(b[6]).lower() == "paid"])
pending_bills = len([b for b in bills if str(b[6]).lower() != "paid"])
total_amount = sum(float(b[4] or 0) for b in bills)
paid_amount = sum(float(p[2] or 0) for p in payments)
pending_amount = total_amount - paid_amount if (total_amount - paid_amount) > 0 else 0.0

# 4 PRO SAAS STAT CARDS
st.markdown(
f"""<div class="metric-grid">
    <div class="pro-card">
        <div class="card-header-flex">
            <span class="card-title">Total Obligation</span>
            <div class="card-icon" style="background:#f1f5f9; color:#475569;">📑</div>
        </div>
        <div class="card-val">PKR {total_amount:,.0f}</div>
        <div class="card-sub">{total_bills} utility bills tracked</div>
    </div>
    <div class="pro-card">
        <div class="card-header-flex">
            <span class="card-title">Pending Balances</span>
            <div class="card-icon" style="background:#fffbeb; color:#d97706;">⏳</div>
        </div>
        <div class="card-val" style="color:#d97706;">PKR {pending_amount:,.0f}</div>
        <div class="card-sub">{pending_bills} bills require clearance</div>
    </div>
    <div class="pro-card">
        <div class="card-header-flex">
            <span class="card-title">Settled Amount</span>
            <div class="card-icon" style="background:#ecfdf5; color:#059669;">✅</div>
        </div>
        <div class="card-val" style="color:#047857;">PKR {paid_amount:,.0f}</div>
        <div class="card-sub">{paid_bills} paid transactions</div>
    </div>
    <div class="pro-card">
        <div class="card-header-flex">
            <span class="card-title">Automation Rate</span>
            <div class="card-icon" style="background:#eff6ff; color:#2563eb;">⚡</div>
        </div>
        <div class="card-val" style="color:#2563eb;">100%</div>
        <div class="card-sub">Autonomous OCR & Agents</div>
    </div>
</div>""",
    unsafe_allow_html=True,
)


# =========================================================
# PRO TAB NAVIGATION
# =========================================================
tab_overview, tab_scan, tab_bills, tab_chat = st.tabs([
    "📊 Financial Overview",
    "📸 Ingest & OCR Scan",
    "💳 Bills & Settlements",
    "🤖 FinGuard Copilot"
])


# ---------------------------------------------------------
# TAB 1: OVERVIEW & INTELLIGENCE
# ---------------------------------------------------------
with tab_overview:
    col_left, col_right = st.columns([1.8, 1.2])

    with col_left:
        with st.container(border=True):
            st.markdown('<div style="font-weight:700; font-size:16px; margin-bottom:14px;">Recent Invoices</div>', unsafe_allow_html=True)
            if bills:
                for b in bills[:6]:
                    b_id, b_type, prov, cons, amt, due, status, created = b
                    is_paid = str(status).lower() == "paid"
                    pill_class = "status-paid" if is_paid else "status-pending"
                    st.markdown(
f"""<div style="display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid #f1f5f9;">
    <div>
        <div style="font-weight:700; color:#0f172a; font-size:14px;">{prov or b_type}</div>
        <div style="font-size:12px; color:#64748b; margin-top:2px;">Ref: {cons or 'N/A'} • Due: {due or 'N/A'}</div>
    </div>
    <div style="text-align:right;">
        <div style="font-weight:800; color:#0f172a; font-size:15px;">PKR {float(amt or 0):,.0f}</div>
        <span class="status-pill {pill_class}">{status}</span>
    </div>
</div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No active invoices recorded in the system.")

    with col_right:
        with st.container(border=True):
            st.markdown('<div style="font-weight:700; font-size:16px; margin-bottom:14px;">Automated Agents</div>', unsafe_allow_html=True)
            
            # Inbox Agent Trigger
            if find_bills_from_inbox:
                st.markdown(
                    """<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:14px; margin-bottom:14px;">
                        <div style="font-weight:700; font-size:13px; color:#0f172a;">📬 Email Ingestion Agent</div>
                        <div style="font-size:11px; color:#64748b; margin-bottom:8px;">Auto-parses receipts from connected inbox.</div>
                    </div>""",
                    unsafe_allow_html=True
                )
                if st.button("Run Inbox Parser Agent", key="inbox_agent_btn"):
                    with st.spinner("Agent parsing inbox json..."):
                        find_bills_from_inbox()
                        st.success("Inbox parsing complete!")
                        st.rerun()

            # Payment Log Summary
            st.markdown('<div style="font-weight:700; font-size:14px; margin-top:18px; margin-bottom:10px;">Recent Settlements</div>', unsafe_allow_html=True)
            if payments:
                for p in payments[:3]:
                    st.markdown(
                        f"""<div style="font-size:12px; padding:8px 0; border-bottom:1px solid #f1f5f9; display:flex; justify-content:space-between;">
                            <span>{p[1]} ({p[3]})</span>
                            <span style="font-weight:700; color:#059669;">PKR {float(p[2] or 0):,.0f}</span>
                        </div>""",
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No payments logged yet.")


# ---------------------------------------------------------
# TAB 2: INGEST & OCR SCAN
# ---------------------------------------------------------
with tab_scan:
    with st.container(border=True):
        st.markdown('<div style="font-weight:700; font-size:17px; margin-bottom:2px;">Automated Receipt Extraction</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px; color:#64748b; margin-bottom:20px;">Upload electricity, gas, or broadband bills to extract parameters instantly.</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload utility document", type=["png", "jpg", "jpeg"], key="main_uploader")

        if uploaded_file:
            col_img, col_proc = st.columns([1, 1.5])
            with col_img:
                st.image(uploaded_file, caption="Receipt Source", use_container_width=True)

            with col_proc:
                if st.button("Run Vision OCR Model", type="primary", key="run_ocr_btn"):
                    if extract_text_from_image:
                        with st.spinner("Extracting text features via OCR..."):
                            extracted = extract_text_from_image(uploaded_file)
                            if extracted:
                                st.session_state["scan_text"] = extracted
                                st.session_state["scan_provider"] = detect_provider(extracted) if detect_provider else ""
                                st.session_state["scan_amount"] = extract_amount(extracted) if extract_amount else 0.0
                                st.session_state["scan_consumer"] = extract_consumer_number(extracted) if extract_consumer_number else ""
                                st.success("Document parameters parsed successfully.")
                            else:
                                st.warning("OCR could not resolve high confidence text. Please verify manually below.")
                    else:
                        st.warning("OCR service is not initialized.")

        st.divider()
        st.markdown('<div style="font-weight:700; font-size:15px; margin-bottom:12px;">Bill Verification & Ingestion</div>', unsafe_allow_html=True)

        c1_in, c2_in = st.columns(2)
        with c1_in:
            provider = st.text_input("Utility Provider", value=st.session_state.get("scan_provider", ""), placeholder="e.g. K-Electric, SSGC, PTCL")
            bill_type = st.selectbox("Classification", ["Electricity", "Gas", "Internet", "Water", "Telecom", "Other"])
            consumer_number = st.text_input("Consumer Account #", value=st.session_state.get("scan_consumer", ""), placeholder="14-digit Account ID")

        with c2_in:
            amount = st.number_input("Payable Amount (PKR)", min_value=0.0, value=float(st.session_state.get("scan_amount", 0.0)), step=100.0)
            due_date = st.text_input("Due Date", placeholder="e.g. 15 Oct 2026")

        if st.button("Save & Register Bill", type="primary", key="save_bill_pro"):
            if add_bill:
                new_id = add_bill(
                    bill_type=bill_type,
                    provider=provider,
                    consumer_number=consumer_number,
                    amount=amount,
                    due_date=due_date,
                    extracted_text=st.session_state.get("scan_text", "")
                )
                st.success(f"Invoice registered successfully as Record #{new_id}.")
                for k in ["scan_text", "scan_provider", "scan_amount", "scan_consumer"]:
                    st.session_state.pop(k, None)
                st.rerun()


# ---------------------------------------------------------
# TAB 3: BILLS & SETTLEMENTS
# ---------------------------------------------------------
with tab_bills:
    with st.container(border=True):
        st.markdown('<div style="font-weight:700; font-size:17px; margin-bottom:2px;">Active Utility Liabilities</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px; color:#64748b; margin-bottom:20px;">Manage settlements and record online payments.</div>', unsafe_allow_html=True)

        if bills:
            for b in bills:
                b_id, b_type, prov, cons, amt, due, status, created = b
                is_paid = str(status).lower() == "paid"

                with st.expander(f"{prov or b_type} • PKR {float(amt or 0):,.0f} ({status.upper()})"):
                    d1, d2 = st.columns(2)
                    with d1:
                        st.markdown(f"**Entity:** {prov}")
                        st.markdown(f"**Type:** {b_type}")
                        st.markdown(f"**Consumer ID:** `{cons or 'N/A'}`")
                    with d2:
                        st.markdown(f"**Due Date:** {due or 'Not provided'}")
                        st.markdown(f"**Outstanding:** PKR {float(amt or 0):,.2f}")
                        st.markdown(f"**Status:** {status}")

                    if not is_paid:
                        if st.button(f"Pay PKR {float(amt or 0):,.0f}", key=f"pay_btn_{b_id}"):
                            st.session_state["selected_bill"] = b_id
                            st.session_state["selected_amount"] = float(amt or 0)
                            st.session_state["show_payment"] = True
                            st.rerun()
        else:
            st.info("No active invoices registered.")

    # Payment Gateway Trigger
    if st.session_state.get("show_payment", False):
        with st.container(border=True):
            st.markdown('<div style="font-weight:700; font-size:16px;">Instant Payment Gateway</div>', unsafe_allow_html=True)
            s_bill = st.session_state.get("selected_bill")
            s_amt = st.session_state.get("selected_amount", 0.0)

            st.write(f"Payment Amount: **PKR {s_amt:,.2f}**")
            p_method = st.selectbox("Settlement Gateway", ["JazzCash Direct", "EasyPaisa Online", "1Link Bank Transfer", "Raast P2M"])

            p_col1, p_col2 = st.columns(2)
            with p_col1:
                if st.button("Complete Transaction", type="primary", key="confirm_pay_btn"):
                    if add_payment:
                        add_payment(bill_id=s_bill, amount=s_amt, method=p_method)
                    st.session_state["show_payment"] = False
                    st.session_state.pop("selected_bill", None)
                    st.session_state.pop("selected_amount", None)
                    st.success("Payment recorded successfully!")
                    st.rerun()
            with p_col2:
                if st.button("Cancel", key="cancel_pay_btn"):
                    st.session_state["show_payment"] = False
                    st.rerun()


# ---------------------------------------------------------
# TAB 4: AI COPILOT
# ---------------------------------------------------------
with tab_chat:
    with st.container(border=True):
        st.markdown('<div style="font-weight:700; font-size:17px; margin-bottom:2px;">FinGuard Financial Copilot</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px; color:#64748b; margin-bottom:15px;">Real-time natural language query interface for your liabilities.</div>', unsafe_allow_html=True)

        bill_ctx = "\n".join([f"- {b[1]} ({b[2]}): PKR {float(b[4] or 0):,.2f}, Due: {b[5]}, Status: {b[6]}" for b in bills]) if bills else "No active bills."

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for role, text in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(text)

        query = st.chat_input("Ask about upcoming deadlines, pending amounts, or payment strategies...")
        if query:
            st.session_state.chat_history.append(("user", query))
            with st.chat_message("user"):
                st.markdown(query)

            prompt = f"User Database Context:\n{bill_ctx}\n\nQuestion: {query}\nAnswer accurately, concisely, and professionally."
            with st.chat_message("assistant"):
                with st.spinner("FinGuard analyzing financial data..."):
                    answer = ask_groq(prompt)
                    st.markdown(answer)

            st.session_state.chat_history.append(("assistant", answer))
