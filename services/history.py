import pandas as pd
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path("data/user_history.csv")


def save_history(user, song, artist, cluster, mood):

    row = {
        "timestamp": datetime.now(),
        "user": user,
        "song": song,
        "artist": artist,
        "cluster": cluster,
        "mood": mood,
    }

    df = pd.DataFrame([row])

    if HISTORY_FILE.exists():
        df.to_csv(HISTORY_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(HISTORY_FILE, index=False)


def load_history():

    if not HISTORY_FILE.exists():
        return pd.DataFrame()

    return pd.read_csv(HISTORY_FILE)


def favorite_cluster():

    history = load_history()

    if history.empty:
        return None

    return history["cluster"].mode()[0]