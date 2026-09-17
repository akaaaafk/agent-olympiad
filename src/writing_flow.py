"""Three-response writing with team peer editing or single-agent self editing."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json


class WritingFlow:
    def __init__(self, manifest, session, config):
        self.solo = config.system_variant == "single_agent"
        if config.team_size != (1 if self.solo else 3) or len(manifest.tasks) != 3 or any(t.programming for t in manifest.tasks):
            raise ValueError("WSC writing requires three distinct tasks and one solo writer or three team writers")
        ids = [t.task_id for t in manifest.tasks]
        if len(set(ids)) != 3:
            raise ValueError("WSC prompts must be distinct")
        self.manifest, self.session, self.config = manifest, session, config
        identity = dict(kind="collaborative_writing_v1", ids=ids, team_size=config.team_size,
                        captain=config.leader or "Agent_1",
                        manifest_sha256=hashlib.sha256(json.dumps(asdict(manifest), sort_keys=True,
                            ensure_ascii=False).encode()).hexdigest())
        restored = session._competition_flow_checkpoint
        self.state = deepcopy(restored) if restored is not None else dict(
            identity=identity, phase="planning", closed=False, drafts={}, edited=[])
        if self.state.get("identity") != identity:
            raise ValueError("writing checkpoint does not match manifest/roster")
        if self.state.get("phase") not in {"planning", "writing", "peer_review", "complete"}:
            raise ValueError("invalid writing phase")
        if type(self.state.get("closed")) is not bool or not isinstance(self.state.get("drafts"), dict):
            raise ValueError("invalid writing checkpoint")
        if not set(self.state["drafts"]) <= set(ids) or not set(self.state.get("edited", [])) <= set(ids):
            raise ValueError("invalid writing checkpoint tasks")
        for draft in self.state["drafts"].values():
            if (not isinstance(draft.get("content"), str) or not draft["content"].strip()
                    or len(draft["content"]) > 60000 or type(draft.get("turn")) is not int
                    or not 0 <= draft["turn"] <= session.budget.turns_used):
                raise ValueError("invalid writing draft")
        phase = self.state["phase"]
        edited = self.state.get("edited")
        if not isinstance(edited, list) or len(set(edited)) != len(edited):
            raise ValueError("invalid writing editor records")
        if (phase == "planning" and self.state["drafts"]
                or phase in {"planning", "writing"} and edited
                or phase == "peer_review" and len(self.state["drafts"]) != 3):
            raise ValueError("writing checkpoint stage/draft mismatch")
        for task in session.tasks:
            committed = phase == "complete" and task.task_id in self.state["drafts"]
            if len(task.submissions) != int(committed) or bool(task.versions) != committed:
                raise ValueError("writing checkpoint submission/draft mismatch")
            if committed and task.versions[-1].content != self.state["drafts"][task.task_id]["content"]:
                raise ValueError("writing checkpoint submitted response mismatch")
            if restored is not None and task.locked != (self.state["closed"] or phase == "complete"):
                raise ValueError("writing checkpoint lock mismatch")
        session.competition_flow = self
        self._sync_locks()

    @property
    def current_ids(self):
        return () if self.state["closed"] or self.state["phase"] == "complete" else tuple(self.state["identity"]["ids"])

    def is_visible(self, task_id):
        return task_id in self.state["identity"]["ids"]

    def require_visible(self, task_id):
        if not self.is_visible(task_id):
            raise ValueError("unknown writing prompt")

    def _sync_locks(self):
        for task in self.session.tasks:
            task.locked = task.task_id not in self.current_ids
        if not self.current_ids and self.session.active_task is not None:
            self.session.skip_task()

    def checkpoint(self):
        return deepcopy(self.state)

    def public_manifest(self):
        return self.manifest

    def owner(self, tid):
        self.require_visible(tid)
        if self.solo:
            return "Agent_1"
        return f"Agent_{self.state['identity']['ids'].index(tid) + 1}"

    def editor(self, tid):
        self.require_visible(tid)
        if self.solo:
            return "Agent_1"
        return f"Agent_{(self.state['identity']['ids'].index(tid) + 1) % 3 + 1}"

    def public_state(self):
        return dict(type="collaborative_writing_v1", phase=self.state["phase"], closed=self.state["closed"],
                    current_task_ids=list(self.current_ids), captain=self.state["identity"]["captain"],
                    authors={tid: self.owner(tid) for tid in self.state["identity"]["ids"]},
                    peer_editors={tid: self.editor(tid) for tid in self.state["identity"]["ids"]},
                    review_mode="self_edit" if self.solo else "peer_edit",
                    draft_present=list(self.state["drafts"]), edited=list(self.state["edited"]),
                    deadline_policy="collect_writing_drafts" if self.config.deadline_submit else "explicit_handins_only",
                    instructions=("Single agent: start_independent_writing, write all three responses with write_writing_response, then start_peer_review to enter self-editing. Edit each of your three responses with review_writing_response, then submit_writing_packet. No independent peer approval is claimed."
                                  if self.solo else "Captain: start_independent_writing, then start_peer_review once all three drafts exist, then submit_writing_packet. Each writer uses write_writing_response; each assigned editor uses read_writing_response and review_writing_response with complete edited text."),
                    limitations=["benchmark prompt grouping", "official stage minutes unknown", "LLM rubric scoring"])

    def _can_submit(self, agent):
        return agent == self.state["identity"]["captain"] and (
            self.config.otc_policy is None or self.config.otc_policy.may_submit(agent))

    def allowed(self, names, agent):
        safe = {"rest", "check_budget", "query_rules", "remember", "recall", "select_problem"}
        phase = self.state["phase"]
        if self.state["closed"] or phase == "complete":
            return set(names) & {"rest", "check_budget", "query_rules", "recall"}
        if phase in {"planning", "peer_review"}:
            safe |= {"speak", "direct_message", "share_note"}
        if phase == "planning" and agent == self.state["identity"]["captain"]:
            safe.add("start_independent_writing")
        if phase == "writing":
            safe |= {"write_writing_response", "read_writing_response"}
            if len(self.state["drafts"]) == 3 and agent == self.state["identity"]["captain"]:
                safe.add("start_peer_review")
        if phase == "peer_review":
            safe |= {"read_writing_response", "review_writing_response"}
            if len(set(self.state["edited"])) == 3 and self._can_submit(agent):
                safe.add("submit_writing_packet")
        return set(names) & safe

    def require_action(self, action, arguments, agent):
        if agent not in {f"Agent_{i+1}" for i in range(self.config.team_size)} or action not in self.allowed({action}, agent):
            raise ValueError("action is not legal for this writing stage or contestant")
        if action in {"write_writing_response", "read_writing_response", "review_writing_response"}:
            tid = arguments.get("problem_id")
            self.require_visible(tid)
            assigned = self.owner(tid) if self.state["phase"] == "writing" else self.editor(tid)
            if agent != assigned:
                raise ValueError("this response belongs to another writer/editor")
            if action == "read_writing_response":
                draft = self.state["drafts"].get(tid)
                if draft is None:
                    raise ValueError("no writing draft exists")
                if self.config.current_turn_only and draft["turn"] != self.session.budget.turns_used:
                    raise ValueError("previous-turn response content is unavailable in this baseline")
            else:
                content = arguments.get("content")
                if not isinstance(content, str) or not content.strip() or len(content) > 60000:
                    raise ValueError("response must be nonempty text of at most 60000 characters")

    def require_answer_creation(self):
        if not self.session._flow_committing:
            raise ValueError("use private writing/editing actions rather than a shared answer")

    def _commit(self):
        receipts = []
        self.session._flow_committing = True
        try:
            for tid in self.state["identity"]["ids"]:
                draft = self.state["drafts"].get(tid)
                if draft is None:
                    continue
                self.session.select_task(tid)
                self.session.create_answer(draft["content"], author=self.owner(tid))
                record = self.session.submit("SUBMITTED", score=0)
                receipts.append(dict(task_id=tid, version_hash=record.version_hash, verdict="SUBMITTED"))
        finally:
            self.session._flow_committing = False
        self.state["phase"] = "complete"
        self._sync_locks()
        return receipts

    def apply(self, action, arguments, agent):
        self.require_action(action, arguments, agent)
        result = {}
        if action == "start_independent_writing":
            self.state["phase"] = "writing"
        elif action in {"write_writing_response", "review_writing_response"}:
            tid = arguments["problem_id"]
            self.state["drafts"][tid] = dict(content=arguments["content"], turn=self.session.budget.turns_used)
            if action == "review_writing_response" and tid not in self.state["edited"]:
                self.state["edited"].append(tid)
        elif action == "read_writing_response":
            result["content"] = self.state["drafts"][arguments["problem_id"]]["content"]
        elif action == "start_peer_review":
            self.state["phase"] = "peer_review"
            # Release to the assigned editors in this round, without publishing shared versions.
            for draft in self.state["drafts"].values():
                draft["turn"] = self.session.budget.turns_used
        elif action == "submit_writing_packet":
            result["submissions"] = self._commit()
        else:
            raise ValueError("unknown writing flow action")
        return dict(**self.public_state(), **result)

    def close(self):
        if not self.state["closed"] and self.state["phase"] != "complete" and self.config.deadline_submit:
            self._commit()
        self.state["closed"] = True
        self._sync_locks()
