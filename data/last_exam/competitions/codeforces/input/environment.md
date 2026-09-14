# Environment

## Roster

```json
{
  "active_min": 3,
  "active_default": 3,
  "active_max": 3,
  "collaboration": "Three contestants collaborate on one shared programming workstation for a Codeforces problem proxied through VJudge.",
  "coach_role": "open_table_preparation_only_not_a_contestant",
  "coach_during_contest": "no_problem_solving_help_after_opening",
  "co_location": "three_contestants_share_one_team_workstation"
}
```

## Allowed tools

```json
[
  "query_rules",
  "execute_code"
]
```

## Resources

```json
{
  "internet": "forbidden",
  "calculator": "forbidden",
  "code_execution": "shared_workstation_only",
  "paper_pencil": "allowed",
  "unapproved_materials": "forbidden",
  "shared_workstation": true,
  "shared_workstation_count": 1,
  "extra_computers": "forbidden",
  "external_llms_and_search_engines": "forbidden",
  "outside_communication": "forbidden"
}
```

## Official execution facts

```json
{
  "official_minutes": 120,
  "multi_problem_packet": "unavailable",
  "problem_language": "English",
  "allowed_languages": [
    "C++",
    "Python3"
  ],
  "program_io_model": "stdin_to_stdout",
  "problems_independent": true,
  "live_scoreboard": "unavailable",
  "clarification_channel": "unavailable"
}
```

## Deliverable

```json
{
  "answer_format": "Submit a complete stdin/stdout program through submit_code / submit.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "algorithmic_programming"
  ],
  "official_deliverable": "source_code",
  "official_languages": [
    "C++",
    "Python3"
  ],
  "io_model": "stdin_stdout"
}
```

