import requests
import pandas as pd
import re

# =========================================================
# 1. PLAYLIST SOURCES
# =========================================================

FREE_PLAYLISTS = [
    "https://pluto.freechannels.me/playlist.m3u",
    "https://iptv-org.github.io/iptv/categories/movies.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plex_us.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plex_ca.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plex_gb.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plutotv_us.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/samsungtvplus_us.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/roku-playlist-generator/refs/heads/main/roku.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/tubi-scraper/refs/heads/main/tubi_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/refs/heads/main/playlists/xumo_playlist.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",

    "https://www.apsattv.com/10fast.m3u",
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://www.apsattv.com/firetv.m3u",
    "https://www.apsattv.com/localnow.m3u",
]

# Playlists we DO NOT touch or re-categorize
PASSTHROUGH_KEYWORDS = [
    "ppv", "buddylive", "streamsu", "streamedsu", "pixelsports"
]

# =========================================================
# 2. CATEGORIES (ORDER PRESERVED)
# =========================================================

CATEGORY_ORDER = [
    "📺 Sports Networks (General)",
    "🏈 NFL Football",
    "🏉 NCAA Football",
    "🏀 NBA Basketball",
    "🏀 NCAA Basketball",
    "⚾ MLB Baseball",
    "🏒 NHL Hockey",
    "🥊 Fight Sports / PPV",
    "🎲 Poker & Sports Betting",
    "🐎 Horse Racing",
    "🎣 Fishing & Hunting",
    "🏎️ Motorsports",
    "⚽ Soccer",
    "⛳ Golf & Tennis",
    "📦 Sports Everything Else",
]

CATEGORY_RULES = {
    "🏈 NFL Football": ["nfl", "redzone"],
    "🏉 NCAA Football": ["ncaaf", "college football"],
    "🏀 NBA Basketball": ["nba"],
    "🏀 NCAA Basketball": ["ncaab", "march madness"],
    "⚾ MLB Baseball": ["mlb"],
    "🏒 NHL Hockey": ["nhl"],
    "🥊 Fight Sports / PPV": ["ufc", "boxing", "wwe", "ppv", "mma"],
    "🎲 Poker & Sports Betting": ["poker", "draftkings", "fanduel", "betting"],
    "🐎 Horse Racing": ["horse", "racing"],
    "🎣 Fishing & Hunting": ["fishing", "hunting", "outdoor"],
    "🏎️ Motorsports": ["nascar", "f1", "formula", "indy"],
    "⚽ Soccer": ["soccer", "futbol", "premier", "laliga"],
    "⛳ Golf & Tennis": ["golf", "tennis", "pga", "atp", "wta"],
}

# =========================================================
# 3. HELPERS
# =========================================================

def fetch(url):
    try:
        print("Fetching:", url)
        return requests.get(url, timeout=25).text
    except:
        return ""

def parse_m3u(text):
    rows = []
    name = group = logo = ""
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1].strip()
            group = re.search(r'group-title="([^"]+)"', line)
            logo = re.search(r'tvg-logo="([^"]+)"', line)
            group = group.group(1) if group else ""
            logo = logo.group(1) if logo else ""
        elif line.startswith("http"):
            rows.append([name, line.strip(), group, logo])
    return pd.DataFrame(rows, columns=["name", "url", "group", "logo"])

def is_passthrough(name, group):
    combo = (name + " " + group).lower()
    return any(k in combo for k in PASSTHROUGH_KEYWORDS)

def clean_name(name):
    return re.sub(r"^\d+\s*", "", name)

# =========================================================
# 4. BUILD
# =========================================================

all_rows = []

for url in FREE_PLAYLISTS:
    text = fetch(url)
    if text.strip():
        df = parse_m3u(text)
        df["source"] = url
        all_rows.append(df)

df = pd.concat(all_rows, ignore_index=True)

# Clean numbers only for non-live
df["name"] = df.apply(
    lambda r: r["name"] if is_passthrough(r["name"], r["group"]) else clean_name(r["name"]),
    axis=1
)

# Categorize
def categorize(row):
    combo = (row["name"] + " " + row["group"]).lower()
    for cat, keys in CATEGORY_RULES.items():
        if any(k in combo for k in keys):
            return cat
    return "📦 Sports Everything Else"

df["category"] = df.apply(
    lambda r: r["group"] if is_passthrough(r["name"], r["group"]) else categorize(r),
    axis=1
)

# =========================================================
# 5. EXPORT
# =========================================================

with open("sports_master.m3u", "w") as f:
    f.write("#EXTM3U\n")
    for cat in CATEGORY_ORDER + sorted(set(df["category"]) - set(CATEGORY_ORDER)):
        block = df[df["category"] == cat]
        if block.empty:
            continue
        for _, r in block.iterrows():
            f.write(
                f'#EXTINF:-1 tvg-logo="{r.logo}" group-title="{cat}",{r.name}\n'
            )
            f.write(r.url + "\n")

print("Done: sports_master.m3u")
