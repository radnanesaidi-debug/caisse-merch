import streamlit as st
import pandas as pd
import plotly.express as px
from google_sheets import get_google_sheet, save_sale
from datetime import datetime

# Configuration
st.set_page_config(page_title="CAISSE MERCHANDISING", layout="wide")

# --- TES DONNÉES OFFICIELLES (À ajuster si besoin) ---
PRODUITS_PRIX = {
    "Tracksuit Black": 650,
    "Tracksuit Red": 650,
    "Never Split Tee": 250,
    "Ana Wydadia": 260,  # Mis à jour selon tes data Sheets
    "Bob": 150,
    "Scarf": 150,
    "Cap": 150
}
STANDS = ["Stand VVIP", "Stand VIP", "ZONE 2"]

st.title("🏟️ CAISSE MERCHANDISING")

# Connexion
sheet, error = get_google_sheet("Ventes")

if error:
    st.error(f"Erreur de connexion : {error}")
else:
    # --- ONGLET NAVIGATION ---
    tab1, tab2 = st.tabs(["🛒 Encaisser", "📊 Dashboard"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            emplacement = st.selectbox("📍 Emplacement", STANDS)
            produit = st.selectbox("👕 Produit", list(PRODUITS_PRIX.keys()))
            taille = st.selectbox("📏 Taille", ["S", "M", "L", "XL", "XXL", "Unique"])
        with col2:
            quantite = st.number_input("🔢 Quantité", min_value=1, value=1)
            # Prix d'office selon le produit
            prix_actuel = PRODUITS_PRIX.get(produit, 200)
            prix_unitaire = st.number_input("💰 Prix Unitaire (DH)", value=prix_actuel)
            mode_paiement = st.radio("💳 Paiement", ["Espèces", "Carte", "Virement"], horizontal=True)

        total = quantite * prix_unitaire
        st.subheader(f"Total à encaisser : {total} DH")

        if st.button("✅ VALIDER LA VENTE", use_container_width=True):
            date_heure = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nouvelle_vente = [date_heure, emplacement, produit, taille, quantite, prix_unitaire, total, mode_paiement]
            if save_sale(nouvelle_vente):
                st.success("Vente enregistrée !")
                st.balloons()

    with tab2:
        st.header("Statistiques en temps réel")
        try:
            # Récupération des données pour le Dashboard
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                
                # KPIs
                total_ca = df['Total'].sum() if 'Total' in df.columns else 0
                st.metric("Chiffre d'Affaires Total", f"{total_ca} DH")

                c1, c2 = st.columns(2)
                with c1:
                    # Graphique par produit
                    fig_prod = px.pie(df, names='Produit', values='Quantité', title="Ventes par Produit")
                    st.plotly_chart(fig_prod, use_container_width=True)
                with c2:
                    # Graphique par stand
                    fig_stand = px.bar(df, x='Stand', y='Total', color='Stand', title="Revenus par Stand")
                    st.plotly_chart(fig_stand, use_container_width=True)
                
                st.dataframe(df.tail(10), use_container_width=True)
            else:
                st.info("Aucune donnée disponible pour le moment.")
        except Exception as e:
            st.error(f"Erreur chargement Dashboard : {e}")
