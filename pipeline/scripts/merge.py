"""Merge per-source grain elevator CSVs into one de-duplicated, geocoded inventory.

usage: python3 -I merge.py DATA_DIR OUT_JSON
Reads DATA_DIR/*/*.csv (federal, north, west, east, south), Census gazetteer files in DATA_DIR/geo,
and a cached Census batch-geocode result in DATA_DIR/geo/batch_*.csv if present.
"""
import csv, glob, hashlib, json, os, re, sys, unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

DATA, OUT = sys.argv[1], sys.argv[2]
COLS = "facility_name,company,address,city,state,zip,county,lat,lon,capacity_bu,license_type,license_number,commodities,source_name,source_url,source_date,notes".split(",")

STOP = {"inc", "incorporated", "co", "company", "corp", "corporation", "llc", "lp", "ltd", "the", "of", "and", "cooperative", "coop", "co-op", "assn", "association", "grain", "elevator", "elevators", "farmers", "ag", "agri"}


def ascii_(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def norm_txt(s):
    s = ascii_(s).lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def name_key(s):
    return " ".join(t for t in norm_txt(s).split() if t not in STOP)


def city_key(s):
    s = norm_txt(re.sub(r"\(.*?\)", " ", s or ""))
    s = re.sub(r"^(saint|st) ", "st ", s)
    s = re.sub(r"^(fort|ft) ", "ft ", s)
    s = re.sub(r"^(mount|mt) ", "mt ", s)
    return s


def addr_key(s):
    s = norm_txt(s)
    rep = {"street": "st", "avenue": "ave", "road": "rd", "highway": "hwy", "drive": "dr", "north": "n", "south": "s", "east": "e", "west": "w", "route": "rt", "county": "co", "box": "box"}
    return " ".join(rep.get(t, t) for t in s.split())


def to_int(v):
    v = re.sub(r"[^0-9.]", "", str(v or ""))
    try:
        f = float(v)
        return int(f) if f > 0 else None
    except ValueError:
        return None


def to_float(v):
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


# ---------- Census place names per state, for cleaning city fields
PLACE_NAMES = defaultdict(dict)  # state -> {lowercase name: proper name}
for _f in ("2024_Gaz_place_national.txt", "2024_Gaz_cousubs_national.txt"):
    with open(os.path.join(DATA, "geo", _f), encoding="latin-1") as _fh:
        _rd = csv.reader(_fh, delimiter="\t")
        _h = [x.strip() for x in next(_rd)]
        for _r in _rd:
            _d = dict(zip(_h, [x.strip() for x in _r]))
            _n = re.sub(r"\s+(city|town|village|CDP|borough|township|plantation)$", "", _d["NAME"], flags=re.I)
            PLACE_NAMES[_d["USPS"]].setdefault(_n.lower(), _n)
FIX = {"w ": "West ", "e ": "East ", "n ": "North ", "s ": "South ", "ft ": "Fort ", "ft. ": "Fort ", "st ": "St. ", "mt ": "Mount ", "mt. ": "Mount "}
city_fixes = defaultdict(int)


def clean_city(city, st):
    """Tidy a city field and repair obvious typos/truncations against Census place names."""
    raw = city
    c = re.sub(r"\s+", " ", city or "").strip().strip(",.;:-").strip()
    if not c:
        return ""
    P = PLACE_NAMES.get(st, {})
    if c.lower() in P:
        if c != raw: city_fixes["punctuation/spacing"] += 1
        return c
    for k, v in FIX.items():
        if c.lower().startswith(k) and (v + c[len(k):]).lower() in P:
            city_fixes["abbreviation"] += 1
            return P[(v + c[len(k):]).lower()]
    base = re.sub(r"\s*\(.*?\)\s*", " ", c).strip()
    if base != c and base.lower() in P:
        city_fixes["parenthetical (kept in grouping only)"] += 1
        return c  # keep the source's label; grouping uses city_key, which drops parentheticals
    if len(c) >= 4:  # truncated name, e.g. "Arthu" -> "Arthur"
        cand = [n for n in P if n.startswith(c.lower()) and len(n) - len(c) <= 3]
        if len(cand) == 1:
            city_fixes["truncated"] += 1
            return P[cand[0]]
    return c


# ---------- load sources
rows, sources = [], {}
for path in sorted(glob.glob(os.path.join(DATA, "*", "*.csv"))):
    if os.sep + "geo" + os.sep in path or os.sep + "raw" + os.sep in path:
        continue
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            r = {c: (r.get(c) or "").strip() for c in COLS}
            st = r["state"].upper()[:2]
            if not re.fullmatch(r"[A-Z]{2}", st):
                continue
            r["state"] = st
            old_city = re.sub(r"\s+", " ", r["city"]).strip()
            r["city"] = clean_city(r["city"], st)
            if old_city and r["city"] != old_city and len(old_city) >= 4:
                for fld in ("facility_name", "company"):  # e.g. "The Arthur Companies, Inc. - Arthu"
                    r[fld] = re.sub(r"(\s[-~]\s)" + re.escape(old_city) + r"$", lambda m: m.group(1) + r["city"], r[fld])
            sname = r["source_name"] or os.path.basename(path)
            skey = hashlib.sha1(sname.encode()).hexdigest()[:8]
            s = sources.setdefault(skey, {"key": skey, "name": sname, "url": r["source_url"].split(" ")[0], "date": r["source_date"], "count": 0})
            s["count"] += 1
            r["_src"] = skey
            r["_file"] = os.path.basename(path)
            rows.append(r)
print("input rows", len(rows), "sources", len(sources), file=sys.stderr)
print("city fixes", dict(city_fixes), file=sys.stderr)

# ---------- de-duplicate within (state, city)
groups = defaultdict(list)
for r in rows:
    groups[(r["state"], city_key(r["city"]))].append(r)


ALIAS = {"archer daniels midland": "adm", "archer daniels midland dba adm": "adm", "consolidated barge": "cgb", "cargill incorporated": "cargill"}
GENERIC = {"op", "co op", "farm center", "warehouse", "storage", "terminal", "mill", "feed", "supply", "seed"}


def keys(a):
    """Name keys for a record: its facility name and its company, ignoring generic ones like 'Co-Op Elevator'."""
    out = []
    for v in (a["facility_name"], a["company"]):
        k = name_key(v)
        k = ALIAS.get(k, k)
        for al, tgt in ALIAS.items():
            if k.startswith(al + " "):
                k = tgt + k[len(al):]
        if k and k not in GENERIC and k not in out:
            out.append(k)
    return out


def names_match(na, nb):
    ta, tb = na.split(), nb.split()
    if na == nb:
        return True
    short = min((na, nb), key=len)
    if len(short) <= 3:  # 'fs', 'chs', 'adm': whole-name match, or the longer name starts with it as its own word
        long_ = nb if short == na else na
        return long_.split()[0] == short and not (short == "fs")
    if set(ta) <= set(tb) or set(tb) <= set(ta):
        return True
    return min(len(na), len(nb)) >= 6 and SequenceMatcher(None, na, nb).ratio() >= 0.86


def conflict(a, b):
    """True when two records are clearly different sites."""
    if a["_src"] == b["_src"] and a["license_number"] and b["license_number"]:
        return a["license_number"] != b["license_number"] or addr_key(a["address"]) != addr_key(b["address"]) or name_key(a["facility_name"]) != name_key(b["facility_name"])
    aa, ab = addr_key(a["address"]), addr_key(b["address"])
    return bool(aa and ab and aa != ab and not (aa in ab or ab in aa))


def same(a, b):
    if conflict(a, b):
        return False
    if a["_src"] == b["_src"] and a["license_number"] and b["license_number"]:
        return True  # identical license, address and name within one source
    for na in keys(a):
        for nb in keys(b):
            if names_match(na, nb):
                return True
    # fallback: full legal names, ignoring corporate suffixes, a trailing " - Town", and co-op spelling
    fa, fb = full_name(a), full_name(b)
    return bool(fa and fb and len(min(fa, fb, key=len)) >= 8 and (fa == fb or SequenceMatcher(None, fa, fb).ratio() >= 0.9))


STATE_WORDS = {"mn": "minnesota", "so": "southern", "ia": "iowa", "nd": "north dakota", "sd": "south dakota", "ne": "nebraska", "ks": "kansas"}


def full_name(a):
    s = re.sub(r"\s[-~]\s.*$", "", a["company"] or a["facility_name"] or "")
    s = norm_txt(s)
    s = re.sub(r"\bco op(erative)?\b", "cooperative", s)
    s = " ".join(STATE_WORDS.get(t, t) for t in s.split() if t not in {"inc", "incorporated", "llc", "lllp", "llp", "lp", "ltd", "corp", "corporation", "co", "company", "the", "of", "and"})
    return s


merged = []
for key, rs in groups.items():
    # records with street addresses seed clusters first, so address-less federal rows attach to the right site
    rs = sorted(rs, key=lambda r: (not r["address"], r["_file"] == "federal.csv"))
    clusters = []
    for r in rs:
        for c in clusters:
            if any(same(r, x) for x in c) and not any(conflict(r, x) for x in c):
                c.append(r)
                break
        else:
            clusters.append([r])
    merged.extend(clusters)
print("facilities after de-dup", len(merged), file=sys.stderr)


def pick(c, field):
    vals = [x[field] for x in c if x[field]]
    return max(vals, key=len) if vals else ""


fac = []
for c in merged:
    caps = [to_int(x["capacity_bu"]) for x in c]
    caps = [v for v in caps if v]
    lic_types = sorted({t.strip() for x in c for t in re.split(r"[;+]", x["license_type"]) if t.strip()})
    lic_nos = sorted({x["license_number"] for x in c if x["license_number"]})
    srcs = sorted({x["_src"] for x in c})
    # federal (WCMD) coordinates are town points only; treat them as a last-resort fallback
    exact = [x for x in c if to_float(x["lat"]) is not None and x["_file"] != "federal.csv"]
    town = [x for x in c if to_float(x["lat"]) is not None and x["_file"] == "federal.csv"]
    lat = to_float(exact[0]["lat"]) if exact else None
    lon = to_float(exact[0]["lon"]) if exact else None
    town_ll = (to_float(town[0]["lat"]), to_float(town[0]["lon"])) if town else None
    name = pick(c, "facility_name") or pick(c, "company")
    f = {
        "name": name, "company": pick(c, "company"), "address": pick(c, "address"), "city": pick(c, "city").title() if pick(c, "city").isupper() else pick(c, "city"),
        "state": c[0]["state"], "zip": (pick(c, "zip") or "")[:5], "county": pick(c, "county").title() if pick(c, "county").isupper() else pick(c, "county"),
        "lat": lat, "lon": lon, "geo": "source" if lat is not None else "",
        "cap": max(caps) if caps else None, "license_type": "; ".join(lic_types), "license_number": "; ".join(lic_nos[:6]),
        "commodities": pick(c, "commodities"), "src": "|".join(srcs),
        "notes": " / ".join(sorted({x["notes"] for x in c if x["notes"]}))[:500],
        "_town": town_ll,
    }
    if f["name"].isupper():
        f["name"] = f["name"].title()
    if f["company"].isupper():
        f["company"] = f["company"].title()
    fac.append(f)

# ---------- stable ids
seen = set()
for f in fac:
    base = f["state"] + "|" + city_key(f["city"]) + "|" + name_key(f["name"]) + "|" + addr_key(f["address"])
    h = hashlib.sha1(base.encode()).hexdigest()
    i = 0
    fid = f["state"] + "-" + h[:8]
    while fid in seen:
        i += 1
        fid = f["state"] + "-" + hashlib.sha1((base + str(i)).encode()).hexdigest()[:8]
    seen.add(fid)
    f["id"] = fid

# ---------- geocoding
G = os.path.join(DATA, "geo")
batch = {}
for p in glob.glob(os.path.join(G, "batch_out_*.csv")):
    with open(p, newline="", encoding="latin-1") as fh:
        for r in csv.reader(fh):
            if len(r) >= 6 and r[2] == "Match" and r[5]:
                lon_s, lat_s = r[5].split(",")
                batch[r[0]] = (float(lat_s), float(lon_s))


def load_gaz(fname, keyf):
    out = {}
    with open(os.path.join(G, fname), encoding="latin-1") as fh:
        rd = csv.reader(fh, delimiter="\t")
        head = [h.strip() for h in next(rd)]
        for r in rd:
            d = dict(zip(head, [x.strip() for x in r]))
            k = keyf(d)
            if k and k not in out:
                out[k] = (float(d["INTPTLAT"]), float(d["INTPTLONG"]))
    return out


SUFFIX = re.compile(r"\s+(city|town|village|cdp|borough|township|plantation|municipality|city and borough|unified government.*|metro government.*|consolidated government.*)$", re.I)
places = load_gaz("2024_Gaz_place_national.txt", lambda d: (d["USPS"], city_key(SUFFIX.sub("", d["NAME"]))))
cousub = load_gaz("2024_Gaz_cousubs_national.txt", lambda d: (d["USPS"], city_key(SUFFIX.sub("", d["NAME"]))))
zcta = load_gaz("2024_Gaz_zcta_national.txt", lambda d: d["GEOID"])
counties = load_gaz("2024_Gaz_counties_national.txt", lambda d: (d["USPS"], city_key(re.sub(r"\s+(county|parish|borough|census area|municipality)$", "", d["NAME"], flags=re.I))))

stat = defaultdict(int)
for f in fac:
    if f["lat"] is not None:
        stat["source"] += 1
        continue
    if f["id"] in batch:
        f["lat"], f["lon"] = batch[f["id"]]
        f["geo"] = "address"
    elif f["zip"] and f["zip"] in zcta and not f["city"]:
        f["lat"], f["lon"] = zcta[f["zip"]]
        f["geo"] = "zip"
    elif (f["state"], city_key(f["city"])) in places:
        f["lat"], f["lon"] = places[(f["state"], city_key(f["city"]))]
        f["geo"] = "city"
    elif (f["state"], city_key(f["city"])) in cousub:
        f["lat"], f["lon"] = cousub[(f["state"], city_key(f["city"]))]
        f["geo"] = "city"
    elif f["zip"] and f["zip"] in zcta:
        f["lat"], f["lon"] = zcta[f["zip"]]
        f["geo"] = "zip"
    elif f["_town"]:
        f["lat"], f["lon"] = f["_town"]
        f["geo"] = "city"
    elif f["county"] and (f["state"], city_key(f["county"])) in counties:
        f["lat"], f["lon"] = counties[(f["state"], city_key(f["county"]))]
        f["geo"] = "county"
    stat[f["geo"] or "none"] += 1
    if f["lat"] is not None:
        f["lat"], f["lon"] = round(f["lat"], 5), round(f["lon"], 5)
print("geocode", dict(stat), file=sys.stderr)
for f in fac:
    f.pop("_town", None)

# ---------- write
SHORT = {}
for s in sources.values():
    s["short"] = s["name"][:60]
cols = ["id", "name", "company", "address", "city", "state", "zip", "county", "lat", "lon", "geo", "cap", "license_type", "license_number", "commodities", "src", "notes"]
fac.sort(key=lambda f: (f["state"], f["city"], f["name"]))
out = {"generated": sys.argv[3] if len(sys.argv) > 3 else "", "sources": sorted(sources.values(), key=lambda s: -s["count"]), "cols": cols,
       "rows": [[f[c] if f[c] != "" else None for c in cols] for f in fac]}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, separators=(",", ":"))
# export rows for batch geocoding (street addresses not yet matched)
with open(os.path.join(G, "to_geocode.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    for f in fac:
        if f["address"] and f["geo"] != "address" and f["geo"] != "source" and not re.match(r"^(p\.?\s*o\.?\s*box|box)\b", f["address"], re.I):
            w.writerow([f["id"], f["address"], f["city"], f["state"], f["zip"]])
by_state = defaultdict(int)
for f in fac:
    by_state[f["state"]] += 1
print("by state", sorted(by_state.items(), key=lambda x: -x[1])[:20], file=sys.stderr)
print("total", len(fac), file=sys.stderr)
