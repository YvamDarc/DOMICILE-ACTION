def process_page_3() -> pd.DataFrame:

    df = _prepare_astreintes_df("perceval_astreintes")

    # 👉 filtre sur les rubriques
    df = df[df["rubrique"].isin(ASTREINTE_RUBRIQUES)].copy()

    # 👉 base dynamique = salariés du fichier
    base = df[["salarié", "salarié_normalisé"]].drop_duplicates()

    # 👉 agrégation
    agg = (
        df.groupby(["salarié_normalisé", "rubrique"], as_index=False)["heures"]
        .sum()
    )

    # 👉 pivot
    wide = agg.pivot(
        index="salarié_normalisé",
        columns="rubrique",
        values="heures",
    ).fillna(0.0).reset_index()

    # 👉 garantir les colonnes
    for col in ASTREINTE_RUBRIQUES:
        if col not in wide.columns:
            wide[col] = 0.0

    # 👉 merge avec base dynamique
    out = base.merge(wide, on="salarié_normalisé", how="left")

    # 👉 remettre salarié lisible
    out = out.fillna(0.0)

    return out.sort_values("salarié", ascending=True).reset_index(drop=True)
