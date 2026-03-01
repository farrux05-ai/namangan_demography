# Architecture & Design Decisions

This document explains *why* the pipeline is built the way it is, not just *what* it does. It is the place to look when something seems unexpected or you want to extend the project.

---

## Layer responsibilities

### Raw layer — immutable archive

Raw CSVs are downloaded once and never touched by dbt. The DuckDB raw views (`raw.sdmx_data_<id>`) are thin wrappers created by a macro — they contain no business logic. This means:

- You can always re-run dbt from scratch against the same raw files and get identical results.
- If a source file is updated upstream, the change is visible and traceable.

### Staging — one model per source dataset

Each SDMX export has its own staging model (`stg_sdmx_<id>_long`). Every staging model does exactly one thing: convert the wide SDMX format (one column per year) into a long format (one row per year).

**Output contract** (all staging models share this):
```
dataset_id, geo_code, geo_name_raw, year, value
```

No business logic is allowed in staging. Metric semantics (what does dataset 226 measure?) are resolved only in the intermediate layer via `dim_metric`.

### Intermediate — single atomic table

`int_demography_atomic` is the central join point. It unions all staging models and enriches each row with the metric dictionary. After this layer every row has:

```
geo_code, year, metric_group, metric_key, sex, settlement_type, value, dataset_id
```

This is the table all facts and marts read from. It keeps downstream models simple: they only need to filter and pivot.

**Why UNION ALL here and not later?**
Doing the union at the intermediate layer means facts and marts don't need to know which dataset IDs are involved. Adding a new data source only requires a new staging model and a row in `dim_metric` — nothing else changes.

### Dimensions

| Dimension | Source | Notes |
|-----------|--------|-------|
| `dim_geo` | Derived from `int_demography_atomic` + `geo_override` seed | Geo names in source files are inconsistent (e.g. "Namangan shahri" vs "Namangan sh."). `geo_override` seed holds canonical names. |
| `dim_metric` | Seed CSV | Maps `dataset_id` to `metric_key`, `metric_group`, `sex`, `settlement_type`. This is the core semantic layer. |
| `dim_sex` | Seed / static | Labels and sort order only. |
| `dim_settlement_type` | Seed / static | Labels and sort order only. |

**Why is `dim_geo` derived and not a seed?**
Geo codes come from the raw data itself. A seed would require manual maintenance every time a new geo appears. The current approach auto-discovers geo codes from the data and applies name overrides on top.

### Facts

Two fact tables sit between the atomic table and the marts:

- `fact_population_yearly` — stock metrics only (population counts)
- `fact_demography_flows_yearly` — flow metrics (births, deaths, migration, marriages, divorces)

This separation follows the stock vs. flow distinction in demographic accounting. It also makes it easier to add temporal logic (e.g. rolling averages) to each type independently.

### Marts

Marts are the only layer the dashboard reads. They are wide, pre-aggregated, and scoped to a specific analytical question.

| Mart | Grain | Key derived columns |
|------|-------|---------------------|
| `mart_region_overview_yearly` | geo × year | `natural_increase`, `net_migration`, `cbr_per_1000`, `cdr_per_1000`, `net_mig_per_1000` |
| `mart_population_split_yearly` | geo × year | `sex_diff`, `settlement_diff`, `missing_women_flag` |
| `mart_births_by_sex_yearly` | geo × year | `share_girls`, `share_boys`, `sex_diff` |
| `mart_metric_coverage` | metric_key × year | `rows_cnt`, `non_null_cnt` |

---

## Data quality approach

### Reconciliation diffs

Several marts include a `*_diff` column that checks whether sub-totals sum to the total:

```sql
-- mart_population_split_yearly
population_total - (population_men + population_women) as sex_diff
population_total - (population_urban + population_rural) as settlement_diff
```

A non-zero diff signals either a data quality issue in the source or a definition mismatch (e.g. some rows include a third settlement category not in urban/rural).

### Missing women flag

Female population data is only available from 2014 in the SIAT source. Rather than silently returning NULL, `mart_population_split_yearly` includes:

```sql
case when population_women is null then 1 else 0 end as missing_women_flag
```

The dashboard surfaces this as a warning when the flag is set.

### Coverage matrix

`mart_metric_coverage` provides a metric × year matrix of non-null counts. This lets consumers see at a glance which combinations are reliable before building charts or comparisons.

---

## Current scope limitation: Namangan only

The `geo_override` seed and mart WHERE clauses currently filter to `1714%`. This was an intentional scoping decision for the first version — the goal was to validate the pipeline against one region before generalising.

To extend to all regions:
1. Add rows to `geo_override.csv` for other viloyatlar
2. Remove the `where cast(geo_code as varchar) like '1714%'` clause from mart models (or replace with a dbt variable)
3. Consider adding a `region_code` column to `dim_geo` to support region-level filtering in the dashboard

---

## Ingestion design

`ingest/download.py` writes a `.meta.json` sidecar next to each raw CSV:

```json
{
  "dataset_id": "226",
  "source_url": "https://siat.stat.uz/...",
  "downloaded_at": "2024-11-15T10:32:00Z",
  "row_count": 1456
}
```

This makes it possible to audit when each file was downloaded and detect if a source has changed without re-running the full pipeline.

---

## What to do next (production readiness checklist)

- [ ] Parameterise geo scope with a dbt variable (`var('geo_prefix', '1714')`)
- [ ] Add `geo_override` rows for other regions
- [ ] Schedule ingestion (cron or Airflow) — currently manual
- [ ] Add `dbt source freshness` check on raw CSV modification dates
- [ ] Move `dev.duckdb` out of the repo; use a shared location or object storage for team use
- [ ] Add `dbt docs generate` to CI so model documentation is always up to date
