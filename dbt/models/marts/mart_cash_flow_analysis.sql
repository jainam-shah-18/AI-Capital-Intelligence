{{ config(materialized='view') }}

with cashflow_observations as (

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
        reporting_basis,
        accession_number

    from {{ ref('int_financial_metric_canonical') }}

    where cross_concept_selection_status = 'CANONICAL_SELECTED'
      and financial_value is not null
      and duration_class = 'QUARTER_DURATION'
      and metric_name in ('OPERATING_CASH_FLOW', 'CAPEX')

),

period_metrics as (

    select
        company_cik,
        company_name,
        unit,
        period_start,
        period_end,
        filing_fiscal_year,
        filing_fiscal_period,

        max(case
            when metric_name = 'OPERATING_CASH_FLOW'
            then financial_value
        end) as operating_cash_flow,

        max(case
            when metric_name = 'CAPEX'
            then financial_value
        end) as capex_reported_value,

        count(distinct case
            when metric_name = 'CAPEX'
            then concept_name
        end) as capex_concept_count,

        max(case
            when metric_name = 'CAPEX'
            then concept_name
        end) as capex_concept_name,

        max(case
            when metric_name = 'CAPEX'
            then reporting_basis
        end) as capex_reporting_basis,

        max(case
            when metric_name = 'OPERATING_CASH_FLOW'
            then accession_number
        end) as ocf_accession_number,

        max(case
            when metric_name = 'CAPEX'
            then accession_number
        end) as capex_accession_number

    from cashflow_observations

    group by
        company_cik,
        company_name,
        unit,
        period_start,
        period_end,
        filing_fiscal_year,
        filing_fiscal_period

),

classified as (

    select
        *,

        case
            when capex_reported_value is null
                then 'CAPEX_UNAVAILABLE'
            when capex_concept_count > 1
                then 'MULTIPLE_CAPEX_CONCEPTS'
            when capex_reporting_basis is null
                then 'CAPEX_BASIS_REVIEW_REQUIRED'
            else 'CAPEX_BASIS_APPROVED'
        end as capex_quality_status

    from period_metrics

)

select
    company_cik,
    company_name,
    unit,
    period_start,
    period_end,
    filing_fiscal_year,
    filing_fiscal_period,

    operating_cash_flow,
    capex_reported_value,
    capex_concept_count,
    capex_concept_name,
    capex_reporting_basis,

    case
        when operating_cash_flow is not null
         and capex_quality_status = 'CAPEX_BASIS_APPROVED'
        then operating_cash_flow - capex_reported_value
        else null
    end as free_cash_flow,

    case
        when operating_cash_flow is null
            then 'OPERATING_CASH_FLOW_UNAVAILABLE'
        when capex_quality_status = 'CAPEX_UNAVAILABLE'
            then 'CAPEX_UNAVAILABLE'
        when capex_quality_status = 'MULTIPLE_CAPEX_CONCEPTS'
            then 'MULTIPLE_CAPEX_CONCEPTS'
        when capex_quality_status = 'CAPEX_BASIS_REVIEW_REQUIRED'
            then 'CAPEX_BASIS_REVIEW_REQUIRED'
        else 'CALCULATED'
    end as free_cash_flow_status,

    capex_quality_status,
    ocf_accession_number,
    capex_accession_number,
    current_timestamp() as model_created_at

from classified
