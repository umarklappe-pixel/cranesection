import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# ---------------- CONFIG ----------------
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_ID = "1v3NjAC6RwtmUrsR2qtzDLPw6hcDJzqSU"  # Replace with your Google Drive folder ID

# Load credentials from Streamlit secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)

# Connect to Google Drive
drive_service = build("drive", "v3", credentials=creds)

# ---------------- UPLOAD FUNCTION ----------------
def upload_to_drive(uploaded_file, folder_id=None):
    file_metadata = {"name": uploaded_file.name}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getbuffer()), mimetype=uploaded_file.type, resumable=True)

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    # Make file public
    drive_service.permissions().create(
        fileId=file["id"],
        body={"role": "reader", "type": "anyone"},
    ).execute()

    # Return links
    return {
        "id": file["id"],
        "webViewLink": file["webViewLink"],
        "directLink": f"https://drive.google.com/uc?export=view&id={file['id']}"
    }

# ---------------- STREAMLIT UI ----------------
st.title("📤 Upload File to Google Drive")

uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is not None:
    if st.button("Upload to Google Drive"):
        result = upload_to_drive(uploaded_file, FOLDER_ID)
        st.success("✅ File uploaded successfully!")
        st.write("🔗 [Open in Google Drive](" + result["webViewLink"] + ")")
        st.image(result["directLink"], caption="Uploaded Preview", use_column_width=True)
