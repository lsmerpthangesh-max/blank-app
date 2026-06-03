import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import qrcode

# -----------------------
# CONFIG UI
# -----------------------
st.set_page_config(page_title="Lingam Super Market", layout="wide")

# 🎨 CUSTOM STYLE
st.markdown("""
<style>

/* 🌿 Background */
body {
    background-color: #009249;
}
.block-container {
    background-color: #009249;
}

/* 🖤 TEXT → BLACK (MAIN FIX) */
h1, h2, h3, h4, h5, h6, p, label, div, span {
    color: black !important;
}


/* 🌿 Sidebar */
[data-testid="stSidebar"] {
    background-color: #007a3a;
}
[data-testid="stSidebar"] * {
    color: black !important;
}

/* 🔘 Buttons */
.stButton > button {
    background-color: #006d33;
    color: white;
    border-radius: 8px;
}

/* 📝 Inputs */
.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stSelectbox div {
    background-color: #e6f5ec;
    color: black;
}

/* 📊 Dataframe */
[data-testid="stDataFrame"] {
    background-color: white;
    color: black;
}

/* 📊 Metrics */
[data-testid="stMetric"] {
    background-color: #006d33;
    padding: 10px;
    border-radius: 10px;
    color: white;
}

/* ⚠ Alerts */
.stAlert {
    background-color: #004d26;
    color: white;
}

</style>
""", unsafe_allow_html=True)

DB = "assets.db"
ADMIN_PASSWORD = "admin123"

