{{ config(materialized='view') }}

with quarterly_metrics as (

    select
        company_cik,
        company_name,
        metric_name,
        concept_name,
        unit,
        period_start,
        period_end,
        filing_fiscal_year,
        filing_fiscal_period,
        financial_value,
        accession_number

    from {{ ref('int_quarterly_financial_observations') }}

    where metric_name in (
        'REVENUE',
        'OPERATING_INCOME',
        'NET_INCOME'
    )

),

year_over_year_comparison as (

    select
        curr.company_cik,
        curr.company_name,
        curr.metric_name,
        curr.concept_name,
        curr.unit,

        curr.period_start,
        curr.period_end,
        curr.filing_fiscal_year,
        curr.filing_fiscal_period,
        curr.financial_value as current_value,

        prev.period_end as prior_year_period_end,
        prev.financial_value as prior_year_value,

        curr.accession_number as current_accession_number,
        prev.accession_number as prior_year_accession_number,

        case
            when prev.financial_value = 0
                then 'ZERO_PRIOR_YEAR_BASELINE'
            when prev.financial_value < 0
                then 'NEGATIVE_PRIOR_YEAR_BASELINE'
            when curr.financial_value < 0
                then 'SIGN_CHANGE_TO_NEGATIVE'
            else 'COMPARABLE'
        end as comparison_quality_status,

        case
            when prev.financial_value > 0
             and curr.financial_value >= 0
            then (
                curr.financial_value
                / nullif(prev.financial_value, 0)
                - 1
            ) * 100
            else null
        end as yoy_growth_pct

    from quarterly_metrics curr

    inner join quarterly_metrics prev
        on curr.company_cik = prev.company_cik
        and curr.metric_name = prev.metric_name
        and curr.concept_name = prev.concept_name
        and curr.unit = prev.unit
        and prev.period_end = dateadd(year, -1, curr.period_end)

),

historical_baseline as (

    select
        *,

        count(yoy_growth_pct) over (
            partition by
                company_cik,
                metric_name,
                concept_name,
                unit
            order by period_end
            rows between 8 preceding and 1 preceding
        ) as historical_observation_count,

        avg(yoy_growth_pct) over (
            partition by
                company_cik,
                metric_name,
                concept_name,
                unit
            order by period_end
            rows between 8 preceding and 1 preceding
        ) as historical_avg_yoy_growth_pct,

        stddev_samp(yoy_growth_pct) over (
            partition by
                company_cik,
                metric_name,
                concept_name,
                unit
            order by period_end
            rows between 8 preceding and 1 preceding
        ) as historical_stddev_yoy_growth_pct

    from year_over_year_comparison

),

scored as (

    select
        *,

        case
            when historical_stddev_yoy_growth_pct > 0
            then (
                yoy_growth_pct
                - historical_avg_yoy_growth_pct
            ) / historical_stddev_yoy_growth_pct
            else null
        end as anomaly_z_score

    from historical_baseline

)

select
    company_cik,
    company_name,
    metric_name,
    concept_name,
    unit,

    period_start,
    period_end,
    filing_fiscal_year,
    filing_fiscal_period,

    current_value,
    prior_year_period_end,
    prior_year_value,

    comparison_quality_status,
    yoy_growth_pct,

    historical_observation_count,
    historical_avg_yoy_growth_pct,
    historical_stddev_yoy_growth_pct,
    anomaly_z_score,

    case
        when comparison_quality_status <> 'COMPARABLE'
            then 'NON_COMPARABLE'

        when historical_observation_count < 6
            then 'INSUFFICIENT_HISTORY'

        when historical_stddev_yoy_growth_pct is null
          or historical_stddev_yoy_growth_pct = 0
            then 'NO_VARIANCE_BASELINE'

        when abs(anomaly_z_score) > 3
            then 'ANOMALY'

        else 'NORMAL'
    end as anomaly_status,

    case
        when comparison_quality_status = 'COMPARABLE'
         and historical_observation_count >= 6
         and historical_stddev_yoy_growth_pct > 0
         and abs(anomaly_z_score) > 3
         and yoy_growth_pct > historical_avg_yoy_growth_pct
            then 'UNUSUALLY_HIGH'

        when comparison_quality_status = 'COMPARABLE'
         and historical_observation_count >= 6
         and historical_stddev_yoy_growth_pct > 0
         and abs(anomaly_z_score) > 3
         and yoy_growth_pct < historical_avg_yoy_growth_pct
            then 'UNUSUALLY_LOW'

        else 'NOT_APPLICABLE'
    end as anomaly_direction,

    current_accession_number,
    prior_year_accession_number,

    3 as anomaly_threshold_standard_deviations,

    current_timestamp() as model_created_at

from scored
