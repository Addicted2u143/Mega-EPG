import requests

# =====================================================
# PLAYLIST SOURCES
# =====================================================

LIVE_EVENT_PLAYLISTS = [
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",
]

OTHER_PLAYLISTS = [
    # BuddyLive
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",

    # FAST / Aggregators
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
# CATEGORY BUCKETS (ORDER MATTERS)
# =====================================================

BUCKETS = [
    ("Poker & Sports Betting", ["poker", "bet", "odds"]),
    ("Horse Racing", ["horse", "racing"]),
    ("Football", ["football", "nfl"]),
    ("Basketball", ["basketball", "nba"]),
    ("Baseball", ["baseball", "mlb"]),
    ("Hockey", ["hockey", "nhl"]),
    ("Fight Sports / PPV", ["ufc", "boxing", "mma", "wwe", "fight"]),
    ("Fishing & Hunting", ["fishing", "hunting", "outdoor"]),
    ("Motorsports", ["nascar", "f1", "formula", "indy"]),
    ("Soccer", ["soccer", "futbol", "mls"]),
    ("Golf & Tennis", ["golf", "tennis"]),
]

DEFAULT_BUCKET = "Sports Networks (General)"

# =====================================================
# HELPERS
# =====================================================

def fetch(url):
    try:
        return requests.get(url, timeout=25).text
    except:
        return ""

def bucketize(name):
    text = name.lower()
    for bucket, keys in BUCKETS:
        if any(k in text for k in keys):
            return bucket
    return DEFAULT_BUCKET

# =====================================================
# BUILD PLAYLIST
# =====================================================

output = ["#EXTM3U"]
seen_urls = set()
current_extinf = None

def process_playlist(url, preserve_groups):
    global current_extinf
    text = fetch(url)
    if not text:
        return

    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1]

            if preserve_groups and 'group-title="' in line:
                current_extinf = line
            else:
                bucket = bucketize(name)
                current_extinf = line.replace(
                    "#EXTINF:-1",
                    f'#EXTINF:-1 group-title="{bucket}"'
                )

        elif line.startswith("http") and current_extinf:
            if line in seen_urls:
                return
            seen_urls.add(line)
            output.append(current_extinf)
            output.append(line)

# Live events first (keep their categories)
for url in LIVE_EVENT_PLAYLISTS:
    process_playlist(url, preserve_groups=True)

# Everything else collapsed into buckets
for url in OTHER_PLAYLISTS:
    process_playlist(url, preserve_groups=False)

# =====================================================
# WRITE FILE
# =====================================================

with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("DONE: sports_master.m3u (usable, sane, no category explosion)")
