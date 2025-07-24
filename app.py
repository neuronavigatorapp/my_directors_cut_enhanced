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

# Load movie titles
def load_movie_titles():
    if os.path.exists(MOVIE_DATA_FILE):
        df = pd.read_csv(MOVIE_DATA_FILE)
        return df["title"].dropna().tolist()
    return []

# Save uploaded CSV
def save_uploaded_csv(upload):
    df = pd.read_csv(upload)
    df.to_csv(MOVIE_DATA_FILE, index=False)

# Setup state
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()

st.sidebar.title("View Options")
uploaded_file = st.sidebar.file_uploader("Upload Movie CSV", type=["csv"])
if uploaded_file:
    save_uploaded_csv(uploaded_file)
    st.success("Movie list updated. Please rerun the app.")

view_mode = st.sidebar.radio("Display Mode", ["Full View", "Poster Grid"])
filter_decade = st.sidebar.selectbox("Filter by Decade", ["All", "1980s", "1990s", "2000s", "2010s", "2020s"])
filter_runtime = st.sidebar.selectbox("Filter by Runtime", ["All", "Short (<90 min)", "Medium (90–120)", "Long (>120)"])
show_recent = st.sidebar.checkbox("Show Recently Added Only")
playlist_trigger = st.sidebar.button("Surprise Me (3 picks)")

# Load and fetch
movie_titles = load_movie_titles()
st.write("Loaded titles:", movie_titles)
movie_data = []
for title in movie_titles:
    movie = fetch_movie_data(title)
    if movie:
        movie_data.append(movie)
st.write("Movies fetched:", len(movie_data))
if not movie_data:
    st.error("⚠️ No movie data was fetched. Please check your TMDb API key or movie titles.")

st.session_state.movies = movie_data

# Utils
def get_decade_label(year):
    try:
        return f"{int(year) // 10 * 10}s"
    except:
        return "Unknown"

def get_runtime_category(runtime):
    if runtime is None: return "Unknown"
    return "Short (<90 min)" if runtime < 90 else "Medium (90–120)" if runtime <= 120 else "Long (>120)"

def render_movie_card(movie):
    title = movie["title"]
    data = st.session_state.user_data.get(title, {})
    note = data.get("note", "")
    tags = data.get("tags", [])
    last_watched = data.get("last_watched", "")

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
            data["note"] = new_note
        if st.checkbox("Favorite", value="Favorite" in tags, key=f"fav_{title}"):
            if "Favorite" not in tags: tags.append("Favorite")
        else:
            if "Favorite" in tags: tags.remove("Favorite")
        if st.checkbox("Watch Later", value="Watch Later" in tags, key=f"wl_{title}"):
            if "Watch Later" not in tags: tags.append("Watch Later")
        else:
            if "Watch Later" in tags: tags.remove("Watch Later")
        if st.button("Watch on Fandango", key=f"watch_{title}"):
            data["last_watched"] = datetime.now().isoformat()
        if last_watched:
            st.markdown(f"<small>Last watched: {last_watched.split('T')[0]}</small>", unsafe_allow_html=True)

        data["tags"] = tags
        st.session_state.user_data[title] = data
        save_user_data(st.session_state.user_data)
    st.markdown("---")

def render_poster_grid(movies):
    cols = st.columns(5)
    for i, movie in enumerate(movies):
        with cols[i % 5]:
            st.image(movie["poster_path"], use_column_width=True)
            st.caption(movie["title"])

# Apply filters
filtered_movies = []
for m in st.session_state.movies:
    if filter_decade != "All" and get_decade_label(m["release_date"]) != filter_decade:
        continue
    if filter_runtime != "All" and get_runtime_category(m.get("runtime")) != filter_runtime:
        continue
    filtered_movies.append(m)

if show_recent:
    filtered_movies = filtered_movies[-5:]

if playlist_trigger:
    st.subheader("🎞️ Your Movie Night Picks:")
    picks = random.sample(filtered_movies, min(3, len(filtered_movies)))
    for movie in picks:
        render_movie_card(movie)
else:
    if view_mode == "Full View":
        for movie in filtered_movies:
            render_movie_card(movie)
    else:
        render_poster_grid(filtered_movies)

# --- THEME TOGGLE ---
theme_choice = st.sidebar.radio("Theme", ["Modern", "Classic"])

