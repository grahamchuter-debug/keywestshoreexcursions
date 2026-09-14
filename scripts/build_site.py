#!/usr/bin/env python3
"""Build server-visible Key West pages. Fragments stay in scripts/content and are not published."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://keywestshoreexcursions.com"
UPDATED = "2026-09-14"
PUBLIC = ROOT / "public"
CONTENT = Path(__file__).resolve().parent / "content"
NAV = [
    ("/can-you-walk-key-west-from-cruise-port", "Walk from port"),
    ("/key-west-cruise-port-guide", "Port guide"),
    ("/one-day-in-key-west", "One day"),
    ("/duval-street-guide", "Duval Street"),
    ("/best-key-west-shore-excursions", "Day ideas"),
    ("/key-west-faq", "FAQ"),
]


def load_pages() -> list[dict]:
    pages = json.loads((Path(__file__).resolve().parent / "pages.json").read_text())
    for page in pages:
        slug = page["path"]
        name = "home.html" if slug == "/" else f"{slug.strip('/')}.html"
        page["body"] = (CONTENT / name).read_text()
        if f"<h1>{page['h1']}</h1>" not in page["body"] and f">{page['h1']}</h1>" not in page["body"]:
            if "<h1" in page["body"]:
                raise SystemExit(f"{name} contains an extra H1")
    return pages


def url_for(path: str) -> str:
    if path == "/":
        return ORIGIN + "/"
    return ORIGIN + path


def crumbs_html(page: dict) -> str:
    if page["path"] == "/":
        return ""
    items = ['<a href="/">Home</a>']
    for label, href in page.get("trail", []):
        items.append(f'<a href="{href}">{html.escape(label)}</a>')
    items.append(html.escape(page["crumb"]))
    return f'<p class="crumbs">{" · ".join(items)}</p>'


def faq_html(page: dict) -> str:
    faqs = page.get("faq") or []
    if not faqs:
        return ""
    blocks = []
    for item in faqs:
        blocks.append(f"<h3>{html.escape(item['q'])}</h3>\n<p>{html.escape(item['a'])}</p>")
    return "<h2>Questions about this page</h2>\n<div class=\"faq\">\n" + "\n".join(blocks) + "\n</div>"


def related_html(page: dict) -> str:
    related = page.get("related") or []
    if not related:
        return ""
    cards = []
    for item in related:
        cards.append(
            f'<a href="{item["href"]}"><strong>{html.escape(item["title"])}</strong>'
            f'<span>{html.escape(item["text"])}</span></a>'
        )
    return "<h2>Related planning pages</h2>\n<div class=\"related\">\n" + "\n".join(cards) + "\n</div>"


def actions_html(page: dict) -> str:
    actions = page.get("actions") or []
    if not actions:
        return ""
    bits = []
    for action in actions:
        cls = "btn-quiet" if action.get("quiet") else "btn"
        bits.append(f'<a class="{cls}" href="{action["href"]}">{html.escape(action["label"])}</a>')
    return '<div class="actions">' + "".join(bits) + "</div>"


def schema(page: dict) -> str:
    page_url = url_for(page["path"])
    graph = []
    if page["path"] == "/":
        graph.append({
            "@type": "WebSite",
            "@id": ORIGIN + "/#website",
            "url": ORIGIN + "/",
            "name": "Key West Shore Excursions",
            "description": "Independent cruise-day planning guides for Key West, Florida. Not a tour operator.",
        })
    graph.append({
        "@type": "Article",
        "headline": page["h1"],
        "description": page["description"],
        "dateModified": UPDATED,
        "mainEntityOfPage": page_url,
        "author": {"@type": "Organization", "name": "Key West Shore Excursions", "url": ORIGIN + "/"},
        "publisher": {"@type": "Organization", "name": "Key West Shore Excursions", "url": ORIGIN + "/"},
    })
    if page["path"] != "/":
        elements = [{
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": ORIGIN + "/",
        }]
        position = 2
        for label, href in page.get("trail", []):
            elements.append({
                "@type": "ListItem",
                "position": position,
                "name": label,
                "item": url_for(href),
            })
            position += 1
        elements.append({
            "@type": "ListItem",
            "position": position,
            "name": page["crumb"],
            "item": page_url,
        })
        graph.append({"@type": "BreadcrumbList", "itemListElement": elements})
    if page.get("faq"):
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in page["faq"]
            ],
        })
    payload = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(payload, ensure_ascii=False)


def nav_html(path: str) -> str:
    links = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == path else ""
        links.append(f'<a href="{href}"{current}>{label}</a>')
    return "\n        ".join(links)


def mark_svg() -> str:
    return (
        '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true">'
        '<rect width="32" height="32" rx="8" fill="#0b4f5c"/>'
        '<path d="M4 20c4-1 7-6 10-6s4 4 7 4 4-3 7-5" fill="none" stroke="#eef6f7" stroke-width="1.6" stroke-linecap="round"/>'
        '<circle cx="23" cy="11" r="2" fill="#e8a04a"/>'
        "</svg>"
    )


def footer_html(pages: list[dict]) -> str:
    start = [
        ("/can-you-walk-key-west-from-cruise-port", "Walk from the cruise port"),
        ("/key-west-cruise-port-guide", "Cruise port guide"),
        ("/one-day-in-key-west", "One day in Key West"),
        ("/key-west-faq", "FAQ"),
    ]
    topics = [(page["path"], page["crumb"]) for page in pages if page["path"] != "/"]

    def lis(items):
        return "\n".join(f'<li><a href="{href}">{html.escape(label)}</a></li>' for href, label in items)

    return f"""<footer class="site-footer">
    <div class="wrap foot-grid">
      <div>
        <h2>Key West Shore Excursions</h2>
        <p>Editorial guides for cruise passengers calling at Key West. We explain walkability, docking context and day shapes. We do not sell tours, take payment, or publish availability.</p>
      </div>
      <div>
        <h2>Start here</h2>
        <ul>
          {lis(start)}
        </ul>
      </div>
      <div>
        <h2>Topics</h2>
        <ul>
          {lis(topics)}
        </ul>
      </div>
    </div>
    <div class="wrap fine">Independent planning guide. Not affiliated with a cruise line. Not a booking site.</div>
  </footer>"""


def render(page: dict, pages: list[dict]) -> str:
    title = html.escape(page["title"])
    description = html.escape(page["description"])
    canonical = url_for(page["path"])
    robots = "noindex, follow" if page.get("noindex") else "index, follow"
    canonical_tag = "" if page.get("noindex") else f'  <link rel="canonical" href="{canonical}">\n'
    og = "" if page.get("noindex") else f"""  <meta property="og:type" content="article">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
