"""Train and save the K-Means model used for online song classification."""

import json
from pathlib import Path

import joblib
from sklearn.cluster import KMeans

from ml.classifier import MODEL_DIR, METADATA_PATH, find_csv_path, prepare_dataframe
from ml.constants import FEATURES

KMEANS_PATH = MODEL_DIR / "kmeans_model.joblib"


def train_and_save(use_scaling: bool = False) -> Path:
    csv_path = find_csv_path()
    if csv_path is None:
        raise FileNotFoundError(
            "No dataset found. Place spotify_prepared.csv in the project root "
            "(export from your Kaggle notebook)."
        )

    df = prepare_dataframe(csv_path)
    X = df[FEATURES].values

    if use_scaling:
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        joblib.dump(scaler, MODEL_DIR / "scaler.joblib")
    else:
        scaler_path = MODEL_DIR / "scaler.joblib"
        if scaler_path.exists():
            scaler_path.unlink()

    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    kmeans.fit(X)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(kmeans, KMEANS_PATH)

    metadata = {
        "features": FEATURES,
        "n_clusters": 5,
        "uses_scaling": use_scaling,
        "trained_from": csv_path.name,
        "n_samples": len(df),
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Model saved to {KMEANS_PATH}")
    print(f"Trained on {len(df)} songs from {csv_path.name}")
    return KMEANS_PATH


if __name__ == "__main__":
    train_and_save(use_scaling=False)
