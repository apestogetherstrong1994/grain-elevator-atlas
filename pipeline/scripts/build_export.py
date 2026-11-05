"""Build export.csv: curated current U.S. grain export elevators.
Each row: primary current source (operator/status/capacity) + optional USACE NDC
Navigation Facilities (Docks) record for address/county/lat/lon.
Usage: python3 -I build_export.py <export_dir>
"""
import csv, json, os, sys

D = sys.argv[1]
RAW = os.path.join(D, 'raw')

usace = {}
for fn in ('docks_grain.json', 'docks_extra.json', 'docks_extra2.json'):
    for f in json.load(open(os.path.join(RAW, fn)))['features']:
        a = f['attributes']
        if a['OBJECTID'] not in usace or len(a) > len(usace[a['OBJECTID']]): usace[a['OBJECTID']] = a

USACE_NAME = 'USACE NDC Navigation Facilities (Docks) FeatureServer'
USACE_URL = 'https://services7.arcgis.com/n1YM8pTrFmm7L4hs/ArcGIS/rest/services/Docks/FeatureServer/0'
USACE_DATE = '2026-09-30'  # layer dataLastEditDate

APS = 'Agri Port Services port-region elevator info sheets'
APS_MS = 'https://www.agriportservices.com/port-regions/mississippi-river-region'
APS_PNW = 'https://www.agriportservices.com/port-regions/pacific-northwest-region'
APS_TX = 'https://www.agriportservices.com/port-regions/texas-region'
APS_AL = 'https://www.agriportservices.com/port-regions/mobile-alabama'
DUL = 'Duluth Seaway Port Authority - Port operations and facilities'
DUL_URL = 'https://duluthport.com/business/port-operations-and-facilities/'
TOL = 'Toledo-Lucas County Port Authority - Toledo Port Facilities map 2020'
TOL_URL = 'https://www.toledoport.org/s/toledo-port-facilities-2020.pdf'
CHS = 'CHS Inc. news story "Wheat / TEMCO" (2021-12-07)'
CHS_URL = 'https://www.chsinc.com/news-and-stories/2021/12/07/wheat-temco'

GRAIN = 'Grain'

