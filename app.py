import streamlit as st
import pandas as pd
from google_sheets import get_google_sheet, save_sale
from datetime import datetime

# Titre de l'application
APP_TITLE = "CAISSE MERCHANDISING"

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(f"🏟️ {APP_TITLE}")

# Initialisation de la connexion
sheet, error = get_google_sheet("Ventes")

if error:
    st.error(f"⚠️ Erreur de connexion Google : {error}")
    st.info("Astuce : Vérifie que ton fichier Google Sheet s'appelle bien 'Ventes_Merch'.")
else:
    # --- FORMULAIRE DE VENTE ---
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            emplacement = st.selectbox("📍 Emplacement", ["Stand VVIP", "Stand VIP", "Stand Tribune", "Stand Pelouse"])
            produit = st.selectbox("👕 Produit", ["Tracksuit Black", "Bob", "Scarf", "Never Split Tee", "Ana Wydadia"])
            taille = st.selectbox("📏 Taille", ["S", "M", "L", "XL", "XXL", "Unique"])

        with col2:
            quantite = st.number_input("🔢 Quantité", min_value=1, value=1)
            prix_unitaire = st.number_input("💰 Prix Unitaire (DH)", min_value=0, value=200)
            mode_paiement = st.radio("💳 Paiement", ["Espèces", "Carte", "Virement"])

    total = quantite * prix_unitaire
    st.subheader(f"Total : {total} DH")

    if st.button("✅ Valider la vente", use_container_width=True):
        date_heure = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nouvelle_vente = [date_heure, emplacement, produit, taille, quantite, prix_unitaire, total, mode_paiement]
        
        if save_sale(nouvelle_vente):
            st.success("Vente enregistrée avec succès !")
            st.balloons()
        else:
            st.error("Erreur lors de l'enregistrement.")
