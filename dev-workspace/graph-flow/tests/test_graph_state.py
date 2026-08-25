#!/usr/bin/env python3
"""Black-box tests for the portable graph-flow state engine."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
ENGINE = SKILL_DIR / "scripts" / "graph_state.py"


class GraphStateCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name) / "repo"
        self.repo.mkdir()
        self.run_id = "test-run"
        self.task_ids: dict[str, str] = {}

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def command(self, *arguments: str, succeeds: bool = True) -> dict:
        completed = subprocess.run(
            [sys.executable, str(ENGINE), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if succeeds:
            self.assertEqual(completed.returncode, 0, completed.stderr)
        else:
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
        output = completed.stdout.strip()
        return json.loads(output) if output else {}

    def raw_command(self, *arguments: str, succeeds: bool = True) -> str:
        completed = subprocess.run(
            [sys.executable, str(ENGINE), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if succeeds:
            self.assertEqual(completed.returncode, 0, completed.stderr)
        else:
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
        return completed.stdout.strip()

    def write_json(self, name: str, contents: dict) -> Path:
        path = Path(self.tempdir.name) / name
        path.write_text(json.dumps(contents))
        return path

    def definition(self, *, max_attempts: int = 2) -> dict:
        return {
            "version": 1,
            "max_concurrency": 2,
            "limits": {"max_attempts_per_node": max_attempts, "max_transitions": 30},
            "nodes": [
                {
                    "id": "inspect",
                    "kind": "decision",
                    "outcomes": ["legacy", "modern"],
                },
                {
                    "id": "legacy-work",
                    "kind": "implementation",
                    "depends_on": [{"node": "inspect", "outcome": "legacy"}],
                    "outcomes": ["done"],
                },
                {
                    "id": "modern-work",
                    "kind": "implementation",
                    "depends_on": [{"node": "inspect", "outcome": "modern"}],
                    "outcomes": ["done"],
                },
                {
                    "id": "verify-modern",
                    "kind": "verification",
                    "depends_on": [{"node": "modern-work", "outcome": "done"}],
                    "outcomes": ["passed", "rejected"],
                    "transitions": {"rejected": "modern-work"},
                },
            ],
        }

    def planned_definition(self, *, max_concurrency: int = 2) -> dict:
        """A complete planned graph used to exercise planned-mode validation."""

        return {
            "version": 1,
            "workstreams": [
                {"id": "engine", "title": "State engine", "objective": "Build the state-engine behavior."},
                {"id": "quality", "title": "Quality", "objective": "Verify the planned graph behavior."},
            ],
            "max_concurrency": max_concurrency,
            "nodes": [
                {
                    "id": "implement",
                    "kind": "implementation",
                    "workstream": "engine",
                    "objective": "Implement planned graph validation.",
                    "assigned_role": "worker",
                    "priority": "high",
                    "acceptance_criteria": ["The engine accepts valid planned graphs."],
                    "paths": ["scripts/graph_state.py", "tests/test_graph_state.py"],
                    "verification_commands": ["python3 -m unittest discover -s tests -v"],
                    "outcomes": ["done"],
                },
                {
                    "id": "verify",
                    "kind": "verification",
                    "workstream": "quality",
                    "objective": "Verify planned graph validation.",
                    "assigned_role": "reviewer",
                    "priority": "high",
                    "acceptance_criteria": ["The graph validation test suite passes."],
                    "paths": ["scripts/graph_state.py", "tests/test_graph_state.py"],
                    "verification_commands": ["python3 -m unittest discover -s tests -v"],
                    "depends_on": [{"node": "implement", "outcome": "done"}],
                    "outcomes": ["passed"],
                },
            ],
        }

    def requirements(self) -> dict:
        return {
            "goal": "Ship portable graph-flow lifecycle controls.",
            "success_criteria": ["The coordinator can resume safely."],
            "scope": {"included": ["state engine"], "excluded": ["runtime adapters"]},
            "constraints": ["Remain vendor neutral."],
            "verification": ["Run the black-box CLI tests."],
            "approval_boundaries": ["Approve the graph before dispatch."],
            "assumptions": ["The coordinator is the single writer."],
        }

    def start_run(self, *, run_id: str | None = None, request: dict | None = None) -> dict:
        return self.command(
            "start",
            "--repo",
            str(self.repo),
            "--run-id",
            run_id or self.run_id,
            "--request",
            json.dumps(request or {"goal": "Ship portable graph-flow lifecycle controls."}),
        )

    def plan_run(self, *, definition: dict | None = None, requirements: dict | None = None) -> dict:
        return self.command(
            "plan",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--definition",
            json.dumps(definition or self.planned_definition()),
            "--requirements",
            json.dumps(requirements or self.requirements()),
        )

    def cockpit(self) -> dict:
        return self.command(
            "status",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--format",
            "json",
        )

    def init_run(self, definition: dict | None = None) -> None:
        definition_path = self.write_json("definition.json", definition or self.definition())
        state = self.command(
            "init",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--definition",
            str(definition_path),
        )
        self.assertEqual(state["status"], "awaiting_approval")

    def tick(self) -> dict:
        return self.command("tick", "--repo", str(self.repo), "--run-id", self.run_id)

    def approve(self) -> None:
        self.command("approve", "--repo", str(self.repo), "--run-id", self.run_id)

    def register(self, node: str, task_id: str) -> None:
        self.task_ids[node] = task_id
        self.command(
            "register",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            node,
            "--task-id",
            task_id,
        )

    def complete(self, node: str, result: dict, *, task_id: str | None = None, succeeds: bool = True) -> dict:
        result_path = self.write_json(f"{node}-{result.get('outcome', 'result')}.json", result)
        return self.command(
            "complete",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            node,
            "--task-id",
            task_id or self.task_ids[node],
            "--result",
            str(result_path),
            succeeds=succeeds,
        )

    def advance_to_modern_verification(self) -> None:
        self.approve()
        self.assertEqual(self.tick()["nodes"], ["inspect"])
        self.register("inspect", "inspect-1")
        self.complete("inspect", {"outcome": "modern", "evidence": {"detected": "v2"}})
        self.assertEqual(self.tick()["nodes"], ["modern-work"])
        self.register("modern-work", "modern-1")
        self.complete("modern-work", {"outcome": "done", "evidence": {"commit": "abc123"}})
        self.assertEqual(self.tick()["nodes"], ["verify-modern"])
        self.register("verify-modern", "verify-1")

    def test_tick_requires_approval_then_routes_only_selected_branch(self) -> None:
        self.init_run()
        self.assertEqual(self.tick()["action"], "await_approval")

        self.approve()
        self.assertEqual(self.tick()["nodes"], ["inspect"])
        self.register("inspect", "inspect-1")
        self.complete("inspect", {"outcome": "modern", "evidence": {"detected": "v2"}})

        next_action = self.tick()
        self.assertEqual(next_action["action"], "dispatch")
        self.assertEqual(next_action["nodes"], ["modern-work"])

        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(summary["nodes"]["legacy-work"]["status"], "skipped")

    def test_rejected_verification_requeues_implementation_and_bounded_loop_completes(self) -> None:
        self.init_run()
        self.advance_to_modern_verification()
        self.complete(
            "verify-modern",
            {
                "outcome": "rejected",
                "evidence": {"command": "python -m unittest", "exit_code": 1, "observed": "broken"},
            },
        )
        repair = self.tick()
        self.assertEqual(repair["nodes"], ["modern-work"])
        self.assertEqual(repair["envelopes"][0]["feedback"][0]["result"]["evidence"]["observed"], "broken")

        self.register("modern-work", "modern-2")
        self.complete("modern-work", {"outcome": "done", "evidence": {"commit": "def456"}})
        self.assertEqual(self.tick()["nodes"], ["verify-modern"])
        self.register("verify-modern", "verify-2")
        self.complete("verify-modern", {"outcome": "passed", "evidence": {"command": "python -m unittest", "exit_code": 0}})
        self.assertEqual(self.tick()["action"], "complete")

    def test_repair_requeue_resets_full_downstream_closure_but_not_unrelated_branches(self) -> None:
        """A verifier rejection must reopen every completed node downstream of its repair target."""

        definition = {
            "version": 1,
            "max_concurrency": 2,
            "limits": {"max_attempts_per_node": 3, "max_transitions": 50},
            "nodes": [
                {"id": "implement", "kind": "implementation", "outcomes": ["done"]},
                {
                    "id": "integrate",
                    "kind": "integration",
                    "depends_on": [{"node": "implement", "outcome": "done"}],
                    "outcomes": ["done"],
                },
                {
                    "id": "verify",
                    "kind": "verification",
                    "depends_on": [{"node": "integrate", "outcome": "done"}],
                    "outcomes": ["passed", "rejected"],
                    "transitions": {"rejected": "implement"},
                },
                {"id": "unrelated", "kind": "implementation", "outcomes": ["done"]},
            ],
        }
        self.init_run(definition)
        self.approve()
        self.tick()
        self.register("implement", "implement-1")
        self.register("unrelated", "unrelated-1")
        self.complete("implement", {"outcome": "done", "evidence": {"revision": 1}})
        self.complete("unrelated", {"outcome": "done", "evidence": {"branch": "unrelated"}})
        self.tick()
        self.register("integrate", "integrate-1")
        self.complete("integrate", {"outcome": "done", "evidence": {"revision": 1}})
        self.tick()
        self.register("verify", "verify-1")
        self.complete(
            "verify",
            {"outcome": "rejected", "evidence": {"command": "tests", "exit_code": 1}},
        )

        repair_state = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(repair_state["nodes"]["implement"]["status"], "pending")
        self.assertEqual(repair_state["nodes"]["integrate"]["status"], "pending")
        self.assertEqual(repair_state["nodes"]["verify"]["status"], "pending")
        self.assertEqual(repair_state["nodes"]["unrelated"]["status"], "completed")
        self.assertEqual(repair_state["nodes"]["unrelated"]["attempts"], 1)
        self.assertEqual(repair_state["nodes"]["unrelated"]["result"]["evidence"], {"branch": "unrelated"})

        self.assertEqual(self.tick()["nodes"], ["implement"])
        self.register("implement", "implement-2")
        self.complete("implement", {"outcome": "done", "evidence": {"revision": 2}})
        self.assertEqual(self.tick()["nodes"], ["integrate"])
        self.register("integrate", "integrate-2")
        self.complete("integrate", {"outcome": "done", "evidence": {"revision": 2}})
        next_action = self.tick()
        self.assertEqual(next_action["action"], "dispatch")
        self.assertEqual(next_action["nodes"], ["verify"])

    def test_repair_blocks_when_transitive_downstream_verifier_is_still_running(self) -> None:
        """Repair must not reopen an ancestor beneath a concurrently running descendant."""

        definition = {
            "version": 1,
            "max_concurrency": 2,
            "limits": {"max_attempts_per_node": 3, "max_transitions": 50},
            "nodes": [
                {"id": "implement", "kind": "implementation", "outcomes": ["done"]},
                {
                    "id": "integrate",
                    "kind": "integration",
                    "depends_on": [{"node": "implement", "outcome": "done"}],
                    "outcomes": ["done"],
                },
                {
                    "id": "verifier-a",
                    "kind": "verification",
                    "depends_on": [{"node": "integrate", "outcome": "done"}],
                    "outcomes": ["passed", "rejected"],
                    "transitions": {"rejected": "implement"},
                },
                {
                    "id": "verifier-b",
                    "kind": "verification",
                    "depends_on": [{"node": "integrate", "outcome": "done"}],
                    "outcomes": ["passed"],
                },
            ],
        }
        self.init_run(definition)
        self.approve()
        self.tick()
        self.register("implement", "implement-1")
        self.complete("implement", {"outcome": "done", "evidence": {"revision": 1}})
        self.tick()
        self.register("integrate", "integrate-1")
        self.complete("integrate", {"outcome": "done", "evidence": {"revision": 1}})
        self.assertEqual(self.tick()["nodes"], ["verifier-a", "verifier-b"])
        self.register("verifier-a", "verify-a-1")
        self.register("verifier-b", "verify-b-1")

        rejected = self.complete(
            "verifier-a",
            {"outcome": "rejected", "evidence": {"command": "tests-a", "exit_code": 1}},
        )
        self.assertEqual(rejected["status"], "blocked")
        self.assertIn("verifier-b=verify-b-1", rejected["reason"])
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["nodes"]["implement"]["status"], "completed")
        self.assertEqual(summary["nodes"]["integrate"]["status"], "completed")
        self.assertEqual(summary["nodes"]["verifier-a"]["status"], "completed")
        self.assertEqual(summary["nodes"]["verifier-b"]["status"], "running")
        self.assertEqual(summary["nodes"]["verifier-b"]["task_id"], "verify-b-1")
        self.assertEqual(summary["driver"]["active_tasks"], {"verifier-b": "verify-b-1"})
        durable = json.loads(Path(summary["state_path"]).read_text())
        self.assertEqual(durable["events"][-1]["event"], "blocked")
        self.assertEqual(
            durable["events"][-1]["active_descendants"],
            [{"node": "verifier-b", "task_id": "verify-b-1"}],
        )
        blocked_tick = self.tick()
        self.assertEqual(blocked_tick["action"], "blocked")
        self.assertEqual(blocked_tick["nodes"], [])

    def test_repair_blocks_when_exact_target_is_already_running(self) -> None:
        """A transition must not clear a live handle already executing the repair target."""

        definition = {
            "version": 1,
            "max_concurrency": 2,
            "limits": {"max_attempts_per_node": 3, "max_transitions": 30},
            "nodes": [
                {"id": "target", "kind": "implementation", "outcomes": ["done"]},
                {
                    "id": "verifier",
                    "kind": "verification",
                    "outcomes": ["passed", "rejected"],
                    "transitions": {"rejected": "target"},
                },
            ],
        }
        self.init_run(definition)
        self.approve()
        self.assertEqual(self.tick()["nodes"], ["target", "verifier"])
        self.register("target", "target-1")
        self.register("verifier", "verifier-1")

        rejected = self.complete(
            "verifier",
            {"outcome": "rejected", "evidence": {"command": "tests", "exit_code": 1}},
        )
        self.assertEqual(rejected["status"], "blocked")
        self.assertIn("target=target-1", rejected["reason"])
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["nodes"]["target"]["status"], "running")
        self.assertEqual(summary["nodes"]["target"]["task_id"], "target-1")
        self.assertEqual(summary["nodes"]["target"]["attempts"], 1)
        self.assertEqual(summary["driver"]["active_tasks"], {"target": "target-1"})
        self.assertEqual(summary["nodes"]["verifier"]["status"], "completed")
        durable = json.loads(Path(summary["state_path"]).read_text())
        self.assertEqual(durable["events"][-1]["event"], "blocked")
        self.assertEqual(
            durable["events"][-1]["active_target"],
            {"node": "target", "task_id": "target-1"},
        )
        tick = self.tick()
        self.assertEqual(tick["action"], "blocked")
        self.assertEqual(tick["nodes"], [])

    def test_verification_without_evidence_is_rejected(self) -> None:
        self.init_run()
        self.advance_to_modern_verification()
        error = self.complete("verify-modern", {"outcome": "passed"}, succeeds=False)
        self.assertIn("evidence", error["error"])

    def test_verification_result_requires_non_empty_object_evidence_and_object_artifacts(self) -> None:
        """Truthy scalar/list proof and artifact payloads must not enter durable state."""

        definition = {
            "version": 1,
            "nodes": [{"id": "verify", "kind": "verification", "outcomes": ["passed"]}],
        }
        for index, evidence in enumerate(("proof", ["proof"], {}), start=1):
            with self.subTest(evidence=evidence):
                self.run_id = f"invalid-evidence-{index}"
                self.init_run(definition)
                self.approve()
                self.tick()
                self.register("verify", f"verify-evidence-{index}")
                error = self.complete(
                    "verify",
                    {"outcome": "passed", "evidence": evidence},
                    succeeds=False,
                )
                self.assertIn("evidence", error["error"])
                self.assertIn("non-empty object", error["error"])
        for index, artifacts in enumerate(("artifact", ["artifact"]), start=1):
            with self.subTest(artifacts=artifacts):
                self.run_id = f"invalid-artifacts-{index}"
                self.init_run(definition)
                self.approve()
                self.tick()
                self.register("verify", f"verify-artifacts-{index}")
                error = self.complete(
                    "verify",
                    {
                        "outcome": "passed",
                        "evidence": {"command": "tests", "exit_code": 0},
                        "artifacts": artifacts,
                    },
                    succeeds=False,
                )
                self.assertIn("artifacts", error["error"])
                self.assertIn("object", error["error"])

    def test_human_result_requires_non_empty_object_evidence(self) -> None:
        """Human approvals must reject scalar and list evidence before state mutation."""

        definition = {
            "version": 1,
            "nodes": [{"id": "approval", "kind": "human", "outcomes": ["approved"]}],
        }
        for index, evidence in enumerate(("human", ["human"]), start=1):
            with self.subTest(evidence=evidence):
                self.run_id = f"invalid-human-evidence-{index}"
                self.init_run(definition)
                self.approve()
                self.tick()
                error = self.command(
                    "approve",
                    "--repo",
                    str(self.repo),
                    "--run-id",
                    self.run_id,
                    "--node",
                    "approval",
                    "--result-json",
                    json.dumps({"outcome": "approved", "evidence": evidence}),
                    succeeds=False,
                )
                self.assertIn("evidence", error["error"])
                self.assertIn("non-empty object", error["error"])

    def test_all_executable_kinds_validate_present_evidence_and_artifacts_as_objects(self) -> None:
        """Optional result payloads must keep one object shape across worker node kinds."""

        cases = (
            ("evidence", "scalar"),
            ("evidence", ["list"]),
            ("artifacts", "scalar"),
            ("artifacts", ["list"]),
        )
        sequence = 0
        for kind in ("decision", "implementation", "integration"):
            for field, invalid in cases:
                sequence += 1
                with self.subTest(kind=kind, field=field, invalid=invalid):
                    self.run_id = f"invalid-{kind}-{field}-{sequence}"
                    definition = {
                        "version": 1,
                        "nodes": [{"id": "work", "kind": kind, "outcomes": ["done"]}],
                    }
                    self.init_run(definition)
                    self.approve()
                    self.tick()
                    self.register("work", f"work-{sequence}")
                    error = self.complete(
                        "work",
                        {"outcome": "done", field: invalid},
                        succeeds=False,
                    )
                    self.assertIn(field, error["error"])
                    self.assertIn("object", error["error"])

    def test_attempt_limit_blocks_the_graph(self) -> None:
        self.init_run(self.definition(max_attempts=1))
        self.advance_to_modern_verification()
        result = self.complete(
            "verify-modern",
            {"outcome": "rejected", "evidence": {"command": "tests", "exit_code": 1}},
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.tick()["action"], "blocked")

    def test_stale_or_duplicate_completion_cannot_overwrite_state(self) -> None:
        self.init_run()
        self.approve()
        self.tick()
        self.register("inspect", "inspect-1")
        self.complete("inspect", {"outcome": "modern", "evidence": {"detected": "v2"}})
        error = self.complete("inspect", {"outcome": "legacy", "evidence": {"detected": "v1"}}, succeeds=False)
        self.assertIn("not running", error["error"])

    def test_complete_requires_the_handle_that_was_registered_for_the_node(self) -> None:
        self.init_run()
        self.approve()
        self.tick()
        self.register("inspect", "inspect-1")
        error = self.complete(
            "inspect",
            {"outcome": "modern", "evidence": {"detected": "v2"}},
            task_id="unregistered-handle",
            succeeds=False,
        )
        self.assertIn("task handle", error["error"])

    def test_claim_blocks_redispatch_until_the_durable_handle_is_attached(self) -> None:
        self.init_run()
        self.approve()
        self.command(
            "claim",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
        )
        self.assertEqual(self.tick()["action"], "wait")
        reconciliation = self.command("reconcile", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(reconciliation["unattached_claims"], ["inspect"])
        self.command(
            "attach",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
            "--task-id",
            "inspect-1",
        )
        self.complete("inspect", {"outcome": "modern", "evidence": {"detected": "v2"}}, task_id="inspect-1")

    def test_unclaim_releases_an_orphaned_claim_for_redispatch(self) -> None:
        self.init_run()
        self.approve()
        self.command(
            "claim",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
        )

        result = self.command(
            "unclaim",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
        )
        self.assertEqual(result["status"], "running")

        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        record = summary["nodes"]["inspect"]
        self.assertEqual(record["status"], "pending")
        self.assertIsNone(record["task_id"])
        self.assertEqual(record["attempts"], 0)
        self.assertNotIn("inspect", summary["driver"]["active_tasks"])
        durable_state = json.loads(Path(summary["state_path"]).read_text())
        self.assertEqual(durable_state["events"][-1]["event"], "unclaimed")
        self.assertEqual(self.tick()["nodes"], ["inspect"])

    def test_unclaim_rejects_a_wrong_or_attached_claim_without_changing_state(self) -> None:
        self.init_run()
        self.approve()
        self.command(
            "claim",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
        )
        wrong_claim = self.command(
            "unclaim",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "other-claim",
            succeeds=False,
        )
        self.assertIn("not claimed", wrong_claim["error"])

        self.command(
            "attach",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
            "--task-id",
            "inspect-1",
        )
        attached_claim = self.command(
            "unclaim",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
            succeeds=False,
        )
        self.assertIn("not claimed", attached_claim["error"])
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(summary["nodes"]["inspect"]["status"], "running")
        self.assertEqual(summary["nodes"]["inspect"]["task_id"], "inspect-1")

    def test_human_node_requires_explicit_in_run_approval(self) -> None:
        definition = self.definition()
        definition["nodes"].append(
            {
                "id": "release-approval",
                "kind": "human",
                "depends_on": [{"node": "verify-modern", "outcome": "passed"}],
                "outcomes": ["approved", "declined"],
                "failure_outcomes": ["declined"],
            }
        )
        self.init_run(definition)
        self.advance_to_modern_verification()
        self.complete("verify-modern", {"outcome": "passed", "evidence": {"command": "tests", "exit_code": 0}})
        gate = self.tick()
        self.assertEqual(gate["action"], "await_approval")
        self.assertEqual(gate["nodes"], ["release-approval"])
        approval = self.write_json("release-approved.json", {"outcome": "approved", "evidence": {"human": "release-manager"}})
        self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "release-approval",
            "--result",
            str(approval),
        )
        self.assertEqual(self.tick()["action"], "complete")

    def test_human_decision_loop_counts_against_the_node_attempt_limit(self) -> None:
        definition = {
            "version": 1,
            "max_concurrency": 1,
            "limits": {"max_attempts_per_node": 1, "max_transitions": 10},
            "nodes": [
                {
                    "id": "confirmation",
                    "kind": "human",
                    "outcomes": ["again", "approved"],
                    "transitions": {"again": "confirmation"},
                }
            ],
        }
        self.init_run(definition)
        self.approve()
        self.assertEqual(self.tick()["nodes"], ["confirmation"])
        result_path = self.write_json("ask-again.json", {"outcome": "again", "evidence": {"human": "reviewer"}})
        result = self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "confirmation",
            "--result",
            str(result_path),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("retry limit", result["reason"])

    def test_failure_outcome_blocks_instead_of_reporting_successful_completion(self) -> None:
        definition = {
            "version": 1,
            "max_concurrency": 1,
            "nodes": [
                {
                    "id": "migration",
                    "kind": "integration",
                    "outcomes": ["done", "failed"],
                    "failure_outcomes": ["failed"],
                }
            ],
        }
        self.init_run(definition)
        self.approve()
        self.tick()
        self.register("migration", "migration-1")
        result = self.complete("migration", {"outcome": "failed", "evidence": {"command": "migrate", "exit_code": 1}})
        self.assertEqual(result["status"], "blocked")
        self.assertIn("failure outcome", result["reason"])

    def test_any_of_branch_join_and_resource_conflicts_are_computed_by_tick(self) -> None:
        definition = {
            "version": 1,
            "max_concurrency": 2,
            "nodes": [
                {"id": "detect", "kind": "decision", "outcomes": ["legacy", "modern"]},
                {
                    "id": "legacy",
                    "kind": "implementation",
                    "depends_on": [{"node": "detect", "outcome": "legacy"}],
                    "outcomes": ["done"],
                    "resources": ["adapter"],
                },
                {
                    "id": "modern",
                    "kind": "implementation",
                    "depends_on": [{"node": "detect", "outcome": "modern"}],
                    "outcomes": ["done"],
                    "resources": ["adapter"],
                },
                {
                    "id": "shared",
                    "kind": "integration",
                    "depends_on_any": [
                        {"node": "legacy", "outcome": "done"},
                        {"node": "modern", "outcome": "done"}
                    ],
                    "outcomes": ["done"],
                },
            ],
        }
        self.init_run(definition)
        self.approve()
        self.register("detect", "detect-1")
        self.complete("detect", {"outcome": "modern", "evidence": {"detected": "v2"}})
        self.assertEqual(self.tick()["nodes"], ["modern"])
        self.register("modern", "modern-1")
        self.complete("modern", {"outcome": "done", "evidence": {"commit": "abc123"}})
        self.assertEqual(self.tick()["nodes"], ["shared"])

        contested = {
            "version": 1,
            "max_concurrency": 2,
            "nodes": [
                {"id": "a", "kind": "implementation", "outcomes": ["done"], "resources": ["lockfile"]},
                {"id": "b", "kind": "implementation", "outcomes": ["done"], "resources": ["lockfile"]},
                {"id": "c", "kind": "implementation", "outcomes": ["done"], "resources": ["docs"]},
            ],
        }
        second_repo = Path(self.tempdir.name) / "second-repo"
        second_repo.mkdir()
        second_definition = self.write_json("contested.json", contested)
        self.command("init", "--repo", str(second_repo), "--run-id", "contested", "--definition", str(second_definition))
        self.command("approve", "--repo", str(second_repo), "--run-id", "contested")
        self.assertEqual(self.command("tick", "--repo", str(second_repo), "--run-id", "contested")["nodes"], ["a", "c"])

    def test_uses_shared_git_common_directory_or_portable_non_git_fallback(self) -> None:
        self.init_run()
        self.assertTrue((self.repo / ".agent-skills" / "graph-flow" / self.run_id / "state.json").exists())

        git_repo = Path(self.tempdir.name) / "git-repo"
        git_repo.mkdir()
        subprocess.run(["git", "init", "-q", str(git_repo)], check=True)
        definition_path = self.write_json("git-definition.json", self.definition())
        self.command(
            "init",
            "--repo",
            str(git_repo),
            "--run-id",
            "git-run",
            "--definition",
            str(definition_path),
        )
        self.assertTrue((git_repo / ".git" / "graph-flow" / "git-run" / "state.json").exists())

    def test_invalid_graph_definition_is_rejected_before_state_is_created(self) -> None:
        invalid = self.definition()
        invalid["nodes"][1]["depends_on"] = [{"node": "missing", "outcome": "done"}]
        definition_path = self.write_json("invalid.json", invalid)
        error = self.command(
            "init",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--definition",
            str(definition_path),
            succeeds=False,
        )
        self.assertIn("unknown node", error["error"])

    def test_planned_graph_requires_complete_plan_metadata_and_known_workstreams(self) -> None:
        """Removing planning facts must reject a graph that opts into planned mode."""

        cases = [
            (
                "missing-node-objective",
                lambda definition: definition["nodes"][0].pop("objective"),
                "objective",
            ),
            (
                "missing-workstream-title",
                lambda definition: definition["workstreams"][0].pop("title"),
                "workstream",
            ),
            (
                "missing-role",
                lambda definition: definition["nodes"][0].pop("assigned_role"),
                "assigned_role",
            ),
            (
                "missing-criteria",
                lambda definition: definition["nodes"][0].pop("acceptance_criteria"),
                "acceptance_criteria",
            ),
            (
                "invalid-role-type",
                lambda definition: definition["nodes"][0].update({"assigned_role": []}),
                "assigned_role",
            ),
            (
                "unknown-workstream",
                lambda definition: definition["nodes"][0].update({"workstream": "missing"}),
                "workstream",
            ),
            (
                "invalid-priority",
                lambda definition: definition["nodes"][0].update({"priority": "soon"}),
                "priority",
            ),
            (
                "invalid-priority-type",
                lambda definition: definition["nodes"][0].update({"priority": []}),
                "priority",
            ),
        ]
        for name, mutate, expected_error in cases:
            with self.subTest(name=name):
                definition = self.planned_definition()
                mutate(definition)
                definition_path = self.write_json(f"{name}.json", definition)
                error = self.command(
                    "init",
                    "--repo",
                    str(self.repo),
                    "--run-id",
                    name,
                    "--definition",
                    str(definition_path),
                    succeeds=False,
                )
                self.assertIn(expected_error, error["error"])

    def test_planned_human_nodes_require_human_role_but_may_omit_executable_fields(self) -> None:
        """Human approvals are explicitly assigned and do not need executable-only fields."""

        definition = self.planned_definition()
        human = {
            "id": "approve",
            "kind": "human",
            "workstream": "engine",
            "objective": "Approve the execution plan.",
            "assigned_role": "human",
            "priority": "critical",
            "outcomes": ["approved"],
        }
        definition["nodes"] = [human]
        self.init_run(definition)

        human["assigned_role"] = "worker"
        definition_path = self.write_json("human-wrong-role.json", definition)
        error = self.command(
            "init",
            "--repo",
            str(self.repo),
            "--run-id",
            "human-wrong-role",
            "--definition",
            str(definition_path),
            succeeds=False,
        )
        self.assertIn("human", error["error"])

    def test_planned_executable_nodes_require_non_empty_paths(self) -> None:
        """Every executable planned node must declare concrete, non-empty path strings."""

        cases = (
            ("missing", lambda node: node.pop("paths"), "paths"),
            ("empty", lambda node: node.update({"paths": []}), "paths"),
            (
                "non-string",
                lambda node: node.update({"paths": [123]}),
                "paths must be a non-empty list of non-empty strings",
            ),
            (
                "empty-string",
                lambda node: node.update({"paths": [""]}),
                "paths must be a non-empty list of non-empty strings",
            ),
            (
                "mixed-non-string",
                lambda node: node.update({"paths": ["valid/path", 1]}),
                "paths must be a non-empty list of non-empty strings",
            ),
            (
                "mixed-empty-string",
                lambda node: node.update({"paths": ["valid/path", ""]}),
                "paths must be a non-empty list of non-empty strings",
            ),
        )
        for kind in ("decision", "implementation", "verification", "integration"):
            for name, mutate, expected_error in cases:
                with self.subTest(kind=kind, case=name):
                    definition = self.planned_definition()
                    node = definition["nodes"][0]
                    node.update({"id": f"{kind}-node", "kind": kind})
                    definition["nodes"] = [node]
                    mutate(node)
                    definition_path = self.write_json(f"{kind}-paths-{name}.json", definition)
                    error = self.command(
                        "init",
                        "--repo",
                        str(self.repo),
                        "--run-id",
                        f"{kind}-paths-{name}",
                        "--definition",
                        str(definition_path),
                        succeeds=False,
                    )
                    self.assertIn(expected_error, error["error"])
                    self.assertNotIn("internal graph-state error", error["error"])

    def test_planned_executable_nodes_require_non_empty_verification_commands(self) -> None:
        """Every executable planned node must provide runnable, non-empty verification commands."""

        cases = (
            ("missing", lambda node: node.pop("verification_commands"), "verification_commands"),
            ("empty", lambda node: node.update({"verification_commands": []}), "verification_commands"),
            (
                "non-string",
                lambda node: node.update({"verification_commands": [123]}),
                "verification_commands must be a non-empty list of non-empty strings",
            ),
            (
                "empty-string",
                lambda node: node.update({"verification_commands": [""]}),
                "verification_commands must be a non-empty list of non-empty strings",
            ),
            (
                "mixed-non-string",
                lambda node: node.update({"verification_commands": ["pytest", 123]}),
                "verification_commands must be a non-empty list of non-empty strings",
            ),
            (
                "mixed-empty-string",
                lambda node: node.update({"verification_commands": ["pytest", ""]}),
                "verification_commands must be a non-empty list of non-empty strings",
            ),
        )
        for kind in ("decision", "implementation", "verification", "integration"):
            for name, mutate, expected_error in cases:
                with self.subTest(kind=kind, case=name):
                    definition = self.planned_definition()
                    node = definition["nodes"][0]
                    node.update({"id": f"{kind}-node", "kind": kind})
                    definition["nodes"] = [node]
                    mutate(node)
                    definition_path = self.write_json(f"{kind}-commands-{name}.json", definition)
                    error = self.command(
                        "init",
                        "--repo",
                        str(self.repo),
                        "--run-id",
                        f"{kind}-commands-{name}",
                        "--definition",
                        str(definition_path),
                        succeeds=False,
                    )
                    self.assertIn(expected_error, error["error"])
                    self.assertNotIn("internal graph-state error", error["error"])

    def test_plan_rejects_malformed_planned_executable_fields(self) -> None:
        """The lifecycle plan command must enforce the same executable-node contract as init."""

        self.start_run()
        cases = (
            ("paths", lambda node: node.pop("paths")),
            ("verification_commands", lambda node: node.update({"verification_commands": []})),
        )
        for field, mutate in cases:
            with self.subTest(field=field):
                definition = self.planned_definition()
                mutate(definition["nodes"][0])
                error = self.command(
                    "plan",
                    "--repo",
                    str(self.repo),
                    "--run-id",
                    self.run_id,
                    "--definition",
                    json.dumps(definition),
                    "--requirements",
                    json.dumps(self.requirements()),
                    succeeds=False,
                )
                self.assertIn(field, error["error"])
                self.assertNotIn("internal graph-state error", error["error"])

    def test_static_dependency_cycles_are_rejected_during_initialization(self) -> None:
        """A static cycle must fail validation instead of later becoming a deadlock."""

        definition = self.planned_definition()
        definition["nodes"] = [
            {
                "id": "first",
                "kind": "implementation",
                "workstream": "engine",
                "objective": "Complete the first step.",
                "assigned_role": "worker",
                "priority": "high",
                "acceptance_criteria": ["First completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "depends_on": [{"node": "second", "outcome": "done"}],
                "outcomes": ["done"],
            },
            {
                "id": "second",
                "kind": "implementation",
                "workstream": "engine",
                "objective": "Complete the second step.",
                "assigned_role": "worker",
                "priority": "high",
                "acceptance_criteria": ["Second completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "depends_on": [{"node": "first", "outcome": "done"}],
                "outcomes": ["done"],
            },
        ]
        definition_path = self.write_json("static-cycle.json", definition)
        error = self.command(
            "init",
            "--repo",
            str(self.repo),
            "--run-id",
            "static-cycle",
            "--definition",
            str(definition_path),
            succeeds=False,
        )
        self.assertIn("static dependency cycle", error["error"])

    def test_planned_scheduler_dispatches_priority_enum_first(self) -> None:
        """An urgent independent work item must win over declaration order."""

        definition = self.planned_definition(max_concurrency=2)
        definition["nodes"] = [
            {
                "id": "later",
                "kind": "implementation",
                "workstream": "engine",
                "objective": "Complete later work.",
                "assigned_role": "worker",
                "priority": "low",
                "acceptance_criteria": ["Later completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "outcomes": ["done"],
            },
            {
                "id": "urgent",
                "kind": "implementation",
                "workstream": "engine",
                "objective": "Complete critical work.",
                "assigned_role": "worker",
                "priority": "critical",
                "acceptance_criteria": ["Urgent completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "outcomes": ["done"],
            },
            {
                "id": "normal",
                "kind": "implementation",
                "workstream": "engine",
                "objective": "Complete normal work.",
                "assigned_role": "worker",
                "priority": "normal",
                "acceptance_criteria": ["Normal completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "outcomes": ["done"],
            },
        ]
        self.init_run(definition)
        self.approve()
        self.assertEqual(self.tick()["nodes"], ["urgent", "normal"])

    def test_planned_scheduler_requires_ready_human_approval_before_dispatching_executable_work(self) -> None:
        """Removing the human-first scheduler branch would dispatch executable work before approval."""

        definition = self.planned_definition(max_concurrency=2)
        definition["nodes"] = [
            {
                "id": "release-approval",
                "kind": "human",
                "workstream": "quality",
                "objective": "Approve work before the implementation begins.",
                "assigned_role": "human",
                "priority": "low",
                "outcomes": ["approved"],
            },
            {
                "id": "implement",
                "kind": "implementation",
                "workstream": "engine",
                "objective": "Implement the approved work.",
                "assigned_role": "worker",
                "priority": "critical",
                "acceptance_criteria": ["The approved work is implemented."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "outcomes": ["done"],
            },
        ]
        self.start_run()
        self.plan_run(definition=definition)
        self.approve()

        gate = self.tick()
        self.assertEqual(gate["action"], "await_approval")
        self.assertEqual(gate["nodes"], ["release-approval"])
        self.assertEqual(gate["envelopes"][0]["kind"], "human")

        approval = self.write_json("release-approved.json", {"outcome": "approved", "evidence": {"human": "release-manager"}})
        self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "release-approval",
            "--result",
            str(approval),
        )

        dispatch = self.tick()
        self.assertEqual(dispatch["action"], "dispatch")
        self.assertEqual(dispatch["nodes"], ["implement"])

    def test_planned_scheduler_uses_downstream_unlock_count_before_declaration_order(self) -> None:
        """Equal-priority sources that unblock more work must dispatch first."""

        definition = self.planned_definition(max_concurrency=1)
        definition["nodes"] = [
            {
                "id": "a-standalone",
                "kind": "implementation",
                "workstream": "engine",
                "objective": "Complete standalone work.",
                "assigned_role": "worker",
                "priority": "high",
                "acceptance_criteria": ["Standalone completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "outcomes": ["done"],
            },
            {
                "id": "z-fanout",
                "kind": "implementation",
                "workstream": "engine",
                "objective": "Unblock related work.",
                "assigned_role": "worker",
                "priority": "high",
                "acceptance_criteria": ["Fanout completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "outcomes": ["done"],
            },
            {
                "id": "first-dependent",
                "kind": "verification",
                "workstream": "quality",
                "objective": "Verify the first dependency.",
                "assigned_role": "reviewer",
                "priority": "high",
                "acceptance_criteria": ["First dependent completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "depends_on": [{"node": "z-fanout", "outcome": "done"}],
                "outcomes": ["passed"],
            },
            {
                "id": "second-dependent",
                "kind": "integration",
                "workstream": "quality",
                "objective": "Integrate the second dependency.",
                "assigned_role": "worker",
                "priority": "high",
                "acceptance_criteria": ["Second dependent completes."],
                "paths": ["scripts/graph_state.py"],
                "verification_commands": ["python3 -m unittest discover -s tests -v"],
                "depends_on": [{"node": "z-fanout", "outcome": "done"}],
                "outcomes": ["done"],
            },
        ]
        self.init_run(definition)
        self.approve()
        self.assertEqual(self.tick()["nodes"], ["z-fanout"])

    def test_legacy_definition_without_planning_metadata_keeps_declaration_order(self) -> None:
        """Legacy definitions must remain valid and retain their previous scheduler order."""

        definition = {
            "version": 1,
            "max_concurrency": 2,
            "nodes": [
                {"id": "z-first", "kind": "implementation", "outcomes": ["done"]},
                {"id": "a-second", "kind": "implementation", "outcomes": ["done"]},
                {"id": "m-third", "kind": "implementation", "outcomes": ["done"]},
            ],
        }
        self.init_run(definition)
        self.approve()
        self.assertEqual(self.tick()["nodes"], ["z-first", "a-second"])

    def test_start_creates_unified_intake_with_repo_default_and_no_progress(self) -> None:
        """Starting without a goal must fail; valid intake must not invent graph progress."""

        invalid = self.command(
            "start",
            "--repo",
            str(self.repo),
            "--run-id",
            "invalid-intake",
            "--request",
            json.dumps({"goal": "  "}),
            succeeds=False,
        )
        self.assertIn("goal", invalid["error"])

        started = self.start_run()
        self.assertEqual(started["status"], "collecting_requirements")
        state = json.loads(Path(started["state_path"]).read_text())
        self.assertEqual(state["schema_version"], 2)
        self.assertEqual(state["intake"]["repository"], str(self.repo.resolve()))
        cockpit = self.cockpit()
        self.assertIsNone(cockpit["progress"])
        self.assertEqual(cockpit["goal"], "Ship portable graph-flow lifecycle controls.")
        self.assertNotIn("definition", cockpit)

    def test_graphless_intake_cockpit_exposes_phase_and_empty_graph_collections(self) -> None:
        """Intake projection must be UI-complete without inventing a planned graph."""

        self.start_run()
        cockpit = self.cockpit()
        self.assertEqual(cockpit.get("phase"), "collecting_requirements")
        self.assertIn("requirements", cockpit)
        self.assertIsNone(cockpit["requirements"])
        self.assertIn("max_concurrency", cockpit)
        self.assertIsNone(cockpit["max_concurrency"])
        self.assertIn("limits", cockpit)
        self.assertIsNone(cockpit["limits"])
        self.assertEqual(cockpit["workstreams"], [])
        self.assertEqual(cockpit["nodes"], [])
        self.assertEqual(cockpit["active_handles"], [])
        self.assertIn("pending_approval", cockpit)
        self.assertIsNone(cockpit["pending_approval"])
        self.assertIsNone(cockpit["node_counts"])
        self.assertIsNone(cockpit["progress"])
        self.assertIsNone(cockpit["reason"])
        self.assertTrue(cockpit["updated_at"].endswith("Z"))
        self.assertEqual(cockpit["recent_events"][-1]["event"], "started")
        self.assertEqual(cockpit["recent_events"][-1]["seq"], 1)

    def test_cockpit_merges_planned_node_metadata_runtime_state_and_recent_events(self) -> None:
        """Public status must contain every graph fact needed by the cockpit UI."""

        definition = self.planned_definition()
        self.start_run()
        self.plan_run(definition=definition)
        self.approve()
        self.tick()
        self.register("implement", "implementation-1")
        self.complete(
            "implement",
            {
                "outcome": "done",
                "evidence": {"command": "python3 -m unittest", "exit_code": 0},
                "artifacts": {"changed_paths": ["scripts/graph_state.py"]},
            },
        )
        self.tick()
        self.register("verify", "verification-1")
        self.assertEqual(self.tick()["action"], "wait")

        cockpit = self.cockpit()
        self.assertEqual(cockpit.get("phase"), "wait")
        self.assertEqual(cockpit.get("requirements"), self.requirements())
        self.assertEqual(cockpit.get("max_concurrency"), 2)
        self.assertEqual(cockpit.get("limits"), {"max_attempts_per_node": 3, "max_transitions": 100})
        self.assertEqual(
            cockpit["workstreams"],
            [
                {
                    "id": "engine",
                    "title": "State engine",
                    "objective": "Build the state-engine behavior.",
                    "status": "completed",
                    "node_counts": {"completed": 1},
                },
                {
                    "id": "quality",
                    "title": "Quality",
                    "objective": "Verify the planned graph behavior.",
                    "status": "active",
                    "node_counts": {"running": 1},
                },
            ],
        )
        self.assertEqual(
            cockpit["nodes"],
            [
                {
                    "id": "implement",
                    "workstream": "engine",
                    "kind": "implementation",
                    "status": "completed",
                    "objective": "Implement planned graph validation.",
                    "assigned_role": "worker",
                    "priority": "high",
                    "resources": [],
                    "outcomes": ["done"],
                    "transitions": {},
                    "failure_outcomes": [],
                    "prompt": "",
                    "paths": ["scripts/graph_state.py", "tests/test_graph_state.py"],
                    "verification_commands": ["python3 -m unittest discover -s tests -v"],
                    "depends_on": [],
                    "depends_on_any": [],
                    "attempts": 1,
                    "task_id": "implementation-1",
                    "acceptance_criteria": ["The engine accepts valid planned graphs."],
                    "evidence": {"command": "python3 -m unittest", "exit_code": 0},
                    "artifacts": {"changed_paths": ["scripts/graph_state.py"]},
                },
                {
                    "id": "verify",
                    "workstream": "quality",
                    "kind": "verification",
                    "status": "running",
                    "objective": "Verify planned graph validation.",
                    "assigned_role": "reviewer",
                    "priority": "high",
                    "resources": [],
                    "outcomes": ["passed"],
                    "transitions": {},
                    "failure_outcomes": [],
                    "prompt": "",
                    "paths": ["scripts/graph_state.py", "tests/test_graph_state.py"],
                    "verification_commands": ["python3 -m unittest discover -s tests -v"],
                    "depends_on": [{"node": "implement", "outcome": "done"}],
                    "depends_on_any": [],
                    "attempts": 1,
                    "task_id": "verification-1",
                    "acceptance_criteria": ["The graph validation test suite passes."],
                    "evidence": None,
                    "artifacts": None,
                },
            ],
        )
        self.assertEqual(cockpit["active_handles"], [{"node": "verify", "task_id": "verification-1"}])
        self.assertEqual(cockpit["node_counts"], {"completed": 1, "running": 1})
        self.assertEqual(cockpit["progress"], {"completed": 1, "skipped": 0, "total": 2, "ratio": 0.5})
        self.assertIsNone(cockpit["reason"])
        sequences = [item["seq"] for item in cockpit["recent_events"]]
        self.assertEqual(sequences, sorted(sequences))
        self.assertLessEqual(len(sequences), 20)
        self.assertEqual(cockpit["recent_events"][-1]["event"], "registered")
        self.assertEqual(cockpit["recent_events"][-1]["node"], "verify")

    def test_cockpit_open_request_includes_action_center_rationale_and_options(self) -> None:
        """Action Center projection must retain the human-facing reason and choices."""

        self.start_run()
        opened = self.command(
            "request",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request",
            json.dumps(
                {
                    "kind": "input",
                    "answer_type": "single_select",
                    "prompt": "Choose a runtime.",
                    "rationale": "Verification commands depend on the runtime.",
                    "options": ["python", "node"],
                }
            ),
        )
        cockpit = self.cockpit()
        self.assertEqual(cockpit.get("phase"), "await_input")
        self.assertEqual(
            cockpit["open_request"],
            {
                "id": opened["request_id"],
                "kind": "input",
                "answer_type": "single_select",
                "prompt": "Choose a runtime.",
                "rationale": "Verification commands depend on the runtime.",
                "options": ["python", "node"],
                "scope": "preflight",
                "node": None,
            },
        )
        self.assertEqual(cockpit["nodes"], [])
        self.assertEqual(cockpit["recent_events"][-1]["event"], "request_opened")
        self.assertIn("pending_approval", cockpit)
        self.assertIsNone(cockpit["pending_approval"])

    def test_cockpit_exposes_graph_level_pending_approval_after_plan(self) -> None:
        """Graph approval must be actionable without reading raw planned state."""

        self.start_run()
        self.plan_run()
        cockpit = self.cockpit()
        self.assertEqual(cockpit["status"], "awaiting_graph_approval")
        self.assertEqual(cockpit.get("requirements"), self.requirements())
        self.assertEqual(cockpit.get("max_concurrency"), 2)
        self.assertEqual(cockpit.get("limits"), {"max_attempts_per_node": 3, "max_transitions": 100})
        self.assertEqual(cockpit["requirements"]["approval_boundaries"], ["Approve the graph before dispatch."])
        self.assertEqual(cockpit["nodes"][0]["resources"], [])
        self.assertEqual(cockpit["nodes"][0]["outcomes"], ["done"])
        self.assertEqual(cockpit["nodes"][0]["transitions"], {})
        self.assertEqual(cockpit["nodes"][0]["failure_outcomes"], [])
        self.assertEqual(cockpit["nodes"][0]["prompt"], "")
        self.assertEqual(cockpit["recent_events"][-1]["event"], "plan_revised")
        self.assertEqual(
            cockpit.get("pending_approval"),
            {
                "scope": "graph",
                "node": None,
                "prompt": "Approve the planned graph.",
                "objective": "Ship portable graph-flow lifecycle controls.",
                "allowed_outcomes": ["approved"],
                "kind": "approval",
                "evidence_required": True,
            },
        )
        self.assertIsNone(cockpit["open_request"])
        self.approve()
        self.assertIsNone(self.cockpit()["pending_approval"])

    def test_cockpit_exposes_ready_planned_human_node_as_pending_approval(self) -> None:
        """Runtime human approval must publish its exact prompt, objective, and outcomes."""

        definition = {
            "version": 1,
            "workstreams": [{"id": "release", "title": "Release", "objective": "Approve the release."}],
            "nodes": [
                {
                    "id": "release-approval",
                    "kind": "human",
                    "workstream": "release",
                    "objective": "Approve deployment to production.",
                    "assigned_role": "human",
                    "priority": "critical",
                    "prompt": "Approve the production deployment?",
                    "outcomes": ["approved", "declined"],
                    "failure_outcomes": ["declined"],
                }
            ],
        }
        self.start_run()
        self.plan_run(definition=definition)
        self.approve()
        self.assertEqual(self.tick()["action"], "await_approval")

        cockpit = self.cockpit()
        self.assertEqual(cockpit["status"], "awaiting_approval")
        self.assertEqual(cockpit.get("max_concurrency"), 1)
        self.assertEqual(cockpit.get("limits"), {"max_attempts_per_node": 3, "max_transitions": 100})
        self.assertEqual(cockpit["nodes"][0]["failure_outcomes"], ["declined"])
        self.assertEqual(cockpit["nodes"][0]["prompt"], "Approve the production deployment?")
        self.assertEqual(
            cockpit.get("pending_approval"),
            {
                "scope": "node",
                "node": "release-approval",
                "prompt": "Approve the production deployment?",
                "objective": "Approve deployment to production.",
                "allowed_outcomes": ["approved", "declined"],
                "kind": "approval",
                "evidence_required": True,
            },
        )
        self.assertIsNone(cockpit["open_request"])

        inline_result = {
            "outcome": "approved",
            "evidence": {"source": "graph-flow-ui", "answer": "approved"},
        }
        missing = self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "release-approval",
            succeeds=False,
        )
        self.assertIn("exactly one", missing["error"])

        result_path = self.write_json("release-approval-result.json", inline_result)
        duplicate_sources = self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "release-approval",
            "--result",
            str(result_path),
            "--result-json",
            json.dumps(inline_result),
            succeeds=False,
        )
        self.assertIn("exactly one", duplicate_sources["error"])

        approved = self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "release-approval",
            "--result-json",
            json.dumps(inline_result),
        )
        self.assertEqual(approved["status"], "running")
        self.assertIsNone(self.cockpit()["pending_approval"])

    def test_node_approval_must_match_persisted_selected_human_gate(self) -> None:
        """A coordinator cannot approve another ready human node than the one tick selected."""

        definition = {
            "version": 1,
            "workstreams": [{"id": "gates", "title": "Gates", "objective": "Collect approvals."}],
            "nodes": [
                {
                    "id": identifier,
                    "kind": "human",
                    "workstream": "gates",
                    "objective": f"Approve {identifier}.",
                    "assigned_role": "human",
                    "priority": "critical",
                    "outcomes": ["approved"],
                }
                for identifier in ("first-gate", "second-gate")
            ],
        }
        self.start_run()
        self.plan_run(definition=definition)
        self.approve()
        selected = self.tick()
        self.assertEqual(selected["nodes"], ["first-gate"])
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        location = Path(summary["state_path"])
        before = location.read_bytes()
        result = json.dumps(
            {"outcome": "approved", "evidence": {"source": "graph-flow-ui", "answer": "approved"}}
        )
        error = self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "second-gate",
            "--result-json",
            result,
            succeeds=False,
        )
        self.assertIn("first-gate", error["error"])
        self.assertEqual(location.read_bytes(), before)

        approved = self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "first-gate",
            "--result-json",
            result,
        )
        self.assertEqual(approved["status"], "running")

    def test_cockpit_workstream_state_prioritizes_blocked_over_active_then_pending(self) -> None:
        """Workstream state must derive from member nodes with blocked precedence."""

        definition = {
            "version": 1,
            "workstreams": [{"id": "ops", "title": "Operations", "objective": "Run independent work."}],
            "max_concurrency": 2,
            "limits": {"max_attempts_per_node": 1, "max_transitions": 20},
            "nodes": [
                {
                    "id": identifier,
                    "kind": "implementation",
                    "workstream": "ops",
                    "objective": f"Execute {identifier}.",
                    "assigned_role": "worker",
                    "priority": "high",
                    "acceptance_criteria": [f"{identifier} completes."],
                    "paths": [f"src/{identifier}.py"],
                    "verification_commands": [f"python3 -m unittest tests.{identifier}"],
                    "outcomes": ["done"],
                }
                for identifier in ("needs-input", "still-running")
            ],
        }
        self.start_run()
        self.plan_run(definition=definition)
        pending = self.cockpit()["workstreams"][0]
        self.assertEqual(
            pending,
            {
                "id": "ops",
                "title": "Operations",
                "objective": "Run independent work.",
                "status": "pending",
                "node_counts": {"pending": 2},
            },
        )

        self.approve()
        self.tick()
        self.register("needs-input", "input-1")
        self.register("still-running", "running-1")
        opened = self.command(
            "request",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "needs-input",
            "--task-id",
            "input-1",
            "--request",
            json.dumps(
                {
                    "kind": "input",
                    "answer_type": "text",
                    "prompt": "Provide the missing value.",
                    "rationale": "The node cannot continue without it.",
                }
            ),
        )
        active = self.cockpit()["workstreams"][0]
        self.assertEqual(active["status"], "active")
        self.assertEqual(active["node_counts"], {"awaiting_input": 1, "running": 1})

        self.command(
            "respond",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request-id",
            opened["request_id"],
            "--answer",
            json.dumps("Use the portable value."),
        )
        blocked = self.cockpit()["workstreams"][0]
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["node_counts"], {"blocked": 1, "running": 1})

    def test_cockpit_workstream_is_completed_when_members_are_completed_or_skipped(self) -> None:
        """A mixed terminal workstream must be completed rather than pending."""

        workstream = {"id": "release", "title": "Release", "objective": "Choose and execute one path."}
        common = {
            "workstream": "release",
            "assigned_role": "worker",
            "priority": "high",
            "acceptance_criteria": ["The node reaches an allowed outcome."],
            "verification_commands": ["python3 -m unittest discover -s tests"],
        }
        definition = {
            "version": 1,
            "workstreams": [workstream],
            "nodes": [
                {
                    **common,
                    "id": "choose",
                    "kind": "decision",
                    "objective": "Choose a path.",
                    "paths": ["src/choice.py"],
                    "outcomes": ["modern", "legacy"],
                },
                {
                    **common,
                    "id": "modern",
                    "kind": "implementation",
                    "objective": "Execute the modern path.",
                    "paths": ["src/modern.py"],
                    "depends_on": [{"node": "choose", "outcome": "modern"}],
                    "outcomes": ["done"],
                },
                {
                    **common,
                    "id": "legacy",
                    "kind": "implementation",
                    "objective": "Execute the legacy path.",
                    "paths": ["src/legacy.py"],
                    "depends_on": [{"node": "choose", "outcome": "legacy"}],
                    "outcomes": ["done"],
                },
            ],
        }
        self.start_run()
        self.plan_run(definition=definition)
        self.approve()
        self.tick()
        self.register("choose", "choose-1")
        self.complete("choose", {"outcome": "modern", "evidence": {"choice": "modern"}})
        self.tick()
        self.register("modern", "modern-1")
        self.complete("modern", {"outcome": "done", "evidence": {"path": "modern"}})
        self.assertEqual(self.tick()["action"], "complete")

        projected = self.cockpit()["workstreams"][0]
        self.assertEqual(
            projected,
            {
                **workstream,
                "status": "completed",
                "node_counts": {"completed": 2, "skipped": 1},
            },
        )

    def test_preflight_requests_validate_typed_answers_and_reject_stale_responses(self) -> None:
        """Wrong typed answers, concurrent requests, and duplicate responses must be rejected."""

        self.start_run()
        request = self.command(
            "request",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request",
            json.dumps(
                {
                    "kind": "input",
                    "answer_type": "single_select",
                    "prompt": "Which runtime should be targeted?",
                    "rationale": "The verification command depends on it.",
                    "options": ["python", "node"],
                }
            ),
        )
        self.assertEqual(request["status"], "awaiting_input")
        duplicate = self.command(
            "request",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request",
            json.dumps(
                {
                    "kind": "approval",
                    "answer_type": "confirm",
                    "prompt": "Proceed?",
                    "rationale": "Only one decision may be open.",
                }
            ),
            succeeds=False,
        )
        self.assertIn("open request", duplicate["error"])

        invalid = self.command(
            "respond",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request-id",
            request["request_id"],
            "--answer",
            json.dumps("ruby"),
            succeeds=False,
        )
        self.assertIn("option", invalid["error"])
        answered = self.command(
            "respond",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request-id",
            request["request_id"],
            "--answer",
            json.dumps("python"),
        )
        self.assertEqual(answered["status"], "collecting_requirements")
        stale = self.command(
            "respond",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request-id",
            request["request_id"],
            "--answer",
            json.dumps("node"),
            succeeds=False,
        )
        self.assertIn("not open", stale["error"])

        typed_cases = [
            ("multi_select", ["tests", "docs"], ["tests", "docs"]),
            ("confirm", None, True),
            ("text", None, "Keep the state portable."),
        ]
        for index, (answer_type, options, answer) in enumerate(typed_cases, start=2):
            body = {
                "kind": "input",
                "answer_type": answer_type,
                "prompt": f"Typed answer {index}?",
                "rationale": "Exercise the public answer contract.",
            }
            if options:
                body["options"] = options
            opened = self.command(
                "request",
                "--repo",
                str(self.repo),
                "--run-id",
                self.run_id,
                "--request",
                json.dumps(body),
            )
            result = self.command(
                "respond",
                "--repo",
                str(self.repo),
                "--run-id",
                self.run_id,
                "--request-id",
                opened["request_id"],
                "--answer",
                json.dumps(answer),
            )
            self.assertEqual(result["answer"], answer)

    def test_late_responses_cannot_revive_blocked_or_stopped_runs(self) -> None:
        """An open request must not authorize a response after a terminal control transition."""

        cases = (("blocked", "block"), ("stopped", "stop"))
        for expected_status, transition in cases:
            with self.subTest(status=expected_status):
                run_id = f"late-response-{expected_status}"
                started = self.start_run(run_id=run_id, request={"goal": "Protect terminal state."})
                opened = self.command(
                    "request",
                    "--repo",
                    str(self.repo),
                    "--run-id",
                    run_id,
                    "--request",
                    json.dumps(
                        {
                            "kind": "input",
                            "answer_type": "confirm",
                            "prompt": "Continue?",
                            "rationale": "Exercise late-response rejection.",
                        }
                    ),
                )
                if transition == "block":
                    self.command(
                        "block",
                        "--repo",
                        str(self.repo),
                        "--run-id",
                        run_id,
                        "--reason",
                        "Operator blocked the run.",
                    )
                else:
                    self.command("stop-request", "--repo", str(self.repo), "--run-id", run_id)
                    self.command(
                        "stop-confirm",
                        "--repo",
                        str(self.repo),
                        "--run-id",
                        run_id,
                        "--evidence",
                        json.dumps({"handles": {}}),
                    )
                location = Path(started["state_path"])
                before = location.read_bytes()
                error = self.command(
                    "respond",
                    "--repo",
                    str(self.repo),
                    "--run-id",
                    run_id,
                    "--request-id",
                    opened["request_id"],
                    "--answer",
                    "true",
                    succeeds=False,
                )
                self.assertIn(expected_status, error["error"])
                self.assertEqual(location.read_bytes(), before)

    def test_answer_at_attempt_limit_blocks_instead_of_requeueing_unclaimable_node(self) -> None:
        """Runtime input on the final attempt must terminate safely instead of creating dead work."""

        definition = {
            "version": 1,
            "limits": {"max_attempts_per_node": 1, "max_transitions": 10},
            "nodes": [{"id": "work", "kind": "implementation", "outcomes": ["done"]}],
        }
        self.init_run(definition)
        self.approve()
        self.tick()
        self.register("work", "work-1")
        opened = self.command(
            "request",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "work",
            "--task-id",
            "work-1",
            "--request",
            json.dumps(
                {
                    "kind": "input",
                    "answer_type": "text",
                    "prompt": "Provide the missing detail.",
                    "rationale": "The final attempt cannot otherwise continue.",
                }
            ),
        )
        result = self.command(
            "respond",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request-id",
            opened["request_id"],
            "--answer",
            json.dumps("Use the portable format."),
        )
        self.assertEqual(result["status"], "blocked")
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(summary["nodes"]["work"]["status"], "blocked")
        self.assertEqual(summary["nodes"]["work"]["attempts"], 1)
        self.assertEqual(self.tick()["action"], "blocked")

    def test_plan_revisions_require_complete_requirements_and_freeze_after_approval(self) -> None:
        """Incomplete intake must not plan, revisions increment, and approval freezes the graph."""

        self.start_run()
        incomplete = self.requirements()
        incomplete["verification"] = []
        error = self.command(
            "plan",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--definition",
            json.dumps(self.planned_definition()),
            "--requirements",
            json.dumps(incomplete),
            succeeds=False,
        )
        self.assertIn("verification", error["error"])

        first = self.plan_run()
        self.assertEqual(first["status"], "awaiting_graph_approval")
        self.assertEqual(first["plan_revision"], 1)
        revised = self.planned_definition()
        revised["nodes"][0]["objective"] = "Implement the revised lifecycle contract."
        second = self.plan_run(definition=revised)
        self.assertEqual(second["plan_revision"], 2)
        self.approve()
        frozen = self.command(
            "plan",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--definition",
            json.dumps(self.planned_definition()),
            "--requirements",
            json.dumps(self.requirements()),
            succeeds=False,
        )
        self.assertIn("running", frozen["error"])

    def test_node_scoped_response_relinquishes_exact_handle_and_requeues_without_attempt_refund(self) -> None:
        """A runtime answer must preserve attempt count and add immutable feedback for redispatch."""

        self.start_run()
        self.plan_run()
        self.approve()
        self.tick()
        self.register("implement", "implementation-1")
        wrong = self.command(
            "request",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "implement",
            "--task-id",
            "wrong-handle",
            "--request",
            json.dumps(
                {
                    "kind": "input",
                    "answer_type": "text",
                    "prompt": "Which compatibility behavior is required?",
                    "rationale": "Implementation cannot proceed safely without it.",
                }
            ),
            succeeds=False,
        )
        self.assertIn("task handle", wrong["error"])

        opened = self.command(
            "request",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "implement",
            "--task-id",
            "implementation-1",
            "--request",
            json.dumps(
                {
                    "kind": "input",
                    "answer_type": "text",
                    "prompt": "Which compatibility behavior is required?",
                    "rationale": "Implementation cannot proceed safely without it.",
                }
            ),
        )
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(summary["nodes"]["implement"]["status"], "awaiting_input")
        self.assertEqual(summary["nodes"]["implement"]["attempts"], 1)
        self.assertNotIn("implement", summary["driver"]["active_tasks"])

        self.command(
            "respond",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--request-id",
            opened["request_id"],
            "--answer",
            json.dumps("Preserve the v1 completion envelope."),
        )
        dispatch = self.tick()
        self.assertEqual(dispatch["nodes"], ["implement"])
        self.assertEqual(dispatch["envelopes"][0]["attempt"], 2)
        feedback = dispatch["envelopes"][0]["feedback"][-1]
        self.assertEqual(feedback["request_id"], opened["request_id"])
        self.assertEqual(feedback["answer"], "Preserve the v1 completion envelope.")

    def test_mutating_a_v1_run_migrates_to_v2_without_losing_task_history(self) -> None:
        """Migration must preserve node identity, attempts, results, and active handles."""

        location = self.repo / ".agent-skills" / "graph-flow" / self.run_id / "state.json"
        location.parent.mkdir(parents=True)
        definition = self.definition()
        nodes = {node["id"]: {"status": "pending", "attempts": 0, "task_id": None, "result": None, "feedback": [], "revision": 0} for node in definition["nodes"]}
        nodes["inspect"].update(
            {
                "status": "completed",
                "attempts": 2,
                "task_id": "inspect-2",
                "result": {"outcome": "modern", "evidence": {"detected": "v2"}},
            }
        )
        nodes["modern-work"].update({"status": "running", "attempts": 1, "task_id": "modern-1"})
        legacy = {
            "schema_version": 1,
            "run_id": self.run_id,
            "repo": str(self.repo),
            "state_path": str(location),
            "status": "running",
            "reason": None,
            "definition": definition,
            "nodes": nodes,
            "driver": {"phase": "wait", "active_tasks": {"modern-work": "modern-1"}, "last_tick_at": None},
            "transition_count": 3,
            "events": [{"at": "2026-01-01T00:00:00Z", "event": "initialized"}],
        }
        location.write_text(json.dumps(legacy))

        self.command(
            "milestone",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--event",
            json.dumps({"name": "migration-checked", "message": "The legacy state remains intact."}),
        )
        migrated = json.loads(location.read_text())
        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(migrated["nodes"]["inspect"]["attempts"], 2)
        self.assertEqual(migrated["nodes"]["inspect"]["result"]["outcome"], "modern")
        self.assertEqual(migrated["driver"]["active_tasks"], {"modern-work": "modern-1"})
        self.assertIn("state_migrated", [item["event"] for item in migrated["events"]])

    def test_milestones_are_coordinator_only_and_events_keep_monotonic_latest_500(self) -> None:
        """Milestones must not spoof task events and event retention must preserve sequence."""

        started = self.start_run()
        spoofed = self.command(
            "milestone",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--event",
            json.dumps({"name": "worker-finished", "message": "Spoofed.", "node": "implement"}),
            succeeds=False,
        )
        self.assertIn("coordinator", spoofed["error"])

        location = Path(started["state_path"])
        state = json.loads(location.read_text())
        state["events"] = [
            {"seq": sequence, "at": "2026-01-01T00:00:00Z", "event": "milestone", "name": f"m-{sequence}", "message": "seed"}
            for sequence in range(1, 501)
        ]
        state["next_event_seq"] = 501
        location.write_text(json.dumps(state))
        self.command(
            "milestone",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--event",
            json.dumps({"name": "latest", "message": "Keep only the latest five hundred."}),
        )
        retained = json.loads(location.read_text())["events"]
        self.assertEqual(len(retained), 500)
        self.assertEqual(retained[0]["seq"], 2)
        self.assertEqual(retained[-1]["seq"], 501)

    def test_cockpit_progress_can_regress_when_completed_work_is_reopened(self) -> None:
        """A repair loop must reduce progress when previously completed work is reopened."""

        self.init_run()
        self.advance_to_modern_verification()
        before = self.cockpit()
        self.assertEqual(before["progress"]["ratio"], 0.75)
        self.complete(
            "verify-modern",
            {"outcome": "rejected", "evidence": {"command": "tests", "exit_code": 1}},
        )
        after = self.cockpit()
        self.assertEqual(after["progress"]["ratio"], 0.5)

    def test_pause_drains_active_handles_before_pausing_and_resume_reenables_dispatch(self) -> None:
        """Pause must block new claims, drain current work, and only resume from paused."""

        self.init_run()
        self.approve()
        self.tick()
        self.register("inspect", "inspect-1")
        requested = self.command("pause", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(requested["status"], "pause_requested")
        self.assertEqual(self.tick()["action"], "drain")
        self.complete("inspect", {"outcome": "modern", "evidence": {"detected": "v2"}})
        paused = self.tick()
        self.assertEqual(paused["action"], "paused")
        self.assertEqual(paused["status"], "paused")
        blocked_claim = self.command(
            "register",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "modern-work",
            "--task-id",
            "modern-1",
            succeeds=False,
        )
        self.assertIn("paused", blocked_claim["error"])
        resumed = self.command("resume", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(resumed["status"], "running")
        self.assertEqual(self.tick()["nodes"], ["modern-work"])

    def test_attach_rejects_stop_requested_run_without_changing_snapshotted_claim(self) -> None:
        """A stop snapshot must remain the authoritative identity for every claimed handle."""

        self.init_run()
        self.approve()
        self.command(
            "claim",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
        )
        stopped = self.command("stop-request", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(stopped["active_handles"][0]["task_id"], "claim:inspect-claim")
        location = Path(stopped["state_path"])
        before = location.read_bytes()
        error = self.command(
            "attach",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
            "--task-id",
            "inspect-1",
            succeeds=False,
        )
        self.assertIn("stop_requested", error["error"])
        self.assertEqual(location.read_bytes(), before)

        self.command(
            "stop-confirm",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--evidence",
            json.dumps({"handles": {"claim:inspect-claim": "cancelled"}}),
        )
        stopped_before = location.read_bytes()
        stopped_error = self.command(
            "attach",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
            "--task-id",
            "inspect-1",
            succeeds=False,
        )
        self.assertIn("stopped", stopped_error["error"])
        self.assertEqual(location.read_bytes(), stopped_before)

    def test_attach_finalizes_exact_claim_while_blocked_without_unblocking_graph(self) -> None:
        """A launched worker may replace its exact claim after an unrelated graph block."""

        self.init_run()
        self.approve()
        self.command(
            "claim",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
        )
        self.command(
            "block",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--reason",
            "An unrelated coordinator invariant failed.",
        )

        unrelated = self.command(
            "attach",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "unrelated-claim",
            "--task-id",
            "unrelated-handle",
            succeeds=False,
        )
        self.assertIn("not claimed", unrelated["error"])

        attached = self.command(
            "attach",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--claim-id",
            "inspect-claim",
            "--task-id",
            "inspect-1",
        )
        self.assertEqual(attached["status"], "blocked")
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["nodes"]["inspect"]["task_id"], "inspect-1")
        self.assertEqual(summary["driver"]["active_tasks"], {"inspect": "inspect-1"})
        self.assertEqual(self.tick()["action"], "blocked")

        stop = self.command("stop-request", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(stop["status"], "stop_requested")
        self.assertEqual(stop["active_handles"], [{"node": "inspect", "task_id": "inspect-1"}])

    def test_steering_requires_an_active_node_and_acknowledges_delivery_evidence(self) -> None:
        """Steering acknowledgement must be durable without changing node execution state."""

        self.init_run()
        self.approve()
        self.tick()
        self.register("inspect", "inspect-1")
        directive = self.command(
            "steer-request",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "inspect",
            "--message",
            "Check the compatibility marker before deciding.",
        )
        acknowledgement = self.command(
            "steer-ack",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--steer-id",
            directive["steer_id"],
            "--evidence",
            json.dumps({"status": "delivered", "detail": "Worker confirmed receipt."}),
        )
        self.assertEqual(acknowledgement["delivery_status"], "delivered")
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(summary["nodes"]["inspect"]["status"], "running")
        self.assertEqual(summary["nodes"]["inspect"]["task_id"], "inspect-1")

    def test_stop_is_two_phase_and_requires_terminal_evidence_for_every_handle(self) -> None:
        """Stop confirmation must not finalize while any requested handle lacks terminal evidence."""

        definition = {
            "version": 1,
            "max_concurrency": 2,
            "nodes": [
                {"id": "first", "kind": "implementation", "outcomes": ["done"]},
                {"id": "second", "kind": "implementation", "outcomes": ["done"]},
            ],
        }
        self.init_run(definition)
        self.approve()
        self.tick()
        self.register("first", "first-1")
        self.register("second", "second-1")
        requested = self.command("stop-request", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertEqual(requested["status"], "stop_requested")
        self.assertEqual({item["task_id"] for item in requested["active_handles"]}, {"first-1", "second-1"})
        incomplete = self.command(
            "stop-confirm",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--evidence",
            json.dumps({"handles": {"first-1": "cancelled"}}),
            succeeds=False,
        )
        self.assertIn("second-1", incomplete["error"])
        stopped = self.command(
            "stop-confirm",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--evidence",
            json.dumps({"handles": {"first-1": "cancelled", "second-1": "failed"}}),
        )
        self.assertEqual(stopped["status"], "stopped")

    def test_late_completion_after_confirmed_stop_is_rejected_without_mutation(self) -> None:
        """A stopped run must not accept a worker result even when its node record remains running."""

        definition = {
            "version": 1,
            "nodes": [{"id": "work", "kind": "implementation", "outcomes": ["done"]}],
        }
        self.init_run(definition)
        self.approve()
        self.tick()
        self.register("work", "work-1")
        self.command("stop-request", "--repo", str(self.repo), "--run-id", self.run_id)
        stopped = self.command(
            "stop-confirm",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--evidence",
            json.dumps({"handles": {"work-1": "cancelled"}}),
        )
        location = Path(stopped["state_path"])
        before = location.read_bytes()
        error = self.complete(
            "work",
            {"outcome": "done", "evidence": {"late": True}},
            task_id="work-1",
            succeeds=False,
        )
        self.assertIn("stopped", error["error"])
        self.assertEqual(location.read_bytes(), before)

    def test_late_completion_after_completed_run_reports_terminal_status_without_mutation(self) -> None:
        """Completed run status must reject stale results before inspecting the node record."""

        definition = {
            "version": 1,
            "nodes": [{"id": "work", "kind": "implementation", "outcomes": ["done"]}],
        }
        self.init_run(definition)
        self.approve()
        self.tick()
        self.register("work", "work-1")
        completed = self.complete("work", {"outcome": "done", "evidence": {"finished": True}})
        self.assertEqual(self.tick()["action"], "complete")
        location = Path(completed["state_path"])
        before = location.read_bytes()
        error = self.complete(
            "work",
            {"outcome": "done", "evidence": {"late": True}},
            task_id="work-1",
            succeeds=False,
        )
        self.assertIn("completed", error["error"])
        self.assertEqual(location.read_bytes(), before)

    def test_no_node_approve_cannot_bypass_a_ready_runtime_human_gate(self) -> None:
        """Graph approval without --node must be rejected once a human node is the active gate."""

        definition = {
            "version": 1,
            "nodes": [
                {
                    "id": "release",
                    "kind": "human",
                    "outcomes": ["approved"],
                }
            ],
        }
        self.init_run(definition)
        self.approve()
        self.assertEqual(self.tick()["action"], "await_approval")
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        location = Path(summary["state_path"])
        before = location.read_bytes()
        error = self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            succeeds=False,
        )
        self.assertIn("--node", error["error"])
        self.assertEqual(location.read_bytes(), before)

        approval = self.write_json(
            "runtime-human-approval.json",
            {"outcome": "approved", "evidence": {"human": "release-manager"}},
        )
        result = self.command(
            "approve",
            "--repo",
            str(self.repo),
            "--run-id",
            self.run_id,
            "--node",
            "release",
            "--result",
            str(approval),
        )
        self.assertEqual(result["status"], "running")

    def test_validate_accepts_a_graphless_intake_run(self) -> None:
        """State validation must not require a graph before planning has occurred."""

        self.start_run()
        result = self.command("validate", "--repo", str(self.repo), "--run-id", self.run_id)
        self.assertTrue(result["valid"])
        self.assertFalse(result["graph_planned"])

    def test_runs_discovers_known_runs_and_status_text_is_a_stable_projection(self) -> None:
        """Discovery must list durable runs while text status remains human-readable, not raw JSON."""

        self.start_run(run_id="intake-run", request={"goal": "Collect requirements."})
        self.start_run(run_id="another-run", request={"goal": "Plan another graph."})
        listing = self.command("runs", "--repo", str(self.repo))
        self.assertEqual([item["run_id"] for item in listing["runs"]], ["another-run", "intake-run"])
        self.assertTrue(all(item["status"] == "collecting_requirements" for item in listing["runs"]))
        self.assertTrue(all(Path(item["state_path"]).name == "state.json" for item in listing["runs"]))

        text_status = self.raw_command(
            "status",
            "--repo",
            str(self.repo),
            "--run-id",
            "intake-run",
            "--format",
            "text",
        )
        self.assertIn("Run: intake-run", text_status)
        self.assertIn("Cockpit version: 1", text_status)
        self.assertIn("Status: collecting_requirements", text_status)
        self.assertIn("Updated at:", text_status)
        self.assertIn("Progress: intake", text_status)
        self.assertIn("Node counts: none", text_status)
        self.assertFalse(text_status.startswith("{"))

    def test_run_ids_reject_posix_and_windows_anchors_without_escaping_control_root(self) -> None:
        """Run IDs must remain portable relative identifiers under graph-flow storage."""

        escaped = Path(self.tempdir.name) / "absolute-escape"
        invalid_ids = (
            str(escaped),
            "C:\\absolute\\run",
            "C:/absolute/run",
            "\\anchored\\run",
            "\\\\server\\share\\run",
        )
        for index, run_id in enumerate(invalid_ids):
            with self.subTest(run_id=run_id):
                error = self.command(
                    "start",
                    "--repo",
                    str(self.repo),
                    "--run-id",
                    run_id,
                    "--request",
                    json.dumps({"goal": "Reject path escape."}),
                    succeeds=False,
                )
                self.assertIn("run-id", error["error"])
        self.assertFalse((escaped / "state.json").exists())

        valid = self.start_run(run_id="team/nested-run", request={"goal": "Allow nested relative IDs."})
        control_root = (self.repo / ".agent-skills" / "graph-flow").resolve()
        location = Path(valid["state_path"]).resolve()
        self.assertEqual(os.path.commonpath((str(control_root), str(location))), str(control_root))

    def test_resource_path_prefixes_and_normalized_variants_are_rejected(self) -> None:
        for parent, child in (("src/auth", "src/auth/login.py"), ("src\\auth\\", "src/auth/login.py"), ("src/auth", "src/auth/")):
            with self.subTest(parent=parent, child=child):
                definition = {
                    "version": 1,
                    "max_concurrency": 2,
                    "nodes": [
                        {"id": "parent", "kind": "implementation", "outcomes": ["done"], "resources": [parent]},
                        {"id": "child", "kind": "implementation", "outcomes": ["done"], "resources": [child]},
                    ],
                }
                definition_path = self.write_json(f"overlap-{len(parent)}-{len(child)}.json", definition)
                error = self.command(
                    "init",
                    "--repo",
                    str(self.repo),
                    "--run-id",
                    f"overlap-{len(parent)}-{len(child)}",
                    "--definition",
                    str(definition_path),
                    succeeds=False,
                )
                self.assertIn("overlapping resource", error["error"])
                self.assertIn("unified logical resource key", error["error"])

    def test_recovers_a_lock_owned_by_a_provably_dead_local_process(self) -> None:
        self.init_run()
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        lock_path = Path(summary["state_path"]).with_suffix(".lock")
        lock_path.write_text(json.dumps({"pid": 999_999_999}))
        self.assertEqual(self.tick()["action"], "await_approval")

    def test_recovers_a_lock_older_than_ten_minutes_even_when_its_pid_is_alive(self) -> None:
        self.init_run()
        summary = self.command("summary", "--repo", str(self.repo), "--run-id", self.run_id)
        lock_path = Path(summary["state_path"]).with_suffix(".lock")
        lock_path.write_text(json.dumps({"pid": os.getpid()}))
        stale_time = time.time() - 601
        os.utime(lock_path, (stale_time, stale_time))

        self.assertEqual(self.tick()["action"], "await_approval")
        self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
