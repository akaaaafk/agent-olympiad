from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.test_competition_tools import sample_arguments, context
from action_modules.competition_tools import BY_COMPETITION
from competition_tool_runtime import execute_preparation_tool

for cid in ('ijso_practical', 'iypt', 'itym', 'ichto'):
    profile = BY_COMPETITION[cid]
    result = execute_preparation_tool(profile.name, sample_arguments(profile), context(cid))
    assert result['format_ok'], result
print('PASS: four affected preparation tools execute.')
