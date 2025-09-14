import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Google Sheet Connect Test", layout="wide")

# Scopes needed
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)

client = gspread.authorize(creds)

# ---------------- CONNECT USING SHEET ID ----------------
SHEET_ID = "1fv-LQimF2XfCQ936Lj-kIukooQQUCJZOJsoM4SNAdjQ"

try:
    sh = client.open_by_key(SHEET_ID)
    worksheet = sh.get_worksheet(0)  # first worksheet/tab
    st.success(f"✅ Connected to Spreadsheet: {sh.title}")

    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        st.warning("Sheet exists but no data (empty).")
    else:
        st.dataframe(df)

except Exception as e:
    st.error(f"❌ Connection failed: {e}")
