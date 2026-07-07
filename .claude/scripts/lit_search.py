#!/usr/bin/env python3
"""Keyless literature search across arXiv, OpenAlex, PubMed, and Semantic Scholar.

Stdlib-only (urllib + xml.etree) — no pip dependencies. Shared core for the Bash CLI and the
literature MCP server (.claude/scripts/literature_mcp.py).

Usage:
  python3 .claude/scripts/lit_search.py <source> "<query>" [--limit N] [--venue "NeurIPS"]
                                        [--year 2020-2026] [--json]
  sources: arxiv | openalex | pubmed | s2 | all

Notes:
- Top-tier conference/journal coverage comes from OpenAlex and Semantic Scholar (venue metadata,
  citation counts, open-access PDF links). arXiv covers preprints; PubMed covers biomed.
- ResearchGate has no public API and scraping violates its ToS — deliberately not included.
- Semantic Scholar without a key shares a public rate pool (429s happen); set S2_API_KEY to lift
  limits. On 429 the tool retries once, then reports the limit honestly.
- Snippets are not evidence: fetch and read the actual paper before citing (brainstorm rules).
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Set LIT_CONTACT_EMAIL (e.g. in .claude/settings.local.json env) to join OpenAlex's polite pool
# — faster, more reliable rate limits. Works without it via the common pool.
_CONTACT = os.environ.get('LIT_CONTACT_EMAIL', '')
UA = {'User-Agent': 'ai-research-orchestrator/1.0'
      + (f' (mailto:{_CONTACT})' if _CONTACT else '')}
TIMEOUT = 20


def http_get(url, headers=None, retry_on_429=True):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode('utf-8', 'replace'), None
    except urllib.error.HTTPError as err:
        if err.code == 429 and retry_on_429:
            time.sleep(2.5)
            return http_get(url, headers, retry_on_429=False)
        return None, f'HTTP {err.code} from {url.split("?")[0]}'
    except Exception as err:  # noqa: BLE001 — report, don't crash the caller
        return None, f'{type(err).__name__}: {err}'


def _rec(title, authors, year, venue, ids, citations, oa_pdf, abstract, url):
    return {
        'title': (title or '').strip(),
        'authors': authors[:4],
        'year': year,
        'venue': venue or '',
        'ids': {k: v for k, v in ids.items() if v},
        'citations': citations,
        'oa_pdf': oa_pdf or '',
        'abstract': re.sub(r'\s+', ' ', abstract or '')[:400],
        'url': url or '',
    }


def parse_years(spec):
    if not spec:
        return None, None
    m = re.match(r'^(\d{4})(?:-(\d{4}))?$', spec)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2) or m.group(1))


def search_arxiv(query, limit, _venue, years):
    # arXiv has no venue metadata — _venue accepted for the uniform source signature, unused.
    q = urllib.parse.quote(f'all:{query}')
    url = (f'https://export.arxiv.org/api/query?search_query={q}'
           f'&max_results={min(limit * 3, 50)}&sortBy=relevance')
    body, err = http_get(url)
    if err:
        return [], err
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    out = []
    for e in ET.fromstring(body).findall('a:entry', ns):
        year = int((e.findtext('a:published', '', ns) or '0000')[:4] or 0)
        lo, hi = years
        if lo and not (lo <= year <= hi):
            continue
        aid = (e.findtext('a:id', '', ns) or '').rsplit('/abs/', 1)[-1]
        out.append(_rec(
            e.findtext('a:title', '', ns),
            [a.findtext('a:name', '', ns) for a in e.findall('a:author', ns)],
            year, 'arXiv preprint', {'arxiv': aid}, None,
            f'https://arxiv.org/pdf/{aid}', e.findtext('a:summary', '', ns),
            f'https://arxiv.org/abs/{aid}'))
        if len(out) >= limit:
            break
    return out, None


def search_openalex(query, limit, venue, years):
    params = {'search': query, 'per-page': min(limit, 25),
              'sort': 'relevance_score:desc',
              'select': 'title,authorships,publication_year,primary_location,ids,'
                        'cited_by_count,open_access,abstract_inverted_index'}
    filt = []
    lo, hi = years
    if lo:
        filt.append(f'from_publication_date:{lo}-01-01,to_publication_date:{hi}-12-31')
    if venue:
        filt.append('primary_location.source.display_name.search:'
                    + venue.replace(',', ' '))
    if filt:
        params['filter'] = ','.join(filt)
    body, err = http_get('https://api.openalex.org/works?' + urllib.parse.urlencode(params))
    if err:
        return [], err
    out = []
    for w in json.loads(body).get('results', []):
        inv = w.get('abstract_inverted_index') or {}
        words = sorted(((p, t) for t, ps in inv.items() for p in ps))
        abstract = ' '.join(t for _, t in words)
        src = ((w.get('primary_location') or {}).get('source') or {})
        ids = w.get('ids') or {}
        out.append(_rec(
            w.get('title'), [a['author']['display_name'] for a in w.get('authorships', [])],
            w.get('publication_year'), src.get('display_name'),
            {'doi': (ids.get('doi') or '').replace('https://doi.org/', '')},
            w.get('cited_by_count'),
            ((w.get('open_access') or {}).get('oa_url')), abstract,
            ids.get('openalex')))
    return out, None


def search_pubmed(query, limit, venue, years):
    term = query + (f' AND {venue}[Journal]' if venue else '')
    lo, hi = years
    if lo:
        term += f' AND {lo}:{hi}[dp]'
    base = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
    body, err = http_get(f'{base}/esearch.fcgi?db=pubmed&retmax={limit}&retmode=json&term='
                         + urllib.parse.quote(term))
    if err:
        return [], err
    ids = json.loads(body)['esearchresult'].get('idlist', [])
    if not ids:
        return [], None
    body, err = http_get(f'{base}/esummary.fcgi?db=pubmed&retmode=json&id=' + ','.join(ids))
    if err:
        return [], err
    res = json.loads(body).get('result', {})
    out = []
    for pmid in ids:
        d = res.get(pmid) or {}
        out.append(_rec(
            d.get('title'), [a.get('name', '') for a in d.get('authors', [])],
            int((d.get('pubdate', '') or '0000')[:4] or 0), d.get('fulljournalname'),
            {'pmid': pmid, 'doi': next((i['value'] for i in d.get('articleids', [])
                                        if i.get('idtype') == 'doi'), '')},
            None, '', '(abstract not returned by esummary — fetch the article)',
            f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'))
    return out, None


def search_s2(query, limit, venue, years):
    params = {'query': query + (f' {venue}' if venue else ''), 'limit': min(limit, 20),
              'fields': 'title,authors,year,venue,citationCount,externalIds,'
                        'openAccessPdf,abstract,url'}
    lo, hi = years
    if lo:
        params['year'] = f'{lo}-{hi}'
    headers = {}
    if os.environ.get('S2_API_KEY'):
        headers['x-api-key'] = os.environ['S2_API_KEY']
    body, err = http_get('https://api.semanticscholar.org/graph/v1/paper/search?'
                         + urllib.parse.urlencode(params), headers)
    if err:
        return [], err + ' (set S2_API_KEY for higher limits)'
    out = []
    for p in json.loads(body).get('data', []):
        ext = p.get('externalIds') or {}
        out.append(_rec(
            p.get('title'), [a.get('name', '') for a in p.get('authors', [])],
            p.get('year'), p.get('venue'),
            {'doi': ext.get('DOI'), 'arxiv': ext.get('ArXiv')},
            p.get('citationCount'), (p.get('openAccessPdf') or {}).get('url'),
            p.get('abstract'), p.get('url')))
    return out, None


SOURCES = {'arxiv': search_arxiv, 'openalex': search_openalex,
           'pubmed': search_pubmed, 's2': search_s2}


def run_search(source, query, limit=8, venue=None, year=None):
    """Core entry point shared by CLI and MCP server. Returns (records, errors)."""
    years = parse_years(year)
    names = list(SOURCES) if source == 'all' else [source]
    records, errors = [], []
    for name in names:
        if name not in SOURCES:
            errors.append(f'unknown source: {name}')
            continue
        recs, err = SOURCES[name](query, limit, venue, years)
        for r in recs:
            r['source'] = name
        records.extend(recs)
        if err:
            errors.append(f'{name}: {err}')
    return records, errors


def to_markdown(records, errors):
    lines = []
    if records:
        lines.append('| # | title | authors | year | venue | cites | ids | oa_pdf |')
        lines.append('|:--|:--|:--|:--|:--|:--|:--|:--|')
        for i, r in enumerate(records, 1):
            ids = ' '.join(f'{k}:{v}' for k, v in r['ids'].items())
            lines.append(f"| {i} | {r['title'][:90]} | {', '.join(r['authors'][:2])}"
                         f"{' et al.' if len(r['authors']) > 2 else ''} | {r['year']} "
                         f"| {r['venue'][:40]} | {r['citations'] if r['citations'] is not None else '—'} "
                         f"| {ids} | {r['oa_pdf'][:60]} |")
        lines.append('')
        for i, r in enumerate(records, 1):
            if r['abstract']:
                lines.append(f"[{i}] {r['abstract']}")
    else:
        lines.append('No results.')
    for err in errors:
        lines.append(f'WARNING: {err}')
    return '\n'.join(lines)


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    source, query = argv[1], argv[2]
    limit, venue, year, as_json = 8, None, None, False
    args = argv[3:]
    while args:
        a = args.pop(0)
        if a == '--limit':
            limit = int(args.pop(0))
        elif a == '--venue':
            venue = args.pop(0)
        elif a == '--year':
            year = args.pop(0)
        elif a == '--json':
            as_json = True
    records, errors = run_search(source, query, limit, venue, year)
    print(json.dumps({'results': records, 'errors': errors}, ensure_ascii=False, indent=1)
          if as_json else to_markdown(records, errors))
    return 0 if records or not errors else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
