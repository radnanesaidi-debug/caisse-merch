# ... (Gardez tout le début identique jusqu'à record_sale)

def record_sale(spreadsheet, stand, product, size, price, mode, vendeur):
    try:
        # On vérifie la connexion avant de commencer
        ws_sales = spreadsheet.worksheet("Ventes")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sale_id = datetime.now().strftime("%H%M%S")
        
        row = [sale_id, now, stand, product, size, price, 1, price, "VALIDE", mode, vendeur]
        
        # Tentative d'écriture avec timeout visuel
        ws_sales.append_row(row, value_input_option="USER_ENTERED")

        ws_prod = spreadsheet.worksheet("Produits")
        headers = ws_prod.row_values(1)
        col_name = f"Stock {stand}"
        
        if col_name not in headers:
            st.error(f"⚠️ Colonne '{col_name}' introuvable !")
            return

        col_idx = headers.index(col_name) + 1
        all_data = ws_prod.get_all_values()

        for i, r in enumerate(all_data):
            if i == 0: continue
            if str(r[0]).strip().lower() == str(product).strip().lower() and \
               str(r[2]).strip().lower() == str(size).strip().lower():
                curr_stock = int(float(r[col_idx-1] or 0))
                ws_prod.update_cell(i + 1, col_idx, max(0, curr_stock - 1))
                break
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"🚨 Erreur de connexion : La vente n'a pas pu être enregistrée. Vérifiez votre internet. ({e})")
        return False

# ... (Le reste des fonctions process_transfer et cancel_last_sale reste identique)
