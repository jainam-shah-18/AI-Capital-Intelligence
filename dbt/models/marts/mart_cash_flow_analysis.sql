
{{ config(materialized='view') }}

with direct_quarterly as (

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
        accession_number,
        'DIRECT' as value_source,
        'DIRECTLY_REPORTED' as derivation_method,
        'DIRECT_REPORTED' as derivation_status

    from {{ ref('int_financial_metric_canonical') }}

    where cross_concept_selection_status = 'CANONICAL_SELECTED'
      and financial_value is not null
      and duration_class = 'QUARTER_DURATION'
      and metric_name in ('OPERATING_CASH_FLOW', 'CAPEX')

),

derived_quarterly as (

    select
        d.company_cik,
        d.company_name,
        d.metric_name,
        d.concept_name,
        d.unit,
        d.period_start,
        d.period_end,
        null as filing_fiscal_year,
        d.derived_fiscal_quarter as filing_fiscal_period,
        d.derived_candidate_value as financial_value,
        case
            when d.current_reporting_basis = d.prior_reporting_basis
            then d.current_reporting_basis
            else null
        end as reporting_basis,
        d.source_accession_current as accession_number,
        'DERIVED' as value_source,
        d.derivation_method,
        d.derivation_status

    from {{ ref('int_financial_quarterly_cashflow_derived') }} d

    where d.derivation_status in (
    'REVIEW_REQUIRED',
    'REPORTING_BASIS_UNKNOWN'
)
  and d.derived_candidate_value is not null

),

all_quarterly as (

    select * from direct_quarterly

    union all

    select * from derived_quarterly

),

ranked_quarterly as (

    select
        *,
        row_number() over (
            partition by
                company_cik,
                metric_name,
                unit,
                period_start,
                period_end
            order by
                case when value_source = 'DIRECT' then 1 else 2 end
        ) as source_rank

    from all_quarterly

),

selected_quarterly as (

    select *
    from ranked_quarterly
    where source_rank = 1

),

period_metrics as (

    select
        company_cik,
        company_name,
        unit,
        period_start,
        period_end,

        max(filing_fiscal_year) as filing_fiscal_year,
        max(filing_fiscal_period) as filing_fiscal_period,

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
        end) as capex_accession_number,

        max(case
            when metric_name = 'OPERATING_CASH_FLOW'
            then value_source
        end) as ocf_value_source,

        max(case
            when metric_name = 'CAPEX'
            then value_source
        end) as capex_value_source,

        max(case
            when metric_name = 'OPERATING_CASH_FLOW'
            then derivation_method
        end) as ocf_derivation_method,

        max(case
            when metric_name = 'CAPEX'
            then derivation_method
        end) as capex_derivation_method,

        max(case
            when metric_name = 'OPERATING_CASH_FLOW'
            then derivation_status
        end) as ocf_derivation_status,

        max(case
            when metric_name = 'CAPEX'
            then derivation_status
        end) as capex_derivation_status

    from selected_quarterly

    group by
        company_cik,
        company_name,
        unit,
        period_start,
        period_end

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
            else 'CAPEX_BASIS_REVIEW_REQUIRED'
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
         and capex_reported_value is not null
         and capex_concept_count = 1
         and capex_quality_status = 'CAPEX_BASIS_APPROVED'
        then operating_cash_flow - capex_reported_value
        else null
    end as free_cash_flow,

    case
        when operating_cash_flow is null
            then 'OPERATING_CASH_FLOW_UNAVAILABLE'
        when capex_reported_value is null
            then 'CAPEX_UNAVAILABLE'
        when capex_concept_count > 1
            then 'MULTIPLE_CAPEX_CONCEPTS'
        else 'CAPEX_BASIS_REVIEW_REQUIRED'
    end as free_cash_flow_status,

    case
        when operating_cash_flow is not null
         and capex_reported_value is not null
         and capex_concept_count = 1
        then operating_cash_flow - capex_reported_value
        else null
    end as free_cash_flow_candidate,

    case
        when operating_cash_flow is not null
         and capex_reported_value is not null
         and capex_concept_count = 1
        then 'CANDIDATE_REQUIRES_CAPEX_BASIS_APPROVAL'
        else 'NOT_CALCULABLE'
    end as free_cash_flow_candidate_status,

    capex_quality_status,
    ocf_value_source,
    capex_value_source,
    ocf_derivation_method,
    capex_derivation_method,
    ocf_derivation_status,
    capex_derivation_status,
    ocf_accession_number,
    capex_accession_number,
    current_timestamp() as model_created_at

from classified