# (facility_name, company, city, state, src_name, src_url, src_date, capacity_bu, commodities, usace_oid, address_override, notes)
R = [
 # ---- Mississippi River, LA ----
 ('ADM Ama Grain Elevator', 'Archer Daniels Midland Co. (ADM)', 'Ama', 'LA', APS, APS_MS, '2023-04-01', 5000000, GRAIN, 14043, None,
  'Mississippi River mile 117.6 West Bank; capacity per APS sheet (5.0 million bu / 136,078 MT).'),
 ('ADM Destrehan Grain Elevator', 'Archer Daniels Midland Co. (ADM)', 'Destrehan', 'LA', APS, APS_MS, '2023-04-01', 6270000, GRAIN, 13885, None,
  'Mississippi River mile 120.6 East Bank; capacity per APS (6.27 million bu / 170,640 MT).'),
 ('ADM Reserve Grain Elevator', 'Archer Daniels Midland Co. (ADM)', 'Reserve', 'LA', APS, APS_MS, '2023-04-01', 3600000, GRAIN, 15117, None,
  'Mississippi River mile 139.2 East Bank; capacity per APS (3.6 million bu / 97,976 MT).'),
 ('ADM St. Elmo Grain Elevator', 'Archer Daniels Midland Co. (ADM)', 'Paulina', 'LA', APS, APS_MS, '2023-04-01', 2000000, GRAIN, 15115, None,
  'Mississippi River mile 150.5 East Bank (APS sheet read by OCR); capacity 2.0 million bu / 54,431 MT. USACE record is titled ADM Growmark Paulina Terminal (operator field still lists Peavey/ConAgra).'),
 ('Bunge Destrehan Grain Elevator', 'Bunge', 'Destrehan', 'LA', APS, APS_MS, '2023-04-01', 3900000, GRAIN, 13736, None,
  'Mississippi River mile 120.2 East Bank; capacity per APS (3.9 million bu / 106,141 MT). Bunge completed its merger with Viterra in 2025.'),
 ('Cargill Reserve Grain Elevator', 'Cargill, Inc.', 'Reserve', 'LA', APS, APS_MS, '2023-04-01', 7743000, GRAIN, 11851, None,
  'Mississippi River mile 139.6 East Bank; capacity per APS (7.743 million bu / 210,730 MT).'),
 ('Cargill Westwego Grain Elevator', 'Cargill, Inc.', 'Westwego', 'LA', APS, APS_MS, '2023-04-01', 4300000, GRAIN, 7170, None,
  'Mississippi River mile 103.0 West Bank; capacity per APS (4.3 million bu / 117,027 MT). USACE: wharf owned by Port of New Orleans, operated by Cargill.'),
 ('CHS Myrtle Grove Grain Elevator', 'CHS Inc.', 'Myrtle Grove', 'LA', APS, APS_MS, '2023-04-01', 6464000, GRAIN, 14737, None,
  'Mississippi River mile 61.5 West Bank, Plaquemines Parish; capacity per APS (6.464 million bu / 176,901 MT).'),
 ('Louis Dreyfus Port Allen Export Grain Elevator', 'Louis Dreyfus Company (LDC)', 'Port Allen', 'LA', APS, APS_MS, '2023-04-01', 8900000, GRAIN, 15947,
  '527 Elevator Road',
  'Mississippi River mile 228.5 West Bank; capacity per APS (8.9 million bu / 242,220 MT). Elevator owned by Port of Greater Baton Rouge; address 527 Elevator Road, Port Allen, LA 70767 from https://www.portgbr.com/export-grain-elevator (LDC operator since 2011).'),
 ('Zen-Noh Grain Convent Elevator', 'Zen-Noh Grain Corp.', 'Convent', 'LA', APS, APS_MS, '2023-04-01', 4000000, GRAIN, 15981, None,
  'Mississippi River mile 163.8 East Bank; capacity per APS (4.0 million bu / 108,862 MT).'),
 # ---- Gulf: AL, TX ----
 ('Agrex Grain Elevator, Alabama State Docks Pier River D', 'Agrex Inc.', 'Mobile', 'AL', APS, APS_AL, '2025-08-20', None, 'Grain', 7159, None,
  'Public grain elevator at Alabama State Docks operated by Agrex; capacity not published on sheet. USACE record lists Agrex Grain Elevator / Pier D.'),
 ('TEMCO Houston Grain Elevator', 'TEMCO LLC (CHS/Cargill JV); Cargill-owned', 'Houston', 'TX', APS, APS_TX, '2026-04', 6000000, 'Grain', None,
  '9702 Clinton Dr',
  'APS sheet (file "Updated 4/2026") gives address 9702 Clinton Dr, Houston, TX 77029. Capacity 6 million bu per FreightWaves 2023-03-05 (https://www.freightwaves.com/news/borderlands-houston-export-terminal-lets-temco-capitalize-on-grain-demand). Formerly Cargill Houston; added to TEMCO JV 2021. USACE record "Cargill, Houston Grain Elevator Pier" (OID 11800, 6,000,000 bu) may be this site but address differs, so no coordinates given.'),
 ('Andersons Grain Terminal Houston', 'The Andersons, Inc.', 'Galena Park', 'TX', APS, APS_TX, '2025-08', 6232000, 'Grain', None,
  '1500 South Main St.',
  'APS "Anderson\'s Grain Terminal Houston Updated" sheet: 1500 South Main St., Galena Park, TX; storage 6,232,000 bu. No matching USACE record found.'),
 ('Hansen-Mueller Terminal Houston (mobile loader)', 'Hansen-Mueller Co.', 'Houston', 'TX', APS, APS_TX, '2025-08', None, 'Wheat; Corn; Sorghum; Soybeans', None, None,
  'APS sheet: mobile ship loader at Houston City Docks (generally dock #16), receives by rail/truck; not a fixed elevator, no storage listed. Include/exclude per your definition.'),
 ('ADM Corpus Christi Grain Elevator', 'Archer Daniels Midland Co. (ADM)', 'Corpus Christi', 'TX', APS, APS_TX, '2024-07', 4500000, 'Grain', 18815, None,
  'APS sheet (docx): Corpus Christi Inner Harbor, storage "about 4.5 million bushels". Elevator owned by Port of Corpus Christi (USACE).'),
 ('Port of Brownsville Grain Elevator', 'West Plains LLC (BioUrja Group)', 'Brownsville', 'TX', 'MyRGV / Valley Morning Star news "Going up: Port elevator resumes grain shipments"',
  'https://myrgv.com/uncategorized/2020/09/17/going-up-port-elevator-resumes-grain-shipments/', '2020-09-17', 3000000, 'Corn; Sorghum', 18814, None,
  'Port-owned elevator reactivated Aug 2020 by West Plains after ~13 years without vessel grain loading; 3 million bu. Current (2025-26) operating status not re-verified.'),
 # ---- PNW ----
 ('Kalama Export Company Grain Terminal', 'Kalama Export Company LLC', 'Kalama', 'WA', APS, APS_PNW, '2023-01-01', 5800000, 'Corn; Sorghum; Soybeans; Wheat; Barley', 12835, None,
  'Columbia River mile 74. APS: JV of ADM, Gavilon and Agrex (Mitsubishi); Gavilon grain was sold to Viterra (2022), now part of Bunge. USACE owner field still says Peavey/ConAgra.'),
 ('TEMCO Kalama Grain Elevator', 'TEMCO LLC (CHS/Cargill JV)', 'Kalama', 'WA', APS, APS_PNW, '2023-01-01', 6400000, 'Grain', 17541, None,
  'Columbia River mile 77; formerly CHS Kalama. Also confirmed as TEMCO terminal by CHS 2021-12-07 (' + CHS_URL + ').'),
 ('United Grain Vancouver Terminal', 'United Grain Corp. (Mitsui & Co.)', 'Vancouver', 'WA', APS, APS_PNW, '2023-01-01', 7000000, 'Grain', 14126, None,
  'Columbia River mile 104; Port of Vancouver USA owns the wharf (USACE).'),
 ('EGT Longview Grain Terminal', 'EGT, LLC (Bunge / ITOCHU / Pan Ocean JV)', 'Longview', 'WA', APS, APS_PNW, '2023-01-01', 4740000, 'Grain; soybean meal; DDGS', 19528, None,
  'Port of Longview Berth 9, Columbia River mile 67; opened 2011; storage 4,740,000 bu (130,000 MT).'),
 ('Columbia Grain Portland Terminal (T5 Berth 501)', 'Columbia Grain International (Marubeni)', 'Portland', 'OR', APS, APS_PNW, '2023-01-01', 4000000, 'Grain', 13029, None,
  'Port of Portland Terminal 5, Berth 501.'),
 ('TEMCO Portland Grain Elevator', 'TEMCO LLC (CHS/Cargill JV)', 'Portland', 'OR', APS, APS_PNW, '2023-01-01', 1500000, 'Grain', 7735, None,
  'Willamette River, downtown Portland; APS says formerly operated by CLD. Confirmed TEMCO terminal by CHS 2021-12-07. Coordinates/address from USACE record "TEMCO Wheat Elevator Terminals, Portland" (USACE address 1100 NW Murray Rd, 97229 is off-river, likely an office, so address left blank; lat/lon is the river dock). Note: a 2021 blog citing Portland Business Journal reports LDC sold its nearby Portland "O dock" elevator in 2019; site identities should be checked.'),
 ('TEMCO Tacoma Grain Terminal', 'TEMCO LLC (CHS/Cargill JV)', 'Tacoma', 'WA', CHS, CHS_URL, '2021-12-07', None, 'Grain', 13441, None,
  'Puget Sound. USACE record "Tacoma Export Marketing Co., Tacoma Elevator Wharf" (Port of Tacoma owner) lists 3,000,000 bu elevator (older figure).'),
 ('Louis Dreyfus Terminal 86 Grain Facility', 'Louis Dreyfus Company (LDC)', 'Seattle', 'WA', 'Port of Seattle Internal Audit Report 2023-11 (Louis Dreyfus)',
  'https://meetings.portseattle.org/portmeetings/attachments/2023/2023_09_07_AM_11_Louis_Dreyfus-Report.pdf', '2023-08-18', 4000000, 'Corn; Soybeans; Sorghum', 12506,
  '955 Alaskan Way W.',
  'Port of Seattle-owned; LDC operator (lease signed 2014-11-01). Capacity "almost 4 million bushels". Address 955 Alaskan Way W., Seattle 98119 from https://www.portseattle.org/page/terminal-86-grain-facility.'),
 ('Penny Newman Stockton Export Elevator', 'Penny Newman Grain Co.', 'Stockton', 'CA', 'Federal Register 90 FR (2025-07-03) AMS official agency geographic areas notice, doc 2025-12487',
  'https://www.govinfo.gov/content/pkg/FR-2025-07-03/html/2025-12487.htm', '2025-07-03', None, 'Grain', 15817, None,
  'FR notice names the "Penny-Newman export elevator in Stockton, CA". Port of Stockton.'),
 # ---- Atlantic ----
 ('Perdue AgriBusiness Chesapeake Export Facility', 'Perdue AgriBusiness', 'Chesapeake', 'VA', 'Perdue AgriBusiness press release (25 years at Chesapeake, VA)',
  'https://business.mammothtimes.com/mammothtimes/article/gnwcq-2025-8-26-perdue-agribusiness-marks-25-years-of-innovation-partnership-and-growth-at-chesapeake-va-facility', '2025-08-26', None,
  'Corn; soybean meal; soybean oil; soy hull pellets', 12868, None,
  'Deepwater bulk grain terminal loading 100+ vessels/yr via Port of Virginia.'),
 # ---- Great Lakes ----
 ('Duluth Lake Port', 'Duluth Seaway Port Authority (owner); Lake Superior Warehousing', 'Duluth', 'MN', DUL, DUL_URL, '2026-05-01', None, 'Grain', 14279, None,
  'Port list (page modified 2026-05-01) commodity: Grain. USACE record "Duluth Lake Port Storage" still lists AGP Grain as owner/operator. Export (vs domestic laker) role not stated by source.'),
 ('Bartlett-Duluth Storage', 'Bartlett', 'Duluth', 'MN', DUL, DUL_URL, '2026-05-01', None, 'Dry bulk; Grain', 13146, '250 Garfield Ave.',
  '250 Garfield Ave., Duluth 55802 (port list). Phone matches USACE Cargill B-1/B-2 dock records (former Cargill Duluth elevator); coordinates from USACE "Cargill B-2 Dock". Export role not stated by source.'),
 ('Bunge Connors Point Terminal', 'Bunge', 'Superior', 'WI', DUL, DUL_URL, '2026-05-01', None, 'Dry bulk; Grain', 14715, '400 N. Main',
  'Former Peavey/ConAgra -> Gavilon -> Viterra terminal, now Bunge (port list 2026). Export role not stated by source.'),
 ('DeLong Agricultural Maritime Export Facility (Port Milwaukee)', 'The DeLong Co.', 'Milwaukee', 'WI', 'Spectrum News 1 Wisconsin',
  'https://spectrumnews1.com/wi/milwaukee/news/2023/09/01/export-facility-changes-the-game-for-wisconsin-farming-exports', '2023-09-01', None, 'DDGS; soybean meal', None, None,
  'Opened 2023 in partnership with Port Milwaukee; exports distillers grains and soybean meal (grain by-products) - phase 2 to add whole grains. No USACE match.'),
 ('ADM Toledo Grain Terminal', 'Archer Daniels Midland Co. (ADM)', 'Toledo', 'OH', TOL, TOL_URL, '2020-12-09', None, 'Grain', 15910, None,
  'Port map lists "ADM Terminal - Grain Terminal". USACE: serves seaway-draft ocean ships and lake vessels.'),
 ('The Andersons Toledo Edwin Drive Terminal', 'The Andersons, Inc.', 'Toledo', 'OH', TOL, TOL_URL, '2020-12-09', None, 'Grain; ethanol', 15909, None,
  'Port map: "Andersons Edwin Dr. Terminal - Grain and Ethanol Terminal".'),
 ('The Andersons Toledo Terminal (Kuhlman Drive)', 'The Andersons, Inc.', 'Toledo', 'OH', TOL, TOL_URL, '2020-12-09', None, 'Grain; bulk cargo', 17360, None,
  'Port map: "Andersons Terminal - Grain/Bulk Cargo Terminal"; matched to USACE Kuhlman Drive terminal record (match by name, not confirmed by source).'),
 ('Burns Harbor International Agriculture Terminal', 'Louis Dreyfus Company (LDC); Ports of Indiana (owner)', 'Portage', 'IN', 'FreightWaves news "Indiana port taps Louis Dreyfus to restart grain terminal"',
  'https://www.freightwaves.com/news/indiana-port-taps-louis-dreyfus-to-restart-grain-terminal', '2025-06-24', 7200000, 'Corn; Soybeans', None, None,
  'Closed 2023; LDC selected to reopen, operations expected early 2026 (reopening not confirmed here). Loads ocean and lake vessels up to 90,000 bu/hr.'),
]

