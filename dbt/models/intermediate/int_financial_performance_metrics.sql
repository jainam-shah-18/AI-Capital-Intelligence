
{{ config(materialized='view') }}

with quarterly_wide as (

    select
        company_cik,
        max(company_name) as company_name,

        reporting_period_key,
        period_end,
        min(period_start) as period_start,
        duration_class,

        coalesce(
            max(case when metric_name = 'REVENUE'
                then filing_fiscal_year end),
            max(case when metric_name = 'OPERATING_INCOME'
                then filing_fiscal_year end),
            max(case when metric_name = 'NET_INCOME'
                then filing_fiscal_year end),
            max(case when metric_name = 'CAPEX'
                then filing_fiscal_year end)
        ) as filing_fiscal_year,

        coalesce(
            max(case when metric_name = 'REVENUE'
                then filing_fiscal_period end),
            max(case when metric_name = 'OPERATING_INCOME'
                then filing_fiscal_period end),
            max(case when metric_name = 'NET_INCOME'
                then filing_fiscal_period end),
            max(case when metric_name = 'CAPEX'
                then filing_fiscal_period end)
        ) as filing_fiscal_period,

        max(case when metric_name = 'REVENUE'
            then financial_value end) as revenue,

        max(case when metric_name = 'OPERATING_INCOME'
            then financial_value end) as operating_income,

        max(case when metric_name = 'NET_INCOME'
            then financial_value end) as net_income,

        max(case when metric_name = 'OPERATING_CASH_FLOW'
            then financial_value end) as operating_cash_flow,

        max(case when metric_name = 'CAPEX'
            then financial_value end) as capex

    from {{ ref('int_financial_period_alignment') }}

    where selection_status = 'CANONICAL_SELECTED'
      and financial_value is not null
      and duration_class = 'QUARTER_DURATION'
      and period_alignment_status = 'ALIGNED_MINOR_START_DATE_VARIANCE'

    group by
        company_cik,
        reporting_period_key,
        period_end,
        duration_class

),

with_prior_quarter as (

    select
        *,

        lag(period_end) over (
            partition by company_cik
            order by period_end
        ) as prior_observed_period_end,

        lag(revenue) over (
            partition by company_cik
            order by period_end
        ) as prior_quarter_revenue,

        lag(operating_income) over (
            partition by company_cik
            order by period_end
        ) as prior_quarter_operating_income,

        lag(net_income) over (
            partition by company_cik
            order by period_end
        ) as prior_quarter_net_income

    from quarterly_wide

),

with_prior_year as (

    select
        current_period.*,

        prior_year.revenue as prior_year_revenue

    from with_prior_quarter current_period

    left join quarterly_wide prior_year
        on current_period.company_cik = prior_year.company_cik
        and dateadd(year, -1, current_period.period_end)
            = prior_year.period_end

)

select

    company_cik,
    company_name,
    reporting_period_key,
    period_start,
    period_end,
    duration_class,
    filing_fiscal_year,
    filing_fiscal_period,

    revenue,
    operating_income,
    net_income,
    operating_cash_flow,
    capex,

    operating_cash_flow - capex as free_cash_flow,

    operating_income / nullif(revenue, 0) * 100
        as operating_margin_pct,

    net_income / nullif(revenue, 0) * 100
        as net_profit_margin_pct,

    (operating_cash_flow - capex) / nullif(revenue, 0) * 100
        as free_cash_flow_margin_pct,

    capex / nullif(revenue, 0) * 100
        as capex_intensity_pct,

    operating_cash_flow / nullif(net_income, 0) * 100
        as cash_conversion_pct,

    case
        when datediff(
            day,
            prior_observed_period_end,
            period_end
        ) between 70 and 110
        then (
            revenue / nullif(prior_quarter_revenue, 0) - 1
        ) * 100
    end as revenue_qoq_growth_pct,

    (
        revenue / nullif(prior_year_revenue, 0) - 1
    ) * 100 as revenue_yoy_growth_pct,

    case
        when datediff(
            day,
            prior_observed_period_end,
            period_end
        ) between 70 and 110
        then (
            operating_income /
            nullif(prior_quarter_operating_income, 0) - 1
        ) * 100
    end as operating_income_qoq_growth_pct,

    case
        when datediff(
            day,
            prior_observed_period_end,
            period_end
        ) between 70 and 110
        then (
            net_income /
            nullif(prior_quarter_net_income, 0) - 1
        ) * 100
    end as net_income_qoq_growth_pct,

    current_timestamp() as model_created_at

from with_prior_year
