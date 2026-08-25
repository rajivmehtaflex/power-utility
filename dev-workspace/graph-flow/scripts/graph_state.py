#!/usr/bin/env python3
"""Deterministic state engine for the graph-flow Agent Skill.

This program deliberately contains no model calls, vendor SDKs, task spawning, or
repository mutation. A runtime-specific coordinator drives agents around it:
tick -> dispatch -> register -> complete -> tick.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterator


SCHEMA_VERSION = 2
LOCK_STALE_SECONDS = 600
EVENT_LIMIT = 500
NODE_KINDS = {"decision", "implementation", "verification", "integration", "human"}
TERMINAL_NODE_STATUSES = {"completed", "skipped"}
PLANNED_ROLES = {"explorer", "default", "worker", "reviewer", "human"}
PRIORITY_ORDER = {"critical": 0, "high": 1, "normal": 2, "low": 3}
ANSWER_TYPES = {"single_select", "multi_select", "confirm", "text"}
REQUEST_KINDS = {"input", "approval"}
TERMINAL_HANDLE_STATUSES = {"completed", "cancelled", "failed", "not_found"}
REQUIREMENT_FIELDS = {
    "goal",
    "success_criteria",
    "scope",
    "constraints",
    "verification",
    "approval_boundaries",
    "assumptions",
}


class GraphError(RuntimeError):
    """An invalid request or an invalid state transition."""


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise GraphError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GraphError(f"invalid JSON in {path}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise GraphError(f"JSON object required: {path}")
    return value


def emit(value: Any, code: int = 0) -> None:
    print(value if isinstance(value, str) else json.dumps(value, sort_keys=True))
    raise SystemExit(code)


def parse_json_value(raw: str, label: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GraphError(f"invalid JSON for {label}: {exc.msg}") from exc


def parse_json_object(raw: str, label: str) -> dict[str, Any]:
    value = parse_json_value(raw, label)
    if not isinstance(value, dict):
        raise GraphError(f"{label} must be a JSON object")
    return value


def git_common_dir(repo: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    common_dir = Path(completed.stdout.strip())
    return common_dir if common_dir.is_absolute() else repo / common_dir


def state_path(repo: Path, run_id: str) -> Path:
    windows_path = PureWindowsPath(run_id)
    parts = run_id.split("/")
    if (
        not run_id
        or "\\" in run_id
        or PurePosixPath(run_id).is_absolute()
        or bool(windows_path.anchor or windows_path.drive)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise GraphError("run-id must be a portable non-empty relative identifier")
    common_dir = git_common_dir(repo)
    root = common_dir if common_dir else repo / ".agent-skills"
    control_root = (root / "graph-flow").resolve()
    location = (control_root.joinpath(*parts) / "state.json").resolve()
    try:
        location.relative_to(control_root)
    except ValueError as exc:
        raise GraphError("resolved run state path escapes graph-flow control root") from exc
    return location


def lock_owner_is_provably_dead(lock: Path) -> bool:
    """Return true when a lock is expired or its local owner no longer exists."""

    try:
        if time.time() - lock.stat().st_mtime > LOCK_STALE_SECONDS:
            return True
    except FileNotFoundError:
        return False

    try:
        owner = read_json(lock)
        process_id = owner.get("pid")
        if not isinstance(process_id, int) or process_id <= 0:
            return False
        os.kill(process_id, 0)
    except ProcessLookupError:
        return True
    except (PermissionError, GraphError, OSError):
        return False
    return False


@contextmanager
def state_lock(path: Path) -> Iterator[None]:
    """A short cross-platform lock for state reductions.

    The coordinator is the normal single writer. The lock also rejects accidental
    simultaneous coordinator processes rather than allowing last-writer-wins.
    """

    lock = path.with_suffix(".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 5
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, json.dumps({"pid": os.getpid(), "created_at": now()}).encode())
        except FileExistsError:
            if lock_owner_is_provably_dead(lock):
                try:
                    lock.unlink()
                    continue
                except FileNotFoundError:
                    continue
            if time.monotonic() >= deadline:
                raise GraphError(f"state is locked: {lock}; do not remove it while another coordinator may be active")
            time.sleep(0.05)
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="state-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(state, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            Path(temporary).unlink()
        except FileNotFoundError:
            pass
        raise


def migrate_v1_state(state: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a v1 snapshot in memory without changing graph execution facts."""

    migrated = dict(state)
    migrated["schema_version"] = SCHEMA_VERSION
    if migrated.get("status") == "awaiting_approval":
        # V1 only used this status for initial graph approval.
        migrated["status"] = "awaiting_graph_approval"
    migrated.setdefault("intake", {"goal": "Legacy initialized graph.", "repository": migrated.get("repo")})
    migrated.setdefault("requirements", None)
    migrated.setdefault("plan_revision", 1 if migrated.get("definition") else 0)
    migrated.setdefault("plan_approved_at", None)
    migrated.setdefault("requests", [])
    migrated.setdefault("next_request_seq", 1)
    migrated.setdefault("controls", {"steering": [], "next_steer_seq": 1, "pause": None, "stop": None})
    migrated["controls"].setdefault("steering", [])
    migrated["controls"].setdefault("next_steer_seq", 1)
    migrated["controls"].setdefault("pause", None)
    migrated["controls"].setdefault("stop", None)
    timestamp = migrated.get("updated_at") or migrated.get("created_at") or now()
    migrated.setdefault("created_at", timestamp)
    migrated["updated_at"] = timestamp
    events = migrated.setdefault("events", [])
    for sequence, item in enumerate(events, start=1):
        item.setdefault("seq", sequence)
    migrated["next_event_seq"] = max((item.get("seq", 0) for item in events), default=0) + 1
    event(migrated, "state_migrated", from_version=1, to_version=SCHEMA_VERSION)
    return migrated


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GraphError(f"graph run does not exist: {path}")
    state = read_json(path)
    if state.get("schema_version") == 1:
        return migrate_v1_state(state)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise GraphError("unsupported graph-flow state schema")
    return state


def nodes_by_id(definition: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["id"]: node for node in definition["nodes"]}


def normalized_resource_path(resource: str) -> str:
    return posixpath.normpath(resource.replace("\\", "/"))


def resources_overlap(first: str, second: str) -> bool:
    if first == second:
        return False
    first_path = normalized_resource_path(first)
    second_path = normalized_resource_path(second)
    if first_path == second_path:
        return True
    return (
        first_path == "/"
        or second_path == "/"
        or second_path.startswith(f"{first_path.rstrip('/')}/")
        or first_path.startswith(f"{second_path.rstrip('/')}/")
    )


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_non_empty_string_list(identifier: str, field: str, value: Any) -> None:
    if not isinstance(value, list) or not value or not all(is_non_empty_string(item) for item in value):
        raise GraphError(f"node {identifier} {field} must be a non-empty list of non-empty strings")


def validate_planned_workstreams(definition: dict[str, Any]) -> set[str] | None:
    """Validate planning metadata when a definition opts into planned mode."""

    if "workstreams" not in definition:
        return None
    workstreams = definition["workstreams"]
    if not isinstance(workstreams, list) or not workstreams:
        raise GraphError("planned graph requires a non-empty workstreams list")
    identifiers: set[str] = set()
    for workstream in workstreams:
        if not isinstance(workstream, dict):
            raise GraphError("each workstream must be an object")
        identifier = workstream.get("id")
        if not is_non_empty_string(identifier):
            raise GraphError("each workstream requires a non-empty id")
        if identifier in identifiers:
            raise GraphError(f"duplicate workstream id: {identifier}")
        for field in ("title", "objective"):
            if not is_non_empty_string(workstream.get(field)):
                raise GraphError(f"workstream {identifier} requires a non-empty {field}")
        identifiers.add(identifier)
    return identifiers


