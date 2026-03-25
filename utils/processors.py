from __future__ import annotations

from typing import Iterable, List

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


def _aggregate_hours_by_rubriques(file_key: str, rubriques: List[str], target_names: List[str] | None = None, metric_name: str = "heures") -> pd.DataFrame:
    df = read_excel_from_state(file_key, sheet_name="A")
    required_cols = ["Rubrique", "Salarié", "nb heures"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans le fichier : {', '.join(missing)}")

    work = df[required_cols].copy()
    work = work.dropna(subset=["Rubrique", "Salarié"])
    work["rubrique_normalisée"] = work["Rubrique"].map(canonical_person_name)
    work["salarié_normalisé"] = work["Salarié"].map(canonical_person_name)
    work["nb heures"] = to_float(work["nb heures"])

    rubric_norm = {canonical_person_name(x) for x in rubriques}
    work = work[work["rubrique_normalisée"].isin(rubric_norm)].copy()

    if target_names:
        target_norm = {canonical_person_name(x) for x in target_names}
        work = work[work["salarié_normalisé"].isin(target_norm)].copy()

    agg = (
        work.groupby(["salarié_normalisé"], as_index=False)["nb heures"]
        .sum()
        .rename(columns={"nb heures": metric_name})
    )
    return agg.sort_values(metric_name, ascending=False).reset_index(drop=True)



def process_page_2() -> pd.DataFrame:
    base = build_common_base()
    agg = _aggregate_hours_by_rubriques(
        file_key="perceval_prestations",
        rubriques=PRESTATION_RUBRIQUES,
        metric_name="heures_djf_preef",
    )
    out = merge_metric(base, agg, "heures_djf_preef")
    return out.sort_values(["heures_djf_preef", "salarié"], ascending=[False, True]).reset_index(drop=True)



def process_page_3() -> pd.DataFrame:
    base = build_common_base()
    agg = _aggregate_hours_by_rubriques(
        file_key="perceval_astreintes",
        rubriques=ASTREINTE_RUBRIQUES,
        target_names=TARGET_NAMES,
        metric_name="heures_astreintes_dim",
    )
    out = merge_metric(base, agg, "heures_astreintes_dim")
    return out.sort_values(["heures_astreintes_dim", "salarié"], ascending=[False, True]).reset_index(drop=True)
