import csv, re, sys
S = sys.argv[1]
places = set()
for f in ("2024_Gaz_place_national.txt", "2024_Gaz_cousubs_national.txt"):
    with open(f"{S}/data/geo/{f}", encoding="latin-1") as fh:
        rd = csv.reader(fh, delimiter="\t"); h = [x.strip() for x in next(rd)]
        for r in rd:
            d = dict(zip(h, [x.strip() for x in r]))
            if d["USPS"] == "MT":
                places.add(re.sub(r"\s+(city|town|CDP|consolidated.*)$", "", d["NAME"], flags=re.I).lower())
COLS = "facility_name,company,address,city,state,zip,county,lat,lon,capacity_bu,license_type,license_number,commodities,source_name,source_url,source_date,notes".split(",")
out = csv.DictWriter(open(f"{S}/data/mt/mt.csv", "w", newline=""), COLS)
out.writeheader(); n = 0; withcity = 0
for line in open(f"{S}/data/mt/raw/mtplants.tsv"):
    lid, name, ops = line.rstrip("\n").split("\t")
    m = re.match(r"^(.*?)\s+(?:~|-)\s+(.*)$", name)
    company, suffix = (m.group(1), m.group(2)) if m else (name, "")
    city = ""
    if suffix:
        c = re.sub(r"\s*\(.*\)$", "", suffix)
        c = re.sub(r"^Ft\.?\s", "Fort ", c)
        c = re.sub(r"\s+(E|West|Pul)$", "", c)
        if c.lower() in places: city = c
    kinds = {"D": "Commodity Dealer", "W": "Commodity Warehouse"}
    lt = "; ".join("MT " + kinds[k.strip()] for k in ops.split(","))
    notes = "Montana list gives no address; " + (f"town taken from licence name ('{suffix}')." if city else (f"location label '{suffix}' not matched to a town." if suffix else "location not given."))
    out.writerow({"facility_name": name, "company": company, "city": city, "state": "MT", "license_type": lt, "license_number": lid,
                  "source_name": "Montana Dept. of Agriculture - MTPlants External License Search (Commodity Dealer/Warehouse)",
                  "source_url": "https://mtplants.mt.gov/Licenses/External/ExternalLicenseSearch.aspx", "source_date": "2026-11-05", "notes": notes})
    n += 1; withcity += bool(city)
print(n, "rows,", withcity, "with town")
