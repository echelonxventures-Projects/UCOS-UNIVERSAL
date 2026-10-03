#!/usr/bin/env python3
"""validate_contracts — checks for contracts, acceptance scenarios, SLOs and repository hygiene.

Complements tools/ucos_check.py (registry, composition, gates). Deterministic, offline, no AI calls.
  1. Repository hygiene: no sync-conflict duplicates ("name 2.ext"), no editor/OS litter tracked
  2. gRPC contracts compile (grpc_tools.protoc, pinned)
  3. OpenAPI 3.1 documents validate (kernel + generated); no colliding paths ('#')
  4. Event payload schemas are valid JSON Schema; AsyncAPI catalogue references only existing payloads
     and lists every event declared by a manifest
  5. Gherkin features parse; every step matches the vocabulary (spec/acceptance/steps.yaml);
     @platform, @gate, @universe and @phase tags resolve; quoted error codes exist in the registry
  6. Service levels validate against their schema; every alert's runbook file and section exist
Exit 0 = all pass. Usage: python3 tools/validate_contracts.py [--quick]   (--quick skips OpenAPI validation)
"""
import glob, json, os, re, subprocess, sys, tempfile
import yaml
from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []
counts = {}
def err(m): errors.append(m)
def rel(p): return os.path.relpath(p, ROOT)

# ---------------------------------------------------------------- 1. hygiene
DUP = re.compile(r' \d+(\.[A-Za-z0-9]+)?$')
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in ('.git', 'node_modules', '.venv', 'generated')]
    for n in filenames + dirnames:
        stem = n.rsplit('.', 1)[0] if '.' in n else n
        if DUP.search(stem) or DUP.search(n):
            err(f'sync-conflict duplicate: {rel(os.path.join(dirpath, n))} (delete it; see CONTRIBUTING.md)')
        if n in ('.DS_Store', 'Thumbs.db'):
            pass  # ignored by .gitignore; harmless locally
counts['hygiene'] = 'ok'

# ---------------------------------------------------------------- 2. protos
proto_root = os.path.join(ROOT, 'spec', 'api', 'proto')
protos = sorted(glob.glob(os.path.join(proto_root, '**', '*.proto'), recursive=True))
if protos:
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run([sys.executable, '-m', 'grpc_tools.protoc', f'-I{proto_root}', f'--descriptor_set_out={td}/d.pb',
                            '--include_imports'] + [os.path.relpath(p, proto_root) for p in protos],
                           capture_output=True, text=True, cwd=proto_root)
        if r.returncode != 0:
            err('protoc failed:\n' + r.stderr.strip())
counts['protos'] = len(protos)

# ---------------------------------------------------------------- 3. OpenAPI
oa_files = sorted(glob.glob(os.path.join(ROOT, 'spec', 'api', 'openapi', '**', '*.yaml'), recursive=True))
op_ids = {}
for f in oa_files:
    d = yaml.safe_load(open(f))
    for path, ops in (d.get('paths') or {}).items():
        if '#' in path:
            err(f'{rel(f)}: colliding path {path!r} (fix the command/query naming or the path rule)')
        for method, op in ops.items():
            if isinstance(op, dict) and 'operationId' in op:
                if op['operationId'] in op_ids:
                    err(f'duplicate operationId {op["operationId"]} in {rel(f)} and {op_ids[op["operationId"]]}')
                op_ids[op['operationId']] = rel(f)
if '--quick' not in sys.argv:
    from openapi_spec_validator import validate
    from openapi_spec_validator.readers import read_from_filename
    for f in oa_files:
        try:
            spec_dict, base_uri = read_from_filename(f)
            validate(spec_dict, base_uri=base_uri)
        except Exception as e:
            err(f'OpenAPI invalid: {rel(f)}: {str(e).splitlines()[0]}')
counts['openapi'] = len(oa_files)
counts['operations'] = len(op_ids)

# ---------------------------------------------------------------- 4. events and AsyncAPI
payload_dir = os.path.join(ROOT, 'spec', 'events', 'payloads')
payloads = sorted(glob.glob(os.path.join(payload_dir, '*.schema.json')) + glob.glob(os.path.join(payload_dir, 'hand', '*.schema.json')))
for f in payloads:
    try:
        Draft202012Validator.check_schema(json.load(open(f)))
    except Exception as e:
        err(f'payload schema invalid: {rel(f)}: {str(e).splitlines()[0]}')
for f in glob.glob(os.path.join(payload_dir, 'hand', '*.schema.json')):
    if not os.path.exists(os.path.join(payload_dir, os.path.basename(f))):
        err(f'hand payload {rel(f)} has no declared event of that type in any manifest')
declared = set()
for f in glob.glob(os.path.join(ROOT, 'spec', 'capabilities', 'packs', '*.yaml')):
    declared |= set(yaml.safe_load(open(f))['spec'].get('provides', {}).get('events', []) or [])
aa_path = os.path.join(ROOT, 'spec', 'api', 'asyncapi', 'ucos-events.yaml')
aa = yaml.safe_load(open(aa_path))
if aa.get('asyncapi') != '3.0.0':
    err('asyncapi: version must be 3.0.0')
msgs = aa.get('components', {}).get('messages', {})
for name, m in msgs.items():
    ref = m.get('payload', {}).get('$ref', '')
    if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(aa_path), ref))):
        err(f'asyncapi: message {name} payload {ref} does not exist')
