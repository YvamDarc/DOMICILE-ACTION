import streamlit as st

st.set_page_config(page_title="Récap DAA", page_icon="📊", layout="wide")

st.title("Récap DAA - contrôles et consolidation")
st.markdown(
    """
Cette application prépare un **dataframe commun salariés** à partir des exports Perceval, Lancelot,
Variables individuelles, frais/km, puis plus tard du tableau **Silae**.

Utilise le menu de gauche pour naviguer entre les pages.
"""
)

st.subheader("Plan prévu")
st.markdown(
    """
- **Page 1 - Import des fichiers**
- **Page 2 - Traitement Perceval prestations**
- **Page 3 - Traitement Perceval astreintes**
- **Page 4 - 2026 export Perceval / consolidation future**
"""
)

st.info("Le code fonctionne même si tous les tableaux ne sont pas encore importés. Les pages concernées affichent simplement un message propre quand un fichier manque.")
