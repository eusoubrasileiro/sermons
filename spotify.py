"""
scrape_tracks.py
------------------------------------------------
Grab every episode from a Spotify show and SoundCloud and try match
with Spotify as reference. 
Because it allows to play with speed multipliers 1.25, 1.5, 2.0 etc. 

USAGE
  python scrape_tracks.py \      
      --client-id    $SPOTIFY_ID \
      --client-secret $SPOTIFY_SECRET \      
      --out tracks.json           # default = tracks_spotify.json
"""
import argparse, json, sys, requests, pathlib
from datetime import datetime, timedelta
import json
from pathlib import Path
from datetime import datetime
import yt_dlp                           # yt‑dlp 2024.10.13 or newer


# ─── Spotify ──────────────────────────────────────────────────────────────── #

def get_spotify_token(cid, secret):
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(cid, secret),
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def get_show_episodes(show_id, token):
    episodes, url = [], f"https://api.spotify.com/v1/shows/{show_id}/episodes?market=BR&limit=50"
    headers = {"Authorization": f"Bearer {token}"}
    while url:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        j = r.json()
        episodes.extend(j["items"])
        url = j.get("next")
    return episodes

def nice_date(iso):
    try:
        return 
    except Exception:
        return None

# ─── SoundCloud ───────────────────────────────────────────────────────────── #

PLAYLIST_URL = "https://soundcloud.com/ipperegrinos"
OUTFILE      = Path("tracks.json")

ydl_opts = {
    "extract_flat": True,   # one JSON object per track, no media download
    "skip_download": True,
}

def get_soundcloud_tracks():
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(PLAYLIST_URL, download=False)
    return info["entries"]


# ─── Helpers ────────────────────────────────────────────────────────────────── #

def match_soundcloud(sc_list, sp_episode):
    for sc in sc_list:
        description = sp_episode['title'] + ' ' + sp_episode['description']
        if sc["title"].lower() in description.lower():
            return { 
                "soundcloud_url" : sc["soundcloud_url"],
                "soundcloud_id"  : sc["soundcloud_id"],
                "artist"         : sc["artist"],                
                "upload_date"    : sc["upload_date"],
                }          # first naïve hit → good enough for now
    return { }

# ─── Main ──────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)    
    parser.add_argument("--out", default="tracks.json")
    args = parser.parse_args()

    # ─── Spotify ───────────────────────────────────────────────────────────── #
    token  = get_spotify_token(args.client_id, args.client_secret)
    eps    = get_show_episodes("1DgxzkzYvNGLNv7UawbEUP", token)
    print(f"Downloaded {len(eps)} episodes from Spotify.")

    sp_records = []
    for ep in eps:
        rec = {
            "title"       : ep["name"],
            "spotify_id"  : ep["id"],
            "description" : ep["description"],
            "spotify_url" : f'https://open.spotify.com/episode/{ep["id"]}',
            "duration"    : str(timedelta(milliseconds=ep["duration_ms"])).split('.')[0], # remove milliseconds
            "release_date": datetime.fromisoformat(ep.get("release_date")).date().isoformat()
        }
        sp_records.append(rec)

    # ─── SoundCloud ───────────────────────────────────────────────────────────── #
    sc_tracks = get_soundcloud_tracks()
    print(f"Downloaded {len(sc_tracks)} tracks from SoundCloud.")
    sc_records = []
    for entry in sc_tracks:
        sc_records.append({
            "artist"         : entry["artist"] if "artist" in entry else None,
            "soundcloud_id"  : entry["id"],
            "title"          : entry["title"],
            "soundcloud_url" : entry["url"],        # direct SoundCloud permalink            
            "upload_date"    : (
                datetime.strptime(entry["upload_date"], "%Y%m%d")
                         .strftime("%Y-%m-%d")   # nicer format
                if entry.get("upload_date") else None
            ),
        })

    # ─── Match ───────────────────────────────────────────────────────────── #
    records = []
    for sp in sp_records:
        rec = {
            **sp,
            **match_soundcloud(sc_records, sp),
        }
        records.append(rec)

    pathlib.Path(args.out).write_text(json.dumps(records, ensure_ascii=False, indent=2))
    print(f"✅  Saved {len(records)} items → {args.out}")    
    matched = sum(bool(r["soundcloud_url"]) for r in records)
    print(f"🔗  Matched {matched}/{len(records)} episodes to SoundCloud titles.")
