import librosa

def extract_audio_features(path):

    y, sr = librosa.load(path)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    rms = librosa.feature.rms(y=y).mean()

    centroid = librosa.feature.spectral_centroid(
        y=y,
        sr=sr
    ).mean()

    bandwidth = librosa.feature.spectral_bandwidth(
        y=y,
        sr=sr
    ).mean()

    return {
        "tempo": float(tempo),
        "energy": float(rms),
        "brightness": float(centroid),
        "bandwidth": float(bandwidth),
    }