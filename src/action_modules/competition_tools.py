"""Competition-owned preparation tools, registered once for both runtimes.

These tools check or assemble contestant-supplied work. They do not grade it,
retrieve solutions, submit it, or claim to simulate an absent live environment.
The rule card must explicitly permit the tool as well as matching its owner.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .contracts import ArgumentSpec, make_action


@dataclass(frozen=True)
class CompetitionTool:
    competition: str
    name: str
    kind: str
    feature: str
    fields: tuple[str, ...]
    limitation: str = "Checks structure and supplied evidence only, not correctness."


# Each row describes the actual selected contest, rather than a domain keyword.
# Related contests reuse implementations, but keep their own output contract.
PROFILES = (
    CompetitionTool("arml_local", "prepare_arml_local_sheet", "answers", "Team Round numbered short answers; expected problem ids come from the supplied packet.", ("problem_ids", "answers")),
    CompetitionTool("arml_national_team", "prepare_arml_team_sheet", "answers", "One national Team Round answer sheet for the selected packet.", ("problem_ids", "answers")),
    CompetitionTool("wmtc", "prepare_wmtc_team_sheet", "answers", "Team Round answers only; preserve the packet's level and numbering.", ("problem_ids", "answers")),
    CompetitionTool("purple_comet", "prepare_purple_comet_answers", "integers", "Non-negative integer answers with exact problem numbering; MS and HS are distinct packets.", ("problem_ids", "answers")),
    CompetitionTool("arml_power", "check_arml_power_proofs", "proofs", "A single numbered proof packet with explicit dependencies between parts.", ("part_ids", "claims", "proofs", "dependencies")),
    CompetitionTool("arml_national_power", "check_arml_national_power_proofs", "proofs", "One national Power solution packet; detect missing references and circular proof dependencies.", ("part_ids", "claims", "proofs", "dependencies")),
    CompetitionTool("pumac_power", "check_pumac_proof_packet", "proofs", "Power proofs must identify earlier-part dependencies; edition-specific anonymity rules still come from the packet.", ("part_ids", "claims", "proofs", "dependencies")),
    CompetitionTool("hmmt_team", "prepare_hmmt_team_packet", "seasonal_answers", "November short answers versus February proofs, selected from the current task's season.", ("problem_ids", "answers", "justifications")),
    CompetitionTool("hmmt_guts", "prepare_guts_set", "guts", "Assemble one November 3-question or February 4-question set using the task's season.", ("problem_ids", "answers"), "Prepares a candidate set; does not unlock later sets, hand in answers, or expose scores."),
    CompetitionTool("fyziklani", "check_physics_answer_units", "quantities", "Physics Brawl numeric answers: preserve values, units, and the caller's unit requirements.", ("quantities", "values", "units", "required_units"), "Checks units and finite numbers; does not simulate progressive series, retries, or scoring."),
    CompetitionTool("icpc", "check_icpc_io_cases", "io_cases", "Stdin/stdout case preparation for the shared-workstation ICPC workflow.", ("case_ids", "inputs", "expected_outputs"), "Detects contradictory duplicate inputs. These are contestant tests, not judge evidence or an Accepted verdict."),
    CompetitionTool("codeforces", "check_codeforces_io_cases", "io_cases", "Prepare explicit stdin/stdout edge cases for the selected Codeforces problem.", ("case_ids", "inputs", "expected_outputs"), "Does not execute source or access hidden tests; use execute_code and submit_code for evaluation."),
    CompetitionTool("iiot", "check_iiot_io_cases", "io_cases", "Prepare deterministic test cases for IIOT's selected language and two-workstation contest.", ("case_ids", "inputs", "expected_outputs"), "Does not acquire either workstation, execute programs, or certify subtask scores."),
    CompetitionTool("iol_team", "check_linguistic_rule_table", "linguistics", "Align proposed linguistic rules with numbered examples and explicit counterexamples in one team script.", ("rule_ids", "rules", "example_refs", "counterexamples")),
    CompetitionTool("ijso_practical", "check_ijso_measurements", "measurements", "Practical report measurements with units, uncertainties and source references; no invented readings.", ("quantities", "values", "units", "uncertainties", "sources")),
    CompetitionTool("eoes", "check_eoes_measurements", "measurements", "Experimental team report: align measured quantities, units, uncertainty and data provenance.", ("quantities", "values", "units", "uncertainties", "sources")),
    CompetitionTool("ioaa_group", "check_ioaa_observations", "observations", "Host-year observation table: object, observation, coordinate frame or units, and provided-material reference.", ("objects", "observations", "frames_or_units", "sources")),
    CompetitionTool("science_olympiad", "prepare_event_answer_sheet", "event_answers", "Event answer sheet bound to the selected season, division and event.", ("problem_ids", "answers")),
    CompetitionTool("qanta", "prepare_quizbowl_answer", "short_answer", "A concise quiz-bowl answerline preserving the contestant's chosen disambiguation.", ("answer",)),
    CompetitionTool("science_bowl", "prepare_science_bowl_answer", "science_answer", "Prepare a multiple-choice letter plus option text, or a concise short answer.", ("answer_type", "answer", "option_text"), "Formatting only; does not buzz, recognize a speaker, confer on a tossup, or award a bonus."),
    CompetitionTool("history_olympiad", "prepare_history_bowl_answer", "short_answer", "Prepare one history answer without guessing quarter-dependent points or later clues.", ("answer",), "No buzzer, opponent, timing, eligibility, or quarter transition is simulated."),
    CompetitionTool("debatebench", "check_bp_speech_order", "speeches", "BP transcript order PM, LO, DPM, DLO, MG, MO, GW, OW; identify duplicate or misplaced roles.", ("roles", "speeches"), "Checks the supplied transcript; does not implement coalition privacy or generate opponents."),
    CompetitionTool("ethics_bowl_appe", "prepare_appe_case_response", "sections", "Separate case response, opposing commentary, reply and answers to judges.", ("case_response", "opposing_commentary", "commentary_reply", "judge_answers")),
    CompetitionTool("ethics_bowl_nhseb", "prepare_nhseb_case_response", "sections", "Separate presentation, commentary, response and answers to judges for the selected scope.", ("presentation", "commentary", "response", "judge_answers")),
    CompetitionTool("ichto", "prepare_chemistry_fight_record", "sections", "Chemistry report, opposition, response, review and experimental evidence as distinct contributions.", ("report", "opposition", "reporter_response", "review", "experimental_evidence"), "Prepares a written record; does not invent live speakers, jury questions or experimental observations."),
    CompetitionTool("iypt", "prepare_physics_research_outline", "sections", "Deck outline separating theory, experimental or simulation evidence, uncertainty, conclusions and citations.", ("question", "theory", "evidence", "uncertainty", "conclusions", "citations")),
    CompetitionTool("itym", "check_math_research_dependencies", "proofs", "Research-paper claims, proofs and dependency graph; computational claims still need reproducible evidence.", ("part_ids", "claims", "proofs", "dependencies")),
    CompetitionTool("mcm", "prepare_mcm_model_record", "sections", "Modeling paper outline connecting assumptions, variables, model, validation and sensitivity.", ("problem", "assumptions", "variables", "model", "validation", "sensitivity", "limitations", "references")),
    CompetitionTool("icm", "prepare_icm_model_record", "sections", "Interdisciplinary modeling record linking stakeholder objectives, model, validation, tradeoffs and disclosures.", ("objectives", "assumptions", "model", "validation", "tradeoffs", "limitations", "references", "disclosures")),
    CompetitionTool("cfa_research_challenge", "prepare_equity_research_record", "sections", "Equity research: investment thesis, valuation assumptions, catalysts, downside risks and public-source citations.", ("company", "thesis", "valuation", "assumptions", "catalysts", "risks", "sources")),
    CompetitionTool("wharton_investment", "check_portfolio_weights", "portfolio", "Portfolio weights, client constraints and position rationales; report total allocation and duplicate holdings.", ("symbols", "weights_percent", "rationales", "client_objectives")),
    CompetitionTool("ieo_business_case", "prepare_ieo_case_recommendation", "sections", "Business Case deck record: alternatives, recommendation, economic evidence and implementation.", ("problem", "alternatives", "recommendation", "economic_evidence", "implementation", "risks", "sources")),
    CompetitionTool("gcch_harvard", "prepare_ma_case_record", "sections", "M&A pitch-book record separating target fit, valuation, financing, synergies and integration risks.", ("industry", "target", "valuation", "financing", "synergies", "integration", "risks")),
    CompetitionTool("jessup", "check_jessup_authority_table", "authorities", "Applicant/Respondent argument map linking each proposition to authority and packet facts.", ("sides", "issues", "propositions", "authorities", "fact_refs")),
    CompetitionTool("vis_moot", "check_vis_authority_table", "authorities", "Claimant/Respondent arbitration argument map with authorities and problem-record references.", ("sides", "issues", "propositions", "authorities", "fact_refs")),
    CompetitionTool("mystery_hunt", "check_puzzle_extraction", "extraction", "Check a proposed ordered letter extraction from contestant-supplied feeder answers and one-based indices.", ("feeder_ids", "answers", "indices"), "Uses only supplied answers; does not query answer keys, confirm a meta answer, or unlock puzzles."),
    CompetitionTool("cybench", "prepare_cybench_flag", "flag", "Preserve an exact recovered flag and its challenge-environment evidence.", ("flag", "recovery_evidence"), "No sandbox is started or accessed; a formatted candidate is not proof of recovery or a correct flag."),
    CompetitionTool("nyu_ctf_bench", "prepare_nyu_ctf_flag", "flag", "Bind a recovered flag candidate to contestant-provided recovery evidence for one NYU CTF challenge.", ("flag", "recovery_evidence"), "No host files, writeups or hidden flags are read. Formatting is not grading."),
    CompetitionTool("ccdc", "prepare_defense_inject_response", "sections", "Inject response connecting business request, affected services, actions, verification evidence and rollback.", ("inject_id", "request", "affected_services", "actions", "verification_evidence", "rollback"), "Prepares a report only; no network mutation, red team or service uptime is simulated."),
    CompetitionTool("wro", "check_robot_mission_sequence", "robot", "Mission plan: action sequence, expected observations and durations against an explicitly supplied run limit.", ("steps", "expected_observations", "durations_seconds", "run_limit_seconds"), "A plan is hypothetical; does not run a robot or report physical mission scores."),
    CompetitionTool("ioai_team", "check_ioai_artifact_manifest", "ai_artifacts", "Check artifact names, media types and provenance for the selected IOAI year; consult the task packet for its output contract.", ("artifact_names", "media_types", "provenance"), "Checks inventory only; does not synthesize creative media, run a robot or substitute a generic ML scoring contract."),
    CompetitionTool("odyssey_of_the_mind", "check_creative_constraint_map", "constraints", "Map each supplied long-term/spontaneous constraint to a solution element and proposed evidence.", ("constraints", "solution_elements", "evidence"), "Coverage is based on the supplied synopsis; physical performance and unpublished scoring are not checked."),
    CompetitionTool("wsc_writing", "check_writing_prompt_allocation", "writing", "Exactly three responses, three distinct teammate authors and three distinct provided prompts.", ("authors", "prompt_ids", "responses"), "Checks a proposed allocation or final packet; does not enforce live preparation, independent-writing or peer-review clocks."),
)


_ARRAY_FIELDS = frozenset({
    "problem_ids", "answers", "justifications", "part_ids", "claims", "proofs", "dependencies",
    "quantities", "values", "units", "required_units", "uncertainties", "sources",
    "case_ids", "inputs", "expected_outputs", "rule_ids", "rules", "example_refs", "counterexamples",
    "objects", "observations", "frames_or_units", "roles", "speeches", "sides", "issues", "propositions",
    "authorities", "fact_refs", "symbols", "weights_percent", "rationales", "feeder_ids", "indices",
    "steps", "expected_observations", "durations_seconds", "artifact_names", "media_types", "provenance",
    "constraints", "solution_elements", "evidence", "authors", "prompt_ids", "responses",
})
_NUMERIC_ARRAYS = {"weights_percent", "durations_seconds", "indices"}


def _arguments(profile):
    for field in profile.fields:
        array = profile.kind != "sections" and field in _ARRAY_FIELDS
        json_type = "array" if array else "number" if field == "run_limit_seconds" else "string"
        description = field.replace("_", " ").capitalize() + "."
        if array:
            description += " Same row order and length as the other arrays."
        if field == "dependencies":
            description += " One comma-separated list of earlier part ids per row; empty string for no dependencies."
        if field in {"counterexamples", "uncertainties"}:
            description += " An empty row explicitly means not supplied."
        if field == "weights_percent":
            description += " Use percentage points (25 means 25 percent), not fractions."
        if field == "indices":
            description += " One-based character indices into the exact supplied answers, including spaces."
        if field == "client_objectives":
            json_type = "string"
        yield ArgumentSpec(field, type=json_type, description=description,
                           items=("integer" if field == "indices" else "number")
                           if field in _NUMERIC_ARRAYS else "string" if array else None)


SPECS = tuple(make_action(
    p.name, p.feature + " " + p.limitation + " Returns private preparation feedback; use work to record a candidate and the normal submission action to hand it in.",
    tuple(_arguments(p)), module="task_specific", pack="contest_preparation",
    visibility="private", tool_calls=1, is_tool=True,
) for p in PROFILES)
BY_NAME = MappingProxyType({p.name: p for p in PROFILES})
BY_COMPETITION = MappingProxyType({p.competition: p for p in PROFILES})
ACTION_NAMES = frozenset(BY_NAME)
if len(BY_NAME) != len(PROFILES) or len(BY_COMPETITION) != len(PROFILES):
    raise ValueError("Competition preparation profiles must be unique")
