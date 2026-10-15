#!/usr/bin/env python3
"""Build the blog from posts/*.md.

Each post is a Markdown file named YYYY-MM-DD-slug.md that starts with a small header:

    ---
    title: The headline
    date: 2026-10-15
    summary: One line for share cards and the list page (optional)
    ---
    Body in Markdown...

Writes blog/index.html, blog/<slug>/index.html for every post, and blog/posts.json
(newest first) which the homepage reads for its "Daily take" section.
Usage: python3 tools/build_blog.py
"""
import datetime, html, json, os, re, sys
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "posts")
OUT = os.path.join(ROOT, "blog")
SITE = "https://commonsensegay.com"
OG = SITE + "/assets/og-home-v3.jpg"


def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        sys.exit(f"{path}: missing --- header")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    body = m.group(2).strip()
    name = os.path.basename(path)[:-3]
    dm = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)$", name)
    if not dm:
        sys.exit(f"{path}: file name must be YYYY-MM-DD-slug.md")
    date = meta.get("date") or dm.group(1)
    datetime.date.fromisoformat(date)
    if not meta.get("title"):
        sys.exit(f"{path}: needs a title")
    body_html = markdown.markdown(body, extensions=["extra", "sane_lists"])
    body_html = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body_html)
    text = re.sub(r"</(p|li|h[1-6]|blockquote)>|<br\s*/?>", " ", body_html)
    text = re.sub(r"<[^>]+>", "", text)
    fp = re.search(r"<p>(.*?)</p>", body_html, re.S)
    first = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fp.group(1)))).strip() if fp else ""
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    base = first or text
    summary = meta.get("summary") or (base[:200].rsplit(" ", 1)[0] + "…" if len(base) > 200 else base)
    words = len(text.split())
    return {
        "slug": dm.group(2), "date": date, "title": meta["title"], "summary": summary,
        "html": body_html, "minutes": max(1, round(words / 230)),
        "url": f"/blog/{dm.group(2)}/", "time": meta.get("time", "00:00"),
    }


def nice(d):
    x = datetime.date.fromisoformat(d)
    return x.strftime("%A, %B ") + str(x.day) + x.strftime(", %Y")


