import os
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Sana",
    "Telegram ID",
    "Username",
    "Ism Familiya",
    "Startup nomi",
    "Telefon",
    "Loyiha fayli",
]

_COMMA_DECIMAL_LANGS = {
    "ru", "de", "fr", "es", "it", "nl", "pt", "pl", "cs",
    "tr", "uk", "fi", "sv", "da", "no", "uz", "kk",
}

_locale_cache: str | None = None


def _client() -> gspread.Client:
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    return gspread.authorize(creds)


def _worksheet() -> gspread.Worksheet:
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    sh = _client().open_by_key(sheet_id)
    ws = sh.sheet1
    if ws.row_count == 0 or not ws.row_values(1):
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
    return ws


def _formula_sep(sh: gspread.Spreadsheet) -> str:
    global _locale_cache
    if _locale_cache is None:
        meta = sh.fetch_sheet_metadata(params={"fields": "properties.locale"})
        _locale_cache = meta["properties"].get("locale", "en_US")
    lang = _locale_cache.split("_")[0].lower()
    return ";" if lang in _COMMA_DECIMAL_LANGS else ","


def append_application(data: dict) -> None:
    ws = _worksheet()
    file_name = (data.get("file_name", "") or "fayl").replace('"', "'")
    file_link = data.get("file_link", "")

    if file_link:
        sep = _formula_sep(ws.spreadsheet)
        file_cell = f'=HYPERLINK("{file_link}"{sep} "{file_name}")'
    else:
        file_cell = file_name

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        str(data.get("user_id", "")),
        data.get("username", ""),
        data.get("full_name", ""),
        data.get("startup_name", ""),
        data.get("phone", ""),
        file_cell,
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")
