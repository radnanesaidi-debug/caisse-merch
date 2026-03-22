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
        return []

def record_sale(spreadsheet, stand, product, size, price, mode): # Ajout mode
    ws_sales = spreadsheet.worksheet(SHEET_SALES)
    if not ws_sales.get_all_values():
        headers = ["ID", "Date", "Stand", "Produit", "Taille", "Prix", "Qté", "Total", "Statut", "Mode"]
        ws_sales.append_row(headers)
        
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sale_id = datetime.now().strftime("%H%M%S")
    row = [sale_id, now, stand, product, size, price, 1, price, "VALIDE", mode]
    ws_sales.append_row(row, value_input_option="USER_ENTERED")

    try:
        ws_prod = spreadsheet.worksheet(SHEET_PRODUCTS)
        all_data = ws_prod.get_all_values()
        col_map = {"Stand VVIP": 6, "VIP": 7, "ZONE 2": 8}
        col_idx = col_map.get(stand)

        for i, r in enumerate(all_data):
            if i == 0: continue
            if str(r[0]).strip().lower() == str(product).strip().lower() and \
               str(r[2]).strip().lower() == str(size).strip().lower():
                current_stock = int(float(r[col_idx-1] or 0))
                ws_prod.update_cell(i + 1, col_idx, max(0, current_stock - 1))
                st.cache_data.clear()
                break
    except Exception as e:
        st.error(f"Erreur Stock : {e}")

@st.cache_data(ttl=60)
def load_sales(_spreadsheet):
    try:
        ws = _spreadsheet.worksheet(SHEET_SALES)
        data = ws.get_all_values()
        if len(data) > 1:
            # Ajout de la colonne Mode dans le DataFrame
            return pd.DataFrame(data[1:], columns=["ID", "Date", "Stand", "Produit", "Taille", "Prix", "Qté", "Total", "Statut", "Mode"])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def cancel_last_sale(spreadsheet):
    try:
        ws_sales = spreadsheet.worksheet(SHEET_SALES)
        all_vals = ws_sales.get_all_values()
        for i in range(len(all_vals)-1, 0, -1):
            row_data = all_vals[i]
            if row_data[8] == "VALIDE":
                stand_vendu = row_data[2]
                produit_vendu = row_data[3]
                taille_vendue = row_data[4]
                ws_sales.update_cell(i+1, 9, "ANNULÉE")
                try:
                    ws_prod = spreadsheet.worksheet(SHEET_PRODUCTS)
                    prod_data = ws_prod.get_all_values()
                    col_map = {"Stand VVIP": 6, "VIP": 7, "ZONE 2": 8}
                    col_idx = col_map.get(stand_vendu)
                    for j, r in enumerate(prod_data):
                        if j == 0: continue
                        if str(r[0]).strip().lower() == str(produit_vendu).strip().lower() and \
                           str(r[2]).strip().lower() == str(taille_vendue).strip().lower():
                            current_stock = int(float(r[col_idx-1] or 0))
                            ws_prod.update_cell(j + 1, col_idx, current_stock + 1)
                            break
                except Exception as stock_err:
                    st.error(f"Erreur remise en stock : {stock_err}")
                st.cache_data.clear()
                return True
        return False
    except Exception as e:
        st.error(f"Erreur annulation : {e}")
        return False
