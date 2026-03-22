import streamlit as st
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏟️")

# --- CSS CUSTOM (Le secret de la prime) ---
st.markdown("""
    <style>
    /* Style global des boutons d'encaissement */
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
    /* Style spécial pour le bouton Annuler (Gris) */
    [data-testid="stSidebar"] .stButton > button, 
    .stColumn:first-child .stButton > button {
        background-color: #f0f2f6 !important;
        color: #31333F !important;
        height: 2.5rem !important;
        font-weight: 500 !important;
    }
    /* Cartes produits */
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        border-radius: 15px !important;
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h3 { color: #1E1E1E; margin-bottom: 5px !important; }
    .stock-label { font-weight: bold; padding: 4px 8px; background: #f8f9fa; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- AFFICHAGE DU LOGO CENTRÉ ---
    col_l1, col_l2, col_l3 = st.columns([1, 0.8, 1])
    with col_l2:
        # Lien direct vers l'image pour l'affichage Streamlit
        st.image("https://i.ibb.co/C3Chk581/votre-image.png", use_container_width=True)

    st.title(f"🏟️ {APP_TITLE}")
    
    try:
        ss = get_or_create_spreadsheet()
    except Exception as e:
        st.error(f"Erreur connexion : {e}")
        return

    tab_v, tab_d = st.tabs(["🛒 ESPACE CAISSE", "📊 STATISTIQUES LIVE"])

    with tab_v:
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown("### ⚙️ RÉGLAGES")
            stand = st.radio("Stand Actif :", STAND_NAMES)
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
                            
                            if st.button(f"ENCAISSER", key=f"btn_{i}"):
                                record_sale(ss, stand, nom, sz, p_ref['Prix'])
                                st.toast(f"✅ VENDU : {nom} ({sz})")
                                time.sleep(0.4); st.rerun()
                        else:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.error("🚫 RUPTURE DE STOCK")
                            st.button("ÉPUISÉ", disabled=True, key=f"off_{i}")

    with tab_d:
        df = load_sales(ss)
        if not df.empty:
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
            df_v = df[df['Statut'].str.upper().str.strip() == "VALIDE"]
            
            if not df_v.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("💰 CHIFFRE D'AFFAIRES", f"{int(df_v['Total'].sum())} DH")
                m2.metric("📦 ARTICLES VENDUS", int(len(df_v)))
                m3.metric("🎫 STAND FAVORI", df_v['Stand'].mode()[0] if not df_v['Stand'].empty else "-")
                
                st.divider()
                g1, g2 = st.columns(2)
                with g1:
                    fig_pie = px.pie(df_v, values='Total', names='Stand', hole=.4, 
                                   title="Répartition CA", color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_pie, use_container_width=True)
                with g2:
                    fig_bar = px.bar(df_v.groupby("Produit").size().reset_index(name='Nb'), 
                                   x="Produit", y="Nb", title="Top Ventes (Volume)",
                                   color_discrete_sequence=['#FF4B4B'])
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with st.expander("📄 Voir le détail des transactions"):
                    st.dataframe(df_v.sort_values("Date", ascending=False), use_container_width=True)
            else:
                st.info("Aucune vente validée pour le moment.")
        else:
            st.info("Réalise ta première vente pour activer le Dashboard !")

if __name__ == "__main__":
    main()
