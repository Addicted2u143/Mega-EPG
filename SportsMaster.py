import requests
import re
from collections import defaultdict

# ============================================================
# 1) SOURCES (FREE ONLY)
# ============================================================

FREE_PLAYLISTS = [
    # --- Live / Event backbone ---
    "https://raw.githubusercontent.com/BuddyChewChew/ppv/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Pixelsports.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamSU.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/BuddyChewChew/My-Streams/refs/heads/main/Backup.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/buddylive-combined/refs/heads/main/combined_playlist.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/buddylive_v1.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/buddylive/refs/heads/main/en/videoall.m3u",

    "https://raw.githubusercontent.com/BuddyChewChew/iptv/refs/heads/main/M3U8/events.m3u8",

    # --- FAST / misc sources (optional but useful) ---
    "https://pluto.freechannels.me/playlist.m3u",
    "https://iptv-org.github.io/iptv/languages/eng.m3u",
    "https://www.apsattv.com/freelivesports.m3u",
    "https://www.apsattv.com/freetv.m3u",
]

# Anything from these sources gets preserved but kept in a dedicated section
DYNAMIC_SOURCE_HINTS = [
    "ppvland", "buddylive", "streamsu", "streamedsu", "pixelsports", "thetvapp", "events.m3u8"
]

# ============================================================
# 2) CATEGORY ORDER (LOCKED)
# ============================================================

CATEGORY_ORDER = [
    "📺 Sports Networks (General)",
    "🎲 Poker & Sports Betting",
    "🐎 Horse Racing",
    "🏈 NFL Football",
    "🏉 NCAA Football",
    "🏀 NBA Basketball",
    "🏀 NCAA Basketball",
    "⚾ MLB Baseball",
    "🏒 NHL Hockey",
    "🥊 Fight Sports / PPV",
    "🎣 Fishing & Hunting",
    "🏎️ Motorsports",
    "⚽ Soccer",
    "⛳ Golf & Tennis",
    "📦 Sports Everything Else",
    "🧩 Live Feeds (Dynamic Sources)",  # keep dynamic sources stable & predictable
]

# ============================================================
# 3) KEYWORDS (STRICT ENOUGH TO STOP SOCCER FLOODING NFL)
# ============================================================

SOCCER_TERMS = ["soccer", "futbol", "bundesliga", "laliga", "serie a", "premier", "uefa", "ucl", "mls"]
BETTING_TERMS = ["draftkings", "fanduel", "sportsgrid", "betting", "poker", "wpt", "world poker", "triton poker"]
BET_BLACK_ENTERTAINMENT_TERMS = ["bet her", "bet gospel", "bet+", "black entertainment"]

RULES = {
    "📺 Sports Networks (General)": ["espn", "fox sports", "cbs sports", "nbc sports", "sportsnet", "tsn", "bein"],
    "🎲 Poker & Sports Betting": BETTING_TERMS,
    "🐎 Horse Racing": ["tvg", "horse", "racing"],
    "🏈 NFL Football": ["nfl", "redzone", "sunday night football", "monday night football", "thursday night football"],
    "🏉 NCAA Football": ["ncaaf", "college football"],
    "🏀 NBA Basketball": ["nba"],
    "🏀 NCAA Basketball": ["ncaab", "college basketball", "march madness"],
    "⚾ MLB Baseball": ["mlb", "baseball"],
    "🏒 NHL Hockey": ["nhl", "hockey"],
    "🥊 Fight Sports / PPV": ["ufc", "mma", "boxing", "wwe", "ppv", "fight"],
    "🎣 Fishing & Hunting": ["fishing", "hunting", "outdoor"],
    "🏎️ Motorsports": ["nascar", "f1", "formula", "indycar", "motogp"],
    "⚽ Soccer": SOCCER_TERMS,
    "⛳ Golf & Tennis": ["golf", "pga", "tennis", "atp", "wta"],
}

LIVE_HINTS = [" live", "live ", " live:", " on air", " in progress", "event", "match", "vs", " at "]

# ============================================================
# 4) HELPERS
# ============================================================

