import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import qrcode
import os

DB = "assets.db"

# -----------------------
# DATABASE INIT
# -----------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT UNIQUE,
        name TEXT,
        category TEXT,
        location TEXT,
        purchase_date TEXT,
        cost REAL,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT,
        date TEXT,
        details TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------
# GENERATE QR
# -----------------------
def generate_qr(asset_id):
    folder = "qr_codes"
    os.makedirs(folder, exist_ok=True)
    path = f"{folder}/{asset_id}.png"

    qr = qrcode.make(asset_id)
    qr.save(path)

    return path

# -----------------------
# ADD ASSET
# -----------------------
def add_asset(asset_id, name, category, location, purchase_date, cost):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO assets (asset_id, name, category, location, purchase_date, cost, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (asset_id, name, category, location, purchase_date, cost, "Active"))

        conn.commit()
        generate_qr(asset_id)
        return True
    except:
        return False
    finally:
        conn.close()

# -----------------------
# FETCH DATA
# -----------------------
def get_assets():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM assets", conn)
    conn.close()
    return df

# -----------------------
# UPDATE STATUS
# -----------------------
def update_status(asset_id, status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE assets SET status=? WHERE asset_id=?", (status, asset_id))
    conn.commit()
    conn.close()

# -----------------------
# ADD MAINTENANCE
# -----------------------
def add_maintenance(asset_id, details):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO maintenance (asset_id, date, details)
    VALUES (?, ?, ?)
    """, (asset_id, datetime.now().strftime("%Y-%m-%d"), details))

    conn.commit()
    conn.close()

# -----------------------
# UI
# -----------------------
st.set_page_config(page_title="Asset Management", layout="wide")

st.title("📦 Asset Management System")

menu = ["Add Asset", "View Assets", "Update Status", "Maintenance"]
choice = st.sidebar.selectbox("Menu", menu)

# -----------------------
# ADD ASSET UI
# -----------------------
if choice == "Add Asset":
    st.subheader("➕ Add New Asset")

    col1, col2 = st.columns(2)

    with col1:
        asset_id = st.text_input("Asset ID")
        name = st.text_input("Asset Name")
        category = st.selectbox("Category", ["Electronics", "Furniture", "Equipment"])

    with col2:
        location = st.text_input("Location")
        purchase_date = st.date_input("Purchase Date")
        cost = st.number_input("Cost", min_value=0.0)

    if st.button("Add Asset"):
        if asset_id and name:
            success = add_asset(asset_id, name, category, location, str(purchase_date), cost)
            if success:
                st.success("Asset Added Successfully!")
                qr_path = f"qr_codes/{asset_id}.png"
                st.image(qr_path, caption="QR Code")
            else:
                st.error("Asset ID already exists!")
        else:
            st.warning("Please fill required fields")

# -----------------------
# VIEW ASSETS
# -----------------------
elif choice == "View Assets":
    st.subheader("📋 Asset List")

    df = get_assets()
    st.dataframe(df, use_container_width=True)

# -----------------------
# UPDATE STATUS
# -----------------------
elif choice == "Update Status":
    st.subheader("🔄 Update Asset Status")

    df = get_assets()
    asset_ids = df["asset_id"].tolist()

    asset_id = st.selectbox("Select Asset", asset_ids)
    status = st.selectbox("Status", ["Active", "Repair", "Scrap"])

    if st.button("Update"):
        update_status(asset_id, status)
        st.success("Status Updated!")

# -----------------------
# MAINTENANCE
# -----------------------
elif choice == "Maintenance":
    st.subheader("🛠 Maintenance Log")

    df = get_assets()
    asset_ids = df["asset_id"].tolist()

    asset_id = st.selectbox("Select Asset", asset_ids)
    details = st.text_area("Maintenance Details")

    if st.button("Add Record"):
        add_maintenance(asset_id, details)
        st.success("Maintenance Added!")
