#!/usr/bin/env python3
"""Static checks for the built public site. Does not deploy."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ORIGIN = "https://keywestshoreexcursions.com"

PAGES = [
    "/",
    "/can-you-walk-key-west-from-cruise-port",
    "/key-west-cruise-port-guide",
    "/duval-street-guide",
    "/one-day-in-key-west",
    "/best-key-west-shore-excursions",
    "/dry-tortugas-excursions",
    "/key-west-conch-train-tours",
    "/key-west-trolley-tours",
    "/key-west-sunset-sailing",
    "/key-west-family-excursions",
    "/southernmost-point-tours",
    "/hemingway-house-tours",
    "/key-west-snorkelling-tours",
    "/key-west-dolphin-watching-tours",
    "/key-west-faq",
]

BANNED = [
    "travelagency",
    "touristtrip",
    '"@type": "product"',
    "book now",
    "book this tour",
    "add to cart",
    "cdn.tailwindcss.com",
    "js/site.js",
    'id="page-content"',
    "data-content=",
    "partials/",
    "most walkable cruise ports in the us",
    "most walkable cruise ports in the united states",
    "5–15 minutes from either",
    "5-15 minutes from either",
    "the main pier",
    "60–90 min buffer",
    "60-90 min buffer",
    "key-west-cruise-port.png",
    "dry-tortugas.png",
    "hemingway-house.png",
    "key-west-dolphin.png",
    "key-west-snorkelling.png",
    "key-west-trolley.png",
    "hero-key-west.jpg",
    "walk-from-port.jpg",
]


def file_for(path: str) -> Path:
    return PUBLIC / ("index.html" if path == "/" else f"{path.strip('/')}.html")


def main() -> int:
    errors: list[str] = []
    if (PUBLIC / "content").exists() or (PUBLIC / "partials").exists():
        errors.append("public content or partials directory must not exist")

    texts = []
    for path in PAGES:
        target = file_for(path)
        if not target.exists():
            errors.append(f"missing built page {path}")
            continue
        html = target.read_text()
        texts.append(html)
        if "<h1>" not in html:
            errors.append(f"{path} missing H1")
        if path != "/" and 'rel="canonical"' not in html:
            errors.append(f"{path} missing canonical")
        canon = re.search(r'rel="canonical" href="([^"]+)"', html)
        if canon:
            href = canon.group(1)
            expected = ORIGIN + ("/" if path == "/" else path)
            if href != expected:
                errors.append(f"{path} canonical {href} != {expected}")
            if href.endswith(".html") or "www." in href or href.startswith("http://"):
                errors.append(f"{path} canonical is not HTTPS apex extensionless")
        if 'property="og:url"' in html:
            og = re.search(r'property="og:url" content="([^"]+)"', html)
            if og and og.group(1) != ORIGIN + ("/" if path == "/" else path):
                errors.append(f"{path} og:url mismatch")
        if "<script src=" in html:
            errors.append(f"{path} has a script src")
        for href in re.findall(r'href="(/[^"]*)"', html):
            if href.startswith("/css/") or href.startswith("/favicon") or href.startswith("/images/"):
                continue
            if href.endswith(".html"):
                errors.append(f"{path} links to html twin {href}")
            bare = href.split("#")[0]
            if bare in {"/", ""}:
                continue
            if bare not in PAGES and not bare.startswith("/#"):
                errors.append(f"{path} unknown internal link {href}")

    blob = "\n".join(texts).lower()
    for phrase in BANNED:
        if phrase in blob:
            errors.append(f"banned phrase: {phrase}")
    if re.search(r"\$\d", blob):
        errors.append("price-like amount found")

    not_found = (PUBLIC / "404.html").read_text().lower()
    if "noindex" not in not_found:
        errors.append("404 missing noindex")
    if "canonical" in not_found:
        errors.append("404 must not have a canonical")
    if "that page is not on this guide" not in not_found:
        errors.append("404 body missing")

    sitemap = (PUBLIC / "sitemap.xml").read_text()
    if ".html" in sitemap:
        errors.append("sitemap lists .html")
    if re.search(r"<loc>https://www\.", sitemap) or re.search(r"<loc>http://", sitemap):
        errors.append("sitemap lists www or http")
    for path in PAGES:
        loc = ORIGIN + ("/" if path == "/" else path)
        if loc not in sitemap:
            errors.append(f"sitemap missing {loc}")

    robots = (PUBLIC / "robots.txt").read_text()
    if f"{ORIGIN}/sitemap.xml" not in robots:
        errors.append("robots missing canonical sitemap")
    if "www." in robots:
        errors.append("robots points at www")

    if errors:
        print("CHECK FAILED")
        for err in errors:
            print(" -", err)
        return 1
    print(f"CHECK OK ({len(PAGES)} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
