import requests

PLAYLISTS = [
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",

    "https://pluto.freechannels.me/playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
]

BUCKETS = [
    ("Poker & Sports Betting", ["poker", "bet"]),
    ("Horse Racing", ["horse"]),
    ("Football", ["football", "nfl"]),
    ("Basketball", ["basketball", "nba"]),
    ("Baseball", ["baseball", "mlb"]),
    ("Hockey", ["hockey", "nhl"]),
    ("Fight Sports / PPV", ["ufc", "boxing", "mma", "wwe"]),
    ("Motorsports", ["nascar", "f1"]),
    ("Soccer", ["soccer", "mls"]),
]

DEFAULT_BUCKET = "Sports Networks (General)"

def fetch(url):
    try:
        return requests.get(url, timeout=20).text
    except:
        return ""

def classify(name):
    n = name.lower()
    for bucket, keys in BUCKETS:
        if any(k in n for k in keys):
            return bucket
    return DEFAULT_BUCKET

output = ["#EXTM3U"]
seen = set()
current = None

for url in PLAYLISTS:
    text = fetch(url)
    if not text:
        continue

    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1]
            group = classify(name)
            current = f'#EXTINF:-1 group-title="{group}",{name}'
        elif line.startswith("http") and current:
            if line in seen:
                continue
            seen.add(line)
            output.append(current)
            output.append(line)

with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("sports_master.m3u built")
