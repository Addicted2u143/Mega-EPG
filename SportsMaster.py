# ============================================================
#   SPORTSMASTER.PY — CLEAN SPORTS-ONLY PLAYLIST GENERATOR
#   Requires: requests, pandas
# ============================================================

import requests
import pandas as pd
import datetime as dt
import xml.etree.ElementTree as ET

# ------------------------------------------------------------
# 1. USER SETTINGS — EDIT ONLY THESE TWO LINES
# ------------------------------------------------------------

paid_username = "Nact6578"
paid_password = "Earm3432"

paid_url = (
    f"http://nomadiptv.online:25461/get.php?"
    f"username={paid_username}&password={paid_password}"
    f"&type=m3u_plus&output=ts"
)

# ------------------------------------------------------------
# FREE SPORTS PLAYLIST SOURCES
# ------------------------------------------------------------

free_playlists = [
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",
]

# ------------------------------------------------------------
# SPORTS CATEGORY DEFINITIONS
# ------------------------------------------------------------

SPORT_KEYWORDS = {
    "Football (NFL + NCAA)": [
        "nfl", "football", "ncaaf", "ncaa", "redzone", "espn college", "college football"
    ],
    "Basketball (NBA + NCAA)": [
        "nba", "basketball", "ncaab", "college basketball"
    ],
    "Baseball (MLB + NCAA)": [
        "mlb", "baseball", "ncaa baseball"
    ],
    "Hockey (NHL)": [
        "nhl", "hockey"
    ],
    "Soccer / Futbol": [
        "soccer", "futbol", "premier", "uptv", "mls", "champions league",
        "bundesliga", "laliga", "serie a"
    ],
    "Combat Sports (UFC/WWE/Boxing)": [
        "ufc", "wwe", "boxing", "mma", "fight", "ppv"
    ],
    "Motorsports (F1/NASCAR/Indy)": [
        "nascar", "f1", "formula", "indy", "motogp"
    ],
    "Golf / Tennis / Other": [
        "golf", "tennis", "pga", "atp", "wta", "ryder"
    ],
}

GENERIC_SPORTS = ["sports", "espn", "bein", "tsn", "sky sports", "fs1", "fs2"]

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def download_m3u(url):
    try:
        print("Fetching:", url)
        return requests.get(url, timeout=20).text
    except:
        return ""

def parse_m3u(text):
    rows = []
    name = logo = group = tvg_id = None

    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1].strip()
            logo = ""
            group = ""
            tvg_id = ""

            if 'tvg-logo="' in line:
                logo = line.split('tvg-logo="')[1].split('"')[0]
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
            if 'tvg-id="' in line:
                tvg_id = line.split('tvg-id="')[1].split('"')[0]

        elif line.startswith("http"):
            rows.append([name, line.strip(), logo, group, tvg_id])

    return pd.DataFrame(rows, columns=["name", "url", "logo", "group", "tvg_id"])


def classify(name, group):
    text = f"{name} {group}".lower()

    for cat, keys in SPORT_KEYWORDS.items():
        if any(k in text for k in keys):
            return cat

    if any(k in text for k in GENERIC_SPORTS):
        return "General Sports"

    return None


# ------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------

dfs = []

# Pull Nomad playlist first so duplicates prefer Nomad’s versions
paid_text = download_m3u(paid_url)
if paid_text.strip():
    dfs.append(parse_m3u(paid_text))

for url in free_playlists:
    text = download_m3u(url)
    if text.strip():
        dfs.append(parse_m3u(text))

if not dfs:
    raise RuntimeError("No playlists loaded.")

merged = pd.concat(dfs, ignore_index=True)

# Remove FULL duplicates based on channel name
merged = merged.drop_duplicates(subset=["name"], keep="first").reset_index(drop=True)

# Apply category filtering
merged["category"] = merged.apply(
    lambda r: classify(r["name"], r["group"]),
    axis=1
)

sports_df = merged[merged["category"].notnull()].copy()

# Sort within category and name
sports_df = sports_df.sort_values(by=["category", "name"])

# FREE ONLY version
sports_free_df = sports_df[sports_df["url"].str.contains("BuddyChewChew")].copy()

# ------------------------------------------------------------
# EXPORT
# ------------------------------------------------------------

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


export(sports_df, "sports_master.m3u")
export(sports_free_df, "sports_master_free.m3u")

print("\nDONE! Your playlists are ready:")
print(" - sports_master.m3u  (Nomad + Free)")
print(" - sports_master_free.m3u  (FREE ONLY)")
