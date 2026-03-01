-- Reconciliation checks for Namangan Demography (1714%)

-- 0) Scope
-- - geo_code like '1714%' covers Namangan region + districts/city
-- - years: 2010–2024
-- - Some components (e.g., population_women) start later (coverage limitation).
--
-- Conventions:
--   diff ~= 0  -> OK
--   diff != 0  -> investigate (could be source definition / rounding / missing component)
--   diff is NULL -> not computed due to missing components (coverage gap)

-- 1) BIRTHS: total vs girls+boys
with births as (
  select
    geo_code,
    year,
    max(case when metric_key = 'birth_total' then value end) as birth_total,
    max(case when metric_key = 'birth_girls' then value end) as birth_girls,
    max(case when metric_key = 'birth_boys' then value end) as birth_boys
  from {{ ref('int_demography_atomic') }}
  where cast(geo_code as varchar) like '1714%'
    and sex = 'total'
    and settlement_type = 'total'
    and metric_key in ('birth_total','birth_girls','birth_boys')
  group by 1,2
)
select
  'births_total_vs_girls_boys' as check_name,
  geo_code,
  year,
  birth_total,
  birth_girls,
  birth_boys,
  (birth_total - (birth_girls + birth_boys)) as diff
from births
order by geo_code, year

-- 2) DEATHS: total vs women+men
--   Note: only computed when all components exist
with deaths as (
  select
    geo_code,
    year,
    max(case when metric_key = 'death_total' then value end) as death_total,
    max(case when metric_key = 'death_women' then value end) as death_women,
    max(case when metric_key = 'death_men' then value end) as death_men
  from {{ ref('int_demography_atomic') }}
  where cast(geo_code as varchar) like '1714%'
    and sex = 'total'
    and settlement_type = 'total'
    and metric_key in ('death_total','death_women','death_men')
  group by 1,2
)
select
  'deaths_total_vs_women_men' as check_name,
  geo_code,
  year,
  death_total,
  death_women,
  death_men,
  (death_total - (death_women + death_men)) as diff
from deaths
order by geo_code, year

-- 3) POPULATION: total vs men+women (only where women exists)
with pop_sex as (
  select
    geo_code,
    year,
    max(case when metric_key = 'population_total' then value end) as population_total,
    max(case when metric_key = 'population_men' then value end) as population_men,
    max(case when metric_key = 'population_women' then value end) as population_women
  from {{ ref('int_demography_atomic') }}
  where cast(geo_code as varchar) like '1714%'
    and metric_key in ('population_total','population_men','population_women')
    and settlement_type = 'total'
  group by 1,2
)
select
  'population_total_vs_men_women' as check_name,
  geo_code,
  year,
  population_total,
  population_men,
  population_women,
  case
    when population_total is not null and population_men is not null and population_women is not null
    then population_total - (population_men + population_women)
    else null
  end as diff,
  case when population_women is null then 1 else 0 end as missing_women_flag
from pop_sex
order by geo_code, year

-- 4) POPULATION: total vs urban+rural
with pop_settlement as (
  select
    geo_code,
    year,
    max(case when metric_key = 'population_total' then value end) as population_total,
    max(case when metric_key = 'population_urban' then value end) as population_urban,
    max(case when metric_key = 'population_rural' then value end) as population_rural
  from {{ ref('int_demography_atomic') }}
  where cast(geo_code as varchar) like '1714%'
    and metric_key in ('population_total','population_urban','population_rural')
    and sex = 'total'
  group by 1,2
)
select
  'population_total_vs_urban_rural' as check_name,
  geo_code,
  year,
  population_total,
  population_urban,
  population_rural,
  case
    when population_total is not null and population_urban is not null and population_rural is not null
    then population_total - (population_urban + population_rural)
    else null
  end as diff
from pop_settlement
order by geo_code, year

-- 5) MARRIAGES: total vs urban+rural
with marriages as (
  select
    geo_code,
    year,
    max(case when metric_key = 'marriages_total' then value end) as marriages_total,
    max(case when metric_key = 'marriages_urban' then value end) as marriages_urban,
    max(case when metric_key = 'marriages_rural' then value end) as marriages_rural
  from {{ ref('int_demography_atomic') }}
  where cast(geo_code as varchar) like '1714%'
    and metric_key in ('marriages_total','marriages_urban','marriages_rural')
    and sex = 'total'
  group by 1,2
)
select
  'marriages_total_vs_urban_rural' as check_name,
  geo_code,
  year,
  marriages_total,
  marriages_urban,
  marriages_rural,
  case
    when marriages_total is not null and marriages_urban is not null and marriages_rural is not null
    then marriages_total - (marriages_urban + marriages_rural)
    else null
  end as diff
from marriages
order by geo_code, year

-- 6) DIVORCES: total vs urban+rural
with divorces as (
  select
    geo_code,
    year,
    max(case when metric_key = 'divorce_total' then value end) as divorce_total,
    max(case when metric_key = 'divorce_urban' then value end) as divorce_urban,
    max(case when metric_key = 'divorce_rural' then value end) as divorce_rural
  from {{ ref('int_demography_atomic') }}
  where cast(geo_code as varchar) like '1714%'
    and metric_key in ('divorce_total','divorce_urban','divorce_rural')
    and sex = 'total'
  group by 1,2
)
select
  'divorces_total_vs_urban_rural' as check_name,
  geo_code,
  year,
  divorce_total,
  divorce_urban,
  divorce_rural,
  case
    when divorce_total is not null and divorce_urban is not null and divorce_rural is not null
    then divorce_total - (divorce_urban + divorce_rural)
    else null
  end as diff
from divorces
order by geo_code, year