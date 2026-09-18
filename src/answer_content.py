"""Reject command-only answer bodies without executing or rewriting their intent.

This is a wire/content boundary check, not an answer-quality or correctness judge.
Quoted examples inside prose and executable source tasks remain legitimate data.
"""
import ast
import json
import re

VERSION = 1
ANSWER_FIELDS = {'work': 'content', 'render_pdf': 'content', 'submit': 'answer'}


def command_names(text: str) -> tuple[str, ...]:
    """Recognize only an entire canonical call/envelope (or batch of calls)."""
    from action_modules import ACTION_REGISTRY

    value = text.strip()
    fence = re.fullmatch(r'```[^\n`]*\n(.*?)\n?```', value, re.S)
    if fence:
        value = fence[1].strip()
    elif value.startswith('`') and value.endswith('`') and '`' not in value[1:-1]:
        value = value[1:-1].strip()
    # A JSON-quoted command is still a command-only payload, not evidence that
    # the operation happened. Never eval model text or infer/run its arguments.
    try:
        decoded = json.loads(value)
    except (ValueError, RecursionError):
        decoded = None
    if isinstance(decoded, str):
        value = decoded.strip()

    def envelope(row):
        if not isinstance(row, dict):
            return ()
        if set(row) == {'tool_calls'} and isinstance(row['tool_calls'], list):
            return batch(row['tool_calls'])
        if ('function' in row and set(row) <= {'function', 'type', 'id'}
                and row.get('type', 'function') == 'function'):
            return envelope(row['function'])
        name = row.get('name')
        if (isinstance(name, str) and name in ACTION_REGISTRY
                and ('arguments' in row or 'input' in row)
                and set(row) <= {'name', 'arguments', 'input', 'type', 'id'}):
            return (name,)
        return ()

    def batch(rows):
        names = [envelope(row) for row in rows]
        return tuple(name for group in names for name in group) if names and all(names) else ()

    if isinstance(decoded, (dict, list)):
        return batch(decoded) if isinstance(decoded, list) else envelope(decoded)
    try:
        tree = ast.parse(value, mode='exec')
    except (SyntaxError, ValueError, RecursionError):
        return ()
    names = []
    for statement in tree.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            return ()
        callee = statement.value.func
        if isinstance(callee, ast.Name):
            name = callee.id
        elif (isinstance(callee, ast.Attribute) and isinstance(callee.value, ast.Name)
              and callee.value.id in {'functions', 'tools'}):
            name = callee.attr
        else:
            return ()
        if name not in ACTION_REGISTRY:
            return ()
        names.append(name)
    return tuple(names)


def content_error(content) -> str | None:
    names = command_names(content) if isinstance(content, str) else ()
    if not names:
        return None
    return (
        'Answer body contains only a tool command (' + ', '.join(dict.fromkeys(names))
        + '), not contestant work. Nothing was saved, rendered, submitted or executed. '
        'Select an available tool through the action interface if you need an operation, '
        'then wait for its result before writing the answer. Do not copy a command into '
        'work.content, render_pdf.content or submit.answer, and do not invent its result.'
    )


def action_content_error(name, arguments, metadata) -> str | None:
    field = ANSWER_FIELDS.get(name)
    if field is None:
        return None
    task_id = arguments.get('problem_id') or metadata.get('task_id')
    if name != 'render_pdf' and task_id in metadata.get('source_task_ids', ()):
        return None
    return content_error(arguments.get(field))
