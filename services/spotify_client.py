import os
from dataclasses import dataclass

import requests


class SpotifyConfigError(Exception):
    pass


@dataclass
class SpotifyTrack:
    track_id: str
    name: str
    artists: str
    album: str
    popularity: int
    preview_url: str | None
    external_url: str | None


class SpotifyClient:
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self._token: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise SpotifyConfigError(
                "Spotify credentials missing. Set SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET in a .env file."
            )

    def _get_token(self) -> str:
        self._ensure_configured()
        if self._token:
            return self._token

        response = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=15,
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def search_tracks(self, query: str, limit: int = 10) -> list[SpotifyTrack]:
        response = requests.get(
            f"{self.API_BASE}/search",
            headers=self._headers(),
            params={"q": query, "type": "track", "limit": limit},
            timeout=15,
        )
        response.raise_for_status()

        tracks = []
        for item in response.json()["tracks"]["items"]:
            artists = ", ".join(a["name"] for a in item["artists"])
            tracks.append(
                SpotifyTrack(
                    track_id=item["id"],
                    name=item["name"],
                    artists=artists,
                    album=item["album"]["name"],
                    popularity=item.get("popularity", 0),
                    preview_url=item.get("preview_url"),
                    external_url=item.get("external_urls", {}).get("spotify"),
                )
            )
        return tracks

    def get_audio_features(self, track_id: str) -> dict:
        response = requests.get(
            f"{self.API_BASE}/audio-features/{track_id}",
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "acousticness": data["acousticness"],
            "danceability": data["danceability"],
            "energy": data["energy"],
            "instrumentalness": data["instrumentalness"],
            "liveness": data["liveness"],
            "loudness": data["loudness"],
            "speechiness": data["speechiness"],
            "tempo": data["tempo"],
            "valence": data["valence"],
        }

    def get_track_features(self, track_id: str, popularity: int) -> dict:
        features = self.get_audio_features(track_id)
        features["popularity"] = popularity
        return features
