import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import test from "node:test";

const projection = await import("../extensions/graph-flow-ui/projection.ts");
const { GraphStateClient, bundledReducerPath, fileUrlToPath } = await import("../extensions/graph-flow-ui/state-client.ts");
const { answerOpenRequest, answerPendingApproval } = await import("../extensions/graph-flow-ui/dialogs.ts");
const { GraphFlowControls } = await import("../extensions/graph-flow-ui/controls.ts");
const { default: graphFlowExtension, refreshCockpit } = await import("../extensions/graph-flow-ui/index.ts");

const snapshot = {
  cockpit_version: 1,
  run_id: "billing-v2",
  status: "running",
  phase: "dispatch",
  updated_at: "2026-08-23T12:00:00Z",
  goal: "Ship billing v2",
  plan_revision: 2,
  max_concurrency: 3,
  limits: { max_attempts_per_node: 3, max_transitions: 100 },
  progress: { completed: 1, skipped: 1, total: 4, ratio: 0.5 },
  node_counts: { completed: 1, pending: 2, skipped: 1 },
  active_handles: [{ node: "implement", task_id: "worker-123" }],
  open_request: null,
  pending_approval: null,
  requirements: {
    goal: "Ship billing v2",
    success_criteria: ["Ship safely"],
    scope: { included: ["billing"], excluded: ["unrelated migrations"] },
    constraints: ["No downtime"],
    verification: ["npm test"],
    approval_boundaries: ["Production release"],
    assumptions: ["Staging is available"],
  },
  reason: "Waiting on provider response",
  state_path: "/tmp/billing-v2/state.json",
  workstreams: [{ id: "engine", title: "Engine", objective: "Ship lifecycle", status: "running", node_counts: { completed: 1, running: 1 } }],
  nodes: [{
    id: "implement",
    status: "running",
    workstream: "engine",
    kind: "implementation",
    objective: "Ship lifecycle",
    assigned_role: "worker",
    priority: "critical",
    paths: ["src/engine.ts"],
    resources: ["src/engine.ts"],
    verification_commands: ["npm test"],
    outcomes: ["done", "rejected"],
    failure_outcomes: ["rejected"],
    transitions: { rejected: "repair" },
    prompt: "Implement the lifecycle without changing public behavior.",
    depends_on: [{ node: "inspect", outcome: "done" }],
    depends_on_any: [{ node: "fallback", outcome: "done" }],
    attempts: 1,
    task_id: "worker-123",
    acceptance_criteria: ["Tests pass"],
    evidence: { command: "npm test", exit_code: 0 },
    artifacts: { changed_paths: ["src/engine.ts"] },
  }],
  recent_events: [{ seq: 12, at: "2026-08-23T12:00:01Z", event: "registered", node: "implement" }],
};

