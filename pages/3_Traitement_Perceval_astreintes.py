import streamlit as st

from utils.helpers import dataframe_download_bytes
from utils.processor_p3 import ASTREINTE_RUBRIQUES, process_page_3

st.title("Page 3 - Traitement du tableau Perceval astreintes")
st.markdown("Cette page traite le fichier **ok 4-2026 02 Export Perceval astreintes salaries DAA**.")

st.write("Rubriques visées :")
st.code("\n".join(ASTREINTE_RUBRIQUES))

try:
    result = process_page_3()
except FileNotFoundError:
    st.warning("Le fichier Perceval astreintes n'est pas encore importé.")
    st.stop()
except Exception as e:
    st.error(f"Erreur de traitement : {e}")
    st.stop()

result = result.copy()
numeric_cols = result.select_dtypes(include="number").columns
result[numeric_cols] = result[numeric_cols].round(2)

st.subheader("Dataframe commun enrichi")
st.dataframe(
    result.style.format({col: "{:.2f}" for col in numeric_cols}),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Télécharger le résultat CSV",
    data=dataframe_download_bytes(result),
    file_name="page_3_perceval_astreintes.csv",
    mime="text/csv",
)
