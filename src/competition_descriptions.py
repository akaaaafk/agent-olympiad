"""Contest-format descriptions shown to every baseline as COMPETITION FORMAT.

Descriptions state the task format or tool interface only. They must never
restate rule-card content, because plain baselines run with rule cards off.
"""
from __future__ import annotations

COMPETITION_DESCRIPTIONS = {
    "arml_local": (
        "ARML local mathematics team rounds: solve a numbered set of contest "
        "problems and submit one shared answer sheet."
    ),
    "arml_national_team": (
        "ARML national team mathematics rounds: teammates divide a difficult "
        "numbered problem set and combine answers on one sheet."
    ),
    "arml_national_power": (
        "ARML National Power Round: a long collaborative proof / exploration "
        "packet. Produce a clear written solution with justifications; partial "
        "credit is rubric-based when an exact answer key is unavailable."
    ),
    "arml_power": (
        "ARML Power Contest (mail-in): collaborative multi-part proof packets. "
        "Write structured solutions with reasoning; exact short-answer keys may "
        "be unavailable and grading may be unsupported until a rubric judge runs."
    ),
    "science_bowl": (
        "Science Bowl toss-up and bonus questions across scientific subjects, "
        "answered directly with a short choice, term, or value."
    ),
    "qanta": (
        "Academic quiz-bowl questions: identify the requested person, place, "
        "work, event, or concept from progressively specific clues."
    ),
    "mystery_hunt": (
        "MIT Mystery Hunt-style puzzles: infer the puzzle mechanism and extract "
        "a final answer word or phrase."
    ),
    "history_olympiad": (
        "History Bowl/Olympiad packets containing many numbered history toss-up "
        "and bonus questions that require concise factual answers."
    ),
    "purple_comet": (
        "Purple Comet online team mathematics: solve a timed numbered set for "
        "the middle- or high-school division and submit short final answers."
    ),
    "hmmt_guts": (
        "HMMT Guts Round: a fast team mathematics contest with a long numbered "
        "packet (36 questions in the 2024 case); prioritize broad answer-sheet "
        "coverage and preserve every solved numbered answer."
    ),
    "wmtc": (
        "World Mathematics Team Championship team round: solve 14 linked or "
        "standalone numbered mathematics questions on one shared answer sheet."
    ),
}

# Tool-interface description: where the challenge lives and how a flag counts.
CTF_DESCRIPTION = (
    "Capture-the-flag challenge. Challenge files and any network services exist only in this "
    "task's Docker environment: call start_environment, then inspect_environment for public "
    "files in /workspace and service targets, and execute_environment_command to analyze them. "
    "The flag must be recovered from the environment and is graded by exact string match."
)
# Submission semantics follow each benchmark's reference harness.
CTF_SUBMISSION = {
    "nyu_ctf_bench": (" Each submit is checked immediately: a wrong flag is reported to the team and the "
                      "challenge stays open; a correct flag ends it."),
    "cybench": " The first submitted flag is final; there is no correctness feedback.",
}
CTF_COMPETITIONS = frozenset(CTF_SUBMISSION)

DEFAULT_DESCRIPTION = "Solve the provided contest task and submit its required deliverable."


def competition_description(competition: str, name: str | None = None) -> str:
    """Curated format text, else the catalog name with the generic instruction."""
    if competition in CTF_COMPETITIONS:
        return CTF_DESCRIPTION + CTF_SUBMISSION[competition]
    if competition in COMPETITION_DESCRIPTIONS:
        return COMPETITION_DESCRIPTIONS[competition]
    return f"{name}: {DEFAULT_DESCRIPTION}" if name else DEFAULT_DESCRIPTION
