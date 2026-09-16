"""Bounded 504 retries. Never executes tools or guesses missing usage."""
import math
import time


def create_with_retry(create, payload, *, max_attempts=3, observe=None, sleep=time.sleep):
    attempts = []
    for number in range(1, max_attempts + 1):
        start = time.monotonic()
        try:
            response = create(**payload).model_dump()
        except Exception as exc:
            status = getattr(exc, 'status_code', None)
            body = getattr(exc, 'body', None)
            delay = 120.0
            candidates = [body.get('retry_after') if isinstance(body, dict) else None]
            http = getattr(exc, 'response', None)
            if http is not None:
                candidates.append(http.headers.get('retry-after'))
            for value in candidates:
                try:
                    parsed = float(value)
                    if math.isfinite(parsed):
                        delay = max(delay, parsed)
                except (TypeError, ValueError):
                    pass
            retry = status == 504 and number < max_attempts
            row = dict(attempt=number, status=status, error_type=type(exc).__name__,
                       elapsed_seconds=time.monotonic()-start, usage_unknown=True,
                       retry_delay_seconds=delay if retry else None)
            attempts.append(row)
            if observe:
                observe(row)
            if not retry:
                exc.gateway_attempts = attempts
                raise
            sleep(delay)
        else:
            row = dict(attempt=number, status=200, elapsed_seconds=time.monotonic()-start,
                       usage_unknown=False)
            attempts.append(row)
            if observe:
                observe(row)
            return response, attempts

