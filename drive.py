import io
import os

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _service():
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_file(content: bytes, filename: str, mime_type: str | None = None) -> str:
    """Upload bytes to Drive, make it readable by anyone with link, return webViewLink."""
    svc = _service()

    metadata = {"name": filename}
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(
        io.BytesIO(content),
        mimetype=mime_type or "application/octet-stream",
        resumable=False,
    )

    file = svc.files().create(
        body=metadata,
        media_body=media,
        fields="id, webViewLink",
        supportsAllDrives=True,
    ).execute()

    svc.permissions().create(
        fileId=file["id"],
        body={"role": "reader", "type": "anyone"},
        supportsAllDrives=True,
    ).execute()

    return file["webViewLink"]
