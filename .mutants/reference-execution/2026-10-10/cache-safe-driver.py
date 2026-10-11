from pathlib import Path
import subprocess,json,hashlib
root=Path.cwd();directory=root/'.mutants/reference-execution/2026-10-10';directory.mkdir(parents=True,exist_ok=True)
paths=['tools/reference_map.py','conversion/reference-map.json'];original={n:Path(n).read_bytes() for n in paths};core=json.loads(Path('conversion/reference-execution-spec-sha256.json').read_text());assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in core['source_sha256'].items())
variants=[
('nop-construction-only','scope = "constructed and submitted; tagged result-zero NOP CQEs, copied/manual consumption, full eight-slot SQ rejection and nonblocking CQ capacity/physical wrap checked; sequential single producer, not u32 counter wrap or concurrent/SQPOLL assurance"','scope = "executed SQE construction; mixed requests intentionally not submitted"'),
('registered-buffer-index-is-file-slot','Registered-buffer index goes in buf_index, not the fixed-file table or IOSQE_FIXED_FILE.','Registered-buffer index selects a fixed-file table slot with IOSQE_FIXED_FILE.'),
('iovec-descriptor-claimed-kernel-borrow','SQE stores that byte address/length, not a borrowed iovec pointer.','SQE stores the iovec pointer borrowed by the kernel through completion.'),
('recv-result-claimed-capacity','positive stream result is initialized byte count, not requested capacity','positive stream result is requested capacity, not initialized byte count'),
]
runner="import unittest,json;r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests.test_reference_execution_map'));print(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)}));raise SystemExit(0 if r.wasSuccessful() else 1)"
report={'scope':'Four syntax-valid binding-producer variants pass generation/freshness but fail whole semantic/execution-reference fixtures. Not native/kernel or whole99-binding/independent acceptance.','mutants':[],'source_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in original.items()}}
def restore():
 for n,b in original.items():Path(n).write_bytes(b)
def command(args,name):
 for cached in (root/'tools/__pycache__').glob('reference_map.*.pyc'):cached.unlink()
 r=subprocess.run(args,capture_output=True,timeout=20);directory.joinpath(name).write_bytes(r.stdout+r.stderr);return r
try:
 for id,old,new in variants:
  restore();text=original['tools/reference_map.py'].decode();assert text.count(old)==1,(id,text.count(old));Path('tools/reference_map.py').write_text(text.replace(old,new));assert command([str(root/'.venv/bin/python'),'-m','py_compile','tools/reference_map.py'],id+'-compile.log').returncode==0
  assert command(['python3','tools/reference_map.py'],id+'-generate.log').returncode==0
  assert command(['python3','tools/reference_map.py','--check'],id+'-freshness.log').returncode==0
  r=command([str(root/'.venv/bin/python'),'-c',runner],id+'-test.log');o=json.loads(r.stdout);assert r.returncode==1 and o=={'tests':1,'failures':1,'errors':0,'skips':0},(id,o)
  report['mutants'].append({'id':id,'kind':'binding-producer','status':'killed','syntax_valid':True,'generation_passed':True,'freshness_passed':True,**o});print(id,o,flush=True)
finally:
 restore();assert command(['python3','tools/reference_map.py','--check'],'restored-freshness.log').returncode==0
 assert command([str(root/'.venv/bin/python'),'-m','unittest','tests.test_reference_execution_map','tests.test_reference'],'restored-test.log').returncode==0
 assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in core['source_sha256'].items());report['restored_source_sha256']={n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in paths};assert report['restored_source_sha256']==report['source_sha256'];directory.joinpath('report.json').write_text(json.dumps(report,indent=2)+'\n');Path('conversion/mutation-reference-execution.json').write_text(json.dumps(report,indent=2)+'\n')
print('Four producer kills; exact producer/generated/core restoration; nine-test baseline',flush=True)
