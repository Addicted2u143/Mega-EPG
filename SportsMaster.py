import requests

# =====================================================
# PLAYLIST SOURCES (FREE ONLY — FULL, SAFE LIST)
# =====================================================
PLAYLISTS = [

    # CORE LIVE / PPV / EVENTS (DYNAMIC)
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",

    # BUDDYCHEW ECOSYSTEM (KEEP GROUPS)
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",

    # FAST / HYBRID
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

    # APSATTV
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://www.apsattv.com/firetv.m3u",
    "https://www.apsattv.com/localnow.m3u",
    "https://www.apsattv.com/galxytv.m3u",
    "https://www.apsattv.com/klowd.m3u",
    "https://www.apsattv.com/xumo.m3u",
]

# =====================================================
# STATIC FALLBACK GROUPS (ORDERED — FIRST MATCH WINS)
# =====================================================
FALLBACK_GROUPS = [
    ("② Sports Networks (General)", ["sports network", "sportsnet", "espn", "fox sports", "cbs sports", "nbc sports", "bein"]),
    ("③ Poker & Sports Betting", ["poker", "bet", "odds"]),
    ("④ Horse Racing", ["horse", "racing"]),
    ("⑤ Football", ["football", "nfl"]),
    ("⑥ Basketball", ["basketball", "nba"]),
    ("⑦ Baseball", ["baseball", "mlb"]),
    ("⑧ Hockey", ["hockey", "nhl"]),
    ("⑨ Fight Sports / PPV", ["ufc", "boxing", "mma", "wwe", "fight", "ppv"]),
    ("⑩ Fishing & Hunting", ["fishing", "hunting", "outdoor"]),
    ("⑪ Motorsports", ["nascar", "f1", "formula", "indy"]),
    ("⑫ Soccer", ["soccer", "futbol", "mls"]),
    ("⑬ Golf & Tennis", ["golf", "tennis"]),
]

DEFAULT_GROUP = "⑭ Sports Everything Else"
LIVE_PREFIX = "① Live | "

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
# PARSE + MERGE (DYNAMIC SAFE, ORDERED)
# =====================================================
output = ["#EXTM3U"]
current_extinf = None

for url in PLAYLISTS:
    text = fetch(url)
    if not text:
        continue

    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1]

            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
                rebuilt = line.replace(
                    f'group-title="{group}"',
                    f'group-title="{LIVE_PREFIX}{group}"'
                )
            else:
                group = classify(name)
                rebuilt = line.replace(
                    "#EXTINF:-1",
                    f'#EXTINF:-1 group-title="{group}"'
                )

            current_extinf = rebuilt

        elif line.startswith("http") and current_extinf:
            output.append(current_extinf)
            output.append(line)

# =====================================================
# WRITE FILE (MATCH WORKFLOW)
# =====================================================
with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("DONE: sports_master.m3u (sports networks restored, dynamic promoted)")
