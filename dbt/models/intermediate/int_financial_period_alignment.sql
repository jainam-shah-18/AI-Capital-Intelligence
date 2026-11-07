
{{ config(materialized='view') }}

with quarterly_observations as (

    select *
    from {{ ref('int_quarterly_financial_observations') }}

),

period_summary as (

    select
        company_cik,
        period_end,
        duration_class,

        min(period_start) as earliest_period_start,
        max(period_start) as latest_period_start,

        datediff(
            day,
            min(period_start),
            max(period_start)
        ) as start_date_variance_days,

        count(distinct metric_name) as metric_count,

        count(distinct accession_number) as filing_count,

        listagg(distinct filing_form, ', ')
            within group (order by filing_form) as filing_forms

    from quarterly_observations

    group by
        company_cik,
        period_end,
        duration_class

)

select
    q.company_cik,
    q.company_name,
    q.metric_name,
    q.concept_name,
    q.unit,

    q.period_start,
    q.period_end,

    q.filing_fiscal_year,
    q.filing_fiscal_period,

    q.financial_value,

    q.filing_form,
    q.filed_date,
    q.accession_number,
    q.sec_frame,
    q.duration_class,

    p.earliest_period_start,
    p.latest_period_start,
    p.start_date_variance_days,
    p.metric_count,
    p.filing_count,
    p.filing_forms,

    concat(
        q.company_cik,
        '|',
        to_varchar(q.period_end, 'YYYY-MM-DD'),
        '|',
        q.duration_class
    ) as reporting_period_key,

    case
        when p.start_date_variance_days <= 3
            then 'ALIGNED_MINOR_START_DATE_VARIANCE'
        else 'REVIEW_START_DATE_VARIANCE'
    end as period_alignment_status,

    q.value_class,
    q.selection_status,
    q.source_accession_current,
    q.source_accession_prior,

    current_timestamp() as model_created_at

from quarterly_observations q

inner join period_summary p
    on q.company_cik = p.company_cik
    and q.period_end = p.period_end
    and q.duration_class = p.duration_class
