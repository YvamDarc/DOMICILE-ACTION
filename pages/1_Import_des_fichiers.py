import streamlit as st

from utils.helpers import EXPECTED_FILES, UPLOAD_LABELS, save_upload, uploaded_status_df

st.title("Page 1 - Import des fichiers")
st.caption("Un bouton d'import par tableau. Les traitements restent utilisables même si certains fichiers manquent.")

for key, label in UPLOAD_LABELS.items():
    with st.expander(label, expanded=key in ["perceval_prestations", "perceval_astreintes", "variables_individuelles"]):
        st.write(f"Fichier attendu : **{EXPECTED_FILES[key]}**")
        uploaded = st.file_uploader(
            f"Importer {label}",
            type=["xlsx", "xls", "csv"],
            key=f"uploader_{key}",
        )
        if uploaded is not None:
            save_upload(key, uploaded)
            st.success(f"Fichier chargé : {uploaded.name}")

st.subheader("État des imports")
st.dataframe(uploaded_status_df(), use_container_width=True, hide_index=True)
