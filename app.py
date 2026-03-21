import streamlit as st
import pandas as pd
from google_sheets import get_google_sheet, save_sale
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="CAISSE MERCHANDISING", layout="wide")

# --- TES DONNÉES OFFICIELLES ---
# Liste des produits avec leurs prix par défaut
PRODUITS_PRIX = {
    "Tracksuit Black": 650,
    "Never Split Tee": 250,
    "Ana Wydadia": 200,
    "Bob": 150,
    "Scarf": 150,
    "Cap": 150
}

STANDS = ["Stand VVIP", "Stand VIP", "ZONE 2"]
TAILLES = ["S", "M", "L", "XL", "XXL", "Unique"]

# Interface
st.title("🏟️ CAISSE MERCHANDISING")

# Connexion au Sheet (onglet "Ventes")
sheet, error = get_google_sheet("Ventes")

if error:
    st.error(f"Erreur de connexion : {error}")
else:
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            emplacement = st.selectbox("📍 Emplacement", STANDS)
            produit = st.selectbox("👕 Produit", list(PRODUITS_PRIX.keys()))
            taille = st.selectbox("📏 Taille", TAILLES)

        with col2:
            quantite = st.number_input("🔢 Quantité", min_value=1, value=1)
            # Le prix s'adapte automatiquement selon le produit choisi
            prix_defaut = PRODUITS_PRIX[produit]
            prix_unitaire = st.number_input("💰 Prix Unitaire (DH)", min_value=0, value=prix_defaut)
            mode_paiement = st.radio("💳 Paiement", ["Espèces", "Carte", "Virement"])

    total = quantite * prix_unitaire
    st.markdown(f"### Total à encaisser : `{total} DH`")

    if st.button("✅ VALIDER LA VENTE", use_container_width=True):
        date_heure = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Structure de la ligne pour ton Google Sheet
        nouvelle_vente = [date_heure, emplacement, produit, taille, quantite, prix_unitaire, total, mode_paiement]
        
        if save_sale(nouvelle_vente):
            st.success(f"Vente de {produit} enregistrée !")
            st.balloons()
        else:
            st.error("Erreur lors de l'enregistrement sur Google Sheets.")

# --- SECTION HISTORIQUE RAPIDE ---
st.divider()
if st.checkbox("Afficher les dernières ventes"):
    try:
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df.tail(10), use_container_width=True)
    except:
        st.write("Aucune donnée à afficher pour le moment.")
