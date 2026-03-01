with source as(
    select *
    from {{source('namangan_raw_data', 'sdmx_data_224')}}
),
unpivoted_data as (
    unpivot source 
    on "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"
    into 
        name year_str
        value value_raw
)
select 
    224 as dataset_id,
    Code as geo_code,
    coalesce(Klassifikator) as geo_name_raw,
    cast(year_str as int) as year,
    cast(value_raw as double) as value
from unpivoted_data
where value_raw is not null