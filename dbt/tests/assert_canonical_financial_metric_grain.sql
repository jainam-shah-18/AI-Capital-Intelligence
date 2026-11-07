
SELECT
    company_cik,
    metric_name,
    unit,
    period_start,
    period_end,
    duration_class

FROM {{ ref('mart_financial_metrics_canonical') }}

GROUP BY
    company_cik,
    metric_name,
    unit,
    period_start,
    period_end,
    duration_class

HAVING COUNT(*) > 1
