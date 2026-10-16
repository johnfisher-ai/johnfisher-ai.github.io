# AI+ by John Fisher

AI, plus the data science, math, statistics and Python behind it.

**Site:** https://johnfisher-ai.github.io/

This repository builds AI+, John Fisher's hub site: articles, a Handbooks shelf, Guides & Labs, and an About page. The handbooks and labs live on their own sites, in their own repositories. This site links to them and never copies them.

## How the site is built

The site is a [Quarto](https://quarto.org/) website. `quarto render` writes the finished pages to `docs/`, and GitHub Pages serves `docs/` from the `main` branch as they are. Nothing is built on GitHub.

- Quarto is pinned at 1.10.19 in `requirements.txt`, because `tools/postrender.py` adjusts its output.
- `tools/postrender.py` runs after every render. It sets page titles, gives every page its folder address (for example `/articles/<slug>/`) in links, the sitemap and link previews, adds reading times, fixes template markup so pages pass the HTML validator and accessibility checks, and builds the search index with [Pagefind](https://pagefind.app/).
- `_freeze/` keeps the output of any Python code, so pages rebuild without rerunning it. Commit it with the page.
- `docs/` is generated. Never edit it by hand.

To build:

```bash
pip install -r requirements.txt
npm install --prefix tools
quarto render
```

## Checks

Run before every change is published:

```bash
bash tools/checks/run.sh
```

It runs the Nu HTML validator, checks every internal link and anchor, checks each page's title, language and footer, checks each article's title, teaser, preview image and license, and runs axe on every page at 1280 px in light mode and 375 px in dark mode. It fails on any sideways scroll, script error or failed request. Links to other sites are checked at each release with the [W3C Link Checker](https://validator.w3.org/checklink).

## Layout

| Path | What it holds |
|---|---|
| `_quarto.yml` | Site settings, top bar, footer and theme |
| `index.qmd` | Home |
| `articles/` | The Articles page and its feed; one folder per article, `articles/<slug>/index.qmd` with its `card.png` |
| `guides/` | The Guides & Labs page and its feed; one folder per guide article |
| `handbooks/` | The Handbooks shelf |
| `about/`, `search/`, `404.qmd` | About, search and the not-found page |
| `_partials/` | Shared blocks: the shelf, the lab cards and the page head |
| `assets/` | Theme, card template, endnote style, Plus Jakarta Sans, the AI+ mark and icons |
| `tools/` | Post-render script, the call-to-action filter and the checks |
| `docs/` | The finished site that GitHub Pages serves |

## Writing an article

Each article is `articles/<slug>/index.qmd`. The slug is the article's claim in three to six words, lowercase with hyphens, and never changes once published.

```yaml
---
title: "Adoption is outrunning governance"   # the claim, 70 characters at most
description: "Two sentences, 160 characters at most. This is the card text and the link preview."
date: 2026-11-03                            # the day of its first LinkedIn post
date-modified: 2026-11-03                   # shown as "Last checked"
categories: [CIO, CTO, AI control plane]    # one to three audiences, then the topic
source: "AI Control Plane Handbook"         # shown on the card
image: card.png                             # 1200 × 630
image-alt: "What the card image shows"
license: "CC BY-NC-ND"                      # "CC BY" unless the article is drawn from the AI Control Plane Handbook
cta-source: "Read the full handbook: [Section 1, The evidence](https://...). See the slides: [slide 4](https://...)."
references:                                 # endnotes, each worded exactly as it should print
  - id: short-key
    type: webpage
    title: "Publisher, “Title”, date."
    URL: https://...
---
```

Cite a source in the text with `[@short-key]`. Endnotes are numbered in order of first citation, and a source cited again keeps its number.

Guide articles follow the same pattern in `guides/<slug>/index.qmd`, with the level (Beginner, Intermediate or Advanced) among the categories and two buttons:

```markdown
[Open the visual guide](https://...){.btn .btn-primary} [Open in Colab](https://...){.btn .btn-outline-primary}
```

## Audience and topic pages

An audience or topic page is a pre-filtered card grid at `audience/<role>/index.qmd` or `topics/<slug>/index.qmd`. Each is added once it has four articles or guides:

```yaml
---
title: "For CIOs"
listing:
  contents: ["../../articles/*/index.qmd", "../../guides/*/index.qmd"]
  include:
    categories: "CIO"
  template: ../../assets/cards.ejs
  template-params:
    heading: 2
  sort: "date desc"
---
```

## Licenses

Articles and guide articles are licensed under CC BY 4.0, except articles drawn from *The AI Control Plane Handbook*, which are licensed under CC BY-NC-ND 4.0, the handbook's own license. Each article names its license under "Reuse". Code is licensed under the MIT License. See [LICENSE.md](LICENSE.md) and [LICENSE-CODE](LICENSE-CODE).

John Fisher works for Salesforce. The views here are his own, not Salesforce's, and are drawn from public information; this site is not affiliated with or endorsed by Salesforce. Product names are trademarks of their owners.
