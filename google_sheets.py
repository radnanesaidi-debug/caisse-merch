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
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return gspread.authorize(creds)

def get_or_create_spreadsheet():
    client = get_gspread_client()
    return client.open(SPREADSHEET_NAME)

@st.cache_data(ttl=60)
def load_products(_spreadsheet):
    try:
        ws = _spreadsheet.worksheet(SHEET_PRODUCTS)
        return ws.get_all_records()
    except:
        st.error("Impossible de lire l'onglet Produits")
        return []

def record_sale(spreadsheet, stand, product, size, price):
    # 1. Enregistre la vente
    ws_sales = spreadsheet.worksheet(SHEET_SALES)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sale_id = datetime.now().strftime("%H%M%S")
    row = [sale_id, now, stand, product, size, price, 1, price, "VALIDE"]
    ws_sales.append_row(row, value_input_option="USER_ENTERED")

    # 2. Déduction du Stock ultra-précise
    try:
        ws_prod = spreadsheet.worksheet(SHEET_PRODUCTS)
        all_data = ws_prod.get_all_values() # On prend tout pour trouver la ligne
        
        # Mapping des colonnes basé sur ton image :
        # A=Nom(0), B=Prix(1), C=Taille(2), D=Emoji(3), E=Actif(4), F=VVIP(5), G=VIP(6), H=ZONE2(7)
        col_map = {"Stand VVIP": 6, "VIP": 7, "ZONE 2": 8}
        col_idx = col_map.get(stand)

        for i, r in enumerate(all_data):
            if i == 0: continue # Skip header
            # Match Nom ET Taille (sans espaces, sans casse)
            if str(r[0]).strip().lower() == str(product).strip().lower() and \
               str(r[2]).strip().lower() == str(size).strip().lower():
                
                current_stock = int(float(r[col_idx-1] or 0))
                new_stock = max(0, current_stock - 1)
                ws_prod.update_cell(i + 1, col_idx, new_stock)
                st.cache_data.clear() # Reset cache pour mise à jour immédiate
                break
    except Exception as e:
        st.error(f"Erreur mise à jour stock : {e}")

@st.cache_data(ttl=60)
def load_sales(_spreadsheet):
    try:
        ws = _spreadsheet.worksheet(SHEET_SALES)
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=["ID", "Date", "Stand", "Produit", "Taille", "Prix", "Qté", "Total", "Statut"])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def cancel_last_sale(spreadsheet):
    try:
        ws = spreadsheet.worksheet(SHEET_SALES)
        all_vals = ws.get_all_values()
        for i in range(len(all_vals)-1, 0, -1):
            if all_vals[i][8] == "VALIDE":
                ws.update_cell(i+1, 9, "ANNULÉE")
                st.cache_data.clear()
                return True
        return False
    except:
        return False
