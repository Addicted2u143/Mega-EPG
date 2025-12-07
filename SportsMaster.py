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

free_playlists = [
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

CATEGORY_ORDER = [
    "🔥 Live Events",
    "📺 Sports Networks (General)",
    "🎲 Action & Odds",             # <-- Poker, Betting, Horse Racing
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

SPORT_KEYWORDS = {
    "🎲 Action & Odds": [
        "poker", "wsop", "world series of poker", "pokergo",
        "vsin", "sports grid", "sportsgrid",
        "bet", "odds", "wager", "sportsbook",
        "tvg", "fan duel tv", "fanduel", "horse racing", "racing channel",
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
    "⚾ MLB Baseball": ["mlb", "major league baseball", "mlb network"],
    "🏒 NHL Hockey": ["nhl"],
    "🥊 Fight Sports / PPV": [
        "ufc", "mma", "boxing", "wwe", "aew", "bellator",
        "fight", "fighting", "ppv", "pay per view", "pay-per-view",
    ],
    "🏎️ Motorsports": [
        "nascar", "indycar", "f1", "formula 1", "formula one", "motogp",
        "motorsport", "motorsports",
    ],
    "⚽ Soccer": [
        "soccer", "futbol", "premier league", "epl", "laliga",
        "serie a", "bundesliga", "champions league", "ucl",
        "europa league", "mls",
    ],
    "⛳🎾 Golf & Tennis": [
        "golf", "pga", "ryder cup", "masters tournament",
        "tennis", "atp", "wta", "us open", "wimbledon",
    ],
    "📺 Sports Networks (General)": [
        "espn", "espn2", "espnu", "espn u",
        "fox sports", "fs1", "fs2",
        "cbs sports", "cbssn",
        "tsn", "bein", "sky sports", "sportsnet",
        "sport", "sports",
    ],
}

GENERIC_SPORT_WORDS = ["sport", "sports", "espn", "sky sports", "fox sports", "tsn", "bein", "cbssn"]

EVENT_KEYWORDS = [
    "event", "ppv", "fight", "card", "round", "ufc",
    "wwe", "aew", "vs.", " vs ", "live event", "main event",
]

LIVE_HINTS = ["live", "live now", "on air", "in progress", "en vivo"]

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
    name = logo = group = tvg_id = None

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            logo = group = tvg_id = ""
            parts = line.split(",", 1)
            name = parts[1].strip() if len(parts) == 2 else ""

            if 'tvg-logo="' in line:
                logo = line.split('tvg-logo="')[1].split('"')[0]
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
            if 'tvg-id="' in line:
                tvg_id = line.split('tvg-id="')[1].split('"')[0]

        elif line.startswith("http"):
            rows.append([name, line, logo, group, tvg_id, source])

    return pd.DataFrame(rows, columns=["name", "url", "logo", "group", "tvg_id", "source"])

def text_contains_any(text: Optional[str], words: List[str]) -> bool:
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(w in t for w in words)

# ==========================
# 4. CATEGORY + LIVE LOGIC
# ==========================

def classify_category(name: str, group: str) -> str:
    combo = f"{name.lower()} {group.lower()}"
    for category, keys in SPORT_KEYWORDS.items():
        if any(k in combo for k in keys):
            return category
    if any(k in combo for k in GENERIC_SPORT_WORDS):
        return "📺 Sports Networks (General)"
    return ""

def is_event(name: str, group: str) -> bool:
    combo = f"{name.lower()} {group.lower()}"
    return any(k in combo for k in EVENT_KEYWORDS)

def extract_event_number(name: str) -> Optional[int]:
    import re
    m = re.search(r"\b(\d{1,4})\b", name.lower())
    return int(m.group(1)) if m else None

def looks_live(name: str, group: str) -> bool:
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
            content = resp.content

            if url.endswith(".gz") or content[:2] == b"\x1f\x8b":
                with gzip.GzipFile(fileobj=BytesIO(content)) as gz:
                    xml = gz.read().decode("utf-8", "ignore")
            else:
                xml = resp.text

            root = ET.fromstring(xml)

            for prog in root.findall("programme"):
                rows.append([
                    prog.get("channel", ""),
                    prog.findtext("title", ""),
                    prog.get("start", ""),
                    prog.get("stop", "")
                ])

        except Exception as e:
            print("EPG failure:", e)

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
    return df.dropna(subset=["start", "stop"])

def attach_epg(df: pd.DataFrame, epg_df: pd.DataFrame) -> pd.DataFrame:
    if epg_df.empty:
        df["epg_title_current"] = ""
        return df

    now = dt.datetime.now(dt.timezone.utc)
    current = epg_df[(epg_df["start"] <= now) & (epg_df["stop"] >= now)]

    if current.empty:
        df["epg_title_current"] = ""
        return df

    df["tid"] = df["tvg_id"].fillna("").str.strip()
    current["cid"] = current["channel_id"].fillna("").str.strip()

    curr_latest = current.groupby("cid")["title"].first().reset_index()
    merged = df.merge(curr_latest, left_on="tid", right_on="cid", how="left")
    merged["epg_title_current"] = merged["title"].fillna("")
    return merged.drop(columns=["title", "cid"])

# ==========================
# 6. MERGE PLAYLISTS
# ==========================

def load_playlists() -> pd.DataFrame:
    dfs = []

    paid = download_m3u(PAID_URL)
    if paid.strip():
        dfs.append(parse_m3u(paid, "paid"))

    for url in free_playlists:
        text = download_m3u(url)
        if text.strip():
            dfs.append(parse_m3u(text, "free"))

    merged = pd.concat(dfs, ignore_index=True)
    merged["source_priority"] = merged["source"].map({"paid": 0, "free": 1})
    merged = merged.sort_values(["source_priority"]).drop_duplicates(subset=["url"])
    return merged.reset_index(drop=True)

# ==========================
# 7. BUILD OUTPUT
# ==========================

def build_display(row):
    if row["epg_title_current"]:
        return f"{row['epg_title_current']} | {row['name']}"
    return row["name"]

def export_m3u(df, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, r in df.iterrows():
            line = (
                f'#EXTINF:-1 tvg-id="{r["tvg_id"]}" '
                f'tvg-logo="{r["logo"]}" '
                f'group-title="{r["group_title"]}",{r["display"]}\n'
            )
            f.write(line)
            f.write(r["url"] + "\n")

# ==========================
# 8. MASTER PIPELINE
# ==========================

def main():
    merged = load_playlists()
    epg_df = download_epg(epg_urls)
    merged = attach_epg(merged, epg_df)

    # classify
    merged["category"] = merged.apply(lambda r: classify_category(r["name"], r["group"]), axis=1)
    merged = merged[merged["category"] != ""].copy()

    merged["is_event"] = merged.apply(lambda r: is_event(r["name"], r["group"]), axis=1)
    merged["event_number"] = merged["name"].apply(extract_event_number)
    merged["is_live"] = merged.apply(lambda r: bool(r["epg_title_current"]) or looks_live(r["name"], r["group"]), axis=1)

    # LIVE EVENTS BLOCK
    live_block = merged[(merged["is_event"]) & (merged["is_live"])].copy()
    live_block["group_title"] = "🔥 Live Events"

    # CATEGORY BLOCKS
    blocks = []

    for cat in CATEGORY_ORDER:
        if cat == "🔥 Live Events":
            continue

        sub = merged[merged["category"] == cat].copy()
        if sub.empty:
            continue

        sub = sub.sort_values(
            by=["is_live", "event_number", "name"],
            ascending=[True, True, True]
        )

        # live channels at top
        sub = pd.concat([
            sub[sub["is_live"]],
            sub[~sub["is_live"]]
        ])

        sub["group_title"] = cat
        blocks.append(sub)

    # final merge
    output = pd.concat([live_block] + blocks, ignore_index=True)
    output["display"] = output.apply(build_display, axis=1)

    # export
    export_m3u(output, "sports_master.m3u")
    export_m3u(output[output["source"] != "paid"], "sports_master_free.m3u")

    print("Generated:")
    print("- sports_master.m3u (paid + free)")
    print("- sports_master_free.m3u (free only)")

if __name__ == "__main__":
    main()
    
