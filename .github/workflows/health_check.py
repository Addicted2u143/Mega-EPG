import requests, gzip, io, sys

PLAYLISTS = [
    "https://raw.githubusercontent.com/Addicted2u143/Mega-EPG/main/sports_master.m3u",
    "https://raw.githubusercontent.com/Addicted2u143/Mega-EPG/main/sports_master_free.m3u"
]

EPG_URL = "https://raw.githubusercontent.com/Addicted2u143/Mega-EPG/main/combined_epg_latest.xml.gz"

def check_url(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        size = len(r.content)
        return True, f"OK ({size/1024:.1f} KB)"
    except Exception as e:
        return False, str(e)

def check_epg():
    try:
        r = requests.get(EPG_URL, timeout=20)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        gzip.GzipFile(fileobj=io.BytesIO(r.content)).read()
        return True, "EPG decompressed successfully"
    except Exception as e:
        return False, f"EPG error: {e}"

print("\n=== PLAYLIST HEALTH ===")
for url in PLAYLISTS:
    ok, msg = check_url(url)
    print(f"{url}: {msg}")

print("\n=== EPG HEALTH ===")
ok, msg = check_epg()
print(msg)

if not ok:
    sys.exit(1)

print("\nEverything looks good ✔")
