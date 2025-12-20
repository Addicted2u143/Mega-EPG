import requests
import re
from collections import OrderedDict

# ============================================================
# SPORTS MASTER — FREE PLAYLISTS ONLY — FINAL
# ============================================================

FREE_PLAYLISTS = [
    # APSATTV
    "https://www.apsattv.com/10fast.m3u",
    "https://www.apsattv.com/cineverse.m3u",
    "https://www.apsattv.com/distro.m3u",
    "https://www.apsattv.com/firetv.m3u",
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freemoviesplus.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://www.apsattv.com/galxytv.m3u",
    "https://www.apsattv.com/klowd.m3u",
    "https://www.apsattv.com/gblg.m3u",
    "https://www.apsattv.com/uslg.m3u",
    "https://www.apsattv.com/localnow.m3u",

    # IPTV-ORG
    "https://iptv-org.github.io/iptv/languages/eng.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ca.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/au.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_abcnews.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_pbs.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_cbsn.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_canelatv.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_firetv.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_distro.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_adultswim.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_amagi.m3u",

    # Pluto / MOJ
    "https://pluto.freechannels.me/playlist.m3u",
    "https://bit.ly/moj-m3u8",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_moveonjoy.m3u",

    # BuddyChewChew
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/main/M3U8/events.m3u8",

    # Local merge (optional)
    "merged_playlist.m3u",
]

# ============================================================
# CATEGORIES (FINAL APPROVED)
# ============================================================

CATEGORIES = OrderedDict({
    "📺 Sports Networks": ["espn", "fox sports", "sportsnet", "bein", "tsn", "sky sports"],
    "🎲 Action & Odds": ["vsin", "fanduel", "sportsgrid", "poker"],
    "🐎 Horse Racing": ["horse", "racing", "tvg"],
    "🏈 NFL Football": ["nfl", "redzone"],
    "🏉 NCAA Football": ["ncaaf", "college football"],
    "🏀 NBA Basketball": ["nba"],
    "🏀 NCAA Basketball": ["ncaab", "college basketball"],
    "⚾ MLB Baseball": ["mlb", "baseball"],
    "🏒 NHL Hockey": ["nhl", "hockey"],
    "🥊 Fight Sports / PPV": ["ufc", "boxing", "mma", "wwe", "ppv"],
    "🎣 Fishing & Hunting": ["fishing", "hunting", "outdoor"],
    "🏎️ Motorsports": ["nascar", "formula", "f1", "indycar", "motogp"],
    "⚽ Soccer": ["soccer", "futbol", "premier", "laliga", "bundesliga", "mls"],
    "⛳ Golf & Tennis": ["golf", "tennis", "pga", "atp", "wta"],
    "📦 Sports Everything Else": []
})

EXCLUDE_KEYWORDS = [
    "bet ",
    "bet+",
    "bet her",
    "bet soul",
    "black entertainment"
]

LIVE_HINTS = ["live", "event", "match", "vs", "fight", "game", "now"]

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

def clean_name(name):
    name = re.sub(r"\s*\|\s*\d+$", "", name)
    name = re.sub(r"\s+\d+$", "", name)
    return name.strip()

def is_numeric(name):
    return bool(re.fullmatch(r"\d+", name))

def excluded(name):
    lname = name.lower()
    return any(x in lname for x in EXCLUDE_KEYWORDS)

def classify(name):
    lname = name.lower()
    for cat, keys in CATEGORIES.items():
        if any(k in lname for k in keys):
            return cat
    return "📦 Sports Everything Else"

def is_live(name):
    lname = name.lower()
    return any(x in lname for x in LIVE_HINTS)

# ============================================================
# BUILD
# ============================================================

def build():
    buckets = {k: [] for k in CATEGORIES}
    seen = set()

    for src in FREE_PLAYLISTS:
        print(f"Fetching: {src}")
        text = fetch(src)
        name = None

        for line in text.splitlines():
            if line.startswith("#EXTINF"):
                name = line.split(",")[-1].strip()
            elif line.startswith("http") and name:
                cname = clean_name(name)

                if not cname or is_numeric(cname) or excluded(cname):
                    name = None
                    continue

                if line in seen:
                    name = None
                    continue

                seen.add(line)
                cat = classify(cname)
                buckets[cat].append((is_live(cname), cname, line))
                name = None

    return buckets

def export(data):
    with open("sports_master.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat, items in data.items():
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
    print("Building Sports Master (full free set)…")
    data = build()
    export(data)
    print("Done → sports_master.m3u")
