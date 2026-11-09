# Facility Atlas (grain elevators and plastics recycling plants)

A map and list of U.S. industrial facilities built from public records, with a **Facility type** switcher at the top:

- **Grain elevators:** every licensed grain elevator and warehouse in federal and state records, about 7,200 facilities in 39 states.
- **Plastics recycling plants:** about 610 plants in 42 states that turn plastic scrap into regrind, flake, pellets or compounds (plants like Ultra-Poly in Portland, PA), plus chemical recyclers as their own category.

Each facility can be assigned to someone on the BD team, given a status, and annotated with notes that everyone on the team sees live. Both types share one sign-in and one tracking table; plastics ids start with `PL-` so they never collide with grain ids. Link straight to a type with `?type=grain` or `?type=plastics`.

- **Front end:** one static page (`public/index.html`) with d3 + TopoJSON for the map. No build step.
- **Shared data:** [Supabase](https://supabase.com) for sign-in (email magic link), the `team`, `tracking` and `notes` tables, and realtime updates.
- **Hosting:** Vercel serves `public/` as a static site.

## Who can sign in

Anyone with an `@lumaril.com` email address, plus anyone listed in the `team` table (for personal addresses). Teammates can add someone from the owner picker by typing their email. Everyone else can browse the inventory and export CSV but can't see or change assignments and notes. Access is enforced by row-level security in `supabase/schema.sql`.

## Setup

1. **Supabase:** create a project. In **SQL Editor**, run `supabase/schema.sql`.
2. **Auth URLs:** in **Authentication → URL Configuration**, set **Site URL** to your Vercel URL and add it under **Redirect URLs** (e.g. `https://grain-elevator-atlas.vercel.app/**`).
3. **Config:** copy the **Project URL** and **anon public key** from **Project Settings → API** into `public/config.js`. The anon key is meant to be public; RLS protects the data.
4. **Vercel:** import this repo. No framework or build command is needed; `vercel.json` points at `public/`.

Optional: enable Google sign-in under **Authentication → Providers**. The page uses magic links by default, so no extra setup is needed.

## Statuses

`none` (Not started), `research`, `contacted`, `convo` (In conversation), `visit` (Site visit), `pilot`, `nofit` (Not a fit).

## License types (map colors)

| Type | Meaning |
|---|---|
| Export elevator | Port terminal that loads grain onto ships for export |
| Federal warehouse | Licensed by USDA under the U.S. Warehouse Act |
| State warehouse | Grain storage licensed and bonded by a state |
| Dealer or buyer only | Licensed to buy grain but not store it for others |
| CCC approved only | Approved to store USDA Commodity Credit Corporation grain, no warehouse license in our sources |
| Type not given | Licensed, but the source doesn't say which license (mainly Indiana) |

## Plastics data

`public/plastics.json` is built by `pipeline/scripts/merge_plastics.py` from `pipeline/plastics/*/*.csv`:

| File | Sources |
|---|---|
| `national/national.csv` | EPA Recycling Infrastructure map (plastic recycling facilities layer), EPA Facility Registry Service and ECHO (filtered by NAICS and name), Beyond Plastics and NRDC chemical-recycling plant lists |
| `industry/industry.csv` | NAPCOR PET reclaimer directory, APR certification list, company plant pages, trade press, ENF Recycling Directory (self-listed; leads, not verified) |
| `east/east.csv` | NC DEQ Recycling Markets Directory, PA DEP plastic processors list, NERC-NEWMOA, RecyclingWorks MA, NY DEC, MD MDE |
| `west/west.csv` | CalRecycle RMDZ directory and grant lists, Oregon DEQ responsible end markets list, WA Ecology, MN PCA, IA DNR, CO, NE, MO, MS |

`pipeline/plastics/excluded.tsv` lists plants found to be closed or suspended; the merge drops them. Plant type comes from each source's description and resins: polyolefin reprocessor, PET reclaimer, mixed or engineering resins, advanced (chemical) recycling, or type not given.

```bash
python3 pipeline/scripts/merge_plastics.py pipeline/plastics public/plastics.json "Nov 9, 2026"
```

## Grain data

`public/elevators.json` is built by `pipeline/scripts/merge.py` from the per-source CSVs in `pipeline/sources/`:

| File | Sources |
|---|---|
| `federal.csv` | USDA AMS Warehouse & Commodity Management dashboard (USWA-licensed and CCC-approved warehouses) |
| `west.csv` | Missouri, Iowa, Nebraska state lists |
| `east.csv` | Illinois, Indiana, Ohio, Michigan, Wisconsin, Kentucky |
| `north.csv` | North Dakota, South Dakota, Minnesota |
| `mt.csv` | Montana (MTPlants license search) |
| `south.csv` | Washington, Texas, Colorado, Louisiana, Tennessee, Georgia, Idaho, Arkansas, Mississippi |
| `export.csv` | Current export terminals from operator, port and Army Corps of Engineers records |

The merge de-duplicates records that describe the same site (matching facility and company names within a town, never across different street addresses), repairs town names against Census places, and places each facility on the map using, in order: source coordinates, Census batch-geocoded street address, town, ZIP, or county centroid. Every facility lists its sources.

To rebuild (needs the Census Gazetteer place, county subdivision, ZCTA and county files in `pipeline/geo/`):

```bash
python3 pipeline/scripts/merge.py pipeline public/elevators.json "Nov 5, 2026"
```

Known gaps: Kansas, Oklahoma, Oregon and most Southeastern and Northeastern states publish no state list, so they come from the federal list only. Small private and on-farm bins aren't licensed and aren't included. Some state rows are dealer or buyer licenses, which can be offices rather than elevators.

Facility IDs (`ND-8903b2be`) are stable hashes of state, town, name and address. If a re-merge changes a facility's name or address, its ID can change, and its assignments and notes would need to be moved to the new ID.
