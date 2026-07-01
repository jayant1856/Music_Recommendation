import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from ml.constants import CLUSTER_MOODS, FEATURES

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
KMEANS_PATH = MODEL_DIR / "kmeans_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"


class SongClassifier:
    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path or KMEANS_PATH
        self.kmeans: KMeans | None = None
        self.uses_scaling = False
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            return
        self.kmeans = joblib.load(self.model_path)
        if METADATA_PATH.exists():
            metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
            self.uses_scaling = metadata.get("uses_scaling", False)

    @property
    def is_ready(self) -> bool:
        return self.kmeans is not None

    def predict_cluster(self, features: dict) -> int:
        if not self.is_ready:
            raise RuntimeError(
                "Classification model not found. Run: python -m ml.train_model"
            )
        row = [float(features[name]) for name in FEATURES]
        cluster = int(self.kmeans.predict(np.array([row]))[0])
        return cluster

    def predict_mood(self, features: dict) -> str:
        return CLUSTER_MOODS[self.predict_cluster(features)]

    def classify_song(self, features: dict) -> dict:
        cluster = self.predict_cluster(features)
        mood = CLUSTER_MOODS[cluster]
        return {
            "cluster": cluster,
            "mood": mood,
            "features": {name: float(features[name]) for name in FEATURES},
        }


def find_csv_path() -> Path | None:
    root = Path(__file__).resolve().parent.parent
    for name in ("spotify_prepared.csv", "spotify_clustered.csv", "data.csv"):
        path = root / name
        if path.exists():
            return path
    return None


def prepare_dataframe(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.drop_duplicates()
    df[FEATURES] = df[FEATURES].fillna(df[FEATURES].mean(numeric_only=True))
    return df
