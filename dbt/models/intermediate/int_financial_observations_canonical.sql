
{{ config(materialized='view') }}

with source_observations as (

    select
        *,
        case
            when filing_role ilike 'PRIMARY_FINANCIAL%'
                then 'PRIMARY'
            when filing_role ilike 'ALTERNATE_FILING%'
                then 'ALTERNATE'
            when filing_role ilike 'AMENDED_FINANCIAL%'
                then 'AMENDED'
            when filing_role ilike 'NON_CANONICAL%'
                then 'NON_CANONICAL'
            else 'OTHER'
        end as filing_evidence_class

    from {{ ref('mart_financial_metrics') }}

),

period_audit as (

    select
        company_cik,
        metric_name,
        concept_name,
        unit,
        period_start,
        period_end,
        duration_class,

        count(*) as source_record_count,
        count(distinct reported_value) as distinct_reported_values,

        max(case when filing_evidence_class = 'PRIMARY'
            then 1 else 0 end) as has_primary_filing,

        max(case when filing_evidence_class = 'ALTERNATE'
            then 1 else 0 end) as has_alternate_filing,

        max(case when filing_evidence_class = 'AMENDED'
            then 1 else 0 end) as has_amended_filing

    from source_observations

    group by
        company_cik,
        metric_name,
        concept_name,
        unit,
        period_start,
        period_end,
        duration_class

),

ranked_observations as (

    select
        s.*,

        a.source_record_count,
        a.distinct_reported_values,
        a.has_primary_filing,
        a.has_alternate_filing,
        a.has_amended_filing,

        row_number() over (
            partition by
                s.company_cik,
                s.metric_name,
                s.concept_name,
                s.unit,
                s.period_start,
                s.period_end,
                s.duration_class

            order by
                case
                    when s.filing_evidence_class = 'PRIMARY' then 1
                    when s.filing_evidence_class = 'ALTERNATE' then 2
                    else 3
                end,
                s.filed_date desc,
                s.accession_number desc
        ) as candidate_rank

    from source_observations s

    inner join period_audit a
        on s.company_cik = a.company_cik
        and s.metric_name = a.metric_name
        and s.concept_name = a.concept_name
        and s.unit = a.unit
        and s.period_start = a.period_start
        and s.period_end = a.period_end
        and s.duration_class = a.duration_class

)

select
    *,

    case
        when distinct_reported_values > 1
            then 'CONFLICT_REVIEW_REQUIRED'

        when filing_evidence_class = 'AMENDED'
            and has_primary_filing = 0
            and has_alternate_filing = 0
            then 'AMENDMENT_REVIEW_REQUIRED'

        when filing_evidence_class not in ('PRIMARY', 'ALTERNATE')
            then 'NOT_ELIGIBLE'

        when candidate_rank = 1
            then 'CANONICAL_SELECTED'

        else 'SUPERSEDED_DUPLICATE'
    end as canonical_selection_status,

    case
        when distinct_reported_values = 1
            and candidate_rank = 1
            and filing_evidence_class in ('PRIMARY', 'ALTERNATE')
            then reported_value
        else null
    end as canonical_value

from ranked_observations
