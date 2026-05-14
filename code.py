# Letterboxd Dashboard — Reid B.

# ---------- Import & Load ----------
import pandas as pd
import matplotlib.pyplot as plt

ratings = pd.read_csv("data/ratings.csv")
diary = pd.read_csv("data/diary.csv")
watched = pd.read_csv("data/watched.csv")
watchlist = pd.read_csv("data/watchlist.csv")

for df in [ratings, diary, watched, watchlist]:
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    if 'year' in df.columns:
        df['year'] = df['year'].astype('Int64')
    if 'watched_date' in df.columns:
        df['watched_date'] = pd.to_datetime(diary['watched_date'], errors='coerce')


# ---------- Rating Distribution ----------
rc = ratings['rating'].value_counts().sort_index()

fig, ax = plt.subplots()
bars = ax.bar(rc.index.astype(str), rc.values, color='green', edgecolor='white')

for bar in bars:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        str(int(bar.get_height())),
        ha='center', va='bottom', fontsize=9
    )

ax.set_title('My rating distribution', fontsize=14, fontweight='bold')
ax.set_xlabel('Rating (★)')
ax.set_ylabel('Films')
plt.tight_layout()
plt.show()

# Films watched per month
monthly = (
    diary_dated
    .groupby(diary_dated['watched_date'].dt.to_period('M'))
    .size()
    .reset_index(name='films')
)
monthly['watched_date'] = monthly['watched_date'].astype(str)

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(monthly['watched_date'], monthly['films'],
        color='#e63946', linewidth=2, marker='o', markersize=4)
ax.fill_between(range(len(monthly)), monthly['films'], alpha=0.15, color='#e63946')
ax.set_xticks(range(len(monthly)))
ax.set_xticklabels(monthly['watched_date'], rotation=45, ha='right')
# show every 3rd label
for i, label in enumerate(ax.get_xticklabels()):
    if i % 3 != 0:
        label.set_visible(False)
ax.set_title('Films watched per month', fontsize=14, fontweight='bold')
ax.set_xlabel('Month')
ax.set_ylabel('Films watched')
plt.tight_layout()
plt.show()


# ---------- Header Stats (All-time) ----------
## Films Watched
films_watched = len(watched)
print(f'Films watched: {films_watched}')

## Longest Streak
### streak (days)
watch_dates = (
    diary.watched_date.dt.date.drop_duplicates().sort_values().reset_index(drop=True)
)

longest_streak = 1
current_streak = 1

for i in range(1, len(watch_dates)):
    gap = (watch_dates[i] - watch_dates[i - 1]).days
    if gap == 1:
        current_streak += 1
        longest_streak = max(longest_streak, current_streak)
    else:
        current_streak = 1

print(f'Longest streak: {longest_streak} consecutive days')

### streak (weeks)
watch_weeks = (
    diary['watched_date'].dt.to_period('W').drop_duplicates().sort_values().reset_index(drop=True)
)

longest_week_streak = 1
current_week_streak = 1

for i in range(1, len(watch_weeks)):
    gap = watch_weeks[i].week - watch_weeks[i - 1].week
    year_gap = watch_weeks[i].year - watch_weeks[i - 1].year
    
    is_consecutive = (gap == 1) or (year_gap == 1 and gap < 0)
    
    if is_consecutive:
        current_week_streak += 1
        longest_week_streak = max(longest_week_streak, current_week_streak)
    else:
        current_week_streak = 1

print(f'Longest weekly streak: {longest_week_streak} consecutive weeks')

## Multi-film Days
films_per_day = diary.groupby(diary['watched_date'].dt.date)['name'].count()
multi_film_days = (films_per_day >= 2).sum()

print(f'Multi-film days: {multi_film_days}')


# ---------- Top Films ----------
## By Year — Films
year_counts = watched['year'].value_counts().sort_index()

fig, ax = plt.subplots()
ax.bar(year_counts.index.astype(str), year_counts.values, color='steelblue', edgecolor='white')
ax.set_title('Films watched by release year', fontsize=14, fontweight='bold')
ax.set_xlabel('Release year')
ax.set_ylabel('Films')

plt.xticks(rotation=45, ha='right')
#show every 5th label to avoid crowding
for i, label in enumerate(ax.get_xticklabels()):
    if i % 5 != 0:
        label.set_visible(False)

plt.tight_layout()
plt.show()

