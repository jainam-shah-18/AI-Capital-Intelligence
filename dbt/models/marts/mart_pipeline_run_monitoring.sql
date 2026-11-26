with pipeline_logs as (

    select *
    from {{ ref('stg_pipeline_run_log') }}

),

latest_pipeline_run as (

    select
        pipeline_name,
        run_id
    from pipeline_logs
    where component = 'PIPELINE'
    qualify row_number() over (
        partition by pipeline_name
        order by started_at desc, created_at desc
    ) = 1

)

select
    logs.run_id,
    logs.pipeline_name,
    logs.component,
    logs.status,
    logs.started_at,
    logs.finished_at,
    logs.duration_seconds,
    logs.rows_extracted,
    logs.rows_loaded,
    logs.source_name,
    logs.target_name,
    logs.error_message,
    logs.created_at,

    (logs.run_id = latest.run_id) as is_latest_run

from pipeline_logs logs

left join latest_pipeline_run latest
    on logs.pipeline_name = latest.pipeline_name