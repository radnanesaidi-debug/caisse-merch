import streamlit as st
import pandas as pd
import plotly.express as px
import time
from config import *
from google_sheets import *

st.set_page_config(page_title=APP_TITLE, layout="wide")

def main():
    st.title(f"🏟️ {APP_TITLE}")
    
    try:
        ss = get_or_create_spreadsheet()
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return

    tab_v, tab_d = st.tabs(["🛒 CAISSE", "📊 DASHBOARD"])

    with tab_v:
        c1, c2 = st.columns([1, 3])
        with c1:
            st.subheader("Configuration")
            stand = st.radio("Choisir le Stand :", STAND_NAMES)
            st.divider()
            if st.button("↩️ Annuler dernière vente"):
                if cancel_last_sale(ss):
                    st.success("Vente annulée !")
                    time.sleep(1)
                    st.rerun()
        
        with c2:
            prods = load_products(ss)
            cols = st.columns(2)
            for i, p in enumerate(prods):
                name = p.get('Nom') or p.get('name')
                price = p.get('Prix') or p.get('price')
                emoji = p.get('Emoji') or p.get('emoji', "📦")
                sizes = str(p.get('Tailles') or p.get('sizes')).replace('[','').replace(']','').replace("'","").split(',')
                
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"### {emoji} {name}")
                        st.markdown(f"**Prix : {price} DH**")
                        sz = st.selectbox(f"Taille", [s.strip() for s in sizes], key=f"sz_{i}")
                        if st.button(f"ENCAISSER {price} DH", key=f"btn_{i}"):
                            record_sale(ss, stand, name, sz, price)
                            st.toast(f"✅ Vendu : {name} ({sz})")

    with tab_d:
        df = load_sales(ss)
        if not df.empty:
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
            df['Qté'] = pd.to_numeric(df['Qté'], errors='coerce').fillna(0)
            df_v = df[df['Statut'].str.upper().str.strip() == "VALIDE"]
            
            if not df_v.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("RECETTE TOTALE", f"{int(df_v['Total'].sum())} DH")
                m2.metric("ARTICLES VENDUS", int(df_v['Qté'].sum()))
                m3.metric("VENTES TOTALES", len(df_v))
                
                st.divider()
                g1, g2 = st.columns(2)
                with g1:
                    fig1 = px.pie(df_v, values='Total', names='Stand', title="Répartition CA / Stand", hole=.4)
                    st.plotly_chart(fig1, use_container_width=True)
                with g2:
                    fig2 = px.bar(df_v.groupby("Produit")["Qté"].sum().reset_index(), x="Produit", y="Qté", title="Top Ventes (Quantité)")
                    st.plotly_chart(fig2, use_container_width=True)
                
                st.subheader("Détail des ventes")
                st.dataframe(df_v.sort_values("Date", ascending=False), use_container_width=True)
            else:
                st.warning("Aucune vente validée dans le fichier.")
        else:
            st.info("Le Dashboard sera visible après la première vente.")

if __name__ == "__main__":
    main()