"""
    ld = "" if page.get("noindex") else f'  <script type="application/ld+json">{schema(page)}</script>\n'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
{canonical_tag}  <meta name="robots" content="{robots}">
{og}  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/site.css">
{ld}</head>
<body>
  <a class="skip" href="#content">Skip to content</a>
  <header class="site-header">
    <div class="header-bar wrap">
      <a class="brand" href="/">{mark_svg()}<span><strong>Key West Shore Excursions</strong><span>Cruise-day planning</span></span></a>
      <input class="nav-toggle" type="checkbox" id="nav-toggle">
      <label class="nav-btn" for="nav-toggle">Menu</label>
      <nav class="site-nav" aria-label="Primary">
        {nav_html(page["path"])}
      </nav>
    </div>
  </header>
  <main id="content">
    <article class="wrap">
      {crumbs_html(page)}
      <header class="hero">
        <p class="eyebrow">{html.escape(page["eyebrow"])}</p>
        <h1>{html.escape(page["h1"])}</h1>
        <p class="lede">{html.escape(page["lede"])}</p>
        {actions_html(page)}
      </header>
      {page["body"]}
      {related_html(page)}
      {faq_html(page)}
      <p class="updated">Independent planning guide. Updated {UPDATED}. Not a booking site.</p>
    </article>
  </main>
  {footer_html(pages)}
</body>
</html>
"""


def render_404() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page not found | Key West Shore Excursions</title>
  <meta name="robots" content="noindex, follow">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/css/site.css">
</head>
<body>
  <header class="site-header">
    <div class="header-bar wrap">
      <a class="brand" href="/">{mark_svg()}<span><strong>Key West Shore Excursions</strong><span>Cruise-day planning</span></span></a>
    </div>
  </header>
  <main id="content" class="wrap prose section">
    <p class="eyebrow">404</p>
    <h1>That page is not on this guide</h1>
    <p>The address does not match a Key West planning page. It has not been sent to the homepage, and it is not a substitute for one.</p>
    <div class="actions">
      <a class="btn" href="/">Homepage</a>
      <a class="btn-quiet" href="/can-you-walk-key-west-from-cruise-port">Walk from the cruise port</a>
      <a class="btn-quiet" href="/key-west-cruise-port-guide">Read the port guide</a>
    </div>
  </main>
</body>
</html>
"""


def sitemap(pages: list[dict]) -> str:
    locs = "\n".join(
        f"  <url><loc>{url_for(page['path'])}</loc><lastmod>{UPDATED}</lastmod></url>"
        for page in pages
        if not page.get("noindex")
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{locs}
</urlset>
"""


def main() -> None:
    pages = load_pages()
    known = {page["path"] for page in pages}
    for page in pages:
        for item in page.get("related", []):
            if item["href"] not in known:
                raise SystemExit(f"Unknown related href {item['href']} on {page['path']}")
        for action in page.get("actions", []):
            href = action["href"]
            if href.startswith("#"):
                continue
            if href not in known:
                raise SystemExit(f"Unknown action href {href} on {page['path']}")
    PUBLIC.mkdir(exist_ok=True)
    (PUBLIC / "css").mkdir(exist_ok=True)
    for page in pages:
        filename = "index.html" if page["path"] == "/" else f"{page['path'].strip('/')}.html"
        (PUBLIC / filename).write_text(render(page, pages))
    (PUBLIC / "404.html").write_text(render_404())
    (PUBLIC / "sitemap.xml").write_text(sitemap(pages))
    (PUBLIC / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}/sitemap.xml\n"
    )
    print(f"Built {len(pages)} pages plus 404")


if __name__ == "__main__":
    main()
