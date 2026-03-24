import streamlit as st
import pandas as pd
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏟️")

# CSS OPTIMISÉ : On réduit tout pour que ça tienne sur un écran
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    .stButton > button {
        border-radius: 6px !important;
        height: 2.5rem !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        padding: 8px !important;
        margin-bottom: -10px !important;
    }
    h3 { font-size: 1rem !important; margin-bottom: 2px !important; }
    .stock-label { font-size: 0.8rem; padding: 2px 5px; }
    .logo-container { display: flex; justify-content: center; padding-top: 10px; }
    .logo-img { width: 50px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    # 1. Gestion de la persistance du Stand via URL
    if "stand" not in st.query_params:
        st.query_params["stand"] = STAND_NAMES[0]
    
    current_stand = st.query_params["stand"]

    st.markdown(f"""<div class="logo-container"><img src="https://i.ibb.co/C3Chk581/votre-image.png" class="logo-img"></div>""", unsafe_allow_html=True)
    
    try:
        ss = get_or_create_spreadsheet()
    except:
        st.error("Erreur connexion Google Sheets")
        return

    tab_v, tab_t, tab_d = st.tabs(["🛒 CAISSE", "🔄 TRANSF", "📊 STATS"])

    with tab_v:
        # Barre de réglages ultra compacte en haut
        r1, r2, r3 = st.columns([1.5, 1, 1])
        with r1:
            # Si on change le stand, on met à jour l'URL et on reload
            new_stand = st.selectbox("STAND :", STAND_NAMES, index=STAND_NAMES.index(current_stand))
            if new_stand != current_stand:
                st.query_params["stand"] = new_stand
                st.rerun()
        with r2:
            show_img = st.toggle("Photos", value=False)
        with r3:
            if st.button("↩️ Annul"):
                if cancel_last_sale(ss):
                    st.toast("Vente annulée !")
                    time.sleep(0.5); st.rerun()

        st.divider()

        # Affichage des produits en petite grille
        raw_p = load_products(ss)
        if not raw_p: return
        
        noms_uniques = sorted(list(set([str(p['Nom']).strip() for p in raw_p if p['Nom']])))
        cols = st.columns(3) # 3 colonnes pour mobile c'est bien
        
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
                        # Selectbox de taille plus petite
                        sz = st.selectbox("T", [str(v['Taille']) for v in tailles_dispo], key=f"sz_{i}", label_visibility="collapsed")
                        
                        v_sel = [v for v in tailles_dispo if str(v['Taille']) == sz][0]
                        stock_val = int(float(v_sel[col_stock_name]))
                        
                        st.markdown(f"{p_ref['Prix']} DH | **{stock_val}** u", unsafe_allow_html=True)
                        
                        # DEUX BOUTONS CÔTE À CÔTE POUR ENCAISSER
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("💵", key=f"esp_{i}", help="Espèces"):
                                record_sale(ss, current_stand, nom, sz, p_ref['Prix'], "ESPECE")
                                st.cache_data.clear() # VIDAGE CACHE FORCE
                                st.toast("✅ Cash")
                                time.sleep(0.3); st.rerun()
                        with b2:
                            if st.button("💳", key=f"tpe_{i}", help="TPE"):
                                record_sale(ss, current_stand, nom, sz, p_ref['Prix'], "TPE")
                                st.cache_data.clear() # VIDAGE CACHE FORCE
                                st.toast("✅ TPE")
                                time.sleep(0.3); st.rerun()
                    else:
                        st.error("RUPTURE")

    # (Le reste des onglets Transferts et Stats reste identique ou simplifié de la même manière)
    # ... [Code onglet Transfert et Stats simplifié ici] ...

if __name__ == "__main__":
    main()
