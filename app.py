import os
from datetime import datetime
from difflib import get_close_matches
import tempfile

from utils.audio_features import extract_audio_features
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from services.history import (
    save_history,
    favorite_cluster
)

from ml.constants import CLUSTER_MOODS, FEATURES, MOOD_DESCRIPTIONS
from ml.classifier import SongClassifier, find_csv_path
from services.ai_features import AIFeatureError, estimate_features_with_ai
from services.spotify_client import SpotifyClient, SpotifyConfigError

load_dotenv()

spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
gemini_api_key = os.getenv("GEMINI_API_KEY")

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

    # Cluster 0 : Classical / Relaxing
    "relax": 0,
    "relaxing": 0,
    "calm": 0,
    "peaceful": 0,
    "sleep": 0,
    "study": 0,
    "focus": 0,
    "meditation": 0,
    "classical": 0,
    "instrumental": 0,
    "soft": 0,

    # Cluster 1 : Party / Energetic
    "party": 1,
    "dance": 1,
    "energetic": 1,
    "energy": 1,
    "workout": 1,
    "gym": 1,
    "running": 1,
    "exercise": 1,
    "celebration": 1,
    "fun": 1,
    "festival": 1,

    # Cluster 2 : Romantic
    "romantic": 2,
    "romance": 2,
    "love": 2,
    "couple": 2,
    "date": 2,
    "relationship": 2,
    "heart": 2,
    "valentine": 2,
    "crush": 2,
    "emotion": 2,
    "affection": 2,

    # Cluster 3 : Happy / Feel-Good
    "happy": 3,
    "feelgood": 3,
    "feel-good": 3,
    "positive": 3,
    "cheerful": 3,
    "joy": 3,
    "smile": 3,
    "uplifting": 3,
    "good mood": 3,
    "motivational": 3,
    "fresh": 3,

    # Cluster 4 : Rap
    "rap": 4,
    "hiphop": 4,
    "hip-hop": 4,
    "trap": 4,
    "freestyle": 4,
    "bars": 4,
    "rapping": 4,
    "drill": 4,
    "beat": 4,
    "street": 4
}

