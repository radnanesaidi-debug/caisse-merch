import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏟️")

def trigger_vibration():
    components.html("<script>if (window.navigator && window.navigator.vibrate) { window.navigator.vibrate(50); }</script>", height=0)

st.markdown("""
    <style>
    header { visibility: hidden; height: 0px !important; }
    #MainMenu { visibility: hidden; }
    .stDeployButton { display: none; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f0f2f6; border-radius: 8px 8px 0px 0px; font-weight: 800; flex-grow: 1; }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
    .stButton > button { border-radius: 6px !important; height: 2.8rem !important; font-weight: 800; }
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] { padding: 10px !important; border-radius: 10px !important; }
    .logo-container { display: flex; justify-content: center; padding-top: 5px; }
    .logo-img { width: 60px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- GESTION DU VENDEUR ---
    if "vendeur" not in st.session_state:
        st.session_state.vendeur = None

    if st.session_state.vendeur is None:
        st.markdown(f"""<div class="logo-container"><img src="https://i.ibb.co/C3Chk581/votre-image.png" class="logo-img"></div>""", unsafe_allow_html=True)
        st.subheader("👤 Qui utilise la caisse ?")
        v_choisi = st.selectbox("Sélectionnez votre nom :", VENDEURS)
        if st.button("OUVRIR LA SESSION", use_container_width=True):
            st.session_state.vendeur = v_choisi
            st.rerun()
        st.stop()

    # --- LOGIQUE NORMALE ---
    if "stand" not in st.query_params:
        st.query_params["stand"] = STAND_NAMES[0]
    current_stand = st.query_params["stand"]

    st.markdown(f"""<div class="logo-container"><img src="https://i.ibb.co/C3Chk581/votre-image.png" class="logo-img"></div>""", unsafe_allow_html=True)
    st.caption(f"Connecté : **{st.session_state.vendeur}**")
    
    try:
        ss = get_or_create_spreadsheet()
    except:
        st.error("🚨 Connexion Google Sheets impossible")
        return

    tab_v, tab_t, tab_d = st.tabs(["🛒 CAISSE", "🔄 TRANSFERTS", "📊 STATS"])

    with tab_v:
        r1, r2, r3 = st.columns([1.5, 1, 1])
        with r1:
            new_stand = st.selectbox("STAND :", STAND_NAMES, index=STAND_NAMES.index(current_stand), label_visibility="collapsed")
            if new_stand != current_stand:
                st.query_params["stand"] = new_stand
                st.rerun()
        with r2:
            show_img = st.toggle("Photos", value=False)
        with r3:
            if st.button("↩️ Annul"):
                if cancel_last_sale(ss, st.session_state.vendeur):
                    st.toast("Ta dernière vente est annulée !")
                    time.sleep(0.5); st.rerun()
                else:
                    st.error("Aucune vente à annuler")

        st.divider()
        raw_p = load_products(ss)
        if not raw_p: return
        
        noms_uniques = sorted(list(set([str(p['Nom']).strip() for p in raw_p if p['Nom']])))
        cols = st.columns(3) 
        
        for i, nom in enumerate(noms_uniques):
            variantes = [p for p in raw_p if str(p['Nom']).strip() == nom]
            p_ref = variantes[0]
            col_stock_name = f"Stock {current_stand}"
            with cols[i % 3]:
                with st.container(border=True):
                    if show_img and p_ref.get('Image'): st.image(p_ref['Image'], use_container_width=True)
                    st.markdown(f"**{nom}**")
                    tailles_dispo = [v for v in variantes if int(float(v.get(col_stock_name, 0))) > 0]
                    if tailles_dispo:
                        sz = st.selectbox("T", [str(v['Taille']) for v in tailles_dispo], key=f"sz_{i}", label_visibility="collapsed")
                        v_sel = [v for v in tailles_dispo if str(v['Taille']) == sz][0]
                        stock_val = int(float(v_sel[col_stock_name]))
                        st.markdown(f"**{p_ref['Prix']} DH** | Stock: `{stock_val}`")
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("💵", key=f"esp_{i}"):
                                record_sale(ss, current_stand, nom, sz, p_ref['Prix'], "ESPECE", st.session_state.vendeur)
                                trigger_vibration(); st.cache_data.clear(); st.toast(f"✅ {nom}"); time.sleep(0.3); st.rerun()
                        with b2:
                            if st.button("💳", key=f"tpe_{i}"):
                                record_sale(ss, current_stand, nom, sz, p_ref['Prix'], "TPE", st.session_state.vendeur)
                                trigger_vibration(); st.cache_data.clear(); st.toast(f"✅ {nom}"); time.sleep(0.3); st.rerun()
                    else:
                        st.error("🚫 RUPTURE")
                        st.button("VIDE", disabled=True, key=f"empty_{i}")

    with tab_t:
        st.markdown("### 📦 Transférer du stock")
        if raw_p:
            t1, t2 = st.columns(2)
            with t1:
                t_prod = st.selectbox("Produit", noms_uniques)
                t_sizes = [str(p['Taille']) for p in raw_p if str(p['Nom']).strip() == t_prod]
                t_sz = st.selectbox("Taille", t_sizes)
                t_qty = st.number_input("Quantité", min_value=1, value=1)
            with t2:
                t_from = st.selectbox("DE :", STAND_NAMES, index=STAND_NAMES.index(current_stand))
                t_to = st.selectbox("VERS :", [s for s in STAND_NAMES if s != t_from])
            if st.button("🚀 VALIDER LE TRANSFERT", use_container_width=True):
                success, msg = process_transfer(ss, t_prod, t_sz, t_from, t_to, t_qty)
                if success: st.success(msg); time.sleep(1); st.rerun()
                else: st.error(msg)

    with tab_d:
        df_sales = load_sales(ss)
        if not df_sales.empty:
            df_sales['Total'] = pd.to_numeric(df_sales['Total'], errors='coerce').fillna(0)
            df_v = df_sales[df_sales['Statut'].str.upper().str.strip() == "VALIDE"].copy()
            if not df_v.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("💰 CA TOTAL", f"{int(df_v['Total'].sum())} DH")
                m2.metric("💵 CASH", f"{int(df_v[df_v['Mode'] == 'ESPECE']['Total'].sum())} DH")
                m3.metric("💳 TPE", f"{int(df_v[df_v['Mode'] == 'TPE']['Total'].sum())} DH")
                
                st.divider()
                st.markdown("### 🏪 RÉCAPITULATIF PAR STAND")
                recap = df_v.groupby(['Stand', 'Mode'])['Total'].sum().unstack(fill_value=0)
                st.table(recap)

                # Nouveau : Recap par vendeur
                st.markdown("### 👤 VENTES PAR VENDEUR")
                v_recap = df_v.groupby('Vendeur')['Total'].sum().reset_index()
                st.table(v_recap.set_index('Vendeur'))

                with st.expander("📄 Historique des ventes"):
                    st.dataframe(df_sales.sort_values("Date", ascending=False), use_container_width=True)
    
    if st.sidebar.button("🚪 Déconnexion"):
        st.session_state.vendeur = None
        st.rerun()

if __name__ == "__main__":
    main()
