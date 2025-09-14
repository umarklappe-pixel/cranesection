import streamlit as st
import pandas as pd
import os
from datetime import datetime
from sqlalchemy import create_engine
from PIL import Image

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="Follow-up & Roster Dashboard", layout="wide")
DB_FILE = "app_data.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------- DATABASE ----------------------
engine = create_engine(f"sqlite:///{DB_FILE}")

# Initialize tables
def init_db():
    with engine.begin() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                equipment TEXT,
                priority TEXT,
                section TEXT,
                problem TEXT,
                picture TEXT,
                note TEXT,
                item_codes TEXT,
                reported_by TEXT,
                resolved_by TEXT,
                status TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS roster (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                sunday TEXT, monday TEXT, tuesday TEXT, wednesday TEXT,
                thursday TEXT, friday TEXT, saturday TEXT
            )
        """)

init_db()

# ---------------------- FOLLOW-UP FUNCTIONS ----------------------
def add_followup(data):
    df = pd.DataFrame([data])
    df.to_sql("followups", engine, if_exists="append", index=False)

def load_followups():
    return pd.read_sql("SELECT * FROM followups", engine)

# ---------------------- ROSTER FUNCTIONS ----------------------
def load_roster():
    df = pd.read_sql("SELECT * FROM roster", engine)
    if df.empty:
        roles = ["QC PM", "QC CM", "RTG PM", "RTG CM", "ARTG PM", "ARTG CM", "Spreader PM/CM", "Maximo/SOP"]
        for role in roles:
            pd.DataFrame([{ "role": role }]).to_sql("roster", engine, if_exists="append", index=False)
        df = pd.read_sql("SELECT * FROM roster", engine)
    return df

def update_roster(df):
    with engine.begin() as conn:
        conn.execute("DELETE FROM roster")
    df.to_sql("roster", engine, if_exists="append", index=False)

# ---------------------- APP ----------------------
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["Follow-up Sheet", "Weekly Roster", "Reports"])

# ---------------------- FOLLOW-UP PAGE ----------------------
if page == "Follow-up Sheet":
    st.title("📋 Follow-up Sheet")

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            timestamp = st.date_input("Timestamp", datetime.today()).strftime("%Y-%m-%d")
            equipment = st.text_input("Equipment")
            priority = st.selectbox("Priority", ["H", "M", "L"])
            section = st.text_input("Section")
            problem = st.text_area("Problem")
        with col2:
            picture = st.file_uploader("Picture", type=["jpg", "png", "jpeg"])
            note = st.text_area("Note")
            item_codes = st.text_input("Item codes (Required items)")
            reported_by = st.text_input("Reported by")
            resolved_by = st.text_input("Resolved by")
            status = st.selectbox("Status", ["Open", "Pending", "Closed"])

        submitted = st.form_submit_button("Add Follow-up")
        if submitted:
            picture_path = None
            if picture:
                picture_path = os.path.join(UPLOAD_FOLDER, picture.name)
                with open(picture_path, "wb") as f:
                    f.write(picture.getbuffer())
            add_followup({
                "timestamp": timestamp,
                "equipment": equipment,
                "priority": priority,
                "section": section,
                "problem": problem,
                "picture": picture_path,
                "note": note,
                "item_codes": item_codes,
                "reported_by": reported_by,
                "resolved_by": resolved_by,
                "status": status
            })
            st.success("✅ Follow-up added successfully!")

    st.subheader("Follow-up Records")
    df = load_followups()
    st.dataframe(df)

    st.download_button("📥 Download Excel", df.to_excel(index=False, engine='openpyxl'), "followups.xlsx")

# ---------------------- ROSTER PAGE ----------------------
elif page == "Weekly Roster":
    st.title("📅 Weekly Duty Roster")
    df = load_roster()
    st.dataframe(df, editable=True)

    if st.button("💾 Save Roster"):
        update_roster(df)
        st.success("✅ Roster updated successfully!")

    st.download_button("📥 Download Excel", df.to_excel(index=False, engine='openpyxl'), "roster.xlsx")

# ---------------------- REPORTS PAGE ----------------------
elif page == "Reports":
    st.title("📊 Reports")
    df = load_followups()

    if df.empty:
        st.info("No data available.")
    else:
        st.metric("Total Follow-ups", len(df))
        st.metric("Open", len(df[df['status']=="Open"]))
        st.metric("Closed", len(df[df['status']=="Closed"]))
        st.metric("Pending", len(df[df['status']=="Pending"]))
