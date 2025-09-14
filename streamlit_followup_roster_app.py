import streamlit as st
import requests
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

st.set_page_config(page_title="Drive Uploader")

CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]
REDIRECT_URI = st.secrets["google"]["redirect_uri"]
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

if "credentials" not in st.session_state:
    # Step 1: Show login button
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={' '.join(SCOPES)}"
        "&access_type=offline"
        "&prompt=consent"
    )
    st.markdown(f"[🔑 Sign in with Google]({auth_url})")

    # Step 2: Handle OAuth redirect
    code = st.query_params.get("code")
    if code:
        data = {
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token = requests.post("https://oauth2.googleapis.com/token", data=data).json()
        st.session_state.credentials = token
        st.experimental_rerun()

else:
    # Step 3: Use Drive API with access token
    token = st.session_state.credentials["access_token"]
    drive_service = build("drive", "v3", credentials=None)
    uploaded_file = st.file_uploader("Upload file", type=["jpg", "png", "pdf"])

    if uploaded_file and st.button("Upload to Drive"):
        media = MediaIoBaseUpload(
            io.BytesIO(uploaded_file.getbuffer()),
            mimetype=uploaded_file.type,
            resumable=False
        )
        file = drive_service.files().create(
            body={"name": uploaded_file.name},
            media_body=media,
            fields="id, webViewLink"
        ).execute()
        st.success(f"Uploaded: {file['webViewLink']}")
