import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os

# Configuration Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "credential.json"

def get_google_sheet(sheet_name):
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            return None, f"Fichier {SERVICE_ACCOUNT_FILE} introuvable."
            
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)
        # Buffer pour éviter les erreurs de signature (JWT)
        creds.expiry = None 
        
        client = gspread.authorize(creds)
        # Assure-toi que ton fichier s'appelle exactement comme ça sur Google Drive
        spreadsheet = client.open("Ventes_Merch")
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
        return None, str(e)
