import streamlit as st
import pandas as pd
import gspread
import cloudinary
import cloudinary.uploader
from google.oauth2.service_account import Credentials
from datetime import datetime
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Follow-up & Roster Dashboard", layout="wide")

# Google Sheets Scopes
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
client = gspread.authorize(creds)

# Cloudinary Config
cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

# ---------------- SHEET CONNECTION ----------------
SHEET_ID = "1fv-LQimF2XfCQ936Lj-kIukooQQUCJZOJsoM4SNAdjQ"

try:
    sh = client.open_by_key(SHEET_ID)
    st.sidebar.success(f"Connected to: {sh.title}")
except Exception as e:
    st.error(f"❌ Failed to connect: {e}")
    st.stop()

# Ensure worksheet exists with correct headers
try:
    followup_ws = sh.worksheet("Followups")
except gspread.exceptions.WorksheetNotFound:
    followup_ws = sh.add_worksheet(title="Followups", rows="1000", cols="20")

headers = ["timestamp", "section", "equipment", "problem", "image_url", "audio_url", "reported_by"]
if followup_ws.row_values(1) != headers:
    followup_ws.clear()
    followup_ws.append_row(headers)

# ---------------- FUNCTIONS ----------------
def upload_to_cloudinary(file, folder="followups"):
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="auto"
    )
    return result["secure_url"]

def add_followup(data):
    followup_ws.append_row(list(data.values()))

def load_followups():
    records = followup_ws.get_all_records()
    return pd.DataFrame(records)

# ---------------- SIDEBAR ----------------
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["Follow-up Sheet", "Reports"])

# ---------------- FOLLOW-UP PAGE ----------------
if page == "Follow-up Sheet":
    st.title("📋 Follow-up Sheet")

    with st.form("add_form", clear_on_submit=True):
        section = st.selectbox("Section", ["RTG", "ARTG", "STS", "Spreader"])
        equipment = st.selectbox("Equipment No.", list(range(1, 54)))
        problem = st.text_area("Problem")
        image = st.file_uploader("Upload Picture", type=["jpg", "jpeg", "png"])
        audio = st.file_uploader("Upload Audio", type=["mp3", "wav"])
        reported_by = st.text_input("Reported by")

        submitted = st.form_submit_button("Add Follow-up")
        if submitted:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            image_url, audio_url = "", ""

            if image:
                image_url = upload_to_cloudinary(image)
            if audio:
                audio_url = upload_to_cloudinary(audio)

            add_followup({
                "timestamp": timestamp,
                "section": section,
                "equipment": equipment,
                "problem": problem,
                "image_url": image_url,
                "audio_url": audio_url,
                "reported_by": reported_by
            })
            st.success("✅ Follow-up added successfully!")

    st.subheader("Follow-up Records")
    df = load_followups()
    if df.empty:
        st.warning("⚠️ No follow-ups recorded yet.")
    else:
        for _, row in df.iterrows():
            st.markdown(f"### {row['section']} — Equipment {row['equipment']}")
            st.write(f"📝 **Problem:** {row['problem']}")
            if row['image_url']:
                st.image(row['image_url'], width=200)
            if row['audio_url']:
                st.audio(row['audio_url'])
            st.caption(f"Reported by: {row['reported_by']} on {row['timestamp']}")
            st.markdown("---")

        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button("📥 Download Excel", buffer.getvalue(),
                           file_name="followups.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------------- REPORTS PAGE ----------------
elif page == "Reports":
    st.title("📊 Reports")
    df = load_followups()

    if df.empty:
        st.info("No data available.")
    else:
        st.metric("Total Follow-ups", len(df))
        st.metric("Sections", df["section"].nunique())
        st.metric("Reported By (Unique)", df["reported_by"].nunique())