test("renders cockpit projection details without reading durable state", () => {
  const lines = projection.renderCockpit(snapshot);
  const text = lines.join("\n");

  assert.match(text, /Run: billing-v2/);
  assert.match(text, /Phase: dispatch/);
  assert.match(text, /Progress: 2\/4 \(50%\)/);
  assert.match(text, /Nodes: completed=1, pending=2, skipped=1/);
  assert.match(text, /Workstream engine \(Engine\): Ship lifecycle/);
  assert.match(text, /Workstream status: running \(completed=1, running=1\)/);
  assert.match(text, /Node implement: running \[worker, critical\]/);
  assert.match(text, /Objective: Ship lifecycle/);
  assert.match(text, /Depends on: inspect:done/);
  assert.match(text, /Depends on any: fallback:done/);
  assert.match(text, /Active handles: implement=worker-123/);
  assert.match(text, /Evidence: {"command":"npm test","exit_code":0}/);
  assert.match(text, /Artifacts: {"changed_paths":\["src\/engine.ts"\]}/);
  assert.match(text, /Blocker: Waiting on provider response/);
  assert.match(text, /Event #12: registered \(implement\)/);
  assert.doesNotMatch(text, /state\.json/);

  const legacyText = projection.renderCockpit({ ...snapshot, workstreams: [{ id: "engine", title: "Engine", objective: "Ship lifecycle" }] }).join("\n");
  assert.doesNotMatch(legacyText, /Workstream status:/);
});

test("renders a complete review-before-approve graph using only public projection fields", () => {
  const review = {
    ...snapshot,
    status: "awaiting_graph_approval",
    phase: "await_graph_approval",
    pending_approval: {
      scope: "graph",
      node: null,
      prompt: "Approve the planned graph.",
      objective: "Ship billing v2",
      allowed_outcomes: ["approved"],
      kind: "approval",
      evidence_required: true,
    },
  };
  const text = projection.renderCockpit(review).join("\n");

  assert.match(text, /Review before approve: required/);
  assert.match(text, /Max concurrency: 3/);
  assert.match(text, /Limits: max attempts per node=3, max transitions=100/);
  assert.match(text, /Requirements:/);
  assert.match(text, /Success criteria: Ship safely/);
  assert.match(text, /Approval boundaries: Production release/);
  assert.match(text, /Scope included: billing/);
  assert.match(text, /Scope excluded: unrelated migrations/);
  assert.match(text, /Resources: src\/engine\.ts/);
  assert.match(text, /Paths: src\/engine\.ts/);
  assert.match(text, /Outcomes: done \| rejected/);
  assert.match(text, /Failure outcomes: rejected/);
  assert.match(text, /Transitions: rejected→repair/);
  assert.match(text, /Task prompt: Implement the lifecycle without changing public behavior\./);
  assert.match(text, /Acceptance criteria: Tests pass/);
  assert.match(text, /Verification commands: npm test/);
  assert.match(text, /Evidence: \{"command":"npm test","exit_code":0\}/);
  assert.match(text, /Artifacts: \{"changed_paths":\["src\/engine\.ts"\]\}/);
});

test("package allowlist ships only the portable runtime and excludes tests and caches", async () => {
  const manifest = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));

  assert.deepEqual(manifest.files, ["SKILL.md", "scripts/graph_state.py", "references", "extensions", "package.json", "tsconfig.json"]);
  assert.ok(manifest.files.every((path) => !/(^|\/)(__pycache__|tests?)(\/|$)|\.pyc$/u.test(path)));
  assert.ok(!manifest.files.includes("scripts/"));
  assert.equal(manifest.scripts.test, "node --test --experimental-strip-types tests/graph-flow-ui.test.mjs tests/adapter-contract.test.mjs");
});

test("renders each Action Center request type with the exact request details", () => {
  const select = projection.renderActionCenter({
    id: "request-1",
    kind: "input",
    answer_type: "single_select",
    prompt: "Choose provider",
    rationale: "Billing depends on it",
    options: ["stripe", "adyen"],
    scope: "preflight",
    node: null,
  }).join("\n");
  const confirm = projection.renderActionCenter({
    id: "request-2",
    kind: "approval",
    answer_type: "confirm",
    prompt: "Approve migration?",
    rationale: "Writes production data",
    scope: "node",
    node: "approve-migration",
  }).join("\n");

  assert.match(select, /Action Center: input \(single_select\)/);
  assert.match(select, /Request: request-1/);
  assert.match(select, /Options: stripe \| adyen/);
  assert.match(confirm, /Action Center: approval \(confirm\)/);
  assert.match(confirm, /Node: approve-migration/);
  assert.deepEqual(projection.renderActionCenter(null), ["Action Center: clear"]);
});

test("renders graph and human pending approvals with their allowed outcomes", () => {
  const graph = {
    scope: "graph",
    node: null,
    prompt: "Approve this execution graph?",
    objective: "Ship billing v2",
    allowed_outcomes: [],
    kind: "approval",
    evidence_required: true,
  };
  const human = {
    scope: "node",
    node: "release-approval",
    prompt: "Approve release?",
    objective: "Approve production release",
    allowed_outcomes: ["approved", "declined"],
    kind: "approval",
    evidence_required: true,
  };

  const graphText = projection.renderActionCenter(null, graph).join("\n");
  const humanText = projection.renderActionCenter(null, human).join("\n");

  assert.match(graphText, /Action Center: graph approval/);
  assert.match(graphText, /Objective: Ship billing v2/);
  assert.match(humanText, /Action Center: human approval/);
  assert.match(humanText, /Node: release-approval/);
  assert.match(humanText, /Allowed outcomes: approved \| declined/);
});

