from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# =============================================================
#  Projekt: Nocny Termometr Polski
#  Autorska aplikacja analityczna Streamlit
#  Źródło danych: Open-Meteo Historical Weather API
# =============================================================

APP_TITLE = "Nocny Termometr Polski"
APP_SUBTITLE = "Czy w polskich miastach trudniejsze robią się dni, czy noce?"
API_URL = "https://archive-api.open-meteo.com/v1/archive"
DATA_START = date(2019, 1, 1)
DATA_END = date(2024, 12, 31)

CITY_META: Dict[str, Dict[str, float]] = {
    "Warszawa": {"lat": 52.2297, "lon": 21.0122},
    "Kraków": {"lat": 50.0647, "lon": 19.9450},
    "Łódź": {"lat": 51.7592, "lon": 19.4560},
    "Wrocław": {"lat": 51.1079, "lon": 17.0385},
    "Poznań": {"lat": 52.4064, "lon": 16.9252},
    "Gdańsk": {"lat": 54.3520, "lon": 18.6466},
    "Szczecin": {"lat": 53.4285, "lon": 14.5528},
    "Lublin": {"lat": 51.2465, "lon": 22.5684},
    "Białystok": {"lat": 53.1325, "lon": 23.1688},
    "Rzeszów": {"lat": 50.0413, "lon": 21.9990},
    "Katowice": {"lat": 50.2649, "lon": 19.0238},
    "Toruń": {"lat": 53.0138, "lon": 18.5984},
}

WEATHER_LABELS = {
    0: "bezchmurnie",
    1: "głównie bezchmurnie",
    2: "częściowe zachmurzenie",
    3: "pochmurno",
    45: "mgła",
    48: "osadzająca się mgła",
    51: "lekka mżawka",
    53: "mżawka",
    55: "silna mżawka",
    61: "lekki deszcz",
    63: "deszcz",
    65: "silny deszcz",
    71: "lekki śnieg",
    73: "śnieg",
    75: "silny śnieg",
    80: "przelotny deszcz",
    81: "mocny przelotny deszcz",
    82: "gwałtowny przelotny deszcz",
    95: "burza",
    96: "burza z gradem",
    99: "silna burza z gradem",
}

MONTHS_PL = {
    1: "sty", 2: "lut", 3: "mar", 4: "kwi", 5: "maj", 6: "cze",
    7: "lip", 8: "sie", 9: "wrz", 10: "paź", 11: "lis", 12: "gru",
}

SEASON_PL = {
    12: "zima", 1: "zima", 2: "zima",
    3: "wiosna", 4: "wiosna", 5: "wiosna",
    6: "lato", 7: "lato", 8: "lato",
    9: "jesień", 10: "jesień", 11: "jesień",
}

NUMERIC_COLS = [
    "tmax", "tmean", "tmin", "apparent_max", "apparent_min",
    "precipitation", "precipitation_hours", "sunshine_duration", "wind_max",
]


def format_number(value: float, suffix: str = "", decimals: int = 1) -> str:
    if pd.isna(value):
        return "brak danych"
    text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return f"{text}{suffix}"


def season_order() -> list[str]:
    return ["zima", "wiosna", "lato", "jesień"]


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(28,43,67,0.92), rgba(20,24,36,0.92));
        border: 1px solid rgba(255,255,255,0.08);
        padding: 14px 16px;
        border-radius: 18px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.18);
    }
    .story-card {
        padding: 18px 20px;
        border-radius: 20px;
        background: rgba(127, 90, 240, 0.08);
        border: 1px solid rgba(127, 90, 240, 0.20);
    }
    .small-muted {opacity: .72; font-size: 0.92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_city_weather(city: str, lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_mean",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "precipitation_sum",
            "precipitation_hours",
            "sunshine_duration",
            "wind_speed_10m_max",
        ]),
        "timezone": "Europe/Warsaw",
    }
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily", {})
    if not daily or "time" not in daily:
        raise ValueError(f"API nie zwróciło dziennych danych dla miasta: {city}")

    df = pd.DataFrame(daily)
    df["city"] = city
    df["lat"] = lat
    df["lon"] = lon
    return df


