import requests
import pandas as pd
import datetime as dt
import xml.etree.ElementTree as ET
import gzip
from io import BytesIO
from typing import List, Dict, Optional

# ==========================
# 1. USER SETTINGS
# ==========================

PAID_USERNAME = "Nact6578"
PAID_PASSWORD = "Earm3432"

PAID_URL = (
    f"http://nomadiptv.online:25461/get.php?"
    f"username={PAID_USERNAME}&password={PAID_PASSWORD}&type=m3u_plus&output=ts"
)

free_playlists: List[str] = [
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",
]

epg_urls: List[str] = [
    "https://raw.githubusercontent.com/Addicted2u143/Mega-EPG/main/combined_epg_latest.xml.gz",
]

# ==========================
# 2. CATEGORY DEFINITIONS
# ==========================

CATEGORY_ORDER: List[str] = [
    "🔥 Live Events",
    "📺 Sports Networks (General)",
    "🎲 Odds, Betting & Racing",
    "🏈 NFL Football",
    "🎓🏈 NCAA Football",
    "🏀 NBA Basketball",
    "🎓🏀 NCAA Basketball",
    "⚾ MLB Baseball",
    "🏒 NHL Hockey",
    "🥊 Fight Sports / PPV",
    "🏎️ Motorsports",
    "⚽ Soccer",
    "⛳🎾 Golf & Tennis",
]

SPORT_KEYWORDS: Dict[str, List[str]] = {
    "🎲 Odds, Betting & Racing": [
        "poker", "pokergo", "world series of poker", "wsop",
        "bet", "sportsgrid", "vsin", "vegas", "odds",
        "horse racing", "tvg", "harness"
    ],
    "🏈 NFL Football": [
        "nfl", "redzone", "red zone", "nfl network", "nfln",
        "thursday night football", "monday night football",
    ],
    "🎓🏈 NCAA Football": [
        "ncaa", "college football", "cfb", "sec network", "acc network",
        "big ten network", "btn", "pac-12", "pac 12", "longhorn network",
    ],
    "🏀 NBA Basketball": ["nba"],
    "🎓🏀 NCAA Basketball": ["march madness", "college basketball", "ncaa basketball"],
    "⚾ MLB Baseball": ["mlb", "baseball", "major league"],
    "🏒 NHL Hockey": ["nhl", "hockey"],
    "🥊 Fight Sports / PPV": [
        "ufc", "mma", "boxing", "wwe", "aew", "bellator", "fight", "card", "ppv"
    ],
    "🏎️ Motorsports": ["nascar", "indycar", "f1", "formula", "motogp"],
    "⚽ Soccer": [
        "soccer", "futbol", "premier league", "epl",
        "laliga", "la liga", "serie a", "bundesliga",
        "champions league", "ucl", "europa", "mls"
    ],
    "⛳🎾 Golf & Tennis": ["golf", "pga", "tennis", "atp", "wta", "us open"],
    "📺 Sports Networks (General)": [
        "espn", "fs1", "fs2", "fox sports", "tsn", "bein",
        "sky sports", "sportsnet", "cbssn", "cbs sports", "sport"
    ],
}

GENERIC_SPORT_WORDS: List[str] = [
    "sport", "sports", "espn", "fox", "tsn", "bein", "cbs"
]

EVENT_KEYWORDS: List[str] = [
    "event", "ppv", "card", "round", "fight", "match",
    "vs.", " vs ", "main event", "featured bout"
]

LIVE_HINTS: List[str] = [
    "live", "live now", "on air", "en vivo", "ao vivo", "in progress"
]

# ==========================
# PLAYLIST PARSING
# ==========================

def download_m3u(url: str) -> str:
    try:
        print(f"Fetching playlist: {url}")
        resp = requests.get(url, timeout=40)
        resp.raise_for_status()
        return resp.text
    except:
        print(f"Failed: {url}")
        return ""

def parse_m3u(text: str, source: str) -> pd.DataFrame:
    rows = []
    current_name = ""
    logo = ""
    group = ""
    tvg_id = ""

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("#EXTINF"):
            current_name = line.split(",", 1)[1] if "," in line else line
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
            rows.append([current_name, line, logo, group, tvg_id, source])

    return pd.DataFrame(rows, columns=["name", "url", "logo", "group", "tvg_id", "source"])

# ==========================
# EPG HANDLING
# ==========================

