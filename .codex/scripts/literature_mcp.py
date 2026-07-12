#!/usr/bin/env python3
"""Literature MCP server — zero-dependency JSON-RPC 2.0 over stdio.

Wraps .codex/scripts/lit_search.py (arXiv / OpenAlex / PubMed / Semantic Scholar) as MCP tools.
Registered as `mcp_servers.literature` in the project's `.codex/config.toml`; loads at session
start. No pip packages required —
implements the MCP stdio protocol (newline-delimited JSON-RPC) directly with the stdlib.

Tools exposed:
  lit_search   — search one source or all, with venue/year filters
  lit_fetch    — fetch a single URL (paper landing page / OA PDF link check) and return text head
"""
import json
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import lit_search as core  # noqa: E402

PROTOCOL = '2024-11-05'

TOOLS = [
    {
        'name': 'lit_search',
        'description': (
            'Search academic literature. Sources: arxiv (preprints), openalex (journals + '
            'top-tier conferences, citation counts, OA links), pubmed (biomed), s2 (Semantic '
            'Scholar; rate-limited without S2_API_KEY), or all. Returns a markdown table with '
            'title/authors/year/venue/citations/ids/OA-pdf plus abstract snippets. Snippets are '
            'not evidence — fetch and read the paper before citing it.'),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'source': {'type': 'string',
                           'enum': ['arxiv', 'openalex', 'pubmed', 's2', 'all']},
                'query': {'type': 'string'},
                'limit': {'type': 'integer', 'minimum': 1, 'maximum': 25},
                'venue': {'type': 'string',
                          'description': 'venue filter, e.g. "NeurIPS" or "Nature Communications"'},
                'year': {'type': 'string', 'description': 'YYYY or YYYY-YYYY'},
            },
            'required': ['source', 'query'],
        },
    },
    {
        'name': 'lit_fetch',
        'description': ('Fetch a URL (paper page or OA PDF link) and return the first part of the '
                        'body — use to verify a link resolves and skim landing-page metadata. '
                        'Not a PDF parser; download PDFs to papers/ for full reading.'),
        'inputSchema': {
            'type': 'object',
            'properties': {'url': {'type': 'string'},
                           'max_chars': {'type': 'integer', 'minimum': 200, 'maximum': 20000}},
            'required': ['url'],
        },
    },
]


def call_tool(name, args):
    if name == 'lit_search':
        records, errors = core.run_search(
            args['source'], args['query'], int(args.get('limit', 8)),
            args.get('venue'), args.get('year'))
        return core.to_markdown(records, errors)
    if name == 'lit_fetch':
        body, err = core.http_get(args['url'])
        if err:
            return f'FETCH ERROR: {err}'
        return body[: int(args.get('max_chars', 5000))]
    raise ValueError(f'unknown tool: {name}')


def reply(msg_id, result=None, error=None):
    out = {'jsonrpc': '2.0', 'id': msg_id}
    if error is not None:
        out['error'] = error
    else:
        out['result'] = result
    sys.stdout.write(json.dumps(out, ensure_ascii=False) + '\n')
    sys.stdout.flush()


def main():
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
            reply(msg_id, {'protocolVersion': PROTOCOL,
                           'capabilities': {'tools': {}},
                           'serverInfo': {'name': 'literature', 'version': '1.0.0'}})
        elif method == 'notifications/initialized':
            continue
        elif method == 'ping':
            reply(msg_id, {})
        elif method == 'tools/list':
            reply(msg_id, {'tools': TOOLS})
        elif method == 'tools/call':
            params = msg.get('params') or {}
            try:
                text = call_tool(params.get('name'), params.get('arguments') or {})
                reply(msg_id, {'content': [{'type': 'text', 'text': text}]})
            except Exception as err:  # noqa: BLE001 — surface to client, keep serving
                reply(msg_id, {'content': [{'type': 'text',
                                            'text': f'TOOL ERROR: {err}'}],
                               'isError': True})
        elif msg_id is not None:
            reply(msg_id, error={'code': -32601, 'message': f'method not found: {method}'})


if __name__ == '__main__':
    main()