@st.cache_data(ttl=24 * 3600, show_spinner="Pobieram i czyszczę dane pogodowe…")
def load_raw_data(cities: Tuple[str, ...], start: str, end: str) -> pd.DataFrame:
    frames = []
    for city in cities:
        meta = CITY_META[city]
        frames.append(fetch_city_weather(city, meta["lat"], meta["lon"], start, end))
    return pd.concat(frames, ignore_index=True)


def prepare_data(raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = raw.copy()
    df = df.rename(columns={
        "time": "date",
        "temperature_2m_max": "tmax",
        "temperature_2m_mean": "tmean",
        "temperature_2m_min": "tmin",
        "apparent_temperature_max": "apparent_max",
        "apparent_temperature_min": "apparent_min",
        "precipitation_sum": "precipitation",
        "wind_speed_10m_max": "wind_max",
    })

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "city"])
    df = df.drop_duplicates(subset=["city", "date"], keep="first")

    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["weather_code"] = pd.to_numeric(df["weather_code"], errors="coerce").astype("Int64")

    missing_before = df[NUMERIC_COLS].isna().sum().rename("braki_przed")

    # Interpolacja w obrębie miasta: zachowuje lokalny kontekst i nie wymyśla całych serii od zera.
    df = df.sort_values(["city", "date"])
    df[NUMERIC_COLS] = (
        df.groupby("city", group_keys=False)[NUMERIC_COLS]
        .apply(lambda group: group.interpolate(method="linear", limit_direction="both"))
    )
    missing_after = df[NUMERIC_COLS].isna().sum().rename("braki_po")

    cleaning_report = pd.concat([missing_before, missing_after], axis=1).reset_index(names="kolumna")
    cleaning_report["uzupelniono"] = cleaning_report["braki_przed"] - cleaning_report["braki_po"]

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["month"].map(MONTHS_PL)
    df["day_of_year"] = df["date"].dt.dayofyear
    df["season"] = df["month"].map(SEASON_PL)
    df["weather_label"] = df["weather_code"].map(WEATHER_LABELS).fillna("inny kod")
    df["sunshine_hours"] = df["sunshine_duration"] / 3600
    df["daily_amplitude"] = df["tmax"] - df["tmin"]

    df["heat_day"] = (df["tmax"] >= 30).astype(int)
    df["summer_day"] = (df["tmax"] >= 25).astype(int)
    df["tropical_night"] = (df["tmin"] >= 20).astype(int)
    df["frost_night"] = (df["tmin"] < 0).astype(int)
    df["heavy_rain_day"] = (df["precipitation"] >= 10).astype(int)
    df["dry_day"] = (df["precipitation"] < 1).astype(int)

    # Własny indeks: największą wagę ma noc, bo brak ochłodzenia gorzej wpływa na regenerację.
    df["night_penalty"] = np.maximum(0, df["tmin"] - 17) * 1.8
    df["day_penalty"] = np.maximum(0, df["tmax"] - 27) * 1.1
    df["humidity_proxy"] = np.where(df["precipitation"] > 0, 0.6, 0.0)
    df["urban_heat_stress"] = (df["night_penalty"] + df["day_penalty"] + df["humidity_proxy"]).round(2)

    # Anomalia względem średniego miesiąca dla danego miasta w całym zbiorze.
    monthly_norm = (
        df.groupby(["city", "month"], as_index=False)["tmean"]
        .mean()
        .rename(columns={"tmean": "city_month_norm"})
    )
    df = df.merge(monthly_norm, on=["city", "month"], how="left")
    df["temp_anomaly"] = df["tmean"] - df["city_month_norm"]

    return df, cleaning_report


def city_story(df: pd.DataFrame) -> str:
    by_city = (
        df.groupby("city", as_index=False)
        .agg(
            stress=("urban_heat_stress", "mean"),
            tropical=("tropical_night", "sum"),
            heat=("heat_day", "sum"),
            rain=("heavy_rain_day", "sum"),
        )
        .sort_values("stress", ascending=False)
    )
    if by_city.empty:
        return "Za mało danych po filtrach, żeby ułożyć interpretację."
    leader = by_city.iloc[0]
    quiet = by_city.iloc[-1]
    return (
        f"W wybranym zakresie najwyższy średni indeks stresu cieplnego ma **{leader['city']}** "
        f"({leader['stress']:.2f}), a najniższy **{quiet['city']}** ({quiet['stress']:.2f}). "
        f"Najbardziej ryzykowne są dni, w których upał nie kończy się wieczorem — dlatego aplikacja "
        f"oddzielnie liczy dni z tmax ≥ 30°C oraz noce z tmin ≥ 20°C."
    )


