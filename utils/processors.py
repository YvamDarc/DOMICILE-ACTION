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

ASTREINTE_RUBRIQUES = [
    "DJF-Actes Essentiels DJF (PREEF)",
    "TRAD-Temps Trajet Dim & Férié (PREEF)",
    "TDAST-Temps effectif astreinte Dim (ADMIN)",
]

ASTREINTE_RENAME = {
    "DJF-Actes Essentiels DJF (PREEF)": "H DIM ECR",
    "TRAD-Temps Trajet Dim & Férié (PREEF)": "H DIM TRAJET",
    "TDAST-Temps effectif astreinte Dim (ADMIN)": "H ASTREINTE DIM",
}

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

    # On garde uniquement les vraies lignes salariés
    out = out[out["salarié"].notna()].copy()
    out["salarié"] = out["salarié"].astype(str).str.strip()
    out = out[out["salarié"] != ""].copy()
    out = out[out["salarié"].str.lower() != "nan"].copy()

    # Normalisation des noms
    out["salarié"] = out["salarié"].apply(canonical_person_name)

    # Conversion robuste des heures
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
        df.groupby("salarié", as_index=False)["heures"]
        .sum()
        .rename(columns={"heures": metric_name})
    )

    return agg


def _aggregate_hours_by_rubriques_multi_columns(
    file_key: str,
    rubriques: list[str],
    rename_map: dict[str, str],
) -> pd.DataFrame:
    df = _prepare_perceval_df(file_key)

    df = df[df["rubrique"].isin(rubriques)].copy()

    agg = (
        df.groupby(["salarié", "rubrique"], as_index=False)["heures"]
        .sum()
    )

    wide = agg.pivot(index="salarié", columns="rubrique", values="heures").fillna(0.0)
    wide = wide.rename(columns=rename_map).reset_index()

    # Garantit la présence de toutes les colonnes attendues
    for col in rename_map.values():
        if col not in wide.columns:
            wide[col] = 0.0

    return wide[["salarié"] + list(rename_map.values())]


def merge_metrics(base: pd.DataFrame, agg: pd.DataFrame, metric_cols: list[str]) -> pd.DataFrame:
    out = base.merge(agg, on="salarié", how="left")
    for col in metric_cols:
        if col in out.columns:
            out[col] = out[col].fillna(0.0)
    return out


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


def process_page_3() -> pd.DataFrame:
    base = build_common_base()

    agg = _aggregate_hours_by_rubriques_multi_columns(
        file_key="perceval_astreintes",
        rubriques=ASTREINTE_RUBRIQUES,
        rename_map=ASTREINTE_RENAME,
    )

    out = merge_metrics(base, agg, list(ASTREINTE_RENAME.values()))

    return out.sort_values("salarié", ascending=True).reset_index(drop=True)
