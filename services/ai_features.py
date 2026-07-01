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