def validate_planned_node(node: dict[str, Any], workstream_ids: set[str]) -> None:
    """Validate fields that make a node dispatchable from an approved plan."""

    identifier = node["id"]
    workstream = node.get("workstream")
    if not isinstance(workstream, str) or workstream not in workstream_ids:
        raise GraphError(f"node {identifier} references unknown workstream {workstream!r}")
    if not is_non_empty_string(node.get("objective")):
        raise GraphError(f"node {identifier} requires a non-empty objective")
    role = node.get("assigned_role")
    if not isinstance(role, str) or role not in PLANNED_ROLES:
        raise GraphError(f"node {identifier} has unsupported assigned_role")
    priority = node.get("priority")
    if not isinstance(priority, str) or priority not in PRIORITY_ORDER:
        raise GraphError(f"node {identifier} has unsupported priority")
    criteria = node.get("acceptance_criteria")
    if node["kind"] == "human":
        if role != "human":
            raise GraphError(f"human node {identifier} requires assigned_role human")
        if criteria is not None and (
            not isinstance(criteria, list) or not criteria or not all(is_non_empty_string(item) for item in criteria)
        ):
            raise GraphError(f"node {identifier} acceptance_criteria must be a non-empty string list")
        return
    if not isinstance(criteria, list) or not criteria or not all(is_non_empty_string(item) for item in criteria):
        raise GraphError(f"node {identifier} requires non-empty acceptance_criteria")
    for field in ("paths", "verification_commands"):
        require_non_empty_string_list(identifier, field, node.get(field))


