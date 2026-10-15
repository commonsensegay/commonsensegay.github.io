#!/usr/bin/env python3
"""Turn the Early Vote Ledger artifact HTML into the standalone page at early-vote/index.html.

Usage: python3 tools/build_early_vote.py <path-to-artifact-html>
Run from the repo root. Exits non-zero and writes nothing if the input doesn't look right.
"""
import json, os, re, sys

src = open(sys.argv[1], encoding="utf-8").read()
if "/*DATA-START*/" not in src or "SNAPSHOTS" not in src:
    sys.exit("input does not look like the Early Vote Ledger page")

m = re.match(r"\s*<!doctype html><html><head>.*?</head><body>\s*", src, re.S | re.I)
body = src[m.end():] if m else src
body = re.sub(r"\s*</body>\s*</html>\s*$", "", body, flags=re.I)

head = []
def grab(pat):
    global body
    mm = re.search(pat, body, re.S)
    if mm:
        head.append(mm.group(0).strip())
        body = body[:mm.start()] + body[mm.end():]
grab(r"<title>.*?</title>")
head = [h for h in head if not h.startswith("<title>")] + ["<title>2026 Early Vote Tracker by Party, Updated Daily | Common Sense Gay</title>"]
grab(r'<link rel="stylesheet"[^>]*>')
grab(r'<script src="https://cdnjs[^>]*fontawesome\.min\.js"[^>]*></script>')
grab(r'<script src="https://cdnjs[^>]*brands\.min\.js"[^>]*></script>')
grab(r"<style>.*?</style>")

URL = "https://commonsensegay.com/early-vote/"
TABS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker_tabs.html"), encoding="utf-8").read()
TOP = """<div class="votebar" id="votebar" role="region" aria-label="Early voting dates" hidden>
  <div class="vb-in"><span class="vb-star" aria-hidden="true">&#9733;</span><span class="vb-msg" aria-live="polite"></span><a class="vb-go" href="https://www.nass.org/can-i-vote/find-your-polling-place" rel="noopener">Find your polling place</a><a class="vb-all" href="/vote/">All states</a></div>
</div>
<div class="csg-top"><div class="in"><a class="home" href="/"><img src="/assets/logo.png" alt="" width="32" height="32">Common Sense Gay</a><nav aria-label="Main"><a href="/blog/">Blog</a><a href="/vote/">Where to vote</a><a class="hide-sm" href="/#follow">Follow</a></nav></div></div>
"""
out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Who has already voted in the 2026 midterm, by party, in every state. Updated every morning and measured against 2022 and 2024.">
<meta property="og:title" content="Common Sense Gay Early Vote Tracker">
<meta property="og:description" content="2026 midterm early vote by party, state by state, against the 2022 baseline. Receipts over rhetoric.">
<meta property="og:type" content="website">
<meta property="og:url" content="{URL}">
<link rel="canonical" href="{URL}">
<meta property="og:image" content="https://commonsensegay.com/assets/og-early-vote.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Common Sense Gay Early Vote Tracker 2026">
<meta property="og:site_name" content="Common Sense Gay">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@commonsensegay">
<meta name="twitter:title" content="Common Sense Gay Early Vote Tracker">
<meta name="twitter:description" content="2026 midterm early vote by party, state by state, against the 2022 baseline. Receipts over rhetoric.">
<meta name="twitter:image" content="https://commonsensegay.com/assets/og-early-vote.jpg">
<meta name="theme-color" content="#0c1e38">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<style>body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
<link rel="stylesheet" href="/assets/votebar.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&display=swap">
{chr(10).join(head)}
</head>
<body>
{TOP}{body.strip()}
{TABS}
<script src="/assets/voting.js"></script>
</body>
</html>
"""
os.makedirs("early-vote", exist_ok=True)
open("early-vote/index.html", "w", encoding="utf-8").write(out)
print(f"wrote early-vote/index.html ({len(out):,} bytes)")

# Headline numbers for the homepage: early-vote/latest.json
def snapshots(html):
    a = html.find("/*DATA-START*/"); b = html.find("/*DATA-END*/")
    js = html[a:b]
    js = js[js.find("["):js.rfind("]") + 1]
    js = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', js)
    js = re.sub(r',\s*([}\]])', r'\1', js)
    return json.loads(js)

def hard(snap, reg):
    r = d = o = n = 0
    for ab, v in snap["states"].items():
        if ab in reg and v[1] + v[2] > 0:
            r += v[1]; d += v[2]; o += v[3]; n += 1
    t = r + d + o
    return {"rep": r, "dem": d, "other": o, "total": t, "states": n,
            "rep_pct": round(r / t * 100, 1) if t else 0,
            "dem_pct": round(d / t * 100, 1) if t else 0,
            "other_pct": round(o / t * 100, 1) if t else 0,
            "margin": round((d - r) / t * 100, 1) if t else 0,
            "_m": (d - r) / t * 100 if t else 0}

try:
    reg = set(re.findall(r'"([A-Z]{2})"', re.search(r"const PARTY_REG=new Set\(\[(.*?)\]\)", src).group(1)))
    snaps = snapshots(src)
    cur = snaps[-1]
    h = hard(cur, reg)
    latest = {"date": cur["date"], "pulled": cur["pulled"],
              "all_ballots": sum(v[0] for v in cur["states"].values()),
              "states_reporting": sum(1 for v in cur["states"].values() if v[0] > 0),
              "hard": h}
    if len(snaps) <= 1:
        h.pop("_m", None)
    if len(snaps) > 1:
        p = hard(snaps[-2], reg)
        latest["prev_date"] = snaps[-2]["date"]
        latest["margin_change"] = round(h["_m"] - p["_m"], 1)
    h.pop("_m", None)
    open("early-vote/latest.json", "w").write(json.dumps(latest, indent=1))
    print("wrote early-vote/latest.json", latest["date"], h["dem_pct"], h["rep_pct"])
except Exception as e:
    print("warning: latest.json not updated:", e)
