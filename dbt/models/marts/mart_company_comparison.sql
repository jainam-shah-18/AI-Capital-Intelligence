
{{ config(materialized='table') }}

WITH base AS (

    SELECT
        company_cik,
        company_name,
        period_start,
        period_end,

        YEAR(period_end) AS calendar_year,
        QUARTER(period_end) AS calendar_quarter,

        filing_fiscal_year,
        filing_fiscal_period,

        revenue,
        operating_income,
        net_income,

        operating_margin_pct,
        net_profit_margin_pct,
        revenue_yoy_growth_pct,

        duration_class,
        mart_created_at

    FROM {{ ref('mart_company_performance') }}

),

period_coverage AS (

    SELECT
        period_end,
        COUNT(DISTINCT company_cik) AS company_count

    FROM base

    GROUP BY period_end

),

common_periods AS (

    SELECT
        period_end

    FROM period_coverage

    WHERE company_count = 4

),

comparison_base AS (

    SELECT
        b.*

    FROM base b

    INNER JOIN common_periods cp
        ON b.period_end = cp.period_end

),

comparison_metrics AS (

    SELECT
        *,

        AVG(revenue) OVER (
            PARTITION BY period_end
        ) AS peer_avg_revenue,

        AVG(operating_income) OVER (
            PARTITION BY period_end
        ) AS peer_avg_operating_income,

        AVG(net_income) OVER (
            PARTITION BY period_end
        ) AS peer_avg_net_income,

        AVG(operating_margin_pct) OVER (
            PARTITION BY period_end
        ) AS peer_avg_operating_margin_pct,

        AVG(net_profit_margin_pct) OVER (
            PARTITION BY period_end
        ) AS peer_avg_net_profit_margin_pct,

        SUM(revenue) OVER (
            PARTITION BY period_end
        ) AS peer_total_revenue,

        RANK() OVER (
            PARTITION BY period_end
            ORDER BY revenue DESC NULLS LAST
        ) AS revenue_rank,

        CASE
            WHEN operating_income IS NOT NULL THEN
                RANK() OVER (
                    PARTITION BY period_end
                    ORDER BY operating_income DESC NULLS LAST
                )
        END AS operating_income_rank,

        CASE
            WHEN net_income IS NOT NULL THEN
                RANK() OVER (
                    PARTITION BY period_end
                    ORDER BY net_income DESC NULLS LAST
                )
        END AS net_income_rank,

        CASE
            WHEN operating_margin_pct IS NOT NULL THEN
                RANK() OVER (
                    PARTITION BY period_end
                    ORDER BY operating_margin_pct DESC NULLS LAST
                )
        END AS operating_margin_rank,

        CASE
            WHEN net_profit_margin_pct IS NOT NULL THEN
                RANK() OVER (
                    PARTITION BY period_end
                    ORDER BY net_profit_margin_pct DESC NULLS LAST
                )
        END AS net_profit_margin_rank,

        CASE
            WHEN revenue_yoy_growth_pct IS NOT NULL THEN
                RANK() OVER (
                    PARTITION BY period_end
                    ORDER BY revenue_yoy_growth_pct DESC NULLS LAST
                )
        END AS revenue_growth_rank

    FROM comparison_base

)

SELECT
    company_cik,
    company_name,

    period_start,
    period_end,

    calendar_year,
    calendar_quarter,

    filing_fiscal_year,
    filing_fiscal_period,

    duration_class,

    revenue,
    operating_income,
    net_income,

    operating_margin_pct,
    net_profit_margin_pct,
    revenue_yoy_growth_pct,

    peer_avg_revenue,
    peer_avg_operating_income,
    peer_avg_net_income,

    peer_avg_operating_margin_pct,
    peer_avg_net_profit_margin_pct,

    peer_total_revenue,

    revenue / NULLIF(peer_total_revenue, 0)
        * 100 AS revenue_share_pct,

    revenue_rank,
    operating_income_rank,
    net_income_rank,

    operating_margin_rank,
    net_profit_margin_rank,
    revenue_growth_rank,

    4 AS comparison_company_count,

    CURRENT_TIMESTAMP() AS mart_created_at

FROM comparison_metrics
