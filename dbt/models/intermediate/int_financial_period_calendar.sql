{{ config(materialized='view') }}

with reported_quarters as (

    select *
    from {{ ref('int_quarterly_financial_observations') }}

),

calendar_classification as (

    select
        *,

        year(period_end) as calendar_year,

        quarter(period_end) as calendar_quarter_number,

        'Q' || quarter(period_end) as calendar_quarter,

        case
            when to_varchar(company_cik) = '789019'
                then 'JULY_JUNE'
            when to_varchar(company_cik) in (
                '1018724',
                '1652044',
                '1326801'
            )
                then 'JANUARY_DECEMBER'
            else 'UNKNOWN'
        end as fiscal_calendar_type

    from reported_quarters

),

fiscal_periods as (

    select
        *,

        case
            when fiscal_calendar_type = 'JULY_JUNE'
                then year(dateadd(month, 6, period_end))
            when fiscal_calendar_type = 'JANUARY_DECEMBER'
                then year(period_end)
            else null
        end as fiscal_year,

        case
            when fiscal_calendar_type = 'JULY_JUNE'
                then quarter(dateadd(month, 6, period_end))
            when fiscal_calendar_type = 'JANUARY_DECEMBER'
                then quarter(period_end)
            else null
        end as fiscal_quarter_number

    from calendar_classification

),

validated_periods as (

    select
        *,

        'Q' || fiscal_quarter_number as fiscal_quarter,

        case
            when fiscal_calendar_type = 'JULY_JUNE'
                then 'JUNE_30'
            when fiscal_calendar_type = 'JANUARY_DECEMBER'
                then 'DECEMBER_31'
            else 'UNKNOWN'
        end as fiscal_year_end_basis,

        case
            when fiscal_calendar_type = 'UNKNOWN'
                then 'UNKNOWN_COMPANY_CALENDAR'
            when filing_fiscal_period is null
                then 'SOURCE_FISCAL_PERIOD_MISSING'
            when upper(trim(filing_fiscal_period))
                = 'Q' || fiscal_quarter_number
                then 'MATCH'
            when upper(trim(filing_fiscal_period)) = 'FY'
                then 'FY_LABEL_ON_QUARTER_RECORD'
            when upper(trim(filing_fiscal_period))
                in ('Q1', 'Q2', 'Q3', 'Q4')
                then 'FISCAL_QUARTER_MISMATCH'
            else 'UNRECOGNIZED_SOURCE_LABEL'
        end as fiscal_period_validation,

        case
            when fiscal_year is null
                then 'UNKNOWN_COMPANY_CALENDAR'
            when filing_fiscal_year is null
                then 'SOURCE_FISCAL_YEAR_MISSING'
            when try_to_number(filing_fiscal_year) = fiscal_year
                then 'MATCH'
            else 'FISCAL_YEAR_MISMATCH'
        end as fiscal_year_validation

    from fiscal_periods

)

select
    company_cik,
    company_name,

    metric_name,
    concept_name,
    unit,

    period_start,
    period_end,

    calendar_year,
    calendar_quarter_number,
    calendar_quarter,

    fiscal_calendar_type,
    fiscal_year,
    fiscal_quarter_number,
    fiscal_quarter,
    fiscal_year_end_basis,

    filing_fiscal_year as original_filing_fiscal_year,
    filing_fiscal_period as original_filing_fiscal_period,

    fiscal_year_validation,
    fiscal_period_validation,

    financial_value,
    duration_class,

    filing_form,
    filed_date,
    accession_number,
    sec_frame,

    value_class,
    selection_status,

    source_accession_current,
    source_accession_prior,

    current_timestamp() as model_created_at

from validated_periods
