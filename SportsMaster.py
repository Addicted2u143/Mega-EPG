import requests
import pandas as pd
import re
from datetime import datetime

# ============================================================
# 1. FREE PLAYLIST SOURCES (RAW ONLY – NO GITHUB HTML LINKS)
# ============================================================

FREE_PLAYLISTS = [
    "https://www.apsattv.com/10fast.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_abcnews.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_adultswim.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_amagi.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk_bbc.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/main/M3U8/events.m3u8",
    "https://www.apsattv.com/cineverse.m3u",
    "https://www.apsattv.com/distro.m3u",
    "https://www.apsattv.com/firetv.m3u",
    "https://pluto.freechannels.me/playlist.m3u",
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freemoviesplus.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://www.apsattv.com/galxytv.m3u",
    "https://www.apsattv.com/klowd.m3u",
    "https://www.apsattv.com/gblg.m3u",
    "https://www.apsattv.com/uslg.m3u",
    "https://www.apsattv.com/localnow.m3u",
    "https://iptv-org.github.io/iptv/languages/eng.m3u"
]

# ============================================================
# 2. CATEGORY DEFINITIONS (FINAL – NO COMMENTARY)
# ============================================================

CATEGORY_KEYWORDS = {
    "📺 Sports Networks": ["espn", "fox sports", "tsn", "bein", "sportsnet", "sky sports"],
    "🎲 Action & Odds": ["bet", "poker", "odds", "casino"],
    "🐎 Horse Racing": ["horse", "racing", "track"],
    "🏈 NFL Football": ["nfl"],
    "🏉 NCAA Football": ["ncaaf", "college football"],
    "🏀 NBA Basketball": ["nba"],
    "🏀 NCAA Basketball": ["ncaab", "college basketball", "march madness"],
    "⚾ MLB Baseball": ["mlb", "baseball"],
    "🏒 NHL Hockey": ["nhl", "hockey"],
    "🥊 Fight Sports / PPV": ["ufc", "boxing", "mma", "wwe", "ppv"],
    "🎣 Fishing & Hunting": ["fishing", "hunting", "outdoor"],
    "🏎 Motorsports": ["nascar", "f1", "formula", "indycar", "motogp"],
    "⚽ Soccer": ["soccer", "futbol", "premier", "laliga", "bundesliga", "mls"],
    "⛳ Golf & Tennis": ["golf", "tennis", "pga", "atp", "wta"],
    "📦 Sports Everything Else": []
}

LIVE_HINTS = ["live", "event", "match", "game", "fight", "now"]

# ============================================================
# 3. CORE HELPERS
# ============================================================

def fetch_m3u(url):
    try:
        print(f"Fetching: {url}")
        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"Failed: {url}")
    return ""

def parse_m3u(text):
    rows = []
    name = logo = group = tvg_id = ""
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1].strip()
            logo = re.search(r'tvg-logo="([^"]*)"', line)
            group = re.search(r'group-title="([^"]*)"', line)
            tvg_id = re.search(r'tvg-id="([^"]*)"', line)
            logo = logo.group(1) if logo else ""
            group = group.group(1) if group else ""
            tvg_id = tvg_id.group(1) if tvg_id else ""
        elif line.startswith("http"):
            rows.append([name, line.strip(), logo, group, tvg_id])
    return pd.DataFrame(rows, columns=["name", "url", "logo", "group", "tvg_id"])

def classify_channel(name, group):
    text = f"{name} {group}".lower()
    for cat, keys in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keys):
            return cat
    return None

def is_live(name, group):
    text = f"{name} {group}".lower()
    return any(k in text for k in LIVE_HINTS)

# ============================================================
# 4. BUILD PLAYLIST
# ============================================================

def build_playlist():
    frames = []
    for url in FREE_PLAYLISTS:
        raw = fetch_m3u(url)
        if raw:
            frames.append(parse_m3u(raw))

    df = pd.concat(frames, ignore_index=True)
    df["category"] = df.apply(lambda r: classify_channel(r["name"], r["group"]), axis=1)
    df = df[df["category"].notna()]
    df["live"] = df.apply(lambda r: is_live(r["name"], r["group"]), axis=1)
    return df

# ============================================================
# 5. EXPORT
# ============================================================

def export_m3u(df, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat in CATEGORY_KEYWORDS.keys():
            block = df[df["category"] == cat]
            if block.empty:
                continue
            block = pd.concat([
                block[block["live"]],
                block[~block["live"]]
            ])
            for _, r in block.iterrows():
                f.write(
                    f'#EXTINF:-1 tvg-id="{r.tvg_id}" tvg-logo="{r.logo}" '
                    f'group-title="{cat}",{r.name}\n'
                )
                f.write(r.url + "\n")

# ============================================================
# 6. RUN
# ============================================================

if __name__ == "__main__":
    print("Building Sports Master playlist…")
    df = build_playlist()
    export_m3u(df, "sports_master.m3u")
    print("Done → sports_master.m3u generated")
