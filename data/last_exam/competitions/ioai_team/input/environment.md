# Environment

## Roster

```json
{
  "active_min": 4,
  "active_default": 4,
  "active_max": 4,
  "collaboration": "Collaborate only within the team under contest rules.",
  "range_basis": "source_record"
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
  "policy": "Selected edition's attached task_contract.json and original task PDF.",
  "internet": "edition_and_task_specific",
  "calculator": "edition_specific_item_policy",
  "code_execution": "edition_specific_environment",
  "provided_materials_only": null,
  "provided_materials_only_scope": "No universal restriction; 2024 expressly permits some external tools and artist images."
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "rules_edition": "selected_historical_task",
  "required_selectors": [
    "problem_id",
    "year",
    "task_contract"
  ],
  "official_minutes_by_year": {
    "2024": 240,
    "2025": null
  }
}
```

## Deliverable

```json
{
  "shared": true,
  "task_types": [
    "team_challenge"
  ],
  "official_deliverable": "edition_specific_task_artifacts",
  "answer_format": "Follow the selected task_contract.json; media/program artifacts and their required documentation are not interchangeable.",
  "mime_types": [
    "application/octet-stream"
  ],
  "official_mime_types": null,
  "by_problem_id": {
    "ioai_team_2024_practical": "cover_image_and_music_video_with_process_documentation",
    "ioai_team_2025_factory": "robot_control_program_for_factory_navigation_and_manipulation"
  }
}
```