## By Year — Ratings
ratings_year = (
    ratings.groupby('year')['rating']
    .agg(['mean', 'count'])
    .reset_index()
    .rename(columns={'mean': 'avg_rating', 'count': 'films'})
    .sort_values('year')
)
# fill in missing years with NaN
full_range = pd.RangeIndex(ratings_year['year'].min(), ratings_year['year'].max() + 1)
ratings_year = ratings_year.set_index('year').reindex(full_range).reset_index()
ratings_year.columns = ['year', 'avg_rating', 'films']
# mask years with fewer than 3 films
ratings_year.loc[ratings_year['films'] < 3, 'avg_rating'] = float('nan')
fig, ax = plt.subplots()
ax.bar(ratings_year['year'].astype(str), ratings_year['avg_rating'].round(2),
       color='gold', edgecolor='white')
ax.set_title('Average rating by release year (min 3 films)', fontsize=14, fontweight='bold')
ax.set_xlabel('Release year')
ax.set_ylabel('Avg rating')
ax.set_ylim(0, 5.5)

plt.xticks(rotation=45, ha='right')
for i, label in enumerate(ax.get_xticklabels()):
    if i % 5 != 0:
        label.set_visible(False)

plt.tight_layout()
plt.show()

## By Year — Diary
fig, ax = plt.subplots()
bars = ax.bar(diary_year.index.astype(str), diary_year.values,
              color='mediumseagreen', edgecolor='white')

for bar in bars:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        str(int(bar.get_height())),
        ha='center', va='bottom', fontsize=9
    )

ax.set_title('Films logged per year', fontsize=14, fontweight='bold')
ax.set_xlabel('Year')
ax.set_ylabel('Films watched')
plt.tight_layout()
plt.show()


# ---------- Highest Rated Decades ----------
## by decade
ratings['decade'] = (ratings['year'] // 10 * 10).astype(str) + 's'
decade_ct = ratings.groupby("decade")["rating"].count().sort_values(ascending=False)
decade_avg = round(ratings.groupby("decade")["rating"].mean().sort_values(ascending=False), 2)

## Filter to decades with at least 20 films
min_films = 20
decade_ct = decade_ct[decade_ct >= min_films]
decade_avg = decade_avg[decade_avg.index.isin(decade_ct.index)]

#print(decade_ct.head())
print(decade_avg.head())

decade_stats = (
    ratings.groupby('decade')['rating']
    .agg(['mean', 'count'])
    .reset_index()
    .rename(columns={'mean': 'avg_rating', 'count': 'films'})
    .query('films >= 20')
    .sort_values('decade')
)

fig, ax = plt.subplots()
bars = ax.bar(decade_stats['decade'], decade_stats['avg_rating'].round(2),
              color='mediumpurple', edgecolor='white')

for bar, val in zip(bars, decade_stats['avg_rating']):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.05,
        f'{val:.2f}',
        ha='center', va='bottom', fontsize=9
    )

ax.set_title('Avg rating by decade (min 20 films)', fontsize=14, fontweight='bold')
ax.set_xlabel('Decade')
ax.set_ylabel('Avg rating')
ax.set_ylim(0, 5.5)
plt.tight_layout()
plt.show()

# Films watched by decade 
decade_counts = ratings['decade'].value_counts().sort_index()

fig, ax = plt.subplots()
bars = ax.bar(decade_counts.index, decade_counts.values, color='teal', edgecolor='white')

for bar in bars:
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        str(int(bar.get_height())),
        ha='center', va='bottom', fontsize=9
    )

ax.set_title('Films watched by decade', fontsize=14, fontweight='bold')
ax.set_xlabel('Decade')
ax.set_ylabel('Films')
plt.tight_layout()
plt.show()


# ---------- Most Watched ----------
#diary.groupby('name').size().sort_values(ascending=False).head(20)

rewatched = (
    diary.groupby(['name', 'year'])
    .size()
    .reset_index(name='watches')
    .query('watches > 1')
    .sort_values('watches')
    .tail(15)
)
rewatched['label'] = rewatched['name'] + ' (' + rewatched['year'].astype(str) + ')'

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(rewatched['label'], rewatched['watches'], color='#e63946', edgecolor='white')

for bar in bars:
    ax.text(
        bar.get_width() + 0.05,
        bar.get_y() + bar.get_height() / 2,
        str(int(bar.get_width())),
        va='center', fontsize=9
    )

ax.set_title('Most rewatched films', fontsize=14, fontweight='bold')
ax.set_xlabel('Times watched')
plt.tight_layout()
plt.show()


# custom ...
# ---------- Viewing Habits ----------
## Heatmap Calendar (All Time)
## Heatmap Calendar (2025)
## Avg Rating by Month
## Films by Day of Week

# ---------- Rating Analysis ----------
## Rating Over Time
## Half Star vs Full Star
## Ratings vs Normal Distribution

# ---------- Film Taste ----------
## Old vs New
## Rewatch Rate

# ---------- Watchlist Analysis ----------
## Watchlist Growth Over Time



# TBD (Requires API)
## Genres, Countries & Languages
## Top Cast
## Top Directors
## Crew & Studios
## World Map