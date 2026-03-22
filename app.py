import streamlit as st
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏟️")

st.markdown("""
    <style>
    .stButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        height: 3.5rem !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #D32F2F !important;
        transform: scale(1.02);
    }
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        border-radius: 15px !important;
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        padding-top: 50px;
        margin-bottom: 10px;
    }
    .logo-img { width: 80px; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    h3 { color: #1E1E1E; margin-bottom: 5px !important; }
    .stock-label { font-weight: bold; padding: 4px 8px; background: #f8f9fa; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.markdown("""<div class="logo-container"><img src="https://i.ibb.co/C3Chk581/votre-image.png" class="logo-img"></div>""", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; margin-top: -5px;'> {APP_TITLE}</h2>", unsafe_allow_html=True)
    
    try:
        ss = get_or_create_spreadsheet()
    except Exception as e:
        st.error(f"Erreur connexion : {e}")
        return

    # --- AJOUT DE L'ONGLET TRANSFERTS ---
    tab_v, tab_t, tab_d = st.tabs(["🛒 ESPACE CAISSE", "🔄 TRANSFERTS", "📊 STATISTIQUES LIVE"])

    with tab_v:
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown("### ⚙️ RÉGLAGES")
            stand = st.radio("Stand Actif :", STAND_NAMES)
            mode_paye = st.radio("Mode de Paiement :", PAYMENT_MODES)
            st.divider()
            if st.button("↩️ Annuler Vente"):
                if cancel_last_sale(ss):
                    st.success("Annulé !")
                    time.sleep(0.5); st.rerun()
        
        with c2:
            raw_p = load_products(ss)
            if not raw_p:
                st.warning("Vérifie ton fichier Produits.")
                return

            noms_uniques = sorted(list(set([str(p['Nom']).strip() for p in raw_p if p['Nom']])))
            cols = st.columns(3)
            
            for i, nom in enumerate(noms_uniques):
                variantes = [p for p in raw_p if str(p['Nom']).strip() == nom]
                p_ref = variantes[0]
                col_stock = f"Stock {stand}"
                
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"### {p_ref.get('Emoji', '📦')} {nom}")
                        tailles_dispo = [v for v in variantes if int(float(v.get(col_stock, 0))) > 0]
                        
                        if tailles_dispo:
                            st.markdown(f"#### {p_ref['Prix']} DH")
                            sz = st.selectbox("Taille", [str(v['Taille']) for v in tailles_dispo], key=f"sz_{i}")
                            stock_val = [int(float(v[col_stock])) for v in tailles_dispo if str(v['Taille']) == sz][0]
                            color = "green" if stock_val > 5 else "orange"
                            st.markdown(f"Stock : <span class='stock-label' style='color:{color}'>{stock_val} unités</span>", unsafe_allow_html=True)
                            
                            if st.button(f"ENCAISSER ({mode_paye})", key=f"btn_{i}"):
                                record_sale(ss, stand, nom, sz, p_ref['Prix'], mode_paye)
                                st.toast(f"✅ {nom} - {mode_paye}")
                                time.sleep(0.4); st.rerun()
                        else:
                            st.error("🚫 RUPTURE")
                            st.button("ÉPUISÉ", disabled=True, key=f"off_{i}")

    # --- CONTENU ONGLET TRANSFERTS ---
    with tab_t:
        st.markdown("### 📦 TRANSFERT DE STOCK")
        raw_p = load_products(ss)
        if raw_p:
            n_uniques = sorted(list(set([str(p['Nom']).strip() for p in raw_p if p['Nom']])))
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                t_prod = st.selectbox("Produit", n_uniques)
                t_sizes = [str(p['Taille']) for p in raw_p if str(p['Nom']).strip() == t_prod]
                t_sz = st.selectbox("Taille ", t_sizes)
            with t_col2:
                t_from = st.selectbox("DE :", STAND_NAMES)
                t_to = st.selectbox("VERS :", [s for s in STAND_NAMES if s != t_from])
            
            t_qty = st.number_input("Quantité", min_value=1, step=1)
            if st.button("🚀 CONFIRMER LE TRANSFERT", use_container_width=True):
                ok, res = process_transfer(ss, t_prod, t_sz, t_from, t_to, t_qty)
                if ok:
                    st.success(res)
                    time.sleep(1); st.rerun()
                else: st.error(res)

    with tab_d:
        df = load_sales(ss)
        if not df.empty:
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
            df_v = df[df['Statut'].str.upper().str.strip() == "VALIDE"]
            
            if not df_v.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("💰 CA TOTAL", f"{int(df_v['Total'].sum())} DH")
                m2.metric("💳 TOTAL TPE", f"{int(df_v[df_v['Mode'] == 'TPE']['Total'].sum())} DH")
                m3.metric("💵 TOTAL ESPECE", f"{int(df_v[df_v['Mode'] == 'ESPECE']['Total'].sum())} DH")
                
                st.divider()
                st.markdown("### 📊 Détail par Stand et Mode")
                fig_pay = px.bar(df_v, x="Stand", y="Total", color="Mode", barmode="group",
                               color_discrete_map={"ESPECE": "#4CAF50", "TPE": "#2196F3"})
                st.plotly_chart(fig_pay, use_container_width=True)

                g1, g2 = st.columns(2)
                with g1:
                    st.plotly_chart(px.pie(df_v, values='Total', names='Mode', hole=.4, title="Global : TPE vs ESPECE"), use_container_width=True)
                with g2:
                    st.plotly_chart(px.bar(df_v.groupby("Produit").size().reset_index(name='Nb'), x="Produit", y="Nb", title="Volumes par Produit"), use_container_width=True)
                
                with st.expander("📄 Historique complet"):
                    st.dataframe(df_v.sort_values("Date", ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()
