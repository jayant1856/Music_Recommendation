"""
Reusable presentational components for the Streamlit frontend.

Every function here only renders UI (HTML snippets + native Streamlit
widgets for anything interactive). None of them touch the ML model,
Spotify API, or history storage directly — callers pass in already
computed data / already-loaded objects.
"""

from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.theme import COLORS, MOOD_COLORS, MOOD_ICONS

# ---------------------------------------------------------------------------
# Layout primitives
# ---------------------------------------------------------------------------


def sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="logo">🎵</div>
            <div>
                <div class="title">SonicMind AI</div>
                <div class="subtitle">Music Recommendation Engine</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="section-header">
            <div class="icon">{icon}</div>
            <div>
                <h3>{title}</h3>
                {f'<p>{subtitle}</p>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, message: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="icon">{icon}</div>
            <div>{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def skeleton_rows(n: int = 3) -> None:
    st.markdown("".join("<div class='skeleton'></div>" for _ in range(n)), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Hero + landing feature cards
# ---------------------------------------------------------------------------


def hero_section() -> None:
    left, right = st.columns([1.4, 1])
    with left:
        st.markdown(
            """
            <div class="hero-wrap">
                <span class="hero-eyebrow">AI · Machine Learning · Spotify</span>
                <h1 class="hero-title">AI Music Recommendation System</h1>
                <p class="hero-subtitle">
                    Discover music intelligently. Search Spotify, classify any song's
                    mood with AI, and get recommendations tuned to how you listen.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        b1, b2, _ = st.columns([1, 1.3, 2])
        get_started = b1.button("Get Started", type="primary", use_container_width=True)
        explore = b2.button("Explore Features", use_container_width=True)
    with right:
        st.markdown(
            """
            <div class="hero-wrap" style="display:flex;align-items:center;justify-content:center;height:100%;">
                <div class="eq"><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return get_started, explore


FEATURE_CARDS = [
    ("😊", "Mood-based Recommendations", "Type a mood or activity and get songs matched by K-Means clustering."),
    ("🔍", "Spotify Search + AI Classify", "Search any track on Spotify and classify its mood in one click."),
    ("🎧", "MP3 Upload Analysis", "Upload an MP3 — real audio features are extracted and classified by AI."),
    ("❤️", "Personalized For You", "Recommendations shaped by your own listening history."),
]


def feature_card_grid() -> None:
    cols = st.columns(4)
    for col, (icon, title, desc) in zip(cols, FEATURE_CARDS):
        with col:
            st.markdown(
                f"""
                <div class="glass-card feature-card">
                    <div class="icon">{icon}</div>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def stat_cards(stats: list[tuple[str, str]]) -> None:
    cols = st.columns(len(stats))
    for col, (label, value) in zip(cols, stats):
        with col:
            st.markdown(
                f"""
                <div class="glass-card stat-card">
                    <div class="value">{value}</div>
                    <div class="label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Song cards
# ---------------------------------------------------------------------------


def mood_badge_html(mood: str | None) -> str:
    if not mood:
        return ""
    color = MOOD_COLORS.get(mood, COLORS["primary"])
    icon = MOOD_ICONS.get(mood, "🎵")
    return (
        f"<span class='badge' style='background:{color}22;color:{color};'>"
        f"{icon} {mood}</span>"
    )


def song_card(
    name: str,
    artist: str,
    popularity,
    *,
    key: str,
    mood: str | None = None,
    cluster: int | None = None,
    spotify_url: str | None = None,
    preview_url: str | None = None,
) -> None:
    """Renders one song as a card with Like / Save / Open-in-Spotify actions."""

    st.session_state.setdefault("liked_songs", {})
    st.session_state.setdefault("saved_songs", {})

    badges = mood_badge_html(mood)
    if cluster is not None:
        badges += f"<span class='badge badge-cluster'>Cluster {cluster}</span>"
    try:
        pop_val = f"{float(popularity):.0f}"
    except (TypeError, ValueError):
        pop_val = str(popularity)
    badges += f"<span class='badge badge-pop'>⭐ {pop_val}</span>"

    with st.container():
        st.markdown(
            f"""
            <div class="glass-card song-card">
                <div class="song-cover">🎵</div>
                <div class="song-info">
                    <div class="song-name">{name}</div>
                    <div class="song-artist">🎤 {artist}</div>
                    <div class="badge-row">{badges}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)

        with c1:
            if preview_url:
                if st.button("▶ Preview", key=f"prev_{key}", use_container_width=True):
                    st.audio(preview_url)
            elif spotify_url:
                st.link_button("🔗 Open in Spotify", spotify_url, use_container_width=True)
            else:
                st.button("▶ Preview", key=f"prev_{key}", use_container_width=True, disabled=True)

        with c2:
            liked = key in st.session_state["liked_songs"]
            if st.button("❤️ Liked" if liked else "🤍 Like", key=f"like_{key}", use_container_width=True):
                if liked:
                    st.session_state["liked_songs"].pop(key, None)
                else:
                    st.session_state["liked_songs"][key] = {"name": name, "artist": artist, "mood": mood}
                    st.toast(f"Added '{name}' to liked songs", icon="❤️")
                st.rerun()

        with c3:
            saved = key in st.session_state["saved_songs"]
            if st.button("⭐ Saved" if saved else "⭐ Save", key=f"save_{key}", use_container_width=True):
                if saved:
                    st.session_state["saved_songs"].pop(key, None)
                else:
                    st.session_state["saved_songs"][key] = {"name": name, "artist": artist, "mood": mood}
                    st.toast(f"Saved '{name}'", icon="⭐")
                st.rerun()


def song_card_row(row: pd.Series, index: int, prefix: str = "song") -> None:
    """Convenience wrapper for rendering a dataframe row from the trained dataset."""
    spotify_url = None
    track_id = row.get("id") if hasattr(row, "get") else None
    if isinstance(track_id, str) and track_id:
        spotify_url = f"https://open.spotify.com/track/{track_id}"

    mood = None
    cluster = row.get("cluster") if hasattr(row, "get") else None
    if cluster is not None:
        from ml.constants import CLUSTER_MOODS  # local import avoids a hard dependency at module load

        try:
            mood = CLUSTER_MOODS.get(int(cluster))
        except (TypeError, ValueError):
            mood = None

    song_card(
        row["name"],
        row["artists"],
        row["popularity"],
        key=f"{prefix}_{index}_{track_id or row['name']}",
        mood=mood,
        cluster=cluster,
        spotify_url=spotify_url,
    )


# ---------------------------------------------------------------------------
# AI classification result
# ---------------------------------------------------------------------------

FEATURE_DISPLAY = {
    "acousticness": ("Acousticness", 0.0, 1.0, "", 100),
    "danceability": ("Danceability", 0.0, 1.0, "", 100),
    "energy": ("Energy", 0.0, 1.0, "", 100),
    "instrumentalness": ("Instrumentalness", 0.0, 1.0, "", 100),
    "liveness": ("Liveness", 0.0, 1.0, "", 100),
    "speechiness": ("Speechiness", 0.0, 1.0, "", 100),
    "valence": ("Valence (positivity)", 0.0, 1.0, "", 100),
    "loudness": ("Loudness", -60.0, 0.0, " dB", 1),
    "tempo": ("Tempo", 50.0, 220.0, " BPM", 1),
    "popularity": ("Popularity", 0.0, 100.0, "", 1),
}


def feature_progress_bars(features: dict) -> None:
    for key, (label, lo, hi, unit, scale) in FEATURE_DISPLAY.items():
        if key not in features:
            continue
        raw = float(features[key])
        pct = max(0.0, min(1.0, (raw - lo) / (hi - lo))) if hi != lo else 0.0
        display_val = raw if scale == 1 else raw * scale
        st.markdown(
            f"""
            <div class="feat-row">
                <div class="feat-label"><span>{label}</span><span>{display_val:.1f}{unit}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(pct)


def confidence_from_kmeans(features: dict, classifier, feature_order: list[str]) -> float | None:
    """Derives an approximate confidence % from distance to cluster centers.

    Uses the KMeans model's own `transform` (distance to every centroid),
    which is a built-in, unmodified sklearn method — no backend files change.
    Returns None if the model isn't available.
    """
    if classifier is None or not getattr(classifier, "is_ready", False):
        return None
    try:
        row = [[float(features[name]) for name in feature_order]]
        distances = classifier.kmeans.transform(row)[0]
        inv = [1.0 / (d + 1e-6) for d in distances]
        total = sum(inv)
        best = max(inv)
        return round(100 * best / total, 1) if total else None
    except Exception:
        return None


def classification_result_card(result: dict, source: str, confidence: float | None = None) -> None:
    mood = result["mood"]
    icon = MOOD_ICONS.get(mood, "🎵")
    color = MOOD_COLORS.get(mood, COLORS["primary"])

    conf_html = ""
    if confidence is not None:
        conf_html = f"""
        <div style="margin-top:10px;">
            <div class="feat-label" style="display:flex;justify-content:space-between;font-size:12.5px;color:var(--text-muted);">
                <span>Model confidence</span><span style="color:{color};font-family:'JetBrains Mono',monospace;">{confidence}%</span>
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div class="glass-card" style="border-left:4px solid {color};">
            <div style="font-size:34px;">{icon}</div>
            <h3 style="margin:6px 0 2px 0;">Predicted Mood: {mood}</h3>
            <p style="color:var(--text-muted);margin:0;">Cluster {result['cluster']}</p>
            <div class="badge-row">
                <span class="badge" style="background:{color}22;color:{color};">Source: {source}</span>
            </div>
            {conf_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_radar_chart(features: dict, title: str = "Feature Profile") -> go.Figure:
    """0-1 normalized radar chart for a single song's audio features."""
    labels, values = [], []
    for key, (label, lo, hi, _, _) in FEATURE_DISPLAY.items():
        if key not in features:
            continue
        raw = float(features[key])
        norm = max(0.0, min(1.0, (raw - lo) / (hi - lo))) if hi != lo else 0.0
        labels.append(label)
        values.append(norm)

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values + values[:1],
            theta=labels + labels[:1],
            fill="toself",
            fillcolor="rgba(29,185,84,0.25)",
            line=dict(color=COLORS["primary"], width=2),
            name=title,
        )
    )
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], gridcolor=COLORS["border"], tickfont=dict(color=COLORS["text_muted"])),
            angularaxis=dict(gridcolor=COLORS["border"], tickfont=dict(color=COLORS["text"], size=11)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        showlegend=False,
        margin=dict(l=30, r=30, t=30, b=20),
        height=340,
    )
    return fig


# ---------------------------------------------------------------------------
# Analytics charts
# ---------------------------------------------------------------------------


def _base_layout(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="Inter"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
    )
    return fig


def mood_distribution_chart(df: pd.DataFrame) -> go.Figure:
    from ml.constants import CLUSTER_MOODS

    counts = df["cluster"].astype(int).value_counts().sort_index()
    labels = [CLUSTER_MOODS.get(c, str(c)) for c in counts.index]
    colors = [MOOD_COLORS.get(l, COLORS["primary"]) for l in labels]
    fig = go.Figure(
        data=[go.Pie(labels=labels, values=counts.values, hole=0.55, marker=dict(colors=colors), textfont=dict(color="#0B1220"))]
    )
    fig.update_layout(title="Mood Distribution")
    return _base_layout(fig)


def cluster_distribution_chart(df: pd.DataFrame) -> go.Figure:
    counts = df["cluster"].astype(int).value_counts().sort_index()
    fig = go.Figure(
        data=[go.Bar(x=[f"Cluster {c}" for c in counts.index], y=counts.values, marker=dict(color=COLORS["accent"]))]
    )
    fig.update_layout(title="Cluster Distribution", xaxis=dict(gridcolor=COLORS["border"]), yaxis=dict(gridcolor=COLORS["border"]))
    return _base_layout(fig)


def popularity_histogram(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(data=[go.Histogram(x=df["popularity"], marker=dict(color=COLORS["primary"]), nbinsx=25)])
    fig.update_layout(title="Popularity Distribution", xaxis=dict(title="Popularity", gridcolor=COLORS["border"]), yaxis=dict(title="Songs", gridcolor=COLORS["border"]))
    return _base_layout(fig)


def cluster_feature_radar(df: pd.DataFrame, feature_order: list[str]) -> go.Figure:
    """Average feature profile per cluster, useful as a dataset-level radar."""
    from ml.constants import CLUSTER_MOODS

    fig = go.Figure()
    grouped = df.groupby(df["cluster"].astype(int))[feature_order].mean()
    for cluster_id, row in grouped.iterrows():
        vals = []
        for key in feature_order:
            lo, hi = FEATURE_DISPLAY.get(key, (None, 0, 1, "", 1))[1:3]
            v = max(0.0, min(1.0, (row[key] - lo) / (hi - lo))) if hi != lo else 0.0
            vals.append(v)
        label = CLUSTER_MOODS.get(cluster_id, f"Cluster {cluster_id}")
        color = MOOD_COLORS.get(label, COLORS["primary"])
        labels = [FEATURE_DISPLAY.get(k, (k,))[0] for k in feature_order]
        fig.add_trace(
            go.Scatterpolar(
                r=vals + vals[:1],
                theta=labels + labels[:1],
                name=label,
                line=dict(color=color),
            )
        )
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], gridcolor=COLORS["border"], tickfont=dict(color=COLORS["text_muted"])),
            angularaxis=dict(gridcolor=COLORS["border"], tickfont=dict(color=COLORS["text"], size=10)),
        ),
        legend=dict(orientation="h", y=-0.1),
        title="Average Feature Profile by Cluster",
    )
    return _base_layout(fig, height=420)


