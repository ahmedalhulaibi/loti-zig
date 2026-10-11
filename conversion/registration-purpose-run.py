import json,sys,unittest
from pathlib import Path
from collections import Counter
from hypothesis.statistics import collector
from typing import Any, Callable, ContextManager, Protocol, cast
root=Path.cwd();sys.path.insert(0,str(root));active: list[str | None] = [None];stats=[]
class StatisticsCollector(Protocol):
 def with_value(self, value: Callable[[dict[str, Any]], None]) -> ContextManager[None]: ...
class Result(unittest.TextTestResult):
 def __init__(self, *args, **kwargs):super().__init__(*args, **kwargs)
 def startTest(self,test):active[0]=test.id();super().startTest(test)
def collect(value):
 phases={}
 for name in ['reuse-phase','generate-phase','shrink-phase']:
  if name in value:
   counts=Counter(item['status'] for item in value[name]['test-cases'])
   phases[name]={status:counts[status] for status in ['valid','interesting','invalid','overrun']}
 stats.append({'test':active[0],'phases':phases,'stopped_because':value['stopped-because']})
names=['tests.test_reference.ReferenceContracts.test_registration_helpers_and_async_notification','tests.test_reference.ReferenceContracts.test_registration_rejects_missing_or_extra_inputs','tests.test_examples.ExampleContracts.test_fixed_buffers_write_and_read_registered_ranges','tests.test_examples.ExampleContracts.test_eventfd_counter_and_completion_are_real','tests.test_examples.ExampleContracts.test_probe_emits_kernel_report_for_every_known_opcode','tests.test_examples.ExampleContracts.test_probe_snapshot_support_respects_both_bounds_and_flag_bit','tests.test_examples.ExampleContracts.test_probe_rejects_invalid_arguments_and_snapshot_sizes','tests.test_reference_probe_types.ProbeTypeBindingContracts.test_probe_header_and_entry_have_whole_native_consumer_contracts']
with cast(StatisticsCollector, collector).with_value(collect):
 result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromNames(names))
assert result.wasSuccessful() and result.testsRun==8 and not result.skipped
assert len(stats)==2 and all(s['phases']['generate-phase']['valid']==400 for s in stats)
Path('/tmp/loti-registration-purpose-tests.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'selected_tests':names,'property_statistics':stats},indent=2)+'\n')
print('8 selected contracts passed;2 attributed properties x400 generated valid cases;full99 receipt not overwritten')
