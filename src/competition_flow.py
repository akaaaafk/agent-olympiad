"""Stateful, single-team contest pilots behind one session interface.

Only manifests explicitly selecting a versioned flow use this module. Judge
inputs stay here; public_state never includes the plan, hidden tasks or keys.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
import math

from action_modules.competition_flow import ACTION_NAMES, OWNERS, flow_type


class CompetitionFlow:
    def __init__(self, manifest, session, config):
        self.manifest, self.session, self.config = manifest, session, config
        kind = flow_type(manifest)
        if kind is None:
            raise ValueError("competition_flow is not enabled")
        if any(task.programming for task in manifest.tasks):
            raise ValueError("stateful pilots require non-programming tasks")
        self.by_id = {task.task_id: task for task in manifest.tasks}
        groups = self._groups(kind)
        captain = config.leader or "Agent_1"
        identity = dict(version=1, kind=kind, groups=groups,
                        team_size=config.team_size, captain=captain,
                        manifest_sha256=hashlib.sha256(json.dumps(asdict(manifest), sort_keys=True,
                                                                 ensure_ascii=False).encode()).hexdigest())
        # Refuse unsupported grading before the first action, not midway through
        # a multi-answer submission. This does not publish expected answers.
        for task in manifest.tasks:
            self._grade(task.task_id, "")
        restored = session._competition_flow_checkpoint
        if restored is not None:
            if restored.get("identity") != identity:
                raise ValueError("competition flow checkpoint does not match manifest/roster")
            self.state = deepcopy(restored)
            self._validate_checkpoint()
        else:
            self.state = dict(identity=identity, cursor=0,
                              phase="set_open" if kind == "guts_sets_v1" else "tossup_open",
                              recognized=None, visible=[], closed=False)
            self.state["visible"] = list(groups[0] if kind == "guts_sets_v1" else groups[0][:1])
        session.competition_flow = self
        if restored is None:
            self._sync_locks()

    def _groups(self, kind):
        tasks = self.manifest.tasks
        if not tasks:
            raise ValueError("competition flow requires tasks")
        if kind == "guts_sets_v1":
            seasons = {t.benchmark.get("season") for t in tasks}
            if len(seasons) != 1 or next(iter(seasons)) not in {"nov", "feb"}:
                raise ValueError("Guts requires one explicit benchmark season (nov/feb)")
            size = 3 if next(iter(seasons)) == "nov" else 4
            if (len({t.parent_problem_id for t in tasks}) != 1
                    or [t.question_id for t in tasks] != [str(i + 1) for i in range(len(tasks))]
                    or len(tasks) % size):
                raise ValueError("Guts requires consecutive split questions starting at 1 in complete season-sized sets")
            return [[t.task_id for t in tasks[i:i + size]] for i in range(0, len(tasks), size)]
        groups = {}
        for task in tasks:
            row = task.benchmark
            key = (row.get("parent_session_id"), row.get("question_number"), row.get("source_file"))
            role = row.get("tossup_or_bonus")
            if not all(value is not None and str(value).strip() for value in key) or role not in {"toss_up", "bonus"}:
                raise ValueError("Science Bowl needs source packet, question number and tossup/bonus metadata")
            pair = groups.setdefault(key, {})
            if role in pair:
                raise ValueError("duplicate Science Bowl question role")
            pair[role] = task.task_id
        if len({key[0] for key in groups}) != 1 or len({key[2] for key in groups}) != 1:
            raise ValueError("Science Bowl pilot must use one source packet")
        if any(set(pair) != {"toss_up", "bonus"} for pair in groups.values()):
            raise ValueError("Science Bowl requires complete same-source tossup/bonus pairs")
        return [[pair["toss_up"], pair["bonus"]] for pair in groups.values()]

    def _grade(self, task_id, answer):
        from contest_adapters import _grade_non_programming
        task = self.by_id[task_id]
        score, maximum = _grade_non_programming(task, answer, self.manifest.competition_id)
        if not math.isfinite(maximum) or maximum <= 0 or not math.isfinite(score):
            raise ValueError("flow requires finite positive supported scoring weights")
        if self.manifest.competition_id == "science_bowl":
            weight = 4.0 if task.benchmark["tossup_or_bonus"] == "toss_up" else 10.0
            score, maximum = weight * score / maximum, weight
        return score, maximum

    @property
    def current_ids(self):
        if self.state["closed"] or self.state["phase"] in {"complete", "awaiting_set"}:
            return ()
        group = self.state["identity"]["groups"][self.state["cursor"]]
        if self.state["identity"]["kind"] == "guts_sets_v1":
            return tuple(group)
        return (group[1] if self.state["phase"] == "bonus_open" else group[0],)

    def is_visible(self, task_id):
        return task_id in self.state["visible"]

    def require_visible(self, task_id):
        if not self.is_visible(task_id):
            raise ValueError("task is not released in the current competition flow")

    def _sync_locks(self):
        current = set(self.current_ids)
        for task in self.session.tasks:
            task.locked = task.task_id not in current
        active = self.session.active_task
        if active is not None and active.task_id not in current:
            self.session.skip_task()

    def _validate_checkpoint(self):
        s = self.state
        groups = s["identity"]["groups"]
        if type(s.get("cursor")) is not int or not 0 <= s["cursor"] < len(groups):
            raise ValueError("invalid competition flow cursor")
        phases = ({"set_open", "awaiting_set", "complete"} if s["identity"]["kind"] == "guts_sets_v1"
                  else {"tossup_open", "tossup_buzzed", "bonus_open", "complete"})
        if s.get("phase") not in phases or type(s.get("closed")) is not bool:
            raise ValueError("invalid competition flow phase")
        visible = s.get("visible")
        if not isinstance(visible, list) or len(set(visible)) != len(visible) or not set(visible) <= set(self.by_id):
            raise ValueError("invalid competition flow visibility")
        if s.get("recognized") not in ({None} | {f"Agent_{i+1}" for i in range(self.config.team_size)}):
            raise ValueError("invalid recognized speaker")
        if (s["phase"] == "tossup_buzzed") != (s.get("recognized") is not None):
            raise ValueError("inconsistent recognized speaker phase")
        if s["phase"] == "complete" and s["cursor"] != len(groups) - 1:
            raise ValueError("competition flow completed before its last group")
        if s["phase"] == "awaiting_set" and s["cursor"] == len(groups) - 1:
            raise ValueError("no next Guts set exists")
        expected_visible = []
        for index, group in enumerate(groups):
            if index > s["cursor"]:
                break
            complete = index < s["cursor"] or s["phase"] in {"complete", "awaiting_set"}
            if s["identity"]["kind"] == "guts_sets_v1":
                expected_visible.extend(group)
                expected_submissions = {tid: int(complete) for tid in group}
            else:
                tossup = self.session.task(group[0])
                earned = bool(tossup.latest_valid_submission and tossup.latest_valid_submission.verdict == "AC")
                expected_visible.extend(group if earned else group[:1])
                if index == s["cursor"] and s["phase"] == "bonus_open" and not earned:
                    raise ValueError("checkpoint bonus was not earned")
                answered_tossup = complete or s["phase"] == "bonus_open"
                expected_submissions = {group[0]: int(answered_tossup), group[1]: int(complete and earned)}
            if any(len(self.session.task(tid).submissions) != count for tid, count in expected_submissions.items()):
                raise ValueError("competition flow phase/submission mismatch")
        if visible != expected_visible:
            raise ValueError("competition flow visibility does not match earned releases")
        current = set(self.current_ids)
        if not current <= set(visible):
            raise ValueError("current competition tasks must be visible")
        for index, group in enumerate(groups):
            if index > s["cursor"] and set(group) & set(visible):
                raise ValueError("checkpoint exposed a future set/question")
        for task in self.session.tasks:
            if task.locked != (task.task_id not in current):
                raise ValueError("competition flow checkpoint lock mismatch")
            if not self.is_visible(task.task_id) and (task.versions or task.submissions):
                raise ValueError("unreleased task contains answers")
        active = self.session.active_task
        if active is not None and active.task_id not in current:
            raise ValueError("competition flow checkpoint active task is not open")

    def checkpoint(self):
        return deepcopy(self.state)

    def public_state(self):
        return dict(type=self.state["identity"]["kind"], phase=self.state["phase"],
                    current_task_ids=list(self.current_ids), recognized=self.state["recognized"],
                    captain=self.state["identity"]["captain"], closed=self.state["closed"],
                    score=sum(task.score for task in self.session.tasks),
                    deadline_policy="explicit_handins_only",
                    limitations=["single team", "turn budget, no live clock", "no opponents or appeals"])

    def public_manifest(self):
        return replace(self.manifest, tasks=tuple(t for t in self.manifest.tasks if self.is_visible(t.task_id)))

    def _can_hand_in(self, agent):
        if self.config.features.leader_submits and agent != self.config.leader:
            return False
        return self.config.otc_policy is None or self.config.otc_policy.may_submit(agent)

    def _set_reviewed(self):
        if not self.config.review_required:
            return True
        from contest_actions import _task_has_independent_approval
        return all(not self.session.task(task_id).versions or _task_has_independent_approval(self.session.task(task_id))
                   for task_id in self.current_ids)

    def allowed(self, names, agent):
        """Intersect an already baseline/card-gated surface with contest legality."""
        requested = set(names)
        names = requested - {"submit", "finish_contest"}
        owned = {name for name in ACTION_NAMES if OWNERS[name] == self.manifest.competition_id}
        names -= ACTION_NAMES
        if self.state["closed"] or self.state["phase"] == "complete":
            return names & {"rest", "check_budget", "query_rules", "recall"}
        phase = self.state["phase"]
        legal = set()
        if phase == "set_open" and self._can_hand_in(agent) and self._set_reviewed():
            legal.add("submit_set")
        elif phase == "awaiting_set":
            legal.add("collect_next_set")
        elif phase == "tossup_open":
            legal.add("buzz")
        elif phase == "tossup_buzzed" and self.state["recognized"] == agent:
            legal.add("answer_tossup")
        elif phase == "bonus_open" and self.state["identity"]["captain"] == agent:
            legal.add("answer_bonus")
        if phase in {"tossup_open", "tossup_buzzed"}:
            # Every channel that publishes another contestant's reasoning is
            # disallowed on a tossup, including shared drafts and memory shares.
            names -= {"work", "speak", "direct_message", "share_note", "propose", "challenge",
                      "provide_evidence", "revise", "decide", "review_answer", "request_review",
                      "assign_problem", "triage_problem"}
        if not self.current_ids:
            names -= {"work", "select_problem", "skip_problem", "review_answer", "request_review"}
        return names | (owned & legal & requested)

    def require_action(self, action, arguments, agent):
        if agent not in {f"Agent_{i+1}" for i in range(self.config.team_size)}:
            raise ValueError("competition action requires an active contestant")
        if action not in self.allowed({action}, agent):
            raise ValueError("action is not legal for this competition phase or speaker")
        targets = []
        if arguments.get("problem_id"):
            targets.append(str(arguments["problem_id"]))
        targets.extend(arguments.get("problem_ids") or [])
        for task_id in targets:
            self.require_visible(str(task_id))
        if action in {"answer_tossup", "answer_bonus"} and not isinstance(arguments.get("answer"), str):
            raise ValueError("spoken answer must be text")

    def _commit_answers(self, candidates, agent):
        # All validation and grading precede mutation: a failed judge cannot
        # leave half of a Guts set handed in.
        graded = [(tid, answer, *self._grade(tid, answer)) for tid, answer in candidates]
        receipts = []
        self.session._flow_committing = True
        try:
            for tid, answer, score, maximum in graded:
                task = self.session.select_task(tid)
                if not task.versions or task.versions[-1].content != answer:
                    self.session.create_answer(answer, author=agent)
                submission = self.session.submit("AC" if score == maximum else "WA", score=score)
                receipts.append(dict(task_id=tid, score=score, max_score=maximum,
                                     version_hash=submission.version_hash, verdict=submission.verdict))
        finally:
            self.session._flow_committing = False
        return receipts

    def apply(self, action, arguments, agent):
        self.require_action(action, arguments, agent)
        receipts = []
        if action == "buzz":
            self.state.update(phase="tossup_buzzed", recognized=agent)
        elif action == "collect_next_set":
            self.state["cursor"] += 1
            self.state["phase"] = "set_open"
            self.state["visible"].extend(self.current_ids)
        elif action == "submit_set":
            candidates = [(tid, self.session.task(tid).versions[-1].content
                           if self.session.task(tid).versions else "") for tid in self.current_ids]
            receipts = self._commit_answers(candidates, agent)
            self.state["phase"] = ("complete" if self.state["cursor"] + 1 == len(self.state["identity"]["groups"])
                                   else "awaiting_set")
        elif action in {"answer_tossup", "answer_bonus"}:
            receipts = self._commit_answers([(self.current_ids[0], arguments["answer"])], agent)
            self.state["recognized"] = None
            if action == "answer_tossup" and receipts[0]["verdict"] == "AC":
                self.state["phase"] = "bonus_open"
                self.state["visible"].extend(self.current_ids)
            elif self.state["cursor"] + 1 == len(self.state["identity"]["groups"]):
                self.state["phase"] = "complete"
            else:
                self.state["cursor"] += 1
                self.state["phase"] = "tossup_open"
                self.state["visible"].extend(self.current_ids)
        else:
            raise ValueError("not a competition flow action")
        self._sync_locks()
        return dict(**self.public_state(), submissions=receipts)

    def close(self):
        """A deadline freezes state; it never promotes drafts to spoken/handed-in answers."""
        self.state["closed"] = True
        self._sync_locks()


def bind_competition_flow(manifest, session, config):
    if flow_type(manifest) == "collaborative_writing_v1":
        from writing_flow import WritingFlow
        return WritingFlow(manifest, session, config)
    if flow_type(manifest) is None:
        if (manifest.competition_id == "wsc_writing" and any(
                t.benchmark.get("evaluation", {}).get("assessment_scope") == "three_author_staged_written"
                for t in manifest.tasks)):
            raise ValueError("use a three-prompt WSC manifest with competition_flow=collaborative_writing_v1")
        if session._competition_flow_checkpoint is not None:
            raise ValueError("cannot restore a competition flow checkpoint in ordinary mode")
        return None
    return CompetitionFlow(manifest, session, config)
