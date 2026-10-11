from pathlib import Path
import hashlib
import json
import subprocess

root = Path.cwd()
directory = root / '.mutants/http-notes/2026-10-11'
directory.mkdir(parents=True, exist_ok=True)
paths = ['conversion/reference-block-disposition.md', 'conversion/line-disposition-verification.json']
original = {name: Path(name).read_bytes() for name in paths}
core = json.loads(Path('conversion/http-note-spec-sha256.json').read_text())
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest() == h for n, h in core['source_sha256'].items())
variants = [
    ('response-body-is-recv-input',
     'binary/empty fixtures are response bodies, not claimed binary/zero-length RECV inputs.',
     'Binary/empty response fixtures prove binary and zero-length RECV inputs.'),
    ('positive-short-send-unverified',
     'P/E; actual remaining prepared SQE ranges/flags and positive-short body SEND CQEs, exact whole TCP response bytes, reset isolation/recovery GET and queried owned socket retirement checked by --observe-send contracts.',
     'P/E; exact HTTP headers/bodies over real TCP; forced partial-send cases remain unverified.'),
    ('sigpipe-and-header-vector-forcing-claimed',
     'Forced header/vector short sends, SIGPIPE delivery and all transports/flags/races/unwind paths remain unverified.',
     'SIGPIPE delivery and all header/vector short sends are verified by these contracts.'),
    ('caller-fragment-is-one-cqe',
     'No per-fragment CQE count, forced short RECV, scalar datagram/multishot or all flags/races/failures assurance.',
     'Each caller fragment is verified to cause exactly one RECV CQE, including forced short reads.'),
]
runner = "import unittest,json;r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests.test_http_note_contracts'));print(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)}));raise SystemExit(0 if r.wasSuccessful() else 1)"
report = {'scope': 'Four structurally valid author-note variants pass complete index generation/freshness but fail the whole two-row meaning contract. Not compiled native mutants, reader-facing source damage or independent/all-note semantic acceptance.',
          'mutants': [], 'source_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in original.items()}}

def restore():
    for name, data in original.items():
        Path(name).write_bytes(data)

def command(args, name):
    result = subprocess.run(args, capture_output=True, timeout=30)
    (directory / name).write_bytes(result.stdout + result.stderr)
    return result

try:
    for identity, old, new in variants:
        restore()
        text = original['conversion/reference-block-disposition.md'].decode()
        assert text.count(old) == 1, (identity, text.count(old))
        changed = text.replace(old, new)
        selected = [line for line in changed.splitlines() if line.startswith('| `ref-liburing/submission.rst:473` |') or line.startswith('| `ref-liburing/submission.rst:493` |')]
        assert len(selected) == 2 and all(len(line.removeprefix('| ').removesuffix(' |').split(' | ')) == 3 for line in selected)
        Path('conversion/reference-block-disposition.md').write_text(changed)
        result = command(['python3', 'tools/check_line_dispositions.py'], identity + '-index-generate.log')
        assert result.returncode == 0 and json.loads(result.stdout) == {'event': 'loti.disposition.written', 'lines': 3618, 'blocks': 128, 'outside_block_lines': 567}
        assert command(['python3', 'tools/check_line_dispositions.py', '--check'], identity + '-index-freshness.log').returncode == 0
        result = command([str(root / '.venv/bin/python'), '-c', runner], identity + '-test.log')
        outcome = json.loads(result.stdout)
        assert result.returncode == 1 and outcome == {'tests': 1, 'failures': 1, 'errors': 0, 'skips': 0}, (identity, outcome)
        report['mutants'].append({'id': identity, 'kind': 'source-prose-author-note', 'status': 'killed',
                                  'table_shape_valid': True, 'index_generation_passed': True, 'index_freshness_passed': True, **outcome})
        print(identity, outcome, flush=True)
finally:
    restore()
    assert command(['python3', 'tools/check_line_dispositions.py', '--check'], 'restored-index.log').returncode == 0
    assert command([str(root / '.venv/bin/python'), '-m', 'unittest', 'tests.test_http_note_contracts', 'tests.test_dispositions',
                    'tests.test_http', 'tests.test_http_send'], 'restored-test.log').returncode == 0
    assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest() == h for n, h in core['source_sha256'].items())
    report['restored_source_sha256'] = {n: hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in paths}
    assert report['restored_source_sha256'] == report['source_sha256']
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    Path('conversion/mutation-http-notes.json').write_text(json.dumps(report, indent=2) + '\n')
print('Four author-note kills; exact note/index/core restoration; nine-test baseline', flush=True)
