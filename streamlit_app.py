import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import qrcode
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Lingam Super Market", layout="wide")

DB = "assets.db"
ADMIN_PASSWORD = "admin123"

# -----------------------
# INIT DB
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
        details TEXT,
        replacement TEXT,
        reason TEXT,
        duration TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS audits (
        asset_id TEXT,
        month TEXT,
        auditor TEXT,
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

# -----------------------
# ASSET ID
# -----------------------
def generate_asset_id():
    df = fetch_df("SELECT asset_id FROM assets")
    nums = [int(i.replace("LSM","")) for i in df["asset_id"]] if not df.empty else []
    next_num = max(nums)+1 if nums else 1
    return f"LSM{str(next_num).zfill(2)}"

# -----------------------
# QR CODE
# -----------------------
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
st.markdown("<h1 style='text-align:center;color:#009249;'>Lingam Super Market Asset Management System</h1>", unsafe_allow_html=True)

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
    df = fetch_df("SELECT * FROM assets")
    st.metric("Total Assets", len(df))

# -----------------------
# CATEGORY
# -----------------------
elif menu == "Add Category":
    name = st.text_input("Category")
    if st.button("Add"):
        run_query("INSERT OR IGNORE INTO categories VALUES (?)", (name,))
        st.success("Added")

# -----------------------
# EMPLOYEE
# -----------------------
elif menu == "Add Employee":
    name = st.text_input("Employee")
    if st.button("Add"):
        run_query("INSERT INTO employees VALUES (?)", (name,))
        st.success("Added")

# -----------------------
# ADD ASSET
# -----------------------
elif menu == "Add Asset":
    categories = fetch_df("SELECT name FROM categories")["name"].tolist()
    employees = fetch_df("SELECT name FROM employees")["name"].tolist()

    name = st.text_input("Asset Name")
    category = st.selectbox("Category", categories)
    location = st.text_input("Location")
    employee = st.selectbox("Assign Employee", employees)
    quantity = st.number_input("Quantity", min_value=1)
    allocation_date = st.date_input("Allocation Date")
    purchase_date = st.date_input("Purchase Date")
    cost = st.number_input("Cost")

    if st.button("Add"):
        asset_id = generate_asset_id()
        run_query("""
        INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (asset_id, name, category, location, employee, quantity,
              str(allocation_date), str(purchase_date), cost, "Active"))

        st.success(f"Added: {asset_id}")

# -----------------------
# VIEW
# -----------------------
elif menu == "View Assets":
    df = fetch_df("SELECT * FROM assets")
    st.dataframe(df)

    st.subheader("📌 QR Code Preview")
    for i in df["asset_id"]:
        path = generate_qr(i)
        st.image(path, caption=i, width=150)

    st.subheader("📥 Export Asset IDs")
    ids_df = df[["asset_id"]]

    st.download_button("Download Excel", ids_df.to_csv(index=False), "asset_ids.csv")

    if st.button("Generate PDF"):
        doc = SimpleDocTemplate("asset_ids.pdf")
        styles = getSampleStyleSheet()
        elements = []

        for i in ids_df["asset_id"]:
            elements.append(Paragraph(i, styles["Normal"]))

        doc.build(elements)

        with open("asset_ids.pdf", "rb") as f:
            st.download_button("Download PDF", f, "asset_ids.pdf")

# -----------------------
# MAINTENANCE
# -----------------------
elif menu == "Maintenance":
    ids = fetch_df("SELECT asset_id FROM assets")["asset_id"].tolist()

    asset_id = st.selectbox("Asset", ids)
    details = st.text_area("Work Done")
    replacement = st.text_input("Changed Component")
    reason = st.text_input("Reason")
    duration = st.text_input("Used Time / Duration")

    if st.button("Submit"):
        run_query("""
        INSERT INTO maintenance VALUES (?,?,?,?,?,?)
        """, (asset_id, str(datetime.now()), details, replacement, reason, duration))
        st.success("Saved")

# -----------------------
# AUDIT
# -----------------------
elif menu == "Audit":
    ids = fetch_df("SELECT asset_id FROM assets")["asset_id"].tolist()

    asset_id = st.selectbox("Asset", ids)
    month = st.selectbox("Month", [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sep","Oct","Nov","Dec"
    ])
    auditor = st.text_input("Auditor Name")
    status = st.checkbox("Checked")

    if st.button("Save"):
        run_query("""
        INSERT INTO audits VALUES (?,?,?,?)
        """, (asset_id, month, auditor, str(status)))
        st.success("Audit Saved")