test("state client reads the public projection through the package-relative reducer path", async () => {
  const calls = [];
  const client = new GraphStateClient({
    repo: "/repo",
    runId: "billing-v2",
    scriptPath: "/installed/graph-flow/scripts/graph_state.py",
    execute: async (command, args) => {
      calls.push([command, args]);
      return { code: 0, stdout: JSON.stringify(snapshot), stderr: "" };
    },
  });
  const seen = [];

  const result = await client.refresh((value) => seen.push(value.run_id));

  assert.equal(result.run_id, "billing-v2");
  assert.deepEqual(seen, ["billing-v2"]);
  assert.deepEqual(calls, [["python3", ["/installed/graph-flow/scripts/graph_state.py", "status", "--repo", "/repo", "--run-id", "billing-v2", "--format", "json"]]]);
});

test("state client surfaces a reducer JSON error returned only through stdout", async () => {
  const client = new GraphStateClient({
    repo: "/repo",
    runId: "billing-v2",
    scriptPath: "scripts/graph_state.py",
    execute: async () => ({ code: 2, stdout: '{"error":"cannot pause graph while it is completed"}', stderr: "" }),
  });

  await assert.rejects(client.command("pause"), /cannot pause graph while it is completed/);
});

test("bundled reducer path is derived from the module URL without pathname decoding", () => {
  const expected = fileURLToPath(new URL("../scripts/graph_state.py", import.meta.url));

  assert.equal(bundledReducerPath(), expected);
  assert.match(bundledReducerPath(), /scripts[\\/]graph_state\.py$/u);
  assert.equal(fileUrlToPath("file:///tmp/graph%20flow/scripts/graph_state.py"), fileURLToPath("file:///tmp/graph%20flow/scripts/graph_state.py"));
  assert.throws(() => fileUrlToPath("file:///tmp/graph%2Fflow/scripts/graph_state.py"));
});

test("watch drops an in-flight projection after disposal", async () => {
  let resolveRefresh;
  const refresh = new Promise((resolve) => { resolveRefresh = resolve; });
  const client = new GraphStateClient({
    repo: "/repo",
    runId: "billing-v2",
    execute: async () => refresh,
  });
  const seen = [];
  const dispose = client.watch((value) => seen.push(value.run_id), () => true);

  dispose();
  resolveRefresh({ code: 0, stdout: JSON.stringify(snapshot), stderr: "" });
  await new Promise((resolve) => setTimeout(resolve, 0));

  assert.deepEqual(seen, []);
});

test("routes controls through public CLI commands without an extra status refresh", async () => {
  const calls = [];
  const client = new GraphStateClient({
    repo: "/repo",
    runId: "billing-v2",
    scriptPath: "scripts/graph_state.py",
    execute: async (command, args) => {
      calls.push([command, args]);
      return { code: 0, stdout: JSON.stringify(snapshot), stderr: "" };
    },
  });
  const controls = new GraphFlowControls(client);

  await controls.pause();
  await controls.resume();
  await controls.steer("implement", "Run focused tests first");
  await controls.requestStop();
  await controls.confirmStop({ handles: { "worker-123": "cancelled" } });

  assert.deepEqual(calls.map(([, args]) => args.slice(1, 2)), [["pause"], ["resume"], ["steer-request"], ["stop-request"], ["stop-confirm"]]);
  assert.deepEqual(calls[2][1], ["scripts/graph_state.py", "steer-request", "--repo", "/repo", "--run-id", "billing-v2", "--node", "implement", "--message", "Run focused tests first"]);
  assert.deepEqual(calls[4][1], ["scripts/graph_state.py", "stop-confirm", "--repo", "/repo", "--run-id", "billing-v2", "--evidence", '{"handles":{"worker-123":"cancelled"}}']);
});

