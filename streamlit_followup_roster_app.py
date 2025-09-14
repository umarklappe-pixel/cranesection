from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st

# ---------- CONFIG ----------
FOLDER_ID = "1v3NjAC6RwtmUrsR2qtzDLPw6hcDJzqSU"  # Replace with your Google Drive folder ID

# Google Drive API scopes
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Load credentials from Streamlit Secrets instead of file
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)

# Build Drive service
drive_service = build("drive", "v3", credentials=creds)


# ---------- FUNCTION ----------
def upload_to_drive(file_path, file_name, folder_id=None):
    """Uploads file to Google Drive and returns shareable link."""
    file_metadata = {"name": file_name}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    file_id = file.get("id")

    # Make file shareable (anyone with link can view)
    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    web_link = file.get("webViewLink")
    direct_link = f"https://drive.google.com/uc?export=view&id={file_id}"

    return {"id": file_id, "webViewLink": web_link, "directLink": direct_link}