# --- STYLE INJECTION ---
if theme_choice == "Modern":
    st.markdown("""
    <style>
    html, body, .stApp {
        background-color: #111;
        color: #f2f2f2;
        font-family: 'Segoe UI', sans-serif;
        font-size: 18px;
    }
    h1, h2, h3 {
        font-weight: 600;
        text-transform: uppercase;
    }
    .movie-poster {
        border-radius: 6px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }
    .tag-chip {
        display: inline-block;
        background-color: #333;
        color: #eee;
        padding: 4px 12px;
        margin: 4px 6px 4px 0;
        border-radius: 16px;
        font-size: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

elif theme_choice == "Classic":
    st.markdown("""
    <style>
    html, body, .stApp {
        background-color: #0a0a0a;
        color: #eaeaea;
        font-family: 'Georgia', serif;
        font-size: 18px;
    }
    h1, h2, h3 {
        font-weight: 500;
        font-style: italic;
        text-transform: none;
        letter-spacing: 0.5px;
    }
    .movie-poster {
        border: 1px solid #444;
        box-shadow: none;
        border-radius: 0;
    }
    .tag-chip {
        display: inline-block;
        background-color: #222;
        color: #ccc;
        padding: 4px 10px;
        margin: 4px 6px 4px 0;
        border-radius: 12px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONT SIZE UPDATE ---
# Applied in both themes for accessibility
if theme_choice == "Modern":
    st.markdown("""
    <style>
    html, body, .stApp {
        font-size: 22px;
    }
    </style>
    """, unsafe_allow_html=True)

elif theme_choice == "Classic":
    st.markdown("""
    <style>
    html, body, .stApp {
        font-size: 22px;
    }
    </style>
    """, unsafe_allow_html=True)

# Updated render_movie_card() with poster styling class
def render_movie_card(movie):
    title = movie["title"]
    data = st.session_state.user_data.get(title, {})
    note = data.get("note", "")
    tags = data.get("tags", [])
    last_watched = data.get("last_watched", "")

    col1, col2 = st.columns([1, 3])
    with col1:
        if movie["poster_path"]:
            st.markdown(
                f"<img src='{movie['poster_path']}' width='240' class='movie-poster'>",
                unsafe_allow_html=True
            )

    with col2:
        st.subheader(title)
        st.caption(f"{movie['release_date']} | {', '.join(movie['genres'])}")
        st.write(movie["overview"] or "_No summary available._")
        new_note = st.text_input("Your Note", value=note, key=f"note_{title}")
        if new_note != note:
            data["note"] = new_note
        if st.checkbox("Favorite", value="Favorite" in tags, key=f"fav_{title}"):
            if "Favorite" not in tags: tags.append("Favorite")
        else:
            if "Favorite" in tags: tags.remove("Favorite")
        if st.checkbox("Watch Later", value="Watch Later" in tags, key=f"wl_{title}"):
            if "Watch Later" not in tags: tags.append("Watch Later")
        else:
            if "Watch Later" in tags: tags.remove("Watch Later")
        if st.button("Watch on Fandango", key=f"watch_{title}"):
            data["last_watched"] = datetime.now().isoformat()
        if last_watched:
            st.markdown(f"<small>Last watched: {last_watched.split('T')[0]}</small>", unsafe_allow_html=True)

        data["tags"] = tags
        st.session_state.user_data[title] = data
        save_user_data(st.session_state.user_data)
    st.markdown("---")

# --- PATCH CLASSIC THEME: gold accent, marquee headers, button hover effects ---
if theme_choice == "Classic":
    st.markdown("""
    <style>
    html, body, .stApp {
        background-color: #0a0a0a;
        color: #eaeaea;
        font-family: 'Georgia', serif;
        font-size: 22px;
    }
    h1, h2, h3 {
        font-weight: 500;
        font-style: italic;
        letter-spacing: 0.5px;
        border-left: 6px solid #d4af37;
        padding-left: 12px;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .movie-poster {
        border: 1px solid #555;
        box-shadow: 0 0 0 1px #333;
        border-radius: 4px;
    }
    .tag-chip {
        display: inline-block;
        background-color: #1a1a1a;
        color: #d4af37;
        border: 1px solid #d4af37;
        padding: 4px 10px;
        margin: 4px 6px 4px 0;
        border-radius: 12px;
        font-size: 14px;
    }
    button[kind="secondary"] {
        color: #d4af37 !important;
        border: 1px solid #d4af37 !important;
        background-color: transparent !important;
    }
    button[kind="secondary"]:hover {
        background-color: #333 !important;
        border-color: #e2c770 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PATCH MODERN THEME: neon accent, bold UI, improved poster/card visual ---
if theme_choice == "Modern":
    st.markdown("""
    <style>
    html, body, .stApp {
        background-color: #111;
        color: #f2f2f2;
        font-family: 'Segoe UI', sans-serif;
        font-size: 22px;
    }
    h1, h2, h3 {
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #08f;
        padding-bottom: 8px;
    }
    .movie-poster {
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.6);
    }
    .tag-chip {
        display: inline-block;
        background-color: #222;
        color: #08f;
        padding: 4px 12px;
        margin: 4px 6px 4px 0;
        border-radius: 16px;
        font-size: 15px;
    }
    button[kind="secondary"] {
        color: #08f !important;
        border: 1px solid #08f !important;
        background-color: transparent !important;
        border-radius: 6px !important;
    }
    button[kind="secondary"]:hover {
        background-color: #08f !important;
        color: black !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)
