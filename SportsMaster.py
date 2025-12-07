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

epg_urls = [
    "https://raw.githubusercontent.com/Addicted2u143/Mega-EPG/main/combined_epg_latest.xml.gz",
]

# ==========================
# 2. CATEGORY DEFINITIONS
# ==========================

CATEGORY_ORDER: List[str] = [
    "🔥 Live Events",
    "📺 Sports Networks (General)",
    "🎲 Action & Odds",
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
    "🎲 Action & Odds": [
        "poker", "pokergo", "wsop", "world series of poker",
        "tvg", "tvg2", "harness", "horse racing",
        "vsin", "sports betting", "sportsbet", "sportsgrid",
        "wager", "odds",
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
    "🎓🏀 NCAA Basketball": ["ncaa basketball", "march madness", "college basketball"],
    "⚾ MLB Baseball": ["mlb", "major league baseball", "yes network", "mlb network"],
    "🏒 NHL Hockey": ["nhl"],
    "🥊 Fight Sports / PPV": [
        "ufc", "mma", "boxing", "wwe", "aew", "bellator",
        "fight", "ppv", "pay per view", "pay-per-view",
    ],
    "🏎️ Motorsports": [
        "nascar", "indycar", "f1", "formula 1", "formula one",
        "motogp", "motorsport",
    ],
    "⚽ Soccer": [
        "soccer", "football club", "premier league", "epl", "laliga",
        "serie a", "bundesliga", "champions league", "ucl",
    ],
    "⛳🎾 Golf & Tennis": [
        "golf", "pga", "ryder", "masters tournament",
        "tennis", "atp", "wta", "wimbledon",
    ],
    "📺 Sports Networks (General)": [
        "espn", "espn2", "espnu", "espn news", "espnnews",
        "fox sports", "fs1", "fs2",
        "cbs sports", "cbssn",
        "tsn", "bein", "sky sports", "sportsnet",
    ],
}

GENERIC_SPORT_WORDS = ["sport", "sports", "espn", "tsn", "fox sports", "bein", "cbssn"]

EVENT_KEYWORDS = [
    "event", "ppv", "fight", "card", "round", "ufc", "wwe", "aew",
    "vs.", " vs ", "live event", "main event",
]

LIVE_HINTS = [
    "live", "live now", "in progress", "on air", "en vivo",
]

# ==========================
# 3. HELPERS
# ==========================

def download_m3u(url: str) -> str:
    try:
        print(f"Fetching playlist: {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def parse_m3u(text: str, source: str) -> pd.DataFrame:
    lines = text.splitlines()
    rows = []
    current_name = None
    logo = ""
    group = ""
    tvg_id = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            logo = ""
            group = ""
            tvg_id = ""

            parts = line.split(",", 1)
            current_name = parts[1].strip() if len(parts) == 2 else line

            if 'tvg-logo="' in line:
                logo = line.split('tvg-logo="')[1].split('"')[0]
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
            if 'tvg-id="' in line:
                tvg_id = line.split('tvg-id="')[1].split('"')[0]

        elif line.startswith("http"):
            rows.append([
                current_name or "",
                line.strip(),
                logo,
                group,
                tvg_id,
                source,
            ])

    return pd.DataFrame(rows, columns=["name", "url", "logo", "group", "tvg_id", "source"])

def text_contains_any(text: Optional[str], keywords: List[str]) -> bool:
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(k in t for k in keywords)

# ==========================
# 4. CATEGORY + EVENT DETECTION
# ==========================

def classify_sport_category(name: str, group: str) -> str:
    combo = f"{name.lower()} {group.lower()}"
    for category, keys in SPORT_KEYWORDS.items():
        if any(k in combo for k in keys):
            return category
    if any(k in combo for k in GENERIC_SPORT_WORDS):
        return "📺 Sports Networks (General)"
    return ""

def is_event_channel(name: str, group: str) -> bool:
    name_l = name.lower()
    group_l = group.lower()
    return any(k in name_l for k in EVENT_KEYWORDS) or any(k in group_l for k in EVENT_KEYWORDS)

# Extract event numbers (UFC 299, Event 12, etc.)
def extract_event_number(name: str) -> Optional[int]:
    import re
    name_l = name.lower()
    patterns = [
        r"(event|ufc|wwe|aew|fight|ppv)\s*(\d+)",
        r"(\d+)\s*(event|ufc|wwe|aew|fight|ppv)",
    ]
    for pat in patterns:
        m = re.search(pat, name_l)
        if m:
            for g in m.groups()[::-1]:
                if g and g.isdigit():
                    return int(g)
    m = re.search(r"\b(\d{1,3})\b", name_l)
    if m:
        return int(m.group(1))
    return None

def looks_live_from_name_or_group(name: str, group: str) -> bool:
    return text_contains_any(name, LIVE_HINTS) or text_contains_any(group, LIVE_HINTS)

# ==========================
# 5. EPG HANDLING
# ==========================

def download_epg(epg_urls: List[str]) -> pd.DataFrame:
    rows = []
    for url in epg_urls:
        try:
            print(f"Fetching EPG: {url}")
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()

            content = resp.content
            if url.endswith(".gz") or content[:2] == b"\x1f\x8b":
                with gzip.GzipFile(fileobj=BytesIO(content)) as gz:
                    xml_text = gz.read().decode("utf-8", errors="ignore")
            else:
                xml_text = content.decode("utf-8", errors="ignore")

            root = ET.fromstring(xml_text)
            for prog in root.findall("programme"):
                chan = prog.get("channel", "").strip()
                start = prog.get("start", "")
                stop = prog.get("stop", "")
                title_el = prog.find("title")
                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                rows.append([chan, title, start, stop])

        except Exception as e:
            print(f"Failed EPG {url}: {e}")

    epg_df = pd.DataFrame(rows, columns=["channel_id", "title", "start_raw", "stop_raw"])
    if epg_df.empty:
        return epg_df

    def parse_xmltv_time(t: str):
        try:
            if " " in t:
                return dt.datetime.strptime(t, "%Y%m%d%H%M%S %z")
            return dt.datetime.strptime(t[:14], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
        except:
            return None

    epg_df["start"] = epg_df["start_raw"].apply(parse_xmltv_time)
    epg_df["stop"] = epg_df["stop_raw"].apply(parse_xmltv_time)
    return epg_df.dropna(subset=["start", "stop"])

def attach_current_epg(df: pd.DataFrame, epg_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or epg_df.empty:
        df["epg_title_current"] = ""
        return df

    now = dt.datetime.now(dt.timezone.utc)
    current = epg_df[(epg_df["start"] <= now) & (epg_df["stop"] >= now)].copy()
    if current.empty:
        df["epg_title_current"] = ""
        return df

    df["tvg_id_clean"] = df["tvg_id"].fillna("").astype(str)
    current["channel_id_clean"] = current["channel_id"].astype(str)

    current_titles = current.groupby("channel_id_clean")["title"].first().reset_index()
    merged = df.merge(
        current_titles,
        how="left",
        left_on="tvg_id_clean",
        right_on="channel_id_clean",
    )

    merged["epg_title_current"] = merged["title"].fillna("")
    return merged.drop(columns=["title", "channel_id_clean"])

# ==========================
# 6. DOWNLOAD + MERGE
# ==========================

def load_all_playlists() -> pd.DataFrame:
    dfs = []

    paid_text = download_m3u(PAID_URL)
    if paid_text.strip():
        dfs.append(parse_m3u(paid_text, "paid"))

    for url in free_playlists:
        t = download_m3u(url)
        if t.strip():
            dfs.append(parse_m3u(t, "free"))

    if not dfs:
        raise RuntimeError("No playlists loaded.")

    merged = pd.concat(dfs, ignore_index=True)
    merged["name"] = merged["name"].fillna("").astype(str)
    merged["group"] = merged["group"].fillna("").astype(str)

    merged["source_priority"] = merged["source"].map({"paid": 0, "free": 1}).fillna(2)
    merged = merged.sort_values("source_priority").drop_duplicates(subset=["url"], keep="first")

    return merged.reset_index(drop=True)

# ==========================
# 7. ENRICH SPORTS
# ==========================

def enrich_sports_metadata(df: pd.DataFrame, epg_df: pd.DataFrame) -> pd.DataFrame:
    df["sport_category"] = df.apply(
        lambda r: classify_sport_category(r["name"], r["group"]),
        axis=1
    )

    df = df[df["sport_category"] != ""].copy()

    df["is_event"] = df.apply(
        lambda r: is_event_channel(r["name"], r["group"]),
        axis=1
    )
    df["event_number"] = df["name"].apply(extract_event_number)

    df = attach_current_epg(df, epg_df)

    def compute_live(row):
        if isinstance(row.get("epg_title_current", ""), str) and row["epg_title_current"].strip():
            return True
        return looks_live_from_name_or_group(row["name"], row["group"])

    df["is_live"] = df.apply(compute_live, axis=1)
    return df

# ==========================
# 8. BUILD CATEGORY DATA
# ==========================

def build_live_events_block(df: pd.DataFrame) -> pd.DataFrame:
    live = df[(df["is_event"]) & (df["is_live"])].copy()
    if live.empty:
        return live

    live["output_group"] = "🔥 Live Events"
    live["cat_sort"] = live["sport_category"].apply(
        lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 999
    )

    return live.sort_values(
        ["cat_sort", "sport_category", "event_number", "name"]
    )

def build_category_blocks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["category_sort_key"] = df.apply(
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
        sub = sub.sort_values("category_sort_key")
        sub["output_group"] = cat
        blocks.append(sub)

    if not blocks:
        return pd.DataFrame()
    return pd.concat(blocks, ignore_index=True)

# ==========================
# 9. EXPORT M3U
# ==========================

def build_display_name(row, use_epg_title: bool) -> str:
    base = row["name"] or "Unknown"
    epg = row.get("epg_title_current", "")
    if use_epg_title and isinstance(epg, str) and epg.strip():
        return f"{epg} | {base}"
    return base

def export_m3u(df: pd.DataFrame, path: str, use_epg_title: bool):
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, r in df.iterrows():
            name = build_display_name(r, use_epg_title)
            ext = (
                f'#EXTINF:-1 tvg-id="{r["tvg_id"]}" '
                f'tvg-logo="{r["logo"]}" '
                f'group-title="{r["output_group"]}",{name}\n'
            )
            f.write(ext)
            f.write(str(r["url"]) + "\n")

# ==========================
# 10. MAIN BUILD
# ==========================

def main():
    print("Loading playlists…")
    merged = load_all_playlists()
    print(f"Streams loaded: {len(merged)}")

    print("Loading EPG…")
    epg_df = download_epg(epg_urls)
    print(f"EPG rows: {len(epg_df)}")

    print("Classifying sports…")
    sports = enrich_sports_metadata(merged, epg_df)
    print(f"Sports channels: {len(sports)}")

    print("Building Live Events…")
    live_block = build_live_events_block(sports)

    print("Building categories…")
    category_block = build_category_blocks(sports)

    final_blocks = []
    if not live_block.empty:
        final_blocks.append(live_block)
    final_blocks.append(category_block)

    final_df = pd.concat(final_blocks, ignore_index=True)

    # PAID+FREE version
    export_m3u(final_df, "sports_master.m3u", use_epg_title=True)

    # FREE mirror version (identical except removing paid)
    free_df = final_df[final_df["source"] != "paid"].copy()
    export_m3u(free_df, "sports_master_free.m3u", use_epg_title=True)

    print("Done! Generated:")
    print(" - sports_master.m3u")
    print(" - sports_master_free.m3u")

if __name__ == "__main__":
    main()
    
