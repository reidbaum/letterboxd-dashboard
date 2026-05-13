import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Letterboxd Stats", page_icon="🎬", layout="wide")

# ── Load data ──────────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    ratings = pd.read_csv("data/ratings.csv")
    diary   = pd.read_csv("data/diary.csv")

    for df in [ratings, diary]:
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    ratings["year"]         = ratings["year"].astype("Int64")
    ratings["decade"]       = (ratings["year"] // 10 * 10).astype(str) + "s"
    diary["watched_date"]   = pd.to_datetime(diary["watched_date"], errors="coerce")
    diary["rating"]         = pd.to_numeric(diary["rating"], errors="coerce")

    return ratings, diary

ratings, diary = load_data()

# ── Header ─────────────────────────────────────────────────────────────────────

st.title("🎬 My Letterboxd Stats")
st.divider()

# ── Top stats row ──────────────────────────────────────────────────────────────

films_watched  = diary["name"].nunique()
avg_rating     = round(ratings["rating"].mean(), 2)
top_year       = int(ratings["year"].value_counts().idxmax())

diary_dated    = diary.dropna(subset=["watched_date"])
films_per_day  = diary_dated.groupby(diary_dated["watched_date"].dt.date)["name"].count()
multi_film_days = int((films_per_day >= 2).sum())

watch_dates     = diary_dated["watched_date"].dt.date.drop_duplicates().sort_values().reset_index(drop=True)
longest, current = 1, 1
for i in range(1, len(watch_dates)):
    if (watch_dates[i] - watch_dates[i - 1]).days == 1:
        current += 1
        longest = max(longest, current)
    else:
        current = 1

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Films watched",    f"{films_watched:,}")
col2.metric("Avg rating",       f"{avg_rating} ★")
col3.metric("Most watched era", top_year)
col4.metric("Longest streak",   f"{longest} days")
col5.metric("2+ film days",     multi_film_days)

st.divider()

# ── Charts ─────────────────────────────────────────────────────────────────────

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Rating distribution")
    rc = ratings["rating"].value_counts().sort_index().reset_index()
    rc.columns = ["rating", "count"]
    fig = px.bar(rc, x="rating", y="count",
                 color="count", color_continuous_scale="Oranges",
                 labels={"rating": "Rating (★)", "count": "Films"})
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Films by decade")
    dc = ratings["decade"].value_counts().sort_index().reset_index()
    dc.columns = ["decade", "count"]
    fig2 = px.bar(dc, x="decade", y="count",
                  color="count", color_continuous_scale="Blues",
                  labels={"decade": "Decade", "count": "Films"})
    fig2.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Films watched per year")
    fy = diary_dated.groupby(diary_dated["watched_date"].dt.year).size().reset_index()
    fy.columns = ["year", "films"]
    fig3 = px.bar(fy, x="year", y="films",
                  color="films", color_continuous_scale="Greens",
                  labels={"year": "Year", "films": "Films watched"})
    fig3.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.subheader("Avg rating by decade")
    da = ratings.groupby("decade")["rating"].mean().round(2).reset_index()
    da.columns = ["decade", "avg_rating"]
    fig4 = px.bar(da, x="decade", y="avg_rating",
                  color="avg_rating", color_continuous_scale="Purples",
                  labels={"decade": "Decade", "avg_rating": "Avg rating"})
    fig4.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig4, use_container_width=True)