with merging as (
    select * from {{ ref("stg_sdmx_223_long") }}
    union all select * from {{ ref("stg_sdmx_224_long") }}
    union all select * from {{ ref("stg_sdmx_225_long") }}
    union all select * from {{ ref("stg_sdmx_226_long") }}
    union all select * from {{ ref("stg_sdmx_227_long") }}
    union all select * from {{ ref("stg_sdmx_228_long") }}
    union all select * from {{ ref("stg_sdmx_230_long") }}
    union all select * from {{ ref("stg_sdmx_232_long") }}
    union all select * from {{ ref("stg_sdmx_233_long") }}
    union all select * from {{ ref("stg_sdmx_235_long") }}
    union all select * from {{ ref("stg_sdmx_242_long") }}
    union all select * from {{ ref("stg_sdmx_243_long") }}
    union all select * from {{ ref("stg_sdmx_244_long") }}
    union all select * from {{ ref("stg_sdmx_245_long") }}
    union all select * from {{ ref("stg_sdmx_246_long") }}
    union all select * from {{ ref("stg_sdmx_247_long") }}
    union all select * from {{ ref("stg_sdmx_248_long") }}
    union all select * from {{ ref("stg_sdmx_268_long") }}
    union all select * from {{ ref("stg_sdmx_269_long") }}
)

select
    m.dataset_id,
    m.geo_code,
    m.geo_name_raw,
    m.year,
    d.metric_group,
    d.metric_key,
    coalesce(d.sex, 'total') as sex,
    coalesce(d.settlement_type, 'total') as settlement_type,
    m.value
from merging m
left join {{ ref("dim_metric") }} d
  on m.dataset_id = d.dataset_id
where d.dataset_id is not null  




