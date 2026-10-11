from pathlib import Path
import hashlib
import json
import subprocess

root = Path.cwd()
directory = root / '.mutants/probe-type/2026-10-10'
directory.mkdir(parents=True, exist_ok=True)
paths = ['tools/reference_map.py', 'conversion/reference-map.json']
original = {name: Path(name).read_bytes() for name in paths}
core = json.loads(Path('conversion/probe-type-spec-sha256.json').read_text())
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest() == h for n, h in core['source_sha256'].items())
variants = [
    ('unused-catalog-primary', 'example = "examples/probe.zig"', 'example = PREPARE', 2),
    ('flexible-array-heap-ownership',
     'Owned fixed-capacity native value, not a flexible-array allocation or foreign pointer.',
     'Heap-allocated flexible-array native pointer; the caller must free it.', 1),
    ('allocated-capacity-is-reported-count',
     'ops holds256 native entries, but only reported entries are valid.',
     'ops_len is the allocated capacity256; all entries are always valid.', 1),
    ('entry-any-nonzero-flag-supported',
     'Entry is_supported tests IO_URING_OP_SUPPORTED bit0;',
     'Entry is_supported accepts any nonzero flags;', 1),
]
runner = "import unittest,json;r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests.test_reference_probe_types'));print(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)}));raise SystemExit(0 if r.wasSuccessful() else 1)"
report = {'scope': 'Four syntax-valid probe-type binding-producer variants pass generation/freshness but fail whole two-row consumer/ownership/bounds/flag contracts. Not native/kernel, all type/binding or independent acceptance.',
          'mutants': [], 'source_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in original.items()}}

def restore():
    for name, data in original.items():
        Path(name).write_bytes(data)

def command(args, name):
    # Owned cache only: same-second equal-length variants must not leak bytecode.
    for cached in (root / 'tools/__pycache__').glob('reference_map.*.pyc'):
        cached.unlink()
    result = subprocess.run(args, capture_output=True, timeout=30)
    (directory / name).write_bytes(result.stdout + result.stderr)
    return result

try:
    for identity, old, new, count in variants:
        restore()
        text = original['tools/reference_map.py'].decode()
        assert text.count(old) == count, (identity, text.count(old))
        Path('tools/reference_map.py').write_text(text.replace(old, new))
        assert command([str(root / '.venv/bin/python'), '-m', 'py_compile', 'tools/reference_map.py'], identity + '-compile.log').returncode == 0
        assert command(['python3', 'tools/reference_map.py'], identity + '-generate.log').returncode == 0
        assert command(['python3', 'tools/reference_map.py', '--check'], identity + '-freshness.log').returncode == 0
        result = command([str(root / '.venv/bin/python'), '-c', runner], identity + '-test.log')
        outcome = json.loads(result.stdout)
        assert result.returncode == 1 and outcome == {'tests': 1, 'failures': 2, 'errors': 0, 'skips': 0}, (identity, outcome)
        report['mutants'].append({'id': identity, 'kind': 'binding-producer', 'status': 'killed',
                                  'syntax_valid': True, 'generation_passed': True, 'freshness_passed': True, **outcome})
        print(identity, outcome, flush=True)
finally:
    restore()
    assert command(['python3', 'tools/reference_map.py', '--check'], 'restored-freshness.log').returncode == 0
    assert command([str(root / '.venv/bin/python'), '-m', 'unittest',
                    'tests.test_reference_probe_types', 'tests.test_reference_execution_map',
                    'tests.test_mapping_bindings', 'tests.test_reference_semantics',
                    'tests.test_examples.ExampleContracts.test_probe_emits_kernel_report_for_every_known_opcode',
                    'tests.test_examples.ExampleContracts.test_probe_rejects_invalid_arguments_and_snapshot_sizes'],
                   'restored-test.log').returncode == 0
    assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest() == h for n, h in core['source_sha256'].items())
    report['restored_source_sha256'] = {n: hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in paths}
    assert report['restored_source_sha256'] == report['source_sha256']
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    Path('conversion/mutation-probe-type.json').write_text(json.dumps(report, indent=2) + '\n')
print('Four producer kills; exact source/generated/core restoration; six-test baseline', flush=True)
