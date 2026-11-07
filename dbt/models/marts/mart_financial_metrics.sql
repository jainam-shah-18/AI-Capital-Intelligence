{{ config(materialized='view') }}

with validated_mappings as (

    select
        company_cik,
        metric_name,
        concept_name,
        unit

    from {{ ref('int_metric_mapping_validation') }}

    where validation_status = 'MATCHED'
      and mapping_status = 'CANDIDATE'

),

financial_observations as (

    select
        s.company_cik,
        s.company_name,
        s.concept_name,
        s.unit,
        s.reported_value,
        s.period_start,
        s.period_end,
        s.filing_form,
        s.filed_date,
        s.filing_fiscal_year,
        s.filing_fiscal_period,
        s.sec_frame,
        s.accession_number,
        s.duration_days,
        s.duration_class,
        s.filing_role

    from {{ ref('stg_sec_financial_observations') }} s

    where s.period_start is not null

),

mapped_metrics as (

    select
        f.company_cik,
        f.company_name,
        m.metric_name,
        f.concept_name,
        f.unit,
        f.reported_value,
        f.period_start,
        f.period_end,
        f.filing_form,
        f.filed_date,
        f.filing_fiscal_year,
        f.filing_fiscal_period,
        f.sec_frame,
        f.accession_number,
        f.duration_days,
        f.duration_class,
        f.filing_role,

        'REPORTED' as value_class

    from financial_observations f

    inner join validated_mappings m
        on f.company_cik = m.company_cik
        and f.concept_name = m.concept_name
        and f.unit = m.unit

)

select *
from mapped_metrics