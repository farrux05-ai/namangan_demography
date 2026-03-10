# 🏙️ Namangan Demography Analytics — dbt + DuckDB + Streamlit

> **End-to-end analytics engineering project** on Uzbekistan's official open statistics (siat.stat.uz).  
> Raw government SDMX exports → tested dbt pipeline → live Streamlit dashboard.

![dbt](https://img.shields.io/badge/dbt-Core-orange?logo=dbt)
![DuckDB](https://img.shields.io/badge/DuckDB-local%20warehouse-yellow)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-red?logo=streamlit)
![Status](https://img.shields.io/badge/status-live-brightgreen)
![Period](https://img.shields.io/badge/period-2010--2024-blue)

---

## 🔗 Live Links

| | |
|--|--|
| 📊 **Dashboard** | [Open Streamlit App](https://app-9oa8mwwxa6kxj9nbkznjvt.streamlit.app/) |
| 📖 **dbt Docs** | [Open dbt Documentation](https://dbt-demography-docs.vercel.app/) |

---
## Why this project matters

Public demographic data is often fragmented, inconsistently structured, and difficult to analyze directly.
This project turns raw official statistics into a tested analytical warehouse with reusable dimensions, facts, and dashboard-ready marts.
It shows how analytics engineering can support regional planning, population trend analysis, and policy-oriented reporting.

## 📌 Project Overview

Uzbekistan's official statistics are published as **static PDFs** — not reusable, not testable, not analytics-ready.

This project transforms raw SDMX exports from [siat.stat.uz](https://siat.stat.uz) into a **clean, tested, documented** analytics layer:

- ✅ Conformed dimensions with single metric definitions
- ✅ Audit trail (dataset_id, source traceability)
- ✅ Data quality tests (dbt tests)
- ✅ Repeatable ingestion + transformations
- ✅ Live dashboard for business users

**Region:** Namangan (geo_code `1714%`) · **Period:** 2010–2024

---

## 🏗️ Architecture
```
Raw CSV (SDMX)
   └── Staging          — wide → long format, typed contracts
        └── Intermediate — union all sources, metric join
             └── Dimensions + Facts — star schema
                  └── Marts        — dashboard-ready KPIs
                       └── Streamlit Dashboard
```

![Architecture Diagram](doc/images/demography_diagram.jpg)
![Project Workflow](doc/images/project_workflow.jpg)
![Star Schema](doc/images/star_schema.jpg)

### Data Model

| Layer | Models | Purpose |
|-------|--------|---------|
| **Raw** | `raw.sdmx_data_*` | DuckDB views over CSV files |
| **Staging** | `stg_sdmx_<id>_long` | Wide → Long, contract: `dataset_id, geo_code, year, value` |
| **Intermediate** | `int_demography_atomic` | Union all sources + dim_metric join |
| **Dimensions** | `dim_geo`, `dim_sex`, `dim_settlement_type`, `dim_metric` | Conformed dims |
| **Facts** | `fact_population_yearly`, `fact_demography_flows_yearly` | Stock & flow facts |
| **Marts** | `mart_*` | Dashboard-ready with derived KPIs |

---

## 📊 Metrics Covered (2010–2024)

| Group | Metrics |
|-------|---------|
| **Population (stock)** | total, male, female *(from 2014)*, urban, rural |
| **Births (flow)** | total, girls, boys |
| **Deaths (flow)** | total, female, male |
| **Migration (flow)** | arrivals, departures |
| **Marriages (flow)** | total, urban, rural |
| **Divorces (flow)** | total, urban, rural |

---

## 🔑 Key Design Decisions

**1. Namangan-first, but extensible**  
Add new regions by updating `ingest/manifest.csv` + `geo_override.csv` — no model changes needed.

**2. Missing women flag**  
`population_women` data starts from 2014. `mart_population_split_yearly` marks gaps with `missing_women_flag = 1`.

**3. Reconciliation diffs**  
`sex_diff` and `settlement_diff` columns expose discrepancies between totals and components — flags source definition issues.

**4. Metric dictionary as seed**  
`dataset_id → metric_key, metric_group, sex, settlement_type` mapping lives in `dim_metric.csv` seed — adding a new dataset requires only one CSV row.

## Core models

| Layer | Model | Purpose |
|---|---|---|
| Dimension | dim_geo | Region / district hierarchy |
| Dimension | dim_metric | Standardized metric catalog |
| Fact | fact_population_yearly | Population levels by geography and year |
| Fact | fact_demography_flows_yearly | Births, deaths, migration flows |
| Mart | mart_region_overview_yearly | Dashboard-ready regional KPI summary |
| Mart | mart_births_by_sex_yearly | Birth trend breakdown |
| Mart | mart_population_split_yearly | Population structure analysis |

## Data quality and reliability

This project includes:
- dbt tests for key model integrity
- standardized seed files for metric and geography consistency
- typed staging contracts before mart generation
- 
## Decision use-cases

- Compare long-term population growth across districts
- Track births, deaths, and migration trends over time
- Identify regions with unusual demographic shifts
- Build reporting inputs for policy or planning discussions

## Limitations

- Source data depends on public SDMX export quality
- Geographic mappings may require periodic override maintenance
- Dashboard currently focuses on yearly aggregates rather than monthly granularity
---

## ⚙️ How to Run

### Prerequisites
- Python 3.9+
- dbt-core + dbt-duckdb (`pip install dbt-core dbt-duckdb`)
```bash
# 1. Clone
git clone https://github.com/farrux05-ai/namangan_demography
cd namangan_demography

# 2. Download raw data
python ingest/download.py

# 3. Run dbt pipeline
cd dbt
dbt deps
dbt seed          # load dim_metric, geo_override
dbt run           # run all models
dbt test          # data quality checks

# 4. Export marts for dashboard
python dashboard/export_marts.py

# 5. Launch dashboard
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Project Structure
```
namangan_demography/
├── ingest/
│   ├── manifest.csv          # dataset_id, URL, metric key
│   └── download.py           # fetches raw CSV + writes .meta.json
├── data/raw/siat_stat_uz/    # raw SDMX CSV files
├── dbt/
│   ├── models/
│   │   ├── staging/          # stg_sdmx_*_long.sql
│   │   ├── intermediate/     # int_demography_atomic.sql
│   │   ├── dimensions/       # dim_geo, dim_sex, dim_metric...
│   │   ├── facts/            # fact_population_yearly, fact_demography_flows
│   │   └── marts/            # mart_*.sql
│   ├── seeds/                # dim_metric.csv, geo_override.csv
│   ├── macros/               # bootstrap_raw_views macro
│   └── tests/                # data quality tests
├── dashboard/
│   ├── app.py                # Streamlit app
│   └── data/                 # mart CSV exports
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python + requests | Data ingestion from SDMX API |
| DuckDB | Local analytical warehouse |
| dbt Core + dbt-duckdb | Transformation & testing |
| Streamlit + Altair | Dashboard & visualization |

---

## 👤 Author

**Farruxbek Valijonov** — Analytics Engineer  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://www.linkedin.com/in/farrux-valijonov)
[![GitHub](https://img.shields.io/badge/GitHub-farrux05--ai-black?logo=github)](https://github.com/farrux05-ai)
