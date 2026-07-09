import os
import tempfile
from datetime import datetime
from difflib import get_close_matches

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ml.classifier import SongClassifier, find_csv_path
from ml.constants import CLUSTER_MOODS, FEATURES, MOOD_DESCRIPTIONS
from services.ai_features import AIFeatureError, estimate_features_with_ai
from services.history import favorite_cluster, load_history, save_history
from services.spotify_client import SpotifyClient, SpotifyConfigError
from utils.audio_features import extract_audio_features

from ui.theme import inject_global_styles, MOOD_ICONS
from ui.components import (
    sidebar_brand,
    section_header,
    empty_state,
    hero_section,
    feature_card_grid,
    stat_cards,
    song_card,
    song_card_row,
    feature_progress_bars,
    confidence_from_kmeans,
    classification_result_card,
    feature_radar_chart,
    mood_distribution_chart,
    cluster_distribution_chart,
    popularity_histogram,
    cluster_feature_radar,
    recent_search_timeline,
    pipeline_diagram,
    session_song_list,
)

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="AI Music Recommendation",
    page_icon="🎵",
    layout="wide",
)

inject_global_styles()

# -------------------------
# DEVELOPER INFO
# (fill in your own links here — empty values are simply hidden)
# -------------------------

DEVELOPER = {
    "name": "Jayant Sharma",
    "role": "AI & Machine Learning Enthusiast",
    "skills": ["Python", "Machine Learning", "Data Science", "Streamlit"],
    "github": "https://github.com/jayant1856",
    "linkedin": "",
    "email": "",
    "resume_url": "",
}

# -------------------------
# DATA / MODEL (unchanged backend logic)
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
    "street": 4,
}

