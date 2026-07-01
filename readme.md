# 🎵 Music Recommendation System

## 📌 Overview

This project is a machine learning-based music recommendation system that suggests songs based on the user's mood and the time of day.

## ✨ Features

- Mood-based song recommendations
- **Online song classification** — search Spotify, extract audio parameters, classify with K-Means
- **AI parameter estimation** — estimate features from song name when Spotify is unavailable
- Popularity-based ranking
- Interactive Streamlit web application

## 🛠️ Technologies Used

- Python
- Pandas
- Scikit-learn
- Streamlit
- Kaggle Dataset

## 📂 Project Structure

```
Music_Recommendation/
│── app.py
│── spotify_clustered.csv
│── requirements.txt
│── README.md
```

## 🚀 Installation

1. Clone the repository:

```bash
git clone https://github.com/jayant1856/Music_Recommendation.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment template and add API keys (optional but needed for online classification):

```bash
copy .env.example .env
```

4. Train the classification model (requires `spotify_prepared.csv` in project root):

```bash
python -m ml.train_model
```

5. Run the **presentation website**:

```bash
python server.py
```

Open `http://localhost:5000` in your browser.

6. Or run the Streamlit app:

```bash
streamlit run app.py
```

## 🔍 Online Song Classification

1. Open the **Classify Online** page in the app
2. **Spotify Search** — finds songs and pulls real audio features (acousticness, tempo, valence, etc.)
3. **AI Estimate** — uses OpenAI to guess parameters from song name/artist
4. Your saved K-Means model assigns a mood: Relax, Party, Romantic, Happy, or Rap

### API setup

| Service | Purpose | Get keys |
|---------|---------|----------|
| Spotify | Search songs + audio features | [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) |
| OpenAI | AI feature estimation fallback | [OpenAI API Keys](https://platform.openai.com/api-keys) |

## 📊 Dataset

The project uses a Spotify dataset containing song information such as:

- Song name
- Artist
- Popularity
- Mood cluster
- Time of day

## 🎯 Future Improvements

- Genre-based recommendations
- User authentication
- Playlist generation
- Spotify API integration

## 👨‍💻 Author

Jayant Sharma