def validate_static_dependencies_acyclic(nodes: list[dict[str, Any]]) -> None:
    """Reject cycles among static dependency edges; runtime transitions may loop."""

    dependencies = {
        node["id"]: [item["node"] for field in ("depends_on", "depends_on_any") for item in node.get(field, [])]
        for node in nodes
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    trail: list[str] = []

    def visit(identifier: str) -> None:
        if identifier in visiting:
            start = trail.index(identifier)
            cycle = trail[start:] + [identifier]
            raise GraphError(f"static dependency cycle: {' -> '.join(cycle)}")
        if identifier in visited:
            return
        visiting.add(identifier)
        trail.append(identifier)
        for dependency in dependencies[identifier]:
            visit(dependency)
        trail.pop()
        visiting.remove(identifier)
        visited.add(identifier)

    for node in nodes:
        visit(node["id"])


def validate_definition(definition: dict[str, Any]) -> None:
    if definition.get("version") != 1:
        raise GraphError("definition version must be 1")
    nodes = definition.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise GraphError("definition requires a non-empty nodes list")
    max_concurrency = definition.get("max_concurrency", 1)
    if not isinstance(max_concurrency, int) or max_concurrency < 1:
        raise GraphError("max_concurrency must be a positive integer")
    limits = definition.get("limits", {})
    for name, default in (("max_attempts_per_node", 3), ("max_transitions", 100)):
        value = limits.get(name, default)
        if not isinstance(value, int) or value < 1:
            raise GraphError(f"limits.{name} must be a positive integer")

    workstream_ids = validate_planned_workstreams(definition)

    identifiers: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise GraphError("each node must be an object")
        identifier = node.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise GraphError("each node requires a non-empty id")
        if identifier in identifiers:
            raise GraphError(f"duplicate node id: {identifier}")
        identifiers.add(identifier)
        if node.get("kind") not in NODE_KINDS:
            raise GraphError(f"node {identifier} has unsupported kind")
        if workstream_ids is not None:
            validate_planned_node(node, workstream_ids)
        outcomes = node.get("outcomes")
        if not isinstance(outcomes, list) or not outcomes or not all(isinstance(item, str) and item for item in outcomes):
            raise GraphError(f"node {identifier} requires non-empty string outcomes")
        if len(set(outcomes)) != len(outcomes):
            raise GraphError(f"node {identifier} has duplicate outcomes")
        for field in ("depends_on", "depends_on_any"):
            dependencies = node.get(field, [])
            if not isinstance(dependencies, list):
                raise GraphError(f"node {identifier} {field} must be a list")
            if field == "depends_on_any" and dependencies == [] and field in node:
                raise GraphError(f"node {identifier} depends_on_any must not be empty")
        resources = node.get("resources", [])
        if not isinstance(resources, list) or not all(isinstance(item, str) and item for item in resources):
            raise GraphError(f"node {identifier} resources must be a list of non-empty strings")
        if len(set(resources)) != len(resources):
            raise GraphError(f"node {identifier} has duplicate resources")
        failure_outcomes = node.get("failure_outcomes", [])
        if not isinstance(failure_outcomes, list) or any(outcome not in outcomes for outcome in failure_outcomes):
            raise GraphError(f"node {identifier} failure_outcomes must be allowed outcomes")
        transitions = node.get("transitions", {})
        if not isinstance(transitions, dict):
            raise GraphError(f"node {identifier} transitions must be an object")
        for outcome in transitions:
            if outcome not in outcomes:
                raise GraphError(f"node {identifier} transition has unknown outcome {outcome}")

    source_nodes = nodes_by_id(definition)
    for node in nodes:
        identifier = node["id"]
        for field in ("depends_on", "depends_on_any"):
            for dependency in node.get(field, []):
                if not isinstance(dependency, dict):
                    raise GraphError(f"node {identifier} has invalid dependency")
                source = dependency.get("node")
                outcome = dependency.get("outcome")
                if source not in source_nodes:
                    raise GraphError(f"node {identifier} depends on unknown node {source}")
                if outcome not in source_nodes[source]["outcomes"]:
                    raise GraphError(f"node {identifier} depends on invalid outcome {source}:{outcome}")
        for target in node.get("transitions", {}).values():
            if target not in source_nodes:
                raise GraphError(f"node {identifier} transitions to unknown node {target}")
        overlap = set(node.get("failure_outcomes", [])) & set(node.get("transitions", {}))
        if overlap:
            raise GraphError(f"node {identifier} cannot both fail and transition on {sorted(overlap)[0]}")

    validate_static_dependencies_acyclic(nodes)

    declared_resources = [
        (node["id"], resource)
        for node in nodes
        for resource in node.get("resources", [])
    ]
    for index, (first_node, first_resource) in enumerate(declared_resources):
        for second_node, second_resource in declared_resources[index + 1 :]:
            if first_node == second_node or not resources_overlap(first_resource, second_resource):
                continue
            raise GraphError(
                f"overlapping resource paths: {first_node}:{first_resource!r} and {second_node}:{second_resource!r}; "
                "use one unified logical resource key"
            )


def validate_requirements(requirements: dict[str, Any]) -> None:
    unknown = set(requirements) - REQUIREMENT_FIELDS
    missing = REQUIREMENT_FIELDS - set(requirements)
    if missing or unknown:
        detail = []
        if missing:
            detail.append(f"missing {', '.join(sorted(missing))}")
        if unknown:
            detail.append(f"unknown {', '.join(sorted(unknown))}")
        raise GraphError(f"requirements fields are invalid: {'; '.join(detail)}")
    if not is_non_empty_string(requirements["goal"]):
        raise GraphError("requirements.goal must be a non-empty string")
    for field in ("success_criteria", "verification"):
        value = requirements[field]
        if not isinstance(value, list) or not value or not all(is_non_empty_string(item) for item in value):
            raise GraphError(f"requirements.{field} must be a non-empty string list")
    for field in ("constraints", "approval_boundaries", "assumptions"):
        value = requirements[field]
        if not isinstance(value, list) or not all(is_non_empty_string(item) for item in value):
            raise GraphError(f"requirements.{field} must be a string list")
    scope = requirements["scope"]
    if not isinstance(scope, dict) or set(scope) != {"included", "excluded"}:
        raise GraphError("requirements.scope must contain exactly included and excluded")
    for field in ("included", "excluded"):
        if not isinstance(scope[field], list) or not all(is_non_empty_string(item) for item in scope[field]):
            raise GraphError(f"requirements.scope.{field} must be a string list")


def validate_intake(request: dict[str, Any], repo: Path) -> dict[str, Any]:
    if not is_non_empty_string(request.get("goal")):
        raise GraphError("initial request requires a non-empty goal")
    normalized = dict(request)
    repository = normalized.get("repository", str(repo))
    if not is_non_empty_string(repository):
        raise GraphError("initial request repository must be a non-empty string")
    normalized["repository"] = repository
    return normalized


def node_record() -> dict[str, Any]:
    return {"status": "pending", "attempts": 0, "task_id": None, "result": None, "feedback": [], "revision": 0}


def base_state(repo: Path, run_id: str, location: Path) -> dict[str, Any]:
    timestamp = now()
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "repo": str(repo),
        "state_path": str(location),
        "reason": None,
        "intake": None,
        "requirements": None,
        "definition": None,
        "plan_revision": 0,
        "plan_approved_at": None,
        "nodes": {},
        "requests": [],
        "next_request_seq": 1,
        "controls": {"steering": [], "next_steer_seq": 1, "pause": None, "stop": None},
        "driver": {"phase": "idle", "active_tasks": {}, "last_tick_at": None},
        "transition_count": 0,
        "events": [],
        "next_event_seq": 1,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    return state


def new_state(repo: Path, run_id: str, definition: dict[str, Any], location: Path) -> dict[str, Any]:
    state = base_state(repo, run_id, location)
    state.update(
        {
            "status": "awaiting_approval",
            "intake": {"goal": "Legacy initialized graph.", "repository": str(repo)},
            "definition": definition,
            "plan_revision": 1,
            "nodes": {node["id"]: node_record() for node in definition["nodes"]},
        }
    )
    state["driver"]["phase"] = "await_approval"
    event(state, "initialized")
    return state


def new_intake_state(repo: Path, run_id: str, intake: dict[str, Any], location: Path) -> dict[str, Any]:
    state = base_state(repo, run_id, location)
    state.update({"status": "collecting_requirements", "intake": intake})
    state["driver"]["phase"] = "collecting_requirements"
    event(state, "started")
    return state


def event(state: dict[str, Any], event_name: str, **fields: Any) -> None:
    timestamp = now()
    sequence = state.setdefault("next_event_seq", 1)
    state["events"].append({"seq": sequence, "at": timestamp, "event": event_name, **fields})
    state["next_event_seq"] = sequence + 1
    state["events"] = state["events"][-EVENT_LIMIT:]
    state["updated_at"] = timestamp


def count_transition(state: dict[str, Any]) -> None:
    state["transition_count"] += 1
    limit = state["definition"].get("limits", {}).get("max_transitions", 100)
    if state["transition_count"] > limit:
        state["status"] = "blocked"
        state["reason"] = f"transition limit exceeded ({limit})"
        state["driver"]["phase"] = "blocked"
        event(state, "blocked", reason=state["reason"])


def dependencies_state(state: dict[str, Any], node: dict[str, Any]) -> str:
    """Return ready, waiting, or unreachable for a pending node."""

    for dependency in node.get("depends_on", []):
        source = state["nodes"][dependency["node"]]
        if source["status"] == "completed" and source["result"]["outcome"] == dependency["outcome"]:
            continue
        if source["status"] in {"completed", "skipped", "blocked", "failed"}:
            return "unreachable"
        return "waiting"

    alternatives = node.get("depends_on_any", [])
    if alternatives:
        waiting = False
        for dependency in alternatives:
            source = state["nodes"][dependency["node"]]
            if source["status"] == "completed" and source["result"]["outcome"] == dependency["outcome"]:
                return "ready"
            if source["status"] not in {"completed", "skipped", "blocked", "failed"}:
                waiting = True
        return "waiting" if waiting else "unreachable"
    return "ready"


def normalize_pending(state: dict[str, Any]) -> None:
    definitions = nodes_by_id(state["definition"])
    changed = True
    while changed:
        changed = False
        for identifier, record in state["nodes"].items():
            if record["status"] != "pending":
                continue
            if dependencies_state(state, definitions[identifier]) == "unreachable":
                record["status"] = "skipped"
                record["revision"] += 1
                count_transition(state)
                event(state, "skipped", node=identifier)
                changed = True


def ready_nodes(state: dict[str, Any]) -> list[str]:
    definitions = nodes_by_id(state["definition"])
    ready = [
        node["id"]
        for node in state["definition"]["nodes"]
        if state["nodes"][node["id"]]["status"] == "pending"
        and dependencies_state(state, definitions[node["id"]]) == "ready"
    ]
    if "workstreams" not in state["definition"]:
        return ready

    declaration_order = {node["id"]: index for index, node in enumerate(state["definition"]["nodes"])}
    downstream_unlocks = {
        identifier: sum(
            any(dependency["node"] == identifier for field in ("depends_on", "depends_on_any") for dependency in node.get(field, []))
            for node in state["definition"]["nodes"]
        )
        for identifier in definitions
    }
    return sorted(
        ready,
        key=lambda identifier: (
            PRIORITY_ORDER[definitions[identifier]["priority"]],
            -downstream_unlocks[identifier],
            declaration_order[identifier],
        ),
    )


def select_ready_nodes(state: dict[str, Any], ready: list[str], capacity: int) -> list[str]:
    definitions = nodes_by_id(state["definition"])
    occupied = {
        resource
        for identifier, record in state["nodes"].items()
        if record["status"] == "running"
        for resource in definitions[identifier].get("resources", [])
    }
    selected: list[str] = []
    for identifier in ready:
        resources = set(definitions[identifier].get("resources", []))
        if resources & occupied:
            continue
        selected.append(identifier)
        occupied.update(resources)
        if len(selected) == capacity:
            break
    return selected


def envelope(state: dict[str, Any], identifier: str) -> dict[str, Any]:
    definition = nodes_by_id(state["definition"])[identifier]
    record = state["nodes"][identifier]
    source_ids = {item["node"] for item in definition.get("depends_on", []) + definition.get("depends_on_any", [])}
    inputs = {
        source: state["nodes"][source]["result"]
        for source in source_ids
        if state["nodes"][source]["status"] == "completed"
    }
    return {
        "run_id": state["run_id"],
        "node": identifier,
        "kind": definition["kind"],
        "attempt": record["attempts"] + 1,
        "allowed_outcomes": definition["outcomes"],
        "depends_on": definition.get("depends_on", []),
        "depends_on_any": definition.get("depends_on_any", []),
        "input_results": inputs,
        "feedback": record["feedback"],
        "prompt": definition.get("prompt", ""),
        "state_path": state["state_path"],
    }


def tick_state(state: dict[str, Any]) -> dict[str, Any]:
    state["driver"]["last_tick_at"] = now()
    if state["status"] == "collecting_requirements":
        state["driver"]["phase"] = "collecting_requirements"
        return {"action": "collect_requirements", "nodes": []}
    if state["status"] == "awaiting_input":
        state["driver"]["phase"] = "await_input"
        return {"action": "await_input", "nodes": []}
    if state["status"] == "awaiting_graph_approval":
        state["driver"]["phase"] = "await_graph_approval"
        return {"action": "await_graph_approval", "nodes": []}
    if state["status"] == "awaiting_approval":
        state["driver"]["phase"] = "await_approval"
        return {"action": "await_approval", "nodes": []}
    if state["status"] == "pause_requested":
        active = state["driver"]["active_tasks"]
        if active:
            state["driver"]["phase"] = "drain"
            return {"action": "drain", "nodes": sorted(active), "status": state["status"]}
        state["status"] = "paused"
        state["driver"]["phase"] = "paused"
        event(state, "paused")
        return {"action": "paused", "nodes": [], "status": state["status"]}
    if state["status"] == "paused":
        return {"action": "paused", "nodes": [], "status": state["status"]}
    if state["status"] == "stop_requested":
        return {"action": "stop", "nodes": sorted(state["driver"]["active_tasks"]), "status": state["status"]}
    if state["status"] == "stopped":
        return {"action": "stopped", "nodes": [], "status": state["status"]}
    if state["status"] == "blocked":
        return {"action": "blocked", "nodes": [], "reason": state["reason"]}
    if state["status"] == "completed":
        return {"action": "complete", "nodes": []}

    normalize_pending(state)
    if state["status"] == "blocked":
        return {"action": "blocked", "nodes": [], "reason": state["reason"]}

    active = state["driver"]["active_tasks"]
    capacity = state["definition"].get("max_concurrency", 1) - len(active)
    ready = ready_nodes(state)
    human_ready = [item for item in ready if nodes_by_id(state["definition"])[item]["kind"] == "human"]
    if human_ready:
        selected = human_ready[:1]
        state["status"] = "awaiting_approval"
        state["driver"]["phase"] = "await_approval"
        state["driver"]["approval_node"] = selected[0]
        return {"action": "await_approval", "nodes": selected, "envelopes": [envelope(state, item) for item in selected]}
    if ready and capacity > 0:
        selected = select_ready_nodes(state, ready, capacity)
        if not selected and active:
            state["driver"]["phase"] = "wait"
            return {"action": "wait", "nodes": sorted(active)}
        if not selected:
            state["status"] = "blocked"
            state["reason"] = "ready nodes conflict on declared resources"
            state["driver"]["phase"] = "blocked"
            event(state, "blocked", reason=state["reason"])
            return {"action": "blocked", "nodes": [], "reason": state["reason"]}
        state["driver"]["phase"] = "dispatch"
        return {"action": "dispatch", "nodes": selected, "envelopes": [envelope(state, item) for item in selected]}
    if active:
        state["driver"]["phase"] = "wait"
        return {"action": "wait", "nodes": sorted(active)}
    if all(record["status"] in TERMINAL_NODE_STATUSES for record in state["nodes"].values()):
        state["status"] = "completed"
        state["driver"]["phase"] = "complete"
        event(state, "completed")
        return {"action": "complete", "nodes": []}
    state["status"] = "blocked"
    state["reason"] = "no ready node and no active task (deadlock)"
    state["driver"]["phase"] = "blocked"
    event(state, "blocked", reason=state["reason"])
    return {"action": "blocked", "nodes": [], "reason": state["reason"]}


def downstream_closure(state: dict[str, Any], target: str) -> set[str]:
    descendants: set[str] = set()
    changed = True
    while changed:
        changed = False
        sources = descendants | {target}
        for definition in state["definition"]["nodes"]:
            identifier = definition["id"]
            dependencies = definition.get("depends_on", []) + definition.get("depends_on_any", [])
            if identifier not in descendants and any(item["node"] in sources for item in dependencies):
                descendants.add(identifier)
                changed = True
    return descendants


def reset_dependents_for_retry(state: dict[str, Any], target: str) -> None:
    descendants = downstream_closure(state, target)

    for definition in state["definition"]["nodes"]:
        identifier = definition["id"]
        if identifier not in descendants:
            continue
        record = state["nodes"][identifier]
        if record["status"] in TERMINAL_NODE_STATUSES:
            record["status"] = "pending"
            record["task_id"] = None
            record["result"] = None
            record["revision"] += 1
            count_transition(state)
            event(state, "reset", node=identifier, because=target)


def requeue(state: dict[str, Any], target: str, feedback: dict[str, Any]) -> None:
    descendants = downstream_closure(state, target)
    target_task_id = state["driver"]["active_tasks"].get(target)
    active_target = {"node": target, "task_id": target_task_id} if target_task_id else None
    active_descendants = [
        {"node": definition["id"], "task_id": state["driver"]["active_tasks"][definition["id"]]}
        for definition in state["definition"]["nodes"]
        if definition["id"] in descendants and definition["id"] in state["driver"]["active_tasks"]
    ]
    if active_target or active_descendants:
        active_handles = ([active_target] if active_target else []) + active_descendants
        handles = ", ".join(f"{item['node']}={item['task_id']}" for item in active_handles)
        state["status"] = "blocked"
        state["reason"] = f"cannot requeue {target} while repair tasks are active: {handles}"
        state["driver"]["phase"] = "blocked"
        event(
            state,
            "blocked",
            reason=state["reason"],
            target=target,
            active_target=active_target,
            active_descendants=active_descendants,
        )
        return
    record = state["nodes"][target]
    limit = state["definition"].get("limits", {}).get("max_attempts_per_node", 3)
    if record["attempts"] >= limit:
        state["status"] = "blocked"
        state["reason"] = f"retry limit reached for {target} ({limit})"
        state["driver"]["phase"] = "blocked"
        event(state, "blocked", reason=state["reason"])
        return
    record["status"] = "pending"
    record["task_id"] = None
    record["result"] = None
    record["feedback"].append(feedback)
    record["feedback"] = record["feedback"][-20:]
    record["revision"] += 1
    count_transition(state)
    event(state, "requeued", node=target)
    reset_dependents_for_retry(state, target)


def require_result(result: dict[str, Any], definition: dict[str, Any]) -> None:
    outcome = result.get("outcome")
    if outcome not in definition["outcomes"]:
        raise GraphError(f"node {definition['id']} received invalid outcome {outcome!r}")
    evidence = result.get("evidence")
    if "evidence" in result and (not isinstance(evidence, dict) or not evidence):
        raise GraphError("result evidence must be a non-empty object when present")
    if definition["kind"] in {"verification", "human"} and "evidence" not in result:
        raise GraphError(f"{definition['kind']} result evidence must be a non-empty object")
    if "artifacts" in result and not isinstance(result["artifacts"], dict):
        raise GraphError("result artifacts must be an object when present")


def with_state(arguments: argparse.Namespace, operation: Any) -> dict[str, Any]:
    repo = Path(arguments.repo).resolve()
    if not repo.is_dir():
        raise GraphError(f"repository directory not found: {repo}")
    location = state_path(repo, arguments.run_id)
    with state_lock(location):
        state = load_state(location)
        output = operation(state)
        state["updated_at"] = now()
        write_state(location, state)
    return {**output, "state_path": str(location)}


def open_request(state: dict[str, Any]) -> dict[str, Any] | None:
    return next((item for item in state["requests"] if item["status"] == "open"), None)


def validate_request_body(body: dict[str, Any]) -> None:
    allowed = {"kind", "answer_type", "prompt", "rationale", "options"}
    unknown = set(body) - allowed
    if unknown:
        raise GraphError(f"request has unknown fields: {', '.join(sorted(unknown))}")
    if body.get("kind") not in REQUEST_KINDS:
        raise GraphError("request.kind must be input or approval")
    if body.get("answer_type") not in ANSWER_TYPES:
        raise GraphError("request.answer_type is unsupported")
    for field in ("prompt", "rationale"):
        if not is_non_empty_string(body.get(field)):
            raise GraphError(f"request.{field} must be a non-empty string")
    options = body.get("options")
    if body["answer_type"] in {"single_select", "multi_select"}:
        if not isinstance(options, list) or len(options) < 2 or not all(is_non_empty_string(item) for item in options):
            raise GraphError("select request options must contain at least two non-empty strings")
        if len(set(options)) != len(options):
            raise GraphError("request options must be unique")
    elif "options" in body:
        raise GraphError("request options are only valid for select answers")


def validate_typed_answer(request: dict[str, Any], answer: Any) -> None:
    answer_type = request["answer_type"]
    options = request.get("options", [])
    if answer_type == "single_select":
        if not isinstance(answer, str) or answer not in options:
            raise GraphError("answer must be one declared option")
    elif answer_type == "multi_select":
        if (
            not isinstance(answer, list)
            or not answer
            or not all(isinstance(item, str) and item in options for item in answer)
            or len(set(answer)) != len(answer)
        ):
            raise GraphError("answer must be a non-empty unique list of declared options")
    elif answer_type == "confirm":
        if not isinstance(answer, bool):
            raise GraphError("confirm answer must be true or false")
    elif answer_type == "text" and not is_non_empty_string(answer):
        raise GraphError("text answer must be a non-empty string")


def command_start(arguments: argparse.Namespace) -> dict[str, Any]:
    repo = Path(arguments.repo).resolve()
    if not repo.is_dir():
        raise GraphError(f"repository directory not found: {repo}")
    intake = validate_intake(parse_json_object(arguments.request, "request"), repo)
    location = state_path(repo, arguments.run_id)
    with state_lock(location):
        if location.exists():
            raise GraphError(f"graph run already exists: {location}")
        state = new_intake_state(repo, arguments.run_id, intake, location)
        write_state(location, state)
    return {"status": state["status"], "run_id": arguments.run_id, "state_path": str(location)}


def command_request(arguments: argparse.Namespace) -> dict[str, Any]:
    body = parse_json_object(arguments.request, "request")
    validate_request_body(body)

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        if open_request(state):
            raise GraphError("exactly one open request is allowed")
        node_scoped = arguments.node is not None or arguments.task_id is not None
        if node_scoped and (not arguments.node or not arguments.task_id):
            raise GraphError("node-scoped request requires both --node and --task-id")
        scope = "node" if node_scoped else "preflight"
        request_record = {
            "id": f"request-{state['next_request_seq']}",
            **body,
            "scope": scope,
            "node": arguments.node,
            "task_id": arguments.task_id,
            "status": "open",
            "created_at": now(),
            "answered_at": None,
            "answer": None,
        }
        if node_scoped:
            if state["status"] != "running":
                raise GraphError(f"node-scoped request requires running graph, got {state['status']}")
            if arguments.node not in state["nodes"]:
                raise GraphError(f"unknown node: {arguments.node}")
            record = state["nodes"][arguments.node]
            if record["status"] != "running" or record["task_id"] != arguments.task_id:
                raise GraphError(f"task handle does not match running task for {arguments.node}")
            record["status"] = "awaiting_input"
            record["task_id"] = None
            record["revision"] += 1
            state["driver"]["active_tasks"].pop(arguments.node, None)
        elif state["status"] not in {"collecting_requirements", "awaiting_graph_approval"}:
            raise GraphError(f"preflight request is not allowed while graph is {state['status']}")
        state["requests"].append(request_record)
        state["next_request_seq"] += 1
        state["status"] = "awaiting_input"
        state["driver"]["phase"] = "await_input"
        event(state, "request_opened", request_id=request_record["id"], scope=scope, node=arguments.node)
        return {"status": state["status"], "request_id": request_record["id"], "request": request_record}

    return with_state(arguments, operation)


def command_respond(arguments: argparse.Namespace) -> dict[str, Any]:
    answer = parse_json_value(arguments.answer, "answer")

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        request_record = next((item for item in state["requests"] if item["id"] == arguments.request_id), None)
        if not request_record or request_record["status"] != "open":
            raise GraphError(f"request {arguments.request_id} is not open")
        if state["status"] != "awaiting_input":
            raise GraphError(f"cannot respond while graph is {state['status']}")
        validate_typed_answer(request_record, answer)
        request_record["status"] = "answered"
        request_record["answer"] = answer
        request_record["answered_at"] = now()
        if request_record["scope"] == "node":
            identifier = request_record["node"]
            record = state["nodes"][identifier]
            if record["status"] != "awaiting_input":
                raise GraphError(f"node {identifier} is not awaiting input")
            feedback = {
                "request_id": request_record["id"],
                "request": {
                    "kind": request_record["kind"],
                    "answer_type": request_record["answer_type"],
                    "prompt": request_record["prompt"],
                    "rationale": request_record["rationale"],
                    **({"options": request_record["options"]} if "options" in request_record else {}),
                },
                "answer": answer,
                "answered_at": request_record["answered_at"],
            }
            record["feedback"].append(feedback)
            record["feedback"] = record["feedback"][-20:]
            record["revision"] += 1
            limit = state["definition"].get("limits", {}).get("max_attempts_per_node", 3)
            if record["attempts"] >= limit:
                record["status"] = "blocked"
                state["status"] = "blocked"
                state["reason"] = f"attempt limit reached for {identifier} ({limit}) after input"
                state["driver"]["phase"] = "blocked"
                event(
                    state,
                    "blocked",
                    reason=state["reason"],
                    node=identifier,
                    request_id=request_record["id"],
                )
            else:
                record["status"] = "pending"
                state["status"] = "running"
                state["driver"]["phase"] = "idle"
                event(state, "node_input_received", request_id=request_record["id"], node=identifier)
        else:
            state["status"] = "collecting_requirements"
            state["driver"]["phase"] = "collecting_requirements"
            event(state, "preflight_input_received", request_id=request_record["id"])
        return {"status": state["status"], "request_id": request_record["id"], "answer": answer}

    return with_state(arguments, operation)


def command_plan(arguments: argparse.Namespace) -> dict[str, Any]:
    definition = parse_json_object(arguments.definition, "definition")
    requirements = parse_json_object(arguments.requirements, "requirements")
    validate_definition(definition)
    validate_requirements(requirements)
    if "workstreams" not in definition:
        raise GraphError("plan requires a planned definition with workstreams")

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        if state["status"] not in {"collecting_requirements", "awaiting_graph_approval"}:
            raise GraphError(f"cannot revise plan while graph is {state['status']}")
        if open_request(state):
            raise GraphError("cannot plan while a request is open")
        state["definition"] = definition
        state["requirements"] = requirements
        state["nodes"] = {node["id"]: node_record() for node in definition["nodes"]}
        state["driver"]["active_tasks"] = {}
        state["plan_revision"] += 1
        state["status"] = "awaiting_graph_approval"
        state["driver"]["phase"] = "await_graph_approval"
        event(state, "plan_revised", revision=state["plan_revision"])
        return {"status": state["status"], "plan_revision": state["plan_revision"]}

    return with_state(arguments, operation)


def command_init(arguments: argparse.Namespace) -> dict[str, Any]:
    repo = Path(arguments.repo).resolve()
    if not repo.is_dir():
        raise GraphError(f"repository directory not found: {repo}")
    definition = read_json(Path(arguments.definition))
    validate_definition(definition)
    location = state_path(repo, arguments.run_id)
    with state_lock(location):
        if location.exists():
            raise GraphError(f"graph run already exists: {location}")
        state = new_state(repo, arguments.run_id, definition, location)
        write_state(location, state)
    return {"status": state["status"], "run_id": arguments.run_id, "state_path": str(location)}


def claim_running_node(state: dict[str, Any], identifier: str, task_id: str, event_name: str) -> dict[str, Any]:
    if state["status"] != "running":
        raise GraphError(f"cannot claim task while graph is {state['status']}")
    if not task_id:
        raise GraphError("task id must not be empty")
    normalize_pending(state)
    definitions = nodes_by_id(state["definition"])
    if identifier not in definitions:
        raise GraphError(f"unknown node: {identifier}")
    definition = definitions[identifier]
    if definition["kind"] == "human":
        raise GraphError(f"human node {identifier} must be completed with approve")
    record = state["nodes"][identifier]
    if record["status"] != "pending" or dependencies_state(state, definition) != "ready":
        raise GraphError(f"node {identifier} is not ready")
    if task_id in state["driver"]["active_tasks"].values():
        raise GraphError(f"task id already registered: {task_id}")
    resources = set(definition.get("resources", []))
    for active_node in state["driver"]["active_tasks"]:
        if resources & set(definitions[active_node].get("resources", [])):
            raise GraphError(f"node {identifier} conflicts with active resources on {active_node}")
    limit = state["definition"].get("limits", {}).get("max_attempts_per_node", 3)
    if record["attempts"] >= limit:
        raise GraphError(f"attempt limit reached for {identifier}")
    record["status"] = "running"
    record["task_id"] = task_id
    record["attempts"] += 1
    record["revision"] += 1
    state["driver"]["active_tasks"][identifier] = task_id
    count_transition(state)
    event(state, event_name, node=identifier, task_id=task_id)
    return {"status": state["status"], "node": identifier, "task_id": task_id}


def reduce_node_result(
    state: dict[str, Any], identifier: str, result: dict[str, Any], task_id: str | None = None
) -> dict[str, Any]:
    if state["status"] in {"stopped", "completed"}:
        raise GraphError(f"cannot reduce node result while graph is {state['status']}")
    definitions = nodes_by_id(state["definition"])
    if identifier not in definitions:
        raise GraphError(f"unknown node: {identifier}")
    definition = definitions[identifier]
    record = state["nodes"][identifier]
    if task_id is None:
        if definition["kind"] != "human" or record["status"] != "pending":
            raise GraphError(f"node {identifier} is not awaiting human approval")
        if dependencies_state(state, definition) != "ready":
            raise GraphError(f"human node {identifier} is not ready")
        limit = state["definition"].get("limits", {}).get("max_attempts_per_node", 3)
        if record["attempts"] >= limit:
            raise GraphError(f"attempt limit reached for {identifier}")
        record["attempts"] += 1
    else:
        if record["status"] != "running":
            raise GraphError(f"node {identifier} is not running")
        if record["task_id"] != task_id:
            raise GraphError(f"task handle does not match registered task for {identifier}")
    require_result(result, definition)
    record["status"] = "completed"
    record["result"] = result
    record["revision"] += 1
    state["driver"]["active_tasks"].pop(identifier, None)
    count_transition(state)
    event(state, "completed_node", node=identifier, outcome=result["outcome"])

    target = definition.get("transitions", {}).get(result["outcome"])
    if result["outcome"] in definition.get("failure_outcomes", []):
        state["status"] = "blocked"
        state["reason"] = f"failure outcome for {identifier}: {result['outcome']}"
        state["driver"]["phase"] = "blocked"
        event(state, "blocked", reason=state["reason"])
    elif target:
        requeue(state, target, {"from": identifier, "result": result})
    return {
        "status": state["status"],
        "reason": state["reason"],
        "node": identifier,
        "outcome": result["outcome"],
        "next": target,
    }


def command_approve(arguments: argparse.Namespace) -> dict[str, Any]:
    has_result_file = arguments.result is not None
    has_result_json = arguments.result_json is not None
    if arguments.node:
        if has_result_file == has_result_json:
            raise GraphError("approve --node requires exactly one of --result or --result-json")
        result = (
            read_json(Path(arguments.result))
            if has_result_file
            else parse_json_object(arguments.result_json, "result-json")
        )
    else:
        if has_result_file or has_result_json:
            raise GraphError("approve result source requires --node")
        result = None

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        if arguments.node:
            if state["status"] not in {"running", "awaiting_approval"}:
                raise GraphError(f"cannot approve node while graph is {state['status']}")
            selected = state["driver"].get("approval_node")
            if arguments.node != selected:
                raise GraphError(f"node approval must match selected human gate {selected!r}")
            reduced = reduce_node_result(state, arguments.node, result)
            state["driver"].pop("approval_node", None)
            if state["status"] == "awaiting_approval":
                state["status"] = "running"
                state["driver"]["phase"] = "idle"
                reduced["status"] = "running"
            return reduced
        if state["status"] not in {"awaiting_approval", "awaiting_graph_approval"}:
            raise GraphError(f"cannot approve graph in {state['status']} state")
        if state["driver"].get("approval_node"):
            raise GraphError(f"ready human node {state['driver']['approval_node']} requires approve --node")
        state["status"] = "running"
        state["plan_approved_at"] = now()
        state["driver"]["phase"] = "idle"
        state["driver"].pop("approval_node", None)
        event(state, "graph_approved", revision=state["plan_revision"])
        return {"status": state["status"]}

    return with_state(arguments, operation)


def command_tick(arguments: argparse.Namespace) -> dict[str, Any]:
    return with_state(arguments, tick_state)


def command_register(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        return claim_running_node(state, arguments.node, arguments.task_id, "registered")

    return with_state(arguments, operation)


def command_claim(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        return claim_running_node(state, arguments.node, f"claim:{arguments.claim_id}", "claimed")

    return with_state(arguments, operation)


def command_attach(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        if state["status"] not in {"running", "pause_requested", "awaiting_input", "awaiting_approval", "blocked"}:
            raise GraphError(f"cannot attach task while graph is {state['status']}")
        definitions = nodes_by_id(state["definition"])
        if arguments.node not in definitions:
            raise GraphError(f"unknown node: {arguments.node}")
        record = state["nodes"][arguments.node]
        expected = f"claim:{arguments.claim_id}"
        if record["status"] != "running" or record["task_id"] != expected:
            raise GraphError(f"node {arguments.node} is not claimed by {arguments.claim_id}")
        if arguments.task_id in state["driver"]["active_tasks"].values():
            raise GraphError(f"task id already registered: {arguments.task_id}")
        record["task_id"] = arguments.task_id
        record["revision"] += 1
        state["driver"]["active_tasks"][arguments.node] = arguments.task_id
        event(state, "attached", node=arguments.node, claim_id=arguments.claim_id, task_id=arguments.task_id)
        return {"status": state["status"], "node": arguments.node, "task_id": arguments.task_id}

    return with_state(arguments, operation)


def command_unclaim(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        definitions = nodes_by_id(state["definition"])
        if arguments.node not in definitions:
            raise GraphError(f"unknown node: {arguments.node}")
        record = state["nodes"][arguments.node]
        expected = f"claim:{arguments.claim_id}"
        if record["status"] != "running" or record["task_id"] != expected:
            raise GraphError(f"node {arguments.node} is not claimed by {arguments.claim_id}")
        record["status"] = "pending"
        record["task_id"] = None
        record["attempts"] = max(0, record["attempts"] - 1)
        record["revision"] += 1
        state["driver"]["active_tasks"].pop(arguments.node, None)
        count_transition(state)
        event(state, "unclaimed", node=arguments.node, claim_id=arguments.claim_id)
        return {
            "status": state["status"],
            "node": arguments.node,
            "claim_id": arguments.claim_id,
            "attempts": record["attempts"],
        }

    return with_state(arguments, operation)


def command_complete(arguments: argparse.Namespace) -> dict[str, Any]:
    result = read_json(Path(arguments.result))

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        return reduce_node_result(state, arguments.node, result, arguments.task_id)

    return with_state(arguments, operation)


def command_block(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        state["status"] = "blocked"
        state["reason"] = arguments.reason
        state["driver"]["phase"] = "blocked"
        event(state, "blocked", reason=arguments.reason)
        return {"status": "blocked", "reason": arguments.reason}

    return with_state(arguments, operation)


def command_milestone(arguments: argparse.Namespace) -> dict[str, Any]:
    milestone = parse_json_object(arguments.event, "event")
    allowed = {"name", "message", "evidence"}
    if set(milestone) - allowed:
        raise GraphError("milestone accepts coordinator fields only: name, message, evidence")
    for field in ("name", "message"):
        if not is_non_empty_string(milestone.get(field)):
            raise GraphError(f"milestone.{field} must be a non-empty string")
    if "evidence" in milestone and not isinstance(milestone["evidence"], dict):
        raise GraphError("milestone.evidence must be an object")

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        event(state, "milestone", **milestone)
        return {"status": state["status"], "event_seq": state["next_event_seq"] - 1}

    return with_state(arguments, operation)


def command_pause(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        if state["status"] != "running":
            raise GraphError(f"cannot pause graph while it is {state['status']}")
        state["status"] = "pause_requested"
        state["driver"]["phase"] = "drain"
        state["controls"]["pause"] = {"requested_at": now()}
        event(state, "pause_requested", active_handles=state["driver"]["active_tasks"])
        return {"status": state["status"], "active_handles": active_handle_projection(state)}

    return with_state(arguments, operation)


def command_resume(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        if state["status"] != "paused":
            raise GraphError(f"cannot resume graph while it is {state['status']}")
        state["status"] = "running"
        state["driver"]["phase"] = "idle"
        if state["controls"]["pause"] is not None:
            state["controls"]["pause"]["resumed_at"] = now()
        event(state, "resumed")
        return {"status": state["status"]}

    return with_state(arguments, operation)


def command_steer_request(arguments: argparse.Namespace) -> dict[str, Any]:
    if not is_non_empty_string(arguments.message):
        raise GraphError("steering message must be non-empty")

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        task_id = state["driver"]["active_tasks"].get(arguments.node)
        if not task_id or state["nodes"].get(arguments.node, {}).get("status") != "running":
            raise GraphError(f"node {arguments.node} has no active handle")
        steer_id = f"steer-{state['controls']['next_steer_seq']}"
        directive = {
            "id": steer_id,
            "node": arguments.node,
            "task_id": task_id,
            "message": arguments.message,
            "status": "pending",
            "requested_at": now(),
            "acknowledged_at": None,
            "evidence": None,
        }
        state["controls"]["steering"].append(directive)
        state["controls"]["next_steer_seq"] += 1
        event(state, "steering_requested", steer_id=steer_id, node=arguments.node, task_id=task_id)
        return {"status": state["status"], "steer_id": steer_id, "task_id": task_id}

    return with_state(arguments, operation)


def command_steer_ack(arguments: argparse.Namespace) -> dict[str, Any]:
    evidence = parse_json_object(arguments.evidence, "evidence")
    if evidence.get("status") not in {"delivered", "failed"}:
        raise GraphError("steering evidence.status must be delivered or failed")

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        directive = next(
            (item for item in state["controls"]["steering"] if item["id"] == arguments.steer_id),
            None,
        )
        if not directive or directive["status"] != "pending":
            raise GraphError(f"steering directive {arguments.steer_id} is not pending")
        directive["status"] = evidence["status"]
        directive["evidence"] = evidence
        directive["acknowledged_at"] = now()
        event(state, "steering_acknowledged", steer_id=directive["id"], delivery_status=evidence["status"])
        return {
            "status": state["status"],
            "steer_id": directive["id"],
            "delivery_status": evidence["status"],
        }

    return with_state(arguments, operation)


def active_handle_projection(state: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"node": identifier, "task_id": task_id}
        for identifier, task_id in sorted(state["driver"]["active_tasks"].items())
    ]


def command_stop_request(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        if state["status"] in {"stopped", "completed"}:
            raise GraphError(f"cannot request stop while graph is {state['status']}")
        if state["status"] == "stop_requested":
            raise GraphError("stop is already requested")
        handles = active_handle_projection(state)
        state["status"] = "stop_requested"
        state["driver"]["phase"] = "stop"
        state["controls"]["stop"] = {"requested_at": now(), "handles": handles, "evidence": None}
        event(state, "stop_requested", active_handles=handles)
        return {"status": state["status"], "active_handles": handles}

    return with_state(arguments, operation)


def command_stop_confirm(arguments: argparse.Namespace) -> dict[str, Any]:
    evidence = parse_json_object(arguments.evidence, "evidence")
    handles_evidence = evidence.get("handles")
    if not isinstance(handles_evidence, dict):
        raise GraphError("stop evidence.handles must be an object keyed by task id")

    def operation(state: dict[str, Any]) -> dict[str, Any]:
        if state["status"] != "stop_requested" or state["controls"]["stop"] is None:
            raise GraphError(f"cannot confirm stop while graph is {state['status']}")
        required = [item["task_id"] for item in state["controls"]["stop"]["handles"]]
        missing = [task_id for task_id in required if handles_evidence.get(task_id) not in TERMINAL_HANDLE_STATUSES]
        if missing:
            raise GraphError(f"terminal stop evidence missing for handles: {', '.join(missing)}")
        state["controls"]["stop"]["evidence"] = evidence
        state["controls"]["stop"]["confirmed_at"] = now()
        state["driver"]["active_tasks"] = {}
        state["status"] = "stopped"
        state["driver"]["phase"] = "stopped"
        event(state, "stopped", evidence=evidence)
        return {"status": state["status"]}

    return with_state(arguments, operation)


def command_reconcile(arguments: argparse.Namespace) -> dict[str, Any]:
    def operation(state: dict[str, Any]) -> dict[str, Any]:
        state["driver"]["phase"] = "reconcile"
        event(state, "reconcile_requested", active_tasks=state["driver"]["active_tasks"])
        unattached = sorted(
            identifier for identifier, task_id in state["driver"]["active_tasks"].items() if task_id.startswith("claim:")
        )
        return {"action": "reconcile", "active_tasks": state["driver"]["active_tasks"], "unattached_claims": unattached}

    return with_state(arguments, operation)


def command_summary(arguments: argparse.Namespace) -> dict[str, Any]:
    repo = Path(arguments.repo).resolve()
    location = state_path(repo, arguments.run_id)
    state = load_state(location)
    return {
        "run_id": state["run_id"],
        "status": state["status"],
        "reason": state["reason"],
        "transition_count": state["transition_count"],
        "driver": state["driver"],
        "nodes": state["nodes"],
        "state_path": str(location),
    }


def cockpit_projection(state: dict[str, Any], location: Path) -> dict[str, Any]:
    progress: dict[str, Any] | None = None
    counts: dict[str, int] | None = None
    definition = state.get("definition")
    if definition:
        total = len(state["nodes"])
        completed = sum(record["status"] == "completed" for record in state["nodes"].values())
        skipped = sum(record["status"] == "skipped" for record in state["nodes"].values())
        counts = {
            status: sum(record["status"] == status for record in state["nodes"].values())
            for status in sorted({record["status"] for record in state["nodes"].values()})
        }
        progress = {
            "completed": completed,
            "skipped": skipped,
            "total": total,
            "ratio": (completed + skipped) / total if total else 0.0,
        }
    pending = open_request(state)
    request_projection = None
    if pending:
        request_projection = {
            "id": pending["id"],
            "kind": pending["kind"],
            "answer_type": pending["answer_type"],
            "prompt": pending["prompt"],
            "rationale": pending["rationale"],
            "scope": pending["scope"],
            "node": pending["node"],
            **({"options": pending["options"]} if "options" in pending else {}),
        }
    pending_approval = None
    if state["status"] == "awaiting_graph_approval" or (
        state["status"] == "awaiting_approval" and not state["driver"].get("approval_node")
    ):
        pending_approval = {
            "scope": "graph",
            "node": None,
            "prompt": "Approve the planned graph.",
            "objective": (state.get("requirements") or state.get("intake") or {}).get("goal"),
            "allowed_outcomes": ["approved"],
            "kind": "approval",
            "evidence_required": True,
        }
    elif state["status"] == "awaiting_approval":
        approval_node = state["driver"].get("approval_node")
        planned_approval = nodes_by_id(definition).get(approval_node) if definition else None
        if planned_approval:
            pending_approval = {
                "scope": "node",
                "node": approval_node,
                "prompt": planned_approval.get("prompt") or planned_approval.get("objective") or f"Approve {approval_node}.",
                "objective": planned_approval.get("objective"),
                "allowed_outcomes": planned_approval["outcomes"],
                "kind": "approval",
                "evidence_required": True,
            }
    node_projection = []
    for planned_node in definition.get("nodes", []) if definition else []:
        record = state["nodes"][planned_node["id"]]
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        node_projection.append(
            {
                "id": planned_node["id"],
                "workstream": planned_node.get("workstream"),
                "kind": planned_node["kind"],
                "status": record["status"],
                "objective": planned_node.get("objective"),
                "assigned_role": planned_node.get("assigned_role"),
                "priority": planned_node.get("priority"),
                "resources": planned_node.get("resources", []),
                "outcomes": planned_node["outcomes"],
                "transitions": planned_node.get("transitions", {}),
                "failure_outcomes": planned_node.get("failure_outcomes", []),
                "prompt": planned_node.get("prompt", ""),
                "paths": planned_node.get("paths", []),
                "verification_commands": planned_node.get("verification_commands", []),
                "depends_on": planned_node.get("depends_on", []),
                "depends_on_any": planned_node.get("depends_on_any", []),
                "attempts": record["attempts"],
                "task_id": record["task_id"],
                "acceptance_criteria": planned_node.get("acceptance_criteria", []),
                "evidence": result.get("evidence"),
                "artifacts": result.get("artifacts"),
            }
        )
    workstream_projection = []
    for workstream in definition.get("workstreams", []) if definition else []:
        records = [
            state["nodes"][planned_node["id"]]
            for planned_node in definition["nodes"]
            if planned_node.get("workstream") == workstream["id"]
        ]
        node_counts = {
            status: sum(record["status"] == status for record in records)
            for status in sorted({record["status"] for record in records})
        }
        statuses = set(node_counts)
        if statuses & {"blocked", "failed"}:
            workstream_status = "blocked"
        elif statuses & {"running", "awaiting_input"}:
            workstream_status = "active"
        elif records and all(record["status"] in TERMINAL_NODE_STATUSES for record in records):
            workstream_status = "completed"
        else:
            workstream_status = "pending"
        workstream_projection.append(
            {
                "id": workstream["id"],
                "title": workstream["title"],
                "objective": workstream["objective"],
                "status": workstream_status,
                "node_counts": node_counts,
            }
        )
    effective_limits = None
    max_concurrency = None
    if definition:
        configured_limits = definition.get("limits", {})
        effective_limits = {
            "max_attempts_per_node": configured_limits.get("max_attempts_per_node", 3),
            "max_transitions": configured_limits.get("max_transitions", 100),
        }
        max_concurrency = definition.get("max_concurrency", 1)
    return {
        "cockpit_version": 1,
        "run_id": state["run_id"],
        "status": state["status"],
        "phase": state["driver"]["phase"],
        "updated_at": state["updated_at"],
        "goal": (state.get("requirements") or state.get("intake") or {}).get("goal"),
        "requirements": state.get("requirements"),
        "max_concurrency": max_concurrency,
        "limits": effective_limits,
        "plan_revision": state["plan_revision"],
        "progress": progress,
        "node_counts": counts,
        "active_handles": active_handle_projection(state),
        "open_request": request_projection,
        "pending_approval": pending_approval,
        "reason": state["reason"],
        "workstreams": workstream_projection,
        "nodes": node_projection,
        "recent_events": [dict(item) for item in state.get("events", [])[-20:]],
        "state_path": str(location),
    }


def cockpit_text(projection: dict[str, Any]) -> str:
    progress = projection["progress"]
    if progress is None:
        progress_text = "intake"
    else:
        finished = progress["completed"] + progress["skipped"]
        progress_text = f"{finished}/{progress['total']} ({progress['ratio'] * 100:.1f}%)"
    handles = ", ".join(
        f"{item['node']}={item['task_id']}" for item in projection["active_handles"]
    ) or "none"
    open_request_value = projection["open_request"]
    request_text = (
        f"{open_request_value['id']}: {open_request_value['prompt']}" if open_request_value else "none"
    )
    node_counts = projection["node_counts"]
    node_counts_text = json.dumps(node_counts, sort_keys=True) if node_counts is not None else "none"
    return "\n".join(
        [
            f"Cockpit version: {projection['cockpit_version']}",
            f"Run: {projection['run_id']}",
            f"Status: {projection['status']}",
            f"Updated at: {projection['updated_at']}",
            f"Goal: {projection['goal'] or '-'}",
            f"Progress: {progress_text}",
            f"Node counts: {node_counts_text}",
            f"Plan revision: {projection['plan_revision']}",
            f"Active handles: {handles}",
            f"Open request: {request_text}",
            f"Reason: {projection['reason'] or '-'}",
            f"State: {projection['state_path']}",
        ]
    )


def command_status(arguments: argparse.Namespace) -> dict[str, Any] | str:
    repo = Path(arguments.repo).resolve()
    location = state_path(repo, arguments.run_id)
    projection = cockpit_projection(load_state(location), location)
    return projection if arguments.format == "json" else cockpit_text(projection)


def runs_root(repo: Path) -> Path:
    common_dir = git_common_dir(repo)
    root = common_dir if common_dir else repo / ".agent-skills"
    return root / "graph-flow"


def command_runs(arguments: argparse.Namespace) -> dict[str, Any]:
    repo = Path(arguments.repo).resolve()
    if not repo.is_dir():
        raise GraphError(f"repository directory not found: {repo}")
    root = runs_root(repo)
    discovered = []
    for location in root.rglob("state.json") if root.exists() else []:
        state = load_state(location)
        discovered.append(
            {
                "run_id": state["run_id"],
                "status": state["status"],
                "updated_at": state["updated_at"],
                "state_path": str(location),
            }
        )
    return {"repo": str(repo), "runs": sorted(discovered, key=lambda item: item["run_id"])}


def command_validate(arguments: argparse.Namespace) -> dict[str, Any]:
    if arguments.definition:
        definition = read_json(Path(arguments.definition))
        validate_definition(definition)
        return {"valid": True, "definition": str(Path(arguments.definition).resolve())}
    repo = Path(arguments.repo).resolve()
    state = load_state(state_path(repo, arguments.run_id))
    graph_planned = state["definition"] is not None
    if graph_planned:
        validate_definition(state["definition"])
    return {"valid": True, "graph_planned": graph_planned, "state_path": state["state_path"]}


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", required=True, help="Repository or project root")
    parser.add_argument("--run-id", required=True, help="Stable graph run identifier")


def parser() -> argparse.ArgumentParser:
    program = argparse.ArgumentParser(description=__doc__)
    commands = program.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start", help="begin unified intake without a graph")
    add_common(start)
    start.add_argument("--request", required=True, help="Initial request JSON object")
    init = commands.add_parser("init", help="validate a definition and create a run")
    add_common(init)
    init.add_argument("--definition", required=True, help="Path to graph definition JSON")
    for name, help_text in (
        ("approve", "record initial or in-run human approval"),
        ("tick", "compute the next deterministic coordinator action"),
        ("summary", "print a run snapshot"),
        ("reconcile", "return active handles after coordinator restart"),
        ("validate", "validate an existing graph run"),
    ):
        item = commands.add_parser(name, help=help_text)
        add_common(item)
    request = commands.add_parser("request", help="open a typed preflight or node-scoped human request")
    add_common(request)
    request.add_argument("--request", required=True, help="Typed request JSON object")
    request.add_argument("--node", help="Running node for a runtime request")
    request.add_argument("--task-id", help="Exact running handle for a runtime request")
    respond = commands.add_parser("respond", help="answer the exact open typed request")
    add_common(respond)
    respond.add_argument("--request-id", required=True)
    respond.add_argument("--answer", required=True, help="Typed JSON answer")
    plan = commands.add_parser("plan", help="create or revise a strict planned graph")
    add_common(plan)
    plan.add_argument("--definition", required=True, help="Planned graph JSON object")
    plan.add_argument("--requirements", required=True, help="Complete requirements JSON object")
    approve = commands.choices["approve"]
    approve.add_argument("--node", help="Ready human node to approve")
    approve.add_argument("--result", help="Human result envelope JSON; requires --node")
    approve.add_argument("--result-json", help="Inline human result envelope JSON; requires --node")
    validate = commands.choices["validate"]
    validate.add_argument("--definition", help="Validate a definition instead of an existing run")
    register = commands.add_parser("register", help="atomically claim a ready node for a task")
    add_common(register)
    register.add_argument("--node", required=True)
    register.add_argument("--task-id", required=True)
    claim = commands.add_parser("claim", help="persist a node claim before dispatching a task")
    add_common(claim)
    claim.add_argument("--node", required=True)
    claim.add_argument("--claim-id", required=True)
    attach = commands.add_parser("attach", help="attach a durable task handle to a prior claim")
    add_common(attach)
    attach.add_argument("--node", required=True)
    attach.add_argument("--claim-id", required=True)
    attach.add_argument("--task-id", required=True)
    unclaim = commands.add_parser("unclaim", help="release an orphaned claim after external task inspection")
    add_common(unclaim)
    unclaim.add_argument("--node", required=True)
    unclaim.add_argument("--claim-id", required=True)
    complete = commands.add_parser("complete", help="reduce a worker result envelope")
    add_common(complete)
    complete.add_argument("--node", required=True)
    complete.add_argument("--task-id", required=True, help="Exact registered task handle")
    complete.add_argument("--result", required=True, help="Path to result envelope JSON")
    block = commands.add_parser("block", help="stop a graph with a durable reason")
    add_common(block)
    block.add_argument("--reason", required=True)
    milestone = commands.add_parser("milestone", help="record a coordinator milestone")
    add_common(milestone)
    milestone.add_argument("--event", required=True, help="Coordinator milestone JSON object")
    for name, help_text in (
        ("pause", "request dispatch pause and active-handle drain"),
        ("resume", "resume a paused graph"),
        ("stop-request", "begin two-phase stop"),
    ):
        item = commands.add_parser(name, help=help_text)
        add_common(item)
    steer_request = commands.add_parser("steer-request", help="persist a directive for an active handle")
    add_common(steer_request)
    steer_request.add_argument("--node", required=True)
    steer_request.add_argument("--message", required=True)
    steer_ack = commands.add_parser("steer-ack", help="acknowledge steering delivery")
    add_common(steer_ack)
    steer_ack.add_argument("--steer-id", required=True)
    steer_ack.add_argument("--evidence", required=True, help="Delivery evidence JSON object")
    stop_confirm = commands.add_parser("stop-confirm", help="confirm all stop handles are terminal")
    add_common(stop_confirm)
    stop_confirm.add_argument("--evidence", required=True, help="Terminal handle evidence JSON object")
    status = commands.add_parser("status", help="render the stable cockpit projection")
    add_common(status)
    status.add_argument("--format", choices=("json", "text"), default="json")
    runs = commands.add_parser("runs", help="discover graph-flow runs for a repository")
    runs.add_argument("--repo", required=True, help="Repository or project root")
    return program


def main() -> None:
    arguments = parser().parse_args()
    handlers = {
        "start": command_start,
        "init": command_init,
        "request": command_request,
        "respond": command_respond,
        "plan": command_plan,
        "approve": command_approve,
        "tick": command_tick,
        "register": command_register,
        "claim": command_claim,
        "attach": command_attach,
        "unclaim": command_unclaim,
        "complete": command_complete,
        "block": command_block,
        "milestone": command_milestone,
        "pause": command_pause,
        "resume": command_resume,
        "steer-request": command_steer_request,
        "steer-ack": command_steer_ack,
        "stop-request": command_stop_request,
        "stop-confirm": command_stop_confirm,
        "reconcile": command_reconcile,
        "summary": command_summary,
        "status": command_status,
        "runs": command_runs,
        "validate": command_validate,
    }
    try:
        emit(handlers[arguments.command](arguments))
    except GraphError as exc:
        emit({"error": str(exc)}, code=1)
    except BrokenPipeError:
        raise
    except Exception as exc:  # keep the coordinator protocol JSON-only on unexpected failure
        emit({"error": f"internal graph-state error: {exc}"}, code=1)


if __name__ == "__main__":
    main()
