import os
import re
import gzip
import json
import requests
import datetime as dt
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape
from io import BytesIO
from typing import List, Dict, Optional, Tuple

import pandas as pd

# ==========================
# 1. USER / ENV SETTINGS
# ==========================

# Nomad credentials from environment (GitHub Secrets: NOMAD_USER / NOMAD_PASS)
NOMAD_USER = os.environ.get("NOMAD_USER", "").strip()
NOMAD_PASS = os.environ.get("NOMAD_PASS", "").strip()

if not NOMAD_USER or not NOMAD_PASS:
    raise RuntimeError("Nomad credentials missing. Check GitHub Secrets NOMAD_USER / NOMAD_PASS.")

PAID_URL = (
    f"http://nomadiptv.online:25461/get.php?"
    f"username={NOMAD_USER}&password={NOMAD_PASS}&type=m3u_plus&output=ts"
)

# Nomad EPG (primary)
NOMAD_EPG_URL = (
    f"http://nomadiptv.online:25461/xmltv.php?"
    f"username={NOMAD_USER}&password={NOMAD_PASS}"
)

# EPGShare (secondary)
EPGSHARE_URL = "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz"

# Sports-focused free playlists
FREE_PLAYLISTS: List[str] = [
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",
]

# Where to write outputs
OUT_MASTER_PRO = "sports_master.m3u"
OUT_MASTER_FREE = "sports_master_free.m3u"
OUT_EPG_XML = "sports_master_epg.xml"
OUT_EPG_GZ = "sports_master_epg.xml.gz"

CHANNEL_MAP_PATH = "channel_map.json"

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
    "🥊 Fight Sports/PPV",
	"🏎️ Motorsports",
    "⚽ Soccer",
    "⛳🎾 Golf & Tennis",
    "📦 Sports Everything Else",
]

