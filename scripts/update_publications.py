#!/usr/bin/env python3
"""Regenerate the auto-generated publication lists from a SciX/ADS library.

Updates two files from the same SciX library fetch:
  - publications.html: full Submitted / Published lists.
  - research.html: per-topic lists, driven by scripts/research_sections.json,
    which maps each <!-- AUTO-GENERATED:<KEY>:... --> block to an ordered
    list of bibcodes/arXiv ids.

Requires an SciX/ADS API token in the ADS_API_TOKEN environment variable
(SciX account -> Settings -> API Token). Same auth as the classic ADS API.
"""
import html
import json
import os
import re
import sys
from pathlib import Path

import requests

API_BASE = "https://scixplorer.org/v1"
LIBRARY_ID = os.environ.get("SCIX_LIBRARY_ID", "IMEafr7DQCSATOaQQCjBKA")
REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_HTML = REPO_ROOT / "publications.html"
RESEARCH_HTML = REPO_ROOT / "research.html"
RESEARCH_SECTIONS_JSON = REPO_ROOT / "scripts" / "research_sections.json"

FIELDS = "bibcode,title,author,year,bibstem,pubdate,doctype,identifier"

ARXIV_ID_RE = re.compile(r"^(?:arxiv:)?(\d{4}\.\d{4,5})(?:v\d+)?$", re.IGNORECASE)


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


def is_preprint_doc(doc):
    bibstem = doc.get("bibstem", [""])[0]
    return doc.get("doctype") == "eprint" or bibstem == "arXiv"


def render_entry(doc, indent="      "):
    """Render a single <li class="pub"> block for doc at the given indent."""
    bibcode = doc["bibcode"]
    title = escape(doc.get("title", [""])[0])
    authors = format_authors(doc.get("author", []))
    year = doc.get("year", bibcode[:4])
    bibstem = doc.get("bibstem", [""])[0]

    is_preprint = is_preprint_doc(doc)
    journal_bit = "arXiv preprint" if is_preprint else html.escape(bibstem)
    meta = f"{authors} · {journal_bit}, {year}"

    link = f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"
    inner = indent + "  "
    return (
        f'{indent}<li class="pub">\n'
        f'{inner}<a class="pub-title" href="{link}" target="_blank" rel="noopener">{title}</a>\n'
        f'{inner}<span class="pub-meta">{meta}</span>\n'
        f'{indent}</li>'
    )


def doc_keys(doc):
    """All identifiers that can be used to reference this doc from research_sections.json:
    its ADS bibcode, plus any bare arXiv id found in its identifier list."""
    keys = {doc["bibcode"]}
    for ident in doc.get("identifier", []):
        m = ARXIV_ID_RE.match(ident.strip())
        if m:
            keys.add(m.group(1))
    return keys


def index_docs(docs):
    index = {}
    for doc in docs:
        for key in doc_keys(doc):
            index[key] = doc
    return index


def replace_section(content, marker, entries_html, marker_indent="    "):
    start = f"<!-- AUTO-GENERATED:{marker}:START -->"
    end = f"<!-- AUTO-GENERATED:{marker}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = start + "\n" + entries_html + "\n" + marker_indent + end
    if not pattern.search(content):
        raise RuntimeError(f"markers for {marker} not found")
    return pattern.sub(replacement, content)


def sync_publications_html(docs):
    submitted, published = [], []
    for doc in docs:
        entry_html = render_entry(doc, indent="      ")
        (submitted if is_preprint_doc(doc) else published).append(entry_html)

    content = PUBLICATIONS_HTML.read_text()
    content = replace_section(content, "SUBMITTED", "\n".join(submitted))
    content = replace_section(content, "PUBLISHED", "\n".join(published))
    PUBLICATIONS_HTML.write_text(content)
    print(f"publications.html: wrote {len(submitted)} submitted and {len(published)} published entries.")


def sync_research_html(docs):
    if not RESEARCH_SECTIONS_JSON.exists():
        print("scripts/research_sections.json not found, skipping research.html sync.", file=sys.stderr)
        return

    mapping = json.loads(RESEARCH_SECTIONS_JSON.read_text())
    mapping = {k: v for k, v in mapping.items() if not k.startswith("_")}
    index = index_docs(docs)

    content = RESEARCH_HTML.read_text()
    missing = []
    for marker, keys in mapping.items():
        entries = []
        for key in keys:
            doc = index.get(key)
            if doc is None:
                missing.append((marker, key))
                continue
            entries.append(render_entry(doc, indent="        "))
        content = replace_section(content, marker, "\n".join(entries), marker_indent="      ")
    RESEARCH_HTML.write_text(content)

    total = sum(len(v) for v in mapping.values()) - len(missing)
    print(f"research.html: synced {total} entries across {len(mapping)} sections.")

    if missing:
        print("research.html: these entries are not (yet) in the SciX library, so they were dropped from their section:", file=sys.stderr)
        for marker, key in missing:
            print(f"  {marker}: {key}", file=sys.stderr)

    mapped_keys = {k for keys in mapping.values() for k in keys}
    unmapped = [d["bibcode"] for d in docs if not (doc_keys(d) & mapped_keys)]
    if unmapped:
        print("research.html: these library papers aren't assigned to a section in research_sections.json yet:", file=sys.stderr)
        for bibcode in unmapped:
            print(f"  {bibcode}", file=sys.stderr)


def main():
    token = os.environ.get("ADS_API_TOKEN")
    if not token:
        print("ADS_API_TOKEN environment variable is not set", file=sys.stderr)
        return 1

    bibcodes = fetch_library_bibcodes(token)
    docs = fetch_metadata(bibcodes, token)
    docs.sort(key=lambda d: d.get("pubdate", "0000-00-00"), reverse=True)

    sync_publications_html(docs)
    sync_research_html(docs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
