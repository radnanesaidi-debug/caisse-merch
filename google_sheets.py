import gspread
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from config import *

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource(ttl=1200)
def get_gspread_client():
    # MÉTHODE SECRETS : On lit le JSON depuis la mémoire de Streamlit
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    # Nettoyage de la clé (évite l'erreur de signature)
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return gspread.authorize(creds)

def get_or_create_spreadsheet():
    client = get_gspread_client()
    return client.open(SPREADSHEET_NAME)

def load_products(spreadsheet):
    try:
        ws = spreadsheet.worksheet(SHEET_PRODUCTS)
        records = ws.get_all_records()
        return records if records else DEFAULT_PRODUCTS
    except:
        return DEFAULT_PRODUCTS

def record_sale(spreadsheet, stand, product, size, price):
    ws = spreadsheet.worksheet(SHEET_SALES)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sale_id = datetime.now().strftime("%H%M%S")
    # Ordre : ID, Date, Stand, Produit, Taille, Prix, Qté, Total, Statut
    row = [sale_id, now, stand, product, size, price, 1, price, "VALIDE"]
    ws.append_row(row, value_input_option="USER_ENTERED")

def load_sales(spreadsheet):
    try:
        ws = spreadsheet.worksheet(SHEET_SALES)
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=["ID", "Date", "Stand", "Produit", "Taille", "Prix", "Qté", "Total", "Statut"])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def cancel_last_sale(spreadsheet):
    ws = spreadsheet.worksheet(SHEET_SALES)
    all_vals = ws.get_all_values()
    for i in range(len(all_vals)-1, 0, -1):
        if all_vals[i][8] == "VALIDE":
            ws.update_cell(i+1, 9, "ANNULÉE")
            return True
    return False
