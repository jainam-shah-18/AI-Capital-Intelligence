
from __future__ import annotations

from datetime import date, timedelta
import math
from typing import Any

import pandas as pd

TAG_CANDIDATES = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "Revenues",
    ],
    "operating_income": ["OperatingIncomeLoss"],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "NetCashProvidedByUsedInOperatingActivities",
    ],
    "capital_expenditure": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "net_income": ["NetIncomeLoss"],
}

ACCEPTED_FORMS = {"10-Q", "10-K", "20-F", "40-F"}
ANNUAL_FORMS = {"10-K", "20-F", "40-F"}
SUPPORTED_PERIOD_TYPES = {
    "quarter", "year_to_date", "annual", "rolling_12_month"
}

OUTPUT_COLUMNS = [
    "ticker", "company_name", "metric", "xbrl_tag", "tag_priority",
    "period_type", "period_start", "period_end", "period_days",
    "filing_fiscal_year", "filing_fiscal_period", "form", "filed_date",
    "accession_number", "currency", "reported_value_usd", "value_usd",
    "source",
]


def _period_type(
    start: str | None,
    end: str,
    form: str | None = None,
) -> str | None:
    """Classify SEC duration facts by inclusive calendar duration."""
    if not start:
        return "instant"

    try:
        days = (
            date.fromisoformat(end) - date.fromisoformat(start)
        ).days + 1
    except (TypeError, ValueError):
        return None

    if 70 <= days <= 110:
        return "quarter"
    if 120 <= days <= 310:
        return "year_to_date"
    if 330 <= days <= 380:
        return "annual" if form in ANNUAL_FORMS else "rolling_12_month"

    return None


def extract_financial_metrics(
    companyfacts: dict[str, Any],
    ticker: str,
    company_name: str,
) -> pd.DataFrame:
    """Extract supported USD observations, retaining all candidate tags."""
    rows: list[dict[str, Any]] = []
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})

    for metric, candidates in TAG_CANDIDATES.items():
        for priority, tag in enumerate(candidates):
            fact = us_gaap.get(tag)

            if not fact:
                continue

            for obs in fact.get("units", {}).get("USD", []):
                start = obs.get("start")
                end = obs.get("end")
                form = obs.get("form")
                value = obs.get("val")

                if not end or value is None or form not in ACCEPTED_FORMS:
                    continue

                period_type = _period_type(start, end, form)

                if period_type not in SUPPORTED_PERIOD_TYPES:
                    continue

                try:
                    period_days = (
                        date.fromisoformat(end)
                        - date.fromisoformat(start)
                    ).days + 1

                    reported_value = float(value)
                except (TypeError, ValueError):
                    continue

                normalized_value = (
                    abs(reported_value)
                    if metric == "capital_expenditure"
                    else reported_value
                )

                rows.append({
                    "ticker": ticker,
                    "company_name": company_name,
                    "metric": metric,
                    "xbrl_tag": tag,
                    "tag_priority": priority,
                    "period_type": period_type,
                    "period_start": start,
                    "period_end": end,
                    "period_days": period_days,
                    "filing_fiscal_year": obs.get("fy"),
                    "filing_fiscal_period": obs.get("fp"),
                    "form": form,
                    "filed_date": obs.get("filed"),
                    "accession_number": obs.get("accn"),
                    "currency": "USD",
                    "reported_value_usd": reported_value,
                    "value_usd": normalized_value,
                    "source": "SEC EDGAR Company Facts",
                    "data_status": "REPORTED",
                })

    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS + ["data_status"])

    df = pd.DataFrame(rows)

    exact_duplicate_columns = [
        "ticker", "metric", "xbrl_tag", "period_start", "period_end",
        "form", "accession_number", "reported_value_usd",
    ]

    df = df.drop_duplicates(
        subset=exact_duplicate_columns,
        keep="last",
    )

    return df.sort_values(
        [
            "ticker", "metric", "period_end",
            "tag_priority", "filed_date", "accession_number",
        ],
        na_position="last",
    ).reset_index(drop=True)


def _as_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)) if pd.notna(value) else None
    except (TypeError, ValueError):
        return None


