import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

def get_google_sheet(sheet_name):
    try:
        # On récupère le secret
        res = st.secrets["gcp_service_account"]
        
        # Si c'est une chaîne (le JSON complet), on le décode
        if isinstance(res, str):
            service_account_info = json.loads(res)
        else:
            # Si Streamlit l'a déjà converti en dictionnaire
            service_account_info = dict(res)
        
        # --- RÉPARATION CRITIQUE DE LA CLÉ ---
        if "private_key" in service_account_info:
            service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Nom exact de ton fichier vu sur ta capture
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
