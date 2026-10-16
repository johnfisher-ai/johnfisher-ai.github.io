#!/usr/bin/env python3
"""Post-render fixes for AI+. Quarto runs this after every render (project.post-render in _quarto.yml).

Quarto writes the site into docs/. A piece marked `draft: true` waits for the day of its first post. With
draft-mode set to unlinked, Quarto renders it at its own address but leaves it out of listings, feeds and the
sitemap, and shows a Draft banner at the top. This script marks each draft noindex and keeps it out of the
search index (with draft-mode set to gone, it removes the empty pages Quarto writes instead). It then makes
these changes:

1. Titles: "Title · AI+ by John Fisher" in <title>, and the bare title in og:title and twitter:title,
   so link previews show the article's own title.
2. Addresses: folder addresses (/articles/<slug>/) instead of .../index.html in links, the sitemap
   and the search index; rel=canonical, og:url and og:type on every page.
3. Markup in Quarto 1.10.19's templates that fails the HTML validator or axe.
4. Reading time: worked out once per article or guide from its rendered text, then shown on the
   page and on every card that links to it, so the two always agree.
5. Category chips on an article or guide page link to the Articles or Guides & Labs filter.
6. Search: marks each page's main content for Pagefind, then builds the search index in docs/pagefind/.

Every change is idempotent: running the script twice changes nothing the second time.
Python standard library, plus Pagefind from tools/package.json.
"""
import html
import json
import math
import os
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

SITE = "AI+ by John Fisher"
SITE_URL = "https://johnfisher-ai.github.io"
OUT = Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "docs"))
WPM = 200  # words a minute, the rate Quarto uses for its own listing reading times
SECTIONS = ("articles", "guides")


def page_address(f: Path) -> str:
    """docs/articles/x/index.html -> /articles/x/ ; docs/about/index.html -> /about/ ; docs/index.html -> /"""
    rel = f.relative_to(OUT).as_posix()
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")]
    return "/" + rel


def is_item_page(f: Path) -> bool:
    """An article or guide page: docs/articles/<slug>/index.html, not the listing page itself."""
    parts = f.relative_to(OUT).parts
    return len(parts) == 3 and parts[0] in SECTIONS and parts[2] == "index.html"


def folder_href(url: str) -> str:
    """Drop a trailing index.html from an internal link, keeping any #fragment or ?query."""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url) or url.startswith("//"):
        return url  # another scheme or host
    new = re.sub(r"(^|/)index\.html(?=$|[#?])", r"\1", url)
    if new != url and (new == "" or new[0] in "#?"):
        new = "./" + new
    return new