HEAD = """<!doctype html>
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
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="{ogtype}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="Common Sense Gay">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@commonsensegay">
<meta name="twitter:image" content="{og}">
<meta name="theme-color" content="#0d1f3a">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="Common Sense Gay" href="/blog/feed.xml">
<link rel="stylesheet" href="/assets/votebar.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;700&family=Archivo+Narrow:wght@600;700&display=swap">
<style>
:root{{--navy:#0d1f3a;--night:#081528;--cream:#efe3c4;--paper:#f6eedb;--sun:#f0a02a;--red:#b8362e;--mist:#a9b6cb;--ink:#16202e;--ink-soft:#57524a;--rule:#d9c9a2;
--display:"Anton",Impact,"Arial Narrow",sans-serif;--body:"Archivo",system-ui,sans-serif;--narrow:"Archivo Narrow","Arial Narrow",sans-serif}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:18px;line-height:1.6;-webkit-font-smoothing:antialiased}}
img{{max-width:100%;height:auto;display:block}}
a{{color:var(--navy)}}
a:focus-visible{{outline:3px solid var(--sun);outline-offset:3px}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 24px}}
.narrow{{max-width:740px}}
@media (max-width:600px){{.wrap{{padding:0 16px}}}}
.bar{{background:var(--night)}}
.bar .wrap{{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:16px;padding-bottom:16px}}
.mark{{display:flex;align-items:center;gap:12px;text-decoration:none;font-family:var(--narrow);font-weight:700;font-size:20px;color:var(--cream)}}
.mark img{{width:44px;height:44px}}
.nav{{display:flex;gap:22px;align-items:center;font-family:var(--narrow);font-weight:600;font-size:17px}}
.nav a{{text-decoration:none;color:var(--mist);white-space:nowrap}}
.nav a:hover,.nav a[aria-current]{{color:var(--cream)}}
.nav a.ev{{background:#f5a21f;color:#0c1e38;padding:4px 12px;border-radius:999px}}
@media (max-width:700px){{.nav a:not(.keep){{display:none}}}}
.top{{background:var(--navy);color:var(--cream);padding:52px 0 56px;border-bottom:6px solid var(--red)}}
.kick{{font-family:var(--narrow);font-weight:700;text-transform:uppercase;letter-spacing:.14em;font-size:15px;color:var(--sun);margin:0 0 12px}}
.kick a{{color:var(--sun);text-decoration:none}}
h1{{font-family:var(--display);font-weight:400;text-transform:uppercase;font-size:clamp(38px,5.4vw,68px);line-height:1.02;margin:0 0 16px;letter-spacing:.01em}}
.lede{{font-size:clamp(18px,2vw,21px);color:#d8dfeb;max-width:58ch;margin:0}}
.meta{{font-family:var(--narrow);font-weight:600;font-size:17px;color:var(--mist);margin:0}}
main{{padding:48px 0 64px}}
.post{{font-size:20px;line-height:1.7}}
.post p{{margin:0 0 22px}}
.post h2,.post h3{{font-family:var(--display);font-weight:400;text-transform:uppercase;color:var(--navy);line-height:1.05;margin:36px 0 14px}}
.post h2{{font-size:36px}}.post h3{{font-size:28px}}
.post blockquote{{margin:0 0 22px;padding:6px 0 6px 20px;border-left:5px solid var(--sun);color:#3d3a33;font-style:italic}}
.post ul,.post ol{{margin:0 0 22px;padding-left:26px}}
.post li{{margin-bottom:8px}}
.post a{{font-weight:700}}
.post img{{border-radius:6px;margin:6px 0 22px}}
.share{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;border-top:2px solid var(--rule);margin-top:34px;padding-top:22px}}
.share b{{font-family:var(--narrow);font-size:18px;margin-right:6px}}
.btn{{display:inline-flex;align-items:center;gap:8px;font-family:var(--narrow);font-weight:700;font-size:17px;text-decoration:none;padding:10px 18px;border-radius:999px;background:var(--navy);color:var(--cream);border:0;cursor:pointer}}
.btn.fb{{background:var(--sun);color:var(--night)}}
.btn.alt{{background:transparent;color:var(--navy);border:2px solid var(--navy)}}
.list{{list-style:none;margin:0;padding:0}}
.list li{{border-bottom:2px solid var(--rule);padding:26px 0}}
.list li:first-child{{padding-top:0}}
.list .d{{font-family:var(--narrow);font-weight:700;font-size:15px;text-transform:uppercase;letter-spacing:.1em;color:var(--red);margin:0 0 6px}}
.list h2{{font-family:var(--display);font-weight:400;text-transform:uppercase;font-size:clamp(28px,3.6vw,40px);line-height:1.05;margin:0 0 8px}}
.list h2 a{{text-decoration:none;color:var(--navy)}}
.list h2 a:hover{{color:var(--red)}}
.list p{{margin:0;color:var(--ink-soft)}}
.empty{{background:#fff;border:2px dashed var(--rule);border-radius:8px;padding:30px;text-align:center;color:var(--ink-soft)}}
.nav2{{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:30px;font-family:var(--narrow);font-weight:700;font-size:18px}}
.nav2 a{{text-decoration:none}}
.cta{{background:var(--navy);color:var(--cream);padding:40px 0}}
.cta .wrap{{display:flex;flex-wrap:wrap;gap:18px;align-items:center;justify-content:space-between}}
.cta p{{margin:0;font-size:19px;max-width:52ch}}
.cta strong{{font-family:var(--display);font-weight:400;text-transform:uppercase;font-size:30px;display:block;color:var(--sun);margin-bottom:4px}}
.cta .acts{{display:flex;gap:10px;flex-wrap:wrap}}
.sub{{background:#fff6e3;border-top:2px solid var(--rule);padding:44px 0}}.sub h2{{font-family:var(--display);font-weight:400;text-transform:uppercase;font-size:clamp(30px,4vw,44px);color:var(--navy);margin:0 0 10px;line-height:1.05}}.sub p{{margin:0 0 18px;color:var(--ink-soft)}}.btn.sub-btn{{background:var(--red);color:#fff;font-size:19px;padding:13px 24px}}
footer{{background:var(--night);color:#7d8ca5;padding:30px 0;font-size:14px;border-top:6px solid var(--red)}}
</style>
</head>
<body>
<div class="votebar" id="votebar" role="region" aria-label="Early voting dates" hidden>
  <div class="vb-in"><span class="vb-star" aria-hidden="true">★</span><span class="vb-msg" aria-live="polite"></span><a class="vb-go" href="https://www.nass.org/can-i-vote/find-your-polling-place" rel="noopener">Find your polling place</a><a class="vb-all" href="/vote/">All states</a></div>
</div>
<header class="bar">
  <div class="wrap">
    <a class="mark" href="/"><img src="/assets/logo.png" alt="" width="44" height="44">Common Sense Gay</a>
    <nav class="nav" aria-label="Main">
      <a class="keep" href="/blog/"{blogcur}>Blog</a>
      <a class="keep ev" href="/early-vote/">Tracker</a>
      <a href="/vote/">Where to vote</a>
      <a href="/#follow">Follow</a>
    </nav>
  </div>
</header>
"""

