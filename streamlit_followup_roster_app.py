import streamlit as st
import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# Setup
CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]
REDIRECT_URI = st.secrets["google"]["redirect_uri"]
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

if "credentials" not in st.session_state:
    # Step 1: Ask user to log in
    if st.button("Login with Google"):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uris": [REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES
        )
        flow.redirect_uri = REDIRECT_URI
        auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")
        st.session_state["state"] = state
        st.markdown(f"[Click here to authorize]({auth_url})")

    # Step 2: Handle the callback (extract `code` from the URL)
    code = st.query_params.get("code")
    state = st.query_params.get("state")
    if code and state == st.session_state.get("state"):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uris": [REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            state=state
        )
        flow.redirect_uri = REDIRECT_URI
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.session_state["credentials"] = creds.to_json()
        st.success("Login successful! You can now upload files.")
else:
    creds = Credentials.from_authorized_user_info(eval(st.session_state["credentials"]))
    st.write("✅ Logged in to Google Drive!")

    uploaded = st.file_uploader("Choose a file to upload")
    if uploaded:
        # Upload file to Google Drive
        files = {
            'data': ('metadata', '{"name": "'+uploaded.name+'"}', 'application/json'),
            'file': uploaded
        }
        headers = {"Authorization": "Bearer " + creds.token}
        r = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers, files=files
        )
        if r.status_code == 200:
            st.success("File uploaded to your Drive!")
        else:
            st.error("Upload failed: " + r.text)
