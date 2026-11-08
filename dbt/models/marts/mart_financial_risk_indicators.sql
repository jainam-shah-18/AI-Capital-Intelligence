{{ config(materialized='view') }}

with quarterly_metrics as (

    select
        company_cik,
        company_name,
        unit,
        period_start,
        period_end,

        max(case when metric_name = 'REVENUE' then financial_value end) as revenue,
        max(case when metric_name = 'OPERATING_INCOME' then financial_value end) as operating_income,
        max(case when metric_name = 'NET_INCOME' then financial_value end) as net_income,

        count(distinct case when metric_name = 'REVENUE' then concept_name end) as revenue_concept_count,
        count(distinct case when metric_name = 'OPERATING_INCOME' then concept_name end) as operating_income_concept_count,
        count(distinct case when metric_name = 'NET_INCOME' then concept_name end) as net_income_concept_count

    from {{ ref('int_quarterly_financial_observations') }}
    where metric_name in ('REVENUE', 'OPERATING_INCOME', 'NET_INCOME')
    group by
        company_cik,
        company_name,
        unit,
        period_start,
        period_end

),

period_comparisons as (

    select
        curr.*,
        prev.revenue as prior_year_revenue,
        prev.operating_income as prior_year_operating_income,
        prev.net_income as prior_year_net_income,
        prev.revenue_concept_count as prior_revenue_concept_count,
        prev.operating_income_concept_count as prior_operating_income_concept_count

    from quarterly_metrics curr
    left join quarterly_metrics prev
        on curr.company_cik = prev.company_cik
        and curr.unit = prev.unit
        and prev.period_end = dateadd(year, -1, curr.period_end)

),

anomaly_summary as (

    select
        company_cik,
        period_end,

        count(*) as anomaly_observation_count,

        sum(case when anomaly_status = 'ANOMALY' then 1 else 0 end)
            as flagged_anomaly_count,

        max(case when metric_name = 'REVENUE' then yoy_growth_pct end)
            as revenue_yoy_growth_pct,

        max(case when metric_name = 'OPERATING_INCOME' then yoy_growth_pct end)
            as operating_income_yoy_growth_pct,

        max(case when metric_name = 'NET_INCOME' then yoy_growth_pct end)
            as net_income_yoy_growth_pct

    from {{ ref('mart_financial_anomalies') }}
    group by company_cik, period_end

),

indicators as (

    select
        p.*,

        case
            when p.revenue_concept_count = 1
             and p.revenue > 0
            then p.operating_income / p.revenue
        end as operating_margin,

        case
            when p.prior_revenue_concept_count = 1
             and p.prior_year_revenue > 0
             and p.prior_operating_income_concept_count = 1
            then p.prior_year_operating_income / p.prior_year_revenue
        end as prior_year_operating_margin,

        case
            when p.revenue_concept_count = 1
            then a.revenue_yoy_growth_pct
        end as revenue_yoy_growth_pct,

        case
            when p.operating_income_concept_count = 1
            then a.operating_income_yoy_growth_pct
        end as operating_income_yoy_growth_pct,

        case
            when p.net_income_concept_count = 1
            then a.net_income_yoy_growth_pct
        end as net_income_yoy_growth_pct,

        coalesce(a.anomaly_observation_count, 0) as anomaly_observation_count,
        coalesce(a.flagged_anomaly_count, 0) as flagged_anomaly_count

    from period_comparisons p
    left join anomaly_summary a
        on p.company_cik = a.company_cik
        and p.period_end = a.period_end

),

risk_flags as (

    select
        *,

        case
            when revenue_yoy_growth_pct < 0 then true
            when revenue_yoy_growth_pct is not null then false
        end as revenue_growth_decline_flag,

        case
            when operating_margin is not null
             and prior_year_operating_margin is not null
             and operating_margin < prior_year_operating_margin
            then true
            when operating_margin is not null
             and prior_year_operating_margin is not null
            then false
        end as operating_margin_contraction_flag,

        case
            when net_income_yoy_growth_pct < 0 then true
            when net_income_yoy_growth_pct is not null then false
        end as net_income_growth_decline_flag,

        case
            when flagged_anomaly_count > 0 then true
            when anomaly_observation_count > 0 then false
        end as financial_anomaly_flag

    from indicators

),

scored as (

    select
        *,
        case
            when operating_margin is not null
             and prior_year_operating_margin is not null
            then (operating_margin - prior_year_operating_margin) * 100
        end as operating_margin_change_pp,

        (
            case when revenue_growth_decline_flag then 1 else 0 end
            + case when operating_margin_contraction_flag then 1 else 0 end
            + case when net_income_growth_decline_flag then 1 else 0 end
            + case when financial_anomaly_flag then 1 else 0 end
        ) as risk_indicator_count

    from risk_flags

)

select
    company_cik,
    company_name,
    unit,
    period_start,
    period_end,

    revenue,
    prior_year_revenue,
    revenue_yoy_growth_pct,

    operating_income,
    operating_margin,
    prior_year_operating_margin,
    operating_margin_change_pp,
    operating_income_yoy_growth_pct,

    net_income,
    prior_year_net_income,
    net_income_yoy_growth_pct,

    revenue_concept_count,
    operating_income_concept_count,
    net_income_concept_count,

    anomaly_observation_count,
    flagged_anomaly_count,

    revenue_growth_decline_flag,
    operating_margin_contraction_flag,
    net_income_growth_decline_flag,
    financial_anomaly_flag,

    risk_indicator_count,

    case
        when risk_indicator_count > 0 then 'REVIEW_REQUIRED'
        when anomaly_observation_count = 0
         and revenue_yoy_growth_pct is null
         and operating_margin_change_pp is null
         and net_income_yoy_growth_pct is null
        then 'INSUFFICIENT_DATA'
        else 'NO_FLAGGED_INDICATORS'
    end as monitoring_status,

    current_timestamp() as model_created_at

from scored
