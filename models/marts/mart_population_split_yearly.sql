with pop as (
  select
    geo_code,
    year,
    metric_key,
    value
  from {{ ref('int_demography_atomic') }}
  where cast(geo_code as varchar) like '1714%'
    and metric_group = 'population'
    and (
      metric_key in (
        'population_total',
        'population_men',
        'population_women',
        'population_urban',
        'population_rural'
      )
    )
),

pivoted as (
  select
    geo_code,
    year,
    max(case when metric_key = 'population_total' then value end) as population_total,
    max(case when metric_key = 'population_men' then value end) as population_men,
    max(case when metric_key = 'population_women' then value end) as population_women,
    max(case when metric_key = 'population_urban' then value end) as population_urban,
    max(case when metric_key = 'population_rural' then value end) as population_rural
  from pop
  group by 1,2
)

select
  *,
  case
    when population_total is not null and population_men is not null and population_women is not null
  then population_total - (population_men + population_women) 
  else null
  end as sex_diff,
  case
    when population_total is not null and population_urban is not null and population_rural is not null
  then population_total - (population_urban + population_rural)
  else null
  end as settlement_diff,
  case when population_women is null then 1 else 0 end as missing_women_flag
from pivoted 
