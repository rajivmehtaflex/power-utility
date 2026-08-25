import type { CockpitSnapshot, InputRequest, PendingApproval } from "./types.ts";

function stableJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${stableJson(record[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function countText(counts: Record<string, number> | null): string {
  return counts ? Object.keys(counts).sort().map((key) => `${key}=${counts[key]}`).join(", ") : "unavailable";
}

function join(values: string[] | undefined): string | undefined {
  return values?.length ? values.join(" | ") : undefined;
}

function appendRequirement(lines: string[], label: string, values: string[] | undefined): void {
  const text = join(values);
  if (text) lines.push(`  ${label}: ${text}`);
}

export function renderCockpit(snapshot: CockpitSnapshot): string[] {
  const progress = snapshot.progress;
  const finished = progress ? progress.completed + progress.skipped : 0;
  const progressText = progress ? `${finished}/${progress.total} (${Math.round(progress.ratio * 100)}%)` : "intake";
  const lines = [
    `Run: ${snapshot.run_id}`,
    `Phase: ${snapshot.phase ?? snapshot.status}`,
    `Goal: ${snapshot.goal ?? "-"}`,
    `Progress: ${progressText}`,
    `Nodes: ${countText(snapshot.node_counts)}`,
    `Plan revision: ${snapshot.plan_revision}`,
    `Updated: ${snapshot.updated_at}`,
  ];

  if (snapshot.pending_approval) {
    lines.push("Review before approve: required");
    if (snapshot.max_concurrency !== undefined) lines.push(`Max concurrency: ${snapshot.max_concurrency}`);
    if (snapshot.limits) {
      const limitText = [
        snapshot.limits.max_attempts_per_node !== undefined ? `max attempts per node=${snapshot.limits.max_attempts_per_node}` : undefined,
        snapshot.limits.max_transitions !== undefined ? `max transitions=${snapshot.limits.max_transitions}` : undefined,
      ].filter((value): value is string => value !== undefined).join(", ");
      if (limitText) lines.push(`Limits: ${limitText}`);
    }
    const requirements = snapshot.requirements;
    if (requirements) {
      lines.push("Requirements:");
      if (requirements.goal) lines.push(`  Goal: ${requirements.goal}`);
      appendRequirement(lines, "Success criteria", requirements.success_criteria);
      appendRequirement(lines, "Scope included", requirements.scope?.included);
      appendRequirement(lines, "Scope excluded", requirements.scope?.excluded);
      appendRequirement(lines, "Constraints", requirements.constraints);
      appendRequirement(lines, "Verification", requirements.verification);
      appendRequirement(lines, "Approval boundaries", requirements.approval_boundaries);
      appendRequirement(lines, "Assumptions", requirements.assumptions);
    }
  }

  for (const workstream of snapshot.workstreams ?? []) {
    lines.push(`Workstream ${workstream.id} (${workstream.title ?? workstream.id}): ${workstream.objective ?? "-"}`);
    if (workstream.status || workstream.node_counts) {
      lines.push(`  Workstream status: ${workstream.status ?? "-"}${workstream.node_counts ? ` (${countText(workstream.node_counts)})` : ""}`);
    }
  }
  for (const node of snapshot.nodes ?? []) {
    lines.push(`Node ${node.id}: ${node.status} [${node.assigned_role ?? "unassigned"}, ${node.priority ?? "normal"}]`);
    if (node.workstream) lines.push(`  Workstream: ${node.workstream}`);
    if (node.objective) lines.push(`  Objective: ${node.objective}`);
    const resources = join(node.resources);
    if (resources) lines.push(`  Resources: ${resources}`);
    const paths = join(node.paths);
    if (paths) lines.push(`  Paths: ${paths}`);
    const outcomes = join(node.outcomes);
    if (outcomes) lines.push(`  Outcomes: ${outcomes}`);
    const failureOutcomes = join(node.failure_outcomes);
    if (failureOutcomes) lines.push(`  Failure outcomes: ${failureOutcomes}`);
    if (node.transitions && Object.keys(node.transitions).length) lines.push(`  Transitions: ${Object.keys(node.transitions).sort().map((outcome) => `${outcome}→${node.transitions?.[outcome]}`).join(", ")}`);
    if (node.prompt) lines.push(`  Task prompt: ${node.prompt}`);
    if (node.depends_on?.length) lines.push(`  Depends on: ${node.depends_on.map((item) => `${item.node}:${item.outcome}`).join(", ")}`);
    if (node.depends_on_any?.length) lines.push(`  Depends on any: ${node.depends_on_any.map((item) => `${item.node}:${item.outcome}`).join(", ")}`);
    const criteria = join(node.acceptance_criteria);
    if (criteria) lines.push(`  Acceptance criteria: ${criteria}`);
    const commands = join(node.verification_commands);
    if (commands) lines.push(`  Verification commands: ${commands}`);
    if (node.evidence) lines.push(`  Evidence: ${stableJson(node.evidence)}`);
    if (node.artifacts) lines.push(`  Artifacts: ${stableJson(node.artifacts)}`);
  }
  lines.push(`Active handles: ${snapshot.active_handles.map((item) => `${item.node}=${item.task_id}`).join(", ") || "none"}`);
  if (snapshot.reason) lines.push(`Blocker: ${snapshot.reason}`);
  for (const event of snapshot.recent_events ?? []) {
    lines.push(`Event #${event.seq}: ${event.event}${event.node ? ` (${event.node})` : ""}`);
  }
  return lines;
}

export function renderActionCenter(request: InputRequest | null, pendingApproval: PendingApproval | null | undefined = null): string[] {
  if (!request && !pendingApproval) return ["Action Center: clear"];
  if (pendingApproval) {
    const lines = [
      `Action Center: ${pendingApproval.scope === "graph" ? "graph" : "human"} approval`,
      `Prompt: ${pendingApproval.prompt}`,
      `Objective: ${pendingApproval.objective ?? "-"}`,
      `Evidence required: ${pendingApproval.evidence_required ? "yes" : "no"}`,
    ];
    if (pendingApproval.node) lines.push(`Node: ${pendingApproval.node}`);
    if (pendingApproval.allowed_outcomes.length) lines.push(`Allowed outcomes: ${pendingApproval.allowed_outcomes.join(" | ")}`);
    return lines;
  }
  if (!request) return ["Action Center: clear"];
  const lines = [
    `Action Center: ${request.kind} (${request.answer_type})`,
    `Request: ${request.id}`,
    `Prompt: ${request.prompt}`,
    `Rationale: ${request.rationale ?? "-"}`,
    `Scope: ${request.scope}`,
  ];
  if (request.node) lines.push(`Node: ${request.node}`);
  if (request.options) lines.push(`Options: ${request.options.join(" | ")}`);
  return lines;
}
