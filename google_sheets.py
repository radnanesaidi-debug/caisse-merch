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
        # On utilise le nom direct de l'onglet pour éviter les erreurs de config
        ws = _spreadsheet.worksheet("Produits")
        return ws.get_all_records()
    except:
        return []

@st.cache_data(ttl=20)
def load_sales(_spreadsheet):
    try:
        # CORRECTION : Ton onglet s'appelle "Ventes" sur la capture
        ws = _spreadsheet.worksheet("Ventes")
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=20)
def load_transfers(_spreadsheet):
    try:
        # CORRECTION : Ton onglet s'appelle "Transferts" sur la capture
        ws = _spreadsheet.worksheet("Transferts")
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def record_sale(spreadsheet, stand, product, size, price, mode):
    try:
        ws_sales = spreadsheet.worksheet("Ventes")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sale_id = datetime.now().strftime("%H%M%S")
        
        # Ordre des colonnes selon ta capture : ID, Date, Stand, Produit, Taille, Prix, Qté, Total, Statut, Mode
        row = [sale_id, now, stand, product, size, price, 1, price, "VALIDE", mode]
        ws_sales.append_row(row, value_input_option="USER_ENTERED")

        # Mise à jour Stock (Colonnes F, G, H d'après tes messages précédents)
        ws_prod = spreadsheet.worksheet("Produits")
        all_data = ws_prod.get_all_values()
        col_map = {"Stand VVIP": 6, "VIP": 7, "ZONE 2": 8}
        col_idx = col_map.get(stand)

        for i, r in enumerate(all_data):
            if i == 0: continue
            if str(r[0]).strip().lower() == str(product).strip().lower() and \
               str(r[2]).strip().lower() == str(size).strip().lower():
                curr_stock = int(float(r[col_idx-1] or 0))
                ws_prod.update_cell(i + 1, col_idx, max(0, curr_stock - 1))
                break
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur technique : {e}")

def process_transfer(spreadsheet, product, size, from_stand, to_stand, qty):
    try:
        ws_prod = spreadsheet.worksheet("Produits")
        all_data = ws_prod.get_all_values()
        col_map = {"Stand VVIP": 6, "VIP": 7, "ZONE 2": 8}
        col_from, col_to = col_map.get(from_stand), col_map.get(to_stand)

        for i, r in enumerate(all_data):
            if i == 0: continue
            if str(r[0]).strip().lower() == str(product).strip().lower() and \
               str(r[2]).strip().lower() == str(size).strip().lower():
                
                s_from = int(float(r[col_from-1] or 0))
                s_to = int(float(r[col_to-1] or 0))
                if s_from < qty: return False, "Stock insuffisant"

                ws_prod.update_cell(i + 1, col_from, s_from - qty)
                ws_prod.update_cell(i + 1, col_to, s_to + qty)
                
                # Log Transfert (Colonnes selon ta capture : Date, Produit, Taille, De, Vers, Quantité)
                ws_t = spreadsheet.worksheet("Transferts")
                ws_t.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), product, size, from_stand, to_stand, qty])
                
                st.cache_data.clear()
                return True, "Transfert validé"
        return False, "Produit non trouvé"
    except Exception as e:
        return False, str(e)

def cancel_last_sale(spreadsheet):
    try:
        ws_sales = spreadsheet.worksheet("Ventes")
        all_vals = ws_sales.get_all_values()
        for i in range(len(all_vals)-1, 0, -1):
            if all_vals[i][8] == "VALIDE": # Colonne Statut
                stand_v, prod_v, size_v = all_vals[i][2], all_vals[i][3], all_vals[i][4]
                ws_sales.update_cell(i+1, 9, "ANNULÉE") # Colonne I (9)
                
                # Remise en stock
                ws_prod = spreadsheet.worksheet("Produits")
                p_data = ws_prod.get_all_values()
                col_map = {"Stand VVIP": 6, "VIP": 7, "ZONE 2": 8}
                col_idx = col_map.get(stand_v)
                for j, r in enumerate(p_data):
                    if j == 0: continue
                    if str(r[0]).strip().lower() == str(prod_v).strip().lower() and \
                       str(r[2]).strip().lower() == str(size_v).strip().lower():
                        curr = int(float(r[col_idx-1] or 0))
                        ws_prod.update_cell(j + 1, col_idx, curr + 1)
                        break
                st.cache_data.clear()
                return True
        return False
    except:
        return False
