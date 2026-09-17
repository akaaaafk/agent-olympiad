"""Deterministic, explicit reference contracts for sets, sequences and ranges."""
import math
import re


def reference_matches(spec, actual):
    if not isinstance(spec, dict):
        raise ValueError('Structured reference requires answer_spec')
    kind = spec['kind']
    text = str(actual).strip().casefold().rstrip('.')
    if kind in {'unordered_set', 'ordered_sequence'}:
        tokens = re.split(r'[\s,;/]+', text.strip('[]{}() '))
        expected = [str(x).casefold() for x in spec['items']]
        if not all(tokens) or len(tokens) != len(expected):
            return False
        return (len(set(tokens)) == len(tokens) and set(tokens) == set(expected)
                if kind == 'unordered_set' else tokens == expected)
    if kind == 'range':
        text = text.replace('\u2013', '-').replace('\u2212', '-')
        number = r'(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?'
        match = re.fullmatch(rf'({number})(?:\s*(?:-|to)\s*({number}))?\s*(.*)', text)
        if not match:
            return False
        unit = ' '.join(match[3].split())
        units = {k.casefold(): v for k, v in spec['units'].items()}
        if unit not in units:
            return False
        values = [float(v) * units[unit] for v in match.group(1, 2) if v is not None]
        if not all(math.isfinite(v) for v in values):
            return False
        low, high = spec['minimum'], spec['maximum']
        if len(values) == 2:
            return math.isclose(values[0], low) and math.isclose(values[1], high)
        return low <= values[0] <= high
    raise ValueError('Unsupported structured reference kind: ' + str(kind))
