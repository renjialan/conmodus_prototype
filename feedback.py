from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import json
import streamlit as st

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Make Google feedback optional
FEEDBACK_ENABLED = all(
    st.secrets.get(key) for key in ["token", "refresh_token", "token_uri", "client_id", "client_secret"]
)

token_data = None
json_data = None

if FEEDBACK_ENABLED:
    token_data = {
        "token": st.secrets["token"],
        "refresh_token": st.secrets["refresh_token"],
        "token_uri": st.secrets["token_uri"],
        "client_id": st.secrets["client_id"],
        "client_secret": st.secrets["client_secret"],
        "scopes": ["https://www.googleapis.com/auth/spreadsheets"],
        "universe_domain": "googleapis.com",
        "account": "",
        "expiry": "2024-08-06T08:36:06.391636Z",
    }
    json_data = json.loads(json.dumps(token_data))

def append_values(spreadsheet_id, range_name, value_input_option, _values):
    if not FEEDBACK_ENABLED:
        print("Feedback disabled - Google secrets not configured")
        return None

    creds = Credentials.from_authorized_user_info(json_data)
    try:
        service = build("sheets", "v4", credentials=creds)
        body = {"values": _values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )
        print(f"{(result.get('updates').get('updatedCells'))} cells appended.")
        return result

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error
