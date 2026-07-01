import os
from pathlib import Path

import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from ml.constants import CLUSTER_MOODS, FEATURES, MOOD_DESCRIPTIONS
from ml.classifier import SongClassifier, find_csv_path
from services.ai_features import AIFeatureError, estimate_features_with_ai
from services.spotify_client import SpotifyClient, SpotifyConfigError

load_dotenv()

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="AI Music Recommendation",
    page_icon="🎵",
    layout="wide",
)

# -------------------------
# CUSTOM CSS
# -------------------------

st.markdown(
    """
<style>
.stApp {
    background-color: #0F172A;
    color: white;
}
.hero {
    text-align: center;
    padding: 40px;
}
.hero h1 {
    font-size: 60px;
    color: white;
}
.hero p {
    font-size: 20px;
    color: #CBD5E1;
}
.song-card {
    background: #1E293B;
    padding: 20px;
    border-radius: 20px;
    margin-bottom: 15px;
    border-left: 5px solid #1DB954;
}
.mood-badge {
    display: inline-block;
    background: #1DB954;
    color: white;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: bold;
    margin-top: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------
# LOAD DATA
# -------------------------

keyword_map = {
    "Relax": 0,
    "Party": 1,
    "Romantic": 2,
    "Happy": 3,
    "Rap": 4,
}


@st.cache_data
def load_data():
    csv_path = find_csv_path()
    if csv_path is None:
        return None
    return pd.read_csv(csv_path)


@st.cache_resource
def get_classifier():
    return SongClassifier()


df = load_data()
classifier = get_classifier()

# -------------------------
# HELPERS
# -------------------------


def get_time_of_day():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    return "Night"


def recommend_songs(mood, dataset):
    cluster = keyword_map[mood]
    dataset = dataset.copy()
    dataset["cluster"] = dataset["cluster"].astype(int)
    return (
        dataset[dataset["cluster"] == cluster]
        .sort_values(by="popularity", ascending=False)
        .head(10)
    )


def render_feature_table(features: dict):
    rows = [{"Feature": name, "Value": round(float(features[name]), 4)} for name in FEATURES]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_classification_result(result: dict, source: str):
    mood = result["mood"]
    st.markdown(
        f"""
        <div class='song-card'>
            <h3>🎭 Predicted Mood: {mood}</h3>
            <p>Cluster {result['cluster']} — {MOOD_DESCRIPTIONS[mood]}</p>
            <span class='mood-badge'>Source: {source}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("View extracted parameters"):
        render_feature_table(result["features"])

# -------------------------
# SIDEBAR
# -------------------------

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🎵 Recommend",
        "🔍 Classify Online",
        "📊 Project",
        "👨‍💻 Developer",
    ],
)

# =====================================================
# HOME
# =====================================================

