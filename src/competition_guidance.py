"""Public competition rules shared by all baselines, without Coach policy."""
import json
from pathlib import Path

from dataset_paths import data_root


def fixed_team_size(competition_id, baseline, *, requested=None, rules_root=None):
    """Resolve the experiment roster from one competition-owned field."""
    root = Path(rules_root) if rules_root is not None else data_root() / 'rules'
    path = root / competition_id / 'competition.json'
    if not path.is_file():
        raise ValueError(f'Missing competition roster: {path}')
    team = json.loads(path.read_text(encoding='utf-8-sig')).get('team', {})
    count = team.get('active_default')
    if type(count) is not int or count < 2:
        raise ValueError(f'{competition_id}: team.active_default must be an integer >= 2')
    size = 1 if baseline == 'single_agent' else count
    if requested is not None and requested != size:
        raise ValueError(f'{competition_id}/{baseline} uses a fixed team size of {size}; '
                         f'--team-size {requested} would change the experimental roster')
    return size


def competition_guidance(manifest, config, *, rules_root=None):
    root = Path(rules_root) if rules_root is not None else data_root() / 'rules'
    path = root / manifest.competition_id / 'competition.json'
    if path.is_file():
        raw = json.loads(path.read_text(encoding='utf-8-sig'))
        # No collaboration.json, evaluator instructions, gold or reference assets.
        fields = ('competition_id', 'team', 'execution', 'resources', 'deliverable',
                  'human_constraints', 'rules_text')
        public = {key: raw[key] for key in fields if key in raw}
        official = json.dumps(public, ensure_ascii=False, sort_keys=True)
    else:
        official = 'No competition.json is available; do not invent official constraints.'
    runtime = {
        'baseline': config.system_variant,
        'active_agents': config.team_size,
        'max_turns': config.max_turns,
        'max_api_calls': config.max_api_calls,
        'max_tokens': config.max_tokens,
        'max_simulated_minutes': config.max_simulated_minutes,
        'minutes_per_turn': config.minutes_per_turn,
        'task_count': len(manifest.tasks),
        'tasks': [{'task_id': task.task_id, 'max_score': task.max_score} for task in manifest.tasks],
    }
    return ('OFFICIAL COMPETITION RULES (shared by every baseline)\n' + official
            + '\nBENCHMARK ADAPTATION (actual settings for this run)\n'
            + json.dumps(runtime, ensure_ascii=False, sort_keys=True)
            + '\nOfficial team sizes, ages, round lengths and question counts describe the human contest. '
            'This benchmark uses the active-agent count, task list and budgets above; '
            'a single_agent run has one contestant and no hidden teammates. '
            'Do not create extra questions or play other rounds mentioned in the official context. '
            'Simulated minutes and turn limits are not measured wall-clock contest time. '
            'Listed task max_score values are benchmark scoring limits, not a claim of official historical weights. '
            'Follow the available action interface and the explicit submission instructions for this run. '
            'These shared rules do not add Coach, memory or review requirements.')
