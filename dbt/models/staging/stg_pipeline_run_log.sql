select
    run_id,
    pipeline_name,
    component,
    status,
    started_at,
    finished_at,
    duration_seconds,
    rows_extracted,
    rows_loaded,
    source_name,
    target_name,
    error_message,
    created_at
from {{ source('aci_monitoring', 'pipeline_run_log') }}