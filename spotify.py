#!/usr/bin/env python3
"""
scrape_spotify_tracks.py
------------------------------------------------
Grab every episode from a Spotify show and (optionally) match
them to the SoundCloud list you already generated.

USAGE
  python scrape_spotify_tracks.py \
      --show-id      7OQmf3n…            # Spotify Show ID
      --client-id    $SPOTIFY_ID \
      --client-secret $SPOTIFY_SECRET \
      --soundcloud-json tracks.json      # optional
      --out merged_tracks.json           # default = tracks_spotify.json
"""

import argparse, json, sys, requests, pathlib
from datetime import datetime

# ─── Helpers ────────────────────────────────────────────────────────────────── #

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
        return datetime.fromisoformat(iso).date().isoformat()
    except Exception:
        return None

def match_soundcloud(sc_list, ep_title):
    for sc in sc_list:
        if sc["title"].lower() in ep_title.lower() or ep_title.lower() in sc["title"].lower():
            return sc["url"]          # first naïve hit → good enough for now
    return None

# ─── Main ──────────────────────────────────────────────────────────────────── #

parser = argparse.ArgumentParser()
parser.add_argument("--client-id", required=True)
parser.add_argument("--client-secret", required=True)
parser.add_argument("--soundcloud-json")        # optional
parser.add_argument("--out", default="tracks.json")
args = parser.parse_args()

token  = get_spotify_token(args.client_id, args.client_secret)
eps    = get_show_episodes("1DgxzkzYvNGLNv7UawbEUP", token)
sc_map = []

if args.soundcloud_json:
    sc_map = json.loads(pathlib.Path(args.soundcloud_json).read_text())

records = []
for ep in eps:
    rec = {
        "title"       : ep["name"],
        "spotify_url" : f'https://open.spotify.com/episode/{ep["id"]}',
        "duration"    : ep["duration_ms"] // 1000,   # seconds
        "release_date": nice_date(ep.get("release_date")),
        "soundcloud_url": match_soundcloud(sc_map, ep["name"]) if sc_map else None,
    }
    records.append(rec)

pathlib.Path(args.out).write_text(json.dumps(records, ensure_ascii=False, indent=2))
print(f"✅  Saved {len(records)} items → {args.out}")
if sc_map:
    matched = sum(bool(r["soundcloud_url"]) for r in records)
    print(f"🔗  Matched {matched}/{len(records)} episodes to SoundCloud titles.")
