#!/usr/bin/env python3
"""Validate a wireframe package: the contract against itself, and the rendered
HTML against the contract. Exits 1 if any check FAILs.

    python3 validate.py design/wireframes [--json]
"""

import json
import os
import re
import sys

VOCAB = {
    'shell', 'header', 'section', 'nav-top', 'nav-side', 'tabs', 'breadcrumb',
    'text', 'stat', 'list', 'table', 'card-grid', 'key-value', 'media', 'avatar', 'chip',
    'form', 'field', 'select', 'choice', 'search', 'filter-bar', 'upload', 'stepper',
    'button', 'link', 'menu', 'banner', 'inline-error', 'empty-state', 'loading', 'toast',
    'modal', 'confirm', 'pagination', 'divider',
}
COLLECTIONS = {'list', 'table', 'card-grid'}
INTERACTIVE = {'button', 'link', 'menu', 'form', 'tabs', 'pagination', 'upload', 'search'}
STATES = ['default', 'empty', 'loading', 'error']
FIELD_TYPE = re.compile(
    r'^(uuid|string|text|int|currency|date|datetime|bool|enum|email|file|url|ref\[[a-z0-9-]+\])$')
ID_SHAPE = re.compile(r'^[a-z0-9]+([.-][a-z0-9]+)*$')
EXEMPT_ID = re.compile(r'\.(shell|main|nav|nav-side|aside|header)$')

checks = []


def add(level, name, detail):
    checks.append({'level': level, 'name': name, 'detail': detail})


def plural(n, s):
    return f"{n} {s}{'' if n == 1 else 's'}"


def trim(problems, keep=3):
    """Render at most `keep` problems, then say how many were left out."""
    shown = ' · '.join(problems[:keep])
    extra = len(problems) - keep
    return shown + (f' · +{extra} more' if extra > 0 else '')


def die(msg):
    print(f'FAIL  package  {msg}', file=sys.stderr)
    sys.exit(1)


# ── load ──────────────────────────────────────────────────────────
args = [a for a in sys.argv[1:] if not a.startswith('--')]
DIR = args[0] if args else 'design/wireframes'
AS_JSON = '--json' in sys.argv

if not os.path.isdir(DIR):
    die(f'no such directory: {DIR}')
contract_path = os.path.join(DIR, 'screens.json')
if not os.path.isfile(contract_path):
    die(f'missing screens.json in {DIR}')
try:
    with open(contract_path, encoding='utf-8') as fh:
        C = json.load(fh)
except json.JSONDecodeError as e:
    die(f'screens.json is not valid JSON — {e}')

meta = C.get('meta') or {}
screens = C.get('screens') or []
flows = C.get('flows') or []
entities = C.get('entities') or {}
fixtures = C.get('fixtures') or {}
screen_ids = {s.get('id') for s in screens}

# walk every component in the contract -> list of (node, screen, region)
nodes = []
for s in screens:
    for r in s.get('regions') or []:
        stack = list(r.get('components') or [])
        while stack:
            n = stack.pop(0)
            nodes.append((n, s, r))
            stack = list(n.get('children') or []) + stack
node_ids = {n['id'] for n, _, _ in nodes if n.get('id')}


def props(n):
    return n.get('props') or {}


# ── 1. meta ───────────────────────────────────────────────────────
need = ['product', 'version', 'device', 'platform', 'auth', 'nonGoals']
missing = [k for k in need if meta.get(k) is None]
if missing:
    add('FAIL', 'meta', 'missing ' + ', '.join(missing))
elif not isinstance(meta['nonGoals'], list) or not meta['nonGoals']:
    add('WARN', 'meta', 'nonGoals is empty — nothing stops scope creep downstream')
else:
    add('PASS', 'meta', f"{meta['product']} v{meta['version']} · {meta['platform']} · "
                        f"{plural(len(meta['nonGoals']), 'non-goal')}")

# ── 2. entities + fixtures ────────────────────────────────────────
bad = []
for eid, e in entities.items():
    fields = e.get('fields') or []
    if not fields:
        bad.append(f'{eid} has no fields')
        continue
    for f in fields:
        if not FIELD_TYPE.match(f.get('type') or ''):
            bad.append(f'{eid}.{f.get("name")}: unknown type "{f.get("type")}"')
        if f.get('type') == 'enum' and not f.get('values'):
            bad.append(f'{eid}.{f.get("name")}: enum with no values')
