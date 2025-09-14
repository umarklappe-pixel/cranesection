import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from io import BytesIO

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="Follow-up & Roster Dashboard", layout="wide")

# ---------------------- GOOGLE SHEETS ----------------------
# Define scope
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
client = gspread.authorize(creds)

# Open Google Sheets (make sure your service account email has Editor access)
SHEET_NAME = "Crane Follow-up Database"
followup_ws = client.open(SHEET_NAME).worksheet("Followups")
roster_ws = client.open(SHEET_NAME).worksheet("Roster")

# ---------------------- FOLLOW-UP FUNCTIONS ----------------------
def add_followup(data):
    followup_ws.append_row(list(data.values()))

def load_followups():
    records = followup_ws.get_all_records()
    return pd.DataFrame(records)

# ---------------------- ROSTER FUNCTIONS ----------------------
def load_roster():
    records = roster_ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        roles = ["QC PM", "QC CM", "RTG PM", "RTG CM", "ARTG PM",
                 "ARTG CM", "Spreader PM/CM", "Maximo/SOP"]
        for role in roles:
            roster_ws.append_row([role, "", "", "", "", "", "", ""])
        records = roster_ws.get_all_records()
        df = pd.DataFrame(records)
    return df

def update_roster(df):
    roster_ws.clear()
    roster_ws.append_row(df.columns.tolist())  # headers
    for row in df.values.tolist():
        roster_ws.append_row(row)

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
            note = st.text_area("Note")
            item_codes = st.text_input("Item codes (Required items)")
            reported_by = st.text_input("Reported by")
            resolved_by = st.text_input("Resolved by")
            status = st.selectbox("Status", ["Open", "Pending", "Closed"])

        submitted = st.form_submit_button("Add Follow-up")
        if submitted:
            add_followup({
                "timestamp": timestamp,
                "equipment": equipment,
                "priority": priority,
                "section": section,
                "problem": problem,
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

    if not df.empty:
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button(
            "📥 Download Excel",
            buffer.getvalue(),
            file_name="followups.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ---------------------- ROSTER PAGE ----------------------
elif page == "Weekly Roster":
    st.title("📅 Weekly Duty Roster")
    df = load_roster()
    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("💾 Save Roster"):
        update_roster(edited_df)
        st.success("✅ Roster updated successfully!")

    buffer = BytesIO()
    edited_df.to_excel(buffer, index=False, engine="openpyxl")
    st.download_button(
        "📥 Download Excel",
        buffer.getvalue(),
        file_name="roster.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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
