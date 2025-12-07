import requests
import pandas as pd
import datetime as dt
import xml.etree.ElementTree as ET
import gzip
from io import BytesIO
from typing import List, Dict, Optional

# ============================================================
# 1. USER SETTINGS
# ============================================================

PAID_USERNAME = "username"
PAID_PASSWORD = "password"

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
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz",
    "http://nomadiptv.online:25461/xmltv.php"
]

# ============================================================
# 2. CATEGORY DEFINITIONS
# ============================================================

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
    "🏈 NFL Football": [
        "nfl", "redzone", "red zone", "nfl network", "tnf", "mnf"
    ],
    "🎓🏈 NCAA Football": [
        "ncaa", "college football", "cfb", "big ten", "sec network",
        "btn", "acc network"
    ],
    "🏀 NBA Basketball": ["nba"],
    "🎓🏀 NCAA Basketball": ["ncaa basketball", "march madness"],
    "⚾ MLB Baseball": ["mlb", "major league baseball", "mlb network"],
    "🏒 NHL Hockey": ["nhl"],
    "🥊 Fight Sports / PPV": [
        "ufc", "boxing", "wwe", "aew", "bellator", "fight", "ppv"
    ],
    "🏎️ Motorsports": [
        "nascar", "indycar", "f1", "formula", "motogp", "motorsport"
    ],
    "⚽ Soccer": [
        "soccer", "premier league", "epl", "la liga", "bundesliga",
        "serie a", "champions league", "ucl", "mls"
    ],
    "⛳🎾 Golf & Tennis": [
        "golf", "pga", "ryder", "tennis", "atp", "wta", "open", "masters"
    ],
    "📺 Sports Networks (General)": [
        "espn", "fox sports", "fs1", "fs2", "cbssn", "tsn", "bein"
    ],
    "🎲 Action & Odds": [
        "poker", "wsop", "pokergo", "vsin", "sportsgrid", "tvg",
        "horseracing", "horse racing", "racing"
    ],
}

GENERIC_SPORT_WORDS = ["sport", "sports", "espn", "fox", "bein", "tsn"]
EVENT_KEYWORDS = ["event", "ppv", "fight", "ufc", "round", "main event"]
LIVE_HINTS = ["live", "en vivo", "live now", "in progress"]

# ============================================================
# 3. BASIC HELPERS
# ============================================================

def download_m3u(url: str) -> str:
    try:
        print(f"Fetching: {url}")
        resp = requests.get(url, timeout=20)
        return resp.text
    except:
        return ""

def parse_m3u(text: str, source: str) -> pd.DataFrame:
    lines = text.splitlines()
    rows = []
    name = logo = group = tvg_id = ""

    for line in lines:
        line = line.strip()

        if line.startswith("#EXTINF"):
            if "," in line:
                name = line.split(",", 1)[1]
            if 'tvg-logo="' in line:
                logo = line.split('tvg-logo="')[1].split('"')[0]
            if 'group-title="' in line:
                group = line.split('group-title="')[1].split('"')[0]
            if 'tvg-id="' in line:
                tvg_id = line.split('tvg-id="')[1].split('"')[0]

        elif line.startswith("http"):
            rows.append([name, line, logo, group, tvg_id, source])

    return pd.DataFrame(rows, columns=["name", "url", "logo", "group", "tvg_id", "source"])

def extract_event_number(name: str) -> Optional[int]:
    import re
    m = re.search(r"(\b\d{1,3}\b)", name.lower())
    return int(m.group()) if m else None

# ============================================================
# 4. EPG LOADING & PARSING
# ============================================================

