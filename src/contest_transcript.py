"""Lossless local audit exports, never used as contestant observations."""
from copy import deepcopy
import json
from pathlib import Path


def _row(event):
    row = deepcopy(event)
    payload = row.get('payload') or {}
    message = payload.get('raw_content') or payload.get('content')
    if message is None:
        message = (' | '.join(str(payload[key]) for key in ('outcome', 'reason') if payload.get(key))
                   or json.dumps(payload, ensure_ascii=False))
    row.update(sender=row.get('actor', 'Unknown'), action=row.get('kind', ''), message=message)
    return row


def communication_history(events):
    from tool_registry import DELIBERATION_ACTION_NAMES
    kinds = DELIBERATION_ACTION_NAMES | {'speak', 'direct_message', 'request_review', 'review_answer'}
    return [_row(event) for event in events if event.get('kind') in kinds]


def communication_sidecar(source):
    events = (source.get('memory') or {}).get('events') or []
    rows = [_row(event) for event in events] if events else deepcopy(source.get('chat_history') or [])
    maximum = max([int((source.get('budget') or {}).get('turns_used') or 0)] +
                  [int(row.get('turn') or 0) for row in rows])
    turns = []
    for turn in range(1, maximum + 1):
        indices = [index for index, row in enumerate(rows) if row.get('turn') == turn]
        turns.append({'turn': turn, 'chat_history_indices': indices,
                      'status': 'archived_events' if indices else 'no_archived_events'})
    return {**{key: source.get(key) for key in ('session_id', 'competition_id', 'system_variant', 'protocol_version')},
            'precontest_coach_guidance': source.get('precontest_coach_guidance') or '',
            'scope': 'full_local_archive_including_private_events',
            'event_count': len(rows), 'chat_history': rows, 'turns': turns}


def communication_markdown(sidecar):
    parts = ['# Contest Archive', '', 'Scope: full local archive, including private records.', '']
    brief = sidecar.get('precontest_coach_guidance')
    if brief:
        parts += ['## Turn 0 - Coach', '', brief, '']
    rows = sidecar['chat_history']
    def append_row(row):
        parts.extend([f"### {row.get('sender', row.get('actor', 'Unknown'))}", '',
                      f"{row.get('action', row.get('kind', 'message'))} | {row.get('visibility', 'unspecified')}",
                      '', str(row.get('message', '')), ''])
    for row in rows:
        if not row.get('turn'):
            append_row(row)
    for turn in sidecar['turns']:
        parts += [f"## Turn {turn['turn']}", '']
        if not turn['chat_history_indices']:
            parts += ['No archived events.', '']
        for index in turn['chat_history_indices']:
            append_row(rows[index])
    return '\n'.join(parts)


def write_communication_sidecars(directory, source):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    sidecar = communication_sidecar(source)
    encoded = json.dumps(sidecar, ensure_ascii=False, indent=2)
    markdown = communication_markdown(sidecar)
    names = ['chat'] + (['otc_chat'] if source.get('system_variant') in {'otc', 'vallina_otc'} else [])
    for name in names:
        for suffix, content in (('.json', encoded), ('.md', markdown)):
            path = directory / (name + suffix)
            temporary = path.with_suffix(path.suffix + '.tmp')
            temporary.write_text(content, encoding='utf-8')
            temporary.replace(path)
    return sidecar
