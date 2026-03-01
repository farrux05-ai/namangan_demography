select
  geo_code,
  year,
  metric_key,
  sex,
  settlement_type,
  value as population_cnt
from {{ ref('int_demography_atomic') }}
where metric_group = 'population'