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

ASTREINTE_RENAME = {
    "DJF-Actes Essentiels DJF (PREEF)": "H DIM ECR",
    "TRAD-Temps Trajet Dim & Férié (PREEF)": "H DIM TRAJET",
    "TDAST-Temps effectif astreinte Dim (ADMIN)": "H ASTREINTE DIM",
}

METRIC_H_DIM_ECR = "H DIM ECR"

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
        metric_name=METRIC_H_DIM_ECR,
    )
    out = merge_metric(base, agg, METRIC_H_DIM_ECR)
    return out.sort_values([METRIC_H_DIM_ECR, "salarié"], ascending=[False, True]).reset_index(drop=True)

def process_page_3() -> pd.DataFrame:
    base = build_common_base()

    if "perceval_astreintes" not in st.session_state:
        raise FileNotFoundError("Le fichier Perceval astreintes n'est pas encore importé.")

    df = st.session_state["perceval_astreintes"].copy()

    # Normalisation minimale des noms de colonnes
    df.columns = [str(c).strip() for c in df.columns]

    # On garde uniquement les lignes utiles
    df = df[df["Rubrique"].isin(ASTREINTE_RUBRIQUES)].copy()

    # On garde uniquement les lignes salariés
    df = df[df["Salarié"].notna()].copy()
    df["Salarié"] = df["Salarié"].astype(str).str.strip()

    # Sécurisation nb heures
    df["nb heures"] = (
        df["nb heures"]
        .astype(str)
        .str.replace("\xa0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["nb heures"] = pd.to_numeric(df["nb heures"], errors="coerce").fillna(0)

    # Agrégation salarié + rubrique
    agg = (
        df.groupby(["Salarié", "Rubrique"], as_index=False)["nb heures"]
        .sum()
    )

    # Pivot : une colonne par rubrique
    wide = agg.pivot(index="Salarié", columns="Rubrique", values="nb heures").fillna(0)

    # Renommage des colonnes métier
    wide = wide.rename(columns=ASTREINTE_RENAME).reset_index()

    # Harmonisation du nom de colonne salarié
    wide = wide.rename(columns={"Salarié": "salarié"})

    # On s'assure que les 3 colonnes existent toujours
    for col in ASTREINTE_RENAME.values():
        if col not in wide.columns:
            wide[col] = 0.0

    # Merge avec la base commune
    out = base.merge(wide, on="salarié", how="left")

    # Remplacement des NaN par 0 sur les colonnes numériques ajoutées
    for col in ASTREINTE_RENAME.values():
        out[col] = out[col].fillna(0)

    return out.sort_values("salarié").reset_index(drop=True)
