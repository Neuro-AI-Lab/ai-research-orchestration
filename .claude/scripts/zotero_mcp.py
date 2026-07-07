#!/usr/bin/env python3
"""Zotero integration — CLI and MCP server in one file, stdlib-only.

Connects the lab to the user's Zotero library via the Zotero Web API v3 (works headless from any
machine) or, with ZOTERO_LOCAL=1, the Zotero desktop local API (http://localhost:23119).

Configuration (put in .claude/settings.local.json "env"; see .claude/ZOTERO.md):
  ZOTERO_API_KEY    key from https://www.zotero.org/settings/keys (read; +write for `add`)
  ZOTERO_USER_ID    numeric userID shown on the same page
  ZOTERO_GROUP_ID   optional — use a group library instead of the personal one
  ZOTERO_LOCAL=1    optional — talk to the running Zotero desktop app instead of the web API

CLI usage (agents call this via Bash):
  zotero_mcp.py search "query" [--limit N] [--tag TAG]
  zotero_mcp.py item KEY                 # full metadata + children (attachments/notes)
  zotero_mcp.py fulltext KEY             # indexed full text of an attachment item
  zotero_mcp.py bibtex KEY[,KEY...]      # BibTeX export — pipe into the Overleaf .bib
  zotero_mcp.py collections
  zotero_mcp.py add --title T [--doi D] [--url U] [--venue V] [--date YYYY] [--abstract A] [--tag T]...
  zotero_mcp.py serve                    # MCP stdio server (registered in .mcp.json)
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API_VERSION = '3'


def config():
    local = os.environ.get('ZOTERO_LOCAL') == '1'
    base = 'http://localhost:23119/api' if local else 'https://api.zotero.org'
    gid, uid = os.environ.get('ZOTERO_GROUP_ID'), os.environ.get('ZOTERO_USER_ID')
    if local:
        prefix = f'{base}/users/0'
    elif gid:
        prefix = f'{base}/groups/{gid}'
    elif uid:
        prefix = f'{base}/users/{uid}'
    else:
        raise SystemExit(
            'Zotero not configured: set ZOTERO_USER_ID (+ ZOTERO_API_KEY) or ZOTERO_GROUP_ID in '
            '.claude/settings.local.json, or ZOTERO_LOCAL=1 with the desktop app running. '
            'Setup guide: .claude/ZOTERO.md')
    return prefix, os.environ.get('ZOTERO_API_KEY', '')


def request(url, data=None, method='GET', raw=False):
    prefix, key = config()
    headers = {'Zotero-API-Version': API_VERSION}
    if key:
        headers['Authorization'] = f'Bearer {key}'
    if data is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data).encode()
    req = urllib.request.Request(prefix + url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode('utf-8', 'replace')
            return (body if raw else json.loads(body or 'null')), None
    except urllib.error.HTTPError as err:
        hints = {403: 'invalid API key, or the key lacks access to this library',
                 404: 'not found — wrong library id or item key',
                 428: 'write requires If-Unmodified-Since-Version (library changed mid-write)'}
        return None, f'HTTP {err.code}: {hints.get(err.code, err.reason)}'
    except Exception as err:  # noqa: BLE001
        return None, f'{type(err).__name__}: {err} (is Zotero running, if ZOTERO_LOCAL=1?)'


def brief(item):
    d = item.get('data', {})
    creators = [c.get('lastName') or c.get('name', '') for c in d.get('creators', [])]
    return {
        'key': item.get('key'),
        'type': d.get('itemType'),
        'title': d.get('title', ''),
        'creators': creators[:4],
        'date': d.get('date', ''),
        'venue': d.get('publicationTitle') or d.get('conferenceName') or d.get('bookTitle', ''),
        'doi': d.get('DOI', ''),
        'tags': [t['tag'] for t in d.get('tags', [])][:8],
        'abstract': (d.get('abstractNote') or '')[:300],
    }


def fmt(records):
    if not records:
        return 'No results.'
    lines = ['| key | title | creators | date | venue | doi |',
             '|:--|:--|:--|:--|:--|:--|']
    for r in records:
        lines.append(f"| {r['key']} | {r['title'][:80]} | {', '.join(r['creators'][:2])}"
                     f"{' et al.' if len(r['creators']) > 2 else ''} | {r['date'][:10]} "
                     f"| {r['venue'][:40]} | {r['doi']} |")
    lines.append('')
    lines += [f"[{r['key']}] {r['abstract']}" for r in records if r['abstract']]
    return '\n'.join(lines)


def search(query, limit=10, tag=None):
    params = {'q': query, 'qmode': 'everything', 'limit': limit,
              'itemType': '-attachment || note'}
    if tag:
        params['tag'] = tag
    body, err = request('/items/top?' + urllib.parse.urlencode(params))
    return (fmt([brief(i) for i in body]) if body else 'No results.') if not err else f'ERROR: {err}'


def item(key):
    body, err = request(f'/items/{key}')
    if err:
        return f'ERROR: {err}'
    out = [json.dumps(body.get('data', {}), indent=1, ensure_ascii=False)]
    children, cerr = request(f'/items/{key}/children')
    if children and not cerr:
        out.append('\nChildren (attachments/notes):')
        for c in children:
            d = c.get('data', {})
            out.append(f"- {c.get('key')} [{d.get('itemType')}] "
                       f"{d.get('title') or d.get('filename', '')} {d.get('contentType', '')}")
    return '\n'.join(out)


def fulltext(key):
    body, err = request(f'/items/{key}/fulltext')
    if err:
        return (f'ERROR: {err}\nNote: fulltext works on ATTACHMENT items — run '
                f'`item <parent-key>` first and use the PDF attachment child key.')
    return (body or {}).get('content', '(no indexed text)')[:60000]


def bibtex(keys):
    body, err = request('/items?' + urllib.parse.urlencode(
        {'itemKey': keys, 'format': 'bibtex'}), raw=True)
    return body if not err else f'ERROR: {err}'


def collections():
    body, err = request('/collections?limit=100')
    if err:
        return f'ERROR: {err}'
    return '\n'.join(f"- {c['key']}  {c['data'].get('name', '')}" for c in body) or '(none)'


def add(fields):
    creators = []
    item_data = {'itemType': 'journalArticle',
                 'title': fields.get('title', ''),
                 'DOI': fields.get('doi', ''), 'url': fields.get('url', ''),
                 'publicationTitle': fields.get('venue', ''),
                 'date': fields.get('date', ''),
                 'abstractNote': fields.get('abstract', ''),
                 'creators': creators,
                 'tags': [{'tag': t} for t in fields.get('tags', [])]}
    body, err = request('/items', data=[item_data], method='POST')
    if err:
        return f'ERROR: {err} (add requires an API key with WRITE permission)'
    ok = (body or {}).get('successful', {})
    fail = (body or {}).get('failed', {})
    if ok:
        k = list(ok.values())[0].get('key')
        return f'added: {k}  {fields.get("title", "")[:70]}'
    return f'FAILED: {json.dumps(fail)}'


# ---------------------------------------------------------------- MCP server

TOOLS = [
    {'name': 'zotero_search',
     'description': ('Search the user\'s Zotero library (titles, creators, full text). Returns a '
                     'markdown table with item keys — keys feed zotero_item / zotero_fulltext / '
                     'zotero_bibtex. Library-first rule: check here before searching the open web.'),
     'inputSchema': {'type': 'object',
                     'properties': {'query': {'type': 'string'},
                                    'limit': {'type': 'integer', 'minimum': 1, 'maximum': 50},
                                    'tag': {'type': 'string'}},
                     'required': ['query']}},
    {'name': 'zotero_item',
     'description': 'Full metadata for one item key, plus its children (PDF attachments, notes).',
     'inputSchema': {'type': 'object', 'properties': {'key': {'type': 'string'}},
                     'required': ['key']}},
    {'name': 'zotero_fulltext',
     'description': ('Indexed full text of an ATTACHMENT item (get the attachment child key via '
                     'zotero_item first). Read the actual paper before citing it.'),
     'inputSchema': {'type': 'object', 'properties': {'key': {'type': 'string'}},
                     'required': ['key']}},
    {'name': 'zotero_bibtex',
     'description': ('BibTeX export for one or more item keys (comma-separated) — use to build '
                     'the .bib file of the Overleaf paper. Never hand-write BibTeX for items '
                     'that exist in Zotero.'),
     'inputSchema': {'type': 'object', 'properties': {'keys': {'type': 'string'}},
                     'required': ['keys']}},
    {'name': 'zotero_collections',
     'description': 'List the library\'s collections (key + name).',
     'inputSchema': {'type': 'object', 'properties': {}}},
    {'name': 'zotero_add',
     'description': ('Save a paper found via lit_search into Zotero (journalArticle). Requires a '
                     'write-enabled API key. Fields: title (required), doi, url, venue, date, '
                     'abstract, tags[].'),
     'inputSchema': {'type': 'object',
                     'properties': {'title': {'type': 'string'}, 'doi': {'type': 'string'},
                                    'url': {'type': 'string'}, 'venue': {'type': 'string'},
                                    'date': {'type': 'string'}, 'abstract': {'type': 'string'},
                                    'tags': {'type': 'array', 'items': {'type': 'string'}}},
                     'required': ['title']}},
]


def call_tool(name, a):
    if name == 'zotero_search':
        return search(a['query'], int(a.get('limit', 10)), a.get('tag'))
    if name == 'zotero_item':
        return item(a['key'])
    if name == 'zotero_fulltext':
        return fulltext(a['key'])
    if name == 'zotero_bibtex':
        return bibtex(a['keys'])
    if name == 'zotero_collections':
        return collections()
    if name == 'zotero_add':
        return add(a)
    raise ValueError(f'unknown tool: {name}')


def reply(msg_id, result=None, error=None):
    out = {'jsonrpc': '2.0', 'id': msg_id}
    out['error' if error is not None else 'result'] = error if error is not None else result
    sys.stdout.write(json.dumps(out, ensure_ascii=False) + '\n')
    sys.stdout.flush()


def serve():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        method, msg_id = msg.get('method'), msg.get('id')
        if method == 'initialize':
            reply(msg_id, {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}},
                           'serverInfo': {'name': 'zotero', 'version': '1.0.0'}})
        elif method == 'notifications/initialized':
            continue
        elif method == 'ping':
            reply(msg_id, {})
        elif method == 'tools/list':
            reply(msg_id, {'tools': TOOLS})
        elif method == 'tools/call':
            p = msg.get('params') or {}
            try:
                text = call_tool(p.get('name'), p.get('arguments') or {})
                reply(msg_id, {'content': [{'type': 'text', 'text': text}]})
            except SystemExit as err:  # unconfigured — report, keep serving
                reply(msg_id, {'content': [{'type': 'text', 'text': str(err)}], 'isError': True})
            except Exception as err:  # noqa: BLE001
                reply(msg_id, {'content': [{'type': 'text', 'text': f'TOOL ERROR: {err}'}],
                               'isError': True})
        elif msg_id is not None:
            reply(msg_id, error={'code': -32601, 'message': f'method not found: {method}'})


def main(argv):
    if len(argv) < 2 or argv[1] == 'serve':
        serve()
        return 0
    cmd, args = argv[1], argv[2:]
    if cmd == 'search':
        q = args[0] if args else ''
        limit, tag = 10, None
        rest = args[1:]
        while rest:
            a = rest.pop(0)
            if a == '--limit':
                limit = int(rest.pop(0))
            elif a == '--tag':
                tag = rest.pop(0)
        print(search(q, limit, tag))
    elif cmd == 'item':
        print(item(args[0]))
    elif cmd == 'fulltext':
        print(fulltext(args[0]))
    elif cmd == 'bibtex':
        print(bibtex(args[0]))
    elif cmd == 'collections':
        print(collections())
    elif cmd == 'add':
        fields = {'tags': []}
        rest = list(args)
        while rest:
            a = rest.pop(0)
            if a.startswith('--'):
                k = a[2:]
                v = rest.pop(0) if rest else ''
                if k == 'tag':
                    fields['tags'].append(v)
                else:
                    fields[k] = v
        print(add(fields))
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
