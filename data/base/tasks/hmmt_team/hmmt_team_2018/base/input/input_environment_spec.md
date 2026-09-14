# Environment

## Roster

```json
{
  "active_min": 6,
  "active_default": 8,
  "active_max": 8,
  "roster_max": 8,
  "range_basis": "mixed_or_unresolved",
  "official_roster_note": "November teams have 4–6 students and February teams have 6–8; archived rows must select their season when known.",
  "collaboration": "All members of one team work together on the Team Round.",
  "range_basis_detail": "season_variant"
}
```

## Allowed tools

```json
[
  "query_rules"
]
```

## Resources

```json
{
  "internet": "forbidden",
  "calculator": "forbidden",
  "code_execution": "forbidden",
  "paper_pencil": "allowed",
  "provided_materials_only": true,
  "outside_communication": "forbidden"
}
```

## Official execution facts

```json
{
  "official_minutes": 60,
  "required_selectors": [
    "season"
  ],
  "season_variants": {
    "nov": {
      "team_size": 6,
      "answer_style": "short_answer"
    },
    "feb": {
      "team_size": 8,
      "answer_style": "proof",
      "partial_credit": true
    }
  }
}
```

## Deliverable

```json
{
  "answer_format": "One shared numbered answer/proof packet.",
  "shared": true,
  "mime_types": [
    "text/plain",
    "application/pdf"
  ],
  "task_types": [
    "team_contest"
  ],
  "official_deliverable": "answer_or_proof_packet"
}
```

