import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ----------------------------
# CONFIG MOBILE
# ----------------------------
st.set_page_config(
    page_title="Carte Porte-à-Porte",
    layout="wide"
)

st.title("📍 Carte Familles — Chiconi")

# ----------------------------
# 1️⃣ Charger les données
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("resultats_rues_mayotte.xlsx")

    # Colonnes nécessaires
    if "Visite" not in df.columns:
        df["Visite"] = "À visiter"

    if "Prioritaire" not in df.columns:
        df["Prioritaire"] = False

    if "Nombre_membres" not in df.columns:
        df["Nombre_membres"] = 1

    # Nettoyage Nom_rue (évite crash tri)
    df["Nom_rue"] = (
        df["Nom_rue"]
        .fillna("Inconnu")
        .astype(str)
        .str.strip()
    )

    # Nettoyage coordonnées
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    return df

df = load_data()

# ----------------------------
# 2️⃣ MENU FILTRES (mobile friendly)
# ----------------------------
quartiers = ["Tous"] + sorted(df["Nom_rue"].unique(), key=str.lower)
quartier_select = st.selectbox("🏘️ Quartier", quartiers)

etat_select = st.multiselect(
    "État visite",
    ["À visiter", "Visité", "En cours"],
    default=["À visiter", "Visité", "En cours"]
)

prioritaire_only = st.checkbox("Afficher uniquement prioritaires")

# ----------------------------
# 3️⃣ Filtrer DataFrame
# ----------------------------
df_plot = df.copy()

if quartier_select != "Tous":
    df_plot = df_plot[df_plot["Nom_rue"] == quartier_select]

df_plot = df_plot[df_plot["Visite"].isin(etat_select)]

if prioritaire_only:
    df_plot = df_plot[df_plot["Prioritaire"]]

# ----------------------------
# 4️⃣ Statistiques terrain
# ----------------------------
col1, col2, col3 = st.columns(3)

total = len(df_plot)
visites = (df_plot["Visite"] == "Visité").sum()
reste = (df_plot["Visite"] == "À visiter").sum()

col1.metric("Familles visibles", total)
col2.metric("Déjà visitées", visites)
col3.metric("Restantes", reste)

# ----------------------------
# 5️⃣ Créer carte
# ----------------------------
if not df_plot.empty:

    lat_mean = df_plot["lat"].mean()
    lon_mean = df_plot["lon"].mean()

    m = folium.Map(
        location=[lat_mean, lon_mean],
        zoom_start=15,
        control_scale=True
    )

    cluster = MarkerCluster().add_to(m)

    colors = {
        "À visiter": "red",
        "Visité": "green",
        "En cours": "orange"
    }

    for idx, row in df_plot.iterrows():

        popup_html = f"""
        <b>{row['Nom']} {row['Prénoms']}</b><br>
        Adresse : {row['Adresse']}<br>
        Famille ID : {row.get('Famille_ID','')}<br>
        État : {row['Visite']}<br>
        Membres : {row['Nombre_membres']}<br>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color=colors.get(row["Visite"], "blue"),
            fill=True,
            fill_color=colors.get(row["Visite"], "blue"),
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(cluster)

    # Affichage carte (mobile compatible)
    st_folium(m, width=None, height=600)

else:
    st.warning("Aucune donnée à afficher avec ces filtres.")