FOOT = """<section class="sub"><div class="wrap narrow"><p class="kick" style="color:var(--red)">Out &amp; Right, the newsletter</p><h2>Get the daily take in your inbox</h2><p>Out of the closet, right of center. The research the headlines skip, with the receipts, delivered free by email.</p><a class="btn sub-btn" href="https://commonsensegay.substack.com/subscribe" rel="noopener">Subscribe free on Substack</a></div></section>
<section class="cta">
  <div class="wrap">
    <p><strong>Follow along</strong>New takes every day. Facebook is home base, TikTok is where the receipts go viral.</p>
    <div class="acts"><a class="btn fb" href="https://www.facebook.com/Commonsensegay/" rel="noopener">Follow on Facebook</a><a class="btn alt" style="color:var(--cream);border-color:var(--cream)" href="https://www.tiktok.com/@commonsensegay" rel="noopener">Follow on TikTok</a></div>
  </div>
</section>
<footer><div class="wrap">Reality over ideology. Data over narratives. I'm your Common Sense Gay.</div></footer>
<script src="/assets/voting.js" defer></script>
</body>
</html>
"""


def page(**kw):
    kw.setdefault("blogcur", "")
    return HEAD.format(og=OG, **kw)


def main():
    os.makedirs(POSTS, exist_ok=True)
    files = sorted(f for f in os.listdir(POSTS) if f.endswith(".md"))
    posts = [parse(os.path.join(POSTS, f)) for f in files]
    posts.sort(key=lambda p: (p["date"], p["time"], p["slug"]), reverse=True)
    slugs = [p["slug"] for p in posts]
    if len(set(slugs)) != len(slugs):
        sys.exit("two posts share a slug")
    os.makedirs(OUT, exist_ok=True)
    keep = set(slugs)
    for d in os.listdir(OUT):
        full = os.path.join(OUT, d)
        if os.path.isdir(full) and d not in keep and os.path.exists(os.path.join(full, "index.html")):
            os.remove(os.path.join(full, "index.html")); os.rmdir(full)

    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        url = SITE + p["url"]
        e = html.escape
        share = (f'<div class="share"><b>Share this</b>'
                 f'<a class="btn fb" href="https://www.facebook.com/sharer/sharer.php?u={url}" target="_blank" rel="noopener">Facebook</a>'
                 f'<a class="btn" href="https://x.com/intent/post?url={url}&text={e(p["title"])}" target="_blank" rel="noopener">X</a>'
                 f'<button class="btn alt" type="button" onclick="navigator.clipboard&&navigator.clipboard.writeText(\'{url}\').then(()=>{{this.textContent=\'Link copied\'}})">Copy link</button></div>')
        nav2 = '<div class="nav2">' + (f'<a href="{older["url"]}">← {e(older["title"])}</a>' if older else '<span></span>') + \
               (f'<a href="{newer["url"]}">{e(newer["title"])} →</a>' if newer else '<a href="/blog/">All posts →</a>') + '</div>'
        out = page(title=f'{e(p["title"])} | Common Sense Gay', desc=e(p["summary"]), url=url,
                   ogtitle=e(p["title"]), ogtype="article")
        out += (f'<div class="top"><div class="wrap narrow"><p class="kick"><a href="/blog/">The Daily Take</a></p>'
                f'<h1>{e(p["title"])}</h1><p class="meta">{nice(p["date"])} · {p["minutes"]} min read</p></div></div>'
                f'<main><div class="wrap narrow"><article class="post">{p["html"]}</article>{share}{nav2}</div></main>')
        out += FOOT
        ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": p["summary"],
              "datePublished": p["date"], "dateModified": p["date"], "mainEntityOfPage": url, "image": OG,
              "author": {"@type": "Organization", "name": "Common Sense Gay", "url": SITE + "/"},
              "publisher": {"@type": "Organization", "name": "Common Sense Gay", "logo": {"@type": "ImageObject", "url": SITE + "/assets/logo.png"}}}
        out = out.replace("</head>", '<script type="application/ld+json">' + json.dumps(ld).replace("</", "<\\/") + "</script>\n</head>", 1)
        os.makedirs(os.path.join(OUT, p["slug"]), exist_ok=True)
        open(os.path.join(OUT, p["slug"], "index.html"), "w", encoding="utf-8").write(out)

    e = html.escape
    items = "".join(f'<li><p class="d">{nice(p["date"])}</p><h2><a href="{p["url"]}">{e(p["title"])}</a></h2><p>{e(p["summary"])}</p></li>' for p in posts)
    body = f'<ul class="list">{items}</ul>' if posts else '<div class="empty">The first post is on its way. Check back soon.</div>'
    out = page(title="The Daily Take | Common Sense Gay",
               desc="My thoughts for the day. Short, blunt takes on the news, with the receipts to back them up.",
               url=SITE + "/blog/", ogtitle="The Daily Take from Common Sense Gay", ogtype="website", blogcur=' aria-current="page"')
    out += ('<div class="top"><div class="wrap narrow"><p class="kick">Blog</p><h1>The Daily Take</h1>'
            '<p class="lede">My thoughts for the day. Short, blunt takes on the news, with the receipts to back them up.</p></div></div>'
            f'<main><div class="wrap narrow">{body}</div></main>') + FOOT
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(out)

    json.dump([{k: p[k] for k in ("title", "date", "summary", "url", "minutes")} for p in posts],
              open(os.path.join(OUT, "posts.json"), "w", encoding="utf-8"), indent=1)

    # RSS
    rss = ['<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Common Sense Gay: The Daily Take</title>'
           f'<link>{SITE}/blog/</link><description>My thoughts for the day.</description>']
    for p in posts[:30]:
        d = datetime.datetime.fromisoformat(p["date"] + "T12:00:00").strftime("%a, %d %b %Y 12:00:00 -0500")
        rss.append(f'<item><title>{e(p["title"])}</title><link>{SITE}{p["url"]}</link><guid>{SITE}{p["url"]}</guid>'
                   f'<pubDate>{d}</pubDate><description>{e(p["summary"])}</description></item>')
    rss.append("</channel></rss>")
    open(os.path.join(OUT, "feed.xml"), "w", encoding="utf-8").write("".join(rss))
    # sitemap + robots for the whole site
    today = datetime.date.today().isoformat()
    newest = posts[0]["date"] if posts else today
    urls = [("/", today, "daily", "1.0"), ("/early-vote/", today, "daily", "0.9"), ("/vote/", today, "weekly", "0.8"),
            ("/blog/", newest, "daily", "0.8")] + [(p["url"], p["date"], "monthly", "0.7") for p in posts]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, d, f, pr in urls:
        sm.append(f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod><changefreq>{f}</changefreq><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nAllow: /\nDisallow: /tools/\nDisallow: /posts/\n\nSitemap: " + SITE + "/sitemap.xml\n")
    print(f"built {len(posts)} post(s)")


if __name__ == "__main__":
    main()
