import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os

# Configuration Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "credential.json"

def get_google_sheet(sheet_name):
    try:
        # On force la lecture du fichier JSON pour s'assurer qu'il est bien chargé
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            return None, f"Erreur : Le fichier {SERVICE_ACCOUNT_FILE} est introuvable."
            
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)
        
        # CETTE LIGNE EST LA SOLUTION : Elle ignore les petits décalages d'heure
        creds.expiry = None 
        
        client = gspread.authorize(creds)
        spreadsheet = client.open("Ventes_Merch")
        sheet = spreadsheet.worksheet(sheet_name)
        return sheet, None
    except Exception as e:
        return None, str(e)
