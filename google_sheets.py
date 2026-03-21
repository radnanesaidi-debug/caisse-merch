import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

def get_google_sheet(sheet_name):
    try:
        # On lit le secret comme une chaîne de caractères JSON
        service_account_info = json.loads(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(service_account_info)
        
        client = gspread.authorize(creds)
        
        # On utilise ton vrai nom de fichier
        spreadsheet = client.open("Caisse_Merchandising")
        sheet = spreadsheet.worksheet(sheet_name)
        return sheet, None
    except Exception as e:
        return None, str(e)

def save_sale(data, sheet_name="Ventes"):
    sheet, error = get_google_sheet(sheet_name)
    if sheet:
        sheet.append_row(data)
        return True
    return False
