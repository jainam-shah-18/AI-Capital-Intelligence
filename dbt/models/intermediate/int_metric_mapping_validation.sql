{{ config(materialized='view') }}

with inventory as (

    select
        company_cik,
        company_name,
        metric_name,
        concept_name,
        unit,
        first_observed_period,
        last_observed_period,
        mapping_status

    from {{ ref('metric_concept_inventory') }}

),

source_concepts as (

    select
        company_cik,
        concept_name,
        unit,
        count(*) as source_observation_count,
        min(period_end) as actual_first_period,
        max(period_end) as actual_last_period

    from {{ ref('stg_sec_financial_observations') }}

    group by
        company_cik,
        concept_name,
        unit

)

select
    i.company_cik,
    i.company_name,
    i.metric_name,
    i.concept_name,
    i.unit,
    i.first_observed_period,
    i.last_observed_period,
    i.mapping_status,

    coalesce(s.source_observation_count, 0) as source_observation_count,
    s.actual_first_period,
    s.actual_last_period,

    case
        when s.source_observation_count is null then 'UNMATCHED'
        else 'MATCHED'
    end as validation_status

from inventory i

left join source_concepts s
    on i.company_cik = s.company_cik
    and i.concept_name = s.concept_name
    and i.unit = s.unit