# Core sports categories
SPORT_KEYWORDS: Dict[str, List[str]] = {
    "🎲 Action & Odds": ["betting", "gambling", "poker", "pokergo", "horse", "fandual racing", "tvg", "sportsgrid", "vsin", "wsop", "odds"
    ],
    "🏈 NFL Football": [
        "nfl", "redzone", "red zone", "nfl network", "nfln",
        "thursday night football", "monday night football", "sunday night football",
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
      "🥊 Fight Sports/PPV": ["boxing", "mma", "wrestling", "ufc", "bellator"
    ],
    "⚽ Soccer": [
        "soccer", "futbol", "football club", "premier league", "epl",
        "laliga", "la liga", "serie a", "bundesliga", "champions league",
        "ucl", "europa league", "mls",
    ],
    "⛳🎾 Golf & Tennis": [
        "golf", "pga", "ryder cup", "masters tournament",
        "tennis", "atp", "wta", "us open", "wimbledon", "roland garros",
    ],
    # Generic sports networks
    "📺 Sports Networks (General)": [
        "espn", "espn2", "espn u", "espnu", "espn news", "espnnews",
        "fox sports", "fs1", "fs2",
        "cbs sports", "cbssn",
        "sec network", "acc network", "big ten network", "btn",
        "tsn", "bein", "sky sports", "sportsnet", "tnt sports",
    ],
    "🏎️ Motorsports": ["motorsport", "nascar", "sports",
    ],
}

# Action & Odds (betting, poker, horse racing, studio shows)
ACTION_ODDS_KEYWORDS: List[str] = [
    "vsin", "vsiñ", "v-sin",
    "sportsgrid", "sports grid",
    "tvg", "tvg2", "tvg 2",
    "fanduel", "fan duel",
    "racing", "horse racing", "twinspires", "fan duel racing",
    "poker", "world series of poker", "wsop",
    "draftkings", "betmgm", "pointsbet",
    "sports betting", "betting network", "odds",
]

# Generic sport detector
GENERIC_SPORT_WORDS: List[str] = [
    "sport", "sports", "deportes", "espn", "fox sports", "sky sports",
    "tsn", "bein", "cbssn", "nba tv", "nfl network",
]

# Event keywords (for event-style channels)
EVENT_KEYWORDS: List[str] = [
    "event", "ppv", "fight", "card", "round", "ufc", "wwe", "aew",
    " vs ", " vs.", " v ", " at ", "@", "live event", "main event",
]

# Live hints in titles or groups
LIVE_HINTS: List[str] = [
    "live", "live now", "on air", "in progress", "en vivo",
]

# Country / language prefixes to strip from names
PREFIXES_TO_STRIP: List[str] = [
    "usa", "uk", "ca", "ar", "br", "mx", "de", "es", "fr", "au", "pt", "it",
]

# ==========================
# 3. UTILITIES
# ==========================

def safe_lower(s: Optional[str]) -> str:
    return s.lower() if isinstance(s, str) else ""


def strip_country_prefix(name: str) -> str:
    """Remove leading 'USA:', 'UK -', etc."""
    if not isinstance(name, str):
        return ""
    n = name.strip()
    # e.g. "USA: ESPN", "UK - Sky Sports", "DE | Sport1"
    m = re.match(r"^([A-Za-z]{2,3})\s*[:|\-]\s*(.+)$", n)
    if m:
        prefix = m.group(1).lower()
        if prefix in PREFIXES_TO_STRIP:
            return m.group(2).strip()
    return n


def text_contains_any(text: Optional[str], keywords: List[str]) -> bool:
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(k in t for k in keywords)


def download_text(url: str, timeout: int = 30) -> str:
    try:
        print(f"Fetching: {url}")
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""


def download_bytes(url: str, timeout: int = 60) -> Optional[bytes]:
    try:
        print(f"Fetching EPG: {url}")
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print(f"Failed to fetch EPG {url}: {e}")
        return None

# ==========================
# 4. PLAYLIST PARSING
# ==========================

def parse_m3u(text: str, source: str) -> pd.DataFrame:
    lines = text.splitlines()
    rows = []
    current_name = None
    logo = ""
    group = ""
    tvg_id = ""
    tvg_name = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            logo = ""
            group = ""
            tvg_id = ""
            tvg_name = ""

            parts = line.split(",", 1)
            if len(parts) == 2:
                current_name = parts[1].strip()
            else:
                current_name = line

            # attributes
            if 'tvg-logo="' in line:
                logo = line.split('tvg-logo="')[1].split('"')[0]
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
            if 'tvg-id="' in line:
                tvg_id = line.split('tvg-id="')[1].split('"')[0]
            if 'tvg-name="' in line:
                tvg_name = line.split('tvg-name="')[1].split('"')[0]

        elif line.startswith("http"):
            url = line.strip()
            rows.append([
                current_name or "",
                url,
                logo,
                group,
                tvg_id,
                tvg_name,
                source,
            ])

    df = pd.DataFrame(
        rows,
        columns=["name", "url", "logo", "group", "tvg_id", "tvg_name", "source"],
    )
    return df


def load_all_playlists() -> pd.DataFrame:
    dfs = []

    # Paid (Nomad) first so it wins on duplicate URLs
    paid_text = download_text(PAID_URL, timeout=40)
    if paid_text.strip():
        dfs.append(parse_m3u(paid_text, source="paid"))
    else:
        print("Warning: paid playlist empty or failed.")

    for url in FREE_PLAYLISTS:
        text = download_text(url, timeout=40)
        if text.strip():
            dfs.append(parse_m3u(text, source="free"))

    if not dfs:
        raise RuntimeError("No playlists loaded. Check URLs and try again.")

    merged = pd.concat(dfs, ignore_index=True)

    # Clean names / groups
    merged["name"] = merged["name"].fillna("").astype(str).apply(strip_country_prefix)
    merged["group"] = merged["group"].fillna("").astype(str).str.strip()
    merged["tvg_id"] = merged["tvg_id"].fillna("").astype(str).str.strip()
    merged["tvg_name"] = merged["tvg_name"].fillna("").astype(str).str.strip()

    # Mark source priority (paid wins on URL dupes)
    merged["source_priority"] = merged["source"].map({"paid": 0, "free": 1}).fillna(2)
    merged = merged.sort_values(by=["source_priority"]).drop_duplicates(
        subset=["url"], keep="first"
    )
    merged = merged.reset_index(drop=True)

    print(f"Total unique streams by URL: {len(merged)}")
    return merged

# ==========================
# 5. EPG PARSING & MERGE
# ==========================

def parse_xmltv_time(t: str) -> Optional[dt.datetime]:
    if not t:
        return None
    try:
        # Handle "YYYYMMDDHHMMSS +0000" or "YYYYMMDDHHMMSS+0000"
        t = t.strip()
        if " " in t:
            return dt.datetime.strptime(t, "%Y%m%d%H%M%S %z")
        elif "+" in t or "-" in t[14:]:
            # timezone packed at end
            base = t[:14]
            off = t[14:]
            return dt.datetime.strptime(base + " " + off, "%Y%m%d%H%M%S %z")
        else:
            # assume UTC
            return dt.datetime.strptime(t[:14], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def load_epg_sources() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      channels_df: channel_id, name (best display-name), source
      progs_df: channel_id, title, start_dt, stop_dt, source
    """
    rows_prog = []
    rows_chan = []

    epg_sources = [
        ("nomad", NOMAD_EPG_URL),
        ("epgshare", EPGSHARE_URL),
    ]

    for source_name, url in epg_sources:
        raw = download_bytes(url)
        if raw is None:
            continue

        # decompress if gz
        if url.endswith(".gz") or raw[:2] == b"\x1f\x8b":
            try:
                with gzip.GzipFile(fileobj=BytesIO(raw)) as gz:
                    xml_text = gz.read().decode("utf-8", errors="ignore")
            except Exception as e:
                print(f"Failed to gunzip EPG {url}: {e}")
                continue
        else:
            xml_text = raw.decode("utf-8", errors="ignore")

        try:
            root = ET.fromstring(xml_text)
        except Exception as e:
            print(f"Failed to parse XML from {url}: {e}")
            continue

        # channels
        for ch in root.findall("channel"):
            cid = ch.get("id", "").strip()
            if not cid:
                continue
            # pick first display-name as label
            name_els = ch.findall("display-name")
            label = ""
            if name_els:
                for el in name_els:
                    if el.text and el.text.strip():
                        label = el.text.strip()
                        break
            rows_chan.append([cid, label, source_name])

        # programmes
        for prog in root.findall("programme"):
            cid = prog.get("channel", "").strip()
            if not cid:
                continue
            start_raw = prog.get("start", "")
            stop_raw = prog.get("stop", "")
            title_el = prog.find("title")
            title = title_el.text.strip() if title_el is not None and title_el.text else ""

            rows_prog.append([cid, title, start_raw, stop_raw, source_name])

    channels_df = pd.DataFrame(rows_chan, columns=["channel_id", "label", "source"])
    progs_df = pd.DataFrame(rows_prog, columns=["channel_id", "title", "start_raw", "stop_raw", "source"])

    if not progs_df.empty:
        progs_df["start_dt"] = progs_df["start_raw"].apply(parse_xmltv_time)
        progs_df["stop_dt"] = progs_df["stop_raw"].apply(parse_xmltv_time)
        progs_df = progs_df.dropna(subset=["start_dt", "stop_dt"])

    return channels_df, progs_df


def build_epg_index(channels_df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Build a lookup for channel_id and fuzzy name matching.
    """
    index = {
        "by_id": {},
        "by_name": {},  # normalized_name -> set(channel_id)
    }

    for _, row in channels_df.iterrows():
        cid = str(row["channel_id"]).strip()
        label = str(row["label"] or "").strip()
        if not cid:
            continue
        index["by_id"].setdefault(cid, set()).add(label)

        # normalized name
        base = label.lower()
        base = re.sub(r"[^a-z0-9]+", " ", base).strip()
        if not base:
            continue
        index["by_name"].setdefault(base, set()).add(cid)

    return index


def fuzzy_match_channel(epg_index: Dict, name: str) -> Optional[str]:
    """
    Very light fuzzy: normalize name and try to match to EPG channel labels.
    """
    if not isinstance(name, str):
        return None
    if not epg_index or "by_name" not in epg_index:
        return None

    base = name.lower()
    base = re.sub(r"[^a-z0-9]+", " ", base).strip()
    if not base:
        return None

    # exact normalized hit
    if base in epg_index["by_name"]:
        # return first candidate
        return next(iter(epg_index["by_name"][base]))

    # loose contains match
    for key, cids in epg_index["by_name"].items():
        if base in key or key in base:
            return next(iter(cids))

    return None


def attach_current_epg(
    df: pd.DataFrame,
    channels_df: pd.DataFrame,
    progs_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Attach current EPG title with priority:
      1) match by tvg_id
      2) match by tvg_name (if present in channel labels)
      3) fuzzy match by channel name
    Source priority:
      nomad > epgshare
    """
    df = df.copy()
    if progs_df.empty:
        df["epg_title_current"] = ""
        return df

    now = dt.datetime.now(dt.timezone.utc)

    # Filter programmes that are on-air now
    current = progs_df[
        (progs_df["start_dt"] <= now) & (progs_df["stop_dt"] >= now)
    ].copy()
    if current.empty:
        df["epg_title_current"] = ""
        return df

    # Build index of EPG channels
    epg_index = build_epg_index(channels_df)

    # Priority for EPG source
    source_priority = {"nomad": 0, "epgshare": 1}

    def find_channel_epg(row) -> str:
        # 1) by tvg_id
        tvg_id = str(row.get("tvg_id", "")).strip()
        tvg_name = str(row.get("tvg_name", "")).strip()
        name = str(row.get("name", "")).strip()

        # Helper to pick best from a channel_id
        def best_for_channel(cid: str) -> Optional[str]:
            if not cid:
                return None
            subset = current[current["channel_id"] == cid]
            if subset.empty:
                return None
            subset = subset.copy()
            subset["prio"] = subset["source"].map(source_priority).fillna(9)
            subset = subset.sort_values(by=["prio", "start_dt"], ascending=[True, False])
            return str(subset.iloc[0]["title"])

        # by tvg_id
        if tvg_id:
            title = best_for_channel(tvg_id)
            if title:
                return title

        # 2) by tvg_name matching EPG channel labels
        if tvg_name:
            cid = fuzzy_match_channel(epg_index, tvg_name)
            if cid:
                title = best_for_channel(cid)
                if title:
                    return title

        # 3) fuzzy by channel name
        if name:
            cid = fuzzy_match_channel(epg_index, name)
            if cid:
                title = best_for_channel(cid)
                if title:
                    return title

        return ""

    df["epg_title_current"] = df.apply(find_channel_epg, axis=1)
    return df

# ==========================
# 6. SPORTS / CATEGORY LOGIC
# ==========================

def classify_sport_category(name: str, group: str) -> str:
    name_l = safe_lower(name)
    group_l = safe_lower(group)
    combo = f"{name_l} {group_l}"

    # Action & Odds first (poker, betting, horse racing, etc.)
    if text_contains_any(combo, ACTION_ODDS_KEYWORDS):
        return "🎲 Action & Odds"

    # Specific sports
    for cat, keys in SPORT_KEYWORDS.items():
        if any(k in combo for k in keys):
            return cat

    # Generic sports networks
    if any(k in combo for k in GENERIC_SPORT_WORDS):
        return "📺 Sports Networks (General)"

    # If it's clearly sports but not matched, we'll mark later as "Everything Else"
    return ""


def compute_sportish_flag(name: str, group: str) -> bool:
    combo = f"{safe_lower(name)} {safe_lower(group)}"
    if any(k in combo for k in GENERIC_SPORT_WORDS):
        return True
    if any(k in combo for k in ["league", "cup", "fc", "club", "arena", "stadium"]):
        return True
    return False


def is_event_channel(name: str, group: str) -> bool:
    combo = f"{safe_lower(name)} {safe_lower(group)}"
    return text_contains_any(combo, EVENT_KEYWORDS)


def extract_event_number(name: str) -> Optional[int]:
    if not isinstance(name, str):
        return None
    s = name.lower()
    # basic patterns: UFC 298, Event 12, etc
    m = re.search(r"(ufc|event|fight|ppv)\s*(\d{1,4})", s)
    if m:
        try:
            return int(m.group(2))
        except Exception:
            return None
    m = re.search(r"\b(\d{1,4})\b", s)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def looks_live_from_meta(name: str, group: str, epg_title: str) -> bool:
    if text_contains_any(epg_title, ["live"]):
        return True
    if text_contains_any(name, LIVE_HINTS):
        return True
    if text_contains_any(group, LIVE_HINTS):
        return True
    return False


def apply_channel_map(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optional channel_map.json to force categories / rename specific channels.
    Format:
    {
      "by_name": {
        "vsin": {
          "canonical_name": "VSiN",
          "force_category": "🎲 Action & Odds"
        },
        ...
      }
    }
    """
    if not os.path.exists(CHANNEL_MAP_PATH):
        return df

    try:
        with open(CHANNEL_MAP_PATH, "r", encoding="utf-8") as f:
            cmap = json.load(f)
    except Exception as e:
        print(f"Failed to load {CHANNEL_MAP_PATH}: {e}")
        return df

    by_name = cmap.get("by_name", {})
    if not by_name:
        return df

    df = df.copy()
    for idx, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        key = name.lower()
        if key in by_name:
            info = by_name[key]
            canon = info.get("canonical_name")
            force_cat = info.get("force_category")
            if canon:
                df.at[idx, "name"] = canon
            if force_cat:
                df.at[idx, "sport_category"] = force_cat
    return df

