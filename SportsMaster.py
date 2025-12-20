import requests

# =====================================================
# PLAYLIST SOURCES (FREE ONLY — SPORTS SAFE)
# =====================================================
PLAYLISTS = [

    # ---------------- CORE LIVE / PPV / EVENTS ----------------
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",

    # ---------------- BUDDYCHEW LIVE (KEEP GROUPS) ----------------
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",

    # ---------------- FAST / HYBRID (SPORTS FILTERED) ----------------
    "https://pluto.freechannels.me/playlist.m3u",
    "https://nocords.xyz/pluto/playlist.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plex_us.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plex_ca.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/plex_gb.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/samsungtvplus_us.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/samsungtvplus_ca.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/samsungtvplus_gb.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/roku_all.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/refs/heads/main/playlists/tubi_all.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/refs/heads/main/playlists/xumo_playlist.m3u",

    # ---------------- APSATTV ----------------
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://www.apsattv.com/firetv.m3u",
    "https://www.apsattv.com/localnow.m3u",
    "https://www.apsattv.com/galxytv.m3u",
    "https://www.apsattv.com/klowd.m3u",
    "https://www.apsattv.com/xumo.m3u",
]

# =====================================================
# STATIC FALLBACK SPORTS CATEGORIES (ORDERED)
# =====================================================
FALLBACK_GROUPS = [
    ("Sports Networks (General)", ["sports network", "sportsnet", "espn", "fox sports", "cbs sports"]),
    ("Poker & Sports Betting", ["poker", "bet", "odds"]),
    ("Horse Racing", ["horse", "racing"]),
    ("Football", ["football", "nfl"]),
    ("Basketball", ["basketball", "nba"]),
    ("Baseball", ["baseball", "mlb"]),
    ("Hockey", ["hockey", "nhl"]),
    ("Fight Sports / PPV", ["ufc", "boxing", "mma", "wwe", "fight", "ppv"]),
    ("Fishing & Hunting", ["fishing", "hunting", "outdoor"]),
    ("Motorsports", ["nascar", "f1", "formula", "indy"]),
    ("Soccer", ["soccer", "futbol", "mls"]),
    ("Golf & Tennis", ["golf", "tennis"]),
]

DEFAULT_GROUP = "Sports Everything Else"

# =====================================================
# SPORTS ALLOWLIST (CRITICAL FILTER)
# =====================================================
SPORTS_KEYWORDS = [
    "sport", "nfl", "nba", "mlb", "nhl", "soccer", "football",
    "basketball", "baseball", "hockey", "fight", "ufc", "mma",
    "boxing", "ppv", "racing", "motorsport", "golf", "tennis",
    "poker", "bet", "odds"
]

def is_sports_channel(name, group):
    text = f"{name} {group}".lower()
    return any(k in text for k in SPORTS_KEYWORDS)

# =====================================================
# HELPERS
# =====================================================
def fetch(url):
    try:
        return requests.get(url, timeout=25).text
    except:
        return ""

def classify(name):
    text = name.lower()
    for group, keys in FALLBACK_GROUPS:
        if any(k in text for k in keys):
            return group
    return DEFAULT_GROUP

# =====================================================
# PARSE + FILTER + MERGE (NO NAME BREAKAGE)
# =====================================================
output = ["#EXTM3U"]
seen_streams = set()
current_extinf = None

for url in PLAYLISTS:
    text = fetch(url)
    if not text:
        continue

    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            current_extinf = line
            name = line.split(",")[-1]

            # Preserve existing group-title
            if 'group-title="' in line:
                rebuilt = line
            else:
                group = classify(name)
                rebuilt = line.replace(
                    "#EXTINF:-1",
                    f'#EXTINF:-1 group-title="{group}"'
                )

            current_extinf = rebuilt

        elif line.startswith("http") and current_extinf:
            name = current_extinf.split(",")[-1]
            group = ""
            if 'group-title="' in current_extinf:
                group = current_extinf.split('group-title="')[1].split('"')[0]

            # HARD FILTER: keep SPORTS ONLY
            if not is_sports_channel(name, group):
                continue

            # Deduplicate by STREAM URL ONLY
            if line in seen_streams:
                continue

            seen_streams.add(line)
            output.append(current_extinf)
            output.append(line)

# =====================================================
# WRITE FILE
# =====================================================
with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("DONE: sports_master.m3u (sports-only, live-safe, stable)")
