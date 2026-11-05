#!/bin/bash
# Batch-geocode street addresses with the US Census geocoder (max 10,000 per request).
# usage: geocode.sh GEO_DIR   (reads GEO_DIR/to_geocode.csv, writes GEO_DIR/batch_out_N.csv)
set -e
G="$1"
cd "$G"
rm -f chunk_* batch_out_*.csv
split -l 250 -d --additional-suffix=.csv to_geocode.csv chunk_
for f in chunk_*; do
  n=${f#chunk_}; n=${n%.csv}
  curl -sS -m 600 --form addressFile=@"$f" --form benchmark=Public_AR_Current \
    -o "batch_out_$n.csv" https://geocoding.geo.census.gov/geocoder/locations/addressbatch \
    -w "$f %{http_code} %{size_download}\n" || echo "$f failed"
done
cat batch_out_*.csv | awk -F'","' '{print $3}' | sort | uniq -c
