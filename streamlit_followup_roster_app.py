import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from io import BytesIO
import tempfile
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Follow-up & Roster Dashboard", layout="wide")

# Google API Scopes
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)

# Google Sheets client
client = gspread.authorize(creds)

# Google Drive client
drive_service = build("drive", "v3", credentials=creds)

# ---------------- SHEET CONNECTION ----------------
SHEET_ID = "1fv-LQimF2XfCQ936Lj-kIukooQQUCJZOJsoM4SNAdjQ"
FOLDER_ID = "1v3NjAC6RwtmUrsR2qtzDLPw6hcDJzqSU"   # 🔑 Replace with your Drive folder ID

try:
    sh = client.open_by_key(SHEET_ID)
    st.sidebar.success(f"Connected to: {sh.title}")
except Exception as e:
    st.error(f"❌ Failed to connect: {e}")
    st.stop()

# Ensure worksheets exist
try:
    followup_ws = sh.worksheet("Followups")
except gspread.exceptions.WorksheetNotFound:
    followup_ws = sh.add_worksheet(title="Followups", rows="1000", cols="20")
    followup_ws.append_row([
        "timestamp", "section", "equipment", "problem",
        "note", "image_url", "reported_by"
    ])

try:
    roster_ws = sh.worksheet("Roster")
except gspread.exceptions.WorksheetNotFound:
    roster_ws = sh.add_worksheet(title="Roster", rows="1000", cols="20")
    roster_ws.append_row([
        "role", "sunday", "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday"
    ])

# ---------------- FUNCTIONS ----------------
def upload_to_drive(file) -> str:
    """Upload image to Google Drive and return public URL"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.getbuffer())
        tmp_path = tmp.name

    file_metadata = {
        "name": file.name,
        "parents": [FOLDER_ID]
    }
    media = MediaFileUpload(tmp_path, mimetype=file.type)
    uploaded_file = drive_service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()

    file_id = uploaded_file.get("id")

    # Make file public
    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"}
    ).execute()

    os.remove(tmp_path)
    return f"https://drive.google.com/uc?id={file_id}"


def add_followup(data):
    followup_ws.append_row(list(data.values()))

def load_followups():
    records = followup_ws.get_all_records()
    return pd.DataFrame(records)

def load_roster():
    records = roster_ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        roles = ["QC PM", "QC CM", "RTG PM", "RTG CM", "ARTG PM",
                 "ARTG CM", "Spreader PM/CM", "Maximo/SOP"]
        for role in roles:
            roster_ws.append_row([role, "", "", "", "", "", "", ""])
        df = pd.DataFrame(roster_ws.get_all_records())
    return df

def update_roster(df):
    roster_ws.clear()
    roster_ws.append_row(df.columns.tolist())  # headers
    for row in df.values.tolist():
        roster_ws.append_row(row)

# ---------------- SIDEBAR ----------------
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["Follow-up Sheet", "Weekly Roster", "Reports"])

# ---------------- FOLLOW-UP PAGE ----------------
if page == "Follow-up Sheet":
    st.title("📋 Follow-up Sheet")

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            section = st.selectbox("Section", ["RTG", "ARTG", "STS", "Spreader"])
            equipment = st.selectbox("Equipment (Week #)", [f"Week {i}" for i in range(1, 54)])
            problem = st.text_area("Problem")
        with col2:
            picture = st.file_uploader("Upload Picture", type=["jpg", "png", "jpeg"])
            note = st.text_area("Note")
            reported_by = st.text_input("Reported by")

        submitted = st.form_submit_button("Add Follow-up")
        if submitted:
            image_url = ""
            if picture:
                image_url = upload_to_drive(picture)

            add_followup({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "section": section,
                "equipment": equipment,
                "problem": problem,
                "note": note,
                "image_url": image_url,
                "reported_by": reported_by
            })
            st.success("✅ Follow-up added successfully!")

    st.subheader("Follow-up Records")
    df = load_followups()

    if not df.empty:
        for _, row in df.iterrows():
            with st.container():
                st.write(f"📌 **{row['section']} - {row['equipment']}** | Reported by: {row['reported_by']}")
                st.write(f"📝 Problem: {row['problem']}")
                st.write(f"📒 Note: {row['note']}")
                if row["image_url"]:
                    st.image(row["image_url"], width=300)
                st.divider()

        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button("📥 Download Excel", buffer.getvalue(),
                           file_name="followups.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------------- ROSTER PAGE ----------------
elif page == "Weekly Roster":
    st.title("📅 Weekly Duty Roster")
    df = load_roster()
    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("💾 Save Roster"):
        update_roster(edited_df)
        st.success("✅ Roster updated successfully!")

    buffer = BytesIO()
    edited_df.to_excel(buffer, index=False, engine="openpyxl")
    st.download_button("📥 Download Excel", buffer.getvalue(),
                       file_name="roster.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------------- REPORTS PAGE ----------------
elif page == "Reports":
    st.title("📊 Reports")
    df = load_followups()

    if df.empty:
        st.info("No data available.")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Total Follow-ups", len(df))
        col2.metric("With Images", df["image_url"].astype(bool).sum())
