{{ config(materialized='table') }}

select
    company_cik,
    company_name,

    metric_name,
    concept_name,
    unit,

    period_start,
    period_end,
    duration_class,

    filing_fiscal_year,
    filing_fiscal_period,

    financial_value,

    filing_form,
    filed_date,
    accession_number,
    sec_frame,

    concept_candidate_count,
    distinct_concept_count,
    distinct_candidate_values,

    policy_applied,
    reporting_basis,
    policy_reason,
    evidence_accession_number,

    cross_concept_selection_status,
    selection_reason,

    source_accession_current,
    source_accession_prior,

    model_created_at,

    current_timestamp() as mart_created_at

from {{ ref('int_financial_metric_canonical') }}

where cross_concept_selection_status = 'CANONICAL_SELECTED'
  and financial_value is not null