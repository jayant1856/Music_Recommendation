const MOOD_EMOJIS = { Relax: "😌", Party: "🎉", Romantic: "💕", Happy: "😊", Rap: "🎤" };
const MOOD_COLORS = { Relax: "#30d158", Party: "#ff375f", Romantic: "#ff9f0a", Happy: "#0a84ff", Rap: "#bf5af2" };
const SOURCE_LABELS = { dataset: "📂 Dataset", ai: "🤖 AI", "ai-random": "🎲 AI Random", spotify: "🎧 Spotify" };

const HINTS = {
  dataset: "Search by song name or artist in the local Spotify dataset.",
  ai: "Enter any song name — AI estimates audio features and classifies the mood.",
  "ai-random": "AI picks random songs and estimates all 10 audio parameters like the dataset.",
  spotify: "Search Spotify online for real audio features and mood classification.",
};

let currentPage = "home";
let currentMode = "dataset";
let selectedMood = "";
let filterMood = "";
let playlist = [];
let trackIndex = 0;
let isPlaying = false;
let discoverMood = null;
let selectedTime = null;
let statsData = null;

/* ── Time ── */
function getTimeOfDay() {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) return "Morning";
  if (h >= 12 && h < 17) return "Afternoon";
  if (h >= 17 && h < 21) return "Evening";
  return "Night";
}

function updateTime() {
  const tod = getTimeOfDay();
  const t = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  document.getElementById("timeDisplay").textContent = t;
  document.getElementById("greetingTime").textContent = tod;
  document.getElementById("statTime").textContent = tod;
  document.getElementById("pageTitle").innerHTML = `Good <span id="greetingTime">${tod}</span>`;
}

setInterval(updateTime, 30000);
updateTime();

/* ── Navigation ── */
function navigate(page) {
  currentPage = page;
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
  document.getElementById(`page-${page}`).classList.add("active");
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add("active");
  document.getElementById("main").scrollTop = 0;
}

document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => navigate(btn.dataset.page));
});

document.querySelectorAll("[data-goto]").forEach((btn) => {
  btn.addEventListener("click", () => navigate(btn.dataset.goto));
});

/* ── Stats ── */
async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    statsData = await res.json();
    if (statsData.total_songs) {
      document.getElementById("statSongs").textContent = statsData.total_songs.toLocaleString();
      document.getElementById("sidebarStats").textContent =
        `${statsData.total_songs.toLocaleString()} songs · K-Means`;
    }
    if (statsData.moods) {
      const tbody = document.getElementById("clusterTableBody");
      tbody.innerHTML = statsData.moods
        .map(
          (m) => `
        <tr>
          <td><span class="dot" style="background:${MOOD_COLORS[m.name]}"></span>${m.id}</td>
          <td>${m.name}</td>
          <td>${m.description}</td>
        </tr>`
        )
        .join("");
    }
    updateTimeRecCard();
  } catch (_) {
    document.getElementById("sidebarStats").textContent = "Dataset not loaded";
    document.getElementById("statSongs").textContent = "—";
  }
}

function updateTimeRecCard() {
  if (!statsData?.time_of_day_moods) return;
  const tod = statsData.current_time_of_day || getTimeOfDay();
  const info = statsData.time_of_day_moods[tod];
  if (!info) return;

  document.getElementById("timeRecDesc").textContent = info.description;
  document.getElementById("timeMoodTags").innerHTML = info.moods
    .map((m) => `<span class="time-mood-tag">${MOOD_EMOJIS[m]} ${m}</span>`)
    .join("");

  selectedTime = tod;
  document.querySelectorAll("#timePickerRow .time-btn").forEach((btn) => {
    btn.classList.toggle("selected", btn.dataset.time === tod);
  });
  const timeInfo = statsData.time_of_day_moods[tod];
  if (timeInfo) {
    document.getElementById("timePickerDesc").textContent = timeInfo.description;
  }
}

/* ── Song rendering ── */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function renderSongList(songs, containerId, mood) {
  const c = document.getElementById(containerId);
  c.innerHTML = songs
    .map((s, i) => {
      const pop = Math.min(100, Math.max(0, s.popularity || 0));
      const emoji = MOOD_EMOJIS[mood || s.mood] || "🎵";
      return `
      <div class="song-row" data-idx="${i}">
        <div>
          <div class="song-num">${i + 1}</div>
          <div class="song-play"><svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg></div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;min-width:0">
          <div class="song-art">${emoji}</div>
          <div>
            <div class="song-title">${escapeHtml(s.name)}</div>
            <div class="song-artist">${escapeHtml(s.artists)}</div>
          </div>
        </div>
        <div class="song-meta">
          <div class="song-pop">${pop}</div>
          <div class="pop-bar"><div class="pop-fill" style="width:${pop}%"></div></div>
        </div>
      </div>`;
    })
    .join("");

  c.querySelectorAll(".song-row").forEach((row) => {
    row.addEventListener("click", () => showNowPlaying(parseInt(row.dataset.idx, 10)));
  });
}

