import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
from io import BytesIO

# ----------------------------
# CONFIG MOBILE & APP
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
    for col, default in [("Visite", "À visiter"), ("Prioritaire", False), ("Nombre_membres", 1)]:
        if col not in df.columns:
            df[col] = default

    # Nettoyage Nom_rue
    df["Nom_rue"] = df.get("Nom_rue", "Inconnu").fillna("Inconnu").astype(str).str.strip()

    # Nettoyage coordonnées
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    return df

df = load_data()

# ----------------------------
# 2️⃣ Sidebar filtres
# ----------------------------
with st.sidebar:
    st.header("Filtres 🛠️")

    quartiers = ["Tous"] + sorted(df["Nom_rue"].unique(), key=str.lower)
    quartier_select = st.multiselect("🏘️ Quartiers", quartiers, default=["Tous"])

    etat_select = st.multiselect(
        "État visite",
        ["À visiter", "Visité", "En cours"],
        default=["À visiter", "Visité", "En cours"]
    )

    prioritaire_only = st.checkbox("Afficher uniquement prioritaires")

    membres_min, membres_max = int(df["Nombre_membres"].min()), int(df["Nombre_membres"].max())
    nb_membres_range = st.slider("Nombre de membres", membres_min, membres_max, (membres_min, membres_max))

# ----------------------------
# 3️⃣ Filtrer DataFrame
# ----------------------------
df_plot = df.copy()

if "Tous" not in quartier_select:
    df_plot = df_plot[df_plot["Nom_rue"].isin(quartier_select)]

df_plot = df_plot[df_plot["Visite"].isin(etat_select)]

if prioritaire_only:
    df_plot = df_plot[df_plot["Prioritaire"]]

df_plot = df_plot[(df_plot["Nombre_membres"] >= nb_membres_range[0]) & 
                  (df_plot["Nombre_membres"] <= nb_membres_range[1])]

# ----------------------------
# 4️⃣ Statistiques terrain
# ----------------------------
st.subheader("📊 Statistiques")

col1, col2, col3, col4 = st.columns(4)
total = len(df_plot)
visites = (df_plot["Visite"] == "Visité").sum()
reste = (df_plot["Visite"] == "À visiter").sum()
prioritaires = df_plot["Prioritaire"].sum()

col1.metric("Familles visibles", total)
col2.metric("Déjà visitées", visites)
col3.metric("Restantes", reste)
col4.metric("Prioritaires", prioritaires)

# ----------------------------
# 5️⃣ Carte interactive
# ----------------------------
st.subheader("🗺️ Carte interactive")
if not df_plot.empty:
    lat_mean = df_plot["lat"].mean()
    lon_mean = df_plot["lon"].mean()

    m = folium.Map(location=[lat_mean, lon_mean], zoom_start=15, control_scale=True)

    cluster = MarkerCluster().add_to(m)

    colors = {
        "À visiter": "red",
        "Visité": "green",
        "En cours": "orange"
    }

    for _, row in df_plot.iterrows():
        priority_badge = "⭐" if row["Prioritaire"] else ""
        popup_html = f"""
        <div style="font-family:sans-serif">
        <b>{row['Nom']} {row['Prénoms']} {priority_badge}</b><br>
        Adresse : {row['Adresse']}<br>
        Famille ID : {row.get('Famille_ID','')}<br>
        État : {row['Visite']}<br>
        Membres : {row['Nombre_membres']}<br>
        </div>
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

    # Heatmap optionnelle (commenter si pas souhaité)
    if st.checkbox("Afficher heatmap densité"):
        heat_data = df_plot[["lat", "lon"]].values.tolist()
        HeatMap(heat_data, radius=15).add_to(m)

    st_folium(m, width=None, height=600)
else:
    st.warning("Aucune donnée à afficher avec ces filtres.")

# ----------------------------
# 6️⃣ Export CSV
# ----------------------------
st.subheader("💾 Exporter les données filtrées")
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(df_plot)
st.download_button(
    label="Télécharger CSV",
    data=csv,
    file_name='familles_filtrees.csv',
    mime='text/csv'
)
