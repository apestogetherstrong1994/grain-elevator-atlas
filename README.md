# Grain Elevator Atlas

A map and list of every licensed U.S. grain elevator and warehouse we could find in public federal and state records — about 7,200 facilities in 39 states. Each facility can be assigned to someone on the BD team, given a status, and annotated with notes that everyone on the team sees live.

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

## Data

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