def aggregate_yearly(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["city", "year"], as_index=False)
        .agg(
            tropical_nights=("tropical_night", "sum"),
            heat_days=("heat_day", "sum"),
            summer_days=("summer_day", "sum"),
            frost_nights=("frost_night", "sum"),
            heavy_rain_days=("heavy_rain_day", "sum"),
            dry_days=("dry_day", "sum"),
            mean_stress=("urban_heat_stress", "mean"),
            mean_tmax=("tmax", "mean"),
            mean_tmin=("tmin", "mean"),
            precipitation_sum=("precipitation", "sum"),
            mean_anomaly=("temp_anomaly", "mean"),
        )
    )


def add_trend_line(fig: go.Figure, data: pd.DataFrame, x_col: str, y_col: str) -> go.Figure:
    clean = data[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 3 or clean[x_col].nunique() < 2:
        return fig
    slope, intercept = np.polyfit(clean[x_col], clean[y_col], 1)
    x_vals = np.linspace(clean[x_col].min(), clean[x_col].max(), 100)
    y_vals = slope * x_vals + intercept
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            name="trend ogólny",
            line=dict(width=3, dash="dash"),
            hovertemplate="trend: %{y:.1f}<extra></extra>",
        )
    )
    return fig


# ------------------------------
# Sidebar
# ------------------------------
st.sidebar.title("🌙 Panel sterowania")
st.sidebar.caption("Filtry zmieniają wszystkie KPI, tabele i wykresy.")

all_cities = list(CITY_META.keys())
city_choice = st.sidebar.multiselect(
    "Miasta",
    options=all_cities,
    default=["Warszawa", "Kraków", "Wrocław", "Gdańsk", "Lublin", "Białystok"],
)
if not city_choice:
    st.sidebar.warning("Zaznacz przynajmniej jedno miasto.")
    st.stop()

selected_range = st.sidebar.date_input(
    "Zakres dat",
    value=(date(2021, 1, 1), DATA_END),
    min_value=DATA_START,
    max_value=DATA_END,
)
if isinstance(selected_range, tuple) and len(selected_range) == 2:
    date_from, date_to = selected_range
else:
    date_from, date_to = date(2021, 1, 1), DATA_END
if date_from > date_to:
    st.sidebar.error("Data początkowa nie może być późniejsza niż końcowa.")
    st.stop()

metric_mode = st.sidebar.selectbox(
    "Główna metryka",
    [
        "Indeks stresu cieplnego",
        "Noce tropikalne",
        "Dni upalne",
        "Suma opadów",
        "Anomalia temperatury",
    ],
)
min_temp = st.sidebar.slider("Pokaż dni z tmax od", -15, 40, 0, step=1, help="Próg działa jak filtr jakości/zakresu obserwacji.")
season_filter = st.sidebar.multiselect("Pory roku", options=season_order(), default=season_order())
show_raw = st.sidebar.checkbox("Pokaż surową tabelę", value=False)

# ------------------------------
# Load + prepare
# ------------------------------
try:
    raw_weather = load_raw_data(tuple(all_cities), DATA_START.isoformat(), DATA_END.isoformat())
    weather, cleaning = prepare_data(raw_weather)
except Exception as exc:
    st.error("Nie udało się pobrać danych z Open-Meteo. Sprawdź połączenie aplikacji z internetem i spróbuj ponownie.")
    st.exception(exc)
    st.stop()

filtered = weather[
    (weather["city"].isin(city_choice))
    & (weather["date"].dt.date >= date_from)
    & (weather["date"].dt.date <= date_to)
    & (weather["tmax"] >= min_temp)
    & (weather["season"].isin(season_filter))
].copy()

if filtered.empty:
    st.warning("Po filtrach nie zostały żadne obserwacje. Poluzuj zakres dat, miast albo próg temperatury.")
    st.stop()

yearly = aggregate_yearly(filtered)

