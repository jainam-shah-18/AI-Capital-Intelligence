{{ config(materialized='view') }}

with canonical_candidates as (

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
        canonical_value as candidate_value,
        filing_form,
        filed_date,
        accession_number,
        sec_frame,
        duration_class

    from {{ ref('int_financial_observations_canonical') }}

    where canonical_selection_status = 'CANONICAL_SELECTED'
      and canonical_value is not null

),

policy_candidates as (

    select
        c.*,

        p.preferred_concept_name,
        p.preferred_accession_number,
        p.reporting_basis,
        p.policy_reason,
        p.evidence_accession_number,

        case
            when p.company_cik is not null then 1
            else 0
        end as has_policy,

        case
            when c.concept_name = p.preferred_concept_name
             and c.accession_number = p.preferred_accession_number
                then 1
            else 0
        end as is_policy_preferred_candidate

    from canonical_candidates c

    left join {{ ref('metric_concept_selection_policy') }} p
        on c.company_cik = p.company_cik
        and c.metric_name = p.metric_name
        and c.unit = p.unit
        and c.period_start = to_date(p.period_start)
        and c.period_end = to_date(p.period_end)
        and c.duration_class = p.duration_class

),

period_audit as (

    select
        company_cik,
        metric_name,
        unit,
        period_start,
        period_end,
        duration_class,

        count(*) as concept_candidate_count,
        count(distinct concept_name) as distinct_concept_count,
        count(distinct candidate_value) as distinct_candidate_values,

        max(has_policy) as has_policy,

        max(is_policy_preferred_candidate)
            as has_policy_preferred_candidate

    from policy_candidates

    group by
        company_cik,
        metric_name,
        unit,
        period_start,
        period_end,
        duration_class

),

ranked_candidates as (

    select
        c.*,

        a.concept_candidate_count,
        a.distinct_concept_count,
        a.distinct_candidate_values,
        a.has_policy_preferred_candidate,

        row_number() over (
            partition by
                c.company_cik,
                c.metric_name,
                c.unit,
                c.period_start,
                c.period_end,
                c.duration_class

            order by
                case
                    when a.has_policy_preferred_candidate = 1
                     and c.is_policy_preferred_candidate = 1
                        then 0
                    when a.distinct_candidate_values = 1
                        then 1
                    else 2
                end,
                c.concept_name asc,
                c.filed_date desc,
                c.accession_number desc
        ) as candidate_rank

    from policy_candidates c

    inner join period_audit a
        on c.company_cik = a.company_cik
        and c.metric_name = a.metric_name
        and c.unit = a.unit
        and c.period_start = a.period_start
        and c.period_end = a.period_end
        and c.duration_class = a.duration_class

),

classified_candidates as (

    select
        *,

        case
            when has_policy = 1
             and has_policy_preferred_candidate = 0
                then 'POLICY_VALIDATION_REQUIRED'

            when distinct_candidate_values > 1
             and has_policy = 0
                then 'CONFLICT_REVIEW_REQUIRED'

            when distinct_candidate_values > 1
             and has_policy = 1
             and is_policy_preferred_candidate = 1
                then 'CANONICAL_SELECTED'

            when distinct_candidate_values > 1
             and has_policy = 1
                then 'POLICY_ALTERNATIVE'

            when distinct_candidate_values = 1
             and candidate_rank = 1
                then 'CANONICAL_SELECTED'

            else 'AGREEMENT_ALTERNATIVE'
        end as cross_concept_selection_status,

        case
            when has_policy = 1
             and has_policy_preferred_candidate = 0
                then 'POLICY_PREFERRED_CANDIDATE_NOT_FOUND'

            when distinct_candidate_values > 1
             and has_policy = 0
                then 'MULTIPLE_VALUES_WITHOUT_DOCUMENTED_POLICY'

            when distinct_candidate_values > 1
             and is_policy_preferred_candidate = 1
                then 'EXPLICIT_DOCUMENTED_POLICY'

            when distinct_candidate_values > 1
             and has_policy = 1
                then 'ALTERNATIVE_TO_POLICY_SELECTION'

            when distinct_candidate_values = 1
             and candidate_rank = 1
             and distinct_concept_count > 1
                then 'AGREEMENT_ACROSS_CONCEPTS'

            when distinct_candidate_values = 1
             and candidate_rank = 1
                then 'SINGLE_ELIGIBLE_CONCEPT'

            else 'AGREEMENT_ALTERNATIVE'
        end as selection_reason

    from ranked_candidates

)

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

    candidate_value,

    case
        when cross_concept_selection_status = 'CANONICAL_SELECTED'
            then candidate_value
        else null
    end as financial_value,

    filing_form,
    filed_date,
    accession_number,
    sec_frame,
    duration_class,

    concept_candidate_count,
    distinct_concept_count,
    distinct_candidate_values,

    has_policy as policy_applied,
    reporting_basis,
    policy_reason,
    evidence_accession_number,

    cross_concept_selection_status,
    selection_reason,

    accession_number as source_accession_current,
    cast(null as varchar) as source_accession_prior,

    current_timestamp() as model_created_at

from classified_candidates
