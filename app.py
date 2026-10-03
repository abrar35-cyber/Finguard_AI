import os
from html import escape as esc

import streamlit as st

# =========================================================
# IMPORTS (safe fallbacks so the app never crashes on import)
# =========================================================
try:
    from database import init_db, get_bills, get_payments, add_bill, add_payment
    DB_OK = True
except ImportError:
    DB_OK = False
    init_db = lambda: None
    get_bills = lambda: []
    get_payments = lambda: []
    add_bill = None
    add_payment = None

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
    extract_text_from_image = extract_amount = detect_provider = extract_consumer_number = None

try:
    from bill_intelligence_agent import analyze_bill
except ImportError:
    analyze_bill = None

try:
    from bill_finder_agent import find_bills_from_inbox
except ImportError:
    find_bills_from_inbox = None

try:
    from reminder_agent import get_reminder_details
except ImportError:
    get_reminder_details = None

st.set_page_config(page_title="FinGuard AI", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

try:
    init_db()
except Exception:
    pass

if not DB_OK:
    st.error("Missing database.py module.")
if st.session_state.get("flash"):
    st.toast(st.session_state.pop("flash"), icon="✅")

# =========================================================
# STYLE
# =========================================================
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root{--bg:#070a12;--card:#0e1422;--card2:#121a2b;--line:#1f2a40;--txt:#f1f5f9;--mut:#8b9ab3;--green:#10b981;--blue:#38bdf8;--amber:#f59e0b;--red:#f43f5e;}
html,body,[class*="css"],.stApp{font-family:'Plus Jakarta Sans',sans-serif!important;color:var(--txt)!important;}
.stApp{background:radial-gradient(900px 400px at 10% -10%,rgba(16,185,129,.14),transparent),radial-gradient(800px 400px at 95% 0%,rgba(56,189,248,.10),transparent),var(--bg)!important;}
section[data-testid="stSidebar"],header[data-testid="stHeader"],#MainMenu,footer{display:none!important;}
.block-container{max-width:1240px;padding-top:18px;padding-bottom:60px;}
.brand{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.brand-logo{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#10b981,#059669);display:flex;align-items:center;justify-content:center;font-size:19px;box-shadow:0 6px 18px rgba(16,185,129,.4)}
.brand-text{font-size:24px;font-weight:800;letter-spacing:-.8px}
.brand-tag{margin-left:auto;font-size:11px;color:var(--mut);border:1px solid var(--line);padding:5px 11px;border-radius:99px;background:rgba(255,255,255,.03)}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:rgba(14,20,34,.8);padding:6px;border-radius:14px;border:1px solid var(--line);margin-bottom:22px}
.stTabs [data-baseweb="tab"]{border-radius:10px;padding:10px 18px;font-weight:600;font-size:13.5px;color:var(--mut)!important;background:transparent!important;border:none!important;transition:.2s}
.stTabs [data-baseweb="tab"]:hover{color:#fff!important;background:rgba(255,255,255,.05)!important}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,rgba(16,185,129,.22),rgba(16,185,129,.08))!important;color:#34d399!important;box-shadow:inset 0 0 0 1px rgba(16,185,129,.5)}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.hero{position:relative;overflow:hidden;border-radius:22px;padding:30px 32px;margin-bottom:20px;border:1px solid rgba(16,185,129,.25);background:linear-gradient(120deg,rgba(16,185,129,.20),rgba(56,189,248,.10) 55%,rgba(14,20,34,.6))}
.hero:after{content:"⚡";position:absolute;right:26px;top:-18px;font-size:150px;opacity:.07}
.hero h1{margin:0 0 6px;font-size:30px;font-weight:800;letter-spacing:-1px}
.hero p{margin:0;color:#b6c2d6;font-size:14.5px}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.chip{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);padding:7px 14px;border-radius:99px;font-size:12.5px;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}
@media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:linear-gradient(160deg,var(--card2),var(--card));border:1px solid var(--line);border-radius:18px;padding:18px 20px;transition:.25s}
.kpi:hover{transform:translateY(-4px);border-color:rgba(16,185,129,.5);box-shadow:0 14px 30px rgba(0,0,0,.4)}
.kpi-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.kpi-t{font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:var(--mut)}
.kpi-i{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px}
.kpi-v{font-size:27px;font-weight:800;letter-spacing:-.8px}
.kpi-s{font-size:12px;color:var(--mut);margin-top:3px}
div[data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(160deg,var(--card2),var(--card))!important;border:1px solid var(--line)!important;border-radius:18px!important;padding:20px!important}
.sec-t{font-weight:700;font-size:16px;margin-bottom:2px}
.sec-s{font-size:12.5px;color:var(--mut);margin-bottom:14px}
.bill-row{display:flex;align-items:center;gap:14px;padding:13px 12px;margin:0 -12px;border-radius:12px;border-bottom:1px solid var(--line);transition:.2s}
.bill-row:hover{background:rgba(255,255,255,.04)}
.bill-ico{width:42px;height:42px;border-radius:12px;background:rgba(255,255,255,.06);display:flex;align-items:center;justify-content:center;font-size:20px}
.bill-main{flex:1;min-width:0}
.bill-name{font-weight:700;font-size:14.5px}
.bill-sub{font-size:12px;color:var(--mut);margin-top:2px}
.bill-right{text-align:right}
.bill-amt{font-weight:800;font-size:15px;margin-bottom:4px}
.badge{display:inline-block;padding:4px 10px;border-radius:99px;font-size:11px;font-weight:700}
.b-critical{background:rgba(244,63,94,.16);color:#fb7185}
.b-warning{background:rgba(245,158,11,.16);color:#fbbf24}
.b-upcoming{background:rgba(56,189,248,.16);color:#7dd3fc}
.b-normal{background:rgba(16,185,129,.16);color:#34d399}
.b-unknown{background:rgba(148,163,184,.16);color:#cbd5e1}
.b-paid{background:rgba(16,185,129,.22);color:#34d399}
.donut-wrap{display:flex;align-items:center;gap:22px;flex-wrap:wrap}
.donut{width:150px;height:150px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.donut-hole{width:104px;height:104px;border-radius:50%;background:var(--card);display:flex;flex-direction:column;align-items:center;justify-content:center}
.donut-hole span{font-size:10.5px;color:var(--mut)}
.donut-hole b{font-size:13px}
.legend{flex:1;min-width:140px}
.lg{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:4px 0}
.lg b{margin-left:auto}
.dot{width:10px;height:10px;border-radius:50%}
.bar{height:12px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;margin:10px 0 8px}
.bar>div{height:100%;border-radius:99px;background:linear-gradient(90deg,#10b981,#38bdf8)}
.bar-l{display:flex;justify-content:space-between;font-size:12px;color:var(--mut)}
.empty{text-align:center;padding:26px 10px}
.empty .big{font-size:46px;margin-bottom:6px}
.empty h3{margin:0 0 6px;font-size:19px}
.steps{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:16px 0 6px}
.step{background:rgba(255,255,255,.05);border:1px solid var(--line);border-radius:12px;padding:10px 16px;font-size:12.5px;font-weight:600}
.muted{color:var(--mut);font-size:13px}
.settle{display:flex;justify-content:space-between;font-size:12.5px;padding:8px 0;border-bottom:1px solid var(--line)}
label[data-testid="stWidgetLabel"] p{color:var(--txt)!important;font-weight:600!important;font-size:13px!important}
.stTextInput input,.stNumberInput input{background:#0b1220!important;color:#fff!important;border:1px solid var(--line)!important;border-radius:10px!important}
.stTextInput input:focus,.stNumberInput input:focus{border-color:var(--green)!important;box-shadow:0 0 0 2px rgba(16,185,129,.25)!important}
div[data-baseweb="select"]>div{background:#0b1220!important;border-color:var(--line)!important;border-radius:10px!important}
[data-testid="stFileUploader"] section{background:#0b1220!important;border:1.5px dashed #2a3a58!important;border-radius:14px!important}
.stButton>button{border-radius:10px!important;border:1px solid var(--line)!important;background:#101828!important;color:#fff!important;font-weight:600!important;transition:.2s}
.stButton>button:hover{border-color:var(--green)!important;color:#34d399!important;transform:translateY(-1px)}
button[kind="primary"]{background:linear-gradient(135deg,#10b981,#059669)!important;border:none!important;box-shadow:0 6px 16px rgba(16,185,129,.3)!important}
button[kind="primary"]:hover{color:#fff!important;filter:brightness(1.1)}
[data-testid="stExpander"]{background:rgba(255,255,255,.02)!important;border:1px solid var(--line)!important;border-radius:12px!important}
[data-testid="stChatMessage"]{background:var(--card2)!important;border:1px solid var(--line)!important;border-radius:14px!important}
[data-testid="stChatInput"]{background:#0b1220!important;border:1px solid var(--line)!important;border-radius:14px!important}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================
ICONS = {"electricity": "⚡", "gas": "🔥", "internet": "🌐", "water": "💧", "telecom": "📱"}
PALETTE = ["#10b981", "#38bdf8", "#f59e0b", "#a78bfa", "#f472b6", "#fb7185"]


def money(x):
    return f"PKR {float(x or 0):,.0f}"


def icon_for(b_type):
    return ICONS.get(str(b_type).lower(), "🧾")


def urgency(due):
    if get_reminder_details:
        d = get_reminder_details(due)
        return d["message"], d["urgency"], d["days_left"]
    return "Due date unavailable", "unknown", None


def status_badge(status, due):
    if str(status).lower() == "paid":
        return '<span class="badge b-paid">Paid</span>'
    msg, urg, _ = urgency(due)
    return f'<span class="badge b-{urg}">{esc(msg)}</span>'


def bill_row(b):
    b_id, b_type, prov, cons, amt, due, status, created = b
    name = esc(str(prov or b_type))
    ref = esc(str(cons or "N/A"))
    due_s = esc(str(due or "N/A"))
    return (
        f'<div class="bill-row"><div class="bill-ico">{icon_for(b_type)}</div>'
        f'<div class="bill-main"><div class="bill-name">{name}</div>'
        f'<div class="bill-sub">Ref {ref} · Due {due_s}</div></div>'
        f'<div class="bill-right"><div class="bill-amt">{money(amt)}</div>{status_badge(status, due)}</div></div>'
    )


def kpi(title, value, sub, icon, color, bg):
    return (
        f'<div class="kpi"><div class="kpi-top"><span class="kpi-t">{title}</span>'
        f'<div class="kpi-i" style="background:{bg};color:{color}">{icon}</div></div>'
        f'<div class="kpi-v" style="color:{color}">{value}</div><div class="kpi-s">{sub}</div></div>'
    )


def donut(bill_list):
    totals = {}
    for b in bill_list:
        k = str(b[2] or b[1])
        totals[k] = totals.get(k, 0) + float(b[4] or 0)
    total = sum(totals.values())
    if total <= 0:
        return '<div class="muted">No spending data yet.</div>'
    stops, legend, start = [], [], 0.0
    for i, (k, v) in enumerate(sorted(totals.items(), key=lambda x: -x[1])):
        c = PALETTE[i % len(PALETTE)]
        end = start + v / total * 100
        stops.append(f"{c} {start:.2f}% {end:.2f}%")
        start = end
        legend.append(f'<div class="lg"><span class="dot" style="background:{c}"></span>{esc(k)}<b>{v / total * 100:.0f}%</b></div>')
    grad = ",".join(stops)
    return (
        f'<div class="donut-wrap"><div class="donut" style="background:conic-gradient({grad})">'
        f'<div class="donut-hole"><span>Total</span><b>{money(total)}</b></div></div>'
        f'<div class="legend">{"".join(legend)}</div></div>'
    )


def run_inbox():
    added = find_bills_from_inbox()
    st.session_state["flash"] = f"{added} new bill(s) added." if added else "No new bills found."
    st.rerun()


# =========================================================
# DATA
# =========================================================
bills = get_bills()
payments = get_payments()

total_bills = len(bills)
paid_bills = len([b for b in bills if str(b[6]).lower() == "paid"])
pending_list = [b for b in bills if str(b[6]).lower() != "paid"]
pending_bills = len(pending_list)
total_amount = sum(float(b[4] or 0) for b in bills)
paid_amount = sum(float(p[2] or 0) for p in payments)
pending_amount = max(total_amount - paid_amount, 0.0)
pct_paid = min(paid_amount / total_amount * 100, 100) if total_amount > 0 else 0

urgent_count = 0
next_due_text = ""
if pending_list and get_reminder_details:
    ranked = sorted(pending_list, key=lambda b: (get_reminder_details(b[5])["days_left"] if get_reminder_details(b[5])["days_left"] is not None else 9999))
    urgent_count = len([b for b in pending_list if get_reminder_details(b[5])["urgency"] in ("critical", "warning")])
    nb = ranked[0]
    next_due_text = f'{nb[2] or nb[1]}: {get_reminder_details(nb[5])["message"]}'

# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<div class="brand"><div class="brand-logo">⚡</div><span class="brand-text">FinGuard AI</span>'
    '<span class="brand-tag">🇵🇰 Smart utility bill assistant</span></div>',
    unsafe_allow_html=True,
)

tab_overview, tab_scan, tab_bills, tab_chat = st.tabs(["📊 Overview", "📸 Scan Bill", "💳 Bills", "🤖 Copilot"])

# ---------------------------------------------------------
# TAB 1: OVERVIEW
# ---------------------------------------------------------
with tab_overview:
    if bills:
        headline = f"{pending_bills} bill(s) waiting, {money(pending_amount)} to clear" if pending_bills else "All bills are cleared. Nice work!"
        chips = f'<span class="chip">📑 {total_bills} bills tracked</span><span class="chip">🔔 {urgent_count} need attention</span>'
        if next_due_text:
            chips += f'<span class="chip">⏰ Next: {esc(next_due_text)}</span>'
    else:
        headline = "Scan your first bill to get started"
        chips = '<span class="chip">📸 Scan</span><span class="chip">🤖 Auto-extract</span><span class="chip">💳 Track &amp; pay</span>'
    st.markdown(
        f'<div class="hero"><h1>Your bills, under control</h1><p>{headline}</p><div class="chips">{chips}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="kpis">'
        + kpi("Total Obligation", money(total_amount), f"{total_bills} bills tracked", "📑", "#cbd5e1", "rgba(148,163,184,.15)")
        + kpi("Pending", money(pending_amount), f"{pending_bills} bills to clear", "⏳", "#f59e0b", "rgba(245,158,11,.15)")
        + kpi("Settled", money(paid_amount), f"{len(payments)} payments", "✅", "#10b981", "rgba(16,185,129,.15)")
        + kpi("Needs Attention", str(urgent_count), "Overdue or due in 3 days", "🔔", "#38bdf8", "rgba(56,189,248,.15)")
        + "</div>",
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.7, 1.3])

    with col_left:
        with st.container(border=True):
            if bills:
                st.markdown('<div class="sec-t">Upcoming &amp; recent bills</div><div class="sec-s">Most urgent first</div>', unsafe_allow_html=True)
                def sort_key(b):
                    if str(b[6]).lower() == "paid":
                        return 99999
                    d = urgency(b[5])[2]
                    return d if d is not None else 9999
                st.markdown("".join(bill_row(b) for b in sorted(bills, key=sort_key)[:6]), unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="empty"><div class="big">🧾</div><h3>No bills yet</h3>'
                    '<div class="muted">Start in three quick steps</div>'
                    '<div class="steps"><div class="step">1 · Scan a bill photo</div><div class="step">2 · Review details</div><div class="step">3 · Pay &amp; track</div></div></div>',
                    unsafe_allow_html=True,
                )
                if find_bills_from_inbox:
                    if st.button("✨ Load demo data", type="primary", key="demo_btn", use_container_width=True):
                        run_inbox()
                else:
                    st.warning("Inbox agent not found. Update bill_finder_agent.py on GitHub to enable demo data.")

    with col_right:
        with st.container(border=True):
            st.markdown('<div class="sec-t">Spending by provider</div><div class="sec-s">Share of total obligation</div>', unsafe_allow_html=True)
            st.markdown(donut(bills), unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<div class="sec-t">Payment progress</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="bar"><div style="width:{pct_paid:.0f}%"></div></div>'
                f'<div class="bar-l"><span>{money(paid_amount)} paid</span><span>{pct_paid:.0f}% of {money(total_amount)}</span></div>',
                unsafe_allow_html=True,
            )

        with st.container(border=True):
            st.markdown('<div class="sec-t">Automation</div><div class="sec-s">Email agent reads bills from your inbox</div>', unsafe_allow_html=True)
            if find_bills_from_inbox:
                if st.button("📬 Run Inbox Parser Agent", key="inbox_agent_btn", use_container_width=True):
                    with st.spinner("Agent parsing inbox..."):
                        run_inbox()
            else:
                st.caption("Inbox agent unavailable. Update bill_finder_agent.py.")
            st.markdown('<div class="sec-t" style="margin-top:16px;font-size:14px">Recent settlements</div>', unsafe_allow_html=True)
            if payments:
                st.markdown(
                    "".join(
                        f'<div class="settle"><span>{esc(str(p[1]))} ({esc(str(p[3]))})</span><b style="color:#34d399">{money(p[2])}</b></div>'
                        for p in payments[:3]
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.caption("No payments logged yet.")

# ---------------------------------------------------------
# TAB 2: SCAN
# ---------------------------------------------------------
with tab_scan:
    with st.container(border=True):
        st.markdown('<div class="sec-t">Scan &amp; add a bill</div><div class="sec-s">Upload a photo of your electricity, gas or internet bill. We read it for you.</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload bill image", type=["png", "jpg", "jpeg"], key="main_uploader")

        if uploaded_file:
            col_img, col_proc = st.columns([1, 1.5])
            with col_img:
                st.image(uploaded_file, caption="Bill preview", use_container_width=True)
            with col_proc:
                st.markdown('<div class="muted" style="margin-bottom:10px">Step 1: extract text from the image</div>', unsafe_allow_html=True)
                if st.button("🔍 Read bill with OCR", type="primary", key="run_ocr_btn"):
                    if extract_text_from_image:
                        with st.spinner("Reading your bill..."):
                            extracted = extract_text_from_image(uploaded_file)
                            if extracted:
                                st.session_state["scan_text"] = extracted
                                st.session_state["scan_provider"] = detect_provider(extracted) if detect_provider else ""
                                st.session_state["scan_amount"] = extract_amount(extracted) if extract_amount else 0.0
                                st.session_state["scan_consumer"] = extract_consumer_number(extracted) if extract_consumer_number else ""
                                st.session_state["scan_due"] = ""
                                if analyze_bill and (not st.session_state["scan_provider"] or not st.session_state["scan_amount"] or not st.session_state["scan_consumer"]):
                                    try:
                                        ai = analyze_bill({"content": extracted, "source": "ocr"}) or {}
                                        if ai.get("provider") and not st.session_state["scan_provider"]:
                                            st.session_state["scan_provider"] = str(ai["provider"])
                                        if ai.get("amount") and not st.session_state["scan_amount"]:
                                            st.session_state["scan_amount"] = float(ai["amount"])
                                        if ai.get("account_number") and not st.session_state["scan_consumer"]:
                                            st.session_state["scan_consumer"] = str(ai["account_number"])
                                        if ai.get("due_date"):
                                            st.session_state["scan_due"] = str(ai["due_date"])
                                    except Exception:
                                        pass
                                st.success("Bill read. Please check the details below.")
                            else:
                                st.warning("Could not read the text clearly. Please fill the details manually.")
                    else:
                        st.warning("OCR service is not available.")

        st.divider()
        st.markdown('<div class="sec-t" style="font-size:15px">Step 2: verify and save</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            provider = st.text_input("Utility provider", value=st.session_state.get("scan_provider", ""), placeholder="e.g. K-Electric, SSGC, PTCL")
            bill_type = st.selectbox("Category", ["Electricity", "Gas", "Internet", "Water", "Telecom", "Other"])
            consumer_number = st.text_input("Consumer / account number", value=st.session_state.get("scan_consumer", ""))
        with c2:
            amount = st.number_input("Payable amount (PKR)", min_value=0.0, value=float(st.session_state.get("scan_amount", 0.0)), step=100.0)
            due_date = st.text_input("Due date", value=st.session_state.get("scan_due", ""), placeholder="e.g. 15 Oct 2026 or 2026-10-15")

        if st.button("💾 Save bill", type="primary", key="save_bill_pro"):
            if add_bill and provider and amount > 0:
                new_id = add_bill(
                    bill_type=bill_type,
                    provider=provider,
                    consumer_number=consumer_number,
                    amount=amount,
                    due_date=due_date,
                    extracted_text=st.session_state.get("scan_text", ""),
                )
                for k in ["scan_text", "scan_provider", "scan_amount", "scan_consumer", "scan_due"]:
                    st.session_state.pop(k, None)
                st.session_state["flash"] = f"Bill #{new_id} saved."
                st.rerun()
            else:
                st.warning("Please enter at least a provider and an amount above 0.")

# ---------------------------------------------------------
# TAB 3: BILLS
# ---------------------------------------------------------
with tab_bills:
    with st.container(border=True):
        st.markdown('<div class="sec-t">Your bills</div><div class="sec-s">Review details and pay securely (demo)</div>', unsafe_allow_html=True)
        view = st.radio("Show", ["All", "Pending", "Paid"], horizontal=True, label_visibility="collapsed")
        shown = [b for b in bills if view == "All" or (view == "Paid") == (str(b[6]).lower() == "paid")]

        if shown:
            for b in shown:
                b_id, b_type, prov, cons, amt, due, status, created = b
                is_paid = str(status).lower() == "paid"
                st.markdown(bill_row(b), unsafe_allow_html=True)
                with st.expander("Details"):
                    d1, d2 = st.columns(2)
                    with d1:
                        st.markdown(f"**Provider:** {prov}")
                        st.markdown(f"**Category:** {b_type}")
                        st.markdown(f"**Consumer ID:** `{cons or 'N/A'}`")
                    with d2:
                        st.markdown(f"**Due date:** {due or 'Not provided'}")
                        st.markdown(f"**Amount:** PKR {float(amt or 0):,.2f}")
                        st.markdown(f"**Status:** {status}")
                    if not is_paid and st.button(f"Pay {money(amt)}", key=f"pay_btn_{b_id}", type="primary"):
                        st.session_state["selected_bill"] = b_id
                        st.session_state["selected_amount"] = float(amt or 0)
                        st.session_state["show_payment"] = True
                        st.rerun()
        else:
            st.info("No bills here yet.")

    if st.session_state.get("show_payment", False):
        with st.container(border=True):
            st.markdown('<div class="sec-t">Checkout</div>', unsafe_allow_html=True)
            st.caption("Demo mode: this only records a payment inside FinGuard. No real money is moved.")
            s_bill = st.session_state.get("selected_bill")
            s_amt = st.session_state.get("selected_amount", 0.0)
            st.write(f"Amount: **PKR {s_amt:,.2f}**")
            p_method = st.selectbox("Payment method", ["JazzCash", "EasyPaisa", "1Link Bank Transfer", "Raast"])
            p1, p2 = st.columns(2)
            with p1:
                if st.button("Confirm payment", type="primary", key="confirm_pay_btn"):
                    ok = add_payment(bill_id=s_bill, amount=s_amt, method=p_method) if add_payment else False
                    for k in ["show_payment", "selected_bill", "selected_amount"]:
                        st.session_state.pop(k, None)
                    st.session_state["flash"] = "Payment recorded." if ok else "That bill is already paid."
                    st.rerun()
            with p2:
                if st.button("Cancel", key="cancel_pay_btn"):
                    st.session_state["show_payment"] = False
                    st.rerun()

# ---------------------------------------------------------
# TAB 4: COPILOT
# ---------------------------------------------------------
with tab_chat:
    with st.container(border=True):
        st.markdown('<div class="sec-t">FinGuard Copilot</div><div class="sec-s">Ask anything about your bills</div>', unsafe_allow_html=True)

        bill_ctx = "\n".join(
            f"- {b[1]} ({b[2]}): PKR {float(b[4] or 0):,.2f}, Due: {b[5]}, Status: {b[6]}" for b in bills
        ) if bills else "No active bills."

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        s1, s2, s3 = st.columns(3)
        for col, q in zip(
            (s1, s2, s3),
            ("Which bill is due first?", "How much do I owe in total?", "How can I save on bills?"),
        ):
            if col.button(q, key=f"sugg_{q}", use_container_width=True):
                st.session_state["quick_q"] = q

        for role, text in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(text)

        query = st.chat_input("Ask about deadlines, pending amounts, or payment tips...") or st.session_state.pop("quick_q", None)

        if query:
            st.session_state.chat_history.append(("user", query))
            with st.chat_message("user"):
                st.markdown(query)
            history_ctx = "\n".join(f"{r}: {t}" for r, t in st.session_state.chat_history[-7:-1])
            prompt = (
                f"User Database Context:\n{bill_ctx}\n\n"
                f"Recent conversation:\n{history_ctx or 'None'}\n\n"
                f"Question: {query}\nAnswer accurately, concisely, and professionally."
            )
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = ask_groq(prompt)
                st.markdown(answer)
            st.session_state.chat_history.append(("assistant", answer))
