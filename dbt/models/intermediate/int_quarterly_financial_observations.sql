{{ config(materialized='view') }}

with reported_quarters as (

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

        filing_form,
        filed_date,
        accession_number,
        sec_frame,

        duration_class,

        'REPORTED' as value_class,
        'CANONICAL_SELECTED' as selection_status,

        accession_number as source_accession_current,
        cast(null as varchar) as source_accession_prior,

        current_timestamp() as model_created_at

    from {{ ref('int_financial_metric_canonical') }}

    where cross_concept_selection_status = 'CANONICAL_SELECTED'
      and financial_value is not null
      and duration_class = 'QUARTER_DURATION'

)

select *
from reported_quarters