class MainText(HTMLParser):
    """Collects the words of an article body: <main>, without the title block, the appendix
    (endnotes, license) or the call-to-action box."""

    SKIP_IDS = {"title-block-header", "quarto-appendix"}
    SKIP_CLASSES = {"cta"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_main = 0
        self.skip = 0
        self.words = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        a = dict(attrs)
        if tag == "main":
            self.in_main += 1
        if self.skip:
            self.skip += 1
            return
        classes = (a.get("class") or "").split()
        if tag in ("script", "style") or a.get("id") in self.SKIP_IDS or self.SKIP_CLASSES & set(classes):
            self.skip = 1

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if self.skip:
            self.skip -= 1
        if tag == "main":
            self.in_main -= 1

    def handle_data(self, data):
        if self.in_main and not self.skip:
            self.words += len(data.split())


def reading_minutes(text: str) -> int:
    p = MainText()
    p.feed(text)
    return max(1, math.ceil(p.words / WPM))


def resolve_item_path(page: Path, path: str) -> str:
    """Turn a card's data-path (as Quarto wrote it) into a site address such as /articles/x/."""
    path = path.split("#")[0].split("?")[0]
    if path.startswith("/"):
        target = path
    else:
        base = page_address(page) if page.name == "index.html" else page_address(page).rsplit("/", 1)[0] + "/"
        parts = [p for p in base.strip("/").split("/") if p]
        for seg in path.split("/"):
            if seg in ("", "."):
                continue
            if seg == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(seg)
        target = "/" + "/".join(parts)
    target = re.sub(r"\.qmd$", ".html", target)
    target = re.sub(r"index\.html$", "", target)
    if not target.endswith("/"):
        target += "/"
    return target


def fix_page(f: Path, s: str, minutes: dict) -> str:
    address = page_address(f)
    draft = '<meta name="quarto:status" content="draft">' in s

    # 1. Titles
    s = re.sub(r"<title>(.*?) – " + re.escape(SITE) + r"</title>", r"<title>\1 · " + SITE + "</title>", s)
    s = re.sub(r'(<meta (?:property="og:title"|name="twitter:title") content=")(.*?) – ' + re.escape(SITE) + '"', r'\1\2"', s)

    # 2. Addresses
    s = re.sub(r'\bhref="([^"]*)"', lambda m: 'href="' + folder_href(m.group(1)) + '"', s)
    if f.name != "404.html" and 'rel="canonical"' not in s:
        canonical = SITE_URL + address
        og_type = "article" if is_item_page(f) else "website"
        tags = (f'<link rel="canonical" href="{canonical}">\n'
                f'<meta property="og:url" content="{canonical}">\n'
                f'<meta property="og:type" content="{og_type}">\n')
        s = s.replace("</head>", tags + "</head>", 1)

    # 3. Template markup
    if 'class="skip-link"' not in s:
        s = re.sub(r"(<body[^>]*>)", r'\1\n<a class="skip-link" href="#quarto-document-content">Skip to content</a>', s, count=1)
    s = s.replace(' role="menu" aria-expanded="false" aria-label="Toggle navigation"',
                  ' aria-expanded="false" aria-label="Toggle navigation"')
    s = re.sub(r'(<div id="fig-[^"]*" class="quarto-float[^"]*"[^>]*?) alt="[^"]*"', r"\1", s)
    s = re.sub(r'<i class="bi ([^"]+)" role="img">', r'<i class="bi \1" aria-hidden="true">', s)
    s = s.replace(' append-hash="true"', "")
    s = re.sub(r'<div class="sourceCode([^"]*)" id="(cb\d+)">',
               r'<div class="sourceCode\1" id="\2" tabindex="0" role="region" aria-label="Code">', s)
    # Tables scroll inside their own box on narrow screens (see .ai-table-scroll in the theme). The box
    # can scroll, so it takes keyboard focus and a name, from the table's caption where it has one.
    def wrap_table(m):
        cap = re.search(r"<caption[^>]*>(.*?)</caption>", m.group(0), re.S)
        name = html.unescape(re.sub(r"<[^>]+>", "", cap.group(1))).strip() if cap else ""
        label = html.escape("Table: " + name if name else "Table", quote=True)
        return f'<div class="ai-table-scroll" tabindex="0" role="region" aria-label="{label}">{m.group(0)}</div>'
    if "<main" in s:
        head, main = s.split("<main", 1)
        # Split out tables already wrapped (a second run), and wrap the rest
        parts = re.split(r'(<div class="ai-table-scroll"[^>]*><table\b.*?</table></div>)', main, flags=re.S)
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r"<table\b.*?</table>", wrap_table, parts[i], flags=re.S)
        s = head + "<main" + "".join(parts)
    # List.js throws on a listing with no items yet; skip starting it until the first item exists
    s = s.replace("if (!listingTargetEl) {", "if (!listingTargetEl || !listingTargetEl.children.length) {")
    # Quarto writes the site-root offset only when its own search is on; its scripts need it to find
    # listings.json (which turns category chips into links)
    if 'name="quarto:offset"' not in s:
        depth = len(f.relative_to(OUT).parts) - 1
        offset = "/" if f.name == "404.html" else ("./" if depth == 0 else "../" * depth)
        s = s.replace("</head>", f'<meta name="quarto:offset" content="{offset}">\n</head>', 1)
    if "quarto-listing-category" in s:
        s = s.replace('<div id="quarto-margin-sidebar" class="sidebar margin-sidebar">',
                      '<div id="quarto-margin-sidebar" class="sidebar margin-sidebar" role="complementary" aria-label="Filter by category">')

    # 4. Reading time: on the page, then on any card
    if is_item_page(f) and address in minutes:
        s = re.sub(r'(<p class="ai-reading">)(.*?)(</p>)', lambda m: f"{m.group(1)}{minutes[address]} min{m.group(3)}", s)

    def card(m):
        key = resolve_item_path(f, m.group(2))
        if key in minutes:
            return f'{m.group(1)}{minutes[key]} min read{m.group(3)}'
        return m.group(0)
    s = re.sub(r'(<span class="ai-reading" data-path="([^"]*)">)(?:.*?)(</span>)', card, s)

    # 5. Category chips on article and guide pages link to the Articles or Guides & Labs filter.
    #    Built here rather than by Quarto's script, which links them to the home page when a reader
    #    arrives without a referrer, and which needs listings.json at a path it cannot find.
    if is_item_page(f):
        section = f.relative_to(OUT).parts[0]

        def chip(m):
            label = html.unescape(m.group(1))
            return (f'<div class="ai-title-category"><a href="/{section}/#category={quote(label, safe="")}">'
                    f'{m.group(1)}</a></div>')
        s = re.sub(r'<div class="quarto-category">([^<]*)</div>', chip, s)

    # Drafts: rendered for review at their own address, kept out of search engines and the site's search
    if draft:
        if 'name="robots"' not in s:
            s = s.replace("</head>", '<meta name="robots" content="noindex">\n</head>', 1)

    # 6. Search: Pagefind indexes each page's main content, without the endnotes or the call-to-action box
    if address not in ("/404.html", "/search/") and not draft:
        s = re.sub(r'<main class="content" id="quarto-document-content"(?![^>]*data-pagefind-body)',
                   '<main class="content" id="quarto-document-content" data-pagefind-body', s, count=1)
        s = re.sub(r'<div id="quarto-appendix" class="([^"]*)"(?! data-pagefind-ignore)',
                   r'<div id="quarto-appendix" class="\1" data-pagefind-ignore', s, count=1)
        s = re.sub(r'<div class="cta"(?! data-pagefind-ignore)', '<div class="cta" data-pagefind-ignore', s)
        s = re.sub(r'<div class="listing-no-matching d-none"(?! data-pagefind-ignore)',
                   '<div class="listing-no-matching d-none" data-pagefind-ignore', s)
    return s