def _asof_compatible_pair(
    current: pd.Series,
    prior_candidates: pd.DataFrame,
) -> pd.Series | None:
    """Choose the latest prior cumulative fact known by current filing date."""
    current_filed = _as_date(current.get("filed_date"))
    candidates = prior_candidates.copy()

    if current_filed is not None and "filed_date" in candidates:
        candidates = candidates[
            candidates["filed_date"].map(_as_date).map(
                lambda d: d is None or d <= current_filed
            )
        ]

    if candidates.empty:
        return None

    candidates["_filed_sort"] = candidates.get(
        "filed_date",
        pd.Series(index=candidates.index, dtype=object),
    ).fillna("")

    candidates = candidates.sort_values(
        ["period_end", "_filed_sort"]
    )

    return candidates.iloc[-1]


def _reconstruct_quarters(
    observations: pd.DataFrame,
) -> pd.DataFrame:
    """Reconstruct missing quarters from compatible cumulative observations.

    Matching requires the same ticker, metric, XBRL tag and fiscal-period
    start. Prior cumulative observations must have been filed no later
    than the current observation.
    """
    if observations.empty:
        return observations.copy()

    generated: list[dict[str, Any]] = []

    reported_quarter_keys = set(
        tuple(row)
        for row in observations.loc[
            observations["period_type"].eq("quarter"),
            [
                "ticker", "metric", "xbrl_tag",
                "period_start", "period_end",
            ],
        ].itertuples(index=False, name=None)
    )

    group_cols = [
        "ticker", "metric", "xbrl_tag", "period_start"
    ]

    for _, group in observations.groupby(
        group_cols,
        dropna=False,
        sort=False,
    ):
        group = group.copy()

        cumulative = group[
            group["period_type"].isin(["year_to_date", "annual"])
        ]

        if cumulative.empty:
            continue

        for _, current in cumulative.iterrows():
            current_end = _as_date(current.get("period_end"))

            if current_end is None:
                continue

            previous = group[
                group["period_type"].isin(
                    ["quarter", "year_to_date"]
                )
                & group["period_end"].map(_as_date).map(
                    lambda d: d is not None and d < current_end
                )
            ]

            if current["period_type"] == "annual":
                previous = previous[
                    previous["period_type"].eq("year_to_date")
                ]

            prior = _asof_compatible_pair(current, previous)

            if prior is None:
                continue

            prior_end = _as_date(prior.get("period_end"))

            if prior_end is None or prior_end >= current_end:
                continue

            quarter_start = prior_end + timedelta(days=1)
            quarter_end = current_end

            quarter_days = (
                quarter_end - quarter_start
            ).days + 1

            if not 70 <= quarter_days <= 110:
                continue

            reported_key = (
                current.get("ticker"),
                current.get("metric"),
                current.get("xbrl_tag"),
                quarter_start.isoformat(),
                quarter_end.isoformat(),
            )

            if reported_key in reported_quarter_keys:
                continue

            row = current.to_dict()

            row.update({
                "period_type": "quarter",
                "period_start": quarter_start.isoformat(),
                "period_end": quarter_end.isoformat(),
                "period_days": quarter_days,
                "value_usd": (
                    float(current["value_usd"])
                    - float(prior["value_usd"])
                ),
                "reported_value_usd": pd.NA,
                "data_status": "DERIVED",
                "derivation_method": (
                    "current_cumulative_minus_previous_cumulative_same_tag_asof"
                ),
                "source_periods": (
                    f"{prior.get('period_start')}..{prior.get('period_end')}|"
                    f"{current.get('period_start')}..{current.get('period_end')}"
                ),
                "source_filed_dates": (
                    f"{prior.get('filed_date')}|{current.get('filed_date')}"
                ),
                "source_accession_numbers": "|".join(
                    str(value)
                    for value in [
                        prior.get("accession_number"),
                        current.get("accession_number"),
                    ]
                    if pd.notna(value) and str(value)
                ),
                "source": (
                    "Derived from SEC EDGAR Company Facts cumulative observations"
                ),
            })

            generated.append(row)

    if not generated:
        return observations.copy()

    combined_records = (
        observations.to_dict(orient="records") + generated
    )

    return pd.DataFrame(combined_records)


def _selection_order(frame: pd.DataFrame) -> pd.DataFrame:
    """Rank reported facts, tag priority and filing vintage."""
    ranked = frame.copy()

    ranked["_status_rank"] = (
        ranked.get(
            "data_status",
            pd.Series("REPORTED", index=ranked.index),
        )
        .fillna("REPORTED")
        .map({"REPORTED": 0, "DERIVED": 1})
        .fillna(2)
    )

    ranked["_tag_priority_rank"] = pd.to_numeric(
        ranked.get(
            "tag_priority",
            pd.Series(0, index=ranked.index),
        ),
        errors="coerce",
    ).fillna(999)

    ranked["_filed_sort"] = ranked.get(
        "filed_date",
        pd.Series("", index=ranked.index),
    ).fillna("").astype(str)

    ranked["_accession_sort"] = ranked.get(
        "accession_number",
        pd.Series("", index=ranked.index),
    ).fillna("").astype(str)

    return ranked.sort_values(
        [
            "_status_rank",
            "_tag_priority_rank",
            "_filed_sort",
            "_accession_sort",
        ],
        ascending=[True, True, False, False],
        kind="stable",
    )