no_fixture = [eid for eid in entities if not fixtures.get(eid)]
for eid, rows in fixtures.items():
    known = {f['name'] for f in (entities.get(eid, {}).get('fields') or [])}
    required = [f['name'] for f in (entities.get(eid, {}).get('fields') or []) if f.get('required')]
    for i, row in enumerate(rows):
        for k in row:
            if k not in known:
                bad.append(f'fixture {eid}[{i}].{k} is not a field on {eid}')
        for k in required:
            if k not in row:
                bad.append(f'fixture {eid}[{i}] missing required {k}')
if bad:
    add('FAIL', 'entities', trim(bad, 4))
elif no_fixture:
    add('WARN', 'entities',
        f'no fixtures for {", ".join(no_fixture)} — screens will show invented data')
else:
    add('PASS', 'entities', f'{len(entities)} entities, all with fixtures')

# ── 3. vocabulary ─────────────────────────────────────────────────
off = [n for n, _, _ in nodes if n.get('type') not in VOCAB]
if off:
    seen = list(dict.fromkeys(f'{n.get("type")} ({n.get("id")})' for n in off))
    add('FAIL', 'vocabulary',
        f'{plural(len(off), "component")} outside the set: ' + ', '.join(seen[:3]))
else:
    kinds = {n.get('type') for n, _, _ in nodes}
    add('PASS', 'vocabulary', f'{plural(len(nodes), "component")}, {len(kinds)} primitives used')

# ── 4. ids ────────────────────────────────────────────────────────
seen_ids, problems = set(), []
for n, s, _ in nodes:
    nid = n.get('id') or ''
    if nid in seen_ids:
        problems.append(f'duplicate {nid}')
    seen_ids.add(nid)
    if not nid.startswith(s['id'] + '.'):
        problems.append(f'{nid} (on {s["id"]}) not prefixed')
    if not ID_SHAPE.match(nid):
        problems.append(f'{nid} not kebab-case')
if problems:
    add('FAIL', 'ids', trim(problems))
else:
    add('PASS', 'ids', f'{plural(len(seen_ids), "id")} unique, prefixed, stable')

# ── 5. data bindings ──────────────────────────────────────────────
unresolved = []


def check_bind(b, where):
    if not b:
        return
    ent, _, field = str(b).partition('.')
    if ent not in entities:
        unresolved.append(f'{where} → unknown entity "{ent}"')
    elif not any(f['name'] == field for f in entities[ent].get('fields') or []):
        unresolved.append(f'{where} → {ent} has no field "{field}"')


for n, _, _ in nodes:
    check_bind(n.get('binds'), n.get('id'))
    for col in props(n).get('columns') or []:
        check_bind(col.get('binds'), f'{n.get("id")}:{col.get("label")}')
    for pr in props(n).get('pairs') or []:
        check_bind(pr.get('binds'), f'{n.get("id")}:{pr.get("label")}')
if unresolved:
    add('FAIL', 'bindings', trim(unresolved))
else:
    add('PASS', 'bindings', 'every displayed value traces to an entity field')

# ── 6. actions ────────────────────────────────────────────────────
broken, no_action = [], []


def resolve(a, where):
    if not a:
        return
    do, target = a.get('do'), a.get('target')
    if do in ('back', 'none', 'submit'):
        return
    if do == 'external':
        if not re.match(r'^external:.+', target or ''):
            broken.append(f'{where} → external target unnamed')
        return
    if not target:
        broken.append(f'{where} → {do} with no target')
    elif target not in screen_ids:
        broken.append(f'{where} → "{target}" is not a screen')
    elif do == 'open' and '.modal-' not in target:
        broken.append(f'{where} → open must target a .modal-* screen')


for n, _, _ in nodes:
    p = props(n)
    if (n.get('type') in INTERACTIVE and not n.get('action')
            and not p.get('rowAction') and not p.get('items') and not p.get('submitAction')):
        no_action.append(n.get('id'))
    resolve(n.get('action'), n.get('id'))
    resolve(p.get('rowAction'), f'{n.get("id")}:row')
    for it in p.get('items') or []:
        if isinstance(it, dict):   # breadcrumb/stepper items are plain strings
            resolve(it.get('action'), f'{n.get("id")}:{it.get("label")}')
problems = broken + [f'{i} has no action' for i in no_action]
if problems:
    add('FAIL', 'actions', trim(problems))
else:
    add('PASS', 'actions',
        'every control resolves to a screen, a submit, or a stated no-op')

