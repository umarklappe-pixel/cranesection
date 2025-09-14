import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Google Sheets Test", layout="wide")

# Scopes required
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)

# Authorize gspread
client = gspread.authorize(creds)

# ---------------- CONNECT TO SHEET ----------------
# ⚠️ Replace this with your actual sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"

try:
    sheet = client.open_by_url(SHEET_URL)
    worksheet = sheet.get_worksheet(0)  # first sheet
    st.success(f"✅ Connected to: {sheet.title}")

    # Load records into DataFrame
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        st.warning("Sheet is empty. Try adding some rows.")
    else:
        st.dataframe(df)

except Exception as e:
    st.error(f"❌ Failed to connect: {e}")