function renderFeatures(features, cardId) {
  const items = Object.entries(features)
    .map(([k, v]) => `<div class="feature-item"><span>${k}:</span> ${Number(v).toFixed(3)}</div>`)
    .join("");
  return `
    <button class="feature-toggle" data-target="${cardId}">Show audio features ▾</button>
    <div class="features-panel" id="${cardId}">${items}</div>`;
}

function renderClassifyCard(song, index) {
  const cardId = `feat-${index}`;
  const source = SOURCE_LABELS[song.source] || song.source;
  const link = song.external_url
    ? `<a class="spotify-link" href="${song.external_url}" target="_blank" rel="noopener">Open in Spotify ↗</a>`
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
      <div class="card-meta">
        <span class="source-tag">${source}</span>
        ${song.popularity != null ? `<span>⭐ ${song.popularity}</span>` : ""}
        ${song.year ? `<span>📅 ${song.year}</span>` : ""}
        ${song.album ? `<span>💿 ${escapeHtml(song.album)}</span>` : ""}
      </div>
      ${song.mood_description ? `<p class="mood-desc">${song.mood_description}</p>` : ""}
      ${song.features ? renderFeatures(song.features, cardId) : ""}
      ${link}
    </div>`;
}

function bindFeatureToggles(container) {
  container.querySelectorAll(".feature-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const panel = document.getElementById(btn.dataset.target);
      panel.classList.toggle("open");
      btn.textContent = panel.classList.contains("open")
        ? "Hide audio features ▴"
        : "Show audio features ▾";
    });
  });
}

/* ── Loading / error states ── */
function showLoading(containerId) {
  document.getElementById(containerId).innerHTML = `
    <div class="loading-state"><div class="loading-spinner"></div><p>Loading…</p></div>`;
}

function showError(containerId, msg) {
  document.getElementById(containerId).innerHTML = `
    <div class="error-state"><p>⚠️ ${escapeHtml(msg)}</p></div>`;
}

/* ── Recommendations ── */
async function fetchRecommendations(mood, limit = 10) {
  const res = await fetch(`/api/recommend?mood=${encodeURIComponent(mood)}&limit=${limit}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Recommendation failed");
  return data;
}

async function fetchTimeRecommendations(timeOfDay, limit = 10) {
  const res = await fetch(
    `/api/recommend-time?time_of_day=${encodeURIComponent(timeOfDay)}&limit=${limit}`
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Time recommendation failed");
  return data;
}

async function playForTime(timeOfDay, containerId, titleEl, countEl) {
  if (containerId === "homeSongList") {
    document.getElementById("homeResults").classList.remove("hidden");
    showLoading("homeSongList");
  } else {
    showLoading("discoverResults");
  }

  try {
    const data = await fetchTimeRecommendations(timeOfDay);
    playlist = data.results;
    discoverMood = null;

    if (titleEl) {
      document.getElementById(titleEl).textContent = `${timeOfDay} Picks`;
    }
    if (countEl) {
      document.getElementById(countEl).textContent = `${data.count} tracks · ${data.suggested_moods.join(", ")}`;
    }

    if (containerId === "discoverResults") {
      document.getElementById("discoverResults").innerHTML = `
        <div class="section-header">
          <h2>${timeOfDay} Recommendations</h2>
          <span class="results-count">${data.count} tracks · ${data.suggested_moods.join(", ")}</span>
        </div>
        <p class="time-picker-desc" style="margin-bottom:16px">${data.description}</p>
        <div class="song-list" id="discoverSongList"></div>`;
      renderSongList(playlist, "discoverSongList", data.suggested_moods[0]);
    } else {
      renderSongList(playlist, containerId, data.suggested_moods[0]);
    }

    if (playlist.length) showNowPlaying(0);
  } catch (err) {
    const errTarget = containerId === "discoverResults" ? "discoverResults" : containerId;
    showError(errTarget, err.message);
  }
}

async function quickMood(mood) {
  document.querySelectorAll("#homeMoodGrid .mood-tile").forEach((t) => t.classList.remove("selected"));
  document.querySelector(`#homeMoodGrid [data-mood="${mood}"]`)?.classList.add("selected");

  showLoading("homeSongList");
  document.getElementById("homeResults").classList.remove("hidden");
  document.getElementById("homeResultsTitle").textContent = `Top ${mood} Picks`;

  try {
    const data = await fetchRecommendations(mood);
    playlist = data.results;
    document.getElementById("homeResultsCount").textContent = `${data.count} tracks`;
    renderSongList(playlist, "homeSongList", mood);
    if (playlist.length) showNowPlaying(0);
  } catch (err) {
    showError("homeSongList", err.message);
  }
}

document.querySelectorAll("#homeMoodGrid .mood-tile").forEach((tile) => {
  tile.addEventListener("click", () => quickMood(tile.dataset.mood));
});

document.getElementById("playForNowBtn").addEventListener("click", () => {
  const tod = statsData?.current_time_of_day || getTimeOfDay();
  document.getElementById("homeResultsTitle").textContent = `${tod} Picks`;
  playForTime(tod, "homeSongList", "homeResultsTitle", "homeResultsCount");
});

/* ── Discover page ── */
document.querySelectorAll(".discover-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".discover-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const isTime = tab.dataset.discover === "time";
    document.getElementById("discoverMoodPanel").classList.toggle("hidden", isTime);
    document.getElementById("discoverTimePanel").classList.toggle("hidden", !isTime);
  });
});

