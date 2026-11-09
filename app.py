from math import ceil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
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


def afficher(fig):
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# Étape 5 : un onglet par question
onglet1, onglet2, onglet3, onglet4, onglet5 = st.tabs(
    ["Poids des cultures", "Rendements", "Pluie", "Évolution", "Par habitant"]
)

with onglet1:
    st.subheader("Quelles cultures pèsent le plus, en tonnes puis en valeur ?")
    poids = df.groupby("culture").agg(tonnes=("production_t", "sum"), valeur=("valeur_htg", "sum"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    poids["tonnes"].sort_values().plot.barh(ax=axes[0], color="seagreen")
    axes[0].set_title("Production (tonnes)")
    (poids["valeur"] / 1e9).sort_values().plot.barh(ax=axes[1], color="goldenrod")
    axes[1].set_title("Valeur de la production (milliards de gourdes)")
    for ax in axes:
        ax.set_ylabel("")
    fig.suptitle("Poids des cultures, en tonnes puis en valeur", y=1.02)
    afficher(fig)
    premier_tonnes = poids["tonnes"].idxmax()
    premier_valeur = poids["valeur"].idxmax()
    tonnes_premier = milliers(poids.loc[premier_tonnes, "tonnes"])
    valeur_premier = poids.loc[premier_valeur, "valeur"] / 1e9
    if premier_tonnes == premier_valeur:
        st.write(
            f"{premier_tonnes} est en tête en tonnes ({tonnes_premier} t) "
            f"comme en valeur ({valeur_premier:.2f} milliards de gourdes)."
        )
    else:
        st.write(
            f"En tonnes, {premier_tonnes} est en tête ({tonnes_premier} t) ; en valeur, c'est {premier_valeur} "
            f"({valeur_premier:.2f} milliards de gourdes) : le classement change."
        )

with onglet2:
    st.subheader("Où les rendements sont-ils les meilleurs, culture par culture ?")
    totaux = df.groupby(["culture", "departement"])[["production_t", "surface_ha"]].sum()
    rendements = (totaux["production_t"] / totaux["surface_ha"]).unstack()
    national = df.groupby("culture")["production_t"].sum() / df.groupby("culture")["surface_ha"].sum()
    relatif = rendements.div(national, axis=0)
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(rendements.index) + 2.5))
    image = ax.imshow(relatif.values, cmap="RdYlGn", vmin=0.7, vmax=1.4, aspect="auto")
    ax.set_xticks(range(len(rendements.columns)))
    ax.set_xticklabels(rendements.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(rendements.index)))
    ax.set_yticklabels(rendements.index)
    for i in range(rendements.shape[0]):
        for j in range(rendements.shape[1]):
            valeur = rendements.iloc[i, j]
            if pd.notna(valeur):
                ax.text(j, i, f"{valeur:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="rendement / moyenne de la culture")
    ax.set_title("Rendement (t/ha) par culture et par département")
    afficher(fig)
    meilleur = rendements.idxmax(axis=1)
    meilleur_rendement = rendements.max(axis=1)
    detail = " ; ".join(
        f"{culture} : {meilleur[culture]} ({meilleur_rendement[culture]:.2f} t/ha)" for culture in rendements.index
    )
    st.write(f"Meilleur département pour chaque culture : {detail}.")

with onglet3:
    st.subheader("La pluie explique-t-elle les rendements ?")
    cultures_presentes = sorted(df["culture"].unique())
    colonnes = min(4, len(cultures_presentes))
    lignes = ceil(len(cultures_presentes) / colonnes)
    fig, axes = plt.subplots(lignes, colonnes, figsize=(4 * colonnes, 3.2 * lignes), squeeze=False)
    correlations = {}
    for ax, culture in zip(axes.flat, cultures_presentes):
        g = df[df["culture"] == culture]
        ax.scatter(g["pluie_mm"], g["rendement_t_ha"], alpha=0.6, s=16, color="seagreen")
        r = g["rendement_t_ha"].corr(g["pluie_mm"]) if len(g) >= 3 else float("nan")
        correlations[culture] = r
        if len(g) >= 3 and g["pluie_mm"].nunique() > 1:
            pente, origine = np.polyfit(g["pluie_mm"], g["rendement_t_ha"], 1)
            x = np.array([g["pluie_mm"].min(), g["pluie_mm"].max()])
            ax.plot(x, pente * x + origine, color="tab:red")
        ax.set_title(f"{culture} (r = {r:.2f})")
        ax.set_xlabel("Pluie (mm)")
        ax.set_ylabel("Rendement (t/ha)")
    for ax in list(axes.flat)[len(cultures_presentes):]:
        ax.axis("off")
    fig.suptitle("Rendement et pluie, une culture par graphique", y=1.02)
    afficher(fig)
    serie = pd.Series(correlations).dropna()
    if serie.empty:
        st.info("Pas assez de relevés pour calculer une corrélation.")
    else:
        fortes = int((serie > 0.5).sum())
        st.write(
            f"La pluie va de pair avec le rendement pour {fortes} culture(s) sur {len(serie)} "
            f"(corrélation supérieure à 0.5) : le lien est le plus fort pour {serie.idxmax()} ({serie.max():.2f}) "
            f"et le plus faible pour {serie.idxmin()} ({serie.min():.2f}). "
            "Une corrélation ne prouve pas que la pluie est la cause."
        )

with onglet4:
    st.subheader("Quelles cultures progressent ou reculent entre 2023 et 2025 ?")
    st.caption("Ce graphique compare toujours 2023 et 2025, quelle que soit la sélection des années.")
    production = base.pivot_table(index="culture", columns="annee", values="production_t", aggfunc="sum")
    if 2023 in production.columns and 2025 in production.columns:
        variation = ((production[2025] / production[2023] - 1) * 100).dropna().sort_values()
    else:
        variation = pd.Series(dtype=float)
    if variation.empty:
        st.info("Pas assez de relevés en 2023 et en 2025 pour cette sélection.")
    else:
        fig, ax = plt.subplots(figsize=(8, 4))
        variation.plot.barh(ax=ax, color=["tab:red" if v < 0 else "tab:green" for v in variation])
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Variation de la production entre 2023 et 2025 (%)")
        ax.set_ylabel("")
        ax.set_title("Évolution de la production par culture")
        afficher(fig)
        st.write(
            f"Entre 2023 et 2025, {int((variation > 0).sum())} culture(s) progressent et "
            f"{int((variation < 0).sum())} reculent. Meilleure évolution : {variation.idxmax()} "
            f"({variation.max():+.1f} %) ; pire évolution : {variation.idxmin()} ({variation.min():+.1f} %)."
        )

with onglet5:
    st.subheader("Quels départements produisent le plus par habitant ?")
    nb_annees = len(annees_choisies)
    par_departement = df.groupby("departement").agg(tonnes=("production_t", "sum"), population=("population", "first"))
    par_departement["kg_par_habitant_an"] = par_departement["tonnes"] * 1000 / par_departement["population"] / nb_annees
    classement = par_departement["kg_par_habitant_an"].sort_values()
    fig, ax = plt.subplots(figsize=(8, 4))
    classement.plot.barh(ax=ax, color="steelblue")
    ax.set_xlabel("kg produits par habitant et par an")
    ax.set_ylabel("")
    ax.set_title("Production par habitant, par département")
    afficher(fig)
    st.write(
        f"{classement.index[-1]} produit le plus par habitant ({classement.iloc[-1]:.1f} kg par an) "
        f"et {classement.index[0]} le moins ({classement.iloc[0]:.1f} kg par an)."
    )

# Étape 6 : la conclusion et les données
st.markdown(
    """
### Conclusion

**Ce qu'il faut retenir** (sur l'ensemble des données, sans filtre) :

- En tonnes, la banane et l'igname dominent ; en valeur, l'igname passe devant la banane, et le haricot et le pois congo gagnent deux places grâce à leur prix.
- Aucun département n'est le meilleur partout : le Nord est premier pour la banane, la Grand'Anse pour l'igname, l'Artibonite pour le riz.
- La pluie va de pair avec le rendement pour toutes les cultures (corrélation de 0.42 pour le riz à 0.76 pour le haricot et le maïs), mais très peu pour le riz en automne.
- Entre 2023 et 2025, le riz, le sorgho et la banane progressent ; l'igname recule de 32 %, surtout parce que ses surfaces baissent.
- Par habitant, la Grand'Anse (81.4 kg par an) devance le Centre (74.6 kg) ; l'Ouest, le plus peuplé, est dernier (16.9 kg).

**Limites des données** :

- Les données sont fictives, sur trois ans seulement, avec 376 relevés : trop peu pour parler de tendance.
- 18 lignes en double et 14 relevés sans production ont été supprimés : la production réelle est un peu sous-estimée.
- Le riz n'est cultivé que dans cinq départements : on ne peut pas le comparer partout.
- La pluie est mesurée par saison : on ne voit ni les sécheresses ni les orages d'un mois.
- Chaque culture a un seul prix : la valeur ne tient pas compte des variations de prix.
- Une corrélation entre la pluie et le rendement ne prouve pas que la pluie en est la cause.
"""
)

with st.expander("Voir les données filtrées"):
    st.dataframe(df, hide_index=True)
