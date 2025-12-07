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
# >>> EDIT THESE ONLY <<<

# Paid service (Nomad IPTV)
PAID_USERNAME = "Nact6578"
PAID_PASSWORD = "Earm3432"

PAID_URL = (
    f"http://nomadiptv.online:25461/get.php?"
    f"username={PAID_USERNAME}&password={PAID_PASSWORD}&type=m3u_plus&output=ts"
)

# Free playlists (sports-focused)
free_playlists: List[str] = [
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",
]

# Optional: XMLTV EPG URLs (for live-only + better titles)
# You can include your combined EPG here if you want live detection via EPG.
epg_urls: List[str] = [

    "https://raw.githubusercontent.com/Addicted2u143/Mega-EPG/main/combined_epg_latest.xml.gz",
]
# ==========================
# 2. CATEGORY DEFINITIONS
# ==========================

CATEGORY_ORDER: List[str] = [
    "🔥 Live Events",
    "📺 Sports Networks (General)",
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
    "🏈 NFL Football": [
        "nfl", "redzone", "red zone", "nfl network", "nfln",
        "thursday night football", "monday night football",
    ],
    "🎓🏈 NCAA Football": [
        "ncaa", "college football", "cfb", "sec network", "acc network",
        "big ten network", "btn", "pac-12", "pac 12", "longhorn network",
    ],
    "🏀 NBA Basketball": [
        "nba", "national basketball association",
    ],
    "🎓🏀 NCAA Basketball": [
        "march madness", "college basketball", "ncaa basketball",
    ],
    "⚾ MLB Baseball": [
        "mlb", "major league baseball", "yes network", "mlb network",
    ],
    "🏒 NHL Hockey": [
        "nhl", "national hockey league",
    ],
    "🥊 Fight Sports / PPV": [
        "ufc", "mma", "boxing", "wwe", "aew", "bellator", "fight", "ppv",
        "pay per view", "pay-per-view",
    ],
    "🏎️ Motorsports": [
        "nascar", "indycar", "f1", "formula 1", "formula one", "motogp",
        "motorsport", "motorsports",
    ],
    "⚽ Soccer": [
        "soccer", "futbol", "football club", "premier league", "epl",
        "laliga", "la liga", "serie a", "bundesliga", "champions league",
        "ucl", "europa league", "mls",
    ],
    "⛳🎾 Golf & Tennis": [
        "golf", "pga", "ryder cup", "masters tournament",
        "tennis", "atp", "wta", "us open", "wimbledon",
    ],
    # Generic sports networks
    "📺 Sports Networks (General)": [
        "espn", "espn2", "espn u", "espnu", "espn news", "espnnews",
        "fox sports", "fs1", "fs2",
        "cbs sports", "cbssn", "sec network", "big ten network", "btn",
        "tsn", "bein", "sky sports", "sportsnet", "sport", "sports",
    ],
}

GENERIC_SPORT_WORDS: List[str] = [
    "sport", "sports", "espn", "sky sports", "fox sports",
    "tsn", "bein", "cbssn",
]

EVENT_KEYWORDS: List[str] = [
    "event", "ppv", "fight", "card", "round", "ufc", "wwe", "aew",
    "vs.", " vs ", "live event", "main event",
]

LIVE_HINTS: List[str] = [
    "live", "live now", "on air", "in progress", "en vivo",
]

# ==========================
# 3. BASIC HELPERS
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
            # reset
            logo = ""
            group = ""
            tvg_id = ""

            # Basic channel name
            parts = line.split(",", 1)
            if len(parts) == 2:
                current_name = parts[1].strip()
            else:
                current_name = line

            # Extract attributes
            if 'tvg-logo="' in line:
                logo = line.split('tvg-logo="')[1].split('"')[0]
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
            if 'tvg-id="' in line:
                tvg_id = line.split('tvg-id="')[1].split('"')[0]

        elif line.startswith("http"):
            url = line.strip()
            rows.append([
                current_name or "",
                url,
                logo,
                group,
                tvg_id,
                source,
            ])

    df = pd.DataFrame(rows, columns=["name", "url", "logo", "group", "tvg_id", "source"])
    return df

def text_contains_any(text: Optional[str], keywords: List[str]) -> bool:
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(k in t for k in keywords)

# ==========================
# 4. SPORTS / EVENT LOGIC
# ==========================

def classify_sport_category(name: str, group: str) -> str:
    name_l = name.lower() if isinstance(name, str) else ""
    group_l = group.lower() if isinstance(group, str) else ""
    combo = f"{name_l} {group_l}"

    for category, keys in SPORT_KEYWORDS.items():
        if any(k in combo for k in keys):
            return category

    # fallback: generic sports
    if any(k in combo for k in GENERIC_SPORT_WORDS):
        return "📺 Sports Networks (General)"

    return ""  # not clearly sports

