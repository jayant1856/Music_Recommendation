let currentMode = "dataset";
let selectedMood = "";

const searchInput = document.getElementById("searchInput");
const artistInput = document.getElementById("artistInput");
const searchBtn = document.getElementById("searchBtn");
const resultsArea = document.getElementById("resultsArea");
const resultsCount = document.getElementById("resultsCount");
const modeHint = document.getElementById("modeHint");
const moodFilters = document.getElementById("moodFilters");

const hints = {
  dataset: "Search by song name or artist in the local Spotify dataset (170K+ tracks).",
  ai: "Enter any song name — AI estimates audio features and classifies the mood.",
  spotify: "Search Spotify online for real audio features and mood classification.",
};

const sourceLabels = {
  dataset: "📂 Dataset",
  ai: "🤖 AI",
  spotify: "🎧 Spotify",
};

async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    if (data.total_songs) {
      document.getElementById("statSongs").textContent =
        data.total_songs.toLocaleString();
    }
  } catch (_) {}
}

document.querySelectorAll(".mode-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".mode-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    currentMode = tab.dataset.mode;
    modeHint.textContent = hints[currentMode];

    if (currentMode === "ai") {
      artistInput.classList.remove("hidden");
      searchInput.placeholder = "Song name...";
      moodFilters.classList.add("hidden");
    } else {
      artistInput.classList.add("hidden");
      searchInput.placeholder = "Search song or artist...";
      moodFilters.classList.toggle("hidden", currentMode === "spotify");
    }
  });
});

document.querySelectorAll(".mood-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".mood-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    selectedMood = chip.dataset.mood;
  });
});

function showLoading() {
  resultsArea.innerHTML = `
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <p>Searching...</p>
    </div>`;
  resultsCount.textContent = "";
}

function showError(msg) {
  resultsArea.innerHTML = `
    <div class="error-state">
      <p>⚠️ ${msg}</p>
    </div>`;
  resultsCount.textContent = "";
}

function renderFeatures(features, cardId) {
  const items = Object.entries(features)
    .map(
      ([key, val]) =>
        `<div class="feature-item"><span>${key}:</span> ${Number(val).toFixed(3)}</div>`
    )
    .join("");
  return `
    <button class="feature-toggle" onclick="toggleFeatures('${cardId}')">Show audio features ▾</button>
    <div class="features-panel" id="${cardId}">
      ${items}
    </div>`;
}

function renderCard(song, index) {
  const cardId = `features-${index}`;
  const source = sourceLabels[song.source] || song.source;
  const year = song.year ? `<span>📅 ${song.year}</span>` : "";
  const album = song.album ? `<span>💿 ${song.album}</span>` : "";
  const link = song.external_url
    ? `<a href="${song.external_url}" target="_blank" rel="noopener" style="color:var(--primary);font-size:0.82rem;font-weight:700;">Open in Spotify ↗</a>`
    : "";

  return `
    <div class="song-card">
      <div class="song-card-top">
        <div>
          <div class="song-title">${escapeHtml(song.name)}</div>
          <div class="song-artist">${escapeHtml(song.artists)}</div>
        </div>
        <span class="mood-badge mood-${song.mood}">${song.mood}</span>
      </div>
      <div class="song-meta">
        <span class="source-tag">${source}</span>
        ${song.popularity != null ? `<span>⭐ ${song.popularity}</span>` : ""}
        ${year}${album}
      </div>
      ${song.mood_description ? `<p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:8px;">${song.mood_description}</p>` : ""}
      ${song.features ? renderFeatures(song.features, cardId) : ""}
      ${link}
    </div>`;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function toggleFeatures(id) {
  const panel = document.getElementById(id);
  panel.classList.toggle("open");
  const btn = panel.previousElementSibling;
  btn.textContent = panel.classList.contains("open")
    ? "Hide audio features ▴"
    : "Show audio features ▾";
}

async function doSearch() {
  const query = searchInput.value.trim();
  const artist = artistInput.value.trim();

  if (!query) {
    showError("Please enter a search term.");
    return;
  }

  showLoading();
  searchBtn.disabled = true;

  try {
    let data;

    if (currentMode === "dataset") {
      const params = new URLSearchParams({ q: query, limit: 24 });
      if (selectedMood) params.set("mood", selectedMood);
      const res = await fetch(`/api/search?${params}`);
      data = await res.json();
      if (!res.ok) throw new Error(data.error || "Search failed");
      renderResults(data.results, data.count);
    } else if (currentMode === "ai") {
      const res = await fetch("/api/classify-ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ song: query, artist }),
      });
      data = await res.json();
      if (!res.ok) throw new Error(data.error || "AI classification failed");
      renderResults([data], 1);
    } else {
      const res = await fetch(`/api/search-spotify?q=${encodeURIComponent(query)}`);
      data = await res.json();
      if (!res.ok) throw new Error(data.error || "Spotify search failed");
      renderResults(data.results, data.count);
    }
  } catch (err) {
    showError(err.message);
  } finally {
    searchBtn.disabled = false;
  }
}

function renderResults(results, count) {
  if (!results || results.length === 0) {
    resultsArea.innerHTML = `
      <div class="empty-state">
        <p>No songs found. Try a different search or switch to AI mode.</p>
      </div>`;
    resultsCount.textContent = "0 results";
    return;
  }

  resultsCount.textContent = `${count} result${count !== 1 ? "s" : ""}`;
  resultsArea.innerHTML = `<div class="results-grid">${results.map(renderCard).join("")}</div>`;
}

searchBtn.addEventListener("click", doSearch);
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});
artistInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});

loadStats();
