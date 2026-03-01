# dashboard/app.py
import os
import duckdb
import pandas as pd
import streamlit as st
import altair as alt

# ----------------------------
# Streamlit sozlamalari (mobilga mos)
# ----------------------------
st.set_page_config(
    page_title="Demografiya dashboardi (AE)",
    page_icon="📊",
    layout="centered",
)

st.title("📊 Demografiya dashboardi (AE loyihasi)")

# ----------------------------
# Agar sizning mart table nomlaringiz boshqacha bo'lsa shu yerda almashtiring
# ----------------------------
TABLES = {
    "overview": "mart_region_overview_yearly",
    "pop_split": "mart_population_split_yearly",
    "birth_sex": "mart_births_by_sex_yearly",
    "coverage": "mart_metric_coverage",  # ixtiyoriy
}

# ----------------------------
# Helper funksiyalar
# ----------------------------
@st.cache_resource
def get_conn(db_path: str):
    return duckdb.connect(db_path, read_only=True)

def table_exists(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    try:
        con.execute(f"select 1 from {table_name} limit 1")
        return True
    except Exception:
        return False

@st.cache_data
def load_df(db_path: str, sql: str) -> pd.DataFrame:
    con = get_conn(db_path)
    return con.execute(sql).df()

def safe_prefix(prefix: str) -> str:
    prefix = (prefix or "").strip()
    return prefix if prefix else "1714"

# ----------------------------
# Sidebar (Filtrlar)
# ----------------------------
with st.sidebar:
    st.header("Filtrlar")

    default_db = os.getenv("DUCKDB_PATH", "dev.duckdb")
    db_path = st.text_input("DuckDB fayl yo‘li", value=default_db)

    region_prefix = st.text_input(
        "Viloyat kodi (prefix)",
        value="1714",
        help="Misol: Namangan = 1714. Boshqa viloyat uchun o‘sha viloyat kodini kiriting."
    )

# ----------------------------
# DB ulanishini tekshirish
# ----------------------------
try:
    con = get_conn(db_path)
except Exception as e:
    st.error(f"DuckDB ochilmadi: `{db_path}`\n\nXato: {e}")
    st.stop()

if not table_exists(con, TABLES["overview"]):
    st.error(
        f"Majburiy jadval topilmadi: `{TABLES['overview']}`.\n\n"
        "dbt bilan martlarni build qiling yoki TABLES mappingni app.py ichida moslang."
    )
    st.stop()

prefix = safe_prefix(region_prefix)

# ----------------------------
# Overview martni yuklash
# ----------------------------
df_overview = load_df(
    db_path,
    f"""
    select *
    from {TABLES["overview"]}
    where cast(geo_code as varchar) like '{prefix}%'
    order by year, geo_code
    """
)

if df_overview.empty:
    st.warning("Bu prefix bo‘yicha ma’lumot topilmadi. Viloyat kodini tekshiring.")
    st.stop()

# Year range slider
min_year, max_year = int(df_overview["year"].min()), int(df_overview["year"].max())
with st.sidebar:
    year_range = st.slider("Yillar oralig‘i", min_year, max_year, (min_year, max_year))

df_overview = df_overview[(df_overview["year"] >= year_range[0]) & (df_overview["year"] <= year_range[1])]

# Geo tanlash
geo_df = (
    df_overview[["geo_code", "geo_name"]]
    .drop_duplicates()
    .sort_values(["geo_name", "geo_code"])
)

geo_map = {int(r.geo_code): f"{r.geo_name} ({int(r.geo_code)})" for r in geo_df.itertuples(index=False)}

with st.sidebar:
    selected_geo = st.selectbox(
        "Hudud (tuman/shahar/viloyat)",
        options=list(geo_map.keys()),
        format_func=lambda x: geo_map[x],
    )

df_geo = df_overview[df_overview["geo_code"] == selected_geo].copy()
latest_year = int(df_geo["year"].max())
latest = df_geo[df_geo["year"] == latest_year].iloc[0]

# ----------------------------
# Tablar
# ----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Umumiy ko‘rinish", "Tumanlar reytingi", "Aholi tarkibi", "Sifat va qamrov"])

# =========================================================
# TAB 1: Umumiy ko‘rinish
# =========================================================
with tab1:
    st.subheader("Umumiy ko‘rinish (KPI + trend)")

    # KPI kartalar
    c1, c2, c3 = st.columns(3)
    c1.metric("Aholi soni", f"{int(latest['population_total']):,}")
    c2.metric("Tug‘ilishlar", f"{int(latest['birth_total']):,}")
    c3.metric("Vafot etganlar", f"{int(latest['death_total']):,}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Tabiiy o‘sish", f"{int(latest['natural_increase']):,}")
    c5.metric("Sof migratsiya", f"{int(latest['net_migration']):,}")
    c6.metric("Tug‘ilish koeff. (‰)", f"{float(latest['cbr_per_1000']):.2f}")

    st.divider()
    st.markdown("### Trend (yillar bo‘yicha)")

    trend_cols = [c for c in ["birth_total", "death_total", "net_migration"] if c in df_geo.columns]
    trend = df_geo[["year"] + trend_cols].melt("year", var_name="ko‘rsatkich", value_name="qiymat")

    chart = (
        alt.Chart(trend)
        .mark_line(point=True)
        .encode(
            x=alt.X("year:O", title="Yil"),
            y=alt.Y("qiymat:Q", title="Qiymat"),
            color=alt.Color("ko‘rsatkich:N", title="Ko‘rsatkich"),
            tooltip=["year", "ko‘rsatkich", "qiymat"],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, width="stretch")

    st.markdown("#### Nimani ko‘ryapmiz?")
    st.write(
        "- Tug‘ilish va o‘lim farqi **tabiiy o‘sish**ni beradi.\n"
        "- Ko‘chish balansi (**sof migratsiya**) aholi o‘zgarishini kuchaytiradi yoki sekinlashtiradi."
    )
    st.markdown("#### So what? (Qanday xulosa/qaror?)")
    st.write(
        "- Aholi o‘sishi asosan **tabiiy**mi yoki **migratsiya** hisobidanmi?\n"
        "- Sof migratsiya manfiy bo‘lsa: qaysi yillarda kuchaygan va sabab bo‘lishi mumkin bo‘lgan omillarni (ish/o‘qish/uy-joy) tekshirish kerak."
    )

# =========================================================
# TAB 2: Tumanlar reytingi
# =========================================================
with tab2:
    st.subheader("Tumanlar reytingi (eng so‘nggi yil)")

    year_latest = int(df_overview["year"].max())
    df_latest = df_overview[df_overview["year"] == year_latest].copy()

    cols = [
        "geo_name", "geo_code",
        "population_total",
        "birth_total", "death_total", "natural_increase",
        "in_migration", "out_migration", "net_migration",
        "cbr_per_1000", "cdr_per_1000", "net_mig_per_1000",
        "marriages_total", "divorces_total",
    ]
    cols = [c for c in cols if c in df_latest.columns]

    sort_col = "net_mig_per_1000" if "net_mig_per_1000" in df_latest.columns else "net_migration"
    df_latest = df_latest.sort_values(sort_col, ascending=True)

    st.dataframe(df_latest[cols], width="stretch")

    st.markdown("#### Nimani ko‘ryapmiz?")
    st.write(
        "- Jadval tuman/shaharlar kesimida ko‘rsatkichlarni taqqoslaydi.\n"
        "- Ayniqsa `sof migratsiya (‰)` eng kuchli ‘chiqish/kirish’ signalini beradi."
    )
    st.markdown("#### So what? (Qanday xulosa/qaror?)")
    st.write(
        "- Manfiy sof migratsiya tumanlari: aholi chiqishi sabablari (ish/o‘qish infratuzilma) bo‘yicha chuqur tahlil.\n"
        "- Ijobiy sof migratsiya tumanlari: maktab/poliklinika/uy-joy kabi xizmatlarda yuklama oshishi mumkin."
    )

# =========================================================
# TAB 3: Aholi tarkibi
# =========================================================
with tab3:
    st.subheader("Aholi tarkibi (shahar/qishloq, erkak/ayol)")

    if table_exists(con, TABLES["pop_split"]):
        df_pop = load_df(
            db_path,
            f"""
            select *
            from {TABLES["pop_split"]}
            where cast(geo_code as varchar) like '{prefix}%'
            order by year, geo_code
            """
        )
        df_pop = df_pop[(df_pop["year"] >= year_range[0]) & (df_pop["year"] <= year_range[1])]
        df_pop_geo = df_pop[df_pop["geo_code"] == selected_geo].copy()

        if df_pop_geo.empty:
            st.info("Tanlangan hudud/yillar bo‘yicha population split ma’lumotlari yo‘q.")
        else:
            # Urban vs Rural
            if "population_urban" in df_pop_geo.columns and "population_rural" in df_pop_geo.columns:
                urb = df_pop_geo[["year", "population_urban", "population_rural"]].melt(
                    "year", var_name="segment", value_name="qiymat"
                )
                chart_urb = (
                    alt.Chart(urb)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("year:O", title="Yil"),
                        y=alt.Y("qiymat:Q", title="Aholi soni"),
                        color=alt.Color("segment:N", title="Segment"),
                        tooltip=["year", "segment", "qiymat"],
                    )
                    .properties(height=280, title="Shahar vs Qishloq")
                )
                st.altair_chart(chart_urb, width="stretch")

            # Men vs Women (coverage-dependent)
            sex_cols = [c for c in ["population_men", "population_women"] if c in df_pop_geo.columns]
            if sex_cols:
                sex_df = df_pop_geo[["year"] + sex_cols].melt(
                    "year", var_name="jins", value_name="qiymat"
                )
                chart_sex = (
                    alt.Chart(sex_df)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("year:O", title="Yil"),
                        y=alt.Y("qiymat:Q", title="Aholi soni"),
                        color=alt.Color("jins:N", title="Jins"),
                        tooltip=["year", "jins", "qiymat"],
                    )
                    .properties(height=280, title="Erkak vs Ayol (qamrovga bog‘liq)")
                )
                st.altair_chart(chart_sex, width="stretch")

            if "missing_women_flag" in df_pop_geo.columns and df_pop_geo["missing_women_flag"].sum() > 0:
                st.warning("Ayollar bo‘yicha aholi qatori ayrim yillarda mavjud emas (manba qamrovi).")

        st.markdown("#### Nimani ko‘ryapmiz?")
        st.write(
            "- Shahar/qishloq ulushi urbanizatsiya yo‘nalishini ko‘rsatadi.\n"
            "- Erkak/ayol tarkibi migratsiya va demografik tuzilma bilan bog‘liq bo‘lishi mumkin."
        )
        st.markdown("#### So what? (Qanday xulosa/qaror?)")
        st.write(
            "- Shahar ulushi oshsa: transport, uy-joy, ish o‘rinlari va kommunal yuklama masalalarini ko‘rib chiqish.\n"
            "- Qishloq ulushi yuqori bo‘lsa: xizmatlarni (maktab/tibbiyot) tarqatish xarajati va kirish imkonini tahlil qilish."
        )
    else:
        st.warning(f"Jadval topilmadi: `{TABLES['pop_split']}`. Avval mart_population_split_yearly build qiling.")

