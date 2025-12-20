import requests

PLAYLISTS = [
    # CORE LIVE / EVENTS (leave untouched)
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",

    # BuddyLive
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",

    # FAST / BACKUP
    "https://pluto.freechannels.me/playlist.m3u",
    "https://nocords.xyz/pluto/playlist.m3u",
    "https://www.apsattv.com/freelivesports.m3u",
]

def fetch(url):
    try:
        return requests.get(url, timeout=30).text
    except:
        return ""

output = ["#EXTM3U"]

for url in PLAYLISTS:
    data = fetch(url)
    if not data:
        continue

    for line in data.splitlines():
        if line.startswith("#EXTINF") or line.startswith("http"):
            output.append(line)

with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("EMERGENCY BUILD COMPLETE")
