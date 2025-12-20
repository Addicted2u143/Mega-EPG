import requests
import re
from collections import defaultdict

# ==========================================================
# FREE PLAYLIST SOURCES (ALL INCLUDED)
# ==========================================================

FREE_PLAYLISTS = [
    "https://www.apsattv.com/10fast.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/galxytv.m3u",
    "https://www.apsattv.com/klowd.m3u",
    "https://www.apsattv.com/gblg.m3u",
    "https://www.apsattv.com/uslg.m3u",
    "https://www.apsattv.com/localnow.m3u",
    "https://pluto.freechannels.me/playlist.m3u",
    "https://iptv-org.github.io/iptv/languages/eng.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",
]

# ==========================================================
# CATEGORY RULES
# ==========================================================

CATEGORIES = {
    "🏈 NFL Football": ["nfl", "redzone", "football"],
    "🏉 NCAA Football": ["ncaaf", "college football"],
    "🏀 NBA Basketball": ["nba"],
    "🏀 NCAA Basketball": ["ncaab", "college basketball"],
    "⚾ MLB Baseball": ["mlb", "baseball"],
    "🏒 NHL Hockey": ["nhl", "hockey"],
    "🥊 Fight Sports / PPV": ["ufc", "boxing", "mma", "ppv", "fight"],
    "🎣 Fishing & Hunting": ["fishing", "hunting", "outdoor"],
    "🏎 Motorsports": ["nascar", "f1", "formula", "indycar", "motogp"],
    "⚽ Soccer": ["soccer", "futbol", "mls", "epl", "la liga", "bundesliga"],
    "⛳ Golf & Tennis": ["golf", "pga", "tennis", "atp", "wta"],
    "🎲 Poker & Sports Betting": [
        "poker", "world poker", "wpt", "triton",
        "fanduel", "draftkings"
    ],
    "📺 Sports Networks": [
        "espn", "fox sports", "cbs sports", "nbc sports",
        "sportsnet", "bein", "sky sports"
    ],
}

EXCLUDE_FALSE_BETTING = ["bet+", "bet her", "bet soul", "black entertainment"]

LIVE_HINTS = [
    " vs ", " at ", " v ", " vs.", "@",
    "live", "kickoff", "round", "match"
]

# ==========================================================
# HELPERS
# ==========================================================

def fetch_m3u(url):
    try:
        print("Fetching:", url)
        return requests.get(url, timeout=20).text
    except:
        return ""

def detect_category(name):
    lname = name.lower()

    for bad in EXCLUDE_FALSE_BETTING:
        if bad in lname:
            return None

    for cat, keys in CATEGORIES.items():
        for k in keys:
            if k in lname:
                return cat
    return None

def looks_live(name):
    lname = name.lower()
    return any(h in lname for h in LIVE_HINTS)

# ==========================================================
# PARSE + BUILD
# ==========================================================

channels_by_category = defaultdict(list)

for src in FREE_PLAYLISTS:
    text = fetch_m3u(src)
    lines = text.splitlines()

    name = None
    meta = ""

    for line in lines:
        if line.startswith("#EXTINF"):
            meta = line
            name = line.split(",")[-1].strip()
        elif line.startswith("http") and name:
            cat = detect_category(name)
            if cat:
                channels_by_category[cat].append((name, line))
            name = None

# ==========================================================
# EXPORT
# ==========================================================

with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for cat in CATEGORIES.keys():
        items = channels_by_category.get(cat)
        if not items:
            continue

        f.write(f'\n#EXTINF:-1 group-title="{cat}",{cat}\n')
        f.write("http://example.com/blank\n")

        for name, url in sorted(items):
            f.write(f'#EXTINF:-1 group-title="{cat}",{name}\n')
            f.write(url + "\n")

print("Done → sports_master.m3u generated")
