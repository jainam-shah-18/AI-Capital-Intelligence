
WITH period_checks AS (

    SELECT
        period_end,
        COUNT(DISTINCT company_cik) AS company_count,
        COUNT(DISTINCT period_start) AS start_date_count,
        COUNT(DISTINCT duration_class) AS duration_class_count,
        SUM(revenue_share_pct) AS total_revenue_share_pct

    FROM {{ ref('mart_company_comparison') }}

    GROUP BY period_end

)

SELECT
    period_end,
    company_count,
    start_date_count,
    duration_class_count,
    total_revenue_share_pct

FROM period_checks

WHERE company_count <> 4
   OR start_date_count <> 1
   OR duration_class_count <> 1
   OR ABS(total_revenue_share_pct - 100) > 0.01