metric_lookup = {
    "Indeks stresu cieplnego": ("mean_stress", "Średni indeks stresu cieplnego"),
    "Noce tropikalne": ("tropical_nights", "Liczba nocy tropikalnych"),
    "Dni upalne": ("heat_days", "Liczba dni upalnych"),
    "Suma opadów": ("precipitation_sum", "Suma opadów [mm]"),
    "Anomalia temperatury": ("mean_anomaly", "Średnia anomalia temperatury [°C]"),
}
y_metric, y_label = metric_lookup[metric_mode]

# ------------------------------
# Header + KPI
# ------------------------------
st.title(f"{APP_TITLE} 🌙")
st.subheader(APP_SUBTITLE)

st.markdown(
    """
    <div class="story-card">
    Aplikacja analizuje rzeczywiste dane historyczne dla polskich miast i sprawdza, czy problemem jest tylko upalne popołudnie,
    czy także noc bez ochłodzenia. Własny indeks <b>urban_heat_stress</b> większą wagę przypisuje minimalnej temperaturze nocnej,
    bo właśnie ona pokazuje, czy organizm i miasto miały kiedy odpocząć.
    </div>
    """,
    unsafe_allow_html=True,
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Obserwacje po filtrach", f"{len(filtered):,}".replace(",", " "))
with kpi2:
    st.metric("Średni indeks stresu", format_number(filtered["urban_heat_stress"].mean(), decimals=2))
with kpi3:
    st.metric("Noce tropikalne", int(filtered["tropical_night"].sum()))
with kpi4:
    st.metric("Dni upalne", int(filtered["heat_day"].sum()))

st.info(city_story(filtered))

# ------------------------------
# Tabs
# ------------------------------
tab_overview, tab_heat, tab_rain, tab_map, tab_quality = st.tabs([
    "1. Trendy i ranking",
    "2. Noc vs dzień",
    "3. Opady i kontrasty",
    "4. Mapa i wkład miast",
    "5. Dane, czyszczenie, wnioski",
])

with tab_overview:
    st.markdown("### Trend roczny wybranej metryki")
    fig_line = px.line(
        yearly,
        x="year",
        y=y_metric,
        color="city",
        markers=True,
        labels={"year": "Rok", y_metric: y_label, "city": "Miasto"},
        title=f"Zmiana w latach: {y_label}",
    )
    fig_line.update_layout(legend_title_text="Miasto", hovermode="x unified")
    st.plotly_chart(fig_line, use_container_width=True)

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("### Ranking miast")
        city_rank = (
            filtered.groupby("city", as_index=False)
            .agg(
                indeks=("urban_heat_stress", "mean"),
                noce_tropikalne=("tropical_night", "sum"),
                dni_upalne=("heat_day", "sum"),
                opad_mm=("precipitation", "sum"),
                anomalia=("temp_anomaly", "mean"),
            )
            .sort_values("indeks", ascending=False)
        )
        fig_bar = px.bar(
            city_rank,
            x="city",
            y="indeks",
            hover_data=["noce_tropikalne", "dni_upalne", "opad_mm", "anomalia"],
            labels={"city": "Miasto", "indeks": "Średni indeks stresu"},
            title="Bar chart: które miasto najbardziej się przegrzewa?",
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    with right:
        st.markdown("### Najważniejsze liczby")
        display = city_rank.rename(columns={
            "city": "miasto",
            "indeks": "średni_indeks",
            "opad_mm": "opad_mm_suma",
        })
        st.dataframe(
            display.style.format({
                "średni_indeks": "{:.2f}",
                "opad_mm_suma": "{:.0f}",
                "anomalia": "{:.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

with tab_heat:
    st.markdown("### Heatmapa: gdzie i kiedy stres cieplny kumuluje się najmocniej?")
    heat_city = st.selectbox("Miasto do heatmapy", options=city_choice, index=0)
    heat_data = filtered[filtered["city"] == heat_city]
    pivot = (
        heat_data.groupby(["year", "month"], as_index=False)["urban_heat_stress"]
        .mean()
        .pivot(index="year", columns="month", values="urban_heat_stress")
        .reindex(columns=list(range(1, 13)))
    )
    fig_heat = px.imshow(
        pivot,
        labels=dict(x="Miesiąc", y="Rok", color="Średni indeks"),
        x=[MONTHS_PL[m] for m in pivot.columns],
        y=pivot.index.astype(str),
        aspect="auto",
        title=f"Heatmap: miesięczny indeks stresu cieplnego — {heat_city}",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Boxplot: rozkład temperatur nocnych")
        box_data = filtered.copy()
        box_data["month_label"] = box_data["month"].map(MONTHS_PL)
        fig_box = px.box(
            box_data,
            x="month_label",
            y="tmin",
            color="city",
            points="outliers",
            labels={"month_label": "Miesiąc", "tmin": "Temperatura minimalna [°C]", "city": "Miasto"},
            category_orders={"month_label": [MONTHS_PL[m] for m in range(1, 13)]},
            title="Boxplot: nocne minima według miesięcy",
        )
        st.plotly_chart(fig_box, use_container_width=True)
    with c2:
        st.markdown("### Scatter: dzień kontra noc")
        sample = filtered.sample(min(len(filtered), 3500), random_state=42)
        fig_scatter = px.scatter(
            sample,
            x="tmax",
            y="tmin",
            color="city",
            size=np.maximum(sample["urban_heat_stress"], 0.1),
            hover_data=["date", "precipitation", "sunshine_hours"],
            labels={
                "tmax": "Temperatura maksymalna [°C]",
                "tmin": "Temperatura minimalna [°C]",
                "city": "Miasto",
                "size": "Indeks",
            },
            title="Scatter: czy gorące dni zostawiają ciepłe noce?",
        )
        fig_scatter.add_hline(y=20, line_dash="dot", annotation_text="noc tropikalna: 20°C")
        fig_scatter.add_vline(x=30, line_dash="dot", annotation_text="dzień upalny: 30°C")
        fig_scatter = add_trend_line(fig_scatter, sample, "tmax", "tmin")
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab_rain:
    st.markdown("### Opady, susza i amplituda dobowa")
    rain_yearly = (
        filtered.groupby(["city", "year"], as_index=False)
        .agg(
            opad=("precipitation", "sum"),
            ulewne=("heavy_rain_day", "sum"),
            suche=("dry_day", "sum"),
            amplituda=("daily_amplitude", "mean"),
        )
    )
    left, right = st.columns(2)
    with left:
        fig_rain = px.area(
            rain_yearly,
            x="year",
            y="opad",
            color="city",
            labels={"year": "Rok", "opad": "Suma opadów [mm]", "city": "Miasto"},
            title="Area chart: suma opadów według roku",
        )
        st.plotly_chart(fig_rain, use_container_width=True)
    with right:
        fig_amp = px.scatter(
            rain_yearly,
            x="suche",
            y="amplituda",
            color="city",
            size="ulewne",
            hover_data=["year", "opad"],
            labels={
                "suche": "Liczba suchych dni",
                "amplituda": "Średnia amplituda dobowa [°C]",
                "ulewne": "Dni z opadem ≥ 10 mm",
                "city": "Miasto",
            },
            title="Scatter: suche dni a amplituda temperatur",
        )
        fig_amp = add_trend_line(fig_amp, rain_yearly, "suche", "amplituda")
        st.plotly_chart(fig_amp, use_container_width=True)

    st.markdown("### Miesięczny profil zjawisk")
    monthly_profile = (
        filtered.groupby(["month", "month_name"], as_index=False)
        .agg(
            dni_upalne=("heat_day", "sum"),
            noce_tropikalne=("tropical_night", "sum"),
            dni_ulewne=("heavy_rain_day", "sum"),
            dni_suche=("dry_day", "sum"),
        )
        .sort_values("month")
    )
    melted = monthly_profile.melt(
        id_vars=["month", "month_name"],
        value_vars=["dni_upalne", "noce_tropikalne", "dni_ulewne", "dni_suche"],
        var_name="zjawisko",
        value_name="liczba_dni",
    )
    fig_group = px.bar(
        melted,
        x="month_name",
        y="liczba_dni",
        color="zjawisko",
        barmode="group",
        category_orders={"month_name": [MONTHS_PL[m] for m in range(1, 13)]},
        labels={"month_name": "Miesiąc", "liczba_dni": "Liczba obserwacji", "zjawisko": "Zjawisko"},
        title="Grouped bar: sezonowość zjawisk ekstremalnych",
    )
    st.plotly_chart(fig_group, use_container_width=True)

with tab_map:
    st.markdown("### Mapa: przestrzenny obraz stresu cieplnego")
    map_df = (
        filtered.groupby(["city", "lat", "lon"], as_index=False)
        .agg(
            mean_stress=("urban_heat_stress", "mean"),
            tropical_nights=("tropical_night", "sum"),
            heat_days=("heat_day", "sum"),
            precipitation_sum=("precipitation", "sum"),
            temp_anomaly=("temp_anomaly", "mean"),
        )
    )
    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        size="tropical_nights",
        color="mean_stress",
        hover_name="city",
        hover_data={
            "lat": False,
            "lon": False,
            "mean_stress": ":.2f",
            "tropical_nights": True,
            "heat_days": True,
            "precipitation_sum": ":.0f",
            "temp_anomaly": ":.2f",
        },
        zoom=4.7,
        center={"lat": 52.0, "lon": 19.2},
        height=560,
        mapbox_style="carto-positron",
        labels={"mean_stress": "Średni indeks", "tropical_nights": "Noce tropikalne"},
        title="Mapa: rozmiar = liczba nocy tropikalnych, kolor = średni indeks stresu",
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("### Treemap: kto buduje łączny stres cieplny?")
    tree_df = (
        filtered.groupby(["season", "city"], as_index=False)
        .agg(total_stress=("urban_heat_stress", "sum"), days=("date", "count"))
    )
    tree_df["season"] = pd.Categorical(tree_df["season"], categories=season_order(), ordered=True)
    fig_tree = px.treemap(
        tree_df,
        path=["season", "city"],
        values="total_stress",
        color="total_stress",
        hover_data=["days"],
        title="Treemap: udział pór roku i miast w sumie indeksu stresu",
    )
    st.plotly_chart(fig_tree, use_container_width=True)

with tab_quality:
    st.markdown("### Co zostało zrobione z danymi")
    st.write(
        "Dane przychodzą z API jako dzienne serie dla współrzędnych miast. Aplikacja wykonuje: "
        "konwersję typów, usuwanie duplikatów miasto–data, kontrolę braków, interpolację krótkich luk w obrębie miasta "
        "oraz obliczenie kolumn pochodnych: pory roku, noce tropikalne, dni upalne, opady intensywne, dni suche, "
        "anomalia miesięczna i autorski indeks stresu cieplnego."
    )
    st.dataframe(cleaning, use_container_width=True, hide_index=True)

    st.markdown("### Interpretacja automatyczna")
    top_city = (
        filtered.groupby("city", as_index=False)["urban_heat_stress"].mean()
        .sort_values("urban_heat_stress", ascending=False)
        .iloc[0]
    )
    night_share = filtered["tropical_night"].sum() / max(filtered["heat_day"].sum(), 1)
    rainy_share = filtered["heavy_rain_day"].sum() / max(len(filtered), 1) * 100
    st.markdown(
        f"- Najwyższy średni indeks stresu ma **{top_city['city']}**: "
        f"{top_city['urban_heat_stress']:.2f}.\n"
        f"- Relacja nocy tropikalnych do dni upalnych wynosi **{night_share:.2f}**. "
        f"Im bliżej 1, tym częściej upał nie kończy się wraz z zachodem słońca.\n"
        f"- Dni z opadem co najmniej 10 mm stanowią **{rainy_share:.1f}%** przefiltrowanych obserwacji."
    )

    st.markdown("### Źródło i ograniczenia")
    st.write(
        "Źródło: Open-Meteo Historical Weather API. Dane są reanalizą pogody dla współrzędnych, "
        "więc nie są tym samym co pomiar dokładnie na konkretnej ulicy. Porównania miejskie należy traktować jako "
        "analityczne przybliżenie, a nie oficjalny ranking meteorologiczny."
    )

    if show_raw:
        st.markdown("### Tabela robocza")
        st.dataframe(filtered.sort_values(["date", "city"]), use_container_width=True, hide_index=True)

st.caption(
    "Projekt zaliczeniowy Streamlit · dane rzeczywiste · czyszczenie + EDA + min. 5 typów wykresów + filtry + cache"
)
