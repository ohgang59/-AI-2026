# pip install streamlit pandas numpy plotly

"""
우리 동네 폭염 대응 AI

data/ 폴더의 기상청 폭염 영향예보 일자료(.xls 형식의 탭 구분 파일)를 읽어
실제 2025년 5~9월 관측값을 기준으로 지역별 폭염 위험을 시뮬레이션합니다.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_DIR = Path("data")
NUMERIC_COLUMNS = [
    "최고체감온도(°C)",
    "최고기온(°C)",
    "평균기온(°C)",
    "최저기온(°C)",
    "평균상대습도(%)",
]
IMPACT_SCORE = {"": 0, "관심": 1, "주의": 2, "경고": 3, "위험": 4}

STATION_COORDS = {
    "서울": (126.98, 37.57), "인천": (126.63, 37.46), "수원": (127.01, 37.26),
    "동두천": (127.06, 37.90), "파주": (126.78, 37.76), "이천": (127.44, 37.28),
    "양평": (127.49, 37.49), "철원": (127.31, 38.15), "춘천": (127.73, 37.88),
    "원주": (127.95, 37.34), "영월": (128.46, 37.18), "북강릉": (128.89, 37.80),
    "강릉": (128.90, 37.75), "동해": (129.11, 37.52), "속초": (128.59, 38.20),
    "대관령": (128.76, 37.68), "태백": (128.99, 37.16),
    "청주": (127.49, 36.64), "충주": (127.93, 36.99), "제천": (128.19, 37.13),
    "보은": (127.73, 36.49), "추풍령": (128.00, 36.22), "서산": (126.45, 36.78),
    "천안": (127.15, 36.81), "보령": (126.61, 36.33), "부여": (126.91, 36.28),
    "금산": (127.49, 36.11), "홍성": (126.66, 36.60), "대전": (127.38, 36.35),
    "세종": (127.29, 36.48),
    "전주": (127.15, 35.82), "군산": (126.71, 35.97), "정읍": (126.86, 35.57),
    "남원": (127.39, 35.41), "임실": (127.28, 35.61), "장수": (127.52, 35.65),
    "고창": (126.70, 35.43), "순창": (127.14, 35.37), "완주": (127.16, 35.90),
    "익산": (126.96, 35.95), "광주": (126.85, 35.16), "경기광주": (127.25, 37.41),
    "목포": (126.39, 34.81), "여수": (127.66, 34.76), "순천": (127.49, 34.95),
    "순천시": (127.49, 34.95), "광양읍": (127.58, 34.98), "고흥": (127.29, 34.61),
    "보성": (127.08, 34.77), "장흥": (126.91, 34.68), "해남": (126.60, 34.57),
    "완도": (126.75, 34.31), "진도": (126.26, 34.48), "흑산도": (125.43, 34.68),
    "영광": (126.51, 35.28), "장성": (126.78, 35.30), "강진군": (126.77, 34.64),
    "영암": (126.70, 34.80), "무안": (126.48, 34.99), "함평": (126.52, 35.07),
    "담양": (126.99, 35.32), "곡성": (127.29, 35.28), "구례": (127.46, 35.20),
    "화순": (126.99, 35.06),
    "대구": (128.60, 35.87), "안동": (128.73, 36.57), "포항": (129.37, 36.03),
    "울진": (129.40, 36.99), "영주": (128.62, 36.81), "문경": (128.19, 36.59),
    "상주": (128.16, 36.41), "구미": (128.34, 36.12), "영천": (128.94, 35.97),
    "경주시": (129.22, 35.86), "의성": (128.70, 36.35), "청송군": (129.06, 36.44),
    "영덕": (129.37, 36.42), "봉화": (128.73, 36.89), "군위": (128.57, 36.24),
    "칠곡": (128.40, 35.99), "김천": (128.12, 36.14), "성주": (128.28, 35.92),
    "고령": (128.27, 35.73), "부산": (129.08, 35.18), "울산": (129.31, 35.54),
    "창원": (128.68, 35.23), "김해시": (128.89, 35.23), "양산시": (129.04, 35.34),
    "밀양": (128.75, 35.50), "창녕": (128.49, 35.54), "함안": (128.41, 35.27),
    "합천": (128.17, 35.57), "거창": (127.91, 35.69), "함양": (127.73, 35.52),
    "산청": (127.87, 35.42), "진주": (128.08, 35.18), "통영": (128.43, 34.85),
    "거제": (128.62, 34.88), "남해": (127.89, 34.84), "제주": (126.53, 33.50),
    "고산": (126.16, 33.29), "성산": (126.91, 33.46), "서귀포": (126.56, 33.25),
}


st.set_page_config(
    page_title="우리 동네 폭염 대응 AI",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_html(markup: str) -> None:
    html = dedent(markup).strip()
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def inject_css() -> None:
    render_html(
        """
        <style>
        :root {
            --ink: #2f3440;
            --muted: #728094;
            --line: rgba(120, 144, 168, 0.18);
            --blue: #7bb7f0;
            --green: #87d6b5;
            --orange: #ffc08a;
            --red: #ff8fa3;
            --panel: rgba(255, 255, 255, 0.78);
        }

        html, body, [class*="css"] {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 5%, rgba(255, 192, 203, 0.30), transparent 30%),
                radial-gradient(circle at 90% 12%, rgba(137, 207, 240, 0.30), transparent 32%),
                linear-gradient(180deg, #fff9fb 0%, #f2fbff 50%, #fff7ee 100%);
            color: var(--ink);
        }

        section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.76);
            border-right: 1px solid var(--line);
            backdrop-filter: blur(18px);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1480px;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 1rem;
        }

        .hero {
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.94);
            border-radius: 18px;
            padding: 30px 34px;
            color: #2f3440;
            background:
                linear-gradient(135deg, rgba(255, 244, 248, 0.96), rgba(229, 246, 255, 0.92) 55%, rgba(255, 243, 225, 0.95)),
                radial-gradient(circle at 78% 20%, rgba(255, 143, 163, 0.22), transparent 28%);
            box-shadow: 0 24px 54px rgba(126, 154, 180, 0.18);
        }

        .hero-inner {
            display: grid;
            grid-template-columns: minmax(0, 1.65fr) minmax(260px, 0.75fr);
            gap: 24px;
            align-items: end;
        }

        .hero-badge,
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 10px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 850;
            border: 1px solid rgba(255, 255, 255, 0.70);
        }

        .hero-badge {
            background: rgba(255, 255, 255, 0.68);
            color: #536277;
            margin-bottom: 15px;
        }

        .hero h1 {
            margin: 0;
            font-size: clamp(2.2rem, 4.5vw, 4.55rem);
            line-height: 1.03;
            letter-spacing: 0;
            font-weight: 950;
        }

        .hero p {
            max-width: 840px;
            margin: 16px 0 0;
            font-size: clamp(1rem, 1.5vw, 1.25rem);
            line-height: 1.62;
            color: #5b6575;
            font-weight: 600;
        }

        .hero-mini {
            border-radius: 14px;
            padding: 18px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.84);
            backdrop-filter: blur(12px);
        }

        .hero-mini .label {
            font-size: 0.86rem;
            color: #728094;
            font-weight: 800;
        }

        .hero-mini .value {
            margin-top: 8px;
            font-size: 2.6rem;
            font-weight: 950;
            line-height: 1;
        }

        .notice,
        .data-strip,
        .glass-card,
        .metric-card,
        .region-card,
        .concept-card,
        .plan-item,
        .decision-card {
            border-radius: 12px;
            background: var(--panel);
            border: 1px solid rgba(255,255,255,0.96);
            box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08);
        }

        .notice {
            margin-top: 12px;
            padding: 12px 15px;
            color: #475569;
            font-size: 0.92rem;
            line-height: 1.55;
        }

        .data-strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1px;
            overflow: hidden;
        }

        .data-cell {
            padding: 16px;
            background: rgba(255,255,255,0.62);
        }

        .data-cell small {
            display: block;
            color: var(--muted);
            font-weight: 800;
            margin-bottom: 6px;
        }

        .data-cell strong {
            font-size: 1.35rem;
            color: var(--ink);
            font-weight: 950;
        }

        .section-title {
            display: flex;
            align-items: center;
            gap: 9px;
            margin: 7px 0 1px;
            font-size: 1.35rem;
            font-weight: 950;
            color: var(--ink);
        }

        .section-title span {
            width: 9px;
            height: 26px;
            border-radius: 4px;
            background: linear-gradient(180deg, #8ecdf7, #91d9bf, #ffc08a);
        }

        .glass-card {
            height: 100%;
            padding: 20px;
        }

        .metric-card {
            min-height: 166px;
            padding: 18px;
            transition: transform 160ms ease, box-shadow 160ms ease;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 44px rgba(15, 23, 42, 0.13);
        }

        .metric-top,
        .region-name {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }

        .metric-icon {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 10px;
            background: rgba(142, 205, 247, 0.22);
            font-size: 1.45rem;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.9rem;
            font-weight: 850;
        }

        .metric-value {
            margin-top: 15px;
            font-size: clamp(1.8rem, 2.7vw, 2.55rem);
            line-height: 1;
            font-weight: 950;
            color: var(--ink);
        }

        .metric-unit {
            margin-left: 3px;
            font-size: 1rem;
            color: var(--muted);
            font-weight: 850;
        }

        .metric-desc {
            margin-top: 11px;
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.45;
            font-weight: 560;
        }

        .badge-low { background: rgba(135, 214, 181, 0.28); color: #25765f; border-color: rgba(135,214,181,0.42); }
        .badge-mid { background: rgba(123, 183, 240, 0.25); color: #356c9d; border-color: rgba(123,183,240,0.40); }
        .badge-high { background: rgba(255, 192, 138, 0.30); color: #9a6129; border-color: rgba(255,192,138,0.44); }
        .badge-critical { background: rgba(255, 143, 163, 0.26); color: #a64157; border-color: rgba(255,143,163,0.40); }

        .region-card {
            padding: 15px;
            min-height: 132px;
        }

        .region-card.selected {
            background: linear-gradient(135deg, rgba(255, 226, 233, 0.96), rgba(222, 245, 255, 0.94));
            color: #2f3440;
            box-shadow: 0 18px 42px rgba(126, 154, 180, 0.18);
        }

        .region-name {
            font-size: 1.05rem;
            font-weight: 950;
        }

        .region-stats {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px;
            margin-top: 13px;
        }

        .region-stat {
            padding: 9px;
            border-radius: 9px;
            background: rgba(15, 23, 42, 0.05);
        }

        .selected .region-stat {
            background: rgba(255,255,255,0.16);
        }

        .region-stat strong {
            display: block;
            font-size: 1.16rem;
            line-height: 1;
        }

        .region-stat small {
            display: block;
            margin-top: 5px;
            color: var(--muted);
            font-weight: 750;
        }

        .selected .region-stat small {
            color: rgba(255,255,255,0.78);
        }

        .decision-card {
            padding: 22px;
            background: linear-gradient(135deg, rgba(255, 244, 248, 0.96), rgba(234, 248, 255, 0.94));
            color: #2f3440;
        }

        .decision-card h3 {
            margin: 0 0 12px;
            color: #2f3440;
            font-size: 1.18rem;
        }

        .decision-card p,
        .decision-card li {
            color: #536277;
            line-height: 1.7;
            font-weight: 570;
        }

        .mission-list {
            margin: 13px 0 0;
            padding-left: 1.15rem;
            color: #334155;
            line-height: 1.8;
            font-weight: 650;
        }

        .concept-card {
            min-height: 186px;
            padding: 20px;
        }

        .concept-card .emoji {
            font-size: 1.75rem;
            margin-bottom: 9px;
        }

        .concept-card h3 {
            margin: 0 0 9px;
            color: var(--ink);
            font-size: 1.08rem;
        }

        .concept-card p {
            margin: 0;
            color: var(--muted);
            line-height: 1.64;
            font-weight: 560;
        }

        .plan-item {
            display: flex;
            gap: 13px;
            align-items: flex-start;
            padding: 16px;
            margin-bottom: 11px;
        }

        .plan-num {
            min-width: 32px;
            height: 32px;
            display: grid;
            place-items: center;
            border-radius: 9px;
            background: linear-gradient(135deg, #8ecdf7, #91d9bf);
            color: white;
            font-weight: 950;
        }

        .plan-item h4 {
            margin: 0 0 5px;
            color: var(--ink);
        }

        .plan-item p {
            margin: 0;
            color: var(--muted);
            line-height: 1.55;
        }

        .stPlotlyChart {
            border-radius: 12px;
            overflow: hidden;
        }

        @media (max-width: 900px) {
            .hero-inner,
            .data-strip {
                grid-template-columns: 1fr;
            }
            .hero {
                padding: 25px 20px;
            }
        }
        </style>
        """
    )


@st.cache_data(show_spinner=False)
def load_heatwave_records() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("ISSUE_HW_DAY_*.xls"))
    frames: list[pd.DataFrame] = []
    for file in files:
        frame = pd.read_csv(file, sep="\t", encoding="cp949")
        frame.columns = [str(column).strip() for column in frame.columns]
        frame["source_file"] = file.name
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    raw = pd.concat(frames, ignore_index=True)
    raw["일시"] = pd.to_datetime(raw["일시"], errors="coerce")
    raw = raw.dropna(subset=["일시", "지점"])
    raw = raw.drop_duplicates(["일시", "지점"]).copy()

    for column in NUMERIC_COLUMNS:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")

    station_parts = raw["지점"].astype(str).str.extract(r"^(?P<station_name>.+?)\((?P<station_code>\d+)\)$")
    raw["station_name"] = station_parts["station_name"].fillna(raw["지점"].astype(str)).str.strip()
    raw["station_code"] = station_parts["station_code"].fillna("")
    raw["station_label"] = raw["station_name"] + " (" + raw["station_code"] + ")"
    raw["month"] = raw["일시"].dt.month
    raw["heat"] = raw["폭염여부(O/X)"].astype(str).str.strip().eq("O")
    raw["tropical_night"] = raw["열대야(O/X)"].astype(str).str.strip().eq("O")
    raw["warning"] = raw["폭염특보(O/X)"].astype(str).str.strip().eq("O")
    raw["impact_label"] = raw["폭염영향예보(단계)"].fillna("").astype(str).str.strip()
    raw["impact_score"] = raw["impact_label"].map(IMPACT_SCORE).fillna(0)
    return raw


@st.cache_data(show_spinner=False)
def summarize_station_data(records: pd.DataFrame) -> pd.DataFrame:
    if records.empty:
        return get_fallback_data()

    grouped = (
        records.groupby(["지점", "station_name", "station_code", "station_label"], as_index=False)
        .agg(
            observed_days=("일시", "count"),
            first_date=("일시", "min"),
            last_date=("일시", "max"),
            base_temp=("평균기온(°C)", "mean"),
            max_temp=("최고기온(°C)", "max"),
            min_temp=("최저기온(°C)", "min"),
            max_felt=("최고체감온도(°C)", "max"),
            avg_felt=("최고체감온도(°C)", "mean"),
            heat_days=("heat", "sum"),
            tropical_nights=("tropical_night", "sum"),
            base_humidity=("평균상대습도(%)", "mean"),
            warnings=("warning", "sum"),
            impact_days=("impact_score", lambda s: int((s > 0).sum())),
            max_impact=("impact_score", "max"),
        )
        .rename(columns={"지점": "station_id", "station_name": "region"})
    )
    grouped["power_risk"] = np.clip(
        grouped["heat_days"] * 0.65
        + grouped["tropical_nights"] * 0.45
        + grouped["max_felt"] * 0.85
        + grouped["warnings"] * 0.30,
        0,
        100,
    )
    grouped["observed_risk"] = np.clip(
        grouped["heat_days"] * 0.45
        + grouped["tropical_nights"] * 0.33
        + grouped["max_felt"] * 0.72
        + grouped["warnings"] * 0.10
        + grouped["impact_days"] * 0.12,
        0,
        100,
    )
    grouped["lon"] = grouped["region"].map(lambda name: STATION_COORDS.get(name, (np.nan, np.nan))[0])
    grouped["lat"] = grouped["region"].map(lambda name: STATION_COORDS.get(name, (np.nan, np.nan))[1])
    grouped = grouped.sort_values(["observed_risk", "heat_days"], ascending=False).reset_index(drop=True)
    return grouped


def get_fallback_data() -> pd.DataFrame:
    data = {
        "서울": {"base_temp": 24.5, "heat_days": 31, "tropical_nights": 47, "base_humidity": 71.6, "power_risk": 74},
        "대구": {"base_temp": 24.7, "heat_days": 45, "tropical_nights": 27, "base_humidity": 68.0, "power_risk": 78},
        "부산": {"base_temp": 24.3, "heat_days": 35, "tropical_nights": 54, "base_humidity": 74.8, "power_risk": 72},
        "광주": {"base_temp": 24.4, "heat_days": 52, "tropical_nights": 32, "base_humidity": 74.5, "power_risk": 82},
        "제주": {"base_temp": 25.3, "heat_days": 47, "tropical_nights": 72, "base_humidity": 70.3, "power_risk": 88},
    }
    fallback = pd.DataFrame.from_dict(data, orient="index").reset_index(names="region")
    fallback["station_id"] = fallback["region"]
    fallback["station_label"] = fallback["region"]
    fallback["station_code"] = ""
    fallback["observed_days"] = 153
    fallback["first_date"] = pd.Timestamp("2025-05-01")
    fallback["last_date"] = pd.Timestamp("2025-09-30")
    fallback["max_temp"] = fallback["base_temp"] + 12
    fallback["min_temp"] = fallback["base_temp"] - 10
    fallback["max_felt"] = fallback["base_temp"] + 12.5
    fallback["avg_felt"] = fallback["base_temp"] + 4.0
    fallback["warnings"] = fallback["heat_days"]
    fallback["impact_days"] = fallback["heat_days"]
    fallback["max_impact"] = 3
    fallback["observed_risk"] = np.clip(
        fallback["heat_days"] * 0.72 + fallback["tropical_nights"] * 0.52 + fallback["max_felt"] * 1.05,
        0,
        100,
    )
    fallback["lon"] = fallback["region"].map(lambda name: STATION_COORDS.get(name, (np.nan, np.nan))[0])
    fallback["lat"] = fallback["region"].map(lambda name: STATION_COORDS.get(name, (np.nan, np.nan))[1])
    return fallback


def get_risk_level(score: float) -> tuple[str, str, str]:
    if score <= 35:
        return "낮음", "badge-low", "#87d6b5"
    if score <= 62:
        return "보통", "badge-mid", "#7bb7f0"
    if score <= 82:
        return "높음", "badge-high", "#ffc08a"
    return "매우 높음", "badge-critical", "#ff8fa3"


def calculate_simulation(
    station_id: str,
    season: str,
    co2: int,
    sea_temp_rise: float,
    humidity_delta: int,
    urban_level: int,
    scenario: str,
    response_level: int,
    data: pd.DataFrame,
) -> dict:
    season_multiplier = {"봄": 0.55, "여름": 1.0, "가을": 0.62, "겨울": 0.22}
    season_temp_offset = {"봄": -6.0, "여름": 0.0, "가을": -5.2, "겨울": -15.0}
    scenario_offsets = {"현재": 0.0, "+1.5℃": 1.5, "+2.0℃": 2.0, "+3.0℃": 3.0, "+4.0℃": 4.0}

    row = data.loc[data["station_id"] == station_id].iloc[0]
    base_temp = float(row["base_temp"])
    max_felt = float(row["max_felt"])
    heat_days = float(row["heat_days"])
    tropical_nights = float(row["tropical_nights"])
    base_humidity = float(row["base_humidity"])
    base_power_risk = float(row["power_risk"])
    observed_risk = float(row["observed_risk"])

    season_factor = season_multiplier[season]
    scenario_offset = scenario_offsets[scenario]
    co2_effect = max(0, (co2 - 420) / 100) * 0.48
    sst_effect = sea_temp_rise * 0.58
    urban_effect = urban_level / 100 * 1.25
    humidity_effect = humidity_delta * 0.035
    response_effect = response_level / 100

    temp_contributions = {
        "온난화 시나리오": scenario_offset,
        "CO₂ 농도": co2_effect,
        "해수면 온도": sst_effect,
        "도시화": urban_effect,
        "습도 변화": humidity_effect,
        "대응 완화": -response_effect * 0.65,
    }

    climate_delta = sum(temp_contributions.values())
    current_temp = base_temp + season_temp_offset[season]
    predicted_temp = current_temp + climate_delta
    adjusted_humidity = float(np.clip(base_humidity + humidity_delta, 25, 98))
    felt_current = max_felt + season_temp_offset[season] * 0.35
    felt_temp = (
        felt_current
        + climate_delta * 1.35
        + max(0, adjusted_humidity - 65) * 0.105
        + urban_level * 0.025
        - response_level * 0.035
    )

    heat_amplifier = (
        scenario_offset * 8.0
        + co2_effect * 7.2
        + sst_effect * 5.2
        + max(0, humidity_delta) * 0.34
        + urban_level * 0.075
        - response_level * 0.105
    )
    night_amplifier = (
        scenario_offset * 6.7
        + co2_effect * 5.1
        + sst_effect * 7.0
        + max(0, humidity_delta) * 0.42
        + urban_level * 0.095
        - response_level * 0.12
    )

    predicted_heat_days = max(0, heat_days * season_factor + heat_amplifier)
    predicted_tropical_nights = max(0, tropical_nights * season_factor + night_amplifier)

    raw_health_score = (
        observed_risk * 0.30
        + felt_temp * 0.65
        + predicted_heat_days * 0.42
        + predicted_tropical_nights * 0.28
        + max(0, adjusted_humidity - 70) * 0.25
        - response_level * 0.30
    )
    health_score = float(np.clip(raw_health_score, 0, 100))

    power_score = float(
        np.clip(
            base_power_risk * 0.38
            + predicted_heat_days * 0.50
            + predicted_tropical_nights * 0.30
            + felt_temp * 0.58
            + urban_level * 0.12
            - response_level * 0.20,
            0,
            100,
        )
    )

    return {
        "station_id": station_id,
        "region": row["region"],
        "station_label": row["station_label"],
        "base_temp": base_temp,
        "current_temp": current_temp,
        "base_heat_days": heat_days,
        "base_tropical_nights": tropical_nights,
        "base_humidity": base_humidity,
        "adjusted_humidity": adjusted_humidity,
        "base_power_risk": base_power_risk,
        "observed_risk": observed_risk,
        "max_felt": max_felt,
        "scenario_offset": scenario_offset,
        "co2_effect": co2_effect,
        "sst_effect": sst_effect,
        "urban_effect": urban_effect,
        "humidity_effect": humidity_effect,
        "response_effect": response_effect,
        "temp_contributions": temp_contributions,
        "predicted_temp": predicted_temp,
        "temp_delta": predicted_temp - current_temp,
        "felt_temp": felt_temp,
        "felt_current": felt_current,
        "predicted_heat_days": predicted_heat_days,
        "predicted_tropical_nights": predicted_tropical_nights,
        "health_score": health_score,
        "power_score": power_score,
    }


def simulate_all_regions(data: pd.DataFrame, inputs: dict) -> pd.DataFrame:
    rows = []
    for station_id in data["station_id"]:
        result = calculate_simulation(data=data, station_id=station_id, **{k: v for k, v in inputs.items() if k != "station_id"})
        rows.append(
            {
                "station_id": station_id,
                "region": result["region"],
                "station_label": result["station_label"],
                "health_score": result["health_score"],
                "power_score": result["power_score"],
                "heat_days": result["predicted_heat_days"],
                "tropical_nights": result["predicted_tropical_nights"],
                "felt_temp": result["felt_temp"],
                "lon": float(data.loc[data["station_id"] == station_id, "lon"].iloc[0]),
                "lat": float(data.loc[data["station_id"] == station_id, "lat"].iloc[0]),
            }
        )
    return pd.DataFrame(rows).sort_values("health_score", ascending=False).reset_index(drop=True)


def generate_explanation(inputs: dict, result: dict, rank: int, total_regions: int) -> str:
    health_level, _, _ = get_risk_level(result["health_score"])
    power_level, _, _ = get_risk_level(result["power_score"])
    biggest_driver = max(
        {k: v for k, v in result["temp_contributions"].items() if k != "대응 완화"}.items(),
        key=lambda item: abs(item[1]),
    )[0]
    heat_change = result["predicted_heat_days"] - result["base_heat_days"]
    night_change = result["predicted_tropical_nights"] - result["base_tropical_nights"]

    return (
        f"{result['region']}은 2025년 5~9월 실제 관측 기준으로 폭염일수 {result['base_heat_days']:.0f}일, "
        f"열대야 {result['base_tropical_nights']:.0f}일이 기록된 지역입니다. 현재 조정한 조건에서는 건강 위험도가 "
        f"{result['health_score']:.0f}점으로 {health_level}이며, 전체 관측지점 {total_regions}곳 중 위험 순위는 "
        f"{rank}위입니다. 위험을 가장 크게 밀어 올리는 요인은 '{biggest_driver}'이고, 폭염일수는 기준 대비 "
        f"{heat_change:+.1f}일, 열대야는 {night_change:+.1f}일 변합니다. 전력 사용 위험도는 {power_level}이라 "
        "냉방 수요와 취약계층 대응을 함께 보는 의사결정 화면으로 활용할 수 있습니다."
    )


def render_metric_card(
    icon: str,
    label: str,
    value: str,
    unit: str,
    description: str,
    badge: str | None = None,
    badge_class: str = "badge-mid",
) -> None:
    badge_html = f"<span class='badge {badge_class}'>{badge}</span>" if badge else ""
    render_html(
        f"""
        <div class="metric-card">
            <div class="metric-top">
                <div>
                    <div class="metric-label">{label}</div>
                    {badge_html}
                </div>
                <div class="metric-icon">{icon}</div>
            </div>
            <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
            <div class="metric-desc">{description}</div>
        </div>
        """
    )


def render_data_strip(records: pd.DataFrame, station_data: pd.DataFrame) -> None:
    if records.empty:
        source = "샘플 기준값"
        date_range = "데이터 파일 없음"
        days = int(station_data["observed_days"].max())
        stations = len(station_data)
    else:
        source = f"{len(sorted(DATA_DIR.glob('ISSUE_HW_DAY_*.xls')))}개 원본 파일"
        date_range = f"{records['일시'].min():%Y.%m.%d} - {records['일시'].max():%Y.%m.%d}"
        days = records["일시"].nunique()
        stations = records["지점"].nunique()

    render_html(
        f"""
        <div class="data-strip">
            <div class="data-cell"><small>실제 데이터</small><strong>{source}</strong></div>
            <div class="data-cell"><small>관측 기간</small><strong>{date_range}</strong></div>
            <div class="data-cell"><small>분석 지점</small><strong>{stations:,}곳</strong></div>
            <div class="data-cell"><small>일 단위 관측</small><strong>{days:,}일</strong></div>
        </div>
        """
    )


def render_sidebar(data: pd.DataFrame) -> dict:
    st.sidebar.markdown("## 🔥 시나리오 조정")
    st.sidebar.caption("값을 움직이면 위험도, 순위, 요인분해가 즉시 바뀝니다.")

    labels = data["station_label"].tolist()
    default_index = next((i for i, label in enumerate(labels) if label.startswith("서울 ")), 0)
    selected_label = st.sidebar.selectbox("지역 선택", labels, index=default_index)
    station_id = data.loc[data["station_label"] == selected_label, "station_id"].iloc[0]

    season = st.sidebar.selectbox("계절", ["봄", "여름", "가을", "겨울"], index=1)
    scenario = st.sidebar.radio("온난화 시나리오", ["현재", "+1.5℃", "+2.0℃", "+3.0℃", "+4.0℃"], index=0)
    co2 = st.sidebar.slider("CO₂ 농도", 420, 900, 480, 20, format="%d ppm")
    sea_temp_rise = st.sidebar.slider("해수면 온도 상승", 0.0, 4.0, 0.5, 0.1, format="%.1f℃")
    humidity_delta = st.sidebar.slider("습도 변화", -20, 25, 0, 1, format="%+d%%p")
    urban_level = st.sidebar.slider("도시화·열섬 강도", 0, 100, 55, 1)
    response_level = st.sidebar.slider("대응 수준", 0, 100, 30, 1)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        dedent(
            f"""
            <div class="glass-card">
                <span class="badge badge-mid">현재 실험</span>
                <p style="margin:12px 0 0;color:#475569;line-height:1.65;font-weight:650;">
                    {selected_label} · {season} · {scenario}<br>
                    CO₂ {co2}ppm · 습도 {humidity_delta:+d}%p · 대응 {response_level}점
                </p>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    return {
        "station_id": station_id,
        "season": season,
        "co2": co2,
        "sea_temp_rise": sea_temp_rise,
        "humidity_delta": humidity_delta,
        "urban_level": urban_level,
        "scenario": scenario,
        "response_level": response_level,
    }


def render_hero(inputs: dict, result: dict, records: pd.DataFrame, station_data: pd.DataFrame) -> None:
    health_level, health_badge_class, _ = get_risk_level(result["health_score"])
    period = "실제 관측 데이터 연결"
    if not records.empty:
        period = f" 실제 관측"
    render_html(
        f"""
        <div class="hero">
            <div class="hero-inner">
                <div>
                    <div class="hero-badge">기상청 폭염 영향예보 기반 · {period}</div>
                    <h1>우리 동네 폭염 대응 AI</h1>
                    <p>162개 관측지점의 실제 폭염·열대야 데이터를 기준으로 CO₂, 해수면 온도, 습도, 도시화, 대응 수준이 바뀔 때 지역 위험도가 어떻게 튀어 오르는지 보여줍니다.</p>
                </div>
                <div class="hero-mini">
                    <div class="label">{result['region']} 시나리오 건강 위험도</div>
                    <div class="value">{result['health_score']:.0f}점</div>
                    <div style="margin-top:14px;"><span class="badge {health_badge_class}">{health_level}</span></div>
                </div>
            </div>
        </div>
        <div class="notice">
            기상청 폭염 영향예보 일자료를 바탕으로 지역별 위험 변화를 계산합니다. 조정값을 바꾸면 카드, 게이지, 지도, 해설이 함께 갱신됩니다.
        </div>
        """
    )


def make_comparison_chart(result: dict) -> go.Figure:
    categories = ["평균기온", "폭염일수", "열대야일수", "체감온도"]
    current_values = [
        result["current_temp"],
        result["base_heat_days"],
        result["base_tropical_nights"],
        result["felt_current"],
    ]
    future_values = [
        result["predicted_temp"],
        result["predicted_heat_days"],
        result["predicted_tropical_nights"],
        result["felt_temp"],
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="실제 관측 기준",
            x=categories,
            y=current_values,
            marker=dict(color="rgba(123, 183, 240, 0.78)", line=dict(width=0)),
            text=[f"{v:.1f}" for v in current_values],
            textposition="outside",
        )
    )
    fig.add_trace(
        go.Bar(
            name="조정 후 시뮬레이션",
            x=categories,
            y=future_values,
            marker=dict(color="rgba(255, 174, 137, 0.86)", line=dict(width=0)),
            text=[f"{v:.1f}" for v in future_values],
            textposition="outside",
        )
    )
    fig.update_layout(
        height=420,
        margin=dict(l=24, r=24, t=42, b=22),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Pretendard, sans-serif", color="#2f3440"),
        yaxis=dict(gridcolor="rgba(15,23,42,0.08)", zeroline=False),
        xaxis=dict(tickfont=dict(size=13)),
    )
    return fig


def make_driver_chart(result: dict) -> go.Figure:
    items = pd.DataFrame(
        {
            "요인": list(result["temp_contributions"].keys()),
            "기온 영향": list(result["temp_contributions"].values()),
        }
    )
    fig = px.bar(
        items,
        x="기온 영향",
        y="요인",
        orientation="h",
        text=items["기온 영향"].map(lambda value: f"{value:+.2f}℃"),
        color="기온 영향",
        color_continuous_scale=["#87d6b5", "#eef4f8", "#ffb680"],
        range_color=[-1.2, 4.5],
    )
    fig.update_layout(
        height=340,
        margin=dict(l=8, r=24, t=20, b=24),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        coloraxis_showscale=False,
        font=dict(family="Pretendard, sans-serif", color="#2f3440"),
        xaxis=dict(title="", gridcolor="rgba(15,23,42,0.08)", zeroline=True),
        yaxis=dict(title=""),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return fig


def make_gauge_chart(title: str, score: float, color: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "점", "font": {"size": 34, "color": "#2f3440"}},
            title={"text": title, "font": {"size": 18, "color": "#2f3440"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)"},
                "bar": {"color": color, "thickness": 0.24},
                "bgcolor": "rgba(255,255,255,0.72)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 35], "color": "rgba(135, 214, 181, 0.28)"},
                    {"range": [35, 62], "color": "rgba(123, 183, 240, 0.25)"},
                    {"range": [62, 82], "color": "rgba(255, 192, 138, 0.30)"},
                    {"range": [82, 100], "color": "rgba(255, 143, 163, 0.28)"},
                ],
            },
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=18, r=18, t=54, b=10),
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Pretendard, sans-serif"),
    )
    return fig


def make_korea_risk_map(ranking: pd.DataFrame, selected_station_id: str) -> go.Figure:
    mapped = ranking.dropna(subset=["lon", "lat"]).copy()
    korea_lon = [
        126.05, 126.22, 126.68, 126.92, 127.17, 127.80, 128.50, 129.15,
        129.50, 129.38, 128.85, 128.30, 127.65, 126.95, 126.35, 126.05,
    ]
    korea_lat = [
        34.45, 35.25, 36.15, 37.25, 38.08, 38.30, 38.18, 37.45,
        36.25, 35.45, 35.05, 34.75, 34.55, 34.35, 34.25, 34.45,
    ]
    jeju_lon = [126.15, 126.55, 126.95, 126.75, 126.25, 126.15]
    jeju_lat = [33.28, 33.18, 33.38, 33.58, 33.55, 33.28]

    selected = mapped[mapped["station_id"] == selected_station_id]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=korea_lon,
            y=korea_lat,
            mode="lines",
            fill="toself",
            fillcolor="rgba(255,255,255,0.58)",
            line=dict(color="rgba(132, 154, 178, 0.48)", width=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=jeju_lon,
            y=jeju_lat,
            mode="lines",
            fill="toself",
            fillcolor="rgba(255,255,255,0.58)",
            line=dict(color="rgba(132, 154, 178, 0.48)", width=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=mapped["lon"],
            y=mapped["lat"],
            mode="markers",
            marker=dict(
                size=np.clip(mapped["health_score"] / 3.8, 9, 24),
                color=mapped["health_score"],
                colorscale=[
                    [0, "#87d6b5"],
                    [0.45, "#9fd0ff"],
                    [0.72, "#ffc08a"],
                    [1, "#ff8fa3"],
                ],
                cmin=0,
                cmax=100,
                opacity=0.86,
                line=dict(color="white", width=1.3),
                colorbar=dict(title="위험도", thickness=12, len=0.78),
            ),
            text=mapped["region"],
            customdata=np.stack(
                [
                    mapped["health_score"].round(0),
                    mapped["heat_days"].round(1),
                    mapped["tropical_nights"].round(1),
                ],
                axis=-1,
            ),
            hovertemplate="<b>%{text}</b><br>건강 위험도 %{customdata[0]}점<br>폭염 %{customdata[1]}일<br>열대야 %{customdata[2]}일<extra></extra>",
            showlegend=False,
        )
    )
    if not selected.empty:
        fig.add_trace(
            go.Scatter(
                x=selected["lon"],
                y=selected["lat"],
                mode="markers+text",
                text=selected["region"],
                textposition="top center",
                marker=dict(size=28, color="rgba(255,255,255,0.98)", line=dict(color="#ff6f91", width=4)),
                textfont=dict(color="#a64157", size=13),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    fig.update_layout(
        height=520,
        margin=dict(l=12, r=12, t=10, b=10),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Pretendard, sans-serif", color="#2f3440"),
        xaxis=dict(range=[125.2, 130.1], visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(range=[33.0, 38.7], visible=False),
    )
    return fig


def make_ranking_chart(ranking: pd.DataFrame, selected_station_id: str) -> go.Figure:
    top = ranking.head(12).copy()
    if selected_station_id not in top["station_id"].tolist():
        selected = ranking[ranking["station_id"] == selected_station_id]
        top = pd.concat([top.head(11), selected], ignore_index=True)
    top["표시"] = top["region"] + " · " + top["health_score"].round(0).astype(int).astype(str) + "점"
    top["selected"] = np.where(top["station_id"] == selected_station_id, "선택 지역", "위험 상위")
    fig = px.bar(
        top.sort_values("health_score"),
        x="health_score",
        y="표시",
        orientation="h",
        color="selected",
        color_discrete_map={"선택 지역": "#ff8fa3", "위험 상위": "#ffb680"},
        text=top.sort_values("health_score")["health_score"].map(lambda value: f"{value:.0f}"),
    )
    fig.update_layout(
        height=430,
        margin=dict(l=8, r=24, t=20, b=24),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        showlegend=False,
        font=dict(family="Pretendard, sans-serif", color="#2f3440"),
        xaxis=dict(title="건강 위험도", range=[0, 105], gridcolor="rgba(15,23,42,0.08)"),
        yaxis=dict(title=""),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return fig


def make_actual_timeline(records: pd.DataFrame, station_id: str) -> go.Figure:
    selected = records[records["지점"] == station_id].sort_values("일시")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=selected["일시"],
            y=selected["최고체감온도(°C)"],
            name="최고체감온도",
            mode="lines",
            line=dict(color="#ff8fa3", width=3),
            fill="tozeroy",
            fillcolor="rgba(220,38,38,0.10)",
        )
    )
    heat_days = selected[selected["heat"]]
    fig.add_trace(
        go.Scatter(
            x=heat_days["일시"],
            y=heat_days["최고체감온도(°C)"],
            name="폭염일",
            mode="markers",
            marker=dict(color="#ffb680", size=8, line=dict(color="white", width=1)),
        )
    )
    fig.update_layout(
        height=330,
        margin=dict(l=24, r=24, t=28, b=24),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        legend=dict(orientation="h", y=1.04, x=0.01),
        font=dict(family="Pretendard, sans-serif", color="#2f3440"),
        yaxis=dict(title="℃", gridcolor="rgba(15,23,42,0.08)", zeroline=False),
        xaxis=dict(title=""),
    )
    return fig


def make_heatmap_chart(records: pd.DataFrame, station_data: pd.DataFrame) -> go.Figure:
    if records.empty:
        heatmap = station_data.head(12).copy()
        heatmap["month"] = "관측"
        heatmap["heat"] = heatmap["heat_days"]
    else:
        top_regions = station_data.head(16)["station_id"].tolist()
        heatmap = (
            records[records["지점"].isin(top_regions)]
            .groupby(["station_name", "month"], as_index=False)
            .agg(heat=("heat", "sum"))
        )
    fig = px.density_heatmap(
        heatmap,
        x="month",
        y="station_name" if "station_name" in heatmap.columns else "region",
        z="heat",
        color_continuous_scale=["#eef8ff", "#ffc08a", "#ff8fa3"],
        text_auto=True,
    )
    fig.update_layout(
        height=430,
        margin=dict(l=8, r=20, t=20, b=28),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        coloraxis_colorbar=dict(title="폭염일"),
        font=dict(family="Pretendard, sans-serif", color="#2f3440"),
        xaxis=dict(title="월"),
        yaxis=dict(title=""),
    )
    return fig


def render_region_cards(ranking: pd.DataFrame, selected_station_id: str) -> None:
    cols = st.columns(5)
    preview = ranking.head(5)
    for col, row in zip(cols, preview.itertuples(index=False)):
        selected = " selected" if row.station_id == selected_station_id else ""
        level, badge_class, _ = get_risk_level(row.health_score)
        with col:
            render_html(
                f"""
                <div class="region-card{selected}">
                    <div class="region-name">
                        <span>{row.region}</span>
                        <span class="badge {badge_class}">{level}</span>
                    </div>
                    <div class="region-stats">
                        <div class="region-stat">
                            <strong>{row.health_score:.0f}</strong>
                            <small>건강 위험도</small>
                        </div>
                        <div class="region-stat">
                            <strong>{row.heat_days:.1f}</strong>
                            <small>예상 폭염일</small>
                        </div>
                    </div>
                </div>
                """
            )


def render_ai_explanation_box(inputs: dict, result: dict, ranking: pd.DataFrame) -> None:
    rank = int(ranking.index[ranking["station_id"] == inputs["station_id"]][0] + 1)
    explanation = generate_explanation(inputs, result, rank, len(ranking))
    urgent = [
        "독거노인·만성질환자 안부 확인",
        "정오~오후 5시 야외활동 축소",
        "학교 체육·현장학습 실내 대체",
    ]
    if result["power_score"] >= 82:
        urgent.append("공공시설 냉방 피크 시간 분산")
    items = "".join(f"<li>{item}</li>" for item in urgent[:4])
    render_html(
        f"""
        <div class="decision-card">
            <h3>AI 해설 박스</h3>
            <p>{explanation}</p>
            <ul>{items}</ul>
        </div>
        """
    )


def render_mission_cards(result: dict) -> None:
    health_level, badge_class, _ = get_risk_level(result["health_score"])
    missions = {
        "학생": [
            "체육수업은 오전 또는 실내 활동으로 전환",
            "등하교 시간 물 섭취 안내와 보건실 냉방 점검",
            "열대야가 높은 날은 수면·집중도 저하 교육 자료 제공",
        ],
        "어르신": [
            "전화 안부 확인과 무더위쉼터 위치 안내",
            "낮 시간 외출 자제, 약 복용자 탈수 증상 확인",
            "냉방 취약 가구 방문 우선순위 지정",
        ],
        "야외근로자": [
            "오후 고위험 시간대 작업 중지 또는 교대",
            "그늘·휴식·물 제공 여부 체크리스트 운영",
            "체감온도 기준으로 작업 강도 자동 조정",
        ],
        "전력관리": [
            "냉방 피크 시간 공공건물 절전 모드 운영",
            "열대야 증가 시 야간 전력 수요까지 반영",
            "취약시설 냉방은 유지하고 일반구역만 분산 제어",
        ],
    }
    tabs = st.tabs(list(missions.keys()))
    for tab, (target, items) in zip(tabs, missions.items()):
        with tab:
            item_html = "".join(f"<li>{item}</li>" for item in items)
            render_html(
                f"""
                <div class="glass-card">
                    <span class="badge {badge_class}">{target} 대응 · {health_level}</span>
                    <ul class="mission-list">{item_html}</ul>
                </div>
                """
            )


def render_simulator_tab(inputs: dict, records: pd.DataFrame, station_data: pd.DataFrame) -> None:
    result = calculate_simulation(data=station_data, **inputs)
    ranking = simulate_all_regions(station_data, inputs)
    health_level, health_badge_class, health_color = get_risk_level(result["health_score"])
    power_level, power_badge_class, power_color = get_risk_level(result["power_score"])
    rank = int(ranking.index[ranking["station_id"] == inputs["station_id"]][0] + 1)

    render_html("<div class='section-title'><span></span>핵심 결과</div>")
    metrics = [
        ("📍", "전체 위험 순위", f"{rank}", f"/ {len(ranking)}위", "현재 조정값을 모든 관측지점에 적용한 순위입니다.", health_level, health_badge_class),
        ("🌡️", "예상 평균기온", f"{result['predicted_temp']:.1f}", "℃", "실제 관측 평균기온에 시나리오 변화를 더했습니다.", None, "badge-mid"),
        ("📈", "기온 변화량", f"{result['temp_delta']:+.1f}", "℃", "CO₂·해수면·도시화·습도·대응 수준의 합산 영향입니다.", None, "badge-high"),
        ("🔥", "예상 폭염일수", f"{result['predicted_heat_days']:.1f}", "일", f"실제 기준 {result['base_heat_days']:.0f}일에서 바뀐 값입니다.", None, "badge-high"),
        ("🌙", "예상 열대야", f"{result['predicted_tropical_nights']:.1f}", "일", f"실제 기준 {result['base_tropical_nights']:.0f}일에서 바뀐 값입니다.", None, "badge-high"),
        ("⚡", "전력 위험도", f"{result['power_score']:.0f}", "점", "냉방 수요와 열대야 영향을 반영한 점수입니다.", power_level, power_badge_class),
    ]
    for row_start in range(0, len(metrics), 3):
        metric_cols = st.columns(3)
        for col, metric in zip(metric_cols, metrics[row_start : row_start + 3]):
            with col:
                render_metric_card(*metric)

    render_html("<div class='section-title'><span></span>위험도 게이지</div>")
    gauge_cols = st.columns(2)
    with gauge_cols[0]:
        st.plotly_chart(make_gauge_chart("건강 위험도", result["health_score"], health_color), width="stretch")
        render_html(f"<span class='badge {health_badge_class}'>건강 위험도 {health_level}</span>")
    with gauge_cols[1]:
        st.plotly_chart(make_gauge_chart("전력 사용 위험도", result["power_score"], power_color), width="stretch")
        render_html(f"<span class='badge {power_badge_class}'>전력 사용 위험도 {power_level}</span>")

    render_html("<div class='section-title'><span></span>위험 해설</div>")
    render_ai_explanation_box(inputs, result, ranking)

    render_html("<div class='section-title'><span></span>슬라이더 변화가 만드는 차이</div>")
    cols = st.columns([1.1, 0.9])
    with cols[0]:
        st.plotly_chart(make_comparison_chart(result), width="stretch")
    with cols[1]:
        st.plotly_chart(make_driver_chart(result), width="stretch")

    render_html("<div class='section-title'><span></span>우리나라 위험 지도</div>")
    map_cols = st.columns([1.12, 0.88])
    with map_cols[0]:
        st.plotly_chart(make_korea_risk_map(ranking, inputs["station_id"]), width="stretch")
    with map_cols[1]:
        st.plotly_chart(make_ranking_chart(ranking, inputs["station_id"]), width="stretch")

    render_html("<div class='section-title'><span></span>실제 관측 타임라인</div>")
    if records.empty:
        render_html("<div class='notice'>data 폴더에 원본 파일이 없어서 샘플 기준값으로 표시 중입니다.</div>")
    else:
        st.plotly_chart(make_actual_timeline(records, inputs["station_id"]), width="stretch")

    render_html("<div class='section-title'><span></span>대상별 대응 추천</div>")
    render_mission_cards(result)


def render_data_tab(records: pd.DataFrame, station_data: pd.DataFrame) -> None:
    render_html("<div class='section-title'><span></span>실제 데이터 증거</div>")
    render_data_strip(records, station_data)

    cols = st.columns([1, 1])
    with cols[0]:
        render_html("<div class='section-title'><span></span>월별 폭염 집중도</div>")
        st.plotly_chart(make_heatmap_chart(records, station_data), width="stretch")
    with cols[1]:
        render_html("<div class='section-title'><span></span>관측 위험 상위 15곳</div>")
        table = station_data[
            [
                "region",
                "station_code",
                "heat_days",
                "tropical_nights",
                "max_felt",
                "base_humidity",
                "warnings",
                "observed_risk",
            ]
        ].head(15)
        st.dataframe(
            table.rename(
                columns={
                    "region": "지역",
                    "station_code": "지점번호",
                    "heat_days": "폭염일수",
                    "tropical_nights": "열대야",
                    "max_felt": "최고체감온도",
                    "base_humidity": "평균습도",
                    "warnings": "폭염특보",
                    "observed_risk": "관측위험도",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    render_html(
        """
        <div class="notice">
            데이터 처리: 원본 파일은 cp949 탭 구분 형식이라 앱에서 자동 파싱합니다. 같은 날짜·지점이 반복된 행은 중복 제거해 통계 왜곡을 막았습니다.
        </div>
        """
    )


def main() -> None:
    inject_css()
    records = load_heatwave_records()
    station_data = summarize_station_data(records)
    inputs = render_sidebar(station_data)
    hero_result = calculate_simulation(data=station_data, **inputs)
    render_hero(inputs, hero_result, records, station_data)

    simulator_tab, data_tab = st.tabs(["대응 시뮬레이터", "실제 데이터"])

    with simulator_tab:
        render_simulator_tab(inputs, records, station_data)

    with data_tab:
        render_data_tab(records, station_data)


if __name__ == "__main__":
    main()