if page == "🏠 Home":
    st.markdown(
        """
        <div class='hero'>
            <h1>🎵 AI Music Recommendation System</h1>
            <p>
            Discover songs by mood, or search online and classify new tracks with AI
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Songs", len(df) if df is not None else "—")

    with col2:
        st.metric("Features", len(FEATURES))

    with col3:
        st.metric("Clusters", 5)

    with col4:
        st.metric("Current Time", get_time_of_day())

    if df is None:
        st.warning(
            "Dataset CSV not found. Add `spotify_prepared.csv` to enable recommendations, "
            "then run `python -m ml.train_model` to enable online classification."
        )
    elif not classifier.is_ready:
        st.info("Run `python -m ml.train_model` once to enable online song classification.")

# =====================================================
# RECOMMEND
# =====================================================

elif page == "🎵 Recommend":
    st.title("🎵 Music Recommendations")

    if df is None:
        st.error("Cannot recommend without `spotify_prepared.csv` in the project folder.")
        st.stop()

    mood = st.selectbox(
        "Select Your Mood",
        ["Relax", "Party", "Romantic", "Happy", "Rap"],
    )

    if st.button("Find Songs", type="primary"):
        with st.spinner("Finding perfect songs..."):
            recommendations = recommend_songs(mood, df)

        st.write("Mood:", mood)
        st.write("Songs Found:", len(recommendations))

        if recommendations.empty:
            st.error("No songs found for this mood.")
        else:
            st.success(f"{len(recommendations)} songs found!")
            for _, row in recommendations.iterrows():
                st.markdown(
                    f"""
                    <div class='song-card'>
                        <h3>🎵 {row['name']}</h3>
                        <p>🎤 {row['artists']}</p>
                        <p>⭐ Popularity: {row['popularity']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# =====================================================
# CLASSIFY ONLINE
# =====================================================

elif page == "🔍 Classify Online":
    st.title("🔍 Classify Songs Online")
    st.write(
        "Search for songs on Spotify, extract audio parameters, and classify them "
        "into mood clusters using your K-Means model."
    )

    if not classifier.is_ready:
        st.error(
            "Classification model not found. Place your CSV in the project root and run:\n\n"
            "`python -m ml.train_model`"
        )
        st.stop()

    spotify = SpotifyClient()
    tab_spotify, tab_ai = st.tabs(["Spotify Search", "AI Estimate (by name)"])

    with tab_spotify:
        if not spotify.is_configured:
            st.warning(
                "Add `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` to a `.env` file. "
                "Create a free app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)."
            )
        else:
            query = st.text_input("Search song or artist", placeholder="e.g. Blinding Lights The Weeknd")
            limit = st.slider("Max results", 5, 20, 10)

            if st.button("Search Spotify", type="primary", key="search_spotify"):
                with st.spinner("Searching..."):
                    try:
                        st.session_state["spotify_results"] = spotify.search_tracks(query, limit=limit)
                    except Exception as exc:
                        st.error(f"Spotify search failed: {exc}")

            results = st.session_state.get("spotify_results", [])
            if results:
                st.subheader("Results")
                for track in results:
                    cols = st.columns([4, 1])
                    with cols[0]:
                        st.markdown(f"**{track.name}** — {track.artists}")
                        st.caption(f"{track.album} · Popularity {track.popularity}")
                    with cols[1]:
                        if st.button("Classify", key=f"classify_{track.track_id}"):
                            with st.spinner("Extracting features & classifying..."):
                                try:
                                    features = spotify.get_track_features(
                                        track.track_id, track.popularity
                                    )
                                    result = classifier.classify_song(features)
                                    st.session_state["last_result"] = {
                                        **result,
                                        "song": track.name,
                                        "artist": track.artists,
                                        "source": "Spotify API",
                                    }
                                except Exception as exc:
                                    st.error(f"Classification failed: {exc}")

    with tab_ai:
        st.write(
            "When a song is not on Spotify or you only know the title, an LLM estimates "
            "the same 10 audio parameters your model was trained on."
        )
        ai_song = st.text_input("Song name", key="ai_song")
        ai_artist = st.text_input("Artist (optional)", key="ai_artist")

        if st.button("Estimate & Classify with AI", type="primary"):
            if not ai_song.strip():
                st.warning("Enter a song name.")
            elif not os.getenv("OPENAI_API_KEY"):
                st.warning("Set `OPENAI_API_KEY` in `.env` to use AI feature estimation.")
            else:
                with st.spinner("AI is analyzing the song..."):
                    try:
                        features = estimate_features_with_ai(ai_song, ai_artist)
                        result = classifier.classify_song(features)
                        st.session_state["last_result"] = {
                            **result,
                            "song": ai_song,
                            "artist": ai_artist or "Unknown",
                            "source": "AI (OpenAI)",
                        }
                    except AIFeatureError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"AI classification failed: {exc}")

    last = st.session_state.get("last_result")
    if last:
        st.divider()
        st.subheader(f"🎵 {last['song']} — {last['artist']}")
        render_classification_result(last, last["source"])

# =====================================================
# PROJECT
# =====================================================

elif page == "📊 Project":
    st.title("📊 About Project")

    st.subheader("Problem Statement")
    st.write(
        "Users often struggle to find songs matching their mood. "
        "This project uses K-Means clustering on Spotify audio features "
        "to group and recommend music."
    )

    st.subheader("Machine Learning")
    st.write(
        """
        - **K-Means Clustering** (5 mood clusters)
        - **10 features**: acousticness, danceability, energy, instrumentalness,
          liveness, loudness, speechiness, tempo, valence, popularity
        - **Online pipeline**: Spotify search → audio features → classify
        - **AI fallback**: LLM estimates parameters from song name/artist
        """
    )

    st.subheader("Mood Clusters")
    for cluster_id, mood in CLUSTER_MOODS.items():
        st.write(f"- **{mood}** (cluster {cluster_id}): {MOOD_DESCRIPTIONS[mood]}")

# =====================================================
# DEVELOPER
# =====================================================

elif page == "👨‍💻 Developer":
    st.title("👨‍💻 Developer")

    st.markdown(
        """
        ### Jayant Sharma

        AI & Machine Learning Enthusiast

        #### Skills
        - Python
        - Machine Learning
        - Data Science
        - Streamlit

        #### Project
        AI Music Recommendation System
        """
    )

    st.markdown("[GitHub](https://github.com/jayant1856)")
