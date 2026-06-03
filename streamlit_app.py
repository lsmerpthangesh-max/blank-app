import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Lingam Super Market", layout="wide")

DB = "assets.db"
ADMIN_PASSWORD = "admin123"   # 🔐 change this

# -----------------------
# INIT DATABASE
# -----------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT UNIQUE,
        name TEXT,
        category TEXT,
        location TEXT,
        employee TEXT,
        purchase_date TEXT,
        cost REAL,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------
# DB HELPERS
# -----------------------
def get_categories():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT name FROM categories", conn)
    conn.close()
    return df["name"].tolist()

def add_category(name):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
    except:
        pass
    conn.close()

def get_employees():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT name FROM employees", conn)
    conn.close()
    return df["name"].tolist()

def add_employee(name):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO employees (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def generate_asset_id(category):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    prefix = "LSM" + category[:3].upper()

    c.execute("SELECT asset_id FROM assets WHERE category=?", (category,))
    ids = c.fetchall()

    numbers = []
    for i in ids:
        try:
            numbers.append(int(i[0].replace(prefix, "")))
        except:
            pass

    next_num = max(numbers)+1 if numbers else 1

    conn.close()
    return f"{prefix}{str(next_num).zfill(2)}"

def add_asset(name, category, location, employee, purchase_date, cost):
    asset_id = generate_asset_id(category)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO assets (asset_id, name, category, location, employee, purchase_date, cost, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (asset_id, name, category, location, employee, purchase_date, cost, "Active"))

        conn.commit()
        return True, asset_id
    except:
        return False, None
    finally:
        conn.close()

def get_assets():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM assets", conn)
    conn.close()
    return df

def delete_asset(asset_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM assets WHERE asset_id=?", (asset_id,))
    conn.commit()
    conn.close()

# -----------------------
# LOGIN
# -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Admin Login")

    pwd = st.text_input("Enter Password", type="password")

    if st.button("Login"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Wrong Password")

    st.stop()

# -----------------------
# HEADER
# -----------------------
st.markdown(
    "<h1 style='text-align:center;color:#009249;'>Lingam Super Market Asset Management System</h1>",
    unsafe_allow_html=True
)

# -----------------------
# SIDEBAR
# -----------------------
menu = st.sidebar.selectbox("Menu", [
    "Dashboard",
    "Add Category",
    "Add Employee",
    "Add Asset",
    "View Assets"
])

# -----------------------
# DASHBOARD
# -----------------------
if menu == "Dashboard":
    st.subheader("📊 Overview")

    df = get_assets()
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Assets", len(df))
    col2.metric("Active", len(df[df["status"]=="Active"]))
    col3.metric("Employees", len(get_employees()))

# -----------------------
# CATEGORY
# -----------------------
elif menu == "Add Category":
    st.subheader("📁 Add Category")

    name = st.text_input("Category Name")

    if st.button("Add"):
        add_category(name)
        st.success("Category Added")

# -----------------------
# EMPLOYEE
# -----------------------
elif menu == "Add Employee":
    st.subheader("👨‍💼 Add Employee")

    name = st.text_input("Employee Name")

    if st.button("Add"):
        add_employee(name)
        st.success("Employee Added")

# -----------------------
# ADD ASSET
# -----------------------
elif menu == "Add Asset":
    st.subheader("➕ Add Asset")

    categories = get_categories()
    employees = get_employees()

    name = st.text_input("Asset Name")
    category = st.selectbox("Category", categories)
    location = st.text_input("Location")
    employee = st.selectbox("Assign to Employee", employees)
    purchase_date = st.date_input("Purchase Date")
    cost = st.number_input("Cost", min_value=0.0)

    if st.button("Add Asset"):
        success, asset_id = add_asset(name, category, location, employee, str(purchase_date), cost)

        if success:
            st.success(f"Asset Added with ID: {asset_id}")
        else:
            st.error("Error adding asset")

# -----------------------
# VIEW ASSETS
# -----------------------
elif menu == "View Assets":
    st.subheader("📋 Asset List")

    df = get_assets()
    st.dataframe(df, use_container_width=True)

    # DELETE
    st.subheader("🗑 Delete Asset")
    asset_ids = df["asset_id"].tolist()

    selected = st.selectbox("Select Asset", asset_ids)

    if st.button("Delete"):
        delete_asset(selected)
        st.success("Deleted Successfully")
        st.rerun()

    # EXPORT
    st.subheader("📥 Export Data")

    if st.button("Download Excel"):
        file = "assets_export.xlsx"
        df.to_excel(file, index=False)
        with open(file, "rb") as f:
            st.download_button("Download File", f, file_name=file)
