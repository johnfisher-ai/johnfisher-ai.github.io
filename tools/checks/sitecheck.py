#!/usr/bin/env python3
"""Checks the rendered site in docs/ before it is published.

- Every internal link and #anchor resolves. Links to John's other sites on the same host are other
  repositories, so they count as external and are checked at release with the W3C Link Checker.
- Every page has lang="en", a title ending "AI+ by John Fisher", and the disclosure in its footer.
- Every article and guide page carries a title of 70 characters or fewer, a teaser of 160 or fewer,
  a preview image, a license ("Reuse") and, for articles, a "Last checked" date.

Usage: python3 sitecheck.py docs
"""
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE_URL = "https://johnfisher-ai.github.io"
DISCLOSURE = ("John Fisher works for Salesforce. The views here are his own, not Salesforce's, and are drawn "
              "from public information; this site is not affiliated with or endorsed by Salesforce. "
              "Product names are trademarks of their owners.")

root = Path(sys.argv[1] if len(sys.argv) > 1 else "docs").resolve()
top_level = {p.name for p in root.iterdir()}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.meta = [], set(), {}
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key:
                self.meta[key] = a.get("content", "")
        if tag == "html":
            self.meta["lang"] = a.get("lang", "")
        for k in ("href", "src"):
            if a.get(k) and not (tag == "link" and a.get("rel") == "canonical") and not (tag == "meta"):
                self.links.append(a[k])

    def handle_data(self, data):
        self.text.append(data)


def target(page: Path, url: str):
    if url.startswith(SITE_URL):
        url = url[len(SITE_URL):] or "/"
    u = urlsplit(url)
    if u.scheme or u.netloc:
        return None, None
    path = unquote(u.path)
    if path.startswith("/"):
        first = path.strip("/").split("/")[0]
        if first and first not in top_level:
            return None, None  # another repository's site on the same host
        t = root / path.lstrip("/")
    elif path == "":
        t = page
    else:
        t = page.parent / path
    t = t.resolve()
    if t.is_dir() or path.endswith("/"):
        t = t / "index.html"
    return t, u.fragment


pages = {}
for f in sorted(root.rglob("*.html")):
    if "site_libs" in f.parts:
        continue
    p = Page()
    s = f.read_text(encoding="utf-8")
    p.feed(s)
    p.raw = s
    pages[f] = p

problems = []
checked = 0
for f, p in pages.items():
    rel = f.relative_to(root).as_posix()
    for url in p.links:
        if url.startswith(("mailto:", "javascript:", "data:")):
            continue
        t, frag = target(f, url)
        if t is None:
            continue
        checked += 1
        if not t.exists():
            problems.append(f"{rel}: broken link {url}")
        elif frag and t.suffix == ".html" and not frag.startswith("category="):
            ids = pages[t].ids if t in pages else set()
            if frag not in ids:
                problems.append(f"{rel}: missing anchor {url}")

    if p.meta.get("lang") != "en":
        problems.append(f"{rel}: html lang is not en")
    m = re.search(r"<title>(.*?)</title>", p.raw, re.S)
    title = html.unescape(m.group(1)) if m else ""
    if not title.endswith("AI+ by John Fisher"):
        problems.append(f"{rel}: title does not end with the site name: {title!r}")
    footer = re.search(r'<footer class="footer">(.*?)</footer>', p.raw, re.S)
    footer_text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", footer.group(1)))) if footer else ""
    footer_text = footer_text.replace("\u2019", "'").replace(" ;", ";").replace(" .", ".")
    if DISCLOSURE not in footer_text:
        problems.append(f"{rel}: disclosure missing from footer")

    parts = f.relative_to(root).parts
    if len(parts) == 3 and parts[0] in ("articles", "guides") and parts[2] == "index.html":
        og_title = p.meta.get("og:title", "")
        desc = p.meta.get("description", "")
        if len(og_title) > 70:
            problems.append(f"{rel}: title is {len(og_title)} characters (70 at most)")
        if not desc or len(desc) > 160:
            problems.append(f"{rel}: teaser is {len(desc)} characters (1 to 160)")
        if not p.meta.get("og:image"):
            problems.append(f"{rel}: no preview image")
        if 'id="quarto-reuse"' not in p.raw:
            problems.append(f"{rel}: no license (Reuse)")
        if parts[0] == "articles" and 'class="date-modified"' not in p.raw:
            problems.append(f"{rel}: no Last checked date")

for line in problems:
    print(line)
print(f"site check: {len(pages)} pages, {checked} internal links, {len(problems)} problems")
sys.exit(1 if problems else 0)