cluster_time_map = {
    0: "Morning",       # Relax
    1: "Evening",       # Party
    2: "Night",         # Romantic
    3: "Afternoon",     # Happy
    4: "Late Evening",  # Rap
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
# HELPERS (unchanged backend logic)
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

    selected_cluster = None
    for cluster, time in cluster_time_map.items():
        if time == current_time:
            selected_cluster = cluster
            break

    dataset = dataset.copy()
    dataset["cluster"] = dataset["cluster"].astype(int)

    recommendations = dataset[dataset["cluster"] == selected_cluster]

    return recommendations.sort_values(by="popularity", ascending=False).head(10)


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
            st.toast(f"Classified '{song_name}' as {result['mood']}", icon=MOOD_ICONS.get(result["mood"], "🎵"))

        except AIFeatureError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Classification failed: {exc}")


# -------------------------
# NAVIGATION
# -------------------------

NAV_ITEMS = [
    "🏠 Home",
    "🎵 Recommend",
    "🔍 Classify Online",
    "❤️ Personalized",
    "📊 Analytics",
    "📁 Project",
    "👨‍💻 Developer",
]

if "page" not in st.session_state:
    st.session_state["page"] = NAV_ITEMS[0]

sidebar_brand()
page = st.sidebar.radio(
    "Navigation",
    NAV_ITEMS,
    index=NAV_ITEMS.index(st.session_state["page"]),
    key="nav_radio",
    label_visibility="collapsed",
)
st.session_state["page"] = page

st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.caption(f"🕒 {get_time_of_day()} · {datetime.now().strftime('%b %d, %Y')}")
if df is not None:
    st.sidebar.caption(f"📀 {len(df):,} songs loaded")

# =====================================================
# HOME
# =====================================================

if page == "🏠 Home":
    get_started, explore = hero_section()
    if get_started:
        st.session_state["page"] = "🎵 Recommend"
        st.rerun()
    if explore:
        st.session_state["page"] = "📁 Project"
        st.rerun()

    st.write("")
    history_df = load_history()
    stat_cards(
        [
            ("Songs in Dataset", f"{len(df):,}" if df is not None else "—"),
            ("Clusters", "5"),
            ("Features", str(len(FEATURES))),
            ("History Entries", f"{len(history_df):,}"),
            ("Time of Day", get_time_of_day()),
        ]
    )

    st.write("")
    section_header("✨", "What you can do here")
    feature_card_grid()

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

    section_header("🎵", "Music Recommendations", "Find songs by mood or by the time of day")

    if df is None:
        st.error("Cannot recommend without spotify_prepared.csv.")
        st.stop()

    st.subheader("😊 Recommend by Mood")

    search_col, btn_col = st.columns([4, 1])
    with search_col:
        user_input = st.text_input(
            "🔍 Enter your mood or activity",
            placeholder="e.g. study, gym, love, party, sleep...",
            label_visibility="visible",
        )
    with btn_col:
        st.write("")
        st.write("")
        find_clicked = st.button("Find Songs", type="primary", use_container_width=True)

    if find_clicked:
        mood = user_input.strip().lower()

        if mood not in keyword_map:
            matches = get_close_matches(mood, keyword_map.keys(), n=5)
            if matches:
                st.warning(f"Did you mean: {', '.join(matches)}?")
            else:
                st.error("Mood not recognized.")
        else:
            with st.spinner("Finding songs that match your mood..."):
                recommendations = recommend_songs(mood, df)

            if recommendations.empty:
                st.warning("No songs found.")
            else:
                st.success(f"{len(recommendations)} songs found!")
                for i, (_, row) in enumerate(recommendations.iterrows()):
                    song_card_row(row, i, prefix="mood")

    st.divider()
    st.subheader("🕒 Recommend According to Current Time")
    st.info(f"Current Time: {get_time_of_day()}")

    if st.button("Recommend by Time"):
        with st.spinner("Curating songs for right now..."):
            recommendations = recommend_by_time(df)

        if recommendations.empty:
            st.warning("No songs found.")
        else:
            st.success(f"{len(recommendations)} songs found!")
            for i, (_, row) in enumerate(recommendations.iterrows()):
                song_card_row(row, i, prefix="time")

# =====================================================
# CLASSIFY ONLINE
# =====================================================

elif page == "🔍 Classify Online":
    section_header("🔍", "Classify Songs Online", "Search Spotify, or let AI estimate audio features")

    if not classifier.is_ready:
        st.error(
            "Classification model not found. Place your CSV in the project root and run:\n\n"
            "`python -m ml.train_model`"
        )
        st.stop()

    spotify = SpotifyClient()
    tab_spotify, tab_ai, tab_mp3 = st.tabs(["Spotify Search", "AI Estimate (by name)", "Upload MP3"])

    with tab_spotify:
        if not spotify.is_configured:
            st.warning(
                "Add `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` to a `.env` file. "
                "Create a free app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)."
            )
        else:
            query = st.text_input("🔍 Search song or artist", placeholder="e.g. Blinding Lights The Weeknd")
            limit = st.slider("Max results", 5, 20, 10)

            if st.button("Search Spotify", type="primary", key="search_spotify"):
                with st.spinner("Searching Spotify..."):
                    try:
                        st.session_state["spotify_results"] = spotify.search_tracks(query, limit=limit)
                    except Exception as exc:
                        st.error(f"Spotify search failed: {exc}")

            results = st.session_state.get("spotify_results", [])
            if results:
                st.subheader("Results")
                for track in results:
                    song_card(
                        track.name,
                        track.artists,
                        track.popularity,
                        key=f"spot_{track.track_id}",
                        spotify_url=track.external_url,
                        preview_url=track.preview_url,
                    )
                    if st.button("🎧 Classify This Track", key=f"classify_{track.track_id}", use_container_width=True):
                        if not os.getenv("GEMINI_API_KEY"):
                            st.error("Set GEMINI_API_KEY in .env")
                        else:
                            classify_and_store(track.name, track.artists, "AI + Spotify Search")
                    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

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

    with tab_mp3:
        st.write(
            "Upload an MP3 file. AI will analyze the audio and classify it "
            "using your trained K-Means model."
        )

        uploaded_audio = st.file_uploader("Choose an MP3 file", type=["mp3"])
        song_name = st.text_input("Song Name (optional)", key="upload_song")
        artist_name = st.text_input("Artist (optional)", key="upload_artist")

        if uploaded_audio is not None:
            st.audio(uploaded_audio)

            if st.button("Analyze & Classify MP3"):
                if not os.getenv("GEMINI_API_KEY"):
                    st.error("Set GEMINI_API_KEY in .env")
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tmp.write(uploaded_audio.read())
                        audio_path = tmp.name

                    with st.spinner("Extracting audio features..."):
                        audio_features = extract_audio_features(audio_path)

                    with st.spinner("AI is estimating Spotify parameters..."):
                        classify_and_store(
                            song_name or uploaded_audio.name,
                            artist_name or "Unknown",
                            "MP3 Upload",
                            audio_features,
                        )

    last = st.session_state.get("last_result")
    if last:
        st.divider()
        section_header(MOOD_ICONS.get(last["mood"], "🎵"), f"{last['song']} — {last['artist']}")

        confidence = confidence_from_kmeans(last["features"], classifier, FEATURES)

        result_col, chart_col = st.columns([1, 1.1])
        with result_col:
            classification_result_card(last, last["source"], confidence)
            with st.expander("View extracted parameters", expanded=True):
                feature_progress_bars(last["features"])
        with chart_col:
            st.plotly_chart(feature_radar_chart(last["features"], last["mood"]), use_container_width=True)

# =====================================================
# PERSONALIZED
# =====================================================

elif page == "❤️ Personalized":
    section_header("❤️", "Personalized For You", "Built from your classification history")

    if df is None:
        st.error("Cannot personalize without spotify_prepared.csv.")
        st.stop()

    history_df = load_history()
    fav = favorite_cluster()

    if fav is None or history_df.empty:
        empty_state("🎧", "No listening history yet. Classify a few songs in <b>Classify Online</b> to unlock personalized recommendations.")
    else:
        fav_mood = CLUSTER_MOODS.get(int(fav), "Unknown")
        fav_artist = (
            history_df["artist"].mode()[0]
            if "artist" in history_df.columns and not history_df["artist"].empty
            else "—"
        )

        stat_cards(
            [
                ("Favorite Mood", f"{MOOD_ICONS.get(fav_mood, '🎵')} {fav_mood}"),
                ("Classifications", f"{len(history_df):,}"),
                ("Top Artist", fav_artist),
            ]
        )

        st.write("")
        col_hist, col_artists = st.columns(2)

        with col_hist:
            section_header("🕘", "Recently Classified")
            recent = history_df.sort_values("timestamp", ascending=False).head(5) if "timestamp" in history_df.columns else history_df.tail(5)
            for _, row in recent.iterrows():
                mood = row.get("mood")
                st.markdown(
                    f"""
                    <div class="glass-card" style="padding:12px 18px;margin-bottom:8px;">
                        <b>{row.get('song', '—')}</b> — {row.get('artist', '—')}
                        <div class="badge-row">{f"<span class='badge' style='background:rgba(29,185,84,0.15);color:#1DB954;'>{MOOD_ICONS.get(mood, '🎵')} {mood}</span>" if mood else ''}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_artists:
            section_header("🎤", "Favorite Artists")
            if "artist" in history_df.columns:
                top_artists = history_df["artist"].value_counts().head(5)
                for artist, count in top_artists.items():
                    st.markdown(
                        f"""
                        <div class="glass-card" style="padding:12px 18px;margin-bottom:8px;display:flex;justify-content:space-between;">
                            <span><b>{artist}</b></span><span style="color:var(--text-muted);">{count} plays</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.divider()
        section_header("🎁", "Recommended Just For You")

        history = load_history()
        personalized = df.copy()
        personalized["cluster"] = personalized["cluster"].astype(int)
        personalized = personalized[personalized["cluster"] == fav]

        played = history["song"] if "song" in history.columns else pd.Series(dtype=str)
        personalized = personalized[~personalized["name"].isin(played)]
        personalized = personalized.sort_values(by="popularity", ascending=False)

        if personalized.empty:
            empty_state("🎵", "No new songs available in your favorite mood right now.")
        else:
            for i, (_, row) in enumerate(personalized.head(10).iterrows()):
                song_card_row(row, i, prefix="personal")

    st.divider()
    like_col, save_col = st.columns(2)
    with like_col:
        session_song_list("Liked Songs", "❤️", st.session_state.get("liked_songs", {}))
    with save_col:
        session_song_list("Saved Songs", "⭐", st.session_state.get("saved_songs", {}))

# =====================================================
# ANALYTICS
# =====================================================

elif page == "📊 Analytics":
    section_header("📊", "Analytics", "How the dataset and your activity break down")

    if df is None:
        st.error("Cannot show analytics without spotify_prepared.csv.")
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(mood_distribution_chart(df), use_container_width=True)
    with c2:
        st.plotly_chart(cluster_distribution_chart(df), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(popularity_histogram(df), use_container_width=True)
    with c4:
        history_df = load_history()
        timeline = recent_search_timeline(history_df)
        if timeline is not None:
            st.plotly_chart(timeline, use_container_width=True)
        else:
            empty_state("📈", "Classify songs over time to see your activity timeline here.")

    st.plotly_chart(cluster_feature_radar(df, FEATURES), use_container_width=True)

# =====================================================
# PROJECT
# =====================================================

elif page == "📁 Project":
    section_header("📁", "About This Project")

    st.markdown(
        """
        <div class="glass-card" style="margin-bottom:20px;">
            <h4>🧩 Overview</h4>
            <p style="color:var(--text-muted);">
                Users often struggle to find songs matching their mood. This project uses
                K-Means clustering on Spotify audio features to group and recommend music,
                with an AI fallback (Gemini) for songs that aren't in the dataset.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_header("🔬", "Machine Learning Pipeline")
    pipeline_diagram(
        [
            ("🔍", "Spotify Search", "Look up any track"),
            ("🎚️", "Feature Extraction", "Audio / AI estimation"),
            ("🤖", "K-Means Model", "Predict cluster"),
            ("🎭", "Mood Mapping", "Cluster → mood label"),
            ("🎵", "Recommendation", "Ranked by popularity"),
        ]
    )

    st.write("")
    col_tech, col_data = st.columns(2)
    with col_tech:
        section_header("🛠️", "Technologies Used")
        techs = ["Streamlit", "Python", "scikit-learn", "Pandas", "NumPy", "Plotly", "Gemini AI", "Spotify API", "Librosa"]
        st.markdown("".join(f"<span class='skill-chip'>{t}</span>" for t in techs), unsafe_allow_html=True)

    with col_data:
        section_header("🗂️", "Dataset & Features")
        if df is not None:
            st.markdown(f"<p style='color:var(--text-muted);'>{len(df):,} songs · {len(FEATURES)} features</p>", unsafe_allow_html=True)
        st.markdown("".join(f"<span class='skill-chip'>{f}</span>" for f in FEATURES), unsafe_allow_html=True)

    st.write("")
    section_header("🎭", "Mood Clusters")
    cols = st.columns(len(CLUSTER_MOODS))
    for col, (cluster_id, mood) in zip(cols, CLUSTER_MOODS.items()):
        with col:
            st.markdown(
                f"""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:26px;">{MOOD_ICONS.get(mood, '🎵')}</div>
                    <h4 style="margin:8px 0 4px 0;">{mood}</h4>
                    <p style="color:var(--text-muted);font-size:12.5px;">Cluster {cluster_id}</p>
                    <p style="color:var(--text-muted);font-size:12.5px;">{MOOD_DESCRIPTIONS[mood]}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =====================================================
# DEVELOPER
# =====================================================

elif page == "👨‍💻 Developer":
    section_header("👨‍💻", "Developer")

    left, right = st.columns([1, 2])
    with left:
        initials = "".join(w[0] for w in DEVELOPER["name"].split()[:2]).upper()
        st.markdown(
            f"""
            <div class="glass-card" style="text-align:center;">
                <div class="dev-avatar">{initials}</div>
                <h3 style="margin:0;">{DEVELOPER['name']}</h3>
                <p style="color:var(--text-muted);margin-top:2px;">{DEVELOPER['role']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f"""
            <div class="glass-card">
                <h4>Skills</h4>
                <div>{''.join(f"<span class='skill-chip'>{s}</span>" for s in DEVELOPER['skills'])}</div>
                <h4 style="margin-top:18px;">Project</h4>
                <p style="color:var(--text-muted);">AI Music Recommendation System</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        link_cols = st.columns(4)
        links = [
            ("GitHub", DEVELOPER["github"]),
            ("LinkedIn", DEVELOPER["linkedin"]),
            ("Email", f"mailto:{DEVELOPER['email']}" if DEVELOPER["email"] else ""),
            ("Resume", DEVELOPER["resume_url"]),
        ]
        for col, (label, url) in zip(link_cols, links):
            with col:
                if url:
                    st.link_button(label, url, use_container_width=True)
                else:
                    st.button(label, disabled=True, use_container_width=True, help=f"Add your {label} link in DEVELOPER dict")