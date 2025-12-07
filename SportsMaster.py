import os
import requests
import pandas as pd
import datetime as dt
import xml.etree.ElementTree as ET
import gzip
from io import BytesIO
from typing import List, Dict, Optional

# ==========================
# 1. USER SETTINGS FROM SECRETS
# ==========================

PAID_USERNAME = os.getenv("NOMAD_USER", "")
PAID_PASSWORD = os.getenv("NOMAD_PASS", "")

if not PAID_USERNAME or not PAID_PASSWORD:
    raise RuntimeError("Nomad credentials missing. Check GitHub Secrets NOMAD_USER / NOMAD_PASS.")

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

# EPG: Nomad + EPGShare01
epg_urls: List[str] = [
    "http://nomadiptv.online:25461/xmltv.php?username=%s&password=%s" % (PAID_USERNAME, PAID_PASSWORD),
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz",
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
        "poker", "pokergo", "wsop", "horse", "tvg", "sportsgrid", "vsin",
        "bet", "odds", "wager", "handicapping"
    ],
    "🏈 NFL Football": [
        "nfl", "redzone", "nfl network", "nfln",
        "monday night football", "thursday night football",
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
        "mlb", "major league baseball", "mlb network",
    ],
    "🏒 NHL Hockey": [
        "nhl", "national hockey league",
    ],
    "🥊 Fight Sports / PPV": [
        "ufc", "mma", "boxing", "wwe", "aew", "fight", "ppv",
    ],
    "🏎️ Motorsports": [
        "nascar", "f1", "formula", "indycar", "motogp",
    ],
    "⚽ Soccer": [
        "soccer", "futbol", "premier league", "epl",
        "laliga", "serie a", "bundesliga", "ucl", "mls",
    ],
    "⛳🎾 Golf & Tennis": [
        "golf", "pga", "tennis", "atp", "wta",
    ],
    "📺 Sports Networks (General)": [
        "espn", "fs1", "fs2", "fox sports", "cbs sports", "cbssn",
        "sky sports", "bein", "tsn", "sportsnet",
    ],
}

GENERIC_SPORT_WORDS = ["sport", "sports", "espn", "sky", "fox sports"]

EVENT_KEYWORDS = ["event", "ufc", "ppv", "fight", "main event"]
LIVE_HINTS = ["live", "in progress", "en vivo"]

# ==========================
# 3. HELPERS
# ==========================

def download_m3u(url: str) -> str:
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return ""

def parse_m3u(text: str, source: str) -> pd.DataFrame:
    lines = text.splitlines()
    rows = []
    name = logo = group = tvg_id = ""

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            name = (line.split(",", 1)[1] if "," in line else "").strip()
            logo = extract_attr(line, "tvg-logo")
            group = extract_attr(line, "group-title")
            tvg_id = extract_attr(line, "tvg-id")
        elif line.startswith("http"):
            rows.append([name, line, logo, group, tvg_id, source])
    return pd.DataFrame(rows, columns=["name","url","logo","group","tvg_id","source"])

def extract_attr(text: str, key: str) -> str:
    if f'{key}="' in text:
        return text.split(f'{key}="')[1].split('"')[0]
    return ""

def text_contains_any(text: Optional[str], words: List[str]) -> bool:
    if not isinstance(text, str): return False
    t = text.lower()
    return any(w in t for w in words)

def classify_sport(name: str, group: str) -> str:
    combo = f"{name.lower()} {group.lower()}"
    for cat, keys in SPORT_KEYWORDS.items():
        if any(k in combo for k in keys):
            return cat
    if any(k in combo for k in GENERIC_SPORT_WORDS):
        return "📺 Sports Networks (General)"
    return ""

def is_event(name: str, group: str) -> bool:
    combo = f"{name.lower()} {group.lower()}"
    return any(k in combo for k in EVENT_KEYWORDS)

# ==========================
# 4. EPG
# ==========================

