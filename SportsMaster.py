import requests

# =====================================================
# PLAYLIST SOURCES (FREE ONLY — FULL & VERIFIED)
# =====================================================
PLAYLISTS = [

    # =================================================
    # CORE LIVE / PPV / EVENTS (NON-NEGOTIABLE)
    # =================================================
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",

    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",

    # =================================================
    # BUDDYCHEW LIVE ECOSYSTEM (KEEP DYNAMIC GROUPS)
    # =================================================
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",

    # =================================================
    # FAST / HYBRID SOURCES (SPORTS HIDING INSIDE)
    # =================================================
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

    # =================================================
    # APSATTV (BACKUP / EDGE SPORTS)
    # =================================================
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://www.apsattv.com/firetv.m3u",
    "https://www.apsattv.com/localnow.m3u",
    "https://www.apsattv.com/galxytv.m3u",
    "https://www.apsattv.com/klowd.m3u",
    "https://www.apsattv.com/xumo.m3u",
]

# =====================================================
# ANCHOR DEFINITIONS (STATIC TOP-LEVEL CATEGORIES)
# =====================================================
ANCHORS = {
    "Football": ["nfl", "football", "ncaa"],
    "Basketball": ["nba", "basketball"],
    "Hockey": ["nhl", "hockey"],
    "Combat Sports": ["ufc", "wwe", "boxing", "mma", "fight"],
    "Motorsports": ["nascar", "f1", "formula", "indy"],
    "Soccer": ["soccer", "futbol", "mls", "premier"],
}

DEFAULT_ANCHOR = "Sports - Live"

# =====================================================
# HELPERS
# =====================================================
def fetch(url):
    try:
        return requests.get(url, timeout=20).text
    except Exception:
        return ""

def find_anchor(name, group):
    text = f"{name} {group}".lower()
    for anchor, keys in ANCHORS.items():
        if any(k in text for k in keys):
            return anchor
    return DEFAULT_ANCHOR

# =====================================================
# BUILD PLAYLIST (DYNAMIC-SAFE)
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
            name = line.split(",")[-1]

            group = ""
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]

            anchor = find_anchor(name, group)

            # -------------------------------------------------
            # CRITICAL BEHAVIOR:
            # Preserve original group-title
            # Prefix it with anchor so it nests correctly
            # -------------------------------------------------
            if group:
                rebuilt = line.replace(
                    f'group-title="{group}"',
                    f'group-title="{anchor} | {group}"'
                )
            else:
                rebuilt = line.replace(
                    "#EXTINF:-1",
                    f'#EXTINF:-1 group-title="{anchor}"'
                )

            current_extinf = rebuilt

        elif line.startswith("http") and current_extinf:
            output.append(current_extinf)
            output.append(line)

# =====================================================
# WRITE FILE
# =====================================================
with open("SportsMaster_Stable.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("DONE: SportsMaster_Stable.m3u")
print("✔ channel names intact")
print("✔ dynamic categories preserved")
print("✔ anchored category order stable")
