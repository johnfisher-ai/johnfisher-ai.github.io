# AI+ by John Fisher

AI, plus the data science, math, statistics and Python behind it.

**Site:** https://johnfisher-ai.github.io/

This repository builds AI+, John Fisher's hub site: articles, a Handbooks shelf, Guides & Labs, and an About page. The handbooks and labs live on their own sites, in their own repositories. This site links to them and never copies them.

## How the site is built

The site is a [Quarto](https://quarto.org/) website. `quarto render` writes the finished pages to `docs/`, and GitHub Pages serves `docs/` from the `main` branch as they are, with no build step on GitHub.

- Quarto is pinned at 1.10.19 in `requirements.txt`, because `tools/postrender.py` adjusts its output.
- `tools/postrender.py` runs after every render. It sets page titles, gives every page its folder address (for example `/articles/<slug>/`) in links, the sitemap and link previews, adds reading times, keeps wide tables inside their own scrolling box on phones, fixes template markup so pages pass the HTML validator and accessibility checks, and builds the search index with [Pagefind](https://pagefind.app/).
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
| `articles/` | The Articles page and its feed<br>One folder per article, `articles/<slug>/index.qmd` with its `card.png` |
| `guides/` | The Guides & Labs page and its feed<br>One folder per guide article |
| `handbooks/` | The Handbooks shelf |
| `about/`<br>`search/`<br>`404.qmd` | About<br>Search<br>The not-found page |
| `_partials/` | Shared blocks for the shelf, the lab cards and the page head |
| `assets/` | Theme, card and Start here templates, endnote style, card image sources, Plus Jakarta Sans, the AI+ mark and icons |
| `tools/` | Post-render script, the call-to-action filter and the checks |
| `docs/` | The finished site that GitHub Pages serves |

## Writing an article

Each article is `articles/<slug>/index.qmd`. The slug is the article's claim in three to six words, lowercase with hyphens, and never changes once published.

```yaml
---
title: "Adoption is outrunning governance"   # the claim, 70 characters at most
description: "Two sentences, 160 characters at most. This is the card text and the link preview."
draft: true                                 # while John reviews it; replaced by date when it is published
date-modified: 2026-11-03                   # shown as "Last checked"
categories: [CIO, CTO, AI control plane]    # one to three audiences, then the topic
source: "AI Control Plane Handbook"         # shown on the card
image: card.png                             # 1200 × 630
image-alt: "What the card image shows"
license: "CC BY-NC-ND"                      # "CC BY" unless the article is drawn from the AI Control Plane Handbook
cta-source: "Read [the full handbook](https://...) and [the executive deck](https://...) online."
references:                                 # endnotes, each worded exactly as it should print
  - id: short-key
    type: webpage
    title: "Publisher, “Title”, date."
    URL: https://...
---
```

Cite a source in the text with `[@short-key]`. Endnotes are numbered in order of first citation, and a source cited again keeps its number.

The audience tags are CIO, CTO, CISO, Architect, Developer, AI Engineer, Analyst, Data Scientist and IT Operations, spelled exactly so.

Guide articles follow the same pattern in `guides/<slug>/index.qmd`. Their categories put the level (Beginner, Intermediate or Advanced) between the audiences and the topic, and two more fields give the time to complete the lab and its format, which the page and the card show in place of a reading time:

```yaml
categories: [Analyst, Developer, Data Scientist, Beginner, Machine learning]
lab-time: "About an hour"
lab-format: "Visual guide and Colab lab"
```

Each guide ends with two buttons, followed by the articles it puts into practice:

```markdown
::: {.ai-actions}
[Open the visual guide](https://...){.btn .btn-primary}
[Open in Colab](https://...){.btn .btn-outline-primary}
:::
```

Link to another article or guide through its `index.qmd`, for example `[Title](../../articles/<slug>/index.qmd)`. While that piece is a draft, Quarto prints the link text without the link, so no page sends a reader to a Draft banner, and the link appears once the piece is published.

## Publishing a piece

A new article or guide starts with `draft: true` while John reviews it. Quarto renders a draft at its own address, so it can be proofread on the site, and leaves it out of the listings, the feeds and the sitemap. Quarto shows a Draft banner at the top of the page, and `tools/postrender.py` keeps it out of the site's search and marks it noindex for search engines.

A piece is published as soon as John approves it. Delete `draft: true`, add `date` and set `date-modified` to that day, and give it a `sequence`, its number in the plan, which orders pieces published on the same day. Then render and run the checks. When a guide is published, each partner article that is already published gets a "Try it" section linking to it.

Promotion on LinkedIn and other social media follows later, on the piece's planned promotion date, and needs no change to the site.

## The home page's Start here row

The row offers one first piece for each audience. `index.qmd` lists the pieces in order under the `start-here` listing, and its `labels` say who each one is for, for example `what-an-ai-control-plane-is: "For CTOs and architects"`. A piece still marked `draft: true` stays out of the row until it is published. To change a pick, edit both lists.

## Audience and topic pages

An audience or topic page is a pre-filtered card grid at `audience/<tag>/index.qmd` or `topics/<slug>/index.qmd`, where `<tag>` is the audience tag in lowercase with hyphens (`audience/ai-engineer/`). Each page is added once it has four published articles or guides:

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

Articles and guide articles are licensed under CC BY 4.0, except articles drawn from *The AI Control Plane Handbook*, which are licensed under CC BY-NC-ND 4.0, the handbook's own license. Each article names its license under "Reuse". Code is licensed under the MIT License, and [LICENSE.md](LICENSE.md) and [LICENSE-CODE](LICENSE-CODE) give the full terms.

John Fisher works for Salesforce. The views here are his own, not Salesforce's, and are drawn from public information; this site is not affiliated with or endorsed by Salesforce. Product names are trademarks of their owners.
