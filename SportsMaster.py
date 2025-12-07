import requests
import pandas as pd
import datetime as dt
import re

# ==========================
# 1. USER SETTINGS
# ==========================

paid_username = "Nact6578"
paid_password = "Earm3432"

paid_url = (
    f"http://nomadiptv.online:25461/get.php?"
    f"username={paid_username}&password={paid_password}"
    f"&type=m3u_plus&output=ts"
)

free_playlists = [
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8"
]

SPORT_KEYWORDS = {
    "🏈 Football (NFL + NCAA FB)": [
        "nfl", "football", "redzone", "big ten", "b1g", "college football"
    ],
    "🏀 Basketball (NBA + NCAA BB)": [
        "nba", "basketball", "ncaab"
    ],
    "⚾ Baseball (MLB)": ["mlb", "baseball"],
    "🏒 Hockey (NHL)": ["nhl", "hockey"],
    "⚽ Soccer": [
        "soccer", "futbol", "premier", "laliga", "bundesliga",
        "serie a", "champions league", "ucl", "mls"
    ],
    "🥊 Combat Sports (UFC/Boxing/WWE)": [
        "ufc", "boxing", "wwe", "mma", "fight", "ppv"
    ],
    "🏎 Motorsports": ["nascar", "indycar", "f1", "formula"],
    "🎾 Golf / Tennis": ["golf", "tennis", "pga", "atp", "wta"],
    "📺 General Sports": ["espn", "fs1", "tsn", "bein", "sports"]
}

EVENT_WORDS = ["event", "ppv", "ufc", "fight", "card", "match", "round", "live"]


# ==========================
# 2. HELPERS
# ==========================

def fetch(url):
    try:
        print("Fetching:", url)
        r = requests.get(url, timeout=20)
        return r.text
    except:
        return ""


def parse_m3u(text):
    lines = text.splitlines()
    rows = []
    name = logo = group = tvg_id = None

    for line in lines:
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1].strip()

            logo = extract(line, 'tvg-logo')
            group = extract(line, 'group-title')
            tvg_id = extract(line, 'tvg-id')

        elif line.startswith("http"):
            rows.append([name, line.strip(), logo, group, tvg_id])

    return pd.DataFrame(rows, columns=["name", "url", "logo", "group", "tvg_id"])


def extract(line, key):
    if f'{key}="' in line:
        return line.split(f'{key}="')[1].split('"')[0]
    return ""


def classify(name, group):
    text = f"{name} {group}".lower()

    for category, words in SPORT_KEYWORDS.items():
        if any(w in text for w in words):
            return category

    return ""


def is_event(name, group):
    text = f"{name} {group}".lower()
    return any(w in text for w in EVENT_WORDS)


# ==========================
# 3. LOAD PLAYLISTS
# ==========================

dfs = []

paid_text = fetch(paid_url)
if paid_text:
    dfs.append(parse_m3u(paid_text))

for url in free_playlists:
    t = fetch(url)
    if t.strip():
        dfs.append(parse_m3u(t))

if not dfs:
    raise RuntimeError("No playlist data loaded.")

merged = pd.concat(dfs, ignore_index=True)
merged = merged.drop_duplicates(subset=["name"], keep="first").reset_index()


# ==========================
# 4. CLASSIFY
# ==========================

merged["category"] = merged.apply(
    lambda r: classify(r["name"], r["group"]),
    axis=1
)

merged["is_event"] = merged.apply(
    lambda r: is_event(r["name"], r["group"]),
    axis=1
)


# ==========================
# 5. SORTING (events first within categories)
# ==========================

merged["sort_event"] = merged["is_event"].apply(lambda x: 0 if x else 1)

sorted_df = merged.sort_values(
    by=["category", "sort_event", "name"],
    ascending=[True, True, True]
)


# ==========================
# 6. EXPORT M3U
# ==========================

def export(df, path):
    with open(path, "w") as f:
        f.write("#EXTM3U\n")
        for _, r in df.iterrows():
            f.write(
                f'#EXTINF:-1 tvg-id="{r["tvg_id"]}" '
                f'tvg-logo="{r["logo"]}" '
                f'group-title="{r["category"]}",{r["name"]}\n'
            )
            f.write(r["url"] + "\n")


# Full version (Nomad + free)
export(sorted_df, "sports_master.m3u")

# Family version (free only)
free_only = sorted_df[~sorted_df["url"].str.contains("nomadiptv")].copy()
export(free_only, "sports_master_free.m3u")

print("Done! Exported:")
print(" - sports_master.m3u")
print(" - sports_master_free.m3u")
