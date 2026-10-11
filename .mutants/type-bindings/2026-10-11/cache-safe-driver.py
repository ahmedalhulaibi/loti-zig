from pathlib import Path
import hashlib
import json
import subprocess

root = Path.cwd()
directory = root / '.mutants/type-bindings/2026-10-11'
directory.mkdir(parents=True, exist_ok=True)
paths = ['tools/reference_map.py', 'conversion/reference-map.json']
original = {n: Path(n).read_bytes() for n in paths}
core = json.loads(Path('conversion/type-binding-spec-sha256.json').read_text())
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest() == h for n, h in core['source_sha256'].items())
variants = [
    ('wrapper-is-kernel-extern', 'Native auto-layout SDK owner with fd/sq/cq, not a kernel extern record or a liburing object to cast or byte-copy.', 'Kernel extern owner with fd/sq/cq, compatible with liburing objects to cast or byte-copy.'),
    ('offset-record-holds-pointers', 'head/tail/cqes are byte offsets into the chosen CQ mapping, not pointers or the native CompletionQueue object.', 'head/tail/cqes are absolute pointers; use them as the native CompletionQueue object.'),
    ('mixed-catalog-is-submitted', 'INPUT batch intentionally unsubmitted;', 'INPUT batch submitted to execute all33 operations;'),
    ('read-iovec-is-const', 'Read iovec.base is mutable bytes; write iovec_const.base is const bytes;', 'Read iovec.base is const bytes; write iovec_const.base is mutable bytes;'),
    ('splice-minus-one-is-pointer', 'C signed64 offset values are encoded as u64 SQE bit patterns here, not pointers.', 'C signed64 offsets are passed as borrowed loff_t pointers, not u64 SQE bit patterns.'),
    ('mode-widths-collapsed', 'Do not equate mode_t width with the u16 Statx output field or u64 OpenHow field merely because all carry mode bits;', 'mode_t, Statx.mode and OpenHow.mode are the same u16 layout and may be interchanged;'),
    ('raw-msghdr-is-libc-portable', 'Raw Linux iovlen/controllen are usize here; POSIX/musl header fields need not share those widths.', 'Raw Linux iovlen/controllen match every POSIX/musl header layout; no native width distinction is needed.'),
    ('kernel-mask-is-libc-128-bytes', '8-byte current x86_64 kernel representation, not glibc/musl1024-bit', '128-byte current x86_64 kernel representation, identical to glibc/musl1024-bit'),
    ('size-t-is-sqe-byte-count', 'SQE.len is u32 and opcode-specific:scalar byte length versus vector count.', 'SQE.len is usize and always a scalar byte length, including vector operations.'),
    ('connect-length-is-output', 'CONNECT borrows peer input and takes length by value, while ACCEPT uses optional address/length outputs.', 'CONNECT borrows a listener output and a length pointer, exactly like ACCEPT address/length outputs.'),
    ('accept-length-is-value', 'Initialize ACCEPT capacity and retain its pointer/output storage through CQE;', 'Pass ACCEPT length as an input value; its output storage and capacity need not remain alive through CQE;'),
    ('statx-return-mask-ignored', 'check returned mask before reading fields', 'ignore returned mask and read all fields as initialized'),
    ('open-how-loan-ends-at-preparation', 'Keep how/path storage through the OPENAT2 CQE;', 'Release how/path storage immediately after OPENAT2 preparation;'),
]
runner = "import unittest,json;r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests.test_type_bindings'));print(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)}));raise SystemExit(0 if r.wasSuccessful() else 1)"
report = {'scope': 'Thirteen syntax-valid binding-producer scope/representation variants pass generation/freshness but fail whole19-row contracts; current-target reflection remains positive. No installed-native mutation, whole-port/architecture/kernel or independent acceptance.', 'mutants': [], 'source_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in original.items()}}

def restore():
    for name, data in original.items():
        Path(name).write_bytes(data)

def command(args, name):
    # Equal-length/same-second producer edits can otherwise reuse stale code.
    for path in (root / 'tools/__pycache__').glob('reference_map.*.pyc'):
        path.unlink()
    result = subprocess.run(args, capture_output=True, timeout=60)
    (directory / name).write_bytes(result.stdout + result.stderr)
    return result

try:
    for identity, old, new in variants:
        restore()
        text = original['tools/reference_map.py'].decode()
        assert text.count(old) == 1, (identity, text.count(old))
        Path('tools/reference_map.py').write_text(text.replace(old, new))
        assert command(['python3', '-m', 'py_compile', 'tools/reference_map.py'], identity + '-syntax.log').returncode == 0
        assert command(['python3', 'tools/reference_map.py'], identity + '-generate.log').returncode == 0
        assert command(['python3', 'tools/reference_map.py', '--check'], identity + '-freshness.log').returncode == 0
        result = command([str(root / '.venv/bin/python'), '-c', runner], identity + '-test.log')
        outcome = json.loads(result.stdout)
        assert result.returncode == 1 and outcome == {'tests': 2, 'failures': 2, 'errors': 0, 'skips': 0}, (identity, outcome)
        report['mutants'].append({'id': identity, 'kind': 'binding-producer', 'status': 'killed', 'syntax_valid': True, 'generation_passed': True, 'freshness_passed': True, **outcome})
        print(identity, outcome, flush=True)
finally:
    restore()
    assert command(['python3', 'tools/reference_map.py', '--check'], 'restored-freshness.log').returncode == 0
    assert command([str(root / '.venv/bin/python'), '-m', 'unittest', 'tests.test_type_bindings', 'tests.test_reference_probe_types', 'tests.test_reference'], 'restored-test.log').returncode == 0
    assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest() == h for n, h in core['source_sha256'].items())
    report['restored_source_sha256'] = {n: hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in paths}
    assert report['restored_source_sha256'] == report['source_sha256']
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    Path('conversion/mutation-type-bindings.json').write_text(json.dumps(report, indent=2) + '\n')
print('13 producer kills; exact producer/map/core restoration; eleven-test baseline', flush=True)
