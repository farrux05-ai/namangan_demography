select
  metric_key,
  year,
  count(*) as rows_cnt,
  sum(case when value is not null then 1 else 0 end) as non_null_cnt
from {{ ref('int_demography_atomic') }}
where cast(geo_code as varchar) like '1714%'
group by 1,2
order by 1,2