def normalize_url(url: str) -> str:
    # Convert github blob URLs to raw URLs so they actually work.
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob", "")
    return url

def fetch_text(url: str) -> str:
    url = normalize_url(url)
    try:
        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

def parse_m3u(text: str):
    """
    Returns list of dict: name, url, group, logo
    Robust against weird spacing and missing commas.
    """
    rows = []
    current = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            # Name is after the last comma. If missing comma, we fallback later.
            name = line.split(",")[-1].strip() if "," in line else ""
            group = ""
            logo = ""

            m = re.search(r'group-title="([^"]*)"', line)
            if m:
                group = m.group(1)

            m = re.search(r'tvg-logo="([^"]*)"', line)
            if m:
                logo = m.group(1)

            current = {"name": name, "group": group, "logo": logo}

        elif line.startswith("http") and current:
            current["url"] = line
            rows.append(current)
            current = None

    return rows

def safe_clean_name(name: str) -> str:
    """
    Remove ugly numeric prefixes, but NEVER produce an empty name.
    """
    original = (name or "").strip()
    if not original:
        return original

    cleaned = re.sub(r"^\s*\d+\s*", "", original).strip()
    cleaned = re.sub(r"\s+\d+\s*$", "", cleaned).strip()

    return cleaned if cleaned else original

def is_dynamic_source(source_url: str, group: str, name: str) -> bool:
    blob = f"{source_url} {group} {name}".lower()
    return any(k in blob for k in DYNAMIC_SOURCE_HINTS)

def looks_live(name: str, group: str) -> bool:
    blob = f" {name} {group} ".lower()
    return any(h in blob for h in LIVE_HINTS)

def classify(name: str, group: str) -> str:
    blob = f" {name} {group} ".lower()

    # Soccer first, so "football" doesn't poison NFL
    if any(t in blob for t in SOCCER_TERMS):
        return "⚽ Soccer"

    # BET channel is NOT betting
    if any(t in blob for t in BET_BLACK_ENTERTAINMENT_TERMS) or blob.strip().startswith("bet "):
        return "📦 Sports Everything Else"

    # True categorization
    for cat, keys in RULES.items():
        if any(k in blob for k in keys):
            return cat

    return "📦 Sports Everything Else"

# ============================================================
# 5) BUILD
# ============================================================

all_rows = []

for src in FREE_PLAYLISTS:
    text = fetch_text(src)
    if not text or "#EXTINF" not in text:
        continue
    all_rows.extend([{**r, "source": src} for r in parse_m3u(text)])

# bucket channels
buckets = defaultdict(list)

for r in all_rows:
    name = safe_clean_name(r.get("name", ""))
    group = r.get("group", "") or ""
    logo = r.get("logo", "") or ""
    url = r.get("url", "") or ""
    source = r.get("source", "")

    if not url or not name:
        # If name is missing entirely, don't write garbage "numbers-only"
        continue

    dynamic = is_dynamic_source(source, group, name)

    if dynamic:
        # Keep dynamic sources stable in ONE section, but preserve original sub-group in the name
        # so you can still see "PPVLand - NFL Action" etc.
        final_group = "🧩 Live Feeds (Dynamic Sources)"
        display_name = f"[{group if group else 'Dynamic'}] {name}".strip()
    else:
        final_group = classify(name, group)
        display_name = name

    entry = {
        "group": final_group,
        "name": display_name,
        "url": url,
        "logo": logo,
        "live": looks_live(display_name, group)
    }

    buckets[final_group].append(entry)

# Sort: live first, then name
for cat in buckets:
    buckets[cat].sort(key=lambda x: (not x["live"], x["name"].lower()))

# ============================================================
# 6) EXPORT
# ============================================================

with open("sports_master.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for cat in CATEGORY_ORDER:
        if cat not in buckets or not buckets[cat]:
            continue

        for e in buckets[cat]:
            f.write(
                f'#EXTINF:-1 tvg-logo="{e["logo"]}" group-title="{cat}",{e["name"]}\n'
            )
            f.write(e["url"] + "\n")

print("Done: sports_master.m3u generated")
