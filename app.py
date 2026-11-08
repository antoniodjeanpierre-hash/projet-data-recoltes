from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent / "donnees"

st.set_page_config(page_title="Les récoltes agricoles", page_icon="🌾", layout="wide")

st.title("Les récoltes agricoles")
st.caption("Projet final, Python pour l'analyse de données, ESIH 2026. Données fictives.")


@st.cache_data
def charger_donnees():
    return pd.read_csv(DOSSIER / "recoltes_propre.csv")


recoltes = charger_donnees()

st.write(
    "Une direction départementale de l'agriculture (fictive) a relevé trois ans de récoltes, de 2023 à 2025, "
    "par saison, département et culture, avec la pluie tombée pendant chaque saison. "
    "Le ministère veut savoir quelles cultures pèsent le plus, où les rendements sont les meilleurs, "
    "et si la pluie explique les mauvaises années."
)
st.caption(
    "Source : direction départementale de l'agriculture (données fictives) : récoltes, pluies, cultures "
    "et départements, de 2023 à 2025."
)

# Étape 3 : les filtres
st.sidebar.header("Filtres")
annees = sorted(int(a) for a in recoltes["annee"].unique())
annees_choisies = st.sidebar.multiselect("Années", annees, default=annees)
saison = st.sidebar.selectbox("Saison", ["Toutes", "Printemps", "Automne"])
tous_les_departements = sorted(recoltes["departement"].unique())
departements_choisis = st.sidebar.multiselect("Départements", tous_les_departements, default=tous_les_departements)
toutes_les_cultures = sorted(recoltes["culture"].unique())
cultures_choisies = st.sidebar.multiselect("Cultures", toutes_les_cultures, default=toutes_les_cultures)

if not annees_choisies or not departements_choisis or not cultures_choisies:
    st.warning("Choisissez au moins une année, un département et une culture dans la barre latérale.")
    st.stop()

masque = recoltes["departement"].isin(departements_choisis) & recoltes["culture"].isin(cultures_choisies)
if saison != "Toutes":
    masque = masque & (recoltes["saison"] == saison)

# `base` garde toutes les années (elle sert à comparer 2023 et 2025) ; `df` applique aussi le filtre des années.
base = recoltes[masque]
df = base[base["annee"].isin(annees_choisies)]

if df.empty:
    st.info("Aucun relevé pour cette sélection : élargissez les filtres (par exemple, le riz n'est cultivé que dans cinq départements).")
    st.stop()


def milliers(nombre):
    return f"{nombre:,.0f}".replace(",", " ")


# Étape 4 : les indicateurs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Production totale", f"{milliers(df['production_t'].sum())} t")
col2.metric("Valeur (milliards de gourdes)", f"{df['valeur_htg'].sum() / 1e9:.2f}")
col3.metric("Rendement moyen", f"{df['production_t'].sum() / df['surface_ha'].sum():.2f} t/ha")
pluie_par_saison = df.drop_duplicates(["annee", "saison", "departement"])["pluie_mm"]
col4.metric("Pluie moyenne par saison", f"{pluie_par_saison.mean():.0f} mm")