def download_epg(epg_urls: List[str]) -> pd.DataFrame:
    rows = []
    for url in epg_urls:
        try:
            content = requests.get(url, timeout=55).content
            if url.endswith(".gz") or content[:2] == b"\x1f\x8b":
                xml_text = gzip.GzipFile(fileobj=BytesIO(content)).read().decode("utf-8", errors="ignore")
            else:
                xml_text = content.decode("utf-8", errors="ignore")

            root = ET.fromstring(xml_text)

            for p in root.findall("programme"):
                rows.append([
                    p.get("channel", "").strip(),
                    (p.findtext("title") or "").strip(),
                    p.get("start", ""),
                    p.get("stop", "")
                ])
        except:
            continue

    df = pd.DataFrame(rows, columns=["channel_id", "title", "start_raw", "stop_raw"])

    if df.empty:
        return df

    def parse_time(t):
        try:
            if " " in t:
                return dt.datetime.strptime(t, "%Y%m%d%H%M%S %z")
            return dt.datetime.strptime(t[:14], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
        except:
            return None

    df["start"] = df["start_raw"].apply(parse_time)
    df["stop"] = df["stop_raw"].apply(parse_time)
    df = df.dropna(subset=["start", "stop"])

    return df

def attach_current_epg(df, epg_df):
    if df.empty or epg_df.empty:
        df["epg_title_current"] = ""
        return df

    now = dt.datetime.now(dt.timezone.utc)
    current = epg_df[(epg_df["start"] <= now) & (epg_df["stop"] >= now)]

    df["tvg_id_clean"] = df["tvg_id"].fillna("").str.strip()
    current["channel_id_clean"] = current["channel_id"].fillna("").str.strip()

    latest = current.groupby("channel_id_clean")["title"].first().reset_index()

    merged = df.merge(latest, how="left", left_on="tvg_id_clean", right_on="channel_id_clean")
    merged["epg_title_current"] = merged["title"].fillna("")
    return merged.drop(columns=["title", "channel_id_clean"])

# ==========================
# CATEGORY LOGIC
# ==========================

def classify_category(name, group):
    combo = f"{name.lower()} {group.lower()}"
    for cat, keys in SPORT_KEYWORDS.items():
        if any(k in combo for k in keys):
            return cat
    if any(k in combo for k in GENERIC_SPORT_WORDS):
        return "📺 Sports Networks (General)"
    return ""

def load_all_playlists():
    dfs = []

    paid = download_m3u(PAID_URL)
    if paid:
        dfs.append(parse_m3u(paid, "paid"))

    for url in free_playlists:
        txt = download_m3u(url)
        if txt:
            dfs.append(parse_m3u(txt, "free"))

    merged = pd.concat(dfs, ignore_index=True)
    merged["source_priority"] = merged["source"].map({"paid": 0, "free": 1})
    merged = merged.sort_values("source_priority").drop_duplicates("url")
    return merged.reset_index(drop=True)

def enrich(df, epg_df):
    df["sport_category"] = df.apply(lambda r: classify_category(r["name"], r["group"]), axis=1)
    df = df[df["sport_category"] != ""].copy()

    df["is_event"] = df.apply(lambda r: text_contains_any(r["name"], EVENT_KEYWORDS), axis=1)

    df = attach_current_epg(df, epg_df)

    df["is_live"] = df.apply(
        lambda r: bool(r["epg_title_current"]) or text_contains_any(r["name"], LIVE_HINTS),
        axis=1
    )

    return df

def build_live(df):
    block = df[(df["is_event"]) & (df["is_live"])].copy()
    if block.empty:
        return block

    block["output_group"] = "🔥 Live Events"
    block["cat_sort"] = block["sport_category"].apply(
        lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 999
    )
    return block.sort_values(["cat_sort", "sport_category", "name"])

def build_categories(df):
    df = df.copy()
    df["sort_key"] = df.apply(
        lambda r: (0 if r["is_live"] else 1, r["name"].lower()),
        axis=1
    )

    blocks = []
    for cat in CATEGORY_ORDER:
        if cat == "🔥 Live Events":
            continue
        sub = df[df["sport_category"] == cat].copy()
        if sub.empty:
            continue
        sub["output_group"] = cat
        sub = sub.sort_values("sort_key")
        blocks.append(sub)

    return pd.concat(blocks, ignore_index=True) if blocks else pd.DataFrame()

def export_m3u(df, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, row in df.iterrows():
            name = row["epg_title_current"] + " | " + row["name"] if row["epg_title_current"] else row["name"]
            f.write(
                f'#EXTINF:-1 tvg-id="{row["tvg_id"]}" '
                f'tvg-logo="{row["logo"]}" '
                f'group-title="{row["output_group"]}",{name}\n'
            )
            f.write(row["url"] + "\n")

# ==========================
# MAIN
# ==========================

def main():
    merged = load_all_playlists()
    epg_df = download_epg(epg_urls)
    sports = enrich(merged, epg_df)

    live = build_live(sports)
    categories = build_categories(sports)

    final = []
    if not live.empty:
        final.append(live)
    final.append(categories)

    final_df = pd.concat(final)

    export_m3u(final_df, "sports_master.m3u")
    export_m3u(final_df[final_df["source"] != "paid"], "sports_master_free.m3u")

    print("Generated: sports_master.m3u + sports_master_free.m3u")

if __name__ == "__main__":
    main()