cols = ['facility_name','company','address','city','state','zip','county','lat','lon','capacity_bu','license_type','license_number','commodities','source_name','source_url','source_date','notes']

def clean(s):
    return ' '.join(str(s).split()).rstrip('.') if s else ''

rows = []
for (fac, co, city, st, sn, su, sd, cap, com, oid, addr, notes) in R:
    a = usace.get(oid) if oid else None
    rec = {c: '' for c in cols}
    rec.update(facility_name=fac, company=co, city=city, state=st, capacity_bu=cap or '',
               license_type='Export elevator', commodities=com, notes=notes)
    names, urls, dates = [sn], [su], [sd]
    if a:
        rec['address'] = addr or clean(a['STREET_ADDRESS'])
        z = clean(a.get('ZIPCODE'))
        rec['zip'] = z
        rec['county'] = clean(a.get('COUNTY_NAME'))
        rec['lat'] = a['LATITUDE']; rec['lon'] = a['LONGITUDE']
        names.append(USACE_NAME); urls.append(USACE_URL + '/query?where=NAV_UNIT_ID%3D%27' + a['NAV_UNIT_ID'] + '%27&outFields=*&f=json')
        dates.append(USACE_DATE)
        rec['notes'] += ' | Address/county/lat/lon from USACE record NAV_UNIT_ID ' + a['NAV_UNIT_ID'] + ' ("' + clean(a['NAV_UNIT_NAME']) + '").'
        if a['STATE'] != st:
            raise SystemExit('state mismatch ' + fac)
    else:
        rec['address'] = addr or ''
    if fac.startswith('Andersons Grain Terminal Houston'): rec['zip'] = ''
    if fac.startswith('TEMCO Houston'): rec['zip'] = '77029'
    if fac.startswith('Louis Dreyfus Port Allen'): rec['zip'] = '70767'
    if fac.startswith('Louis Dreyfus Terminal 86'): rec['zip'] = '98119'
    if fac.startswith('Bartlett') or fac.startswith('Duluth Lake Port'): rec['zip'] = '55802'
    if fac.startswith('Bunge Connors'): rec['zip'] = '54880'
    if fac.startswith('Duluth Lake Port'): rec['address'] = '602 Helberg Drive'
    if fac.startswith('TEMCO Portland'): rec['address'] = ''; rec['zip'] = ''  # USACE address is an office (NW Murray Rd); dock coords kept
    rec['source_name'] = ' | '.join(names); rec['source_url'] = ' | '.join(urls); rec['source_date'] = ' | '.join(dates)
    rows.append(rec)

out = os.path.join(D, 'export.csv')
with open(out, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r['state'] for r in rows))
