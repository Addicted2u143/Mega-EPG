import requests
from collections import OrderedDict

# ============================================================
# SPORTS MASTER — FREE ONLY — PRODUCTION SAFE
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
    "https://pluto.freechannels.me/playlist.m3u",
    "https://www.apsattv.com/freelivesports.m3u"
]

# ============================================================
# CATEGORY DEFINITIONS (FINAL)
# ============================================================

CATEGORIES = OrderedDict({
    "📺 Sports Networks (General)": [
        "espn", "fox sports", "sportsnet", "bein", "tsn", "sky sports"
    ],
    "🎲 Action & Odds": [
        "vsin", "fanduel", "sportsgrid", "poker"
    ],
    "🐎 Horse Racing": [
        "horse", "racing", "tvg"
    ],
    "🏈 NFL Football": [
        "nfl", "redzone"
    ],
    "🏉 NCAA Football": [
        "ncaaf", "college football", "sec network", "acc network", "big ten"
    ],
    "🏀 NBA Basketball": [
        "nba"
    ],
    "🏀 NCAA Basketball": [
        "ncaab", "college basketball", "march madness"
    ],
    "⚾ MLB Baseball": [
        "mlb", "baseball"
    ],
    "🏒 NHL Hockey": [
        "nhl", "hockey"
    ],
    "🥊 Fight Sports / PPV": [
        "ufc", "boxing", "mma", "wwe", "ppv"
    ],
    "🎣 Fishing & Hunting": [
        "fishing", "hunting", "outdoor"
    ],
    "🏎️ Motorsports": [
        "nascar", "formula", "f1", "indycar", "motogp"
    ],
    "⚽ Soccer": [
        "soccer", "futbol", "premier", "laliga", "bundesliga", "mls"
    ],
    "⛳ Golf & Tennis": [
        "golf", "tennis", "pga", "atp", "wta"
    ],
    "📦 Sports Everything Else": []
})

# Explicit exclusions (prevents false positives)
BET_EXCLUSIONS = [
    "bet ",       # BET channel prefix
    "bet+", 
    "bet her",
    "bet soul",
    "black entertainment"
]

LIVE_KEYWORDS = [
    "live", "event", "match", "vs", "fight", "game", "now"
]

# ============================================================
# HELPERS
# ============================================================

def fetch(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and "#EXTM3U" in r.text:
            return r.text
    except:
        pass
    return ""

def parse_m3u(text):
    entries = []
    name = None
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1].strip()
        elif line.startswith("http") and name:
            entries.append((name, line.strip()))
            name = None
    return entries

def is_bet_entertainment(name):
    lname = name.lower()
    return any(bad in lname for bad in BET_EXCLUSIONS)

def classify(name):
    lname = name.lower()

    # Hard exclusion: BET ≠ betting
    if is_bet_entertainment(lname):
        return "📦 Sports Everything Else"

    for cat, keys in CATEGORIES.items():
        if any(k in lname for k in keys):
            return cat

    return "📦 Sports Everything Else"

def is_live(name):
    lname = name.lower()
    return any(k in lname for k in LIVE_KEYWORDS)

# ============================================================
# BUILD PLAYLIST
# ============================================================

def build_playlist():
    seen_urls = set()
    categorized = {cat: [] for cat in CATEGORIES}

    for src in FREE_PLAYLISTS:
        print(f"Fetching: {src}")
        text = fetch(src)
        for name, url in parse_m3u(text):
            if not name or url in seen_urls:
                continue
            seen_urls.add(url)

            cat = classify(name)
            live = is_live(name)
            categorized[cat].append((live, name, url))

    return categorized

# ============================================================
# EXPORT
# ============================================================

def export_m3u(categorized, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat, items in categorized.items():
            if not items:
                continue
            items.sort(key=lambda x: (not x[0], x[1].lower()))
            for live, name, url in items:
                f.write(f'#EXTINF:-1 group-title="{cat}",{name}\n')
                f.write(url + "\n")

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    print("Building Sports Master playlist...")
    playlist = build_playlist()
    export_m3u(playlist, "sports_master.m3u")
    print("Done → sports_master.m3u")
