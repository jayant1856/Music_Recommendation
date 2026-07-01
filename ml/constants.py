FEATURES = [
    "acousticness",
    "danceability",
    "energy",
    "instrumentalness",
    "liveness",
    "loudness",
    "speechiness",
    "tempo",
    "valence",
    "popularity",
]

CLUSTER_MOODS = {
    0: "Relax",
    1: "Party",
    2: "Romantic",
    3: "Happy",
    4: "Rap",
}

MOOD_DESCRIPTIONS = {
    "Relax": "Low energy, high acousticness, slower tempo",
    "Party": "High danceability, high energy, loud",
    "Romantic": "High valence, moderate tempo",
    "Happy": "High valence, upbeat tempo",
    "Rap": "High speechiness, strong beat",
}
