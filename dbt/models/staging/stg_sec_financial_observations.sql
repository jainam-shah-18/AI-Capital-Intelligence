{{ config(materialized='view') }}

select
    company_cik,
    company_name,
    source_file,
    concept_name,
    unit,
    reported_value,
    period_start,
    period_end,
    filing_form,
    filed_date,
    filing_fiscal_year,
    filing_fiscal_period,
    sec_frame,
    accession_number,
    ingested_at,
    duration_days,
    duration_class,
    filing_role

from {{ source('aci_analytics', 'int_financial_observations') }}