def download_epg(urls: List[str]) -> pd.DataFrame:
    rows = []

    for url in urls:
        print(f"Fetching EPG: {url}")
        try:
            resp = requests.get(url, timeout=40)
            content = resp.content

            if url.endswith(".gz") or content[:2] == b"\x1f\x8b":
                xml = gzip.decompress(content).decode("utf-8", "ignore")
            else:
                xml = content.decode("utf-8", "ignore")

            root = ET.fromstring(xml)

            for prog in root.findall("programme"):
                chan = prog.get("channel", "")
                start = prog.get("start", "")
                stop = prog.get("stop", "")
                title_el = prog.find("title")
                title = title_el.text if title_el is not None else ""
                rows.append([chan, title, start, stop])

        except:
            continue

    df = pd.DataFrame(rows, columns=["channel_id", "title", "start_raw", "stop_raw"])

    def parse(t):
        try:
            if " " in t:
                return dt.datetime.strptime(t, "%Y%m%d%H%M%S %z")
            return dt.datetime.strptime(t[:14], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
        except:
            return None

    df["start_dt"] = df["start_raw"].apply(parse)
    df["stop_dt"] = df["stop_raw"].apply(parse)
    df = df.dropna(subset=["start_dt", "stop_dt"])
    return df

# ============================================================
# 5. SPORTS LOGIC
# ============================================================

def classify_category(name: str, group: str) -> str:
    combo = f"{name.lower()} {group.lower()}"
    for cat, keys in SPORT_KEYWORDS.items():
        if any(k in combo for k in keys):
            return cat
    if any(k in combo for k in GENERIC_SPORT_WORDS):
        return "📺 Sports Networks (General)"
    return ""

def attach_current_epg(df, epg):
    if df.empty or epg.empty:
        df["epg_now"] = ""
        return df

    now = dt.datetime.now(dt.timezone.utc)  # FIXED — tz-aware

    current = epg[(epg["start_dt"] <= now) & (epg["stop_dt"] >= now)]
    if current.empty:
        df["epg_now"] = ""
        return df

    current = current.groupby("channel_id")["title"].first().reset_index()

    df["tvg_id_clean"] = df["tvg_id"].fillna("").astype(str)
    merged = df.merge(current, left_on="tvg_id_clean", right_on="channel_id", how="left")
    merged["epg_now"] = merged["title"].fillna("")
    return merged.drop(columns=["channel_id", "title"])

# ============================================================
# 6. MAIN BUILD PIPELINE
# ============================================================

def load_playlists():
    dfs = []

    paid = download_m3u(PAID_URL)
    if paid.strip():
        dfs.append(parse_m3u(paid, "paid"))

    for url in free_playlists:
        text = download_m3u(url)
        if text.strip():
            dfs.append(parse_m3u(text, "free"))

    merged = pd.concat(dfs, ignore_index=True)
    merged = merged.drop_duplicates(subset=["url"], keep="first")
    return merged

def enrich(df, epg):
    df["sport_category"] = df.apply(lambda r: classify_category(r["name"], r["group"]), axis=1)
    df = df[df["sport_category"] != ""].copy()

    df["is_event"] = df["name"].str.lower().apply(lambda x: any(k in x for k in EVENT_KEYWORDS))
    df["event_number"] = df["name"].apply(extract_event_number)

    df = attach_current_epg(df, epg)

    df["is_live"] = df.apply(
        lambda r: bool(r["epg_now"]) or any(h in r["name"].lower() for h in LIVE_HINTS),
        axis=1
    )

    return df

# ============================================================
# 7. CATEGORY BUILD
# ============================================================

def build_live(df):
    live = df[df["is_live"] & df["is_event"]].copy()
    if live.empty:
        return live
    live["output_group"] = "🔥 Live Events"
    return live.sort_values(by=["sport_category", "event_number", "name"])

def build_categories(df):
    blocks = []
    for cat in CATEGORY_ORDER:
        if cat == "🔥 Live Events":
            continue
        sub = df[df["sport_category"] == cat].copy()
        if sub.empty:
            continue
        sub["output_group"] = cat
        sub = sub.sort_values(by=["is_live", "name"], ascending=[False, True])
        blocks.append(sub)
    return pd.concat(blocks, ignore_index=True)

# ============================================================
# 8. EXPORT
# ============================================================

def export(df, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, r in df.iterrows():
            name = r["epg_now"] + " | " + r["name"] if r["epg_now"] else r["name"]
            f.write(
                f'#EXTINF:-1 tvg-id="{r["tvg_id"]}" tvg-logo="{r["logo"]}" '
                f'group-title="{r["output_group"]}",{name}\n{r["url"]}\n'
            )

# ============================================================
# 9. MAIN
# ============================================================

def main():
    print("Loading playlists…")
    merged = load_playlists()

    print("Loading EPG…")
    epg = download_epg(epg_urls)

    print("Classifying sports…")
    enriched = enrich(merged, epg)

    print("Building Live Events…")
    live = build_live(enriched)

    print("Building categories…")
    cats = build_categories(enriched)

    final = pd.concat([live, cats], ignore_index=True)

    # Paid + free:
    export(final, "sports_master.m3u")

    # Free-only:
    export(final[final["source"] != "paid"], "sports_master_free.m3u")

    print("Done!")

if __name__ == "__main__":
    main()
