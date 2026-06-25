import streamlit as st
import pandas as pd
from datetime import datetime

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="AI Music Recommendation",
    page_icon="🎵",
    layout="wide"
)

# -------------------------
# CUSTOM CSS
# -------------------------

st.markdown("""
<style>

.stApp{
    background-color:#0F172A;
    color:white;
}

.hero{
    text-align:center;
    padding:40px;
}

.hero h1{
    font-size:60px;
    color:white;
}

.hero p{
    font-size:20px;
    color:#CBD5E1;
}

.song-card{
    background:#1E293B;
    padding:20px;
    border-radius:20px;
    margin-bottom:15px;
    border-left:5px solid #1DB954;
}

.metric-box{
    background:#1E293B;
    padding:20px;
    border-radius:15px;
    text-align:center;
}

.big-button{
    width:100%;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# LOAD DATA
# -------------------------

@st.cache_data
def load_data():
    return pd.read_csv("spotify_prepared.csv")

df = load_data()

# -------------------------
# MOOD MAP
# -------------------------

keyword_map = {
    "Relax":0,
    "Party":1,
    "Romantic":2,
    "Happy":3,
    "Rap":4
}

# -------------------------
# TIME
# -------------------------

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


def recommend_songs(mood):

    cluster = keyword_map[mood]

    df["cluster"] = df["cluster"].astype(int)

    recommendations = (
        df[df["cluster"] == cluster]
        .sort_values(by="popularity", ascending=False)
        .head(10)
    )

    return recommendations

# -------------------------
# SIDEBAR
# -------------------------

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🎵 Recommend",
        "📊 Project",
        "👨‍💻 Developer"
    ]
)

# =====================================================
# HOME
# =====================================================

if page == "🏠 Home":

    st.markdown("""
    <div class='hero'>
        <h1>🎵 AI Music Recommendation System</h1>
        <p>
        Discover songs based on your mood and time of day using Machine Learning
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1,col2,col3,col4 = st.columns(4)

    with col1:
        st.metric("Songs", len(df))

    with col2:
        st.metric("Features", len(df.columns))

    with col3:
        st.metric("Clusters", 5)

    with col4:
        st.metric("Current Time", get_time_of_day())

# =====================================================
# RECOMMEND
# =====================================================

elif page == "🎵 Recommend":

    st.title("🎵 Music Recommendations")

    mood = st.selectbox(
        "Select Your Mood",
        [
            "Relax",
            "Party",
            "Romantic",
            "Happy",
            "Rap"
        ]
    )

    if st.button("Find Songs"):

    with st.spinner("Finding perfect songs..."):

        recommendations = recommend_songs(mood)

    st.write("Mood:", mood)
    st.write("Songs Found:", len(recommendations))

    if recommendations.empty:

        st.error("No songs found for this mood.")

    else:

        st.success(f"{len(recommendations)} songs found!")

        for _, row in recommendations.iterrows():

            st.markdown(
                """
                <div class='song-card'>
                    <h3>🎵 {row['name']}</h3>
                    <p>🎤 {row['artists']}</p>
                    <p>⭐ Popularity: {row['popularity']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <div class='song-card'>
                    <h3>🎵 {row['name']}</h3>
                    <p>🎤 {row['artists']}</p>
                    <p>⭐ Popularity: {row['popularity']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# =====================================================
# PROJECT
# =====================================================

elif page == "📊 Project":

    st.title("📊 About Project")

    st.subheader("Problem Statement")

    st.write("""
    Users often struggle to find songs matching their mood.
    This project uses Machine Learning and clustering techniques
    to recommend suitable music.
    """)

    st.subheader("Machine Learning")

    st.write("""
    - K-Means Clustering
    - Spotify Dataset
    - Mood Classification
    - Popularity-Based Ranking
    """)

# =====================================================
# DEVELOPER
# =====================================================

elif page == "👨‍💻 Developer":

    st.title("👨‍💻 Developer")

    st.markdown("""
    ### Jayant Sharma

    AI & Machine Learning Enthusiast

    #### Skills
    - Python
    - Machine Learning
    - Data Science
    - Streamlit

    #### Project
    AI Music Recommendation System
    """)

    st.markdown(
        "[GitHub](https://github.com/jayant1856)"
    )