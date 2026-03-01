{% macro bootstrap_raw_views() %}
  {% set table_ids = [223, 224, 225, 226, 227, 228, 230, 232, 233, 235, 238, 239, 242, 243, 244, 245, 246, 247, 248, 268, 269] %}

  {% set sql %}
    create schema if not exists raw;
    {% for id in table_ids %}
      create or replace view raw.sdmx_data_{{ id }} as
      select * from read_csv_auto('data/raw/siat_stat_uz/sdmx_data_{{ id }}.csv');
    {% endfor %}
  {% endset %}

  {% do run_query(sql) %}
  {{ print('Viewslar hammasi muvaffaqiyatli yaratildi') }}
{% endmacro %}