# ── 7. states ─────────────────────────────────────────────────────
problems = []
for s in screens:
    for k in STATES:
        st = (s.get('states') or {}).get(k)
        if st is None:
            problems.append(f'{s["id"]}.{k} undeclared')
            continue
        if st.get('render') is False and not st.get('reason'):
            problems.append(f'{s["id"]}.{k} skipped with no reason')
        if st.get('render') is True:
            if not st.get('file'):
                problems.append(f'{s["id"]}.{k} rendered but no file')
            elif not os.path.isfile(os.path.join(DIR, st['file'])):
                problems.append(f'{s["id"]}.{k} → {st["file"]} missing')
            if k in ('empty', 'error') and not (st.get('copy') or {}).get('title'):
                problems.append(f'{s["id"]}.{k} has no copy.title')
if problems:
    add('FAIL', 'states', trim(problems))
else:
    add('PASS', 'states',
        f'{len(screens) * len(STATES)} state decisions across {plural(len(screens), "screen")}')

# ── 8. empty states on collections ────────────────────────────────
bare = []
for s in screens:
    cols = [n for n, sc, _ in nodes if sc['id'] == s['id'] and n.get('type') in COLLECTIONS]
    if not cols:
        continue
    st = (s.get('states') or {}).get('empty')
    if not st or (st.get('render') is not True and not st.get('reason')):
        bare.append(f'{s["id"]} ({cols[0].get("type")})')
if bare:
    add('FAIL', 'empty-states',
        f'{plural(len(bare), "collection screen")} with nothing decided: ' + ', '.join(bare[:3]))
else:
    add('PASS', 'empty-states', 'every list, table, and grid says what it looks like at zero')

# ── 9. destructive actions ────────────────────────────────────────
unguarded = []
for n, s, _ in nodes:
    if n.get('type') != 'button' or props(n).get('variant') != 'danger':
        continue
    # a danger button that lives inside a confirm IS the confirmation
    if any(sc['id'] == s['id'] and c.get('type') == 'confirm' for c, sc, _ in nodes):
        continue
    a = n.get('action') or {}
    target = a.get('target')
    has_confirm = (a.get('do') == 'open' and target in screen_ids
                   and any(sc['id'] == target and c.get('type') == 'confirm'
                           for c, sc, _ in nodes))
    if not has_confirm:
        unguarded.append(n.get('id'))
if unguarded:
    add('FAIL', 'destructive',
        f'{plural(len(unguarded), "danger action")} with no confirm screen: '
        + ', '.join(unguarded[:3]))
else:
    add('PASS', 'destructive', 'every destructive action opens a confirm')

# ── 10. primary button per screen ─────────────────────────────────
problems = []
for s in screens:
    n_primary = sum(1 for n, sc, _ in nodes
                    if sc['id'] == s['id'] and n.get('type') == 'button'
                    and props(n).get('variant') == 'primary')
    if n_primary > 1:
        problems.append(f'{s["id"]} has {n_primary}')
if problems:
    add('WARN', 'emphasis', 'more than one primary action: ' + ', '.join(problems[:3]))
else:
    add('PASS', 'emphasis', 'at most one primary action per screen')

# ── 11. flows and orphans ─────────────────────────────────────────
reached, problems = set(), []
for f in flows:
    steps = f.get('steps') or []
    if not steps:
        problems.append(f'flow {f.get("id")} has no steps')
        continue
    for st in steps:
        if st.get('screen') not in screen_ids:
            problems.append(f'flow {f.get("id")} → unknown screen {st.get("screen")}')
        else:
            reached.add(st['screen'])
        if st.get('to'):
            if st['to'] not in screen_ids:
                problems.append(f'flow {f.get("id")} → unknown target {st["to"]}')
            else:
                reached.add(st['to'])
        if st.get('action') and st['action'] not in node_ids:
            problems.append(f'flow {f.get("id")} → unknown control {st["action"]}')
orphans = [s['id'] for s in screens if s['id'] not in reached]
if problems:
    add('FAIL', 'flows', trim(problems))
elif not any(f.get('primary') for f in flows):
    add('WARN', 'flows', f'{plural(len(flows), "flow")} but none marked primary')
elif orphans:
    add('WARN', 'flows', f'{plural(len(orphans), "screen")} unreachable from any flow: '
                         + ', '.join(orphans[:3]))
else:
    add('PASS', 'flows', f'{plural(len(flows), "flow")}, every screen reachable')

# ── 12. acceptance criteria ───────────────────────────────────────
thin = [s['id'] for s in screens if len(s.get('acceptance') or []) < 3]
vague = [f'{s["id"]}: "{a[:40]}"' for s in screens for a in s.get('acceptance') or []
         if re.match(r'^there (is|are) ', a, re.I) or len(a) < 25]
