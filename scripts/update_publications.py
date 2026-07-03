#!/usr/bin/env python3
"""Regenerate the auto-generated sections of publications.html from a SciX/ADS library.

Requires an SciX/ADS API token in the ADS_API_TOKEN environment variable
(SciX account -> Settings -> API Token). Same auth as the classic ADS API.
"""
import html
import os
import re
import sys
from pathlib import Path

import requests

API_BASE = "https://scixplorer.org/v1"
LIBRARY_ID = os.environ.get("SCIX_LIBRARY_ID", "IMEafr7DQCSATOaQQCjBKA")
REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_HTML = REPO_ROOT / "publications.html"

FIELDS = "bibcode,title,author,year,bibstem,pubdate,doctype,identifier"


def api_get(path, token, **params):
    resp = requests.get(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_library_bibcodes(token):
    bibcodes = []
    start = 0
    rows = 200
    while True:
        data = api_get(f"/biblib/libraries/{LIBRARY_ID}", token, start=start, rows=rows)
        docs = data.get("documents", [])
        bibcodes.extend(docs)
        if len(docs) < rows:
            break
        start += rows
    return bibcodes


def fetch_metadata(bibcodes, token):
    if not bibcodes:
        return []
    query = "bibcode:(" + " OR ".join(bibcodes) + ")"
    data = api_get("/search/query", token, q=query, fl=FIELDS, rows=len(bibcodes))
    return data["response"]["docs"]


def format_authors(authors):
    formatted = []
    for full_name in authors:
        if "," in full_name:
            last, first = full_name.split(",", 1)
        else:
            parts = full_name.rsplit(" ", 1)
            last, first = (parts[0], "") if len(parts) == 1 else (parts[1], parts[0])
        last = last.strip()
        initials = "".join(part[0] for part in first.strip().split() if part)
        formatted.append(f"{last} {initials}".strip())

    if len(formatted) > 8:
        return ", ".join(formatted[:3]) + ", et al."
    return ", ".join(formatted)


def escape(text):
    # Preserve existing HTML entities/tags already present in ADS titles
    # (e.g. "H&alpha;", "<SUP>56</SUP>"), only escape bare ampersands.
    text = re.sub(r"&(?!#?\w+;)", "&amp;", text)
    return text


def build_entry(doc):
    bibcode = doc["bibcode"]
    title = escape(doc.get("title", [""])[0])
    authors = format_authors(doc.get("author", []))
    year = doc.get("year", bibcode[:4])
    bibstem = doc.get("bibstem", [""])[0]

    is_preprint = doc.get("doctype") == "eprint" or bibstem == "arXiv"
    journal_bit = "arXiv preprint" if is_preprint else html.escape(bibstem)
    meta = f"{authors} · {journal_bit}, {year}"

    link = f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"
    return is_preprint, (
        f'      <li class="pub">\n'
        f'        <a class="pub-title" href="{link}" target="_blank" rel="noopener">{title}</a>\n'
        f'        <span class="pub-meta">{meta}</span>\n'
        f'      </li>'
    )


def replace_section(content, marker, entries_html):
    start = f"<!-- AUTO-GENERATED:{marker}:START -->"
    end = f"<!-- AUTO-GENERATED:{marker}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = start + "\n" + entries_html + "\n    " + end
    if not pattern.search(content):
        raise RuntimeError(f"markers for {marker} not found in publications.html")
    return pattern.sub(replacement, content)


def main():
    token = os.environ.get("ADS_API_TOKEN")
    if not token:
        print("ADS_API_TOKEN environment variable is not set", file=sys.stderr)
        return 1

    bibcodes = fetch_library_bibcodes(token)
    docs = fetch_metadata(bibcodes, token)
    docs.sort(key=lambda d: d.get("pubdate", "0000-00-00"), reverse=True)

    submitted, published = [], []
    for doc in docs:
        is_preprint, entry_html = build_entry(doc)
        (submitted if is_preprint else published).append(entry_html)

    content = PUBLICATIONS_HTML.read_text()
    content = replace_section(content, "SUBMITTED", "\n".join(submitted))
    content = replace_section(content, "PUBLISHED", "\n".join(published))
    PUBLICATIONS_HTML.write_text(content)
    print(f"Wrote {len(submitted)} submitted and {len(published)} published entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
