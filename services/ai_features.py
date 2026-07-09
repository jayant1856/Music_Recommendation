import json
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ml.constants import FEATURES

load_dotenv()

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

GEMINI_MODEL = "gemini-2.5-flash"

_client: "genai.Client | None" = None


class AIFeatureError(Exception):
    pass


def _get_client(api_key: str | None = None) -> "genai.Client":
    global _client
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise AIFeatureError(
            "Gemini API key missing. Set GEMINI_API_KEY in .env to use AI features."
        )
    if api_key or _client is None:
        _client = genai.Client(api_key=key)
    return _client


def _clamp(name: str, value: float) -> float:
    low, high = FEATURE_RANGES[name]
    return max(low, min(high, value))


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _call_gemini(prompt: str, temperature: float = 0.3, api_key: str | None = None) -> str:
    client = _get_client(api_key)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        raise AIFeatureError(f"AI feature estimation failed: {exc}") from exc
    return response.text or ""


def _normalize_features(raw: dict) -> dict:
    features = {}
    for name in FEATURES:
        if name not in raw:
            raise AIFeatureError(f"AI response missing feature: {name}")
        features[name] = _clamp(name, float(raw[name]))
    return features

def estimate_features_with_ai(
    song_name: str,
    artist: str = "",
    audio_features: dict | None = None,
    api_key: str | None = None,
) -> dict:
    """Estimate Spotify-style audio features using Gemini."""

    audio_info = ""

    if audio_features:
        audio_info = f"""

Real audio analysis extracted from uploaded MP3:

Tempo: {audio_features.get("tempo")}
Energy: {audio_features.get("energy")}
Brightness: {audio_features.get("brightness")}
Bandwidth: {audio_features.get("bandwidth")}

Use these measured values while estimating Spotify features.
"""

    prompt = f"""
You are an expert in Spotify audio analysis.

Estimate Spotify audio features for this song.

Song:
{song_name}

Artist:
{artist or "Unknown"}

{audio_info}

Return ONLY valid JSON.

{{
    "acousticness": 0.0,
    "danceability": 0.0,
    "energy": 0.0,
    "instrumentalness": 0.0,
    "liveness": 0.0,
    "loudness": 0.0,
    "speechiness": 0.0,
    "tempo": 0.0,
    "valence": 0.0,
    "popularity": 0
}}

If audio measurements are provided, use them as the primary evidence.
Otherwise estimate from the song name and artist.
"""

    try:
        content = _call_gemini(prompt, api_key=api_key)
        return _normalize_features(_parse_json_response(content))

    except AIFeatureError:
        raise

    except Exception as exc:
        raise AIFeatureError(
            f"AI feature estimation failed: {exc}"
        ) from exc


def suggest_random_songs_with_ai(
    count: int = 5,
    time_of_day: str = "",
    mood: str = "",
    api_key: str | None = None,
) -> list[dict]:
    """Ask an LLM to suggest random songs with full Spotify-style audio features."""
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

    try:
        content = _call_gemini(prompt, temperature=0.9, api_key=api_key)
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
            results.append(
                {
                    "name": name,
                    "artist": artist,
                    "features": _normalize_features(item),
                }
            )

        if not results:
            raise AIFeatureError("AI returned no valid songs.")
        return results
    except AIFeatureError:
        raise
    except Exception as exc:
        raise AIFeatureError(f"AI random pick failed: {exc}") from exc