import streamlit as st

from utils.helpers import dataframe_download_bytes
from utils.processors import ASTREINTE_RUBRIQUES, TARGET_NAMES, process_page_3

st.title("Page 3 - Traitement du tableau Perceval astreintes")
st.markdown("Cette page traite le fichier **ok 4-2026 02 Export Perceval astreintes salaries DAA**.")

st.write("Rubriques visées :")
st.code("\n".join(ASTREINTE_RUBRIQUES))

st.write("Salariées suivies :")
st.code("\n".join(TARGET_NAMES))

try:
    result = process_page_3()
except FileNotFoundError:
    st.warning("Le fichier Perceval astreintes n'est pas encore importé.")
    st.stop()
except Exception as e:
    st.error(f"Erreur de traitement : {e}")
    st.stop()

st.subheader("Dataframe commun enrichi")
st.dataframe(result, use_container_width=True, hide_index=True)

st.download_button(
    "Télécharger le résultat CSV",
    data=dataframe_download_bytes(result),
    file_name="page_3_perceval_astreintes.csv",
    mime="text/csv",
)
