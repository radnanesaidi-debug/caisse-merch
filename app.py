import streamlit as st
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide")

# CSS pour compacter l'affichage
st.markdown("""
    <style>
    .stButton button { width: 100%; padding: 0.2rem; font-size: 14px; }
    h3 { font-size: 18px !important; margin-bottom: 5px; }
    .stSelectbox { margin-bottom: -15px; }
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
            stand = st.radio("Stand :", STAND_NAMES)
            if st.button("↩️ Annuler"):
                if cancel_last_sale(ss):
                    st.success("Annulé !")
                    time.sleep(1); st.rerun()
        
        with c2:
            all_p = load_products(ss)
            # On regroupe par nom pour l'affichage
            noms_produits = sorted(list(set([p['Nom'] for p in all_p])))
            
            # Affichage en 3 colonnes pour gagner de la place
            cols = st.columns(3)
            for i, nom in enumerate(noms_produits):
                # Variantes du même produit (différentes tailles)
                variantes = [p for p in all_p if p['Nom'] == nom]
                p_ref = variantes[0]
                col_stock = f"Stock {stand}"
                
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"### {p_ref['Emoji']} {nom}")
                        
                        # Filtrer les tailles qui ont du stock > 0
                        tailles_dispo = [v for v in variantes if int(v.get(col_stock, 0)) > 0]
                        
                        if tailles_dispo:
                            st.caption(f"Prix: {p_ref['Prix']} DH")
                            sz = st.selectbox(f"Taille", [v['Taille'] for v in tailles_dispo], key=f"sz_{i}")
                            if st.button(f"ENCAISSER", key=f"btn_{i}"):
                                record_sale(ss, stand, nom, sz, p_ref['Prix'])
                                st.toast(f"✅ Vendu: {nom}")
                                time.sleep(0.5); st.rerun()
                        else:
                            st.error("🚫 SOLD OUT")
                            st.button("EPUISE", disabled=True, key=f"dis_{i}")

    with tab_d:
        df = load_sales(ss)
        if not df.empty:
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
            df['Qté'] = pd.to_numeric(df['Qté'], errors='coerce').fillna(0)
            df_v = df[df['Statut'].str.upper().str.strip() == "VALIDE"]
            if not df_v.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("RECETTE", f"{int(df_v['Total'].sum())} DH")
                m2.metric("ARTICLES", int(df_v['Qté'].sum()))
                m3.metric("VENTES", len(df_v))
                g1, g2 = st.columns(2)
                with g1:
                    st.plotly_chart(px.pie(df_v, values='Total', names='Stand', hole=.4), use_container_width=True)
                with g2:
                    st.plotly_chart(px.bar(df_v.groupby("Produit")["Qté"].sum().reset_index(), x="Produit", y="Qté"), use_container_width=True)
                st.dataframe(df_v.sort_values("Date", ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()
