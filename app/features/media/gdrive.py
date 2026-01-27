import os
import httpx
from typing import Dict, Any, Optional

from google.oauth2 import service_account
from google.auth.transport.requests import Request
from app.core.config import settings


class GDriveError(Exception):
    pass

def _access_token() -> str:
    if not settings.GSA_JSON_PATH:
        raise GDriveError("GOOGLE_APPLICATION_CREDENTIALS_MISSING")
    creds = service_account.Credentials.from_service_account_file(settings.GSA_JSON_PATH, scopes=settings.SCOPES)
    creds.refresh(Request())
    return creds.token

async def create_resumable_upload_session(file_name: str, mime_type: str, size_bytes: int) -> str:
    """
    Returns upload_url (session URL).
    Client will PUT bytes to this URL.
    """
    token = _access_token()
    if not settings.GDRIVE_FOLDER_ID:
        raise GDriveError("GDRIVE_FOLDER_ID_MISSING")

    meta = {
        "name": file_name,
        "parents": [settings.GDRIVE_FOLDER_ID],
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": mime_type,
        "X-Upload-Content-Length": str(size_bytes),
    }

    url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=meta)
        if r.status_code >= 400:
            raise GDriveError(f"RESUMABLE_INIT_FAILED: {r.status_code} {r.text[:300]}")
        upload_url = r.headers.get("Location")
        if not upload_url:
            raise GDriveError("RESUMABLE_LOCATION_MISSING")
        return upload_url

async def get_file_meta(file_id: str) -> Dict[str, Any]:
    token = _access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=id,name,size,mimeType,webViewLink,webContentLink"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers)
        if r.status_code >= 400:
            raise GDriveError(f"GET_FILE_META_FAILED: {r.status_code} {r.text[:200]}")
        return r.json()

async def download_file_bytes(file_id: str) -> bytes:
    token = _access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, headers=headers)
        if r.status_code >= 400:
            raise GDriveError(f"DOWNLOAD_FAILED: {r.status_code} {r.text[:200]}")
        return r.content
