import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ----------------------------
# CONFIG MOBILE & PAGE
# ----------------------------
st.set_page_config(
    page_title="Carte Porte-à-Porte",
    layout="wide"
)

# CSS personnalisé pour mobile et style
st.markdown(
    """
    <style>
    /* Rendre les selectbox et sliders plus lisibles sur mobile */
    .stSelectbox, .stSlider {
        font-size: 1rem;
    }
    .stMetric {
        font-size: 1.2rem;
    }
    .stAlert {
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📍 Carte Familles — Chiconi")

# ----------------------------
# 1️⃣ Charger les données
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("resultats_rues_mayotte.xlsx")

    # Colonnes par défaut
    df["Visite"] = df.get("Visite", "À visiter")
    df["Prioritaire"] = df.get("Prioritaire", False)
    df["Nombre_membres"] = pd.to_numeric(df.get("Nombre_membres", 1), errors="coerce").fillna(1).astype(int)
    df["Nom_rue"] = df.get("Nom_rue", "Inconnu").astype(str).str.strip()

    # Nettoyage coordonnées
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    return df

df = load_data()

# ----------------------------
# 2️⃣ MENU FILTRES (sidebar)
# ----------------------------
st.sidebar.header("Filtres dynamiques")

# Quartier
quartiers = ["Tous"] + sorted(df["Nom_rue"].unique(), key=str.lower)
quartier_select = st.sidebar.selectbox("🏘️ Quartier", quartiers)

# État visite
etat_select = st.sidebar.multiselect(
    "État visite",
    ["À visiter", "Visité", "En cours"],
    default=["À visiter", "Visité", "En cours"]
)

# Prioritaires
prioritaire_only = st.sidebar.checkbox("Afficher uniquement prioritaires")

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
# 4️⃣ Slider Nombre de membres (sécurisé)
# ----------------------------
if not df_plot.empty and "Nombre_membres" in df_plot.columns:
    membres_series = pd.to_numeric(df_plot["Nombre_membres"], errors="coerce").dropna().astype(int)
    if len(membres_series) > 0:
        membres_min = int(membres_series.min())
        membres_max = int(membres_series.max())
        if membres_min <= membres_max:
            nb_membres_range = st.sidebar.slider(
                "Nombre de membres",
                membres_min,
                membres_max,
                (membres_min, membres_max)
            )
            # Filtrer selon slider
            df_plot = df_plot[
                (df_plot["Nombre_membres"] >= nb_membres_range[0]) &
                (df_plot["Nombre_membres"] <= nb_membres_range[1])
            ]
        else:
            nb_membres_range = (membres_min, membres_min)
    else:
        nb_membres_range = (0, 0)
else:
    nb_membres_range = (0, 0)

# ----------------------------
# 5️⃣ Statistiques terrain
# ----------------------------
col1, col2, col3 = st.columns(3)
total = len(df_plot)
visites = (df_plot["Visite"] == "Visité").sum()
reste = (df_plot["Visite"] == "À visiter").sum()

col1.metric("Familles visibles", total)
col2.metric("Déjà visitées", visites)
col3.metric("Restantes", reste)

# ----------------------------
# 6️⃣ Carte interactive
# ----------------------------
if not df_plot.empty:
    lat_mean = df_plot["lat"].mean()
    lon_mean = df_plot["lon"].mean()

    m = folium.Map(location=[lat_mean, lon_mean], zoom_start=15, control_scale=True)
    cluster = MarkerCluster().add_to(m)

    colors = {"À visiter": "red", "Visité": "green", "En cours": "orange"}

    for idx, row in df_plot.iterrows():
        popup_html = f"""
        <div style='font-size:0.9rem'>
        <b>{row.get('Nom','')} {row.get('Prénoms','')}</b><br>
        Adresse : {row.get('Adresse','')}<br>
        Famille ID : {row.get('Famille_ID','')}<br>
        État : {row.get('Visite','')}<br>
        Membres : {row.get('Nombre_membres','')}<br>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color=colors.get(row.get("Visite"), "blue"),
            fill=True,
            fill_color=colors.get(row.get("Visite"), "blue"),
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(cluster)

    st_folium(m, width=None, height=600)
else:
    st.warning("Aucune donnée à afficher avec ces filtres.")
