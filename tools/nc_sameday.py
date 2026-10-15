#!/usr/bin/env python3
"""Same-day comparison of North Carolina early/absentee ballots for 2022, 2024 and 2026.

Reads NC State Board of Elections absentee files (one row per ballot) and writes
data/nc-sameday.json with cumulative accepted ballots by party and method, by days
before Election Day.

Usage: python3 tools/nc_sameday.py <dir with absentee_YYYYMMDD.zip files>
Source: https://dl.ncsbe.gov/?prefix=ENRS/
"""
import csv, io, json, os, sys, zipfile, datetime as dt
from collections import defaultdict

ELECTIONS = {"2022": "2022-11-08", "2024": "2024-11-05", "2026": "2026-11-03"}
FILES = {"2022": "absentee_20221108.zip", "2024": "absentee_20241105.zip", "2026": "absentee_20261103.zip"}
MAXOUT = 60  # days before Election Day to keep
TODAY = dt.date.today()

def party(p):
    p = (p or "").strip().upper()
    return "D" if p == "DEM" else "R" if p == "REP" else "O"

def run(folder):
    prev = {}
    if os.path.exists("data/nc-sameday.json"):
        try:
            prev = json.load(open("data/nc-sameday.json")).get("years", {})
        except Exception:
            prev = {}
    out = {"source": "NC State Board of Elections absentee files, dl.ncsbe.gov/ENRS",
           "note": "Accepted ballots (including cured and exceptions) by return date. Days out = days before Election Day.",
           "generated": dt.date.today().isoformat(), "years": {}}
    for yr, fn in FILES.items():
        path = os.path.join(folder, fn)
        if not os.path.exists(path):
            if yr in prev:
                out["years"][yr] = prev[yr]  # keep stored history (2022, 2024) without re-downloading
            continue
        ed = dt.date.fromisoformat(ELECTIONS[yr])
        daily = defaultdict(lambda: {"D": 0, "R": 0, "O": 0, "mail": 0, "inperson": 0})
        z = zipfile.ZipFile(path)
        with z.open(z.namelist()[0]) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1")):
                if not (row.get("ballot_rtn_status") or "").upper().startswith("ACCEPTED"):
                    continue
                d = (row.get("ballot_rtn_dt") or "").strip()
                try:
                    rd = dt.datetime.strptime(d, "%m/%d/%Y").date()
                except ValueError:
                    continue
                if rd > TODAY:
                    continue  # data-entry dates in the future
                out_days = (ed - rd).days
                if out_days < 0 or out_days > MAXOUT:
                    if out_days > MAXOUT:
                        out_days = MAXOUT
                    else:
                        continue
                rec = daily[out_days]
                rec[party(row.get("voter_party_code"))] += 1
                if (row.get("ballot_req_type") or "").upper().startswith(("EARLY", "ONE-STOP")):
                    rec["inperson"] += 1
                else:
                    rec["mail"] += 1
        # cumulative from the earliest day out (largest number) down to 0
        cum = {"D": 0, "R": 0, "O": 0, "mail": 0, "inperson": 0}
        series = []
        last_day = min(daily) if daily else MAXOUT
        for k in range(MAXOUT, -1, -1):
            if k in daily:
                for key in cum:
                    cum[key] += daily[k][key]
            if k < last_day:
                break
            t = cum["D"] + cum["R"] + cum["O"]
            series.append({"out": k, "date": (ed - dt.timedelta(days=k)).isoformat(), "D": cum["D"], "R": cum["R"], "O": cum["O"],
                           "total": t, "mail": cum["mail"], "inperson": cum["inperson"],
                           "margin": round((cum["D"] - cum["R"]) / t * 100, 2) if t else None})
        out["years"][yr] = {"election": ELECTIONS[yr], "through": series[-1]["date"] if series else None, "series": series}
        print(yr, "through", out["years"][yr]["through"], "days", len(series), "final", series[-1] if series else None)
    os.makedirs("data", exist_ok=True)
    json.dump(out, open("data/nc-sameday.json", "w"), separators=(",", ":"))
    print("wrote data/nc-sameday.json", os.path.getsize("data/nc-sameday.json"), "bytes")

if __name__ == "__main__":
    run(sys.argv[1])
