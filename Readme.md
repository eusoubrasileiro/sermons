python scrape_sermons.py \
  --client-id      xxxxx  \
  --client-secret  xxxx 

python3 -m http.server 9000


#### Spotiy limitations

Spotify’s show episodes endpoint (GET /v1/shows/{id}/episodes) in practice Spotify only exposes a slice of the catalog per show. 
Some shows/API responses reach ~500 and then go empty. 
This cap isn’t documented beyond the standard paging params, so there’s no API-side trick to fetch episode #501+

##### TODO: Spotify Search API to backfill the missing ones found on SoundCloud

gpt5 the super-short recipe to use 

curl -G "https://api.spotify.com/v1/search" \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'q="The Big Launch" "My Startup Show" year:2021' \
  --data-urlencode 'type=episode' \
  --data-urlencode 'limit=10' \
  --data-urlencode 'market=US'