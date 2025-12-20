import requests

# =====================================================
# PLAYLIST SOURCES (FREE ONLY — FROZEN LIST)
# =====================================================
PLAYLISTS = [

    # CORE LIVE / PPV / EVENTS (DYNAMIC — KEEP GROUPS)
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",

    # BUDDYCHEW LIVE ECOSYSTEM (DYNAMIC GROUPS)
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",

    # FAST / HYBRID SOURCES (SPORTS HIDING INSIDE)
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

    # APSATTV (EDGE / BACKUP)
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://www.apsattv.com/firetv.m3u",
    "https://www.apsattv.com/localnow.m3u",
    "https://www.apsattv.com/galxytv.m3u",
    "https://www.apsattv.com/klowd.m3u",
    "https://www.apsattv.com/xumo.m3u",
]

# =====================================================
# STATIC FALLBACK CATEGORY ORDER (ONLY IF NO GROUP)
# =====================================================
FALLBACK_GROUPS = [
    ("Sports Networks (General)", ["espn", "sportsnet", "fox sports", "cbs sports"]),
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
# REDZONE CONTROL (SURGICAL, NOT GLOBAL)
# =====================================================
REDZONE_LIMIT = 6
redzone_seen_urls = set()
redzone_count = 0

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
# PARSE + MERGE (SAFE, NO NAME BREAKING)
# =====================================================
output = ["#EXTM3U"]
current_extinf = None

for url in PLAYLISTS:
    text = fetch(url)
    if not text:
        continue

    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            current_extinf = line
            channel_name = line.split(",")[-1]

            # Respect existing group-title
            if 'group-title="' in line:
                rebuilt = line
            else:
                group = classify(channel_name)
                rebuilt = line.replace(
                    "#EXTINF:-1",
                    f'#EXTINF:-1 group-title="{group}"'
                )

            current_extinf = rebuilt

        elif line.startswith("http") and current_extinf:
            name_lower = current_extinf.lower()

            # NFL RedZone special handling
            if "redzone" in name_lower:
                if line in redzone_seen_urls:
                    continue
                if redzone_count >= REDZONE_LIMIT:
                    continue

                redzone_seen_urls.add(line)
                redzone_count += 1

                tagged = current_extinf.replace(
                    ",",
                    f" | Alt {redzone_count},",
                    1
                )
                output.append(tagged)
                output.append(line)
            else:
                output.append(current_extinf)
                output.append(line)

# =====================================================
# WRITE FILE
# =====================================================
with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("DONE: sports_master.m3u — stable, dynamic, RedZone-safe")
