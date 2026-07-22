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
    "time_of_day": get_time_of_day(),
    "day_of_week": get_day_of_week()
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

def get_time_of_day():

    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Morning"

    elif 12 <= hour < 17:
        return "Afternoon"

    elif 17 <= hour < 21:
        return "Evening"

    else:
        return "Night"


def get_day_of_week():

    return datetime.now().strftime("%A")

def favorite_time():
    history = load_history()

    if history.empty:
        return None

    if "time_of_day" not in history.columns:
        return None

    values = history["time_of_day"].dropna()

    if values.empty:
        return None

    return values.mode().iloc[0]

    

def favorite_day():
    history = load_history()

    if history.empty:
        return None

    if "day_of_week" not in history.columns:
        return None

    values = history["day_of_week"].dropna()

    if values.empty:
        return None

    return values.mode().iloc[0]