def download_epg(urls: List[str]) -> pd.DataFrame:
    rows = []
    for url in urls:
        try:
            resp = requests.get(url, timeout=40)
            content = resp.content
            if url.endswith(".gz") or content[:2] == b"\x1f\x8b":
                content = gzip.GzipFile(fileobj=BytesIO(content)).read()
            xml = content.decode("utf-8", errors="ignore")
            root = ET.fromstring(xml)
            for p in root.findall("programme"):
                ch = p.get("channel","")
                start=p.get("start","")
                stop=p.get("stop","")
                title_el=p.find("title")
                title=title_el.text if (title_el is not None and title_el.text) else ""
                rows.append([ch,title,start,stop])
        except:
            continue

    df=pd.DataFrame(rows,columns=["channel","title","start","stop"])
    return df

# ==========================
# 5. BUILD
# ==========================

def main():

    print("Loading playlists…")
    paid_text = download_m3u(PAID_URL)
    paid_df = parse_m3u(paid_text,"paid") if paid_text else pd.DataFrame()

    free_dfs=[]
    for url in free_playlists:
        txt=download_m3u(url)
        if txt:
            free_dfs.append(parse_m3u(txt,"free"))

    merged=pd.concat([paid_df]+free_dfs,ignore_index=True)
    merged["name"]=merged["name"].fillna("").astype(str)
    merged["group"]=merged["group"].fillna("").astype(str)

    # dedupe by URL, paid wins
    merged["priority"]=merged["source"].map({"paid":0,"free":1})
    merged=merged.sort_values("priority").drop_duplicates("url",keep="first")

    print("Loading EPG…")
    epg=download_epg(epg_urls)

    # attach EPG titles
    merged["epg_title"]=""
    if not epg.empty:
        now=dt.datetime.utcnow()
        epg["start_dt"]=pd.to_datetime(epg["start"],errors="coerce")
        epg["stop_dt"]=pd.to_datetime(epg["stop"],errors="coerce")
        current=epg[(epg["start_dt"]<=now)&(epg["stop_dt"]>=now)]
        if not current.empty:
            latest=current.groupby("channel")["title"].first()
            merged["epg_title"]=merged["tvg_id"].map(latest).fillna("")

    # classification
    merged["category"]=merged.apply(lambda r: classify_sport(r["name"],r["group"]),axis=1)
    merged=merged[merged["category"]!=""]

    merged["is_event"]=merged.apply(lambda r:is_event(r["name"],r["group"]),axis=1)
    merged["is_live"]=merged["epg_title"].astype(bool) | merged["name"].str.contains("live",case=False)

    # Live Events block
    live_block=merged[(merged["is_event"])&(merged["is_live"])].copy()
    live_block["output_group"]="🔥 Live Events"

    # category blocks
    blocks=[]
    for cat in CATEGORY_ORDER:
        if cat=="🔥 Live Events": continue
        sub=merged[merged["category"]==cat].copy()
        if sub.empty: continue
        sub=sub.sort_values(["is_live","name"],ascending=[False,True])
        sub["output_group"]=cat
        blocks.append(sub)

    final=pd.concat(([live_block] if not live_block.empty else [])+blocks,ignore_index=True)

    # export
    export(final, "sports_master.m3u", use_epg=True)

    free=final[final["source"]!="paid"].copy()
    export(free,"sports_master_free.m3u",use_epg=True)

    print("Done.")

def export(df,path,use_epg):
    with open(path,"w",encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _,r in df.iterrows():
            title = r["epg_title"]+" | "+r["name"] if (use_epg and r["epg_title"]) else r["name"]
            f.write(f'#EXTINF:-1 tvg-id="{r["tvg_id"]}" tvg-logo="{r["logo"]}" group-title="{r["output_group"]}",{title}\n')
            f.write(r["url"]+"\n")

if __name__=="__main__":
    main()
    
