with risk as (
    select
        *,
        count(*) over (
            partition by company_cik, period_end
        ) as company_quarter_count
    from {{ ref('mart_financial_risk_indicators') }}
),

checked as (
    select
        *,
        case
            when company_cik is null
              or company_name is null
              or period_end is null
                then 'NULL_COMPANY_OR_PERIOD'

            when company_quarter_count > 1
                then 'DUPLICATE_COMPANY_QUARTER'

            when monitoring_status not in (
                'REVIEW_REQUIRED',
                'NO_FLAGGED_INDICATORS',
                'INSUFFICIENT_DATA'
            ) or monitoring_status is null
                then 'INVALID_MONITORING_STATUS'

            when revenue_concept_count > 1
              or operating_income_concept_count > 1
              or net_income_concept_count > 1
                then 'AMBIGUOUS_FINANCIAL_CONCEPTS'

            when risk_indicator_count < 0
              or risk_indicator_count > 4
                then 'INVALID_RISK_INDICATOR_COUNT'

            when risk_indicator_count <>
                (
                    case when revenue_growth_decline_flag then 1 else 0 end
                    + case when operating_margin_contraction_flag then 1 else 0 end
                    + case when net_income_growth_decline_flag then 1 else 0 end
                    + case when financial_anomaly_flag then 1 else 0 end
                )
                then 'FLAG_COUNT_MISMATCH'

            when risk_indicator_count > 0
              and monitoring_status <> 'REVIEW_REQUIRED'
                then 'INVALID_REVIEW_STATUS'

            when operating_margin is not null
              and (
                  revenue is null
                  or revenue <= 0
                  or operating_income is null
              )
                then 'INVALID_MARGIN_CALCULATION'
        end as test_failure
    from risk
)

select
    company_cik,
    period_end,
    test_failure
from checked
where test_failure is not null
