import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

def get_google_sheet(sheet_name):
    try:
        # Récupération du secret
        res = st.secrets["gcp_service_account"]
        info = json.loads(res) if isinstance(res, str) else dict(res)
        
        # Nettoyage automatique de la clé privée
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")

        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(creds)
        
        return client.open("Caisse_Merchandising").worksheet(sheet_name), None
    except Exception as e:
        return None, str(e)

def save_sale(data, sheet_name="Ventes"):
    sheet, error = get_google_sheet(sheet_name)
    if sheet:
        sheet.append_row(data)
        return True
    return False