cluster_time_map = {
    0: "Morning",       # Relax
    1: "Evening",       # Party
    2: "Night",         # Romantic
    3: "Afternoon",     # Happy
    4: "Late Evening"   # Rap
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

    elif 21 <= hour < 23:
        return "Late Evening"

    else:
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
    
def recommend_by_time(dataset):

    current_time = get_time_of_day()

    # Find which cluster belongs to this time
    selected_cluster = None

    for cluster, time in cluster_time_map.items():
        if time == current_time:
            selected_cluster = cluster
            break

    dataset = dataset.copy()
    dataset["cluster"] = dataset["cluster"].astype(int)

    recommendations = dataset[
        dataset["cluster"] == selected_cluster
    ]

    return (
        recommendations
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


def classify_and_store(
    song_name: str,
    artist_name: str,
    source_label: str,
    audio_features: dict | None = None,
):
    """Runs the AI feature estimator and stores the result."""

    with st.spinner("AI is estimating song parameters..."):

        try:

            features = estimate_features_with_ai(
                song_name,
                artist_name,
                audio_features=audio_features,
            )

            result = classifier.classify_song(features)

            save_history(
                user="Guest",
                song=song_name,
                artist=artist_name,
                cluster=result["cluster"],
                mood=result["mood"],
            )

            st.session_state["last_result"] = {
                **result,
                "song": song_name,
                "artist": artist_name,
                "source": source_label,
            }

        except AIFeatureError as exc:
            st.error(str(exc))

        except Exception as exc:
            st.error(f"Classification failed: {exc}")

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
        st.error("Cannot recommend without spotify_prepared.csv.")
        st.stop()

    # ===========================================
    # Mood Based Recommendation
    # ===========================================

    st.subheader("😊 Recommend by Mood")

    user_input = st.text_input(
        "Enter your mood or activity",
        placeholder="e.g. study, gym, love, party, sleep..."
    )

    if st.button("Find Songs", type="primary"):

        mood = user_input.strip().lower()

        if mood not in keyword_map:

            matches = get_close_matches(mood, keyword_map.keys(), n=5)

            if matches:
                st.warning(f"Did you mean: {', '.join(matches)}?")
            else:
                st.error("Mood not recognized.")

        else:

            cluster = keyword_map[mood]

            recommendations = (
                df[df["cluster"] == cluster]
                .sort_values(by="popularity", ascending=False)
                .head(10)
            )

            if recommendations.empty:
                st.warning("No songs found.")

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

    # ===========================================
    # Recommend by Time
    # ===========================================

    st.divider()

    st.subheader("🕒 Recommend According to Current Time")

    st.info(f"Current Time: {get_time_of_day()}")

    if st.button("Recommend by Time"):

        recommendations = recommend_by_time(df)

        if recommendations.empty:
            st.warning("No songs found.")

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

    # ===========================================
    # Personalized Recommendation
    # ===========================================

    st.divider()

    st.subheader("⭐ Personalized Recommendation")

    if st.button("Recommend From My History"):

        fav = favorite_cluster()

        if fav is None:
            st.warning("No listening history found. Classify a few songs first.")

        else:

            history = pd.read_csv("data/user_history.csv")

            personalized = df.copy()
            personalized["cluster"] = personalized["cluster"].astype(int)

            personalized = personalized[
                personalized["cluster"] == fav
            ]

            # Remove songs already listened to
            played = history["song"]

            personalized = personalized[
                ~personalized["name"].isin(played)
            ]

            # Sort by popularity
            personalized = personalized.sort_values(
                by="popularity",
                ascending=False
            )

            if personalized.empty:
                st.warning("No new songs available.")

            else:

                st.success("Recommended just for you ❤️")

                for _, row in personalized.head(10).iterrows():

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
    tab_spotify, tab_ai, tab_mp3 = st.tabs(
    [
        "Spotify Search",
        "AI Estimate (by name)",
        "Upload MP3"
    ]
)

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
                            if not os.getenv("GEMINI_API_KEY"):
                                st.error("Set GEMINI_API_KEY in .env")
                            else:
                                classify_and_store(
                                    track.name,
                                    track.artists,
                                    "AI + Spotify Search",
                                )

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
            elif not os.getenv("GEMINI_API_KEY"):
                st.warning("Set `GEMINI_API_KEY` in `.env` to use AI feature estimation.")
            else:
                classify_and_store(ai_song, ai_artist or "Unknown", "AI (Gemini)")

   
        # =====================================================
        # Upload MP3
        # =====================================================
    with tab_mp3:

        st.write(
        "Upload an MP3 file. AI will analyze the audio and classify it "
        "using your trained K-Means model."
    )

    uploaded_audio = st.file_uploader(
        "Choose an MP3 file",
        type=["mp3"]
    )

    song_name = st.text_input(
        "Song Name (optional)",
        key="upload_song"
    )

    artist_name = st.text_input(
        "Artist (optional)",
        key="upload_artist"
    )

    if uploaded_audio is not None:

        st.audio(uploaded_audio)

        if st.button("Analyze & Classify MP3"):

            if not os.getenv("GEMINI_API_KEY"):
                st.error("Set GEMINI_API_KEY in .env")

            else:

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".mp3"
                ) as tmp:

                    tmp.write(uploaded_audio.read())

                    audio_path = tmp.name

                with st.spinner("Extracting audio features..."):

                    audio_features = extract_audio_features(audio_path)

                with st.spinner("AI is estimating Spotify parameters..."):

                    classify_and_store(
                        song_name or uploaded_audio.name,
                        artist_name or "Unknown",
                        "MP3 Upload",
                        audio_features
                    )
                    
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