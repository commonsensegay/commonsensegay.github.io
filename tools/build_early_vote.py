#!/usr/bin/env python3
"""Turn the Early Vote Ledger artifact HTML into the standalone page at early-vote/index.html.

Usage: python3 tools/build_early_vote.py <path-to-artifact-html>
Run from the repo root. Exits non-zero and writes nothing if the input doesn't look right.
"""
import os, re, sys

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
grab(r'<link rel="stylesheet"[^>]*>')
grab(r'<script src="https://cdnjs[^>]*fontawesome\.min\.js"[^>]*></script>')
grab(r'<script src="https://cdnjs[^>]*brands\.min\.js"[^>]*></script>')
grab(r"<style>.*?</style>")

URL = "https://commonsensegay.com/early-vote/"
out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Common Sense Gay's 2026 midterm early vote tracker. Daily party-registration counts by state, compared against the 2022 final numbers.">
<meta property="og:title" content="Common Sense Gay Early Vote Tracker">
<meta property="og:description" content="2026 midterm early vote by party, state by state, against the 2022 baseline. Receipts over rhetoric.">
<meta property="og:type" content="website">
<meta property="og:url" content="{URL}">
<link rel="canonical" href="{URL}">
<style>body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{chr(10).join(head)}
</head>
<body>
{body.strip()}
</body>
</html>
"""
os.makedirs("early-vote", exist_ok=True)
open("early-vote/index.html", "w", encoding="utf-8").write(out)
print(f"wrote early-vote/index.html ({len(out):,} bytes)")
