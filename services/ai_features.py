import json
import os
import re

import requests

from ml.constants import FEATURES


class AIFeatureError(Exception):
    pass


FEATURE_RANGES = {
    "acousticness": (0.0, 1.0),
    "danceability": (0.0, 1.0),
    "energy": (0.0, 1.0),
    "instrumentalness": (0.0, 1.0),
    "liveness": (0.0, 1.0),
    "speechiness": (0.0, 1.0),
    "valence": (0.0, 1.0),
    "loudness": (-60.0, 0.0),
    "tempo": (50.0, 220.0),
    "popularity": (0, 100),
}


def _clamp(name: str, value: float) -> float:
    low, high = FEATURE_RANGES[name]
    return max(low, min(high, value))


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def estimate_features_with_ai(
    song_name: str,
    artist: str = "",
    api_key: str | None = None,
) -> dict:
    """Estimate Spotify-style audio features using an LLM."""
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIFeatureError(
            "OpenAI API key missing. Set OPENAI_API_KEY in .env, or use Spotify search."
        )

    prompt = f"""You are a music analysis expert. Estimate Spotify audio feature values for this song.

Song: {song_name}
Artist: {artist or "Unknown"}

Return ONLY valid JSON with these keys (no extra text):
{{
  "acousticness": 0.0-1.0,
  "danceability": 0.0-1.0,
  "energy": 0.0-1.0,
  "instrumentalness": 0.0-1.0,
  "liveness": 0.0-1.0,
  "loudness": -60 to 0 (dB),
  "speechiness": 0.0-1.0,
  "tempo": BPM (50-220),
  "valence": 0.0-1.0,
  "popularity": 0-100
}}

Base estimates on genre, era, and known characteristics of the track."""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        },
        timeout=30,
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    parsed = _parse_json_response(content)

    features = {}
    for name in FEATURES:
        if name not in parsed:
            raise AIFeatureError(f"AI response missing feature: {name}")
        features[name] = _clamp(name, float(parsed[name]))

    return features


def suggest_random_songs_with_ai(
    count: int = 5,
    time_of_day: str = "",
    mood: str = "",
    api_key: str | None = None,
) -> list[dict]:
    """Ask an LLM to suggest random songs with full Spotify-style audio features."""
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIFeatureError(
            "OpenAI API key missing. Set OPENAI_API_KEY in .env to use AI random picks."
        )

    count = max(1, min(count, 10))
    context_parts = []
    if time_of_day:
        context_parts.append(f"time of day: {time_of_day}")
    if mood:
        context_parts.append(f"mood vibe: {mood}")
    context = f" ({', '.join(context_parts)})" if context_parts else ""

    feature_keys = ", ".join(FEATURES)
    prompt = f"""You are a music expert. Suggest {count} diverse, real, well-known songs{context}.
For each song, estimate Spotify audio feature values.

Return ONLY valid JSON (no markdown, no extra text):
{{
  "songs": [
    {{
      "name": "Song Title",
      "artist": "Artist Name",
      "acousticness": 0.0-1.0,
      "danceability": 0.0-1.0,
      "energy": 0.0-1.0,
      "instrumentalness": 0.0-1.0,
      "liveness": 0.0-1.0,
      "loudness": -60 to 0,
      "speechiness": 0.0-1.0,
      "tempo": 50-220,
      "valence": 0.0-1.0,
      "popularity": 0-100
    }}
  ]
}}

Include all keys for every song: {feature_keys}. Pick varied genres and eras."""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.9,
        },
        timeout=45,
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    parsed = _parse_json_response(content)
    songs = parsed.get("songs", [])
    if not songs:
        raise AIFeatureError("AI returned no songs. Try again.")

    results = []
    for item in songs[:count]:
        name = (item.get("name") or "").strip()
        artist = (item.get("artist") or item.get("artists") or "Unknown").strip()
        if not name:
            continue
        features = {}
        for feat in FEATURES:
            if feat not in item:
                raise AIFeatureError(f"AI response missing feature '{feat}' for {name}")
            features[feat] = _clamp(feat, float(item[feat]))
        results.append({"name": name, "artist": artist, "features": features})

    if not results:
        raise AIFeatureError("AI returned no valid songs.")
    return results
