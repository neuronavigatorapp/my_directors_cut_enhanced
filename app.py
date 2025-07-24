# app.py
import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime
from tmdb_helper import fetch_movie_data

st.set_page_config(page_title="My Director's Cut", layout="wide")

MOVIE_DATA_FILE = "movie_data.csv"
USER_DATA_FILE = "user_data.json"

# Load saved user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save user data
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Load movie data
def load_movie_titles():
    if os.path.exists(MOVIE_DATA_FILE):
        df = pd.read_csv(MOVIE_DATA_FILE)
        return df["title"].tolist()
    return []

# Save uploaded movie CSV
def save_uploaded_csv(upload):
    df = pd.read_csv(upload)
    df.to_csv(MOVIE_DATA_FILE, index=False)

# Setup session state
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()

# --- SIDEBAR: Controls ---
st.sidebar.title("View Options")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload Movie CSV", type=["csv"])
if uploaded_file is not None:
    save_uploaded_csv(uploaded_file)
    st.success("Movie list updated. Reload the app to see changes.")

view_mode = st.sidebar.radio("Display Mode", ["Full View", "Poster Grid"])
filter_decade = st.sidebar.selectbox("Filter by Decade", ["All", "1980s", "1990s", "2000s", "2010s", "2020s"])
filter_runtime = st.sidebar.selectbox("Filter by Runtime", ["All", "Short (<90 min)", "Medium (90–120)", "Long (>120)"])
show_recent = st.sidebar.checkbox("Show Recently Added Only")
playlist_trigger = st.sidebar.button("Surprise Me (3 picks)")

# --- Load and Fetch Movies ---
movie_titles = load_movie_titles()
movie_data = []

for title in movie_titles:
    movie = fetch_movie_data(title)
    if movie:
        movie_data.append(movie)

# Save all movie metadata for filtering/sorting
st.session_state.movies = movie_data

# --- Utility Functions ---

def get_decade_label(year):
    try:
        year = int(year)
        return f"{year // 10 * 10}s"
    except:
        return "Unknown"

def get_runtime_category(runtime):
    if runtime is None:
        return "Unknown"
    if runtime < 90:
        return "Short (<90 min)"
    elif 90 <= runtime <= 120:
        return "Medium (90–120)"
    else:
        return "Long (>120)"

# --- Movie Card Renderers ---

def render_movie_card(movie):
    title = movie["title"]
    user_data = st.session_state.user_data.get(title, {})
    note = user_data.get("note", "")
    tags = user_data.get("tags", [])
    last_watched = user_data.get("last_watched", "")

    col1, col2 = st.columns([1, 3])
    with col1:
        if movie["poster_path"]:
            st.image(movie["poster_path"], width=240)

    with col2:
        st.subheader(title)
        st.caption(f"{movie['release_date']} | {', '.join(movie['genres'])}")
        st.write(movie["overview"] or "_No summary available._")

        new_note = st.text_input("Your Note", value=note, key=f"note_{title}")
        if new_note != note:
            user_data["note"] = new_note
            st.session_state.user_data[title] = user_data
            save_user_data(st.session_state.user_data)

        fav_key = f"{title}_fav"
        is_fav = "Favorite" in tags
        new_fav = st.checkbox("Favorite", value=is_fav, key=fav_key)
        if new_fav and "Favorite" not in tags:
            tags.append("Favorite")
        elif not new_fav and "Favorite" in tags:
            tags.remove("Favorite")

        watch_later_key = f"{title}_watch_later"
        is_watch_later = "Watch Later" in tags
        new_watch_later = st.checkbox("Watch Later", value=is_watch_later, key=watch_later_key)
        if new_watch_later and "Watch Later" not in tags:
            tags.append("Watch Later")
        elif not new_watch_later and "Watch Later" in tags:
            tags.remove("Watch Later")

        if st.button("Watch on Fandango", key=f"watch_{title}"):
            user_data["last_watched"] = datetime.now().isoformat()
            st.session_state.user_data[title] = user_data
            save_user_data(st.session_state.user_data)

        user_data["tags"] = tags
        st.session_state.user_data[title] = user_data
        save_user_data(st.session_state.user_data)

        if last_watched:
            st.markdown(f"<small>Last watched: {last_watched.split('T')[0]}</small>", unsafe_allow_html=True)

    st.markdown("---")

def render_poster_grid(movies):
    cols = st.columns(5)
    for i, movie in enumerate(movies):
        with cols[i % 5]:
            st.image(movie["poster_path"], use_column_width=True)
            st.caption(movie["title"])

# --- Apply Filters and Render ---

filtered_movies = []
for movie in st.session_state.movies:
    # Filter by decade
    if filter_decade != "All":
        movie_decade = get_decade_label(movie["release_date"])
        if movie_decade != filter_decade:
            continue

    # Filter by runtime
    runtime_cat = get_runtime_category(movie.get("runtime", None))
    if filter_runtime != "All" and runtime_cat != filter_runtime:
        continue

    filtered_movies.append(movie)

# Recently added = last 5 titles in order
if show_recent:
    filtered_movies = filtered_movies[-5:]

# Playlist shuffle = pick 3 random movies
if playlist_trigger:
    st.subheader("🎞️ Your Movie Night Picks:")
    playlist = random.sample(filtered_movies, min(3, len(filtered_movies)))
    for movie in playlist:
        render_movie_card(movie)
else:
    # Main display logic
    if view_mode == "Full View":
        for movie in filtered_movies:
            render_movie_card(movie)
    elif view_mode == "Poster Grid":
        render_poster_grid(filtered_movies)