# ==========================
# 7. ENRICH & BUILD BLOCKS
# ==========================

def enrich_sports(df: pd.DataFrame, channels_df: pd.DataFrame, progs_df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # classify categories
    df["sport_category"] = df.apply(
        lambda r: classify_sport_category(r["name"], r["group"]),
        axis=1,
    )

    # broad sports flag
    df["is_sportish"] = df.apply(
        lambda r: compute_sportish_flag(r["name"], r["group"]),
        axis=1,
    )

    # If no category but clearly sports -> "Everything Else"
    df.loc[(df["sport_category"] == "") & (df["is_sportish"]), "sport_category"] = "📦 Sports Everything Else"

    # Keep only sports
    df = df[df["sport_category"] != ""].copy()

    # event flag
    df["is_event"] = df.apply(
        lambda r: is_event_channel(r["name"], r["group"]),
        axis=1,
    )

    # event number
    df["event_number"] = df["name"].apply(extract_event_number)

    # attach current EPG title
    df = attach_current_epg(df, channels_df, progs_df)

    # live flag
    df["is_live"] = df.apply(
        lambda r: looks_live_from_meta(
            str(r.get("name", "")),
            str(r.get("group", "")),
            str(r.get("epg_title_current", "")),
        ),
        axis=1,
    )

    # Apply optional channel_map for overrides
    df = apply_channel_map(df)

    return df


def build_live_events_block(df: pd.DataFrame) -> pd.DataFrame:
    live_events = df[(df["is_event"]) & (df["is_live"])].copy()
    if live_events.empty:
        return live_events

    live_events["output_group"] = "🔥 Live Events"

    def cat_index(cat: str) -> int:
        return CATEGORY_ORDER.index(cat) if cat in CATEGORY_ORDER else 999

    live_events["cat_sort"] = live_events["sport_category"].apply(cat_index)
    live_events = live_events.sort_values(
        by=["cat_sort", "sport_category", "event_number", "name"],
        ascending=[True, True, True, True],
    )

    return live_events


def build_category_blocks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # inside category: live first, then name
    def sort_key(row):
        return (0 if row["is_live"] else 1, safe_lower(row["name"]))

    df["category_sort_key"] = df.apply(sort_key, axis=1)

    blocks = []
    for category in CATEGORY_ORDER:
        if category == "🔥 Live Events":
            continue
        sub = df[df["sport_category"] == category].copy()
        if sub.empty:
            continue
        sub = sub.sort_values(by="category_sort_key")
        sub["output_group"] = category
        blocks.append(sub)

    if not blocks:
        return pd.DataFrame(columns=df.columns)

    return pd.concat(blocks, ignore_index=True)


def build_display_name(row, use_epg_title: bool) -> str:
    base_name = row.get("name") or "Unknown"
    if use_epg_title:
        epg = row.get("epg_title_current", "")
        if isinstance(epg, str) and epg.strip():
            # Prefer event-style titles if they look like matchups
            title_l = epg.lower()
            if any(t in title_l for t in [" vs ", " vs.", " at ", "@"]):
                return f"{epg} | {base_name}"
            return f"{epg} | {base_name}"
    return base_name


def export_m3u(df: pd.DataFrame, path: str, use_epg_title: bool) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, row in df.iterrows():
            display_name = build_display_name(row, use_epg_title)
            tvg_id = str(row.get("tvg_id") or "")
            logo = str(row.get("logo") or "")
            group_title = str(row.get("output_group") or row.get("sport_category") or "")

            extinf = (
                f'#EXTINF:-1 tvg-id="{tvg_id}" '
                f'tvg-logo="{logo}" '
                f'group-title="{group_title}",{display_name}\n'
            )
            f.write(extinf)
            f.write(str(row["url"]) + "\n")


def export_sports_epg(progs_df: pd.DataFrame, used_channel_ids: List[str]) -> None:
    """
    Write a trimmed XMLTV containing only the channel_ids used in the sports playlists.
    """
    if progs_df.empty or not used_channel_ids:
        print("No EPG or no used channels; skipping sports_master_epg.xml export.")
        return

    used_set = set(str(cid).strip() for cid in used_channel_ids if cid)

    subset = progs_df[progs_df["channel_id"].isin(used_set)].copy()
    if subset.empty:
        print("No matching EPG programmes for sports channels.")
        return

    # Write minimal TV XML
    with open(OUT_EPG_XML, "w", encoding="utf-8") as f:
        f.write('<tv>\n')
        for _, row in subset.iterrows():
            cid = row["channel_id"]
            title = row["title"]
            start_raw = row["start_raw"]
            stop_raw = row["stop_raw"]

            f.write(
                f'<programme channel="{cid}" start="{start_raw}" stop="{stop_raw}">'
            )
            safe_title = xml_escape(title) if isinstance(title, str) else ""
            f.write(f"<title>{safe_title}</title>")
            f.write("</programme>\n")
        f.write("</tv>\n")

    # Gzip it
    with open(OUT_EPG_XML, "rb") as src, gzip.open(OUT_EPG_GZ, "wb") as gz:
        gz.write(src.read())

    print(f"Exported sports EPG: {OUT_EPG_XML} and {OUT_EPG_GZ}")

# ==========================
# 8. MAIN
# ==========================

def main():
    print("Loading playlists…")
    merged = load_all_playlists()

    print("Loading EPG sources…")
    channels_df, progs_df = load_epg_sources()
    if progs_df.empty:
        print("Warning: EPG empty or failed; continuing without EPG live detection.")

    print("Classifying sports & enriching…")
    sports_df = enrich_sports(merged, channels_df, progs_df)
    print(f"Sports-related streams: {len(sports_df)}")

    if sports_df.empty:
        raise RuntimeError("No sports channels detected. Check keywords or playlists.")

    print("Building Live Events…")
    live_block = build_live_events_block(sports_df)
    print(f"Live events count: {len(live_block)}")

    print("Building category blocks…")
    category_block = build_category_blocks(sports_df)

    final_blocks = []
    if not live_block.empty:
        final_blocks.append(live_block)
    if not category_block.empty:
        final_blocks.append(category_block)

    if not final_blocks:
        raise RuntimeError("No output data; something went wrong.")

    final_master = pd.concat(final_blocks, ignore_index=True)

    # PRO = paid + free
    master_pro = final_master.copy()
    # FREE = exclude paid source
    master_free = final_master[final_master["source"] != "paid"].copy()

    print(f"Exporting M3U playlists: {OUT_MASTER_PRO}, {OUT_MASTER_FREE}")
    export_m3u(master_pro, OUT_MASTER_PRO, use_epg_title=True)
    export_m3u(master_free, OUT_MASTER_FREE, use_epg_title=True)

    # Export trimmed sports EPG
    if not progs_df.empty:
        used_ids = list(
            set(
                [str(x).strip() for x in master_pro["tvg_id"].tolist() if str(x).strip()]
            )
        )
        export_sports_epg(progs_df, used_ids)

    print("Done. Generated:")
    print(f"- {OUT_MASTER_PRO}  (Pro: Nomad + free)")
    print(f"- {OUT_MASTER_FREE} (Family: free-only)")
    print(f"- {OUT_EPG_XML} / {OUT_EPG_GZ} (sports-only EPG)")

if __name__ == "__main__":
    main()
    
