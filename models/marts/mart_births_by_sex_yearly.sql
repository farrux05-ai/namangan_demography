-- grain geo_code x year x sex
-- total birth, birth girl, birth boy, share
with sex_split as (
    select
        geo_code,
        year,
        sex,
        metric_key,
        value
    from {{ref("int_demography_atomic")}}
    where cast(geo_code as varchar) like '1714%'
    and metric_key in (
        'birth_total',
        'birth_girls',
        'birth_boys'
    )
),
pivoted as(
    select
        geo_code,
        year,
        max(case when metric_key = 'birth_total' then value end) as total_birth_yearly,
        max(case when metric_key = 'birth_girls' then value end) as birth_girls,
        max(case when metric_key = 'birth_boys' then value end) as birth_boys
    from sex_split
    group by 1,2
)
select 
    *,
    (birth_girls / nullif(total_birth_yearly, 0)* 100) as share_girls,
    (birth_boys / nullif(total_birth_yearly, 0) * 100) as share_boys,
    (total_birth_yearly - (birth_girls + birth_boys)) as sex_diff
from pivoted