import streamlit as st
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide")

# CSS pour compacter et embellir
st.markdown("""
    <style>
    .stButton button { width: 100%; height: 3rem; font-weight: bold; background-color: #f0f2f6; }
    .stButton button:hover { border-color: #ff4b4b; color: #ff4b4b; }
    h3 { font-size: 1.1rem !important; margin-bottom: 0px; }
    .stock-label { font-size: 0.8rem; color: #666; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title(f"🏟️ {APP_TITLE}")
    
    try:
        ss = get_or_create_spreadsheet()
    except Exception as e:
        st.error(f"Erreur connexion Google : {e}")
        return

    tab_v, tab_d = st.tabs(["🛒 CAISSE", "📊 DASHBOARD"])

    with tab_v:
        c1, c2 = st.columns([1, 4])
        with c1:
            stand = st.radio("Sélection du Stand :", STAND_NAMES)
            st.divider()
            if st.button("↩️ Annuler dernière vente"):
                if cancel_last_sale(ss):
                    st.success("Vente annulée !")
                    time.sleep(1); st.rerun()
        
        with c2:
            raw_p = load_products(ss)
            if not raw_p:
                st.warning("Aucun produit disponible.")
                return

            # Nettoyage et regroupement par nom
            noms_uniques = sorted(list(set([str(p['Nom']).strip() for p in raw_p if p['Nom']])))
            
            cols = st.columns(3) # 3 colonnes pour compacter
            for i, nom in enumerate(noms_uniques):
                # On récupère toutes les tailles pour ce produit
                variantes = [p for p in raw_p if str(p['Nom']).strip() == nom]
                p_ref = variantes[0]
                col_stock = f"Stock {stand}"
                
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"### {p_ref.get('Emoji', '📦')} {nom}")
                        
                        # Filtrer tailles dispos (stock > 0)
                        tailles_dispo = [v for v in variantes if int(float(v.get(col_stock, 0))) > 0]
                        
                        if tailles_dispo:
                            st.markdown(f"**{p_ref['Prix']} DH**")
                            # Selectbox taille
                            options_tailles = [str(v['Taille']) for v in tailles_dispo]
                            sz = st.selectbox("Taille", options_tailles, key=f"sz_{i}")
                            
                            # Affichage du stock spécifique à la taille choisie
                            stock_actuel = [int(float(v[col_stock])) for v in tailles_dispo if str(v['Taille']) == sz][0]
                            st.markdown(f"<p class='stock-label'>Stock restant : {stock_actuel}</p>", unsafe_allow_html=True)
                            
                            if st.button(f"ENCAISSER", key=f"btn_{i}"):
                                record_sale(ss, stand, nom, sz, p_ref['Prix'])
                                st.toast(f"✅ {nom} ({sz}) vendu !")
                                time.sleep(0.5); st.rerun()
                        else:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.error("🚫 SOLD OUT")
                            st.button("RUPTURE", disabled=True, key=f"off_{i}")

    with tab_d:
        df = load_sales(ss)
        if not df.empty:
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
            df_v = df[df['Statut'].str.upper().str.strip() == "VALIDE"]
            if not df_v.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("CA TOTAL", f"{int(df_v['Total'].sum())} DH")
                m2.metric("ARTICLES", int(len(df_v)))
                m3.metric("VENTES", len(df_v))
                
                g1, g2 = st.columns(2)
                with g1:
                    st.plotly_chart(px.pie(df_v, values='Total', names='Stand', hole=.4, title="CA par Stand"), use_container_width=True)
                with g2:
                    st.plotly_chart(px.bar(df_v.groupby("Produit").size().reset_index(name='Nb'), x="Produit", y="Nb", title="Volumes par Produit"), use_container_width=True)
                st.dataframe(df_v.sort_values("Date", ascending=False), use_container_width=True)
            else:
                st.info("En attente de ventes validées...")
        else:
            st.info("Le Dashboard sera prêt après la première vente.")

if __name__ == "__main__":
    main()
