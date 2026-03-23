import json
import os
from datetime import datetime

import gspread
from config.settings import (
    GOOGLE_SHEETS_CREDENTIALS,
    GOOGLE_SHEETS_SPREADSHEET_KEY,
)

HEADERS = [
    "Name", "Position", "Company", "Company Website", "Email",
    "Registered At", "Brand Analyzed", "Report Generated At", "Report Filename",
]


def _get_sheet():
    """Authenticate and return the first worksheet of the configured spreadsheet."""
    creds_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        GOOGLE_SHEETS_CREDENTIALS,
    )

    if os.path.exists(creds_path):
        gc = gspread.service_account(filename=creds_path)
    else:
        # Fallback 1: Streamlit secrets (for Streamlit Community Cloud)
        try:
            import streamlit as st
            creds_dict = dict(st.secrets["gcp_service_account"])
            gc = gspread.service_account_from_dict(creds_dict)
        except (ImportError, KeyError, FileNotFoundError):
            # Fallback 2: env var (for other deployed environments)
            creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
            if not creds_json:
                raise RuntimeError(
                    "Google Sheets credentials not found. "
                    "Add gcp_service_account to Streamlit secrets, "
                    "set GOOGLE_SHEETS_CREDENTIALS_JSON env var, "
                    f"or place credentials file at {creds_path}"
                )
            creds_dict = json.loads(creds_json)
            gc = gspread.service_account_from_dict(creds_dict)

    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_KEY)
    worksheet = spreadsheet.sheet1

    # Ensure headers exist
    existing = worksheet.row_values(1)
    if not existing or existing[0] != HEADERS[0]:
        worksheet.update("A1:I1", [HEADERS])

    return worksheet


def save_user(name: str, position: str, company: str, website: str, email: str) -> tuple[bool, str]:
    """Append a new user registration row. Returns (success, error_message)."""
    try:
        sheet = _get_sheet()
        row = [
            name,
            position,
            company,
            website,
            email,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "",  # Brand Analyzed (filled later)
            "",  # Report Generated At (filled later)
            "",  # Report Filename (filled later)
        ]
        sheet.append_row(row, value_input_option="RAW")
        return True, ""
    except Exception as e:
        return False, str(e)


def attach_report(email: str, brand_name: str, report_filename: str) -> bool:
    """Find the user's most recent row by email and attach report details."""
    try:
        sheet = _get_sheet()
        all_values = sheet.get_all_values()

        # Find the last row matching this email (skip header)
        target_row = None
        for i, row in enumerate(all_values):
            if i == 0:
                continue
            if len(row) >= 5 and row[4].strip().lower() == email.strip().lower():
                target_row = i + 1  # 1-indexed for gspread

        if target_row is None:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.update(f"G{target_row}:I{target_row}", [[brand_name, timestamp, report_filename]])
        return True
    except Exception as e:
        print(f"Error attaching report to Google Sheets: {e}")
        return False
