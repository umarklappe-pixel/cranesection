import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
from datetime import datetime
import os

# =============== Cloudinary Setup ===============
# Put your Cloudinary credentials in a .env file or here directly
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "your_cloud_name"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "your_api_key"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "your_api_secret"),
    secure=True
)

CSV_FILE = "reports.csv"

# Load or initialize CSV
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=[
        "section", "equipment", "problem",
        "image_url", "audio_url", "reported_by", "timestamp"
    ])


# =============== Upload Helpers ===============
def upload_to_cloudinary(file, folder="equipment_reports"):
    """Upload file to Cloudinary and return URL"""
    result = cloudinary.uploader.upload(file, folder=folder, resource_type="auto")
    return result["secure_url"]


# =============== Streamlit UI ===============
st.title("⚙️ Equipment Fault Reporting")

with st.form("report_form"):
    section = st.text_input("Section")
    equipment = st.text_input("Equipment Name")
    problem = st.text_area("Describe the Problem")
    image = st.file_uploader("Upload Picture", type=["jpg", "jpeg", "png"])
    audio = st.file_uploader(
        "Upload Audio/Video",
        type=[
            "mp3", "wav", "aac", "m4a", "ogg", "flac",
            "mp4", "mov", "avi", "mpg", "mpeg", "webm"
        ]
    )
    reported_by = st.text_input("Your Name")
    submitted = st.form_submit_button("Submit Report")

    if submitted:
        if section and equipment and problem:
            image_url = upload_to_cloudinary(image) if image else ""
            audio_url = upload_to_cloudinary(audio) if audio else ""
            new_row = {
                "section": section,
                "equipment": equipment,
                "problem": problem,
                "image_url": image_url,
                "audio_url": audio_url,
                "reported_by": reported_by,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.success("✅ Report submitted successfully!")
        else:
            st.warning("⚠️ Please fill in Section, Equipment, and Problem details.")


# =============== Display All Reports ===============
st.header("📋 All Reports")

if not df.empty:
    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"### 🏭 {row['section']} — ⚡ {row['equipment']}")
            st.write(f"**Problem:** {row['problem']}")

            # Image
            if row['image_url']:
                st.image(row['image_url'], width=200)

            # Audio or Video
            if row['audio_url']:
                if any(row['audio_url'].lower().endswith(ext) for ext in [".mp4", ".mov", ".avi", ".mpg", ".mpeg", ".webm"]):
                    st.video(row['audio_url'])
                else:
                    st.audio(row['audio_url'])

            st.caption(f"Reported by {row['reported_by']} on {row['timestamp']}")
            st.markdown("---")

    # ========== Show Table/List at Bottom ==========
    st.subheader("📑 Reports Table View")
    st.dataframe(df)
else:
    st.info("No reports submitted yet.")
