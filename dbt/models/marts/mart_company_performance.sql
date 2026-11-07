{{ config(materialized='table') }}

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
    free_cash_flow,

    operating_margin_pct,
    net_profit_margin_pct,
    free_cash_flow_margin_pct,
    capex_intensity_pct,
    cash_conversion_pct,

    revenue_qoq_growth_pct,
    revenue_yoy_growth_pct,
    operating_income_qoq_growth_pct,
    net_income_qoq_growth_pct,

    current_timestamp() as mart_created_at

from {{ ref('int_financial_performance_metrics') }}