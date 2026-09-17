"""Opt-in session actions for the two stateful contest pilots."""
from functools import partial
from .contracts import ArgumentSpec, make_action

_action = partial(make_action, module="task_specific", pack="contest_flow",
                  runtimes=frozenset({"session"}))
SPECS = (
    _action("submit_set", "Irreversibly hand in every current Guts draft (blank entries score zero).",
            (), submission=True, submission_attempts=1),
    _action("collect_next_set", "Collect the next Guts set after handing in the current one.", ()),
    _action("buzz", "Claim the current fully displayed tossup; only you may answer it.", ()),
    _action("answer_tossup", "Give your first and final tossup answer after recognition; empty text passes.",
            (ArgumentSpec("answer", description="Final spoken answer; empty string passes."),),
            submission=True, submission_attempts=1),
    _action("answer_bonus", "Captain gives the first and final earned bonus answer; empty text passes.",
            (ArgumentSpec("answer", description="Final spoken answer; empty string passes."),),
            submission=True, submission_attempts=1),
)
_WRITING_SPECS = (
    _action("start_independent_writing", "Captain ends planning and starts private individual writing.", ()),
    _action("write_writing_response", "Replace your assigned private response during individual writing.",
            (ArgumentSpec("problem_id"), ArgumentSpec("content")), visibility="private"),
    _action("read_writing_response", "Read your own draft while writing, or your assigned peer draft during editing.",
            (ArgumentSpec("problem_id"),), visibility="private"),
    _action("start_peer_review", "Captain ends independent writing after all three responses exist.", ()),
    _action("review_writing_response", "Replace the response assigned to you for peer editing with the complete edited text.",
            (ArgumentSpec("problem_id"), ArgumentSpec("content")), visibility="private"),
    _action("submit_writing_packet", "Captain submits all three responses after peer editing.", (),
            submission=True, submission_attempts=1),
)
OWNERS = {s.name: ("hmmt_guts" if s.name in {"submit_set", "collect_next_set"}
                   else "science_bowl") for s in SPECS}
OWNERS.update({s.name: "wsc_writing" for s in _WRITING_SPECS})
SPECS += _WRITING_SPECS
ACTION_NAMES = frozenset(OWNERS)
FLOW_TYPES = {"hmmt_guts": "guts_sets_v1", "science_bowl": "science_bowl_buzzer_v1",
              "wsc_writing": "collaborative_writing_v1"}


def flow_type(manifest):
    value = manifest.metadata.get("competition_flow")
    if value is None:
        return None
    if not isinstance(value, str) or value != FLOW_TYPES.get(manifest.competition_id):
        raise ValueError("unsupported competition_flow for this competition")
    return value
