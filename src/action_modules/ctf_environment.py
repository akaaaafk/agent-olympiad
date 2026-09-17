"""Session tools for a competition's isolated Docker task workspace."""
from .contracts import ArgumentSpec, make_action, SESSION_ONLY

NAMES = frozenset({'start_environment','reset_environment','inspect_environment','execute_environment_command'})
SPECS = tuple(make_action(name, description, arguments, module='task_specific',
    pack='resources', visibility='private', tool_calls=1, is_tool=True,
    runtimes=SESSION_ONLY) for name,description,arguments in (
    ('start_environment','Start or resume this task Docker environment.',()),
    ('reset_environment','Discard this task workspace and restart its Docker environment.',()),
    ('inspect_environment','Inspect this task containers and network targets.',()),
    ('execute_environment_command','Run a shell command inside this task contestant container only.',
     (ArgumentSpec('command',description='Linux shell command inside /workspace.'),
      ArgumentSpec('timeout',type='integer',description='Timeout in seconds, 1..120.',required=False))),
))
