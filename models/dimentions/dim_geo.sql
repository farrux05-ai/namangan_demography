with base as (
  select
    geo_code,
    min(geo_name_raw) as geo_name_raw
  from {{ ref('int_demography_atomic') }}
  group by 1
),
ovr as (
  select
    cast(geo_code as bigint) as geo_code,
    geo_name_clean
  from {{ ref('geo_override') }}   
)
select
  b.geo_code,
  coalesce(o.geo_name_clean, b.geo_name_raw) as geo_name,
  case
    when regexp_matches(geo_name_raw, '(?i)shahri') then 'shahar'
    when regexp_matches(geo_name_raw, '(?i)tumani')then 'tuman'
    when regexp_matches(geo_name_raw, '(?i)viloyati')then 'viloyat'
    when regexp_matches(geo_name_raw, '(?i)respublikasi') then 'respublika'
    else 'nomalum'
  end as geo_level  
from base b
left join ovr o
  on b.geo_code = o.geo_code

