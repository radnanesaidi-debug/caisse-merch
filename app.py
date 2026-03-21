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
            # On charge les produits depuis Google Sheets
            raw_products = load_products(ss)
            
            # --- NETTOYAGE DES DONNÉES (Pour éviter le KeyError) ---
            all_p_clean = []
            for p in raw_products:
                # On essaie toutes les variantes de noms de colonnes possibles
                nom = p.get('Nom') or p.get('nom') or p.get('Name') or p.get('name')
                taille = p.get('Taille') or p.get('taille') or p.get('Size') or p.get('size')
                prix = p.get('Prix') or p.get('prix') or p.get('Price') or p.get('price')
                
                # Si la ligne a au moins un nom et une taille, on l'accepte
                if nom and taille:
                    clean_p = {
                        'Nom': str(nom),
                        'Taille': str(taille),
                        'Prix': prix or 0,
                        'Emoji': p.get('Emoji') or p.get('emoji', '📦')
                    }
                    # On ajoute les stocks dynamiquement selon tes stands
                    for s in STAND_NAMES:
                        col_stock = f"Stock {s}"
                        clean_p[col_stock] = p.get(col_stock, 0)
                    all_p_clean.append(clean_p)

            # --- AFFICHAGE ---
            if not all_p_clean:
                st.warning("Aucun produit trouvé. Vérifie les titres de ton Google Sheet.")
            else:
                noms_produits = sorted(list(set([p['Nom'] for p in all_p_clean])))
                cols = st.columns(3)
                
                for i, nom in enumerate(noms_produits):
                    variantes = [p for p in all_p_clean if p['Nom'] == nom]
                    p_ref = variantes[0]
                    col_stock_select = f"Stock {stand}"
                    
                    with cols[i % 3]:
                        with st.container(border=True):
                            st.markdown(f"### {p_ref['Emoji']} {nom}")
                            
                            # Filtrer uniquement les tailles avec du stock > 0
                            tailles_dispo = [v for v in variantes if int(float(v.get(col_stock_select, 0))) > 0]
                            
                            if tailles_dispo:
                                st.caption(f"Prix: {p_ref['Prix']} DH")
                                liste_tailles = [v['Taille'] for v in tailles_dispo]
                                sz = st.selectbox(f"Taille", liste_tailles, key=f"sz_{i}")
                                
                                if st.button(f"ENCAISSER", key=f"btn_{i}"):
                                    # On récupère le prix spécifique à la taille choisie
                                    prix_final = [v['Prix'] for v in tailles_dispo if v['Taille'] == sz][0]
                                    record_sale(ss, stand, nom, sz, prix_final)
                                    st.toast(f"✅ Vendu: {nom} ({sz})")
                                    time.sleep(0.5); st.rerun()
                            else:
                                st.error("🚫 SOLD OUT")
                                st.button("ÉPUISÉ", disabled=True, key=f"dis_{i}")

    with tab_d:
        # Code du dashboard reste identique
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
