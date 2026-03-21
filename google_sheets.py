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

def load_products(spreadsheet):
    try:
        ws = spreadsheet.worksheet(SHEET_PRODUCTS)
        return ws.get_all_records()
    except:
        return DEFAULT_PRODUCTS

def record_sale(spreadsheet, stand, product, size, price):
    # 1. Enregistre la vente
    ws_sales = spreadsheet.worksheet(SHEET_SALES)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sale_id = datetime.now().strftime("%H%M%S")
    row = [sale_id, now, stand, product, size, price, 1, price, "VALIDE"]
    ws_sales.append_row(row, value_input_option="USER_ENTERED")

    # 2. Déduction du Stock
    try:
        ws_prod = spreadsheet.worksheet(SHEET_PRODUCTS)
        all_prods = ws_prod.get_all_values()
        
        # On cherche la ligne qui correspond au Produit ET à la Taille
        for idx, r in enumerate(all_prods):
            if r[0] == product and r[1] == str(size):
                col_map = {"Stand VVIP": 5, "VIP": 6, "ZONE 2": 7}
                col_idx = col_map.get(stand)
                current_stock = int(r[col_idx-1])
                ws_prod.update_cell(idx + 1, col_idx, current_stock - 1)
                break
    except Exception as e:
        st.error(f"Erreur stock : {e}")

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
