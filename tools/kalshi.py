#!/usr/bin/env python3
"""Merge a Kalshi browser dump into data/kalshi.json for the /odds/ page.

Usage (from the repo root):
    python3 tools/kalshi.py <dump.json> [--tx <texas early vote dump.json>]

The dump is produced in the browser (on kalshi.com, where the public API can be
fetched) by the daily scheduled pull. Shape:
{
  "pulled": "2026-10-26T15:10:00Z",
  "live":   {TICKER: {"last":0.36,"bid":0.35,"ask":0.36,"vol24":748939,"oi":21742924}},
  "candles":{TICKER: [["2026-10-25", 0.36, 748939], ...]},   # date = US Eastern trading day, close price, contracts traded
  "big":    [{"t":"2026-10-21T19:52:27Z","ticker":"SENATETX-26-R","side":"no","contracts":184720,"usd":121915,"price":0.34}],
  "taker":  {TICKER: {"2026-10-25":[yes_taker_contracts, no_taker_contracts]}},
  "book":   {TICKER: {"for":n, "against":n}},
  "scan_from": "2026-10-24T05:00:00Z",                        # start of the trade scan window (big orders, taker)               # resting contracts within 3 cents of the price, for and against YES
  "hourly": {"start": unix_hour_end, "step": 3600,
             "price": {TICKER: [640, 650, ...]},             # tenths of a cent, last trade of each hour, carried forward
             "vol":   {RACE_ID: [12, 30, ...]}}              # thousands of contracts per hour, both sides of the race
}
Every section is optional. Existing history is never deleted; same-key entries are replaced.
It also refreshes the early vote party split for each race state from early-vote/index.html.
"""
import json, re, sys, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "kalshi.json")
EV_HTML = os.path.join(ROOT, "early-vote", "index.html")

# basis: "party" = state registers voters by party (hard counts), "modeled" = no party registration
RACES = [
    {"id": "control", "label": "Senate control", "state": None, "basis": None,
     "d": {"ticker": "CONTROLS-2026-D", "name": "Democrats"}, "r": {"ticker": "CONTROLS-2026-R", "name": "Republicans"}},
    {"id": "TX", "label": "Texas", "state": "TX", "basis": "modeled",
     "d": {"ticker": "SENATETX-26-D", "name": "James Talarico"}, "r": {"ticker": "SENATETX-26-R", "name": "Ken Paxton"}},
    {"id": "OH", "label": "Ohio (special)", "state": "OH", "basis": "modeled",
     "d": {"ticker": "SENATEOHS-26-D", "name": "Sherrod Brown"}, "r": {"ticker": "SENATEOHS-26-R", "name": "Jon Husted"}},
    {"id": "ME", "label": "Maine", "state": "ME", "basis": "party",
     "d": {"ticker": "SENATEME-26-D", "name": "Troy Jackson"}, "r": {"ticker": "SENATEME-26-R", "name": "Susan Collins"}},
    {"id": "MI", "label": "Michigan", "state": "MI", "basis": "modeled",
     "d": {"ticker": "SENATEMI-26-D", "name": "Abdul El-Sayed"}, "r": {"ticker": "SENATEMI-26-R", "name": "Mike Rogers"}},
    {"id": "IA", "label": "Iowa", "state": "IA", "basis": "party",
     "d": {"ticker": "SENATEIA-26-D", "name": "Josh Turek"}, "r": {"ticker": "SENATEIA-26-R", "name": "Ashley Hinson"}},
    {"id": "AK", "label": "Alaska", "state": "AK", "basis": "party",
     "d": {"ticker": "SENATEAK-26-D", "name": "Democrat"}, "r": {"ticker": "SENATEAK-26-R", "name": "Republican"}},
    {"id": "NE", "label": "Nebraska", "state": "NE", "basis": "party",
     "d": {"ticker": "SENATENE-26-DOSB", "name": "Dan Osborn (I)"}, "r": {"ticker": "SENATENE-26-R", "name": "Pete Ricketts"}},
    {"id": "NC", "label": "North Carolina", "state": "NC", "basis": "party",
     "d": {"ticker": "SENATENC-26-D", "name": "Roy Cooper"}, "r": {"ticker": "SENATENC-26-R", "name": "Michael Whatley"}},
    {"id": "GA", "label": "Georgia", "state": "GA", "basis": "modeled",
     "d": {"ticker": "SENATEGA-26-D", "name": "Jon Ossoff"}, "r": {"ticker": "SENATEGA-26-R", "name": "Mike Collins"}},
    {"id": "NH", "label": "New Hampshire", "state": "NH", "basis": "party",
     "d": {"ticker": "SENATENH-26-D", "name": "Chris Pappas"}, "r": {"ticker": "SENATENH-26-R", "name": "John E. Sununu"}},
    {"id": "MN", "label": "Minnesota", "state": "MN", "basis": "modeled",
     "d": {"ticker": "SENATEMN-26-D", "name": "Peggy Flanagan"}, "r": {"ticker": "SENATEMN-26-R", "name": "Michele Tafoya"}},
]
TICKERS = {s["ticker"] for r in RACES for s in (r["d"], r["r"])}


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def num(x):
    return None if x is None else float(x)


