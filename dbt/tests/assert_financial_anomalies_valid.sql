with anomalies as (

    select *
    from {{ ref('mart_financial_anomalies') }}

)

select
    company_cik,
    metric_name,
    period_end,
    'INVALID_COMPARISON_STATUS' as test_failure

from anomalies

where comparison_quality_status not in (
    'COMPARABLE',
    'ZERO_PRIOR_YEAR_BASELINE',
    'NEGATIVE_PRIOR_YEAR_BASELINE',
    'SIGN_CHANGE_TO_NEGATIVE'
)

union all

select
    company_cik,
    metric_name,
    period_end,
    'NON_COMPARABLE_HAS_GROWTH' as test_failure

from anomalies

where comparison_quality_status <> 'COMPARABLE'
  and yoy_growth_pct is not null

union all

select
    company_cik,
    metric_name,
    period_end,
    'COMPARABLE_MISSING_GROWTH' as test_failure

from anomalies

where comparison_quality_status = 'COMPARABLE'
  and yoy_growth_pct is null

union all

select
    company_cik,
    metric_name,
    period_end,
    'INVALID_ANOMALY_FLAG' as test_failure

from anomalies

where anomaly_status = 'ANOMALY'
  and (
      comparison_quality_status <> 'COMPARABLE'
      or historical_observation_count < 6
      or historical_stddev_yoy_growth_pct is null
      or historical_stddev_yoy_growth_pct <= 0
      or abs(anomaly_z_score) <= 3
  )

union all

select
    company_cik,
    metric_name,
    period_end,
    'INVALID_ANOMALY_STATUS' as test_failure

from anomalies

where anomaly_status not in (
    'ANOMALY',
    'NORMAL',
    'INSUFFICIENT_HISTORY',
    'NO_VARIANCE_BASELINE',
    'NON_COMPARABLE'
)