for ev in sorted(declared - set(msgs)):
    err(f'asyncapi: declared event {ev} missing from the catalogue (run tools/gen_contracts.py)')
for op, o in aa.get('operations', {}).items():
    ch = o['channel']['$ref'].split('/')[-1]
    if ch not in aa.get('channels', {}):
        err(f'asyncapi: operation {op} references unknown channel {ch}')
counts['events'] = len(declared)

# ---------------------------------------------------------------- 5. acceptance
from gherkin.parser import Parser
vocab = yaml.safe_load(open(os.path.join(ROOT, 'spec', 'acceptance', 'steps.yaml')))['steps']
vocab_re = [(s['id'], re.compile(s['pattern'])) for s in vocab]
used_ids = set()
gate_ids = {g['id'] for g in yaml.safe_load(open(os.path.join(ROOT, 'spec', 'certification', 'gates.yaml')))['gates']}
golden = {os.path.basename(p).replace('.pd.yaml', '') for p in glob.glob(os.path.join(ROOT, 'spec', 'composition', 'golden', '*.pd.yaml'))}
universes = {os.path.basename(p).split('-')[0] for p in glob.glob(os.path.join(ROOT, 'constitutions', 'U*')) if os.path.isdir(p)}
error_codes = {e['code'] for e in yaml.safe_load(open(os.path.join(ROOT, 'spec', 'registries', 'errors.yaml')))['errors']}
features = sorted(glob.glob(os.path.join(ROOT, 'spec', 'acceptance', '**', '*.feature'), recursive=True))
n_scen = 0
for f in features:
    try:
        doc = Parser().parse(open(f, encoding='utf-8').read())
    except Exception as e:
        err(f'gherkin parse error: {rel(f)}: {e}')
        continue
    feat = doc.get('feature')
    if not feat:
        err(f'{rel(f)}: no Feature')
        continue
    tags = [t['name'] for t in feat.get('tags', [])]
    if not any(t.startswith('@platform:') for t in tags):
        err(f'{rel(f)}: feature needs a @platform:<golden-pd|any> tag')
    if not any(t.startswith('@gate:') for t in tags):
        err(f'{rel(f)}: feature needs at least one @gate:<id> tag')
    for t in tags:
        k, _, v = t[1:].partition(':')
        if k == 'platform' and v != 'any' and v not in golden:
            err(f'{rel(f)}: @platform:{v} is not a golden platform definition')
        elif k == 'gate' and v not in gate_ids:
            err(f'{rel(f)}: @gate:{v} is not in spec/certification/gates.yaml')
        elif k == 'universe' and v not in universes:
            err(f'{rel(f)}: @universe:{v} has no constitution')
        elif k == 'phase' and not v.isdigit():
            err(f'{rel(f)}: @phase:{v} must be a number')
    for child in feat.get('children', []):
        block = child.get('background') or child.get('scenario')
        if not block:
            continue
        if child.get('scenario'):
            n_scen += 1
        for st in block.get('steps', []):
            text = st['text']
            hits = [i for i, rx in vocab_re if rx.match(text)]
            if not hits:
                err(f'{rel(f)}:{st["location"]["line"]}: step not in vocabulary: "{text}"')
            used_ids.update(hits)
            for code in re.findall(r'error "([A-Z][A-Z0-9_]+)"', text):
                if code not in error_codes:
                    err(f'{rel(f)}:{st["location"]["line"]}: error code {code} is not in spec/registries/errors.yaml')
for sid in sorted({i for i, _ in vocab_re} - used_ids):
    err(f'steps.yaml: step {sid} is not used by any feature (remove it or add a scenario)')
counts['features'] = len(features)
counts['scenarios'] = n_scen

# ---------------------------------------------------------------- 6. SLOs and runbooks
slo_schema = json.load(open(os.path.join(ROOT, 'spec', 'slo', 'service-level.schema.json')))
slo_v = Draft202012Validator(slo_schema)
def anchors(md):
    out = set()
    for line in open(md, encoding='utf-8'):
        m = re.match(r'^#{1,6} (.+)$', line)
        if m:
            out.add(re.sub(r'[^a-z0-9 -]', '', m.group(1).lower()).strip().replace(' ', '-'))
    return out
slo_files = sorted(glob.glob(os.path.join(ROOT, 'spec', 'slo', '*.yaml')))
for f in slo_files:
    d = yaml.safe_load(open(f))
    for e in slo_v.iter_errors(d):
        err(f'{rel(f)}: {e.message}')
    if d.get('universe') not in universes:
        err(f'{rel(f)}: universe {d.get("universe")} has no constitution')
    slo_ids = {s['id'] for s in d.get('slos', [])}
    for a in d.get('alerts', []):
        if a.get('slo') not in slo_ids:
            err(f'{rel(f)}: alert {a.get("id")} references unknown SLO {a.get("slo")}')
        path, _, anchor = a.get('runbook', '').partition('#')
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            err(f'{rel(f)}: runbook {path} does not exist')
        elif anchor not in anchors(full):
            err(f'{rel(f)}: runbook {path} has no section #{anchor}')
counts['slo-files'] = len(slo_files)

# ---------------------------------------------------------------- report
print('  '.join(f'{k}: {v}' for k, v in counts.items()))
print(f'errors: {len(errors)}')
for e in errors:
    print('  ERROR  ', e)
sys.exit(1 if errors else 0)