def recent_search_timeline(history_df: pd.DataFrame) -> go.Figure | None:
    if history_df.empty or "timestamp" not in history_df.columns:
        return None
    hist = history_df.copy()
    hist["timestamp"] = pd.to_datetime(hist["timestamp"], errors="coerce")
    hist = hist.dropna(subset=["timestamp"]).sort_values("timestamp")
    if hist.empty:
        return None
    daily = hist.groupby(hist["timestamp"].dt.date).size().reset_index(name="count")
    fig = go.Figure(
        data=[go.Scatter(x=daily["timestamp"], y=daily["count"], mode="lines+markers", line=dict(color=COLORS["primary"], width=3), marker=dict(size=7))]
    )
    fig.update_layout(title="Classification Activity Over Time", xaxis=dict(gridcolor=COLORS["border"]), yaxis=dict(title="Songs classified", gridcolor=COLORS["border"]))
    return _base_layout(fig)


# ---------------------------------------------------------------------------
# Project / pipeline diagram
# ---------------------------------------------------------------------------


def session_song_list(title: str, icon: str, items: dict) -> None:
    """Renders the liked/saved songs collected in st.session_state (this session only)."""
    section_header(icon, title, "Kept for this browser session only")
    if not items:
        empty_state(icon, f"Nothing here yet — tap {icon} on a song card to add it.")
        return
    for key, info in items.items():
        badge = mood_badge_html(info.get("mood"))
        st.markdown(
            f"""
            <div class="glass-card" style="padding:12px 18px;margin-bottom:8px;">
                <b>{info.get('name')}</b> — {info.get('artist')}
                <div class="badge-row">{badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def pipeline_diagram(steps: list[tuple[str, str, str]]) -> None:
    """steps: list of (icon, title, description)."""
    parts = []
    for i, (icon, title, desc) in enumerate(steps):
        parts.append(
            f"<div class='step'><div class='icon'>{icon}</div><div class='title'>{title}</div><div class='desc'>{desc}</div></div>"
        )
        if i < len(steps) - 1:
            parts.append("<div class='arrow'>➜</div>")
    st.markdown(f"<div class='glass-card pipeline'>{''.join(parts)}</div>", unsafe_allow_html=True)
    