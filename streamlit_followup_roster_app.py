from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ---------- CONFIG ----------
# Replace with your Drive folder ID
FOLDER_ID = "1v3NjAC6RwtmUrsR2qtzDLPw6hcDJzqSU"

# Google Drive API scopes
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Load credentials from service account JSON
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

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


# ---------- TEST ----------
if __name__ == "__main__":
    # Example: upload a test image
    result = upload_to_drive("test_image.jpg", "MyUploadedImage.jpg", FOLDER_ID)
    print("✅ Uploaded successfully!")
    print("Web Link:", result["webViewLink"])
    print("Direct Image Link:", result["directLink"])
