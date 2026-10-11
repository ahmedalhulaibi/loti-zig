from collections import Counter
from pathlib import Path
from typing import Any, Callable, ContextManager, cast
import json,sys,unittest
from hypothesis.statistics import collector
root=Path.cwd();sys.path.insert(0,str(root));statistics=[]
def record(value):
 phases={}
 for name in ('reuse-phase','generate-phase','shrink-phase'):
  if name in value:
   counts=Counter(case['status'] for case in value[name]['test-cases'])
   phases[name]={status:counts[status] for status in ('valid','interesting','invalid','overrun')}
 statistics.append({'test':'tests.test_reference.ReferenceContracts.test_nonblocking_completion_capacities_follow_queue_model','phases':phases,'stopped_because':value['stopped-because']})
names=['tests.test_reference.ReferenceContracts.test_mapping_sizes_dontfork_and_actual_raw_read','tests.test_reference.ReferenceContracts.test_copy_and_manual_ack_are_distinct_and_deadline_really_expires','tests.test_reference.ReferenceContracts.test_nonblocking_completion_capacities_follow_queue_model','tests.test_reference.ReferenceContracts.test_completion_rejects_invalid_capacity_plans','tests.test_signals','tests.test_ordinary_signals','tests.test_mapping_failures','tests.test_provided_buffer_zero.ProvidedBufferZeroContracts.test_literal_and_invalid_modes_keep_the_default_contract']
scoped_collector=cast(Callable[[Callable[[dict[str, Any]], None]], ContextManager[None]],collector.with_value)
with scoped_collector(record):
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
assert result.wasSuccessful() and result.testsRun==12 and not result.skipped
assert len(statistics)==1 and statistics[0]['phases']['generate-phase']['valid']==400
Path('/tmp/loti-setup-completion-purpose-tests.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'selected_tests':names,'property_statistics':statistics},indent=2)+'\n')
print('12 selected contracts passed;one attributed property x400 generated valid cases;full99 receipt not overwritten')
