import streamlit as st
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏟️")

# --- CSS MAGIQUE POUR FORCER 2 COLONNES SUR MOBILE ---
st.markdown("""
    <style>
    /* Réduction globale des marges */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    
    /* Forcer la grille de produits à 2 colonnes sur mobile */
    [data-testid="column"] {
        width: calc(50% - 1rem) !important;
        flex: 1 1 calc(50% - 1rem) !important;
        min-width: calc(50% - 1rem) !important;
    }

    /* Rendre les cartes produits minuscules */
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        padding: 5px !important;
        margin-bottom: -15px !important;
        border-radius: 8px !important;
    }

    /* Ajuster la taille des textes et boutons */
    h3, b, p { font-size: 0.85rem !important; margin-bottom: 2px !important; }
    .stButton > button {
        height: 2.2rem !important;
        font-size: 1.1rem !important; /* Pour que les emojis soient gros */
        padding: 0px !important;
    }
    
    /* Cacher les labels inutiles pour gagner de la place */
    label { display: none !important; }
    
    .logo-img { width: 40px; }
    .stTabs [data-baseweb="tab"] { height: 35px; padding: 0px 10px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

def main():
    if "stand" not in st.query_params:
        st.query_params["stand"] = STAND_NAMES[0]
    
    current_stand = st.query_params["stand"]

    # Header minimaliste
    st.markdown(f"""<div style="display:flex; justify-content:center;"><img src="https://i.ibb.co/C3Chk581/votre-image.png" style="width:40px;"></div>""", unsafe_allow_html=True)
    
    try:
        ss = get_or_create_spreadsheet()
    except:
        st.error("Sheet Error")
        return

    tab_v, tab_t, tab_d = st.tabs(["🛒 CAISSE", "🔄 MOV", "📊 STAT"])

    with tab_v:
        # Barre de réglage sur une seule ligne
        r1, r2, r3 = st.columns([2, 1, 1])
        with r1:
            new_stand = st.selectbox("S", STAND_NAMES, index=STAND_NAMES.index(current_stand))
            if new_stand != current_stand:
                st.query_params["stand"] = new_stand
                st.rerun()
        with r2:
            show_img = st.toggle("🖼️", value=False)
        with r3:
            if st.button("↩️"):
                if cancel_last_sale(ss):
                    st.toast("Annulé")
                    time.sleep(0.5); st.rerun()

        raw_p = load_products(ss)
        if not raw_p: return
        
        noms_uniques = sorted(list(set([str(p['Nom']).strip() for p in raw_p if p['Nom']])))
        
        # On utilise une boucle simple, le CSS s'occupe de mettre 2 produits par ligne
        cols = st.columns(2) 
        
        for i, nom in enumerate(noms_uniques):
            variantes = [p for p in raw_p if str(p['Nom']).strip() == nom]
            p_ref = variantes[0]
            col_stock_name = f"Stock {current_stand}"
            
            # On alterne entre col[0] et col[1]
            with cols[i % 2]:
                with st.container(border=True):
                    if show_img and p_ref.get('Image'):
                        st.image(p_ref['Image'], use_container_width=True)
                    
                    st.markdown(f"**{nom[:15]}**") # Coupe le nom si trop long
                    tailles_dispo = [v for v in variantes if int(float(v.get(col_stock_name, 0))) > 0]
                    
                    if tailles_dispo:
                        sz = st.selectbox("T", [str(v['Taille']) for v in tailles_dispo], key=f"sz_{i}")
                        v_sel = [v for v in tailles_dispo if str(v['Taille']) == sz][0]
                        stock_val = int(float(v_sel[col_stock_name]))
                        
                        st.markdown(f"{p_ref['Prix']}DH | **{stock_val}** u")
                        
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("💵", key=f"esp_{i}"):
                                record_sale(ss, current_stand, nom, sz, p_ref['Prix'], "ESPECE")
                                st.cache_data.clear()
                                st.rerun()
                        with b2:
                            if st.button("💳", key=f"tpe_{i}"):
                                record_sale(ss, current_stand, nom, sz, p_ref['Prix'], "TPE")
                                st.cache_data.clear()
                                st.rerun()
                    else:
                        st.error("RUPTURE")

    # --- Transferts et Stats (Gardés simples) ---
    with tab_t:
        # ... (code transfert précédent)
        pass
    with tab_d:
        # ... (code stats précédent)
        pass

if __name__ == "__main__":
    main()
