import streamlit as st
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏟️")

# CSS : CACHER LE HEADER + STYLISER LES ONGLETS
st.markdown("""
    <style>
    /* 1. Cacher la barre Streamlit en haut */
    header { visibility: hidden; height: 0px !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* 2. Ajuster l'espacement global */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    
    /* 3. Style des Onglets (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        width: 100%;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
        padding: 0px 15px;
        font-weight: 700;
        flex-grow: 1; /* Les onglets prennent toute la largeur */
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff !important; /* Couleur bleue quand sélectionné */
        color: white !important;
    }

    /* 4. Style des Boutons de vente */
    .stButton > button {
        border-radius: 6px !important;
        height: 3rem !important;
        font-weight: 800 !important;
        font-size: 1.2rem !important;
    }
    
    /* 5. Conteneur Produits */
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        padding: 10px !important;
        margin-bottom: -10px !important;
        border-radius: 10px !important;
    }
    
    .logo-container { display: flex; justify-content: center; padding-top: 5px; margin-bottom: 5px; }
    .logo-img { width: 50px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    if "stand" not in st.query_params:
        st.query_params["stand"] = STAND_NAMES[0]
    current_stand = st.query_params["stand"]

    st.markdown(f"""<div class="logo-container"><img src="https://i.ibb.co/C3Chk581/votre-image.png" class="logo-img"></div>""", unsafe_allow_html=True)
    
    try:
        ss = get_or_create_spreadsheet()
    except:
        st.error("🚨 Connexion Google Sheets impossible")
        return

    # Onglets avec icônes
    tab_v, tab_t, tab_d = st.tabs(["🛒 CAISSE", "🔄 TRANSFERT", "📊 STATS"])

    # --- ONGLET CAISSE ---
    with tab_v:
        r1, r2, r3 = st.columns([1.5, 1, 1])
        with r1:
            new_stand = st.selectbox("S", STAND_NAMES, index=STAND_NAMES.index(current_stand), label_visibility="collapsed")
            if new_stand != current_stand:
                st.query_params["stand"] = new_stand
                st.rerun()
        with r2:
            show_img = st.toggle("Img", value=False)
        with r3:
            if st.button("↩️"):
                if cancel_last_sale(ss):
                    st.toast("Annulé")
                    time.sleep(0.5); st.rerun()

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
                    if show_img and p_ref.get('Image'):
                        st.image(p_ref['Image'], use_container_width=True)
                    
                    st.markdown(f"**{nom}**")
                    tailles_dispo = [v for v in variantes if int(float(v.get(col_stock_name, 0))) > 0]
                    
                    if tailles_dispo:
                        sz = st.selectbox("T", [str(v['Taille']) for v in tailles_dispo], key=f"sz_{i}", label_visibility="collapsed")
                        v_sel = [v for v in tailles_dispo if str(v['Taille']) == sz][0]
                        stock_val = int(float(v_sel[col_stock_name]))
                        st.markdown(f"**{p_ref['Prix']}** | `{stock_val}u`")
                        
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("💵", key=f"esp_{i}"):
                                record_sale(ss, current_stand, nom, sz, p_ref['Prix'], "ESPECE")
                                st.cache_data.clear(); st.rerun()
                        with b2:
                            if st.button("💳", key=f"tpe_{i}"):
                                record_sale(ss, current_stand, nom, sz, p_ref['Prix'], "TPE")
                                st.cache_data.clear(); st.rerun()
                    else:
                        st.error("RUPTURE")

    # --- TRANSFERTS ---
    with tab_t:
        st.markdown("### 📦 Mouvement de Stock")
        t1, t2 = st.columns(2)
        with t1:
            t_prod = st.selectbox("Prod", noms_uniques)
            t_sizes = [str(p['Taille']) for p in raw_p if str(p['Nom']).strip() == t_prod]
            t_sz = st.selectbox("Taille", t_sizes)
            t_qty = st.number_input("Qté", min_value=1, value=1)
        with t2:
            t_from = st.selectbox("DE", STAND_NAMES, index=STAND_NAMES.index(current_stand))
            t_to = st.selectbox("VERS", [s for s in STAND_NAMES if s != t_from])
        
        if st.button("🚀 VALIDER LE TRANSFERT", use_container_width=True):
            success, msg = process_transfer(ss, t_prod, t_sz, t_from, t_to, t_qty)
            if success: st.success(msg); time.sleep(1); st.rerun()
            else: st.error(msg)

    # --- STATS ---
    with tab_d:
        df_sales = load_sales(ss)
        if not df_sales.empty:
            df_v = df_sales[df_sales['Statut'].str.upper().str.strip() == "VALIDE"].copy()
            df_v['Total'] = pd.to_numeric(df_v['Total'], errors='coerce')
            
            st.metric("💰 CA TOTAL", f"{int(df_v['Total'].sum())} DH")
            st.table(df_v.groupby(['Stand', 'Mode'])['Total'].sum().unstack(fill_value=0))
            
            with st.expander("Historique"):
                st.dataframe(df_sales.sort_values("Date", ascending=False))

if __name__ == "__main__":
    main()