def remove_draft_placeholders():
    """A piece marked `draft: true` waits for the day of its first post. Quarto leaves it out of listings,
    feeds, the sitemap and its own search, but still writes an empty page at its address and copies its
    images. Remove both, so nothing of a waiting piece is published."""
    held = []
    for f in sorted(OUT.rglob("*.html")):
        s = f.read_text(encoding="utf-8")
        if re.fullmatch(r"\s*<!DOCTYPE html>\s*<html[^>]*>\s*</html>\s*", s, re.I):
            folder = f.parent
            held.append(page_address(f))
            f.unlink()
            if folder != OUT and not any(folder.rglob("*.html")):
                shutil.rmtree(folder)
    if held:
        print("post-render: drafts held back: " + ", ".join(held))


def build_search_index():
    """Index the finished pages with Pagefind 1.4.0 (tools/package.json), the version the handbook uses."""
    tools = Path(__file__).resolve().parent
    exe = tools / "node_modules" / ".bin" / "pagefind"
    if not exe.exists():
        subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--prefix", str(tools)], check=True)
    subprocess.run([str(exe), "--site", str(OUT), "--quiet"], check=True)


def main():
    if not OUT.is_dir():
        raise SystemExit(f"post-render: no output folder at {OUT}")
    remove_draft_placeholders()
    pages = sorted(OUT.rglob("*.html"))

    minutes = {}
    for f in pages:
        if is_item_page(f):
            minutes[page_address(f)] = reading_minutes(f.read_text(encoding="utf-8"))

    for f in pages:
        s = f.read_text(encoding="utf-8")
        new = fix_page(f, s, minutes)
        if new != s:
            f.write_text(new, encoding="utf-8")

    sitemap = OUT / "sitemap.xml"
    if sitemap.exists():
        s = sitemap.read_text(encoding="utf-8")
        new = re.sub(r"(<loc>[^<]*/)index\.html(</loc>)", r"\1\2", s)
        if new != s:
            sitemap.write_text(new, encoding="utf-8")

    search = OUT / "search.json"
    if search.exists():
        data = json.loads(search.read_text(encoding="utf-8"))
        changed = False
        for item in data:
            for key in ("href", "objectID"):
                if isinstance(item.get(key), str):
                    new = re.sub(r"(^|/)index\.html(?=$|#)", r"\1", item[key])
                    if new != item[key]:
                        item[key] = new or "./"
                        changed = True
        if changed:
            search.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    build_search_index()


if __name__ == "__main__":
    main()