test("routes graph and human approvals through the public approve command", async () => {
  const calls = [];
  const client = new GraphStateClient({
    repo: "/repo",
    runId: "billing-v2",
    scriptPath: "scripts/graph_state.py",
    execute: async (command, args) => {
      calls.push([command, args]);
      return { code: 0, stdout: JSON.stringify(snapshot), stderr: "" };
    },
  });
  const controls = new GraphFlowControls(client);

  await controls.approveGraph();
  await controls.approveNode("release-approval", "approved");

  assert.deepEqual(calls.map(([, args]) => args.slice(1, 2)), [["approve"], ["approve"]]);
  assert.deepEqual(calls[0][1], ["scripts/graph_state.py", "approve", "--repo", "/repo", "--run-id", "billing-v2"]);
  assert.deepEqual(calls[1][1], ["scripts/graph_state.py", "approve", "--repo", "/repo", "--run-id", "billing-v2", "--node", "release-approval", "--result-json", '{"outcome":"approved","evidence":{"source":"graph-flow-ui","answer":"approved"}}']);
});

test("interactive dialogs map every request type and compose multi-select answers", async () => {
  const answers = [];
  const selections = ["stripe", "unit", "Done", "yes"];
  const selectCalls = [];
  const ui = {
    select: async (_title, options) => {
      selectCalls.push(options);
      return selections.shift();
    },
    confirm: async () => true,
    input: async () => "details",
  };
  const requests = [
    { id: "request-1", kind: "input", answer_type: "single_select", prompt: "Provider", rationale: "Billing", options: ["stripe", "adyen"], scope: "preflight", node: null },
    { id: "request-2", kind: "input", answer_type: "multi_select", prompt: "Checks", rationale: "Verification", options: ["unit", "integration"], scope: "preflight", node: null },
    { id: "request-3", kind: "input", answer_type: "confirm", prompt: "Continue?", rationale: "Risk", scope: "preflight", node: null },
    { id: "request-4", kind: "input", answer_type: "text", prompt: "Details", rationale: "Scope", scope: "preflight", node: null },
    { id: "request-5", kind: "approval", answer_type: "confirm", prompt: "Approve?", rationale: "Writes", scope: "node", node: "approve" },
    { id: "request-6", kind: "approval", answer_type: "text", prompt: "Explain?", rationale: "Audit", scope: "node", node: "approve" },
    { id: "request-7", kind: "approval", answer_type: "single_select", prompt: "Choose?", rationale: "Audit", options: ["yes", "no"], scope: "node", node: "approve" },
  ];
  for (const request of requests) await answerOpenRequest(request, ui, async (requestId, answer) => answers.push([requestId, answer]));
  const headless = await answerOpenRequest(requests[1], undefined, async () => {
    throw new Error("headless clients must not block on dialogs");
  });

  assert.deepEqual(answers, [["request-1", "stripe"], ["request-2", ["unit"]], ["request-3", true], ["request-4", "details"], ["request-5", true], ["request-6", "details"], ["request-7", "yes"]]);
  assert.deepEqual(selections, []);
  assert.ok(selectCalls[2].includes("Done"));
  assert.equal(headless, false);
});

test("pending approvals use native confirmation or outcome selection with required evidence", async () => {
  const calls = [];
  const ui = {
    select: async () => "approved",
    confirm: async () => true,
    input: async () => undefined,
  };
  const graph = { scope: "graph", node: null, prompt: "Approve graph?", objective: "Ship billing v2", allowed_outcomes: [], kind: "approval", evidence_required: true };
  const human = { scope: "node", node: "release-approval", prompt: "Approve release?", objective: "Release", allowed_outcomes: ["approved", "declined"], kind: "approval", evidence_required: true };

  await answerPendingApproval(graph, ui, {
    approveGraph: async () => calls.push(["graph"]),
    approveNode: async (node, outcome) => calls.push(["node", node, outcome]),
  });
  await answerPendingApproval(human, ui, {
    approveGraph: async () => calls.push(["graph"]),
    approveNode: async (node, outcome) => calls.push(["node", node, outcome]),
  });

  assert.deepEqual(calls, [["graph"], ["node", "release-approval", "approved"]]);
});

test("refresh updates native widgets or returns stable headless lines", async () => {
  const widgets = [];
  const statuses = [];
  const interactive = await refreshCockpit(snapshot, {
    hasUI: true,
    ui: {
      setWidget: (key, lines) => widgets.push([key, lines]),
      setStatus: (key, text) => statuses.push([key, text]),
    },
  });
  const headless = await refreshCockpit(snapshot, { hasUI: false });

  assert.equal(interactive, undefined);
  assert.equal(widgets[0][0], "graph-flow");
  assert.match(widgets[0][1].join("\n"), /Run: billing-v2/);
  assert.deepEqual(statuses, [["graph-flow", "Graph flow: running"]]);
  assert.match(headless.join("\n"), /Action Center: clear/);
});