if thin:
    add('WARN', 'acceptance', f'under 3 criteria on {", ".join(thin[:3])}')
elif vague:
    add('WARN', 'acceptance', 'not observable: ' + ' · '.join(vague[:2]))
else:
    total = sum(len(s.get('acceptance') or []) for s in screens)
    add('PASS', 'acceptance', f'{total} observable assertions')

# ── 13. HTML ↔ contract ───────────────────────────────────────────
sdir = os.path.join(DIR, 'screens')
files = sorted(os.path.join(sdir, f) for f in os.listdir(sdir)
               if f.endswith('.html')) if os.path.isdir(sdir) else []
if not files:
    add('FAIL', 'render', 'no rendered screens found in screens/')
else:
    strays, unrendered, dead_links, seen_in_html = [], [], [], set()
    for path in files:
        with open(path, encoding='utf-8') as fh:
            html = fh.read()
        base = os.path.basename(path)
        for m in re.finditer(r'data-id="([^"]+)"', html):
            nid = m.group(1)
            seen_in_html.add(nid)
            stripped = re.sub(r'\.(empty|loading|error)$', '', nid)
            if nid not in node_ids and not EXEMPT_ID.search(nid) and stripped not in node_ids:
                strays.append(f'{base}: {nid}')
        for m in re.finditer(r'href="\./([^"#]+\.html)"', html):
            if not os.path.isfile(os.path.join(sdir, m.group(1))):
                dead_links.append(f'{base} → {m.group(1)}')
    for n, s, _ in nodes:
        default_file = ((s.get('states') or {}).get('default') or {}).get('file')
        if not default_file:
            continue
        p = os.path.join(DIR, default_file)
        if not os.path.isfile(p):
            continue
        with open(p, encoding='utf-8') as fh:
            if f'data-id="{n.get("id")}"' not in fh.read():
                unrendered.append(n.get('id'))
    problems = ([f'stray {s}' for s in strays]
                + [f'{u} in contract, not in HTML' for u in unrendered]
                + [f'dead link {d}' for d in dead_links])
    if problems:
        add('FAIL', 'render', f'{plural(len(files), "file")} · ' + trim(problems))
    else:
        add('PASS', 'render', f'{plural(len(files), "file")}, {len(seen_in_html)} ids, '
                              'contract and HTML agree')

# ── 14. placeholder text ──────────────────────────────────────────
PLACEHOLDER = re.compile(
    r'\b(lorem ipsum|dolor sit|TODO|TBD|FIXME|xxx+|placeholder text|your text here)\b', re.I)
hits = []


def scan(text, where):
    for m in PLACEHOLDER.finditer(text):
        hits.append(f'{where}: "{m.group(1)}"')


scan(json.dumps(C), 'screens.json')
for f in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
    if f.endswith('.html'):
        with open(os.path.join(sdir, f), encoding='utf-8') as fh:
            scan(fh.read(), f)
for doc in ('spec.md', 'BUILD.md', 'brief.md', 'inventory.md'):
    p = os.path.join(DIR, doc)
    if os.path.isfile(p):
        with open(p, encoding='utf-8') as fh:
            scan(fh.read(), doc)
if hits:
    add('FAIL', 'copy', f'{plural(len(hits), "undecided string")}: ' + trim(hits))
else:
    add('PASS', 'copy', 'no lorem, no TODOs — every string is a decision')

# ── 15. package completeness ──────────────────────────────────────
need = ['brief.md', 'inventory.md', 'screens.json', 'spec.md', 'BUILD.md',
        'index.html', 'wireframe.css']
missing = [f for f in need if not os.path.isfile(os.path.join(DIR, f))]
if missing:
    add('FAIL', 'package', 'missing ' + ', '.join(missing))
else:
    add('PASS', 'package', f'{len(need)} files, ready for handoff')

# ── report ────────────────────────────────────────────────────────
fails = sum(1 for c in checks if c['level'] == 'FAIL')
warns = sum(1 for c in checks if c['level'] == 'WARN')

if AS_JSON:
    print(json.dumps({'dir': DIR, 'ok': fails == 0, 'fails': fails,
                      'warns': warns, 'checks': checks}, indent=2))
else:
    w = max(len(c['name']) for c in checks)
    print()
    for c in checks:
        print(f'  {c["level"]:<5} {c["name"]:<{w}}  {c["detail"]}')
    print()
    print(f'  {len(checks)} checks · {plural(warns, "warning")} · contract is buildable'
          if fails == 0
          else f'  {plural(fails, "failure")} · do not hand this off yet')
    print()

sys.exit(0 if fails == 0 else 1)
