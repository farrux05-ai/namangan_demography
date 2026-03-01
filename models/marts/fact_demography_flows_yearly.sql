select
  geo_code,
  year,
  metric_group,
  metric_key,
  sex,
  settlement_type,
  value as event_cnt
from {{ ref('int_demography_atomic') }}
where metric_group in ('birth', 'death', 'migration', 'marriages', 'divorce')