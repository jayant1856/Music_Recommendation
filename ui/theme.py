"""
Design tokens and global styling for the AI Music Recommendation System.

This module only injects CSS / fonts. It never touches ML, Spotify, or
history logic — it is purely presentational.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Design tokens (kept in one place so every component pulls from the same
# palette instead of hardcoding hex values).
# ---------------------------------------------------------------------------

COLORS = {
    "primary": "#1DB954",       # Spotify green — CTAs, active states, accents
    "primary_dark": "#169c46",
    "secondary": "#0F172A",     # deep navy — hero background
    "accent": "#3B82F6",        # electric blue — links, secondary accents
    "bg": "#111827",            # app background
    "card": "#1F2937",          # card surfaces
    "card_hover": "#243247",
    "border": "#2D3B4F",
    "text": "#F9FAFB",
    "text_muted": "#94A3B8",
    "danger": "#F87171",
    "warning": "#FBBF24",
}

MOOD_COLORS = {
    "Relax": "#38BDF8",
    "Party": "#F472B6",
    "Romantic": "#FB7185",
    "Happy": "#FBBF24",
    "Rap": "#A78BFA",
}

MOOD_ICONS = {
    "Relax": "😌",
    "Party": "🎉",
    "Romantic": "💕",
    "Happy": "😊",
    "Rap": "🎤",
}


def inject_global_styles() -> None:
    """Injects fonts, CSS variables, and every reusable class used across pages."""

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {{
            --primary: {COLORS['primary']};
            --primary-dark: {COLORS['primary_dark']};
            --secondary: {COLORS['secondary']};
            --accent: {COLORS['accent']};
            --bg: {COLORS['bg']};
            --card: {COLORS['card']};
            --card-hover: {COLORS['card_hover']};
            --border: {COLORS['border']};
            --text: {COLORS['text']};
            --text-muted: {COLORS['text_muted']};
            --danger: {COLORS['danger']};
            --warning: {COLORS['warning']};
        }}

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(circle at 15% 0%, rgba(29,185,84,0.08), transparent 45%),
                radial-gradient(circle at 85% 10%, rgba(59,130,246,0.07), transparent 40%),
                var(--bg);
            color: var(--text);
        }}

        h1, h2, h3, h4, .font-display {{
            font-family: 'Sora', sans-serif !important;
            letter-spacing: -0.02em;
        }}

        code, .mono {{
            font-family: 'JetBrains Mono', monospace !important;
        }}

        /* Hide default Streamlit chrome that clashes with the custom look */
        #MainMenu, footer {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{ background: transparent; }}

        /* ---------------- Sidebar ---------------- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0B1220 0%, #0F172A 100%);
            border-right: 1px solid var(--border);
        }}
        section[data-testid="stSidebar"] .stRadio > label {{
            display: none;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            background: transparent;
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 4px;
            transition: background 0.15s ease, transform 0.15s ease;
            width: 100%;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: rgba(29,185,84,0.12);
            transform: translateX(2px);
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label p {{
            font-size: 15px !important;
            font-weight: 500;
        }}

        .sidebar-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 4px 18px 4px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 16px;
        }}
        .sidebar-brand .logo {{
            width: 38px; height: 38px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            display: flex; align-items: center; justify-content: center;
            font-size: 19px;
        }}
        .sidebar-brand .title {{
            font-family: 'Sora', sans-serif;
            font-weight: 700;
            font-size: 16px;
            line-height: 1.1;
        }}
        .sidebar-brand .subtitle {{
            font-size: 11px;
            color: var(--text-muted);
        }}

        /* ---------------- Buttons ---------------- */
        .stButton > button, .stLinkButton > a, .stDownloadButton > button {{
            border-radius: 10px !important;
            border: 1px solid var(--border) !important;
            background: var(--card) !important;
            color: var(--text) !important;
            font-weight: 600 !important;
            transition: all 0.18s ease !important;
        }}
        .stButton > button:hover, .stLinkButton > a:hover, .stDownloadButton > button:hover {{
            border-color: var(--primary) !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(29,185,84,0.18);
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
            border: none !important;
            color: #06120A !important;
            box-shadow: 0 4px 14px rgba(29,185,84,0.35);
        }}
        .stButton > button[kind="primary"]:hover {{
            box-shadow: 0 8px 22px rgba(29,185,84,0.45);
        }}

        /* ---------------- Inputs ---------------- */
        .stTextInput > div > div, .stTextArea > div > div {{
            background: var(--card) !important;
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
        }}
        .stTextInput input {{ color: var(--text) !important; }}

        /* ---------------- Hero ---------------- */
        .hero-wrap {{
            padding: 46px 40px;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(15,23,42,0.9), rgba(17,24,39,0.9));
            border: 1px solid var(--border);
            margin-bottom: 28px;
            position: relative;
            overflow: hidden;
        }}
        .hero-eyebrow {{
            display: inline-block;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--primary);
            background: rgba(29,185,84,0.12);
            border: 1px solid rgba(29,185,84,0.3);
            padding: 4px 12px;
            border-radius: 999px;
            margin-bottom: 18px;
        }}
        .hero-title {{
            font-size: 44px;
            font-weight: 800;
            line-height: 1.1;
            margin: 0 0 14px 0;
            background: linear-gradient(90deg, #FFFFFF 40%, var(--primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .hero-subtitle {{
            font-size: 17px;
            color: var(--text-muted);
            max-width: 520px;
            line-height: 1.55;
        }}

        /* Equalizer signature element */
        .eq {{
            display: flex;
            align-items: flex-end;
            gap: 6px;
            height: 90px;
            justify-content: center;
        }}
        .eq span {{
            width: 8px;
            border-radius: 4px;
            background: linear-gradient(180deg, var(--primary), var(--accent));
            animation: eq-bounce 1.1s ease-in-out infinite;
        }}
        .eq span:nth-child(1) {{ height: 30%; animation-delay: 0s; }}
        .eq span:nth-child(2) {{ height: 65%; animation-delay: 0.12s; }}
        .eq span:nth-child(3) {{ height: 95%; animation-delay: 0.24s; }}
        .eq span:nth-child(4) {{ height: 50%; animation-delay: 0.36s; }}
        .eq span:nth-child(5) {{ height: 80%; animation-delay: 0.48s; }}
        .eq span:nth-child(6) {{ height: 40%; animation-delay: 0.6s; }}
        .eq span:nth-child(7) {{ height: 70%; animation-delay: 0.72s; }}
        @keyframes eq-bounce {{
            0%, 100% {{ transform: scaleY(0.35); opacity: 0.75; }}
            50% {{ transform: scaleY(1); opacity: 1; }}
        }}

        /* ---------------- Generic cards ---------------- */
        .glass-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 20px 22px;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
            animation: fade-up 0.35s ease both;
        }}
        .glass-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(29,185,84,0.45);
            box-shadow: 0 12px 28px rgba(0,0,0,0.35);
        }}

        @keyframes fade-up {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Feature cards (landing page) */
        .feature-card {{
            text-align: left;
        }}
        .feature-card .icon {{
            font-size: 26px;
            width: 48px; height: 48px;
            border-radius: 12px;
            background: rgba(29,185,84,0.12);
            display: flex; align-items: center; justify-content: center;
            margin-bottom: 14px;
        }}
        .feature-card h4 {{ margin: 0 0 6px 0; font-size: 16px; }}
        .feature-card p {{ margin: 0; font-size: 13.5px; color: var(--text-muted); line-height: 1.5; }}

        /* Stat cards */
        .stat-card {{
            text-align: center;
            padding: 18px 10px;
        }}
        .stat-card .value {{
            font-family: 'Sora', sans-serif;
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-card .label {{
            font-size: 12.5px;
            color: var(--text-muted);
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        /* Song cards */
        .song-card {{
            display: flex;
            gap: 16px;
            align-items: center;
            padding: 16px;
        }}
        .song-cover {{
            width: 56px; height: 56px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            display: flex; align-items: center; justify-content: center;
            font-size: 22px;
            flex-shrink: 0;
        }}
        .song-info {{ flex: 1; min-width: 0; }}
        .song-name {{
            font-weight: 700;
            font-size: 15.5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .song-artist {{
            font-size: 13px;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .badge-row {{ margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 11.5px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 999px;
        }}
        .badge-pop {{ background: rgba(59,130,246,0.15); color: #93C5FD; }}
        .badge-cluster {{ background: rgba(148,163,184,0.15); color: #CBD5E1; }}

        /* Progress / feature bars */
        .feat-row {{ margin-bottom: 14px; }}
        .feat-row .feat-label {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            margin-bottom: 5px;
            color: var(--text-muted);
        }}
        .feat-row .feat-label span:last-child {{
            font-family: 'JetBrains Mono', monospace;
            color: var(--text);
        }}
        div[data-testid="stProgress"] > div > div {{
            background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
            border-radius: 999px !important;
        }}
        div[data-testid="stProgress"] > div {{
            background: rgba(255,255,255,0.06) !important;
            border-radius: 999px !important;
        }}

        /* Section header */
        .section-header {{ display: flex; align-items: center; gap: 10px; margin: 6px 0 18px 0; }}
        .section-header .icon {{
            width: 34px; height: 34px;
            border-radius: 9px;
            background: rgba(59,130,246,0.14);
            display: flex; align-items: center; justify-content: center;
            font-size: 16px;
        }}
        .section-header h3 {{ margin: 0; }}
        .section-header p {{ margin: 0; color: var(--text-muted); font-size: 13px; }}

        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            border: 1px dashed var(--border);
            border-radius: 16px;
            color: var(--text-muted);
        }}
        .empty-state .icon {{ font-size: 34px; margin-bottom: 10px; }}

        /* Skeleton loader */
        .skeleton {{
            border-radius: 14px;
            height: 76px;
            background: linear-gradient(90deg, var(--card) 25%, var(--card-hover) 37%, var(--card) 63%);
            background-size: 400% 100%;
            animation: skeleton-loading 1.2s ease-in-out infinite;
            margin-bottom: 12px;
        }}
        @keyframes skeleton-loading {{
            0% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        /* Pipeline diagram */
        .pipeline {{ display: flex; align-items: center; flex-wrap: wrap; gap: 0; }}
        .pipeline .step {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 16px;
            min-width: 150px;
            text-align: center;
        }}
        .pipeline .step .icon {{ font-size: 20px; margin-bottom: 6px; }}
        .pipeline .step .title {{ font-weight: 700; font-size: 13.5px; }}
        .pipeline .step .desc {{ font-size: 11.5px; color: var(--text-muted); margin-top: 2px;}}
        .pipeline .arrow {{ color: var(--primary); font-size: 20px; padding: 0 10px; }}

        /* Developer card */
        .dev-avatar {{
            width: 96px; height: 96px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            display: flex; align-items: center; justify-content: center;
            font-size: 38px;
            font-weight: 800;
            margin: 0 auto 16px auto;
            box-shadow: 0 10px 30px rgba(29,185,84,0.3);
        }}
        .skill-chip {{
            display: inline-block;
            background: rgba(148,163,184,0.12);
            border: 1px solid var(--border);
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 12.5px;
            margin: 3px 4px 0 0;
        }}

        hr {{ border-color: var(--border) !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )