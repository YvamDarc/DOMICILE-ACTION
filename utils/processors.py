from __future__ import annotations

import pandas as pd

from utils.helpers import (
    build_common_base,
    canonical_person_name,
    merge_metric,
    read_excel_from_state,
)

PRESTATION_RUBRIQUES = [
    "DJF-Actes Essentiels DJF (PREEF)",
    "TRAD-Temps Trajet Dim & Férié (PREEF)",
    "TDAST-Temps effectif astreinte Dim (ADMIN)",
]

METRIC_H_DIM_ECR = "H DIM ECR"


def _normalize_colname(col: str) -> str:
    return str(col).strip().lower()


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str:
    normalized = {_normalize_colname(c): c for c in df.columns}
    for candidate in candidates:
        key = _normalize_colname(candidate)
        if key in normalized:
            return normalized[key]
    raise KeyError(f"Colonne introuvable parmi : {candidates}")


def _prepare_perceval_df(file_key: str) -> pd.DataFrame:
    df = read_excel_from_state(file_key).copy()
    df.columns = [str(c).strip() for c in df.columns]

    col_rubrique = _find_column(df, ["Rubrique"])
    col_salarie = _find_column(df, ["Salarié", "Salarie"])
    col_heures = _find_column(df, ["nb heures", "Nb heures", "heures", "Heures"])

    out = df[[col_rubrique, col_salarie, col_heures]].copy()
    out.columns = ["rubrique", "salarié", "heures"]

    out["rubrique"] = out["rubrique"].astype(str).str.strip()

    # garder uniquement les vraies lignes salariés
    out = out[out["salarié"].notna()].copy()
    out["salarié"] = out["salarié"].astype(str).str.strip()
    out = out[out["salarié"] != ""].copy()
    out = out[out["salarié"].str.lower() != "nan"].copy()

    # normalisation de la clé de jointure
    out["salarié_normalisé"] = out["salarié"].apply(canonical_person_name)

    # conversion robuste des heures
    out["heures"] = (
        out["heures"]
        .astype(str)
        .str.replace("\xa0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    out["heures"] = pd.to_numeric(out["heures"], errors="coerce").fillna(0.0)

    return out


def _aggregate_hours_by_rubriques(
    file_key: str,
    rubriques: list[str],
    metric_name: str,
) -> pd.DataFrame:
    df = _prepare_perceval_df(file_key)
    df = df[df["rubrique"].isin(rubriques)].copy()

    agg = (
        df.groupby("salarié_normalisé", as_index=False)["heures"]
        .sum()
        .rename(columns={"heures": metric_name})
    )

    return agg


def process_page_2() -> pd.DataFrame:
    base = build_common_base()

    agg = _aggregate_hours_by_rubriques(
        file_key="perceval_prestations",
        rubriques=PRESTATION_RUBRIQUES,
        metric_name=METRIC_H_DIM_ECR,
    )

    out = merge_metric(base, agg, METRIC_H_DIM_ECR)

    return (
        out.sort_values([METRIC_H_DIM_ECR, "salarié"], ascending=[False, True])
        .reset_index(drop=True)
    )
