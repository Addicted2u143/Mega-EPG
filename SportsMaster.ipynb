import requests
import pandas as pd
import re

# ============================================================
# 1. FREE PLAYLIST SOURCES (AUTO-CLEANED)
# ============================================================

RAW_FREE_PLAYLISTS = [
    "https://www.apsattv.com/10fast.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_abcnews.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/refs/heads/master/streams/us_adultswim.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_amagi.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/uk_bbc.m3u",
    "https://github.com/BuddyChewChew/buddylive/blob/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_canelatv.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_cbsn.m3u",
    "https://github.com/BuddyChewChew/iptv/blob/main/M3U8/base.m3u8",
    "https://github.com/BuddyChewChew/iptv/blob/main/M3U8/TV.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://github.com/BuddyChewChew/iptv/blob/main/M3U8/events.m3u8",
    "https://www.apsattv.com/cineverse.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_cineversetv.m3u",
    "https://www.apsattv.com/distro.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_distro.m3u",
    "https://www.apsattv.com/firetv.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_firetv.m3u",
    "https://pluto.freechannels.me/playlist.m3u",
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freemoviesplus.m3u",
    "https://www.apsattv.com/freetv.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_frequency.m3u",
    "https://www.apsattv.com/galxytv.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_glewedtv.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/au.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/ca.m3u",
    "https://iptv-org.github.io/iptv/languages/eng.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/uk.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_30a.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_3abn.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_klowdtv.m3u",
    "https://www.apsattv.com/klowd.m3u",
    "https://www.apsattv.com/gblg.m3u",
    "https://www.apsattv.com/uslg.m3u",
    "https://www.apsattv.com/localnow.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_local.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_moveonjoy.m3u",
    "https://github.com/iptv-org/iptv/blob/master/streams/us_pbs.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
]

def normalize_url(url):
    if url.endswith(".xml") or "bit.ly" in url or "merged_playlist" in url:
        return None
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url

FREE_PLAYLISTS = [u for u in (normalize_url(x) for x in RAW_FREE_PLAYLISTS) if u]

# ============================================================
# 2. FINAL CATEGORY SYSTEM (LOCKED)
# ============================================================

SPORT_KEYWORDS = {
    "📺 Sports Networks (General)": [
        "espn", "fox sports", "cbs sports", "nbc sports",
        "bein", "sportsnet", "tsn", "sky sports"
    ],
    "🎲 Action & Odds": [
        "vsin", "fanduel", "sportsgrid", "poker", "bet", "odds"
    ],
    "🐎 Horse Racing": [
        "horse", "racing", "tvg", "tvg2", "fanduel racing"
    ],
    "🏈 NFL Football": [
        "nfl", "redzone"
    ],
    "🏉 NCAA Football": [
        "ncaaf", "college football", "sec network",
        "acc network", "big ten", "b1g", "pac-12"
    ],
    "🏀 NBA Basketball": [
        "nba"
    ],
    "🏀 NCAA Basketball": [
        "ncaab", "college basketball", "march madness"
    ],
    "⚾ MLB Baseball": [
        "mlb", "baseball"
    ],
    "🏒 NHL Hockey": [
        "nhl", "hockey"
    ],
    "🥊 Fight Sports / PPV": [
        "ufc", "boxing", "mma", "wwe", "aew", "ppv", "fight"
    ],
    "🎣 Fishing & Hunting": [
        "fishing", "hunting", "outdoor", "sportsman"
    ],
    "🏎️ Motorsports": [
        "nascar", "f1", "formula", "indycar", "motogp"
    ],
    "⚽ Soccer": [
        "soccer", "futbol", "premier", "epl", "laliga",
        "serie a", "bundesliga", "ligue 1", "mls", "ucl"
    ],
    "⛳ Golf & Tennis": [
        "golf", "tennis", "pga", "liv golf", "atp", "wta"
    ],
    "📦 Sports Everything Else": [
        "sports"
    ],
}

LIVE_HINTS = [
    "live", "on air", "in progress", "pregame",
    "postgame", "vs", " v ", "event", "round", "match"
]

# ============================================================
# 3. HELPERS
# ============================================================

def clean_name(name):
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\s+HD$", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def download_m3u(url):
    try:
        return requests.get(url, timeout=20).text
    except:
        return ""

def parse_m3u(text):
    rows = []
    name = logo = group = tvg_id = None

    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            name = clean_name(line.split(",")[-1].strip())
            logo = re.search(r'tvg-logo="([^"]*)"', line)
            group = re.search(r'group-title="([^"]*)"', line)
            tvg_id = re.search(r'tvg-id="([^"]*)"', line)
        elif line.startswith("http") and name:
            rows.append({
                "name": name,
                "url": line.strip(),
                "logo": logo.group(1) if logo else "",
                "group": group.group(1) if group else "",
                "tvg_id": tvg_id.group(1) if tvg_id else ""
            })
            name = None
    return pd.DataFrame(rows)

def classify_category(name, group):
    combo = f"{name} {group}".lower()
    for cat, keys in SPORT_KEYWORDS.items():
        if any(k in combo for k in keys):
            return cat
    return None

def looks_live(name, group):
    combo = f"{name} {group}".lower()
    return any(k in combo for k in LIVE_HINTS)

# ============================================================
# 4. LOAD + PROCESS
# ============================================================

dfs = []
for url in FREE_PLAYLISTS:
    text = download_m3u(url)
    if text.strip():
        dfs.append(parse_m3u(text))

df = pd.concat(dfs, ignore_index=True)

df["category"] = df.apply(lambda r: classify_category(r["name"], r["group"]), axis=1)
df = df[df["category"].notna()]
df["is_live"] = df.apply(lambda r: looks_live(r["name"], r["group"]), axis=1)

df = df.drop_duplicates(subset="url", keep="first")

# ============================================================
# 5. BUILD SORTED PLAYLIST
# ============================================================

blocks = []
for cat in SPORT_KEYWORDS.keys():
    block = df[df["category"] == cat]
    if block.empty:
        continue
    live = block[block["is_live"]].sort_values("name")
    rest = block[~block["is_live"]].sort_values("name")
    blocks.append((cat, pd.concat([live, rest])))

# ============================================================
# 6. EXPORT
# ============================================================

with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for cat, dfc in blocks:
        for _, r in dfc.iterrows():
            f.write(
                f'#EXTINF:-1 tvg-id="{r.tvg_id}" tvg-logo="{r.logo}" '
                f'group-title="{cat}",{r.name}\n'
            )
            f.write(r.url + "\n")

print("Done. Created sports_master.m3u (FREE ONLY, FINAL v1)")
