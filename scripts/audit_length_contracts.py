"""Offline main/mini configuration matrix, not a live competition evaluation."""
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from artifact_contract import contract_for, delivery_route
from contest_manifest import ContestManifest, ManifestTask
from rules.loader import load_rule_card
from work_content import DRAFT_MAX_CHARS, action_argument_limits, action_argument_limits_by_task, work_char_limit


def cases():
    rows = []
    for label, base in (('data', ROOT/'data'), ('mini_data', ROOT/'data/mini_data')):
        index = json.loads((base/'benchmarks/index.json').read_text(encoding='utf8'))
        for entry in index['olympiads']:
            card = load_rule_card(entry['id'], rules_root=base/'rules', required=True)
            route = delivery_route(card)
            source = card.deliverable.get('official_deliverable') == 'source_code'
            metadata = {'artifact_contract': asdict(contract_for(card))} if route in {'document','slides'} else {}
            task = ManifestTask('q','q',None,'Synthetic boundary fixture from configured delivery route.',
                                'programming' if source else 'general',1,source,{})
            manifest = ContestManifest('length-audit',entry['id'],(task,),metadata)
            limit = work_char_limit(manifest,'q')
            configured = card.simulation.get('open_table_coach', {}).get(
                'contestant_turn_policy', {}).get('max_chars_by_action', {}).get('work')
            expected = (metadata['artifact_contract']['max_source_chars'] if metadata else
                        None if source else max(DRAFT_MAX_CHARS, configured)
                        if type(configured) is int else DRAFT_MAX_CHARS)
            # Native proof limits are loaded from the active data root at runtime.
            # Fail explicitly if this root differs from the catalog being audited.
            assert limit == expected, f'{label}/{entry["id"]}: active work limit differs from selected rules'
            declared = action_argument_limits_by_task(manifest)['q'].get('work',{}).get('content')
            assert limit == declared
            rows.append((dict(dataset=label, competition=entry['id'], delivery_route=route,
                source_task_fixture=source, work_character_limit=limit,
                transport_limits=action_argument_limits(manifest)), manifest))
    return rows


if __name__ == '__main__':
    rows = [row for row, _ in cases()]
    print(json.dumps(dict(scope='configuration-derived representatives; not full task or live model runs',
                         cases=len(rows), competitions=len({r['competition'] for r in rows}),
                         rows=rows), ensure_ascii=False, indent=2))
