"""One visibility and provenance boundary for laboratory/chart resources."""
import hashlib
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def resource_matches(value, role):
    return role in re.split(r'[^a-z0-9]+', str(value).lower())


def visible_resources(benchmark, role):
    for asset in benchmark.get('assets') or []:
        if not isinstance(asset, dict) or asset.get('role') != 'agent_visible':
            continue
        label = asset.get('resource_type') or asset.get('path') or ''
        if not resource_matches(label, role):
            continue
        expected = asset.get('sha256')
        if not expected:
            continue
        try:
            path = (REPO_ROOT / str(asset.get('path') or '')).resolve()
            if not path.is_relative_to(REPO_ROOT.resolve()) or not path.is_file():
                continue
            raw = path.read_bytes()
        except (OSError, ValueError):
            continue
        if hashlib.sha256(raw).hexdigest() == expected:
            yield asset, path, raw


def resource_fixtures(benchmark, role):
    return {key: value for key, value in (benchmark.get('tool_fixtures') or {}).items()
            if resource_matches(key, role) and not (
                isinstance(value, dict) and value.get('role', 'agent_visible') != 'agent_visible')}


def has_resource(benchmark, role):
    return bool(resource_fixtures(benchmark, role)) or next(visible_resources(benchmark, role), None) is not None


def resource_text(benchmark, role, selector):
    selector = selector.strip()
    fixtures = resource_fixtures(benchmark, role)
    if selector in fixtures:
        return str(fixtures[selector])[:8000]
    matches = list(visible_resources(benchmark, role))
    if selector and selector != role:
        matches = [item for item in matches if selector in
                   {str(item[0].get('id') or ''), str(item[0].get('name') or ''),
                    str(item[0].get('path') or ''), item[1].name, item[1].stem}]
    if len(matches) == 1:
        return matches[0][2].decode('utf-8', errors='replace')[:8000]
    if selector in ('', role) and role in fixtures:
        return str(fixtures[role])[:8000]
    return None  # Missing/ambiguous selectors never expose an arbitrary file.
