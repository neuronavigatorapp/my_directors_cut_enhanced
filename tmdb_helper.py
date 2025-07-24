# tmdb_helper.py
import requests

TMDB_API_KEY = "YOUR_TMDB_API_KEY"

# Genre mapping (used for display if needed)
GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
    53: "Thriller", 10752: "War", 37: "Western"
}

def fetch_movie_data(title):
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": False
    }

    try:
        search_response = requests.get(search_url, params=params)
        search_response.raise_for_status()
        results = search_response.json().get("results", [])
    except Exception as e:
        print(f"TMDb search error for '{title}': {e}")
        return None

    if not results:
        return None

    movie = results[0]
    movie_id = movie.get("id")

    # Fetch full details
    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    try:
        details_response = requests.get(details_url, params={"api_key": TMDB_API_KEY})
        details_response.raise_for_status()
        details = details_response.json()
    except Exception as e:
        print(f"TMDb details error for '{title}': {e}")
        return None

    genres = [g["name"] for g in details.get("genres", [])]
    runtime = details.get("runtime", None)

    return {
        "title": movie.get("title", title),
        "overview": movie.get("overview", ""),
        "release_date": movie.get("release_date", "")[:4],
        "poster_path": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}",
        "genres": genres,
        "runtime": runtime
    }