def early_vote_split():
    """{state: {date: [total, rep, dem]}} from the SNAPSHOTS array in early-vote/index.html."""
    out = {}
    try:
        html = open(EV_HTML).read()
    except FileNotFoundError:
        return out
    m = re.search(r"/\*DATA-START\*/(.*?)/\*DATA-END\*/", html, re.S)
    if not m:
        return out
    block = m.group(1)
    want = {r["state"] for r in RACES if r["state"]}
    for sm in re.finditer(r'\{date:"(\d{4}-\d{2}-\d{2})".*?states:\{(.*?)\}\s*\}', block, re.S):
        date, states = sm.group(1), sm.group(2)
        for st in want:
            v = re.search(r"\b%s:\[([^\]]*)\]" % st, states)
            if not v:
                continue
            vals = [int(float(x)) for x in v.group(1).split(",")[:3]]
            if vals[0] > 0:
                out.setdefault(st, {})[date] = vals
    return out


def tx_turnout(path):
    d = load(path, {})
    out = {}
    for day in d.get("days", []):
        if day.get("ip_day", 0) == 0 and day.get("reporting", 0) == 0 and day["date"] >= "2026-10-19":
            continue  # carried-forward or not yet posted
        if day["date"] >= "2026-10-19" and day.get("reporting", 0) < 150:
            continue  # partial county posting
        out[day["date"]] = [day["total"], day["ip"], day["mail"]]
    return out


def early_vote_pull_times():
    """{date: "YYYY-MM-DDTHH:MM"} Central, from each SNAPSHOTS entry's pulled string."""
    out = {}
    try:
        html = open(EV_HTML).read()
    except FileNotFoundError:
        return out
    for m in re.finditer(r'\{date:"(\d{4}-\d{2}-\d{2})",\s*pulled:"([^"]+)"', html):
        date, pulled = m.group(1), m.group(2)
        t = re.search(r"(\w{3}) (\d{1,2}), (\d{4}),? (\d{1,2}):(\d{2}) ?([AP]M)", pulled)
        if not t:
            continue
        mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(t.group(1)) + 1
        hh = int(t.group(4)) % 12 + (12 if t.group(6) == "PM" else 0)
        out[date] = "%s-%02d-%02dT%02d:%s" % (t.group(3), mon, int(t.group(2)), hh, t.group(5))
    return out


def merge_hourly(data, new):
    """Merge {"start", "step", "price": {ticker: [...]}, "vol": {race: [...]}} onto one hourly grid.
    Newer values replace older ones for the same hour (the last hour of a pull is often partial)."""
    if not new or not new.get("price"):
        return 0
    old = data.get("hourly") or {"start": new["start"], "step": 3600, "price": {}, "vol": {}}
    start = min(old["start"], new["start"])
    def end_of(h):
        lens = [len(v) for v in list(h["price"].values()) + list(h["vol"].values())] or [0]
        return h["start"] + (max(lens) - 1) * 3600
    end = max(end_of(old), end_of(new))
    n = (end - start) // 3600 + 1
    merged = {"start": start, "step": 3600, "price": {}, "vol": {}}
    count = 0
    for kind, blank in (("price", None), ("vol", 0)):
        keys = set(old[kind]) | set(new[kind])
        for k in keys:
            arr = [blank] * n
            for src in (old, new):
                vals = src[kind].get(k)
                if not vals:
                    continue
                off = (src["start"] - start) // 3600
                for i, v in enumerate(vals):
                    if v is not None:
                        arr[off + i] = int(v)
                        if src is new:
                            count += 1
            if kind == "price":  # carry forward through gaps
                first = next((x for x in arr if x is not None), None)
                last = first
                for i in range(n):
                    if arr[i] is None:
                        arr[i] = last
                    last = arr[i]
            merged[kind][k] = arr
    data["hourly"] = merged
    return count


