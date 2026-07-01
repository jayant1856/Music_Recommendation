"""Flask server for the internship presentation website."""

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from ml.classifier import SongClassifier, find_csv_path, prepare_dataframe
from ml.constants import (
    CLUSTER_MOODS,
    FEATURES,
    MOOD_DESCRIPTIONS,
    TIME_DESCRIPTIONS,
    TIME_OF_DAY_MOODS,
)
from services.ai_features import (
    AIFeatureError,
    estimate_features_with_ai,
    suggest_random_songs_with_ai,
)
from services.spotify_client import SpotifyClient

load_dotenv()

app = Flask(__name__)
CORS(app)

_df: pd.DataFrame | None = None
_classifier: SongClassifier | None = None


def get_dataframe() -> pd.DataFrame:
    global _df
    if _df is None:
        csv_path = find_csv_path()
        if csv_path is None:
            raise FileNotFoundError("spotify_prepared.csv not found")
        _df = prepare_dataframe(csv_path)
        _df["cluster"] = _df["cluster"].astype(int)
        _df["mood"] = _df["cluster"].map(CLUSTER_MOODS)
        _df["search_text"] = (
            _df["name"].astype(str) + " " + _df["artists"].astype(str)
        ).str.lower()
    return _df


def get_classifier() -> SongClassifier:
    global _classifier
    if _classifier is None:
        _classifier = SongClassifier()
    return _classifier


def get_time_of_day(hour: int | None = None) -> str:
    if hour is None:
        hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Morning"
    if 12 <= hour < 17:
        return "Afternoon"
    if 17 <= hour < 21:
        return "Evening"
    return "Night"


def song_row_to_dict(row) -> dict:
    return {
        "name": row["name"],
        "artists": row["artists"],
        "popularity": int(row["popularity"]),
        "cluster": int(row["cluster"]),
        "mood": CLUSTER_MOODS[int(row["cluster"])],
        "year": int(row["year"]) if pd.notna(row.get("year")) else None,
        "source": "dataset",
        "features": {f: round(float(row[f]), 4) for f in FEATURES},
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/stats")
def stats():
    try:
        df = get_dataframe()
        mood_counts = df["mood"].value_counts().to_dict()
        return jsonify(
            {
                "total_songs": len(df),
                "features": len(FEATURES),
                "clusters": len(CLUSTER_MOODS),
                "mood_counts": mood_counts,
                "current_time_of_day": get_time_of_day(),
                "time_of_day_moods": {
                    k: {"moods": v, "description": TIME_DESCRIPTIONS[k]}
                    for k, v in TIME_OF_DAY_MOODS.items()
                },
                "moods": [
                    {
                        "id": k,
                        "name": v,
                        "description": MOOD_DESCRIPTIONS[v],
                    }
                    for k, v in CLUSTER_MOODS.items()
                ],
            }
        )
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/recommend")
def recommend():
    mood = request.args.get("mood", "").strip()
    limit = min(int(request.args.get("limit", 10)), 50)

    if mood not in CLUSTER_MOODS.values():
        return jsonify({"error": "Select a valid mood: Relax, Party, Romantic, Happy, Rap"}), 400

    try:
        df = get_dataframe()
        cluster_id = next(k for k, v in CLUSTER_MOODS.items() if v == mood)
        results = (
            df[df["cluster"] == cluster_id]
            .sort_values("popularity", ascending=False)
            .head(limit)
        )
        return jsonify(
            {
                "mood": mood,
                "count": len(results),
                "results": [song_row_to_dict(row) for _, row in results.iterrows()],
            }
        )
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/recommend-time")
def recommend_time():
    time_of_day = request.args.get("time_of_day", "").strip() or get_time_of_day()
    limit = min(int(request.args.get("limit", 10)), 50)

    if time_of_day not in TIME_OF_DAY_MOODS:
        valid = ", ".join(TIME_OF_DAY_MOODS.keys())
        return jsonify({"error": f"Invalid time. Use: {valid}"}), 400

    try:
        df = get_dataframe()
        moods = TIME_OF_DAY_MOODS[time_of_day]
        cluster_ids = [
            next(k for k, v in CLUSTER_MOODS.items() if v == mood) for mood in moods
        ]
        results = (
            df[df["cluster"].isin(cluster_ids)]
            .sort_values("popularity", ascending=False)
            .head(limit)
        )

        return jsonify(
            {
                "time_of_day": time_of_day,
                "description": TIME_DESCRIPTIONS[time_of_day],
                "suggested_moods": moods,
                "count": len(results),
                "results": [song_row_to_dict(row) for _, row in results.iterrows()],
            }
        )
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/search")
def search_dataset():
    query = request.args.get("q", "").strip()
    mood = request.args.get("mood", "").strip()
    limit = min(int(request.args.get("limit", 20)), 50)

    if not query and not mood:
        return jsonify({"error": "Enter a search term or select a mood"}), 400

    try:
        df = get_dataframe()
        results = df

        if query:
            q = query.lower()
            results = results[results["search_text"].str.contains(q, na=False)]

        if mood and mood in CLUSTER_MOODS.values():
            cluster_id = next(k for k, v in CLUSTER_MOODS.items() if v == mood)
            results = results[results["cluster"] == cluster_id]

        results = results.sort_values("popularity", ascending=False).head(limit)

        return jsonify(
            {
                "query": query,
                "mood": mood,
                "count": len(results),
                "results": [song_row_to_dict(row) for _, row in results.iterrows()],
            }
        )
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/classify-ai", methods=["POST"])
def classify_ai():
    data = request.get_json(silent=True) or {}
    song = (data.get("song") or "").strip()
    artist = (data.get("artist") or "").strip()

    if not song:
        return jsonify({"error": "Song name is required"}), 400

    classifier = get_classifier()
    if not classifier.is_ready:
        return jsonify(
            {"error": "Model not trained. Run: python -m ml.train_model"}
        ), 503

    try:
        features = estimate_features_with_ai(song, artist)
        result = classifier.classify_song(features)
        return jsonify(
            {
                "name": song,
                "artists": artist or "Unknown",
                "source": "ai",
                "cluster": result["cluster"],
                "mood": result["mood"],
                "mood_description": MOOD_DESCRIPTIONS[result["mood"]],
                "features": result["features"],
            }
        )
    except AIFeatureError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"AI classification failed: {exc}"}), 500


