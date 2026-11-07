{{ config(materialized='view') }}

select
    *,

    case
        when period_start is null then 'INSTANT_FACT'
        else 'DURATION_FACT'
    end as fact_type,

    case
        when period_start is null then 'NOT_APPLICABLE_INSTANT'
        when duration_class in (
            'QUARTER_DURATION',
            'HALF_YEAR_DURATION',
            'NINE_MONTH_DURATION',
            'ANNUAL_DURATION'
        ) then 'STANDARD_DURATION'
        when duration_class = 'UNUSUAL_DURATION' then 'UNUSUAL_DURATION'
        else 'UNCLASSIFIED_DURATION'
    end as duration_quality,

    case
        when filing_role ilike 'PRIMARY_FINANCIAL%' then 'PRIMARY'
        when filing_role ilike 'ALTERNATE_FILING%' then 'ALTERNATE'
        when filing_role ilike 'AMENDED_FINANCIAL%' then 'AMENDED'
        when filing_role ilike 'NON_CANONICAL%' then 'NON_CANONICAL'
        else 'OTHER'
    end as filing_evidence_class

from {{ ref('stg_sec_financial_observations') }}
