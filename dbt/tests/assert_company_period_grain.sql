
WITH performance_duplicates AS (

    SELECT
        'MART_COMPANY_PERFORMANCE' AS model_name,
        company_cik,
        period_end
    FROM {{ ref('mart_company_performance') }}
    GROUP BY company_cik, period_end
    HAVING COUNT(*) > 1

),

comparison_duplicates AS (

    SELECT
        'MART_COMPANY_COMPARISON' AS model_name,
        company_cik,
        period_end
    FROM {{ ref('mart_company_comparison') }}
    GROUP BY company_cik, period_end
    HAVING COUNT(*) > 1

)

SELECT * FROM performance_duplicates

UNION ALL

SELECT * FROM comparison_duplicates
