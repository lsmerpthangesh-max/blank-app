import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os
import io

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lingam Super Market – Asset Management",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap');

:root {
  --green-dark:   #004d26;
  --green-mid:    #006d33;
  --green-bright: #00a650;
  --yellow:       #FFD700;
  --yellow-light: #FFF176;
  --bg-main:      #f0f7f2;
  --bg-card:      #ffffff;
  --text-main:    #0d2b1a;
  --text-muted:   #4a7c5b;
  --danger:       #c0392b;
  --danger-light: #fdecea;
  --radius:       12px;
  --shadow:       0 4px 18px rgba(0,77,38,.12);
}

html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.main { background: var(--bg-main); }
h1,h2,h3,h4,h5,h6 { font-family:'Rajdhani',sans-serif; color: var(--green-dark) !important; }

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--green-dark) 0%, #002a15 100%);
  border-right: 3px solid var(--yellow);
}
[data-testid="stSidebar"] * { color: #e8f5ec !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: var(--green-mid) !important;
  border: 1px solid var(--yellow) !important;
  color: var(--yellow) !important;
}

[data-testid="stMetric"] {
  background: var(--bg-card);
  border-left: 5px solid var(--green-bright);
  border-radius: var(--radius);
  padding: 14px 18px !important;
  box-shadow: var(--shadow);
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size:.8rem; }
[data-testid="stMetricValue"] { color: var(--green-dark) !important; font-family:'Rajdhani',sans-serif; font-size:2rem; }

.stButton > button {
  background: linear-gradient(135deg, var(--green-mid), var(--green-bright));
  color: #fff !important;
  border: none;
  border-radius: var(--radius);
  font-weight: 600;
  padding: 0.5rem 1.4rem;
  transition: transform .15s, box-shadow .15s;
}
.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,166,80,.35);
}

.section-header {
  background: linear-gradient(90deg, var(--green-dark), var(--green-mid));
  color: var(--yellow) !important;
  padding: 10px 20px;
  border-radius: var(--radius);
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: .05em;
  margin-bottom: 14px;
}

