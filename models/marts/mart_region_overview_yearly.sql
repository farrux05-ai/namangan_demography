with base as (
  select
    i.geo_code,
    d.geo_name,
    d.geo_level,
    i.year,
    i.metric_key,
    i.value
  from {{ ref('int_demography_atomic') }} i
  left join {{ref('dim_geo')}} d 
  on i.geo_code = d.geo_code
  where cast(i.geo_code as varchar) like '1714%'
    and i.sex = 'total'
    and i.settlement_type = 'total'
    and i.metric_key in (
      'population_total',
      'birth_total',
      'death_total',
      'in_migration',
      'out_migration',
      'marriages_total',
      'divorces_total'
    )
),
pivoted as (
  select
    geo_code,
    geo_name,
    geo_level,
    year,
    max(case when metric_key = 'population_total' then value end) as population_total,
    max(case when metric_key = 'birth_total' then value end) as birth_total,
    max(case when metric_key = 'death_total' then value end) as death_total,
    max(case when metric_key = 'in_migration' then value end) as in_migration,
    max(case when metric_key = 'out_migration' then value end) as out_migration,
    max(case when metric_key = 'marriages_total' then value end) as marriages_total,
    max(case when metric_key = 'divorces_total' then value end) as divorces_total
  from base
  group by 1,2,3,4
)

select
  *,
  (birth_total - death_total) as natural_increase,
  (in_migration - out_migration) as net_migration,
  (birth_total / nullif(population_total, 0)) * 1000 as cbr_per_1000,
  (death_total / nullif(population_total, 0)) * 1000 as cdr_per_1000,
  ((in_migration - out_migration) / nullif(population_total, 0)) * 1000 as net_mig_per_1000,
from pivoted
where cast(geo_code as varchar) like '1714%'