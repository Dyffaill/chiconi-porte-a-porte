import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ----------------------------
# CONFIG PAGE
# ----------------------------
st.set_page_config(
    page_title="Carte Porte-à-Porte",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    /* Personnalisation CSS */
    .stSlider > div[data-baseweb] { width: 100% !important; }
    .stButton>button { background-color:#4CAF50; color:white; border:none; padding:0.5em 1em; border-radius:5px; }
    .stMetric { text-align:center !important; }
    </style>
    """, unsafe_allow_html=True
)

st.title("📍 Carte Familles — Chiconi")

# ----------------------------
# 1️⃣ Charger les données
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("resultats_rues_mayotte.xlsx")

    # Colonnes nécessaires
    df["Visite"] = df.get("Visite", pd.Series("À visiter"))
    df["Prioritaire"] = df.get("Prioritaire", pd.Series(False))
    df["Nombre_membres"] = df.get("Nombre_membres", pd.Series(1))

    df["Nom_rue"] = df["Nom_rue"].fillna("Inconnu").astype(str).str.strip()

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    return df

df = load_data()

# ----------------------------
# 2️⃣ Sidebar filtres
# ----------------------------
st.sidebar.header("Filtres")

# Quartier
quartiers = ["Tous"] + sorted(df["Nom_rue"].unique(), key=str.lower)
quartier_select = st.sidebar.selectbox("🏘️ Quartier", quartiers)

# État visite
etat_options = ["À visiter", "Visité", "En cours"]
etat_select = st.sidebar.multiselect(
    "État visite",
    etat_options,
    default=etat_options
)

# Prioritaires
prioritaire_only = st.sidebar.checkbox("Afficher uniquement prioritaires")

# Nombre de membres (slider sécurisé)
if not df.empty:
    membres_min = int(df["Nombre_membres"].min())
    membres_max = int(df["Nombre_membres"].max())
else:
    membres_min, membres_max = 0, 1

if membres_max >= membres_min:
    nb_membres_range = st.sidebar.slider(
        "Nombre de membres",
        membres_min,
        membres_max,
        (membres_min, membres_max)
    )
else:
    nb_membres_range = (membres_min, membres_max)

# ----------------------------
# 3️⃣ Filtrer DataFrame
# ----------------------------
df_plot = df.copy()

if quartier_select != "Tous":
    df_plot = df_plot[df_plot["Nom_rue"] == quartier_select]

df_plot = df_plot[df_plot["Visite"].isin(etat_select)]
if prioritaire_only:
    df_plot = df_plot[df_plot["Prioritaire"]]

# Filtrer par nombre de membres
df_plot = df_plot[
    df_plot["Nombre_membres"].between(nb_membres_range[0], nb_membres_range[1])
]

# ----------------------------
# 4️⃣ Statistiques terrain
# ----------------------------
col1, col2, col3, col4 = st.columns(4)

total = len(df_plot)
visites = (df_plot["Visite"] == "Visité").sum()
reste = (df_plot["Visite"] == "À visiter").sum()
en_cours = (df_plot["Visite"] == "En cours").sum()

col1.metric("Familles visibles", total)
col2.metric("Déjà visitées", visites)
col3.metric("Restantes", reste)
col4.metric("En cours", en_cours)

# ----------------------------
# 5️⃣ Carte interactive
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

    for _, row in df_plot.iterrows():
        popup_html = f"""
        <b>{row.get('Nom','')} {row.get('Prénoms','')}</b><br>
        Adresse : {row.get('Adresse','')}<br>
        Famille ID : {row.get('Famille_ID','')}<br>
        État : {row.get('Visite','')}<br>
        Membres : {row.get('Nombre_membres','')}<br>
        Prioritaire : {row.get('Prioritaire', False)}
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

    # Carte responsive
    st_folium(m, width="100%", height=650)
else:
    st.warning("Aucune donnée à afficher avec ces filtres.")
