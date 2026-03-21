import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

def get_google_sheet(sheet_name):
    try:
        # Utilise les secrets configurés dans Streamlit Cloud
        info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(info)
        
        client = gspread.authorize(creds)
        
        # NOM DU FICHIER CORRIGÉ ICI
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
