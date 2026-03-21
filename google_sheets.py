import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json

def get_google_sheet(sheet_name):
    try:
        # 1. On charge le JSON depuis les secrets
        service_account_info = json.loads(st.secrets["gcp_service_account"])
        
        # 2. Définition des permissions (Scopes) standard
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # 3. Création des credentials avec les bons scopes
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        
        # 4. Connexion
        client = gspread.authorize(creds)
        
        # 5. Ouverture du fichier
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
