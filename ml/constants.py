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

TIME_OF_DAY_MOODS = {
    "Morning": ["Happy", "Relax"],
    "Afternoon": ["Happy", "Party"],
    "Evening": ["Romantic", "Relax"],
    "Night": ["Relax", "Rap"],
}

TIME_DESCRIPTIONS = {
    "Morning": "Upbeat and calm tracks to start your day",
    "Afternoon": "Energetic songs to keep you going",
    "Evening": "Romantic and mellow vibes to wind down",
    "Night": "Chill and late-night beats",
}
