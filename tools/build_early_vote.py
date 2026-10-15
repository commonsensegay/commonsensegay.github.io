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
# ---- Trend chart: add the raw Democratic ballot lead (firewall) on a second, right-hand axis
CHART_PATCHES = [
    ('const W=720,Hh=260,pl=60,pr=16,pt=16,pb=30;', 'const W=720,Hh=270,pl=60,pr=70,pt=30,pb=30;'),
    ('const X=i=>pl+(W-pl-pr)*i/(T.length-1),Y=v=>pt+(Hh-pt-pb)*(hi-v)/(hi-lo);',
     'const X=i=>pl+(W-pl-pr)*i/(T.length-1),Y=v=>pt+(Hh-pt-pb)*(hi-v)/(hi-lo);'
     'const fv=T.map(t=>t.f);let flo=Math.min(...fv),fhi=Math.max(...fv);const fsp=(fhi-flo)||1;fhi+=fsp*0.1;flo-=fsp*0.1;'
     'const YF=v=>pt+(Hh-pt-pb)*(v-flo)/(fhi-flo);const fk=v=>Math.abs(v)>=1e6?(v/1e6).toFixed(2)+"M":Math.round(v/1e3)+"K";'
     'const fline=`<polyline fill="none" stroke="#0c1e38" stroke-width="2.5" stroke-dasharray="6 4" points="${T.map((t,i)=>X(i).toFixed(1)+","+YF(t.f).toFixed(1)).join(" ")}"/>`+T.map((t,i)=>`<rect x="${X(i)-3.5}" y="${YF(t.f)-3.5}" width="7" height="7" fill="#0c1e38"/>`).join("");'
     'const faxis=Array.from({length:5},(_,k)=>flo+(fhi-flo)*k/4).map(v=>`<text x="${W-pr+8}" y="${YF(v)+4}" text-anchor="start" fill="#0c1e38">${fk(v)}</text>`).join("")+`<text x="${W-4}" y="${pt-14}" text-anchor="end" fill="#0c1e38" font-weight="700">Dem lead, ballots</text><text x="${pl}" y="${pt-14}" text-anchor="start" fill="var(--muted)" font-weight="700">Dem lead, points</text>`;'),
    ('segs+dots+lbl+`<g id="cursor"', 'segs+fline+faxis+dots+lbl+`<g id="cursor"'),
    ('<span><b style="background:var(--dem);opacity:.6"></b>Democrats gaining (line falling)</span></div>',
     '<span><b style="background:var(--dem);opacity:.6"></b>Democrats gaining (line falling)</span><span><b style="background:#0c1e38;height:3px;vertical-align:3px"></b>Dem lead in raw ballots, right axis (dashed)</span></div>'),
    ('Hover or tap a point for the shares that day.</p>',
     'Hover or tap a point for the shares that day. The dashed line is the same lead counted in raw ballots (the firewall), on the right-hand axis. Both axes run the same way: up is better for Republicans. When the solid line climbs while the dashed line drops, the Democratic lead is shrinking as a share but still growing in raw ballots because more people are voting.</p>'),
]
for _old, _new in CHART_PATCHES:
    if _old in body:
        body = body.replace(_old, _new, 1)
    else:
        print("warning: trend chart patch not applied:", _old[:50])

TABS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker_tabs.html"), encoding="utf-8").read()
TOP = """<div class="votebar" id="votebar" role="region" aria-label="Early voting dates" hidden>
  <div class="vb-in"><span class="vb-star" aria-hidden="true">&#9733;</span><span class="vb-msg" aria-live="polite"></span><a class="vb-go" href="https://www.nass.org/can-i-vote/find-your-polling-place" rel="noopener">Find your polling place</a><a class="vb-all" href="/vote/">All states</a></div>
</div>
<div class="csg-top"><div class="in"><a class="home" href="/"><img src="/assets/logo.png" alt="" width="32" height="32">Common Sense Gay</a><nav aria-label="Main"><a href="/blog/">Blog</a><a href="/vote/">Where to vote</a><a class="hide-sm" href="/#follow">Follow</a></nav></div></div>
"""
out = f"""<!doctype html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-LYH4ZTMX31"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', 'G-LYH4ZTMX31');
</script>
<script src="/assets/track.js" defer></script>
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