@app.route("/api/ai-random", methods=["POST"])
def ai_random():
    data = request.get_json(silent=True) or {}
    count = min(int(data.get("count", 5)), 10)
    time_of_day = (data.get("time_of_day") or "").strip()
    mood = (data.get("mood") or "").strip()

    classifier = get_classifier()
    if not classifier.is_ready:
        return jsonify(
            {"error": "Model not trained. Run: python -m ml.train_model"}
        ), 503

    try:
        suggestions = suggest_random_songs_with_ai(
            count=count,
            time_of_day=time_of_day or get_time_of_day(),
            mood=mood,
        )
        results = []
        for song in suggestions:
            classified = classifier.classify_song(song["features"])
            results.append(
                {
                    "name": song["name"],
                    "artists": song["artist"],
                    "source": "ai-random",
                    "cluster": classified["cluster"],
                    "mood": classified["mood"],
                    "mood_description": MOOD_DESCRIPTIONS[classified["mood"]],
                    "features": classified["features"],
                    "popularity": int(classified["features"]["popularity"]),
                }
            )
        return jsonify(
            {
                "count": len(results),
                "time_of_day": time_of_day or get_time_of_day(),
                "results": results,
            }
        )
    except AIFeatureError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"AI random pick failed: {exc}"}), 500


@app.route("/api/search-spotify")
def search_spotify():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Enter a search term"}), 400

    client = SpotifyClient()
    if not client.is_configured:
        return jsonify(
            {
                "error": "Spotify not configured. Add credentials to .env file.",
            }
        ), 503

    classifier = get_classifier()
    if not classifier.is_ready:
        return jsonify({"error": "Model not trained"}), 503

    try:
        tracks = client.search_tracks(query, limit=10)
        results = []
        for track in tracks:
            features = client.get_track_features(track.track_id, track.popularity)
            classified = classifier.classify_song(features)
            results.append(
                {
                    "name": track.name,
                    "artists": track.artists,
                    "album": track.album,
                    "popularity": track.popularity,
                    "external_url": track.external_url,
                    "source": "spotify",
                    "cluster": classified["cluster"],
                    "mood": classified["mood"],
                    "mood_description": MOOD_DESCRIPTIONS[classified["mood"]],
                    "features": classified["features"],
                }
            )
        return jsonify({"query": query, "count": len(results), "results": results})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting website at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
