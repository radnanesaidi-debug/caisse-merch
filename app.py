import streamlit as st
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide")

# CSS personnalisé pour le bouton Rouge et le texte Blanc
st.markdown("""
    <style>
    /* Style du bouton ENCAISSER */
    div.stButton > button:first-child {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
        height: 3.5rem !important;
        font-weight: bold !important;
        font-size: 16px !important;
        text-transform: uppercase;
    }
    div.stButton > button:first-child:hover {
        background-color: #D32F2F !important;
        color: white !important;
    }
    /* Bouton Annuler (Gris) */
    div.stColumn:first-child div.stButton > button {
        background-color: #f0f2f6 !important;
        color: #31333F !important;
        height: 2.5rem !important;
    }
    h3 { font-size: 1.1rem !important; margin-bottom: 0px; }
    .stock-label { font-size: 0.85rem; color: #666; margin-top: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title(f"🏟️ {APP_TITLE}")
    
    try:
        ss = get_or_create_spreadsheet()
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return

    tab_v, tab_d = st.tabs(["🛒 CAISSE", "📊 DASHBOARD"])

    with tab_v:
        c1, c2 = st.columns([1, 4])
        with c1:
            stand = st.radio("Stand actuel :", STAND_NAMES)
            st.divider()
            if st.button("↩️ Annuler vente"):
                if cancel_last_sale(ss):
                    st.success("Dernière vente annulée")
                    time.sleep(1); st.rerun()
        
        with c2:
            raw_p = load_products(ss)
            if not raw_p:
                st.warning("Aucun produit trouvé dans le Google Sheet.")
                return

            # Nettoyage et tri
            noms_uniques = sorted(list(set([str(p['Nom']).strip() for p in raw_p if p['Nom']])))
            cols = st.columns(3)
            
            for i, nom in enumerate(noms_uniques):
                variantes = [p for p in raw_p if str(p['Nom']).strip() == nom]
                p_ref = variantes[0]
                col_stock = f"Stock {stand}"
                
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"### {p_ref.get('Emoji', '📦')} {nom}")
                        
                        # Tailles avec stock > 0
                        tailles_dispo = [v for v in variantes if int(float(v.get(col_stock, 0))) > 0]
                        
                        if tailles_dispo:
                            st.markdown(f"**{p_ref['Prix']} DH**")
                            sz = st.selectbox("Taille", [str(v['Taille']) for v in tailles_dispo], key=f"sz_{i}")
                            
                            # Affichage du stock dynamique
                            stock_val = [int(float(v[col_stock])) for v in tailles_dispo if str(v['Taille']) == sz][0]
                            st.markdown(f"<p class='stock-label'>Reste : {stock_val}</p>", unsafe_allow_html=True)
                            
                            if st.button(f"ENCAISSER", key=f"btn_{i}"):
                                record_sale(ss, stand, nom, sz, p_ref['Prix'])
                                st.toast(f"✅ Vendu : {nom} ({sz})")
                                time.sleep(0.4); st.rerun()
                        else:
                            st.error("🚫 RUPTURE DE STOCK")
                            st.button("EPUISE", disabled=True, key=f"dis_{i}")

    with tab_d:
        df = load_sales(ss)
        if not df.empty:
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
            df_v = df[df['Statut'].str.upper().str.strip() == "VALIDE"]
            if not df_v.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("RECETTE", f"{int(df_v['Total'].sum())} DH")
                m2.metric("ARTICLES", int(len(df_v)))
                m3.metric("STAND ACTIF", stand)
                
                g1, g2 = st.columns(2)
                with g1:
                    st.plotly_chart(px.pie(df_v, values='Total', names='Stand', hole=.4, title="Ventes par Stand"), use_container_width=True)
                with g2:
                    st.plotly_chart(px.bar(df_v.groupby("Produit").size().reset_index(name='Ventes'), x="Produit", y="Ventes", title="Top Produits"), use_container_width=True)
                st.dataframe(df_v.sort_values("Date", ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()
