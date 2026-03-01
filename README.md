# Namangan Demography (Analytics Engineering Project)

This project turns Uzbekistan open statistics (SIAT SDMX exports) into a reusable analytics dataset and dashboard-ready marts for **Namangan region (geo_code prefix `1714%`)**.

The main goal is to produce a **more reusable and auditable** alternative to static PDF summaries:
- consistent metric definitions
- conformed dimensions (geo / sex / settlement type / metric dictionary)
- data quality & coverage checks
- reproducible ingestion + dbt transformations

---

## What you can analyze

### Core indicators (2010–2024)
- **Population (stock)**: total, male, female *(female coverage starts in 2014)*, urban, rural
- **Births (flow)**: total, girls, boys
- **Deaths (flow)**: total, women, men
- **Migration (flow)**: in / out (total)
- **Marriages (flow)**: total, urban, rural
- **Divorces (flow)**: total, urban, rural

---

## Data sources

Data is downloaded from SIAT SDMX export endpoints, stored as raw CSV files, and then processed via dbt + DuckDB.

- Raw file naming convention: `sdmx_data_<dataset_id>.csv`
- Dataset dictionary is maintained in `dbt/seeds/dim_metric.csv`
- Geographical naming overrides are maintained in `dbt/seeds/geo_override.csv`

---

## Architecture (layered)

**Raw → Staging → Intermediate → Dimensions → Marts**

### 1) Ingestion (raw archive)
- `ingest/manifest.csv`: registry of dataset ids, URLs, filenames, and metric keys
- `ingest/download.py`: downloads all datasets and writes metadata sidecars (`.meta.json`)
- Raw files are stored in `data/raw/siat_stat_uz/`

### 2) DuckDB raw views
A dbt macro creates DuckDB views over raw CSV files:
- `raw.sdmx_data_<id>` views point to `data/raw/siat_stat_uz/sdmx_data_<id>.csv`

### 3) Staging (reshape)
Each SDMX wide CSV is converted to a long format:
- `stg_sdmx_<id>_long`
- contract: `dataset_id, geo_code, geo_name_raw, year, value`

### 4) Intermediate (conformed atomic)
`int_demography_atomic` unions all staging models and joins the metric dictionary (`dim_metric`) to provide consistent semantics:
- contract: `geo_code, year, metric_group, metric_key, sex, settlement_type, value, dataset_id`

### 5) Dimensions (conformed)
- `dim_geo`: clean geo names + hierarchy (`parent_geo_code`)
- `dim_sex`: male / female / total labels & order
- `dim_settlement_type`: urban / rural / total labels & order
- `dim_metric` (seed): dataset_id → metric semantics

### 6) Marts (dashboard-ready)
- `fact_population_yearly` - total population urban, rural, men and woman, representes stock of geo
- `fact_demography_flows_yearly` - flow (birth, death, in migration, out migration, divorces, marriages) 
- `mart_namangan_overview_yearly`: totals + derived KPIs (CBR/CDR/net migration per 1000)
- `mart_population_split_yearly`: population components + reconciliation diffs + missing flags
- `mart_births_by_sex_yearly`: girls/boys shares + reconciliation diff
- `mart_metric_coverage` : dataset coverage and missing values

---

## How to run (local)

### Prerequisites
- Python environment (for ingestion)
- dbt + DuckDB adapter configured

### Step 1 — Download raw data
```bash
python ingest/download.py