# =========================================================
# TAB 4: Sifat va qamrov
# =========================================================
with tab4:
    st.subheader("Sifat va qamrov (coverage + checks)")

    # Coverage jadvali (ixtiyoriy)
    if table_exists(con, TABLES["coverage"]):
        df_cov = load_df(db_path, f"select * from {TABLES['coverage']} order by metric_key, year")
        st.markdown("### Qamrov jadvali (ko‘rsatkich × yil)")
        st.dataframe(df_cov, width="stretch")
    else:
        st.info("Qamrov jadvali (mart_metric_coverage) topilmadi — ixtiyoriy.")

    st.divider()

    # Births by sex (ixtiyoriy)
    if table_exists(con, TABLES["birth_sex"]):
        df_birth = load_df(
            db_path,
            f"""
            select *
            from {TABLES["birth_sex"]}
            where cast(geo_code as varchar) like '{prefix}%'
            order by year, geo_code
            """
        )
        df_birth = df_birth[(df_birth["year"] >= year_range[0]) & (df_birth["year"] <= year_range[1])]
        df_birth_geo = df_birth[df_birth["geo_code"] == selected_geo].copy()

        st.markdown("### Tug‘ilish bo‘yicha tekshiruv (qiz + o‘g‘il ≈ jami)")
        if not df_birth_geo.empty and "sex_diff" in df_birth_geo.columns:
            cols = [c for c in ["year", "total_birth_yearly", "birth_girls", "birth_boys", "sex_diff"] if c in df_birth_geo.columns]
            st.dataframe(df_birth_geo[cols], width="stretch")
        else:
            st.info("Tanlangan hudud/yillar bo‘yicha tug‘ilish (sex split) ma’lumotlari yo‘q.")
    else:
        st.info("Tug‘ilish (sex split) mart jadvali topilmadi — ixtiyoriy.")

    st.markdown("#### Nimani ko‘ryapmiz?")
    st.write(
        "- Qamrov jadvali qaysi metrik qaysi yilda mavjud/yo‘qligini ko‘rsatadi.\n"
        "- `diff` tekshiruvlari (jami = qismlar yig‘indisi) faqat qismlar mavjud bo‘lganda meaningful."
    )
    st.markdown("#### So what? (Qanday xulosa/qaror?)")
    st.write(
        "- KPI va taqqoslashni faqat qamrov to‘liq bo‘lgan davrda qiling.\n"
        "- `diff` katta bo‘lgan yil/hududlarda manba definitsiyasi yoki raw datasetlarni qayta tekshiring."
    )

    st.caption(
        "Eslatma: Ayrim qatorlar (masalan, ayollar bo‘yicha aholi) ma’lum yildan boshlab mavjud bo‘lishi mumkin — bu manba qamrovi."
    )