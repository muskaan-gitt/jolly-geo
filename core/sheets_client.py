import os
from datetime import datetime

import gspread
from config.settings import (
    GOOGLE_SHEETS_CREDENTIALS,
    GOOGLE_SHEETS_SPREADSHEET_KEY,
)

HEADERS = [
    "Name", "Position", "Company", "Email",
    "Registered At", "Brand Analyzed", "Report Generated At", "Report Filename",
]


def _get_sheet():
    """Authenticate and return the first worksheet of the configured spreadsheet."""
    creds_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        GOOGLE_SHEETS_CREDENTIALS,
    )
    gc = gspread.service_account(filename=creds_path)
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_KEY)
    worksheet = spreadsheet.sheet1

    # Ensure headers exist
    existing = worksheet.row_values(1)
    if not existing or existing[0] != HEADERS[0]:
        worksheet.update("A1:H1", [HEADERS])

    return worksheet


def save_user(name: str, position: str, company: str, email: str) -> bool:
    """Append a new user registration row. Returns True on success."""
    try:
        sheet = _get_sheet()
        row = [
            name,
            position,
            company,
            email,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "",  # Brand Analyzed (filled later)
            "",  # Report Generated At (filled later)
            "",  # Report Filename (filled later)
        ]
        sheet.append_row(row, value_input_option="RAW")
        return True
    except Exception as e:
        print(f"Error saving user to Google Sheets: {e}")
        return False


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
            if len(row) >= 4 and row[3].strip().lower() == email.strip().lower():
                target_row = i + 1  # 1-indexed for gspread

        if target_row is None:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.update(f"F{target_row}:H{target_row}", [[brand_name, timestamp, report_filename]])
        return True
    except Exception as e:
        print(f"Error attaching report to Google Sheets: {e}")
        return False
