import streamlit as st
import pandas as pd
import gspread
import cloudinary
import cloudinary.uploader
from google.oauth2.service_account import Credentials
from datetime import datetime
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Crane Section Follow-up Dashboard", layout="wide")

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

headers = [
    "timestamp", "equipment", "section", "location", "issue",
    "picture_url", "voice_url",
    "required_items", "reported_by", "resolved_by",
    "after_picture_url", "status"
]

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
page = st.sidebar.radio("Go to", ["Follow-up Form", "Dashboard"])

# ---------------- FOLLOW-UP PAGE ----------------
if page == "Follow-up Form":
    st.title("📋 Follow-up")

    with st.form("add_form", clear_on_submit=True):
        equipment = st.selectbox("Equipment", ["ARTG", "RTG", "QC", "ROS", "SQ"])
        equipment_no = st.number_input("Equipment No.", min_value=1, step=1)
        section = st.selectbox("Section", ["Electrical", "Mechanical", "Welding"])
        location = st.text_area("Location")
        issue = st.text_area("Issue / Problem")
        picture = st.file_uploader("Upload Picture", type=["jpg", "jpeg", "png"])
        voice = st.file_uploader("Upload Voice Note (Audio/Video)", type=["mp3","wav","aac","m4a","ogg","flac","mp4","mov","webm","mkv","avi","wmv","3gp"]
)
        reported_by = st.text_input("Reported by")

        submitted = st.form_submit_button("✅ Submit Follow-up")
        if submitted:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            picture_url, voice_url = "", ""

            if picture:
                picture_url = upload_to_cloudinary(picture)
            if voice:
                voice_url = upload_to_cloudinary(voice)

            add_followup({
                "timestamp": timestamp,
                "equipment": f"{equipment}-{equipment_no}",
                "section": section,
                "location": location,
                "issue": issue,
                "picture_url": picture_url,
                "voice_url": voice_url,
                "required_items": "",      # future use
                "reported_by": reported_by,
                "resolved_by": "",         # future use
                "after_picture_url": "",   # future use
                "status": ""               # future use
            })
            st.success("✅ Follow-up added successfully!")

# ---------------- DASHBOARD PAGE ----------------
elif page == "Dashboard":
    st.title("📊 Follow-up Dashboard")
    df = load_followups()

    if df.empty:
        st.info("No follow-ups recorded yet.")
    else:
        st.subheader("📌 All Records")

        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"### 🏗️ {row['equipment']} — Equipment {row['equipment_no']}")
                st.write(f"**Section:** {row['section']}")
                st.write(f"📝 **Issue:** {row['issue']}")

                cols = st.columns([1, 2])  # layout for image + text/audio
                with cols[0]:
                    if row['picture_url']:
                        st.image(row['picture_url'], caption="Picture", width=200)

                with cols[1]:
                    if row['voice_url']:
                        if row['voice_url'].endswith((".mp4", ".m4a")):
                            st.video(row['voice_url'])
                        else:
                            st.audio(row['voice_url'])

                st.caption(f"👤 Reported by: {row['reported_by']} on {row['timestamp']}")
                st.markdown("---")

        # Download option
        st.subheader("📥 Export Data")
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button("Download Excel", buffer.getvalue(),
                           file_name="followups.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