.tip-box {
  background: linear-gradient(135deg,#fffde7,#f0f7f2);
  border-left: 5px solid var(--yellow);
  border-radius: var(--radius);
  padding: 12px 18px;
  margin: 8px 0 16px 0;
  font-size:.88rem;
  color: var(--text-main);
}
.tip-box strong { color: var(--green-dark); }

.top-banner {
  background: linear-gradient(100deg, var(--green-dark) 60%, var(--yellow) 140%);
  border-radius: var(--radius);
  padding: 18px 28px;
  margin-bottom: 22px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.top-banner h1 {
  color: var(--yellow) !important;
  font-family:'Rajdhani',sans-serif;
  font-size: 1.8rem;
  margin:0;
}
.top-banner p { color: #c8f0d8 !important; margin:0; font-size:.9rem; }

.stTextInput input, .stNumberInput input,
.stDateInput input, .stTextArea textarea {
  border: 1.5px solid #b2d8bf !important;
  border-radius: 8px !important;
  background: #f6fbf8 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────
DB = "lsm_assets.db"

def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS categories (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS employees (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'Staff'
    );
    CREATE TABLE IF NOT EXISTS assets (
        asset_id        TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        category        TEXT,
        location        TEXT,
        employee        TEXT,
        quantity        INTEGER DEFAULT 1,
        allocation_date TEXT,
        purchase_date   TEXT,
        cost            REAL DEFAULT 0,
        status          TEXT DEFAULT 'Active',
        notes           TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS maintenance (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT,
        date     TEXT,
        details  TEXT,
        cost     REAL DEFAULT 0,
        vendor   TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS audits (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id   TEXT,
        month      TEXT,
        year       TEXT,
        status     TEXT DEFAULT 'Pending',
        checked_by TEXT DEFAULT '',
        remarks    TEXT DEFAULT '',
        audit_date TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS audit_checkers (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def run_query(q, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(q, params)
    conn.commit()
    conn.close()

def fetch_df(q, params=()):
    conn = get_conn()
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df

def fetch_one(q, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(q, params)
    row = c.fetchone()
    conn.close()
    return row

def generate_asset_id():
    row = fetch_one("SELECT MAX(CAST(SUBSTR(asset_id,4) AS INTEGER)) FROM assets")
    n = (row[0] or 0) + 1
    return f"LSM{str(n).zfill(3)}"

def tip(text):
    st.markdown(f'<div class="tip-box">💡 <strong>Tip:</strong> {text}</div>', unsafe_allow_html=True)

def section(text):
    st.markdown(f'<div class="section-header">▸ {text}</div>', unsafe_allow_html=True)

def merged_excel_bytes():
    assets = fetch_df("SELECT * FROM assets")
    maint  = fetch_df("SELECT asset_id, date, details, cost, vendor FROM maintenance")
    audits = fetch_df("SELECT asset_id, month, year, status, checked_by, remarks, audit_date FROM audits")

    if not maint.empty:
        maint_agg = maint.groupby("asset_id").agg(
            maintenance_count  = ("date", "count"),
            last_maintenance   = ("date", "max"),
            total_maint_cost   = ("cost", "sum"),
            last_maint_details = ("details", "last"),
            last_vendor        = ("vendor", "last")
        ).reset_index()
    else:
        maint_agg = pd.DataFrame(columns=[
            "asset_id","maintenance_count","last_maintenance",
            "total_maint_cost","last_maint_details","last_vendor"
        ])

    if not audits.empty:
        audit_agg = audits.groupby("asset_id").agg(
            audit_count  = ("month", "count"),
            last_audit   = ("audit_date", "max"),
            last_status  = ("status", "last"),
            last_checker = ("checked_by", "last"),
            last_remarks = ("remarks", "last")
        ).reset_index()
    else:
        audit_agg = pd.DataFrame(columns=[
            "asset_id","audit_count","last_audit",
            "last_status","last_checker","last_remarks"
        ])

    merged = assets.merge(maint_agg, on="asset_id", how="left") \
                   .merge(audit_agg,  on="asset_id", how="left")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        wb = writer.book

        hdr_fmt = wb.add_format({
            'bold': True, 'bg_color': '#004d26', 'font_color': '#FFD700',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11
        })
        cell_fmt = wb.add_format({'border': 1, 'valign': 'vcenter', 'font_size': 10})
        alt_fmt  = wb.add_format({
            'border': 1, 'valign': 'vcenter', 'font_size': 10, 'bg_color': '#f0f7f2'
        })
        money_fmt = wb.add_format({
            'border': 1, 'valign': 'vcenter', 'num_format': '0.00', 'font_size': 10
        })
        title_fmt = wb.add_format({
            'bold': True, 'font_size': 14, 'font_color': '#004d26', 'valign': 'vcenter'
        })

        # Sheet 1 - Asset Master (merged)
        ws = wb.add_worksheet("Asset Master")
        writer.sheets["Asset Master"] = ws

        cols = list(merged.columns)
        title_text = (
            "Lingam Super Market — Asset Master Report  |  Generated: "
            + datetime.now().strftime("%d %b %Y %H:%M")
        )
        ws.set_row(0, 32)
        ws.merge_range(0, 0, 0, max(len(cols) - 1, 0), title_text, title_fmt)
        ws.set_row(1, 22)
        for ci, col in enumerate(cols):
            ws.write(1, ci, col.replace("_", " ").title(), hdr_fmt)

        col_widths = {ci: max(len(str(col)), 10) for ci, col in enumerate(cols)}
        for ri, row in merged.iterrows():
            fmt = alt_fmt if ri % 2 else cell_fmt
            for ci, col in enumerate(cols):
                val = row[col]
                if pd.isna(val):
                    val = ""
                if "cost" in col.lower() and val != "":
                    try:
                        ws.write(ri + 2, ci, float(val), money_fmt)
                    except (ValueError, TypeError):
                        ws.write(ri + 2, ci, val, fmt)
                else:
                    ws.write(ri + 2, ci, val, fmt)
                col_widths[ci] = max(col_widths[ci], len(str(val)))
        for ci, w in col_widths.items():
            ws.set_column(ci, ci, min(w + 2, 32))
        ws.freeze_panes(2, 1)

        # Raw sheets helper
        def raw_sheet(sheet_name, df):
            ws2 = wb.add_worksheet(sheet_name)
            writer.sheets[sheet_name] = ws2
            if df.empty:
                ws2.write(0, 0, "No data available.", title_fmt)
                return
            ws2.set_row(0, 28)
            ws2.merge_range(
                0, 0, 0, max(len(df.columns) - 1, 0),
                f"{sheet_name} — {len(df)} records", title_fmt
            )
            ws2.set_row(1, 20)
            for ci, col in enumerate(df.columns):
                ws2.write(1, ci, col.replace("_", " ").title(), hdr_fmt)
                ws2.set_column(ci, ci, max(len(col) + 4, 14))
            for ri, row in df.iterrows():
                fmt = alt_fmt if ri % 2 else cell_fmt
                for ci, col in enumerate(df.columns):
                    val = row[col]
                    if pd.isna(val):
                        val = ""
                    ws2.write(ri + 2, ci, val, fmt)
            ws2.freeze_panes(2, 0)

        raw_sheet("Assets Raw",      assets)
        raw_sheet("Maintenance Raw", maint)
        raw_sheet("Audits Raw",      audits)

    buf.seek(0)
    return buf.read()

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN / LOGOUT
# ─────────────────────────────────────────────────────────────────────────────
USERS = {
    "admin":   {"password": "admin123", "role": "Admin"},
    "manager": {"password": "mgr456",   "role": "Manager"},
    "staff":   {"password": "staff789", "role": "Staff"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.role = ""

def do_logout():
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("""
        <div style='text-align:center; padding:32px 0 20px;'>
            <span style='font-size:3.5rem;'>🏪</span>
            <h2 style='color:#004d26 !important; font-family:Rajdhani,sans-serif;
                       font-size:1.8rem; margin:10px 0 4px;'>
                Lingam Super Market
            </h2>
            <p style='color:#4a7c5b; font-size:.9rem; margin:0;'>
                Asset Management System — Please login
            </p>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("👤 Username", placeholder="admin / manager / staff")
        password = st.text_input("🔒 Password", type="password")

        if st.button("🔐 Login", use_container_width=True):
            u = username.strip().lower()
            if u in USERS and USERS[u]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.session_state.role = USERS[u]["role"]
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

        st.markdown("""
        <div class='tip-box' style='margin-top:16px;'>
            <strong>Demo accounts:</strong><br>
            admin / admin123 &nbsp;|&nbsp; manager / mgr456 &nbsp;|&nbsp; staff / staff789
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
ROLE = st.session_state.role

with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding:14px 0 18px;
                border-bottom:1px solid #1a5c35; margin-bottom:12px;'>
        <div style='font-size:2.2rem;'>🏪</div>
        <div style='font-size:1.1rem; font-family:Rajdhani,sans-serif;
                    color:#FFD700 !important; font-weight:700;'>
            Lingam Super Market
        </div>
        <div style='font-size:.75rem; color:#a8d5b5 !important; margin-top:4px;'>
            Logged in as
            <b style='color:#FFD700 !important;'>{st.session_state.user}</b>
            &nbsp;({ROLE})
        </div>
    </div>
    """, unsafe_allow_html=True)

    all_menus = [
        "📊 Dashboard",
        "📦 Assets",
        "🏷️ Categories",
        "👤 Employees",
        "🔧 Maintenance",
        "✅ Audit",
    ]
    if ROLE == "Admin":
        all_menus += ["⚙️ Admin Panel", "📥 Download Report"]

    menu = st.selectbox("Navigation", all_menus, label_visibility="collapsed")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    if st.button("🚪 Logout", use_container_width=True):
        do_logout()
        st.rerun()

    st.markdown("<hr style='border-color:#1a5c35;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:.73rem; color:#7ab891 !important; padding:4px 0;'>
        <b style='color:#FFD700 !important;'>Quick Tips</b><br>
        • Dashboard = live KPI overview<br>
        • Add checkers in Admin Panel<br>
        • Download merged report monthly<br>
        • Maintenance cost tracked per asset<br>
        • Edit assets anytime in Assets tab
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TOP BANNER
# ─────────────────────────────────────────────────────────────────────────────
PAGE_META = {
    "📊 Dashboard":      ("📊 Dashboard",        "Live overview of all assets & KPIs"),
    "📦 Assets":         ("📦 Asset Register",    "Add, view, edit and delete assets"),
    "🏷️ Categories":     ("🏷️ Categories",        "Manage asset categories"),
    "👤 Employees":      ("👤 Employees",         "Staff & responsible persons"),
    "🔧 Maintenance":    ("🔧 Maintenance Log",   "Track repairs and service history"),
    "✅ Audit":          ("✅ Audit Tracker",     "Monthly audit with checker assignment"),
    "⚙️ Admin Panel":   ("⚙️ Admin Panel",       "Manage users, checkers & settings"),
    "📥 Download Report":("📥 Download Report",  "Export merged Excel report"),
}
page_title, page_sub = PAGE_META.get(menu, (menu, ""))
st.markdown(f"""
<div class='top-banner'>
    <div>
        <h1>{page_title}</h1>
        <p>{page_sub}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if menu == "📊 Dashboard":
    assets = fetch_df("SELECT * FROM assets")
    maint  = fetch_df("SELECT * FROM maintenance")
    audits = fetch_df("SELECT * FROM audits")

    total      = len(assets)
    active     = len(assets[assets["status"] == "Active"])      if not assets.empty else 0
    damaged    = len(assets[assets["status"] == "Damaged"])     if not assets.empty else 0
    in_repair  = len(assets[assets["status"] == "In Repair"])   if not assets.empty else 0
    disposed   = len(assets[assets["status"] == "Disposed"])    if not assets.empty else 0
    total_cost = assets["cost"].sum()                            if not assets.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📦 Total Assets",  total)
    c2.metric("✅ Active",         active)
    c3.metric("❌ Damaged",        damaged)
    c4.metric("🔧 In Repair",      in_repair)
    c5.metric("🗑️ Disposed",      disposed)
    c6.metric("💰 Total Cost (₹)", f"{total_cost:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1.4, 1])

    with col_l:
        section("Asset Register")
        if not assets.empty:
            st.dataframe(
                assets[[
                    "asset_id","name","category","location",
                    "employee","quantity","cost","status","purchase_date"
                ]],
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No assets added yet.")

    with col_r:
        section("Recent Maintenance")
        if not maint.empty:
            st.dataframe(
                maint.tail(8)[["asset_id","date","details","cost"]],
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No maintenance records.")

        st.markdown("<br>", unsafe_allow_html=True)
        section("Audit Summary")
        if not audits.empty:
            summ = audits.groupby("status").size().reset_index(name="count")
            st.dataframe(summ, use_container_width=True, hide_index=True)
        else:
            st.info("No audits yet.")

    if datetime.now().day >= 25:
        st.warning("⚠️ Month-end approaching — ensure all audits are completed!")

    tip("Use the Asset Register page for full CRUD. Download merged report from Admin menu.")

    section("Filter Assets by Purchase Date")
    d1, d2 = st.columns(2)
    f_start = d1.date_input("From", value=date(2020, 1, 1))
    f_end   = d2.date_input("To",   value=date.today())
    if not assets.empty:
        assets["purchase_date"] = pd.to_datetime(assets["purchase_date"], errors="coerce")
        filtered = assets[
            (assets["purchase_date"] >= pd.to_datetime(f_start)) &
            (assets["purchase_date"] <= pd.to_datetime(f_end))
        ]
        st.dataframe(filtered, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# ASSETS
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📦 Assets":
    tab_add, tab_view, tab_edit = st.tabs(["➕ Add Asset", "📋 View & Delete", "✏️ Edit Asset"])

    # ADD
    with tab_add:
        tip("Asset ID is auto-generated (LSM001, LSM002 …). Cost can be 0 for donated items.")
        cats = fetch_df("SELECT name FROM categories")["name"].tolist()
        emps = fetch_df("SELECT name FROM employees")["name"].tolist()

        if not cats:
            st.warning("⚠️ Add at least one Category first.")
        if not emps:
            st.warning("⚠️ Add at least one Employee first.")

        c1, c2 = st.columns(2)
        with c1:
            a_name     = st.text_input("Asset Name *")
            a_category = st.selectbox("Category *", ["— select —"] + cats)
            a_location = st.text_input("Location / Department")
            a_employee = st.selectbox("Assigned To *", ["— select —"] + emps)
        with c2:
            a_qty      = st.number_input("Quantity", min_value=1, value=1)
            a_purchase = st.date_input("Purchase Date", value=date.today())
            a_cost     = st.number_input("Cost (₹)", min_value=0.0, step=100.0)
            a_status   = st.selectbox("Status", ["Active","Damaged","In Repair","Disposed"])
        a_notes = st.text_area("Notes / Remarks", height=80)

        if st.button("✅ Add Asset", use_container_width=True):
            if not a_name or a_category == "— select —" or a_employee == "— select —":
                st.error("Fill all required (*) fields.")
            else:
                aid = generate_asset_id()
                run_query(
                    "INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        aid, a_name, a_category, a_location, a_employee,
                        a_qty, str(datetime.now()), str(a_purchase),
                        a_cost, a_status, a_notes
                    )
                )
                st.success(f"✅ Asset **{aid}** — *{a_name}* added!")
                st.balloons()

    # VIEW & DELETE
    with tab_view:
        tip("Use filters to narrow down. Deleting an asset also removes its maintenance & audit records.")
        assets = fetch_df("SELECT * FROM assets")

        if assets.empty:
            st.info("No assets in the register yet.")
        else:
            cf1, cf2, cf3 = st.columns(3)
            cat_opts  = ["All"] + sorted(assets["category"].dropna().unique().tolist())
            stat_opts = ["All"] + sorted(assets["status"].dropna().unique().tolist())
            f_cat  = cf1.selectbox("Category", cat_opts)
            f_stat = cf2.selectbox("Status",   stat_opts)
            f_srch = cf3.text_input("Search Name / ID")

            view = assets.copy()
            if f_cat  != "All": view = view[view["category"] == f_cat]
            if f_stat != "All": view = view[view["status"]   == f_stat]
            if f_srch:
                view = view[
                    view["name"].str.contains(f_srch, case=False, na=False) |
                    view["asset_id"].str.contains(f_srch, case=False, na=False)
                ]

            st.info(f"Showing **{len(view)}** of **{len(assets)}** assets")
            st.dataframe(view, use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            section("Delete Asset")
            if ROLE not in ["Admin","Manager"]:
                st.warning("Only Admin or Manager can delete assets.")
            else:
                del_id = st.selectbox(
                    "Select Asset ID to Delete",
                    ["— select —"] + assets["asset_id"].tolist()
                )
                if del_id != "— select —":
                    r = assets[assets["asset_id"] == del_id].iloc[0]
                    st.markdown(f"""
                    <div style='background:#fff3cd; border-left:4px solid #ffc107;
                                padding:10px 16px; border-radius:8px; font-size:.9rem;'>
                        ⚠️ Deleting <b>{del_id}</b> — <b>{r['name']}</b>
                        ({r['category']}) · Status: {r['status']}
                    </div>""", unsafe_allow_html=True)
                    if st.button("🗑️ Confirm Delete Asset"):
                        run_query("DELETE FROM assets       WHERE asset_id=?", (del_id,))
                        run_query("DELETE FROM maintenance  WHERE asset_id=?", (del_id,))
                        run_query("DELETE FROM audits       WHERE asset_id=?", (del_id,))
                        st.success(f"Deleted {del_id} and all linked records.")
                        st.rerun()

    # EDIT
    with tab_edit:
        tip("Select an Asset ID to load its current data, update any field, then save.")
        assets = fetch_df("SELECT * FROM assets")
        if assets.empty:
            st.info("No assets to edit.")
        else:
            edit_id = st.selectbox(
                "Asset ID to Edit",
                ["— select —"] + assets["asset_id"].tolist(),
                key="edit_sel"
            )
            if edit_id != "— select —":
                r    = assets[assets["asset_id"] == edit_id].iloc[0]
                cats = fetch_df("SELECT name FROM categories")["name"].tolist()
                emps = fetch_df("SELECT name FROM employees")["name"].tolist()

                c1, c2 = st.columns(2)
                with c1:
                    e_name = st.text_input("Asset Name",  value=r["name"])
                    e_cat  = st.selectbox(
                        "Category", cats,
                        index=cats.index(r["category"]) if r["category"] in cats else 0
                    )
                    e_loc  = st.text_input("Location", value=r["location"] or "")
                    e_emp  = st.selectbox(
                        "Employee", emps,
                        index=emps.index(r["employee"]) if r["employee"] in emps else 0
                    )
                with c2:
                    e_qty  = st.number_input("Quantity", min_value=1, value=int(r["quantity"]))
                    e_cost = st.number_input("Cost (₹)", min_value=0.0, value=float(r["cost"]))
                    s_opts = ["Active","Damaged","In Repair","Disposed"]
                    e_stat = st.selectbox(
                        "Status", s_opts,
                        index=s_opts.index(r["status"]) if r["status"] in s_opts else 0
                    )
                e_notes = st.text_area("Notes", value=r["notes"] or "")

                if st.button("💾 Save Changes", use_container_width=True):
                    run_query(
                        """UPDATE assets SET name=?,category=?,location=?,employee=?,
                           quantity=?,cost=?,status=?,notes=? WHERE asset_id=?""",
                        (e_name, e_cat, e_loc, e_emp, e_qty, e_cost, e_stat, e_notes, edit_id)
                    )
                    st.success(f"Asset {edit_id} updated!")
                    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🏷️ Categories":
    tip("Keep category names short and specific, e.g. 'IT Equipment', 'Furniture', 'Vehicles'.")
    tab_add, tab_view = st.tabs(["➕ Add", "📋 View & Delete"])

    with tab_add:
        c_name = st.text_input("Category Name *")
        if st.button("✅ Add Category"):
            if c_name.strip():
                run_query("INSERT OR IGNORE INTO categories (name) VALUES (?)", (c_name.strip(),))
                st.success(f"Category '{c_name}' added.")
            else:
                st.error("Enter a name.")

    with tab_view:
        df = fetch_df("SELECT * FROM categories ORDER BY name")
        if df.empty:
            st.info("No categories yet.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            if ROLE in ["Admin","Manager"]:
                del_cat = st.selectbox("Delete Category", ["— select —"] + df["name"].tolist())
                if del_cat != "— select —":
                    if st.button("🗑️ Delete Category"):
                        run_query("DELETE FROM categories WHERE name=?", (del_cat,))
                        st.success(f"Deleted '{del_cat}'.")
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEES
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "👤 Employees":
    tip("Assign each asset to an employee for accountability. Update assignment via Edit Asset.")
    tab_add, tab_view = st.tabs(["➕ Add", "📋 View & Delete"])

    with tab_add:
        e_name = st.text_input("Employee Name *")
        e_role = st.selectbox("Role", ["Staff","Supervisor","Manager","Admin"])
        if st.button("✅ Add Employee"):
            if e_name.strip():
                run_query("INSERT INTO employees (name, role) VALUES (?,?)", (e_name.strip(), e_role))
                st.success(f"Employee '{e_name}' added.")
            else:
                st.error("Enter a name.")

    with tab_view:
        df = fetch_df("SELECT * FROM employees ORDER BY name")
        if df.empty:
            st.info("No employees yet.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            if ROLE in ["Admin","Manager"]:
                del_emp = st.selectbox(
                    "Delete Employee",
                    ["— select —"] + df["name"].tolist(),
                    key="del_emp"
                )
                if del_emp != "— select —":
                    if st.button("🗑️ Delete Employee"):
                        run_query("DELETE FROM employees WHERE name=?", (del_emp,))
                        st.success(f"Deleted '{del_emp}'.")
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# MAINTENANCE
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🔧 Maintenance":
    tip("Always log vendor/technician name for warranty tracking and repeat-vendor analysis.")
    tab_add, tab_view = st.tabs(["➕ Log Maintenance", "📋 View & Delete"])

    with tab_add:
        ids = fetch_df("SELECT asset_id, name FROM assets")
        if ids.empty:
            st.warning("No assets available. Add assets first.")
        else:
            id_opts = [f"{r['asset_id']} – {r['name']}" for _, r in ids.iterrows()]
            sel     = st.selectbox("Asset *", ["— select —"] + id_opts)
            c1, c2  = st.columns(2)
            m_details = c1.text_area("Maintenance Details *", height=120)
            m_cost    = c1.number_input("Cost (₹)", min_value=0.0, step=50.0)
            m_vendor  = c2.text_input("Vendor / Technician")
            m_date    = c2.date_input("Service Date", value=date.today())

            if st.button("✅ Save Maintenance Record"):
                if sel == "— select —" or not m_details.strip():
                    st.error("Select an asset and enter details.")
                else:
                    aid = sel.split(" – ")[0]
                    run_query(
                        "INSERT INTO maintenance (asset_id,date,details,cost,vendor) VALUES (?,?,?,?,?)",
                        (aid, str(m_date), m_details.strip(), m_cost, m_vendor)
                    )
                    if m_cost > 0:
                        run_query(
                            "UPDATE assets SET status='In Repair' WHERE asset_id=? AND status='Active'",
                            (aid,)
                        )
                    st.success("Maintenance record saved!")

    with tab_view:
        df = fetch_df("""
            SELECT m.id, m.asset_id, a.name AS asset_name,
                   m.date, m.details, m.cost, m.vendor
            FROM maintenance m
            LEFT JOIN assets a ON m.asset_id = a.asset_id
            ORDER BY m.date DESC
        """)
        if df.empty:
            st.info("No maintenance records yet.")
        else:
            f_aid = st.text_input("Filter by Asset ID")
            view  = df[df["asset_id"].str.contains(f_aid, case=False)] if f_aid else df
            st.dataframe(view, use_container_width=True, hide_index=True)
            st.markdown(f"**Total Maintenance Cost: ₹{df['cost'].sum():,.2f}**")

            if ROLE in ["Admin","Manager"]:
                section("Delete Maintenance Record")
                del_mid = st.selectbox(
                    "Record ID",
                    ["— select —"] + df["id"].astype(str).tolist()
                )
                if del_mid != "— select —":
                    if st.button("🗑️ Delete Record"):
                        run_query("DELETE FROM maintenance WHERE id=?", (int(del_mid),))
                        st.success("Record deleted.")
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "✅ Audit":
    tip("Assign a checker for every audit entry. Checkers are managed in the Admin Panel.")
    MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    checkers = fetch_df("SELECT name FROM audit_checkers")["name"].tolist()
    assets   = fetch_df("SELECT asset_id, name FROM assets")

    tab_add, tab_view = st.tabs(["➕ Add Audit Entry", "📋 View & Delete"])

    with tab_add:
        if assets.empty:
            st.warning("No assets to audit. Add assets first.")
        else:
            id_opts   = [f"{r['asset_id']} – {r['name']}" for _, r in assets.iterrows()]
            a_sel     = st.selectbox("Asset *", ["— select —"] + id_opts)
            c1, c2    = st.columns(2)
            a_month   = c1.selectbox("Month *", MONTHS, index=datetime.now().month - 1)
            a_year    = c2.text_input("Year *", value=str(datetime.now().year))
            a_status  = c1.selectbox(
                "Audit Status *",
                ["Pending","Verified OK","Missing","Damaged","Discrepancy"]
            )
            checker_opts = ["— select —"] + checkers if checkers else ["— No checkers yet —"]
            a_checker = c2.selectbox("Checked By *", checker_opts)
            a_remarks = st.text_area("Remarks / Notes", height=80)
            a_date    = st.date_input("Audit Date", value=date.today())

            if st.button("✅ Save Audit Entry", use_container_width=True):
                invalid_checker = a_checker in ["— select —","— No checkers yet —"]
                if a_sel == "— select —" or invalid_checker:
                    st.error("Select a valid asset and checker. Add checkers in Admin Panel.")
                else:
                    aid = a_sel.split(" – ")[0]
                    run_query(
                        """INSERT INTO audits
                           (asset_id,month,year,status,checked_by,remarks,audit_date)
                           VALUES (?,?,?,?,?,?,?)""",
                        (aid, a_month, a_year, a_status, a_checker, a_remarks, str(a_date))
                    )
                    st.success(f"Audit entry saved for {aid}.")

        if not checkers:
            st.warning("⚠️ No audit checkers configured. Go to **Admin Panel** to add them.")

    with tab_view:
        df = fetch_df("""
            SELECT au.id, au.asset_id, a.name AS asset_name,
                   au.month, au.year, au.status,
                   au.checked_by, au.remarks, au.audit_date
            FROM audits au
            LEFT JOIN assets a ON au.asset_id = a.asset_id
            ORDER BY au.audit_date DESC, au.id DESC
        """)
        if df.empty:
            st.info("No audit entries yet.")
        else:
            cf1, cf2 = st.columns(2)
            f_month  = cf1.selectbox("Filter Month",  ["All"] + MONTHS)
            f_status = cf2.selectbox(
                "Filter Status",
                ["All","Pending","Verified OK","Missing","Damaged","Discrepancy"]
            )
            view = df.copy()
            if f_month  != "All": view = view[view["month"]  == f_month]
            if f_status != "All": view = view[view["status"] == f_status]
            st.dataframe(view, use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            summ = df.groupby("status").size().reset_index(name="count")
            st.dataframe(summ, use_container_width=True, hide_index=True)

            if ROLE in ["Admin","Manager"]:
                section("Delete Audit Entry")
                del_aid = st.selectbox(
                    "Audit Record ID",
                    ["— select —"] + df["id"].astype(str).tolist()
                )
                if del_aid != "— select —":
                    if st.button("🗑️ Delete Audit Entry"):
                        run_query("DELETE FROM audits WHERE id=?", (int(del_aid),))
                        st.success("Audit entry deleted.")
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "⚙️ Admin Panel":
    if ROLE != "Admin":
        st.error("🔒 Admin access only.")
        st.stop()

    tip("Add checkers here so they appear in the Audit dropdown. Each checker is a verified staff member.")
    tab_chk, tab_tips = st.tabs(["👷 Audit Checkers", "📌 Best Practices"])

    with tab_chk:
        section("Add Audit Checker")
        chk_name = st.text_input("Checker Full Name *")
        if st.button("✅ Add Checker"):
            if chk_name.strip():
                run_query("INSERT OR IGNORE INTO audit_checkers (name) VALUES (?)", (chk_name.strip(),))
                st.success(f"Checker '{chk_name}' added.")
            else:
                st.error("Enter a name.")

        section("Current Checkers")
        df = fetch_df("SELECT * FROM audit_checkers ORDER BY name")
        if df.empty:
            st.info("No checkers configured yet.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            del_c = st.selectbox("Remove Checker", ["— select —"] + df["name"].tolist())
            if del_c != "— select —":
                if st.button("🗑️ Remove Checker"):
                    run_query("DELETE FROM audit_checkers WHERE name=?", (del_c,))
                    st.success(f"Removed '{del_c}'.")
                    st.rerun()

    with tab_tips:
        st.markdown("""
        <div class='tip-box'>
        <b>🏪 10 Best Practices — Lingam Super Market Asset Management</b><br><br>
        <b>1. Monthly Audits</b> — Run audits before the 25th. Missing audits = compliance risk.<br><br>
        <b>2. Cost Tracking</b> — Enter purchase &amp; maintenance costs accurately for real ROI reports.<br><br>
        <b>3. Checker Accountability</b> — Rotate checkers quarterly to avoid audit collusion.<br><br>
        <b>4. Status Discipline</b> — Update status immediately after inspection:
        Active → Damaged → In Repair → Active.<br><br>
        <b>5. Disposal Process</b> — Mark as Disposed only after formal write-off. Never delete active assets.<br><br>
        <b>6. Vendor Records</b> — Log vendor/technician in maintenance for warranty &amp; repeat-vendor analysis.<br><br>
        <b>7. Export Monthly</b> — Download merged Excel report at month-end for archiving.<br><br>
        <b>8. Employee Transfers</b> — Reassign assets before removing an employee from the system.<br><br>
        <b>9. Category Granularity</b> — Use specific categories:
        "Refrigeration – Display" vs "Refrigeration – Storage".<br><br>
        <b>10. Location Tagging</b> — Use aisle/section codes (e.g., "Aisle 3 – Dairy") for precise tracking.
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DOWNLOAD REPORT
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📥 Download Report":
    if ROLE != "Admin":
        st.error("🔒 Only Admin can download reports.")
        st.stop()

    tip("The merged report has one row per asset combining maintenance and audit summaries.")

    st.markdown("""
    <div style='background:#fff; border:2px solid #00a650; border-radius:14px; padding:24px;'>
        <h3 style='color:#004d26 !important; margin-top:0;'>📊 Report Contents</h3>
        <ul style='color:#0d2b1a; line-height:2.2;'>
            <li><b>Sheet 1 – Asset Master</b>: All assets merged with latest maintenance &amp;
                audit data (one row per Asset ID)</li>
            <li><b>Sheet 2 – Assets Raw</b>: Complete asset register</li>
            <li><b>Sheet 3 – Maintenance Raw</b>: Full maintenance log with costs &amp; vendors</li>
            <li><b>Sheet 4 – Audits Raw</b>: Full audit history with checker names &amp; remarks</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔄 Generate Report", use_container_width=True):
        with st.spinner("Building Excel report…"):
            report_bytes = merged_excel_bytes()
        fname = "LSM_Asset_Report_" + datetime.now().strftime("%Y%m%d_%H%M") + ".xlsx"
        st.download_button(
            label="📥 Download Excel Report",
            data=report_bytes,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.success("Report ready! Click the button above to download.")
