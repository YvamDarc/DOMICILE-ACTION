import streamlit as st
import pandas as pd

st.title("Page 2 - Traitement du tableau Perceval prestations")

if "perceval_prestations" in st.session_state:

    df = st.session_state["perceval_prestations"]

    # Nettoyage colonnes (adaptable selon ton fichier réel)
    df.columns = [c.strip() for c in df.columns]

    # Normalisation noms
    df["SALARIE"] = (
        df["Nom"].str.strip().str.upper()
        + " "
        + df["Prénom"].str.strip().str.upper()
    )

    # 🎯 Les 3 rubriques demandées
    rubriques_cibles = [
        "DJF-Actes Essentiels DJF (PREEF)",
        "TRAD-Temps Trajet Dim & Férié (PREEF)",
        "TDAST-Temps effectif astreinte Dim (ADMIN)"
    ]

    # Filtrage
    df_filtre = df[df["Rubrique"].isin(rubriques_cibles)]

    # Agrégation
    recap = (
        df_filtre
        .groupby(["SALARIE", "Rubrique"])["Heures"]
        .sum()
        .reset_index()
    )

    # Pivot pour affichage propre
    recap_pivot = recap.pivot(
        index="SALARIE",
        columns="Rubrique",
        values="Heures"
    ).fillna(0)

    # Total
    recap_pivot["TOTAL"] = recap_pivot.sum(axis=1)

    st.subheader("Récapitulatif des heures par salarié")
    st.dataframe(recap_pivot)

else:
    st.warning("Veuillez importer le fichier Perceval prestations dans la page 1.")
