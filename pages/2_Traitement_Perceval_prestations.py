import streamlit as st

from utils.helpers import dataframe_download_bytes
from utils.processors import PRESTATION_RUBRIQUES, process_page_2

st.title("Page 2 - Traitement du tableau Perceval prestations")
st.markdown("Cette page traite le fichier **ok 3-2026 02 Export Perceval Prestations rubriques salaries DAA**.")

st.write("Rubriques visées :")
st.code("\n".join(PRESTATION_RUBRIQUES))

try:
    result = process_page_2()
except FileNotFoundError:
    st.warning("Le fichier Perceval prestations n'est pas encore importé.")
    st.stop()
except Exception as e:
    st.error(f"Erreur de traitement : {e}")
    st.stop()

# 👉 Arrondi global à 2 décimales (uniquement colonnes numériques)
result = result.copy()
numeric_cols = result.select_dtypes(include="number").columns
result[numeric_cols] = result[numeric_cols].round(2)

st.subheader("Dataframe commun enrichi")

# 👉 Affichage propre avec 2 décimales
st.dataframe(
    result.style.format({col: "{:.2f}" for col in numeric_cols}),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Télécharger le résultat CSV",
    data=dataframe_download_bytes(result),
    file_name="page_2_perceval_prestations.csv",
    mime="text/csv",
)