test("registers void Pi command handlers that render UI or print stable headless text", async () => {
  const commands = new Map();
  const events = new Map();
  const widgets = [];
  const statuses = [];
  const notices = [];
  const commandsRun = [];
  const pi = {
    exec: async (command, args) => {
      commandsRun.push([command, args]);
      return { code: 0, stdout: JSON.stringify(snapshot), stderr: "" };
    },
    on: (event, handler) => events.set(event, handler),
    registerCommand: (name, options) => commands.set(name, options),
  };
  const interactiveContext = {
    cwd: "/consumer/project",
    hasUI: true,
    ui: {
      select: async () => undefined,
      confirm: async () => false,
      input: async () => undefined,
      setWidget: (key, lines) => widgets.push([key, lines]),
      setStatus: (key, text) => statuses.push([key, text]),
      notify: (message, kind) => notices.push([message, kind]),
    },
  };
  graphFlowExtension(pi);
  const headless = [];
  const originalLog = console.log;
  try {
    const interactiveResult = await commands.get("graph-flow").handler("billing-v2 status", interactiveContext);
    assert.equal(interactiveResult, undefined);
    assert.match(widgets.at(-1)[1].join("\n"), /Run: billing-v2/);
    assert.deepEqual(statuses.at(-1), ["graph-flow", "Graph flow: running"]);
    assert.match(notices.at(-1)[0], /Graph flow/);
    assert.ok(commands.has("graph-flow-status"));
    commandsRun.length = 0;
    await commands.get("graph-flow").handler("billing-v2 pause", interactiveContext);
    assert.deepEqual(commandsRun.map(([, args]) => args[1]), ["pause", "status"]);
    console.log = (value) => headless.push(value);
    const headlessResult = await commands.get("graph-flow-status").handler("billing-v2", { ...interactiveContext, hasUI: false });
    assert.equal(headlessResult, undefined);
  } finally {
    console.log = originalLog;
    await events.get("session_shutdown")({}, interactiveContext);
  }
  assert.match(headless.join("\n"), /Run: billing-v2/);
});

test("graph-flow approve and answer route pending approval without treating it as input", async () => {
  const commands = new Map();
  const events = new Map();
  const commandsRun = [];
  let current = {
    ...snapshot,
    pending_approval: { scope: "graph", node: null, prompt: "Approve graph?", objective: "Ship billing v2", allowed_outcomes: [], kind: "approval", evidence_required: true },
  };
  const pi = {
    exec: async (command, args) => {
      commandsRun.push([command, args]);
      return { code: 0, stdout: JSON.stringify(current), stderr: "" };
    },
    on: (event, handler) => events.set(event, handler),
    registerCommand: (name, options) => commands.set(name, options),
  };
  const context = {
    cwd: "/consumer/project",
    hasUI: true,
    ui: {
      select: async () => "approved",
      confirm: async () => true,
      input: async () => "input",
      setWidget: () => undefined,
      setStatus: () => undefined,
      notify: () => undefined,
    },
  };
  graphFlowExtension(pi);
  try {
    await commands.get("graph-flow").handler("billing-v2 approve", context);
    assert.deepEqual(commandsRun.map(([, args]) => args[1]), ["status", "approve", "status"]);
    assert.deepEqual(commandsRun[1][1], [bundledReducerPath(), "approve", "--repo", "/consumer/project", "--run-id", "billing-v2"]);

    current = {
      ...snapshot,
      pending_approval: { scope: "node", node: "release-approval", prompt: "Approve release?", objective: "Release", allowed_outcomes: ["approved", "declined"], kind: "approval", evidence_required: true },
    };
    commandsRun.length = 0;
    await commands.get("graph-flow").handler("billing-v2 answer", context);
    assert.deepEqual(commandsRun.map(([, args]) => args[1]), ["status", "approve", "status"]);
    assert.match(commandsRun[1][1].join(" "), /--node release-approval --result-json/);
  } finally {
    await events.get("session_shutdown")({}, context);
  }
});