document.querySelectorAll("#timePickerRow .time-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#timePickerRow .time-btn").forEach((b) => b.classList.remove("selected"));
    btn.classList.add("selected");
    selectedTime = btn.dataset.time;
    const info = statsData?.time_of_day_moods?.[selectedTime];
    document.getElementById("timePickerDesc").textContent = info?.description || "";
  });
});

document.getElementById("findTimeBtn").addEventListener("click", () => {
  const tod = selectedTime || statsData?.current_time_of_day || getTimeOfDay();
  playForTime(tod, "discoverResults");
});
document.querySelectorAll("#discoverMoodRow .mood-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#discoverMoodRow .mood-btn").forEach((b) => b.classList.remove("selected"));
    btn.classList.add("selected");
    discoverMood = btn.dataset.mood;
    const findBtn = document.getElementById("findBtn");
    findBtn.disabled = false;
    findBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      Play ${discoverMood} Music`;
  });
});

document.getElementById("findBtn").addEventListener("click", async () => {
  if (!discoverMood) return;
  showLoading("discoverResults");

  try {
    const data = await fetchRecommendations(discoverMood);
    playlist = data.results;
    document.getElementById("discoverResults").innerHTML = `
      <div class="section-header">
        <h2>Top ${discoverMood} Songs</h2>
        <span class="results-count">${data.count} tracks</span>
      </div>
      <div class="song-list" id="discoverSongList"></div>`;
    renderSongList(playlist, "discoverSongList", discoverMood);
    if (playlist.length) showNowPlaying(0);
  } catch (err) {
    showError("discoverResults", err.message);
  }
});

/* ── Classify page ── */
document.querySelectorAll(".mode-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".mode-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    currentMode = tab.dataset.mode;

    const artistInput = document.getElementById("artistInput");
    const moodFilters = document.getElementById("moodFilters");
    const searchInput = document.getElementById("searchInput");
    const searchRow = document.getElementById("searchRow");
    const aiRandomPanel = document.getElementById("aiRandomPanel");
    const modeHint = document.getElementById("modeHint");

    if (currentMode === "ai-random") {
      searchRow.classList.add("hidden");
      aiRandomPanel.classList.remove("hidden");
      moodFilters.classList.add("hidden");
      modeHint.classList.add("hidden");
    } else {
      searchRow.classList.remove("hidden");
      aiRandomPanel.classList.add("hidden");
      modeHint.classList.remove("hidden");
      modeHint.textContent = HINTS[currentMode];

      if (currentMode === "ai") {
        artistInput.classList.remove("hidden");
        searchInput.placeholder = "Song name…";
        moodFilters.classList.add("hidden");
      } else {
        artistInput.classList.add("hidden");
        searchInput.placeholder = "Search song or artist…";
        moodFilters.classList.toggle("hidden", currentMode === "spotify");
      }
    }
  });
});

document.querySelectorAll(".mood-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".mood-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    filterMood = chip.dataset.mood;
  });
});

async function doAiRandom() {
  const btn = document.getElementById("aiRandomBtn");
  showLoading("classifyResults");
  btn.disabled = true;

  try {
    const res = await fetch("/api/ai-random", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        count: parseInt(document.getElementById("aiRandomCount").value, 10),
        time_of_day: document.getElementById("aiRandomTime").value,
        mood: document.getElementById("aiRandomMood").value,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "AI random pick failed");
    renderClassifyResults(data.results, data.count, true);
  } catch (err) {
    showError("classifyResults", err.message);
  } finally {
    btn.disabled = false;
  }
}

async function doSearch() {
  const query = document.getElementById("searchInput").value.trim();
  const artist = document.getElementById("artistInput").value.trim();
  const searchBtn = document.getElementById("searchBtn");

  if (currentMode === "ai-random") {
    return doAiRandom();
  }

  if (!query) {
    showError("classifyResults", "Please enter a search term.");
    return;
  }

  showLoading("classifyResults");
  searchBtn.disabled = true;

  try {
    let data;
    if (currentMode === "dataset") {
      const params = new URLSearchParams({ q: query, limit: 24 });
      if (filterMood) params.set("mood", filterMood);
      const res = await fetch(`/api/search?${params}`);
      data = await res.json();
      if (!res.ok) throw new Error(data.error || "Search failed");
      renderClassifyResults(data.results, data.count);
    } else if (currentMode === "ai") {
      const res = await fetch("/api/classify-ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ song: query, artist }),
      });
      data = await res.json();
      if (!res.ok) throw new Error(data.error || "AI classification failed");
      renderClassifyResults([data], 1);
    } else {
      const res = await fetch(`/api/search-spotify?q=${encodeURIComponent(query)}`);
      data = await res.json();
      if (!res.ok) throw new Error(data.error || "Spotify search failed");
      renderClassifyResults(data.results, data.count);
    }
  } catch (err) {
    showError("classifyResults", err.message);
  } finally {
    searchBtn.disabled = false;
  }
}

function renderClassifyResults(results, count, featuresOpen = false) {
  const container = document.getElementById("classifyResults");
  if (!results || !results.length) {
    container.innerHTML = `
      <div class="empty-state"><div class="empty-icon">🔍</div><p>No songs found. Try a different search.</p></div>`;
    return;
  }
  container.innerHTML = `
    <div class="section-header" style="margin-bottom:16px">
      <h2>Results</h2>
      <span class="results-count">${count} result${count !== 1 ? "s" : ""}</span>
    </div>
    <div class="results-grid">${results.map(renderClassifyCard).join("")}</div>`;
  bindFeatureToggles(container);
  if (featuresOpen) {
    container.querySelectorAll(".features-panel").forEach((p) => p.classList.add("open"));
    container.querySelectorAll(".feature-toggle").forEach((b) => {
      b.textContent = "Hide audio features ▴";
    });
  }
}

document.getElementById("searchBtn").addEventListener("click", doSearch);
document.getElementById("aiRandomBtn").addEventListener("click", doAiRandom);
document.getElementById("searchInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});
document.getElementById("artistInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});

/* ── Now Playing ── */
function showNowPlaying(idx) {
  if (!playlist.length) return;
  trackIndex = idx;
  const s = playlist[idx];
  const mood = discoverMood || s.mood;
  document.getElementById("npArt").textContent = MOOD_EMOJIS[mood] || "🎵";
  document.getElementById("npTitle").textContent = s.name;
  document.getElementById("npArtist").textContent = s.artists;
  document.getElementById("npMood").textContent = s.mood || mood;
  document.getElementById("npMood").className = `mood-badge mood-${s.mood || mood}`;
  document.getElementById("npPop").textContent =
    s.popularity != null ? `Popularity: ${s.popularity}` : "";
  document.getElementById("nowPlaying").classList.add("visible");
  isPlaying = true;
  updatePlayIcon();
}

function updatePlayIcon() {
  document.getElementById("npPlay").innerHTML = isPlaying
    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
}

document.getElementById("npPlay").addEventListener("click", () => {
  isPlaying = !isPlaying;
  updatePlayIcon();
});

document.getElementById("npPrev").addEventListener("click", () => {
  if (!playlist.length) return;
  showNowPlaying((trackIndex - 1 + playlist.length) % playlist.length);
});

document.getElementById("npNext").addEventListener("click", () => {
  if (!playlist.length) return;
  showNowPlaying((trackIndex + 1) % playlist.length);
});

loadStats();
