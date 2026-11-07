WITH candidates AS (

    SELECT *
    FROM {{ ref('int_financial_quarterly_cashflow_derived') }}

),

duplicate_candidates AS (

    SELECT
        company_cik,
        metric_name,
        concept_name,
        derived_fiscal_quarter,
        period_start,
        period_end
    FROM candidates
    GROUP BY ALL
    HAVING COUNT(*) > 1

),

violations AS (

    SELECT 'NULL_DERIVED_VALUE' AS issue
    FROM candidates
    WHERE derived_candidate_value IS NULL

    UNION ALL

    SELECT 'MISSING_SOURCE_ACCESSION'
    FROM candidates
    WHERE source_accession_current IS NULL
       OR source_accession_prior IS NULL

    UNION ALL

    SELECT 'INVALID_DERIVATION_STATUS'
    FROM candidates
    WHERE derivation_status NOT IN (
        'REPORTING_BASIS_UNKNOWN',
        'REPORTING_BASIS_MISMATCH',
        'REVIEW_REQUIRED'
    )

    UNION ALL

    SELECT 'INVALID_QUARTER'
    FROM candidates
    WHERE derived_fiscal_quarter NOT IN ('Q2', 'Q3', 'Q4')

    UNION ALL

    SELECT 'DUPLICATE_CANDIDATE'
    FROM duplicate_candidates

)

SELECT *
FROM violations