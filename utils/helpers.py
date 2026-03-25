from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd
import streamlit as st

EXPECTED_FILES = {
    "perceval_prestations": "ok 3-2026 02 Export Perceval Prestations rubriques salaries DAA.xlsx",
    "perceval_astreintes": "ok 4-2026 02 Export Perceval astreintes salaries DAA.xlsx",
    "variables_individuelles": "ok 2026-02 Variables individuelles.xls",
    "frais_km": "ok 2026 Récap Frais et Km.xlsx",
    "lancelot_heures_1": "ok 6 1 – 2026 02 Export Lancelot HEURES SALARIEES EXO NON EXO DAA ad.xls",
    "lancelot_heures_2": "ok 6 2 – 2026 02 Export Lancelot HEURES SALARIEES EXO NON EXO DAA ad.xls",
    "sylae": "tableau sylae à venir",
}

UPLOAD_LABELS = {
    "perceval_prestations": "Tableau 1 - Perceval prestations rubriques salariés",
    "perceval_astreintes": "Tableau 2 - Perceval astreintes salariés",
    "variables_individuelles": "Tableau 3 - Variables individuelles",
    "frais_km": "Tableau 4 - Récap frais et km",
    "lancelot_heures_1": "Tableau 5 - Lancelot heures salariées exo/non exo (fichier 1)",
    "lancelot_heures_2": "Tableau 6 - Lancelot heures salariées exo/non exo (fichier 2)",
    "sylae": "Tableau 7 - Récap paie Silae (à venir)",
}


def ensure_state() -> None:
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {}



def get_uploaded_bytes(key: str) -> Optional[bytes]:
    ensure_state()
    item = st.session_state.uploaded_files.get(key)
    if item is None:
        return None
    return item["content"]



def save_upload(key: str, uploaded_file) -> None:
    ensure_state()
    if uploaded_file is None:
        return
    st.session_state.uploaded_files[key] = {
        "name": uploaded_file.name,
        "content": uploaded_file.getvalue(),
    }



def uploaded_status_df() -> pd.DataFrame:
    ensure_state()
    rows = []
    for key, label in UPLOAD_LABELS.items():
        info = st.session_state.uploaded_files.get(key)
        rows.append(
            {
                "clé": key,
                "tableau": label,
                "fichier attendu": EXPECTED_FILES[key],
                "statut": "Importé" if info else "Absent",
                "fichier importé": info["name"] if info else "",
            }
        )
    return pd.DataFrame(rows)



def read_excel_from_state(key: str, sheet_name=0, **kwargs) -> pd.DataFrame:
    content = get_uploaded_bytes(key)
    if content is None:
        raise FileNotFoundError(f"Aucun fichier importé pour la clé '{key}'.")

    suffix = Path(st.session_state.uploaded_files[key]["name"]).suffix.lower()
    engine = None
    if suffix == ".xls":
        engine = "xlrd"
    elif suffix == ".xlsx":
        engine = "openpyxl"

    return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name, engine=engine, **kwargs)



def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper()
    text = re.sub(r"\s+", " ", text)
    return text.strip()



def canonical_person_name(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    parts = text.split(" ")
    if len(parts) >= 2:
        last = " ".join(parts[:-1])
        first = parts[-1]
        return f"{last} {first}".strip()
    return text



def to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)



def base_employees_from_variables() -> pd.DataFrame:
    df = read_excel_from_state("variables_individuelles", sheet_name="Variables de paie")
    df.columns = [str(c).strip() for c in df.columns]
    needed = [c for c in ["Matricule", "nom", "prenom", "SECTEUR", "Emploi"] if c in df.columns]
    out = df[needed].copy()
    rename_map = {"Matricule": "matricule", "nom": "nom", "prenom": "prenom", "SECTEUR": "secteur", "Emploi": "emploi"}
    out = out.rename(columns=rename_map)
    out = out[(out.get("nom", "") != "") & (out.get("prenom", "") != "")].copy()
    out["nom"] = out["nom"].astype(str).str.strip()
    out["prenom"] = out["prenom"].astype(str).str.strip()
    out["salarié"] = out["nom"] + " " + out["prenom"]
    out["salarié_normalisé"] = out["salarié"].map(canonical_person_name)
    if "matricule" in out.columns:
        out["matricule"] = out["matricule"].astype(str).str.strip()
    return out.drop_duplicates(subset=["salarié_normalisé"]).reset_index(drop=True)



def fallback_employees_from_sheet(df: pd.DataFrame, employee_col: str) -> pd.DataFrame:
    employees = df[[employee_col]].copy()
    employees = employees.dropna().drop_duplicates()
    employees["salarié"] = employees[employee_col].astype(str).str.strip()
    employees["salarié_normalisé"] = employees["salarié"].map(canonical_person_name)
    return employees[["salarié", "salarié_normalisé"]].reset_index(drop=True)



def build_common_base() -> pd.DataFrame:
    try:
        base = base_employees_from_variables()
    except Exception:
        base = pd.DataFrame(columns=["salarié", "salarié_normalisé", "matricule", "secteur", "emploi"])

    if not base.empty:
        return base

    for key in ["perceval_prestations", "perceval_astreintes"]:
        try:
            df = read_excel_from_state(key, sheet_name="A")
            if "Salarié" in df.columns:
                return fallback_employees_from_sheet(df, "Salarié")
        except Exception:
            pass

    return pd.DataFrame(columns=["salarié", "salarié_normalisé", "matricule", "secteur", "emploi"])



def merge_metric(base_df: pd.DataFrame, metric_df: pd.DataFrame, metric_col: str) -> pd.DataFrame:
    if metric_df.empty:
        out = base_df.copy()
        out[metric_col] = 0.0
        return out
    out = base_df.merge(metric_df[["salarié_normalisé", metric_col]], on="salarié_normalisé", how="left")
    out[metric_col] = out[metric_col].fillna(0.0)
    return out



def dataframe_download_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
