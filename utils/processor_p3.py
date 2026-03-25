from __future__ import annotations

import pandas as pd

from utils.helpers import (
    build_common_base,
    canonical_person_name,
    read_excel_from_state,
)

ASTREINTE_RUBRIQUES = [
    "ASBDF-ASTREINTE ADM DIM & JRS FERIES (ADMIN)",
    "ASBSE-ASTREINTE ADM SEMAINE (ADMIN)",
    "ASTDF-ASTREINTE DIM & JRS FERIES (PREEF)",
    "ASTSE-ASTREINTE SEMAINE (PREEF)",
]


def _normalize_colname(col: str) -> str:
    return str(col).strip().lower()


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str:
    normalized = {_normalize_colname(c): c for c in df.columns}
    for candidate in candidates:
        key = _normalize_colname(candidate)
        if key in normalized:
            return normalized[key]
    raise KeyError(f"Colonne introuvable parmi : {candidates}")


def _to_numeric_series(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("\xa0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def _merge_metrics(base: pd.DataFrame, agg: pd.DataFrame, metric_cols: list[str]) -> pd.DataFrame:
    out = base.merge(agg, on="salarié_normalisé", how="left")
    for col in metric_cols:
        if col in out.columns:
            out[col] = out[col].fillna(0.0)
    return out


def _prepare_astreintes_df(file_key: str) -> pd.DataFrame:
    df = read_excel_from_state(file_key).copy()
    df.columns = [str(c).strip() for c in df.columns]

    col_rubrique = _find_column(df, ["Rubrique"])
    col_salarie = _find_column(df, ["Salarié", "Salarie"])
    col_heures = _find_column(df, ["nb heures", "Nb heures", "heures", "Heures"])
    col_date_debut = _find_column(df, ["Date Début", "Date Debut"])
    col_date_fin = _find_column(df, ["Date Fin"])
    col_heure_debut = _find_column(df, ["Heure Début", "Heure Debut"])
    col_heure_fin = _find_column(df, ["Heure Fin"])

    out = df[
        [
            col_rubrique,
            col_salarie,
            col_heures,
            col_date_debut,
            col_date_fin,
            col_heure_debut,
            col_heure_fin,
        ]
    ].copy()

    out.columns = [
        "rubrique",
        "salarié",
        "heures",
        "date_debut",
        "date_fin",
        "heure_debut",
        "heure_fin",
    ]

    out["rubrique"] = out["rubrique"].astype(str).str.strip()

    # garder uniquement les vraies lignes salariés
    out = out[out["salarié"].notna()].copy()
    out["salarié"] = out["salarié"].astype(str).str.strip()
    out = out[out["salarié"] != ""].copy()
    out = out[out["salarié"].str.lower() != "nan"].copy()

    # exclure les lignes de détail (celles avec dates/heures remplies)
    mask_ligne_recap_salarie = (
        out["date_debut"].isna()
        & out["date_fin"].isna()
        & out["heure_debut"].isna()
        & out["heure_fin"].isna()
    )
    out = out[mask_ligne_recap_salarie].copy()

    out["salarié_normalisé"] = out["salarié"].apply(canonical_person_name)
    out["heures"] = _to_numeric_series(out["heures"])

    return out


def process_page_3() -> pd.DataFrame:
    base = build_common_base()

    df = _prepare_astreintes_df("perceval_astreintes")
    df = df[df["rubrique"].isin(ASTREINTE_RUBRIQUES)].copy()

    agg = (
        df.groupby(["salarié_normalisé", "rubrique"], as_index=False)["heures"]
        .sum()
    )

    wide = agg.pivot(
        index="salarié_normalisé",
        columns="rubrique",
        values="heures",
    ).fillna(0.0).reset_index()

    for col in ASTREINTE_RUBRIQUES:
        if col not in wide.columns:
            wide[col] = 0.0

    wide = wide[["salarié_normalisé"] + ASTREINTE_RUBRIQUES]

    out = _merge_metrics(base, wide, ASTREINTE_RUBRIQUES)

    return out.sort_values("salarié", ascending=True).reset_index(drop=True)
