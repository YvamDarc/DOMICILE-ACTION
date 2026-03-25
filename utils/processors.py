from __future__ import annotations

from typing import Iterable, List
import streamlit as st
import pandas as pd

from utils.helpers import (
    build_common_base,
    canonical_person_name,
    merge_metric,
    read_excel_from_state,
    to_float,
)


PRESTATION_RUBRIQUES = ["DJF-Actes Essentiels DJF (PREEF)",
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

def _aggregate_hours_by_rubriques_multi_columns(
    file_key: str,
    rubriques: list[str],
    rename_map: dict[str, str],
) -> pd.DataFrame:
    df = get_uploaded_df(file_key).copy()

    df.columns = [str(c).strip() for c in df.columns]

    df = df[df["Rubrique"].isin(rubriques)].copy()
    df = df[df["Salarié"].notna()].copy()

    df["Salarié"] = df["Salarié"].astype(str).str.strip()

    df["nb heures"] = (
        df["nb heures"]
        .astype(str)
        .str.replace("\xa0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["nb heures"] = pd.to_numeric(df["nb heures"], errors="coerce").fillna(0)

    agg = (
        df.groupby(["Salarié", "Rubrique"], as_index=False)["nb heures"]
        .sum()
    )

    wide = agg.pivot(index="Salarié", columns="Rubrique", values="nb heures").fillna(0)
    wide = wide.rename(columns=rename_map).reset_index()
    wide = wide.rename(columns={"Salarié": "salarié"})

    for col in rename_map.values():
        if col not in wide.columns:
            wide[col] = 0.0

    cols = ["salarié"] + list(rename_map.values())
    return wide[cols]

def process_page_2() -> pd.DataFrame:
    base = build_common_base()
    agg = _aggregate_hours_by_rubriques(
        file_key="perceval_prestations",
        rubriques=PRESTATION_RUBRIQUES,
        metric_name=METRIC_H_DIM_ECR,
    )
    out = merge_metric(base, agg, METRIC_H_DIM_ECR)
    return out.sort_values([METRIC_H_DIM_ECR, "salarié"], ascending=[False, True]).reset_index(drop=True)

def merge_metrics(base: pd.DataFrame, agg: pd.DataFrame, metric_cols: list[str]) -> pd.DataFrame:
    out = base.merge(agg, on="salarié", how="left")
    for col in metric_cols:
        if col in out.columns:
            out[col] = out[col].fillna(0)
    return out

