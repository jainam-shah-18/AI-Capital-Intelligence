{{ config(materialized='table') }}

with revenue_history as (

    select
        company_cik,
        company_name,
        fiscal_calendar_type,
        fiscal_year,
        fiscal_quarter_number,
        fiscal_quarter,
        period_start,
        period_end,
        financial_value as actual_revenue

    from {{ ref('int_financial_period_calendar') }}

    where metric_name = 'REVENUE'
      and duration_class = 'QUARTER_DURATION'
      and financial_value is not null
      and fiscal_year is not null
      and fiscal_quarter_number is not null

),

historical_backtest as (

    select
        current_period.company_cik,
        current_period.company_name,
        current_period.fiscal_calendar_type,

        'BACKTEST' as forecast_record_type,

        current_period.fiscal_year as target_fiscal_year,
        current_period.fiscal_quarter as target_fiscal_quarter,

        current_period.period_start as target_period_start,
        current_period.period_end as target_period_end,

        current_period.period_end as actual_period_end,

        prior_period.period_end as forecast_source_period_end,

        current_period.actual_revenue,

        prior_period.actual_revenue as forecast_revenue,

        current_period.actual_revenue
            - prior_period.actual_revenue as forecast_error,

        abs(
            current_period.actual_revenue
            - prior_period.actual_revenue
        ) as absolute_error,

        abs(
            (
                current_period.actual_revenue
                - prior_period.actual_revenue
            ) / nullif(current_period.actual_revenue, 0)
        ) * 100 as absolute_percentage_error

    from revenue_history current_period

    left join revenue_history prior_period
        on current_period.company_cik = prior_period.company_cik
        and current_period.fiscal_year - 1 = prior_period.fiscal_year
        and current_period.fiscal_quarter_number
            = prior_period.fiscal_quarter_number

),

latest_company_period as (

    select *

    from revenue_history

    qualify row_number() over (
        partition by company_cik
        order by period_end desc
    ) = 1

),

next_quarter_targets as (

    select
        company_cik,
        company_name,
        fiscal_calendar_type,

        case
            when fiscal_quarter_number = 4
                then fiscal_year + 1
            else fiscal_year
        end as target_fiscal_year,

        mod(fiscal_quarter_number, 4) + 1
            as target_fiscal_quarter_number,

        'Q' || (mod(fiscal_quarter_number, 4) + 1)
            as target_fiscal_quarter,

        last_day(dateadd(month, 3, period_end)) as target_period_end

    from latest_company_period

),


next_quarter_forecast as (

    select
        target.company_cik,
        target.company_name,
        target.fiscal_calendar_type,

        'NEXT_QUARTER_FORECAST' as forecast_record_type,

        target.target_fiscal_year,
        target.target_fiscal_quarter,

        cast(null as date) as target_period_start,

        target.target_period_end,

        cast(null as date) as actual_period_end,

        coalesce(
            source.period_end,
            latest.period_end
        ) as forecast_source_period_end,

        cast(null as number(38, 2)) as actual_revenue,

        coalesce(
            source.actual_revenue,
            latest.actual_revenue
        ) as forecast_revenue,

        cast(null as number(38, 2)) as forecast_error,

        cast(null as number(38, 2)) as absolute_error,

        cast(null as number(38, 4))
            as absolute_percentage_error

    from next_quarter_targets target

    left join revenue_history source
        on target.company_cik = source.company_cik
        and target.target_fiscal_year - 1 = source.fiscal_year
        and target.target_fiscal_quarter_number
            = source.fiscal_quarter_number

    left join latest_company_period latest
        on target.company_cik = latest.company_cik

)

select
    *,
    current_timestamp() as model_created_at
from historical_backtest

union all

select
    *,
    current_timestamp() as model_created_at
from next_quarter_forecast
