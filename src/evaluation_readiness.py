"""One readiness contract for catalog registration and execution preflight."""
READY_STATUSES = {'ready', 'ready_with_limitations', 'remote_judge_ready'}


def readiness_blockers(rows):
    return [f"Record not ready: {r['problem_id']} ({(r.get('evaluation') or {}).get('status', 'missing')})"
            for r in rows if (r.get('evaluation') or {}).get('status') not in READY_STATUSES
            or not (r.get('evaluation') or {}).get('evaluator_id')]


def require_ready(rows):
    blockers = readiness_blockers(rows)
    if blockers:
        raise ValueError('; '.join(blockers))