# -----------------------
# DB INIT
# -----------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (name TEXT)")

    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        asset_id TEXT PRIMARY KEY,
        name TEXT,
        category TEXT,
        location TEXT,
        employee TEXT,
        quantity INTEGER,
        allocation_date TEXT,
        purchase_date TEXT,
        cost REAL,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS maintenance (
        asset_id TEXT,
        date TEXT,
        details TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS audits (
        asset_id TEXT,
        month TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------
# HELPERS
# -----------------------
def run_query(q, params=()):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(q, params)
    conn.commit()
    conn.close()

def fetch_df(q):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(q, conn)
    conn.close()
    return df

def generate_asset_id():
    df = fetch_df("SELECT asset_id FROM assets")
    nums = [int(i.replace("LSM","")) for i in df["asset_id"]] if not df.empty else []
    next_num = max(nums)+1 if nums else 1
    return f"LSM{str(next_num).zfill(2)}"

def generate_qr(asset_id):
    os.makedirs("qr_codes", exist_ok=True)
    path = f"qr_codes/{asset_id}.png"
    qr = qrcode.make(asset_id)
    qr.save(path)
    return path

# -----------------------
# LOGIN
# -----------------------
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Admin Login")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Wrong Password")
    st.stop()

# -----------------------
# HEADER
# -----------------------
st.markdown(
    "<h1 style='text-align:center; color:yellow;'>Lingam Super Market Asset Management System</h1>",
    unsafe_allow_html=True)

menu = st.sidebar.selectbox("Menu", [
    "Dashboard",
    "Add Category",
    "Add Employee",
    "Add Asset",
    "View Assets",
    "Maintenance",
    "Audit"
])

# -----------------------
# DASHBOARD
# -----------------------
if menu == "Dashboard":
    st.subheader("📊 Dashboard")

    df = fetch_df("SELECT * FROM assets")
    maint = fetch_df("SELECT * FROM maintenance")
    audit = fetch_df("SELECT * FROM audits")

    col1, col2, col3, col4 = st.columns(4)

    total = len(df)
    damaged = len(df[df["status"]=="Damaged"])
    maintenance_count = len(maint)
    checked = len(audit[audit["status"]=="True"])
    not_checked = len(df) - checked

    col1.metric("📦 Total Assets", total)
    col2.metric("❌ Damaged", damaged)
    col3.metric("🛠 Maintenance", maintenance_count)
    col4.metric("✅ Checked", checked)

    st.metric("⚠ Not Checked", not_checked)

    # ALERT
    today = datetime.now().day
    if today > 25:
        st.warning("⚠ Month End Audit Pending!")

    # DATE FILTER
    st.subheader("📅 Filter")
    start = st.date_input("From")
    end = st.date_input("To")

    if start and end:
        df["purchase_date"] = pd.to_datetime(df["purchase_date"])
        filtered = df[(df["purchase_date"]>=pd.to_datetime(start)) &
                      (df["purchase_date"]<=pd.to_datetime(end))]
        st.dataframe(filtered)

    # EXPORT FULL DASHBOARD
    if st.button("📥 Download Full Report"):
        with pd.ExcelWriter("dashboard.xlsx") as writer:
            df.to_excel(writer, sheet_name="Assets", index=False)
            maint.to_excel(writer, sheet_name="Maintenance", index=False)
            audit.to_excel(writer, sheet_name="Audit", index=False)

        with open("dashboard.xlsx","rb") as f:
            st.download_button("Download", f, "dashboard.xlsx")

# -----------------------
# ADD CATEGORY
# -----------------------
elif menu == "Add Category":
    name = st.text_input("Category")
    if st.button("Add"):
        run_query("INSERT OR IGNORE INTO categories VALUES (?)", (name,))
        st.success("Added")

    st.subheader("📋 View")
    st.dataframe(fetch_df("SELECT * FROM categories"))

# -----------------------
# ADD EMPLOYEE
# -----------------------
elif menu == "Add Employee":
    name = st.text_input("Employee")
    if st.button("Add"):
        run_query("INSERT INTO employees VALUES (?)", (name,))
        st.success("Added")

    st.subheader("📋 View")
    st.dataframe(fetch_df("SELECT * FROM employees"))

# -----------------------
# ADD ASSET
# -----------------------
elif menu == "Add Asset":
    categories = fetch_df("SELECT name FROM categories")["name"].tolist()
    employees = fetch_df("SELECT name FROM employees")["name"].tolist()

    name = st.text_input("Asset Name")
    category = st.selectbox("Category", categories)
    location = st.text_input("Location")
    employee = st.selectbox("Employee", employees)
    qty = st.number_input("Quantity", min_value=1)
    purchase = st.date_input("Purchase Date")

    if st.button("Add"):
        asset_id = generate_asset_id()
        run_query("""
        INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (asset_id, name, category, location, employee, qty,
              str(datetime.now()), str(purchase), 0, "Active"))
        st.success(f"Added {asset_id}")

# -----------------------
# VIEW ASSETS
# -----------------------
elif menu == "View Assets":
    df = fetch_df("SELECT * FROM assets")
    st.dataframe(df)

    st.subheader("📌 QR View")
    for i in df["asset_id"]:
        st.image(generate_qr(i), width=120)

# -----------------------
# MAINTENANCE
# -----------------------
elif menu == "Maintenance":
    ids = fetch_df("SELECT asset_id FROM assets")["asset_id"].tolist()

    asset_id = st.selectbox("Asset", ids)
    details = st.text_area("Details")

    if st.button("Save"):
        run_query("INSERT INTO maintenance VALUES (?,?,?)",
                  (asset_id, str(datetime.now()), details))
        st.success("Saved")

    st.subheader("📋 View")
    st.dataframe(fetch_df("SELECT * FROM maintenance"))

# -----------------------
# AUDIT
# -----------------------
elif menu == "Audit":
    ids = fetch_df("SELECT asset_id FROM assets")["asset_id"].tolist()

    asset_id = st.selectbox("Asset", ids)
    month = st.selectbox("Month", ["Jan","Feb","Mar","Apr","May","Jun",
                                  "Jul","Aug","Sep","Oct","Nov","Dec"])
    status = st.checkbox("Checked")

    if st.button("Save"):
        run_query("INSERT INTO audits VALUES (?,?,?)",
                  (asset_id, month, str(status)))
        st.success("Saved")

    st.subheader("📋 View")
    st.dataframe(fetch_df("SELECT * FROM audits"))
