# export_marts.py
# Bu faylni dbt loyihangiz papkasida (dev.duckdb bor joyda) ishga tushiring
#
# pip install duckdb pandas
# python3 export_marts.py

import duckdb
import pandas as pd
import os

DB_PATH = "dev.duckdb"  # dev.duckdb shu papkada bo'lishi kerak
OUT_DIR = "dashboard/data"  # CSV lar shu yerga tushadi

os.makedirs(OUT_DIR, exist_ok=True)

con = duckdb.connect(DB_PATH, read_only=True)

martlar = [
    "mart_region_overview_yearly",
    "mart_population_split_yearly",
    "mart_births_by_sex_yearly",
    "mart_metric_coverage",
]

for mart in martlar:
    try:
        df = con.execute(f"SELECT * FROM {mart}").df()
        path = os.path.join(OUT_DIR, f"{mart}.csv")
        df.to_csv(path, index=False)
        print(f" {mart}.csv — {len(df)} qator → {path}")
    except Exception as e:
        print(f" {mart}: {e}")

con.close()
print(f"\nTayyor! Endi repoga push qiling:")
print(f"   git add dashboard/data/ dashboard/app.py")
print(f"   git commit -m 'feat: CSV based dashboard'")
print(f"   git push")