def compute_flips(daily):
    flips = []
    for r in RACES:
        dd, rr = daily.get(r["d"]["ticker"], {}), daily.get(r["r"]["ticker"], {})
        prev = None
        for date in sorted(set(dd) & set(rr)):
            dp, rp = dd[date][0], rr[date][0]
            if dp is None or rp is None or dp == rp:
                continue
            lead = "d" if dp > rp else "r"
            if prev and lead != prev:
                flips.append({"race": r["id"], "date": date, "to": lead,
                              "d": round(dp, 3), "r": round(rp, 3)})
            prev = lead
    return flips


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    dump = load(argv[1], None)
    if dump is None:
        print("dump not found:", argv[1])
        return 1
    tx_path = None
    if "--tx" in argv:
        tx_path = argv[argv.index("--tx") + 1]

    data = load(OUT, {})
    data.setdefault("daily", {})
    data.setdefault("big", [])
    data.setdefault("taker", {})
    data.setdefault("book", {})
    data.setdefault("live", {})

    changed = 0
    for t, rows in (dump.get("candles") or {}).items():
        if t not in TICKERS:
            continue
        slot = data["daily"].setdefault(t, {})
        for row in rows:
            date, close, vol = row[0], num(row[1]), int(round(float(row[2] or 0)))
            if close is None:
                continue
            slot[date] = [round(close, 4), vol]
            changed += 1
    for t, v in (dump.get("live") or {}).items():
        if t in TICKERS:
            data["live"][t] = {k: v.get(k) for k in ("last", "bid", "ask", "vol24", "oi")}
    seen = {(b["t"], b["ticker"], b["side"]) for b in data["big"]}
    for b in dump.get("big") or []:
        key = (b["t"], b["ticker"], b["side"])
        if b["ticker"] in TICKERS and key not in seen:
            data["big"].append({"t": b["t"], "ticker": b["ticker"], "side": b["side"],
                                "contracts": int(b["contracts"]), "usd": int(b["usd"]), "price": num(b["price"])})
            seen.add(key)
    data["big"].sort(key=lambda b: b["t"])
    for t, days in (dump.get("taker") or {}).items():
        if t in TICKERS:
            data["taker"].setdefault(t, {}).update({d: [int(v[0]), int(v[1])] for d, v in days.items()})
    pulled_day = (dump.get("pulled") or "")[:10] or datetime.date.today().isoformat()
    for t, v in (dump.get("book") or {}).items():
        if t in TICKERS:
            data["book"].setdefault(t, {})[pulled_day] = {"for": int(v["for"]), "against": int(v["against"])}

    # which markets have had their trades scanned for big orders, and from when
    scan_from = dump.get("scan_from")
    if scan_from:
        cov = data.setdefault("big_scanned_from", {})
        for t in dump.get("scanned") or list((dump.get("taker") or {}).keys()):
            if t in TICKERS and (t not in cov or scan_from < cov[t]):
                cov[t] = scan_from

    hourly_rows = merge_hourly(data, dump.get("hourly"))

    data["ev"] = early_vote_split()
    data["ev_pulls"] = early_vote_pull_times()
    if tx_path:
        data.setdefault("tx_turnout", {}).update(tx_turnout(tx_path))
    data["races"] = RACES
    data["flips"] = compute_flips(data["daily"])
    data["pulled"] = dump.get("pulled") or data.get("pulled")
    data["source"] = "Kalshi public market data API (api.elections.kalshi.com/trade-api/v2): daily candlesticks, trades and order book"
    data["note"] = ("Prices are the last trade of each US Eastern trading day, in dollars per $1 contract "
                    "(0.64 = 64 percent implied chance). big = taker orders of 25,000+ contracts filled in the same second "
                    "on the same side. taker = contracts bought aggressively on each side per Central time day. "
                    "book = resting contracts within 3 cents of the price, backing YES (for) and against YES (against).")
    data["note"] += (" hourly = last trade of each hour on a grid starting at hourly.start (Unix seconds, hour END times), "
                     "price in tenths of a cent (640 = 64 percent), carried forward through hours with no trade; "
                     "hourly.vol = thousands of contracts traded per race per hour, both sides combined. "
                     "ev_pulls = when the early vote tracker captured each day's numbers (Central).")
    data = {k: data[k] for k in ["source", "note", "pulled", "races", "daily", "live", "flips", "big", "taker", "book", "big_scanned_from", "hourly", "ev", "ev_pulls", "tx_turnout"] if k in data}

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("kalshi.json: %d candle rows merged, %d hourly points merged, %d big orders, %d flips, pulled %s" %
          (changed, hourly_rows, len(data["big"]), len(data["flips"]), data.get("pulled")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