def _select_vintage_compatible_rows(
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Select canonical observations, preferring a common OCF/capex filing."""
    if candidates.empty:
        return candidates.copy()

    period_keys = [
        "ticker", "period_type", "period_start", "period_end"
    ]

    selected_records: list[dict[str, Any]] = []

    for _, period_group in candidates.groupby(
        period_keys,
        dropna=False,
        sort=False,
    ):
        chosen: dict[str, pd.Series] = {}

        # Initially select the best candidate independently for each metric.
        for metric, metric_group in period_group.groupby(
            "metric",
            dropna=False,
            sort=False,
        ):
            ranked = _selection_order(metric_group)

            chosen[str(metric)] = ranked.iloc[0].drop(
                labels=[
                    "_status_rank",
                    "_tag_priority_rank",
                    "_filed_sort",
                    "_accession_sort",
                ],
                errors="ignore",
            )

        ocf_rows = period_group[
            period_group["metric"].eq("operating_cash_flow")
        ].copy()

        capex_rows = period_group[
            period_group["metric"].eq("capital_expenditure")
        ].copy()

        if not ocf_rows.empty and not capex_rows.empty:
            ocf_rows = ocf_rows[
                ocf_rows["accession_number"].notna()
            ]

            capex_rows = capex_rows[
                capex_rows["accession_number"].notna()
            ]

            if not ocf_rows.empty and not capex_rows.empty:
                pairs = ocf_rows.merge(
                    capex_rows,
                    on="accession_number",
                    suffixes=("_ocf", "_capex"),
                    how="inner",
                )

                if not pairs.empty:
                    for side in ("ocf", "capex"):
                        pairs[f"_status_{side}"] = (
                            pairs[f"data_status_{side}"]
                            .fillna("REPORTED")
                            .map({"REPORTED": 0, "DERIVED": 1})
                            .fillna(2)
                        )

                        pairs[f"_priority_{side}"] = pd.to_numeric(
                            pairs[f"tag_priority_{side}"],
                            errors="coerce",
                        ).fillna(999)

                        pairs[f"_filed_{side}"] = (
                            pairs[f"filed_date_{side}"]
                            .fillna("")
                            .astype(str)
                        )

                    pairs["_status_sum"] = (
                        pairs["_status_ocf"] + pairs["_status_capex"]
                    )

                    pairs["_priority_sum"] = (
                        pairs["_priority_ocf"] + pairs["_priority_capex"]
                    )

                    pairs["_latest_filed"] = pairs[
                        ["_filed_ocf", "_filed_capex"]
                    ].max(axis=1)

                    pairs = pairs.sort_values(
                        [
                            "_status_sum",
                            "_priority_sum",
                            "_latest_filed",
                            "_filed_ocf",
                            "_filed_capex",
                        ],
                        ascending=[
                            True, True, False, False, False
                        ],
                        kind="stable",
                    )

                    best_pair = pairs.iloc[0]
                    accession = best_pair["accession_number"]

                    best_ocf = _selection_order(
                        ocf_rows[
                            ocf_rows["accession_number"].eq(accession)
                        ]
                    ).iloc[0]

                    best_capex = _selection_order(
                        capex_rows[
                            capex_rows["accession_number"].eq(accession)
                        ]
                    ).iloc[0]

                    drop_columns = [
                        "_status_rank",
                        "_tag_priority_rank",
                        "_filed_sort",
                        "_accession_sort",
                    ]

                    chosen["operating_cash_flow"] = best_ocf.drop(
                        labels=drop_columns,
                        errors="ignore",
                    )

                    chosen["capital_expenditure"] = best_capex.drop(
                        labels=drop_columns,
                        errors="ignore",
                    )

        selected_records.extend(
            row.to_dict() for row in chosen.values()
        )

    if not selected_records:
        return pd.DataFrame(columns=candidates.columns)

    return pd.DataFrame(selected_records).reset_index(drop=True)


def resolve_duplicate_period_ends(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Resolve duplicate canonical periods without discarding source observations.

    The canonical key is ticker + period_type + period_end. Conflicting
    non-null financial values or tied completeness scores stop processing
    and require manual review.
    """
    if df.empty:
        return df.copy(), pd.DataFrame()

    result = df.copy().reset_index(drop=True)
    keys = ["ticker", "period_type", "period_end"]
    metric_columns = [
        "revenue",
        "operating_income",
        "net_income",
        "operating_cash_flow",
        "capital_expenditure",
        "free_cash_flow",
    ]
    available_metrics = [
        column for column in metric_columns if column in result.columns
    ]

    duplicate_rows = result.loc[result.duplicated(keys, keep=False)]
    if duplicate_rows.empty:
        return result, pd.DataFrame()

    keep_indices = set(result.index[~result.duplicated(keys, keep=False)])
    audit_records: list[dict[str, Any]] = []

    for group_key, group in duplicate_rows.groupby(
        keys, dropna=False, sort=False
    ):
        # Identical or missing values are acceptable; disagreements are not.
        for metric in available_metrics:
            values = pd.to_numeric(
                group[metric], errors="coerce"
            ).dropna().tolist()

            if len(values) > 1:
                reference_value = float(values[0])
                for value in values[1:]:
                    if not math.isclose(
                        reference_value,
                        float(value),
                        rel_tol=1e-9,
                        abs_tol=0.01,
                    ):
                        raise ValueError(
                            f"Conflicting {metric} values for canonical "
                            f"period {group_key}: {values}. Manual review required."
                        )

        scores = {
            idx: sum(pd.notna(row[column]) for column in available_metrics)
            for idx, row in group.iterrows()
        }
        highest_score = max(scores.values())
        winners = [
            idx for idx, score in scores.items()
            if score == highest_score
        ]

        if len(winners) != 1:
            raise ValueError(
                f"Ambiguous duplicate canonical period {group_key}; "
                f"completeness scores={scores}. Manual review required."
            )

        selected_index = winners[0]
        keep_indices.add(selected_index)

        for idx, row in group.iterrows():
            audit_records.append({
                "ticker": group_key[0],
                "period_type": group_key[1],
                "period_end": group_key[2],
                "period_start": row.get("period_start"),
                "completeness_score": scores[idx],
                "selected": idx == selected_index,
                "selection_reason": (
                    "highest_financial_metric_completeness"
                    if idx == selected_index
                    else "less_complete_duplicate_period"
                ),
            })

    resolved = (
        result.loc[sorted(keep_indices)]
        .sort_values(["ticker", "period_end", "period_type"])
        .reset_index(drop=True)
    )

    remaining_duplicates = resolved.duplicated(keys).sum()
    if remaining_duplicates:
        raise ValueError(
            f"Duplicate canonical periods remain: {remaining_duplicates}"
        )

    return resolved, pd.DataFrame(audit_records)


def add_derived_metrics(
    df: pd.DataFrame,
    return_audit: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame]:
    """Reconstruct all filing vintages, select canonical facts and calculate FCF."""
    if df.empty:
        empty = pd.DataFrame()
        if return_audit:
            return empty, pd.DataFrame()
        return empty

    required = {
        "ticker",
        "metric",
        "period_type",
        "period_start",
        "period_end",
        "filed_date",
        "value_usd",
    }

    missing = required.difference(df.columns)

    if missing:
        raise ValueError(
            "Cannot derive metrics. Missing columns: "
            + ", ".join(sorted(missing))
        )

    raw = df.copy().reset_index(drop=True)

    defaults = {
        "tag_priority": 0,
        "xbrl_tag": pd.NA,
        "data_status": "REPORTED",
        "accession_number": pd.NA,
    }

    for column, default in defaults.items():
        if column not in raw.columns:
            raw[column] = default

    raw["value_usd"] = pd.to_numeric(
        raw["value_usd"],
        errors="coerce",
    )

    capex_mask = raw["metric"].eq("capital_expenditure")

    raw.loc[capex_mask, "value_usd"] = raw.loc[
        capex_mask, "value_usd"
    ].abs()

    # IMPORTANT:
    # Reconstruct before canonical deduplication.
    # This preserves alternate filing vintages that may share an accession
    # between OCF and capex.
    candidates = _reconstruct_quarters(raw)

    canonical = _select_vintage_compatible_rows(candidates)

    period_keys = [
        "ticker", "period_type", "period_start", "period_end"
    ]

    wide = canonical.pivot_table(
        index=period_keys,
        columns="metric",
        values="value_usd",
        aggfunc="last",
    ).reset_index()

    wide.columns.name = None

    metadata_fields = (
        "xbrl_tag",
        "tag_priority",
        "filed_date",
        "accession_number",
        "data_status",
        "derivation_method",
        "source_periods",
        "source_filed_dates",
        "source_accession_numbers",
    )

    for field in metadata_fields:
        if field not in canonical.columns:
            continue

        metadata = canonical.pivot_table(
            index=period_keys,
            columns="metric",
            values=field,
            aggfunc="last",
        )

        metadata.columns = [
            f"{metric}_{field}"
            for metric in metadata.columns
        ]

        wide = wide.merge(
            metadata.reset_index(),
            on=period_keys,
            how="left",
        )

    # Capex tag conflict must be calculated from all source observations.
    capex_rows = raw[
        raw["metric"].eq("capital_expenditure")
    ].copy()

    if not capex_rows.empty and "xbrl_tag" in capex_rows.columns:
        conflicts = (
            capex_rows.groupby(
                period_keys,
                dropna=False,
            )["xbrl_tag"]
            .nunique(dropna=True)
            .gt(1)
            .rename("capital_expenditure_tag_conflict")
            .reset_index()
        )

        wide = wide.merge(
            conflicts,
            on=period_keys,
            how="left",
        )

        wide["capital_expenditure_tag_conflict"] = (
            wide["capital_expenditure_tag_conflict"]
            .fillna(False)
            .astype(bool)
        )
    else:
        wide["capital_expenditure_tag_conflict"] = False

    # Anchor filing and complete derivation lineage are separate concepts.
    for metric in (
        "operating_cash_flow",
        "capital_expenditure",
    ):
        filed_col = f"{metric}_filed_date"
        accession_col = f"{metric}_accession_number"

        if filed_col in wide.columns:
            wide[f"{metric}_anchor_filed_date"] = wide[filed_col]

        if accession_col in wide.columns:
            wide[f"{metric}_anchor_accession_number"] = wide[
                accession_col
            ]

    if {
        "operating_cash_flow",
        "capital_expenditure",
    }.issubset(wide.columns):

        wide["free_cash_flow"] = pd.NA

        wide["free_cash_flow_definition"] = (
            "not_calculated_missing_component"
        )

        wide["fcf_vintage_mismatch"] = False

        for idx, row in wide.iterrows():
            ocf = row.get("operating_cash_flow")
            capex = row.get("capital_expenditure")

            if pd.isna(ocf) or pd.isna(capex):
                continue

            ocf_anchor = row.get(
                "operating_cash_flow_anchor_accession_number"
            )

            capex_anchor = row.get(
                "capital_expenditure_anchor_accession_number"
            )

            ocf_filed = row.get(
                "operating_cash_flow_anchor_filed_date"
            )

            capex_filed = row.get(
                "capital_expenditure_anchor_filed_date"
            )

            # Different known accessions are never treated as compatible.
            if pd.notna(ocf_anchor) and pd.notna(capex_anchor):
                same_anchor = (
                    str(ocf_anchor) == str(capex_anchor)
                )

            elif pd.isna(ocf_anchor) and pd.isna(capex_anchor):
                same_anchor = (
                    pd.notna(ocf_filed)
                    and pd.notna(capex_filed)
                    and str(ocf_filed) == str(capex_filed)
                )

            else:
                same_anchor = False

            if same_anchor:
                wide.at[idx, "free_cash_flow"] = (
                    float(ocf) - float(capex)
                )

                wide.at[idx, "free_cash_flow_definition"] = (
                    "operating_cash_flow_minus_capex_same_period_same_anchor_filing"
                )

            else:
                wide.at[idx, "fcf_vintage_mismatch"] = True

                wide.at[idx, "free_cash_flow_definition"] = (
                    "not_calculated_anchor_filing_mismatch"
                )

    else:
        wide["free_cash_flow"] = pd.NA

        wide["free_cash_flow_definition"] = (
            "not_calculated_missing_component"
        )

        wide["fcf_vintage_mismatch"] = False

    wide = wide.sort_values(
        ["ticker", "period_end", "period_type"]
    ).reset_index(drop=True)

    # Resolve end-date duplicates only after all metric columns and FCF
    # have been assembled. Raw SEC observations remain unchanged.
    resolved, resolution_audit = resolve_duplicate_period_ends(wide)

    if return_audit:
        return resolved, resolution_audit

    return resolved
