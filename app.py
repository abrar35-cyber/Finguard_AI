import json
import re
import secrets
import time
from datetime import datetime
from html import escape as esc

import streamlit as st

# =========================================================
# IMPORTS (safe fallbacks so the app never crashes on import)
# =========================================================
try:
    from database import (
        init_db, get_bills, get_payments, add_bill, add_payment,
        register_user, get_user, update_user, export_user_data, delete_user_data,
    )
    DB_OK = True
except ImportError:
    DB_OK = False
    init_db = lambda: None
    get_bills = lambda user_email=None: []
    get_payments = lambda user_email=None: []
    add_bill = add_payment = register_user = get_user = None
    update_user = export_user_data = delete_user_data = None

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

if not DB_OK or not register_user or not update_user:
    st.error("database.py is missing or outdated. Please update it on GitHub.")
    st.stop()

if st.session_state.get("flash"):
    _msg, _icon = st.session_state.pop("flash")
    st.toast(_msg, icon=_icon)

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
button[kind="primary"],button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#10b981,#059669)!important;border:none!important;box-shadow:0 6px 16px rgba(16,185,129,.3)!important}
button[kind="primary"]:hover,button[kind="primaryFormSubmit"]:hover{color:#fff!important;filter:brightness(1.1)}
[data-testid="stExpander"]{background:rgba(255,255,255,.02)!important;border:1px solid var(--line)!important;border-radius:12px!important}
[data-testid="stChatMessage"]{background:var(--card2)!important;border:1px solid var(--line)!important;border-radius:14px!important}
[data-testid="stChatInput"]{background:#0b1220!important;border:1px solid var(--line)!important;border-radius:14px!important}
.auth-hero h1{font-size:44px;font-weight:800;letter-spacing:-1.5px;line-height:1.08;margin:18px 0 12px}
.auth-hero h1 span{background:linear-gradient(90deg,#34d399,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.auth-hero p{color:#b6c2d6;font-size:16px;max-width:460px}
.feat{display:flex;gap:12px;align-items:center;margin:14px 0;font-size:14.5px}
.feat i{font-style:normal;width:38px;height:38px;border-radius:11px;background:rgba(16,185,129,.14);display:flex;align-items:center;justify-content:center;font-size:18px}
.userchip{display:flex;align-items:center;gap:10px;justify-content:flex-end;font-size:12.5px;color:var(--mut)}
.userchip b{color:var(--txt)}
.avatar{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#38bdf8,#10b981);display:flex;align-items:center;justify-content:center;font-weight:800;color:#06210f}
.agent{display:flex;gap:14px;align-items:flex-start;background:linear-gradient(120deg,rgba(16,185,129,.16),rgba(56,189,248,.08));border:1px solid rgba(16,185,129,.35);border-radius:16px;padding:16px 18px;margin-bottom:12px}
.agent-av{width:44px;height:44px;border-radius:13px;background:linear-gradient(135deg,#10b981,#059669);display:flex;align-items:center;justify-content:center;font-size:22px;flex:none}
.agent-n{font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#34d399;margin-bottom:4px}
.agent-m{font-size:14.5px;line-height:1.55}
.receipt{border:1px solid rgba(16,185,129,.5);background:linear-gradient(120deg,rgba(16,185,129,.2),rgba(14,20,34,.8));border-radius:18px;padding:20px 24px;margin-bottom:18px}
.receipt h3{margin:0 0 8px;font-size:18px}
.receipt .row{display:flex;justify-content:space-between;font-size:13.5px;padding:5px 0;color:#cbd5e1}
.pipe{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:6px 0 4px}
@media(max-width:900px){.pipe{grid-template-columns:1fr}}
.node{background:rgba(255,255,255,.04);border:1px solid var(--line);border-radius:16px;padding:16px;text-align:center;transition:.25s;position:relative}
.node:hover{transform:translateY(-4px);border-color:rgba(16,185,129,.5)}
.node .ic{font-size:26px;margin-bottom:6px}
.node .nm{font-weight:700;font-size:13.5px}
.node .ds{font-size:11.5px;color:var(--mut);margin:4px 0 8px;min-height:32px}
.node .mt{font-size:20px;font-weight:800;color:#34d399}
.node .ml{font-size:10.5px;color:var(--mut)}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================
ICONS = {"electricity": "⚡", "gas": "🔥", "internet": "🌐", "water": "💧", "telecom": "📱"}
PALETTE = ["#10b981", "#38bdf8", "#f59e0b", "#a78bfa", "#f472b6", "#fb7185"]
WALLETS = ["JazzCash", "Easypaisa", "SadaPay", "NayaPay", "Bank account", "Other wallet"]
AVATAR_COLORS = {"Emerald": "#10b981", "Sky": "#38bdf8", "Amber": "#f59e0b", "Violet": "#a78bfa", "Rose": "#fb7185"}
OTP_SECONDS = 300


def flash(msg, icon="✅"):
    st.session_state["flash"] = (msg, icon)


def money(x):
    return f"PKR {float(x or 0):,.0f}"


def icon_for(b_type):
    return ICONS.get(str(b_type).lower(), "🧾")


def normalize_phone(raw):
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("92") and len(digits) == 12:
        digits = "0" + digits[2:]
    return digits if re.fullmatch(r"03\d{9}", digits) else ""


def normalize_account(raw):
    """Accept a mobile wallet number (03XXXXXXXXX), an IBAN (PK..), or an 8 to 20 digit account number."""
    phone = normalize_phone(raw)
    if phone:
        return phone
    cleaned = re.sub(r"[\s\-]", "", raw or "").upper()
    if re.fullmatch(r"PK\d{2}[A-Z0-9]{20}", cleaned):
        return cleaned
    if re.fullmatch(r"\d{8,20}", cleaned):
        return cleaned
    return ""


def mask_phone(num):
    num = str(num or "")
    return f"{num[:4]}****{num[-3:]}" if len(num) >= 8 else num


def valid_email(e):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", (e or "").strip()))


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
    return (
        f'<div class="bill-row"><div class="bill-ico">{icon_for(b_type)}</div>'
        f'<div class="bill-main"><div class="bill-name">{esc(str(prov or b_type))}</div>'
        f'<div class="bill-sub">Ref {esc(str(cons or "N/A"))} · Due {esc(str(due or "N/A"))}</div></div>'
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


# =========================================================
# AUTH (register / sign in)
# =========================================================
def auth_page():
    left, right = st.columns([1.15, 1], gap="large")

    with left:
        st.markdown(
            '<div class="auth-hero"><div class="brand"><div class="brand-logo">⚡</div><span class="brand-text">FinGuard AI</span></div>'
            '<h1>Never miss a <span>utility bill</span> again.</h1>'
            '<p>AI agents find your bills, explain them, warn you before the due date, and pay with one OTP from your own wallet.</p>'
            '<div class="feat"><i>📬</i><div><b>Finds bills for you</b><br><span class="muted">From your inbox or a photo</span></div></div>'
            '<div class="feat"><i>🔔</i><div><b>Warns you early</b><br><span class="muted">Overdue and due-soon alerts</span></div></div>'
            '<div class="feat"><i>🔐</i><div><b>Pays only with your OTP</b><br><span class="muted">Nothing moves without your approval</span></div></div></div>',
            unsafe_allow_html=True,
        )

    with right:
        with st.container(border=True):
            tab_reg, tab_in = st.tabs(["Create account", "Sign in"])

            with tab_reg:
                with st.form("register_form"):
                    name = st.text_input("Full name", placeholder="e.g. Ali Khan")
                    email = st.text_input("Email", placeholder="you@example.com")
                    wallet = st.selectbox("Your wallet", WALLETS)
                    number = st.text_input("Wallet number or account number", placeholder="03XX XXXXXXX")
                    go = st.form_submit_button("Create my account", type="primary", use_container_width=True)
                if go:
                    phone = normalize_account(number)
                    if not name.strip():
                        st.warning("Please enter your name.")
                    elif not valid_email(email):
                        st.warning("Please enter a valid email address.")
                    elif not phone:
                        st.warning("Enter a wallet number like 0300 1234567, or a bank account number or IBAN.")
                    elif get_user(email):
                        st.warning("This email already has an account. Please use the Sign in tab.")
                    else:
                        st.session_state["user"] = register_user(email, name.strip(), wallet, phone)
                        flash(f"Welcome, {name.strip()}!", "👋")
                        st.rerun()
                st.caption("Prototype: no real money moves. Please use a test number, not your real wallet.")

            with tab_in:
                with st.form("login_form"):
                    email_in = st.text_input("Email", placeholder="you@example.com", key="login_email")
                    go_in = st.form_submit_button("Sign in", type="primary", use_container_width=True)
                if go_in:
                    user = get_user(email_in) if valid_email(email_in) else None
                    if user:
                        st.session_state["user"] = user
                        flash(f"Welcome back, {user['name']}!", "👋")
                        st.rerun()
                    else:
                        st.warning("No account with this email. Please create one first.")
                st.caption("Prototype sign-in uses email only. Production would verify with an OTP.")


if "user" not in st.session_state:
    auth_page()
    st.stop()

user = st.session_state["user"]
email = user["email"]
first_name = user["name"].split()[0] if user["name"] else "there"
wallet_label = f'{user["wallet_provider"]} {mask_phone(user["wallet_number"])}'

# =========================================================
# DATA
# =========================================================
bills = get_bills(email)
payments = get_payments(email)

total_bills = len(bills)
pending_list = [b for b in bills if str(b[6]).lower() != "paid"]
pending_bills = len(pending_list)
total_amount = sum(float(b[4] or 0) for b in bills)
paid_amount = sum(float(p[2] or 0) for p in payments)
pending_amount = max(total_amount - paid_amount, 0.0)
pct_paid = min(paid_amount / total_amount * 100, 100) if total_amount > 0 else 0


def days_left(b):
    d = urgency(b[5])[2]
    return d if d is not None else 9999


urgent_count = len([b for b in pending_list if urgency(b[5])[1] in ("critical", "warning")]) if get_reminder_details else 0
ranked_pending = sorted(pending_list, key=days_left)
next_due_text = ""
if ranked_pending:
    nb = ranked_pending[0]
    next_due_text = f'{nb[2] or nb[1]}: {urgency(nb[5])[0]}'


def run_inbox():
    added = find_bills_from_inbox(email)
    flash(f"{added} new bill(s) added." if added else "No new bills found.", "📬")
    st.rerun()


# =========================================================
# PAYMENT AGENT (asks, then OTP, then pays)
# =========================================================
def payment_flow(b, ctx):
    b_id, b_type, prov, cons, amt, due, status, created = b
    msg, urg, _ = urgency(due)
    st.markdown(
        f'<div class="agent"><div class="agent-av">🤖</div><div>'
        f'<div class="agent-n">Payment Agent</div>'
        f'<div class="agent-m">Hi {esc(first_name)}, your <b>{esc(str(prov or b_type))}</b> bill of <b>{money(amt)}</b> '
        f'is waiting. <span class="badge b-{urg}">{esc(msg)}</span><br>'
        f'Shall I pay it from your <b>{esc(wallet_label)}</b>?</div></div></div>',
        unsafe_allow_html=True,
    )

    otp = st.session_state.get("otp")
    active = bool(otp) and otp["bill_id"] == b_id

    if not active:
        if st.button("📲 Get OTP", key=f"{ctx}_otp_{b_id}", type="primary", use_container_width=True):
            st.session_state["otp"] = {
                "bill_id": b_id,
                "code": str(secrets.randbelow(900000) + 100000),
                "exp": time.time() + OTP_SECONDS,
                "tries": 0,
            }
            st.rerun()
        return

    st.info(f"Demo mode: SMS is not connected, so your OTP is shown here: **{otp['code']}** (valid 5 minutes)")
    code_in = st.text_input("Enter the 6-digit OTP", max_chars=6, key=f"{ctx}_code_{b_id}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Confirm & pay", key=f"{ctx}_ok_{b_id}", type="primary", use_container_width=True):
            if time.time() > otp["exp"]:
                st.session_state.pop("otp", None)
                flash("OTP expired. Please request a new one.", "⏰")
                st.rerun()
            elif code_in.strip() == otp["code"]:
                ok = add_payment(bill_id=b_id, amount=float(amt or 0), method=user["wallet_provider"], user_email=email)
                st.session_state.pop("otp", None)
                if ok:
                    st.session_state["receipt"] = {
                        "provider": str(prov or b_type), "amount": float(amt or 0),
                        "wallet": wallet_label, "ref": f"FG-{b_id:05d}",
                        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                    }
                else:
                    flash("That bill is already paid.", "ℹ️")
                st.rerun()
            else:
                otp["tries"] += 1
                if otp["tries"] >= 3:
                    st.session_state.pop("otp", None)
                    flash("Too many wrong attempts. Please request a new OTP.", "⛔")
                    st.rerun()
                st.error(f"Wrong OTP. {3 - otp['tries']} attempt(s) left.")
    with c2:
        if st.button("Cancel", key=f"{ctx}_cancel_{b_id}", use_container_width=True):
            st.session_state.pop("otp", None)
            st.rerun()


# =========================================================
# HEADER
# =========================================================
h1, h2, h3 = st.columns([5, 3, 1])
with h1:
    st.markdown('<div class="brand"><div class="brand-logo">⚡</div><span class="brand-text">FinGuard AI</span></div>', unsafe_allow_html=True)
with h2:
    st.markdown(
        f'<div class="userchip"><div><b>{esc(user["name"])}</b><br>{esc(wallet_label)}</div>'
        f'<div class="avatar" style="background:{esc(user.get("avatar_color") or "#38bdf8")}">{esc(user["name"][:1].upper())}</div></div>',
        unsafe_allow_html=True,
    )
with h3:
    if st.button("Log out", key="logout_btn"):
        for k in ["user", "otp", "receipt", "chat_history", "pay_focus", "wallet_change"]:
            st.session_state.pop(k, None)
        st.rerun()

receipt = st.session_state.pop("receipt", None)
if receipt:
    st.balloons()
    st.markdown(
        f'<div class="receipt"><h3>✅ Payment successful</h3>'
        f'<div class="row"><span>Biller</span><b>{esc(receipt["provider"])}</b></div>'
        f'<div class="row"><span>Amount</span><b>{money(receipt["amount"])}</b></div>'
        f'<div class="row"><span>Paid from</span><b>{esc(receipt["wallet"])}</b></div>'
        f'<div class="row"><span>Reference</span><b>{receipt["ref"]}</b></div>'
        f'<div class="row"><span>Time</span><b>{receipt["time"]}</b></div>'
        f'<div class="muted" style="margin-top:8px">Demo receipt. No real money was moved.</div></div>',
        unsafe_allow_html=True,
    )

tab_overview, tab_scan, tab_bills, tab_agents, tab_chat, tab_settings = st.tabs(
    ["🏠 Home", "📸 Scan Bill", "💳 Bills", "🧠 AI Agents", "💬 Copilot", "⚙️ Settings"]
)

# ---------------------------------------------------------
# TAB 1: HOME
# ---------------------------------------------------------
with tab_overview:
    if bills:
        headline = f"{pending_bills} bill(s) waiting, {money(pending_amount)} to clear" if pending_bills else "All bills are cleared. Nice work!"
        chips = f'<span class="chip">📑 {total_bills} bills tracked</span><span class="chip">🔔 {urgent_count} need attention</span>'
        if next_due_text:
            chips += f'<span class="chip">⏰ Next: {esc(next_due_text)}</span>'
    else:
        headline = "Add your first bill and let the agents take over"
        chips = '<span class="chip">📸 Scan</span><span class="chip">🤖 Auto-extract</span><span class="chip">📲 Pay with OTP</span>'
    st.markdown(
        f'<div class="hero"><h1>Hello, {esc(first_name)} 👋</h1><p>{headline}</p><div class="chips">{chips}</div></div>',
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
        if pending_list:
            focus = st.session_state.get("pay_focus")
            focus_bill = next((b for b in pending_list if b[0] == focus), ranked_pending[0])
            with st.container(border=True):
                payment_flow(focus_bill, "home")

        with st.container(border=True):
            if bills:
                st.markdown('<div class="sec-t">Upcoming &amp; recent bills</div><div class="sec-s">Most urgent first</div>', unsafe_allow_html=True)
                order = sorted(bills, key=lambda b: 99999 if str(b[6]).lower() == "paid" else days_left(b))
                st.markdown("".join(bill_row(b) for b in order[:6]), unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="empty"><div class="big">🧾</div><h3>No bills yet</h3>'
                    '<div class="muted">Start in three quick steps</div>'
                    '<div class="steps"><div class="step">1 · Scan a bill</div><div class="step">2 · Review details</div><div class="step">3 · Pay with OTP</div></div></div>',
                    unsafe_allow_html=True,
                )
                if find_bills_from_inbox:
                    if st.button("✨ Load demo bills from inbox", type="primary", key="demo_btn", use_container_width=True):
                        run_inbox()
                else:
                    st.warning("Inbox agent not found. Update bill_finder_agent.py on GitHub.")

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
                    bill_type=bill_type, provider=provider, consumer_number=consumer_number,
                    amount=amount, due_date=due_date,
                    extracted_text=st.session_state.get("scan_text", ""), user_email=email,
                )
                for k in ["scan_text", "scan_provider", "scan_amount", "scan_consumer", "scan_due"]:
                    st.session_state.pop(k, None)
                flash(f"Bill #{new_id} saved.")
                st.rerun()
            else:
                st.warning("Please enter at least a provider and an amount above 0.")

# ---------------------------------------------------------
# TAB 3: BILLS
# ---------------------------------------------------------
with tab_bills:
    focus = st.session_state.get("pay_focus")
    focus_bill = next((b for b in pending_list if b[0] == focus), None)
    if focus_bill:
        with st.container(border=True):
            payment_flow(focus_bill, "bills")
            if st.button("Close", key="close_focus"):
                st.session_state.pop("pay_focus", None)
                st.session_state.pop("otp", None)
                st.rerun()

    with st.container(border=True):
        st.markdown('<div class="sec-t">Your bills</div><div class="sec-s">Tap Pay on any pending bill</div>', unsafe_allow_html=True)
        view = st.radio("Show", ["All", "Pending", "Paid"], horizontal=True, label_visibility="collapsed")
        shown = [b for b in bills if view == "All" or (view == "Paid") == (str(b[6]).lower() == "paid")]

        if shown:
            for b in shown:
                b_id, b_type, prov, cons, amt, due, status, created = b
                is_paid = str(status).lower() == "paid"
                r1, r2 = st.columns([6, 1.4])
                with r1:
                    st.markdown(bill_row(b), unsafe_allow_html=True)
                with r2:
                    if not is_paid:
                        if st.button("Pay", key=f"pay_{b_id}", type="primary", use_container_width=True):
                            st.session_state["pay_focus"] = b_id
                            st.session_state.pop("otp", None)
                            st.rerun()
        else:
            st.info("No bills here yet.")

# ---------------------------------------------------------
# TAB 4: AI AGENTS
# ---------------------------------------------------------
with tab_agents:
    with st.container(border=True):
        st.markdown('<div class="sec-t">Your AI agent team</div><div class="sec-s">Five agents work together. Payments always need your OTP.</div>', unsafe_allow_html=True)

        def node(ic, nm, ds, mt, ml):
            return f'<div class="node"><div class="ic">{ic}</div><div class="nm">{nm}</div><div class="ds">{ds}</div><div class="mt">{mt}</div><div class="ml">{ml}</div></div>'

        st.markdown(
            '<div class="pipe">'
            + node("📬", "Bill Finder", "Reads your inbox and bill photos", total_bills, "bills found")
            + node("🧠", "Intelligence", "Groq LLM extracts amount, due date, provider", total_bills, "bills understood")
            + node("🔔", "Reminder", "Ranks urgency and warns early", urgent_count, "need attention")
            + node("🤖", "Payment", "Asks you, then pays after OTP", pending_bills, "awaiting approval")
            + node("💬", "Copilot", "Answers questions about your bills", len(st.session_state.get("chat_history", [])) // 2, "questions answered")
            + "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Flow: Find, Understand, Warn, Ask for approval, Pay, Record.")

# ---------------------------------------------------------
# TAB 5: COPILOT
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
                f"User: {user['name']}\n"
                f"Reply language: {'Roman Urdu (Urdu written in English letters)' if user.get('language') == 'Roman Urdu' else 'English'}\n"
                f"User Database Context:\n{bill_ctx}\n\n"
                f"Recent conversation:\n{history_ctx or 'None'}\n\n"
                f"Question: {query}\nAnswer accurately, concisely, and professionally."
            )
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = ask_groq(prompt)
                st.markdown(answer)
            st.session_state.chat_history.append(("assistant", answer))

# ---------------------------------------------------------
# TAB 6: SETTINGS
# ---------------------------------------------------------
with tab_settings:
    st.markdown('<div class="sec-t">Settings</div><div class="sec-s">Manage your wallet, profile and privacy</div>', unsafe_allow_html=True)
    s_wallet, s_profile, s_privacy = st.tabs(["💳 Wallet", "🎨 Personalisation", "🔒 Privacy"])

    # ----- WALLET -----
    with s_wallet:
        with st.container(border=True):
            st.markdown('<div class="sec-t">Payment wallet</div><div class="sec-s">The Payment Agent pays from this wallet or account, only after you confirm with an OTP.</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="agent"><div class="agent-av">👛</div><div><div class="agent-n">Current wallet</div>'
                f'<div class="agent-m"><b>{esc(user["wallet_provider"])}</b><br>{esc(mask_phone(user["wallet_number"]))}</div></div></div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="sec-t" style="font-size:15px;margin-top:6px">Change wallet</div>', unsafe_allow_html=True)

            wc = st.session_state.get("wallet_change")
            if not wc:
                idx = WALLETS.index(user["wallet_provider"]) if user["wallet_provider"] in WALLETS else 0
                new_provider = st.selectbox("Wallet or bank", WALLETS, index=idx, key="wl_provider")
                new_number = st.text_input("Wallet number or account number", placeholder="03XX XXXXXXX or PK.. IBAN", key="wl_number")
                if st.button("📲 Get OTP to confirm change", key="wl_otp_btn", type="primary"):
                    acct = normalize_account(new_number)
                    if not acct:
                        st.warning("Enter a wallet number like 0300 1234567, or a bank account number or IBAN.")
                    else:
                        st.session_state["wallet_change"] = {
                            "provider": new_provider, "number": acct,
                            "code": str(secrets.randbelow(900000) + 100000),
                            "exp": time.time() + OTP_SECONDS, "tries": 0,
                        }
                        st.rerun()
            else:
                st.markdown(f'<div class="muted">Changing to <b>{esc(wc["provider"])}</b> {esc(mask_phone(wc["number"]))}</div>', unsafe_allow_html=True)
                st.info(f"Demo mode: SMS is not connected, so your OTP is shown here: **{wc['code']}** (valid 5 minutes)")
                code_in = st.text_input("Enter the 6-digit OTP", max_chars=6, key="wl_code")
                w1, w2 = st.columns(2)
                with w1:
                    if st.button("✅ Confirm change", key="wl_confirm", type="primary", use_container_width=True):
                        if time.time() > wc["exp"]:
                            st.session_state.pop("wallet_change", None)
                            flash("OTP expired. Please try again.", "⏰")
                            st.rerun()
                        elif code_in.strip() == wc["code"]:
                            update_user(email, wallet_provider=wc["provider"], wallet_number=wc["number"])
                            st.session_state["user"] = get_user(email)
                            st.session_state.pop("wallet_change", None)
                            flash("Wallet updated.", "👛")
                            st.rerun()
                        else:
                            wc["tries"] += 1
                            if wc["tries"] >= 3:
                                st.session_state.pop("wallet_change", None)
                                flash("Too many wrong attempts. Please start again.", "⛔")
                                st.rerun()
                            st.error(f"Wrong OTP. {3 - wc['tries']} attempt(s) left.")
                with w2:
                    if st.button("Cancel", key="wl_cancel", use_container_width=True):
                        st.session_state.pop("wallet_change", None)
                        st.rerun()
            st.caption("Prototype: no real money moves. Use a test number, not your real wallet.")

    # ----- PERSONALISATION -----
    with s_profile:
        with st.container(border=True):
            st.markdown('<div class="sec-t">Your profile</div><div class="sec-s">Make FinGuard feel like yours</div>', unsafe_allow_html=True)
            cur_color_name = next((n for n, c in AVATAR_COLORS.items() if c == user.get("avatar_color")), "Sky")
            with st.form("profile_form"):
                p_name = st.text_input("Full name", value=user["name"])
                st.text_input("Email (cannot be changed)", value=user["email"], disabled=True)
                p_color = st.selectbox("Avatar colour", list(AVATAR_COLORS), index=list(AVATAR_COLORS).index(cur_color_name))
                langs = ["English", "Roman Urdu"]
                p_lang = st.selectbox("Copilot language", langs, index=langs.index(user.get("language", "English")) if user.get("language", "English") in langs else 0)
                saved = st.form_submit_button("Save profile", type="primary", use_container_width=True)
            if saved:
                if not p_name.strip():
                    st.warning("Name cannot be empty.")
                else:
                    update_user(email, name=p_name.strip(), avatar_color=AVATAR_COLORS[p_color], language=p_lang)
                    st.session_state["user"] = get_user(email)
                    flash("Profile updated.", "🎨")
                    st.rerun()

    # ----- PRIVACY -----
    with s_privacy:
        with st.container(border=True):
            st.markdown('<div class="sec-t">Privacy policy</div><div class="sec-s">Prototype version 0.1, October 2026. This is a plain-language summary for a prototype, not legal advice.</div>', unsafe_allow_html=True)
            with st.expander("1. What we collect", expanded=True):
                st.markdown("Your name and email, the wallet or account number you enter, the bills you add or the inbox agent reads (provider, amount, due date, consumer number and extracted text), your payment records, and your Copilot questions during a session.")
            with st.expander("2. How we use it"):
                st.markdown("To show your bills and reminders, to prepare payments for your approval, and to answer your questions about your bills.")
            with st.expander("3. AI processing"):
                st.markdown("Bill text and your Copilot questions are sent to the Groq API so the AI can extract bill details and write answers. Please do not add information you would not want processed by an AI service.")
            with st.expander("4. Payments"):
                st.markdown("This is a prototype. **No real money is moved.** OTP codes are shown on screen because no SMS or email gateway is connected.")
            with st.expander("5. Storage and retention"):
                st.markdown("Data is kept in the app's database on the hosting platform and may be erased whenever the app restarts. Your wallet number is shown masked inside the app.")
            with st.expander("6. Your controls"):
                st.markdown("You can change your wallet and profile in Settings, download a copy of your data, or permanently delete your account and everything linked to it.")
            with st.expander("7. Before a real launch"):
                st.markdown("A production version would add real OTP verification at sign-in, encryption of stored data, explicit consent screens, a security review, and legal review against applicable Pakistani regulations.")

        with st.container(border=True):
            st.markdown('<div class="sec-t">Your data</div><div class="sec-s">Download a copy or delete everything</div>', unsafe_allow_html=True)
            st.download_button(
                "⬇️ Download my data (JSON)",
                data=json.dumps(export_user_data(email), indent=2, default=str),
                file_name="finguard_my_data.json",
                mime="application/json",
                key="dl_data",
            )
            st.divider()
            sure = st.checkbox("I understand this permanently deletes my account, bills and payment history.", key="del_sure")
            if st.button("🗑️ Delete my account", key="del_btn", disabled=not sure):
                delete_user_data(email)
                for k in ["user", "otp", "receipt", "chat_history", "pay_focus", "wallet_change"]:
                    st.session_state.pop(k, None)
                flash("Your account and data were deleted.", "🗑️")
                st.rerun()