def is_event_channel(name: str, group: str) -> bool:
    name_l = name.lower() if isinstance(name, str) else ""
    group_l = group.lower() if isinstance(group, str) else ""
    if any(k in name_l for k in EVENT_KEYWORDS):
        return True
    if any(k in group_l for k in EVENT_KEYWORDS):
        return True
    return False

def extract_event_number(name: str) -> Optional[int]:
    if not isinstance(name, str):
        return None
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
# 5. EPG PARSING (OPTIONAL)
# ==========================

def download_epg(epg_urls: List[str]) -> pd.DataFrame:
    if not epg_urls:
        print("No EPG URLs configured. Skipping EPG step.")
        return pd.DataFrame(columns=["channel_id", "title", "start", "stop"])

    rows = []
    for url in epg_urls:
        try:
            print(f"Fetching EPG: {url}")
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            content = resp.content

            # handle gzip
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
            print(f"Failed to parse EPG {url}: {e}")

    epg_df = pd.DataFrame(rows, columns=["channel_id", "title", "start_raw", "stop_raw"])
    if epg_df.empty:
        return epg_df

    def parse_xmltv_time(t: str):
        try:
            if " " in t:
                return dt.datetime.strptime(t, "%Y%m%d%H%M%S %z")
            else:
                return dt.datetime.strptime(t[:14], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
        except Exception:
            return None

    epg_df["start"] = epg_df["start_raw"].apply(parse_xmltv_time)
    epg_df["stop"] = epg_df["stop_raw"].apply(parse_xmltv_time)
    epg_df = epg_df.dropna(subset=["start", "stop"])

    return epg_df

def attach_current_epg(df: pd.DataFrame, epg_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or epg_df.empty:
        df["epg_title_current"] = ""
    else:
        now = dt.datetime.now(dt.timezone.utc)
        current = epg_df[(epg_df["start"] <= now) & (epg_df["stop"] >= now)].copy()

        if current.empty:
            df["epg_title_current"] = ""
        else:
            df["tvg_id_clean"] = df["tvg_id"].fillna("").astype(str).str.strip()
            current["channel_id_clean"] = current["channel_id"].fillna("").astype(str).str.strip()

            latest = current.groupby("channel_id_clean")["title"].first().reset_index()

            merged = df.merge(
                latest,
                how="left",
                left_on="tvg_id_clean",
                right_on="channel_id_clean",
            )
            merged["epg_title_current"] = merged["title"].fillna("")
            merged = merged.drop(columns=["title", "channel_id_clean"])
            df = merged

    return df

# ==========================
# 6. DOWNLOAD & MERGE PLAYLISTS
# ==========================

def load_all_playlists() -> pd.DataFrame:
    dfs = []

    # paid first so it wins when de-duping by URL
    paid_text = download_m3u(PAID_URL)
    if paid_text.strip():
        paid_df = parse_m3u(paid_text, source="paid")
        dfs.append(paid_df)
    else:
        print("Warning: paid playlist empty or failed.")

    for url in free_playlists:
        text = download_m3u(url)
        if text.strip():
            df = parse_m3u(text, source="free")
            dfs.append(df)

    if not dfs:
        raise RuntimeError("No playlists loaded. Check URLs and try again.")

    merged = pd.concat(dfs, ignore_index=True)

    # Basic cleaning
    merged["name"] = merged["name"].fillna("").astype(str).str.strip()
    merged["group"] = merged["group"].fillna("").astype(str).str.strip()

    # De-duplicate by URL, keeping paid first when same URL appears in both
    merged["source_priority"] = merged["source"].map({"paid": 0, "free": 1}).fillna(2)
    merged = merged.sort_values(by=["source_priority"]).drop_duplicates(
        subset=["url"], keep="first"
    )
    merged = merged.reset_index(drop=True)

    return merged

# ==========================
# 7. APPLY SPORTS / LIVE LOGIC
# ==========================

def enrich_sports_metadata(df: pd.DataFrame, epg_df: pd.DataFrame) -> pd.DataFrame:
    # classify categories
    df["sport_category"] = df.apply(
        lambda r: classify_sport_category(r["name"], r["group"]),
        axis=1
    )

    # keep only sports-related
    df = df[df["sport_category"] != ""].copy()

    # event flag
    df["is_event"] = df.apply(
        lambda r: is_event_channel(r["name"], r["group"]),
        axis=1
    )

    # event number (for sorting)
    df["event_number"] = df["name"].apply(extract_event_number)

    # attach EPG
    df = attach_current_epg(df, epg_df)

    # live flag (EPG or hints)
    def compute_live(row):
        epg_title = row.get("epg_title_current", "")
        if isinstance(epg_title, str) and epg_title.strip():
            return True
        return looks_live_from_name_or_group(row["name"], row["group"])

    df["is_live"] = df.apply(compute_live, axis=1)

    return df

# ==========================
# 8. BUILD "LIVE EVENTS" & CATEGORY SORTING
# ==========================

def build_live_events_block(df: pd.DataFrame) -> pd.DataFrame:
    live_events = df[(df["is_event"]) & (df["is_live"])].copy()
    if live_events.empty:
        return live_events

    # In Live Events, group-title is always "🔥 Live Events"
    live_events["output_group"] = "🔥 Live Events"

    # sort: sport category, event number, name
    live_events["cat_sort"] = live_events["sport_category"].apply(
        lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 999
    )
    live_events = live_events.sort_values(
        by=["cat_sort", "sport_category", "event_number", "name"],
        ascending=[True, True, True, True],
    )

    return live_events

def build_category_blocks(df: pd.DataFrame) -> pd.DataFrame:
    # Work on a copy so we don't mutate original
    df = df.copy()

    # inside categories: live first, then non-live, all sorted by name
    def cat_key(row):
        live_rank = 0 if row["is_live"] else 1
        return live_rank, str(row["name"]).lower()

    df["category_sort_key"] = df.apply(cat_key, axis=1)

    blocks = []
    for category in CATEGORY_ORDER:
        if category == "🔥 Live Events":
            # handled separately
            continue
        sub = df[df["sport_category"] == category].copy()
        if sub.empty:
            continue
        sub = sub.sort_values(by="category_sort_key", ascending=True)
        sub["output_group"] = category
        blocks.append(sub)

    if not blocks:
        return pd.DataFrame(columns=df.columns)

    return pd.concat(blocks, ignore_index=True)

# ==========================
# 9. EXPORT HELPERS
# ==========================

def build_display_name(row, use_epg_title: bool) -> str:
    base_name = row["name"] or "Unknown"
    if use_epg_title:
        epg_title = row.get("epg_title_current", "")
        if isinstance(epg_title, str) and epg_title.strip():
            return f"{epg_title} | {base_name}"
    return base_name

def export_m3u(df: pd.DataFrame, path: str, use_epg_title: bool) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, row in df.iterrows():
            display_name = build_display_name(row, use_epg_title)
            tvg_id = row.get("tvg_id", "") or ""
            logo = row.get("logo", "") or ""
            group_title = row.get("output_group", "") or row.get("sport_category", "")

            extinf = (
                f'#EXTINF:-1 tvg-id="{tvg_id}" '
                f'tvg-logo="{logo}" '
                f'group-title="{group_title}",{display_name}\n'
            )
            f.write(extinf)
            f.write(str(row["url"]) + "\n")

# ==========================
# 10. MASTER BUILD
# ==========================

def main():
    print("Loading playlists (paid + free)...")
    merged = load_all_playlists()
    print(f"Total unique streams by URL: {len(merged)}")

    print("Loading EPG (if configured)...")
    epg_df = download_epg(epg_urls)
    if epg_df.empty:
        print("EPG not used (empty or failed).")
    else:
        print(f"EPG rows loaded: {len(epg_df)}")

    print("Enriching sports metadata...")
    sports_df = enrich_sports_metadata(merged, epg_df)
    print(f"Sports-related streams: {len(sports_df)}")

    if sports_df.empty:
        raise RuntimeError("No sports channels detected. Check keywords or playlists.")

    print("Building Live Events block...")
    live_block = build_live_events_block(sports_df)
    print(f"Live Events channels: {len(live_block)}")

    print("Building per-category blocks with live pinned to top...")
    category_block = build_category_blocks(sports_df)

    # Final concatenation order:
    # 1) Live Events category (if any)
    # 2) All normal categories, each with live pinned at top for that category
    final_master = []
    if not live_block.empty:
        final_master.append(live_block)
    if not category_block.empty:
        final_master.append(category_block)

    if not final_master:
        raise RuntimeError("No output data. Something went wrong.")
    final_master_df = pd.concat(final_master, ignore_index=True)

    # Split paid + free
    master_paid = final_master_df.copy()
    master_free = final_master_df[final_master_df["source"] != "paid"].copy()

    # EXPORT:
    # Paid+free master
    export_m3u(master_paid, "sports_master.m3u", use_epg_title=True)
    # Free-only version
    export_m3u(master_free, "sports_master_free.m3u", use_epg_title=True)

    print("\nDone. Generated playlists:")
    print("- sports_master.m3u       (paid + free)")
    print("- sports_master_free.m3u  (free only)")


if __name__ == "__main__":
    main()
    
