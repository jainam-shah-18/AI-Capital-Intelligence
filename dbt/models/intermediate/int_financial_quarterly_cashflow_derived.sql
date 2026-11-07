
{{ config(materialized='view') }}

with canonical_cashflows as (

    select
        company_cik,
        company_name,
        metric_name,
        concept_name,
        unit,
        period_start,
        period_end,
        duration_class,
        filing_fiscal_period,
        financial_value,
        reporting_basis,
        filing_form,
        filed_date,
        accession_number

    from {{ ref('int_financial_metric_canonical') }}

    where cross_concept_selection_status = 'CANONICAL_SELECTED'
      and financial_value is not null
      and metric_name in ('OPERATING_CASH_FLOW', 'CAPEX')

),

/* Q2 = H1 cumulative - Q1 */

q2_candidates as (

    select
        h.company_cik,
        h.company_name,
        h.metric_name,
        h.concept_name,
        h.unit,

        dateadd(day, 1, q.period_end) as period_start,
        h.period_end as period_end,

        'QUARTER_DURATION' as duration_class,
        'Q2' as derived_fiscal_quarter,

        h.financial_value - q.financial_value
            as derived_candidate_value,

        'H1_MINUS_Q1' as derivation_method,

        h.accession_number as source_accession_current,
        q.accession_number as source_accession_prior,

        h.reporting_basis as current_reporting_basis,
        q.reporting_basis as prior_reporting_basis,

        h.filing_form as current_filing_form,
        h.filed_date as current_filed_date,

        case
            when h.reporting_basis is null
              or q.reporting_basis is null
                then 'REPORTING_BASIS_UNKNOWN'
            when h.reporting_basis <> q.reporting_basis
                then 'REPORTING_BASIS_MISMATCH'
            else 'REVIEW_REQUIRED'
        end as derivation_status

    from canonical_cashflows h

    inner join canonical_cashflows q
        on h.company_cik = q.company_cik
       and h.metric_name = q.metric_name
       and h.concept_name = q.concept_name
       and h.unit = q.unit
       and h.period_start = q.period_start
       and h.duration_class = 'HALF_YEAR_DURATION'
       and q.duration_class = 'QUARTER_DURATION'
       and q.period_end = dateadd(day, -1, dateadd(month, 3, h.period_start))
       and h.period_end = dateadd(day, -1, dateadd(month, 6, h.period_start))

),

/* Q3 = 9M cumulative - H1 cumulative */

q3_candidates as (

    select
        n.company_cik,
        n.company_name,
        n.metric_name,
        n.concept_name,
        n.unit,

        dateadd(day, 1, h.period_end) as period_start,
        n.period_end as period_end,

        'QUARTER_DURATION' as duration_class,
        'Q3' as derived_fiscal_quarter,

        n.financial_value - h.financial_value
            as derived_candidate_value,

        'NINE_MONTH_MINUS_HALF_YEAR' as derivation_method,

        n.accession_number as source_accession_current,
        h.accession_number as source_accession_prior,

        n.reporting_basis as current_reporting_basis,
        h.reporting_basis as prior_reporting_basis,

        n.filing_form as current_filing_form,
        n.filed_date as current_filed_date,

        case
            when n.reporting_basis is null
              or h.reporting_basis is null
                then 'REPORTING_BASIS_UNKNOWN'
            when n.reporting_basis <> h.reporting_basis
                then 'REPORTING_BASIS_MISMATCH'
            else 'REVIEW_REQUIRED'
        end as derivation_status

    from canonical_cashflows n

    inner join canonical_cashflows h
        on n.company_cik = h.company_cik
       and n.metric_name = h.metric_name
       and n.concept_name = h.concept_name
       and n.unit = h.unit
       and n.period_start = h.period_start
       and n.duration_class = 'NINE_MONTH_DURATION'
       and h.duration_class = 'HALF_YEAR_DURATION'
       and h.period_end = dateadd(day, -1, dateadd(month, 6, n.period_start))
       and n.period_end = dateadd(day, -1, dateadd(month, 9, n.period_start))

),

/* Q4 = full fiscal year - 9M cumulative */

q4_candidates as (

    select
        f.company_cik,
        f.company_name,
        f.metric_name,
        f.concept_name,
        f.unit,

        dateadd(day, 1, n.period_end) as period_start,
        f.period_end as period_end,

        'QUARTER_DURATION' as duration_class,
        'Q4' as derived_fiscal_quarter,

        f.financial_value - n.financial_value
            as derived_candidate_value,

        'FULL_YEAR_MINUS_NINE_MONTH' as derivation_method,

        f.accession_number as source_accession_current,
        n.accession_number as source_accession_prior,

        f.reporting_basis as current_reporting_basis,
        n.reporting_basis as prior_reporting_basis,

        f.filing_form as current_filing_form,
        f.filed_date as current_filed_date,

        case
            when f.reporting_basis is null
              or n.reporting_basis is null
                then 'REPORTING_BASIS_UNKNOWN'
            when f.reporting_basis <> n.reporting_basis
                then 'REPORTING_BASIS_MISMATCH'
            else 'REVIEW_REQUIRED'
        end as derivation_status

    from canonical_cashflows f

    inner join canonical_cashflows n
        on f.company_cik = n.company_cik
       and f.metric_name = n.metric_name
       and f.concept_name = n.concept_name
       and f.unit = n.unit
       and f.period_start = n.period_start
       and f.duration_class = 'ANNUAL_DURATION'
       and n.duration_class = 'NINE_MONTH_DURATION'
       and f.filing_fiscal_period = 'FY'
       and n.period_end = dateadd(day, -1, dateadd(month, 9, f.period_start))
       and f.period_end = dateadd(day, -1, dateadd(month, 12, f.period_start))

    where
        (
            f.company_cik in ('1018724', '1326801', '1652044')
            and month(f.period_start) = 1
            and day(f.period_start) = 1
            and month(f.period_end) = 12
            and day(f.period_end) = 31
        )
        or
        (
            f.company_cik = '789019'
            and month(f.period_start) = 7
            and day(f.period_start) = 1
            and month(f.period_end) = 6
            and day(f.period_end) = 30
        )

)

select * from q2_candidates

union all

select * from q3_candidates

union all

select * from q4_candidates
