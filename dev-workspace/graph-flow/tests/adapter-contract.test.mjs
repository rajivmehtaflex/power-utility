import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const fixtureDirectory = new URL("./fixtures/", import.meta.url);
const fixtureNames = ["codex", "prime-agent", "pi-core", "pi-subagents"];
const requiredDispatchFields = [
  "run_id",
  "node",
  "kind",
  "attempt",
  "allowed_outcomes",
  "depends_on",
  "depends_on_any",
  "input_results",
  "feedback",
  "prompt",
  "state_path",
];
const requiredEnvelopeFields = [
  "dispatch",
  "role",
  "objective",
  "repository",
  "worktree",
  "paths",
  "exclusive_ownership",
  "prohibited_scope",
  "acceptance_criteria",
  "verification_commands",
  "result_contract",
];
const expectedControls = {
  graph_approval: "approve",
  runtime_approval: "approve --node <id> --result <file>",
  input: "respond --request-id <id> --answer <typed-json>",
  pause: "pause then tick drains active handles to paused",
  resume: "resume only from paused",
  stop: "stop-request then stop-confirm with terminal handle evidence",
};

async function loadFixture(name) {
  return JSON.parse(await readFile(new URL(`${name}.json`, fixtureDirectory), "utf8"));
}

test("offline adapter fixtures preserve the portable worker envelope and control contract", async () => {
  for (const name of fixtureNames) {
    const fixture = await loadFixture(name);

    assert.equal(fixture.adapter, name);
    assert.deepEqual(Object.keys(fixture.role_mapping).sort(), ["default", "explorer", "human", "reviewer", "worker"]);
    assert.equal(fixture.role_mapping.human.dispatches, false);
    for (const role of ["explorer", "default", "worker", "reviewer"]) {
      assert.equal(fixture.role_mapping[role].dispatches, true);
    }
    assert.deepEqual(Object.keys(fixture.envelope).sort(), [...requiredEnvelopeFields].sort());
    assert.deepEqual(Object.keys(fixture.envelope.dispatch).sort(), [...requiredDispatchFields].sort());
    assert.equal(fixture.envelope.role, "worker");
    assert.ok(fixture.envelope.paths.length > 0);
    assert.ok(fixture.envelope.verification_commands.length > 0);
    assert.equal(fixture.envelope.exclusive_ownership.access, "write");
    assert.ok(fixture.envelope.prohibited_scope.includes("graph state mutation or recursive dispatch"));
    assert.ok(fixture.handle_lifecycle.launch.includes("register") || fixture.handle_lifecycle.launch.includes("claim"));
    for (const operation of ["inspect", "wait", "steer", "stop", "complete"]) {
      assert.equal(fixture.handle_lifecycle.operations[operation], true, `${name} supports ${operation}`);
    }
    assert.deepEqual(fixture.controls, expectedControls);
    assert.ok(["full", "sequential"].includes(fixture.capability.primary));
    assert.equal(fixture.headless_fallback.accepts_typed_json, true);
    assert.equal(fixture.headless_fallback.emits_reducer_projection, true);
    assert.equal(fixture.headless_fallback.renders_human_gates, true);
  }
});

test("offline adapter fixtures encode the documented host-specific tiers and fallbacks", async () => {
  const codex = await loadFixture("codex");
  const prime = await loadFixture("prime-agent");
  const piCore = await loadFixture("pi-core");
  const piSubagents = await loadFixture("pi-subagents");

  assert.deepEqual(
    [codex, prime, piSubagents].map((fixture) => fixture.capability),
    [
      { primary: "full", degraded: "managed" },
      { primary: "full", degraded: "managed" },
      { primary: "full", degraded: "managed" },
    ],
  );
  assert.deepEqual(piCore.capability, { primary: "sequential", degraded: null });
  assert.match(codex.role_mapping.explorer.native, /explorer threads/u);
  assert.match(prime.role_mapping.worker.native, /rlm\(\)/u);
  assert.match(piCore.role_mapping.worker.native, /sequential/u);
  assert.match(piSubagents.role_mapping.worker.native, /async subagent/u);
  assert.match(codex.headless_fallback.projection, /status --format json/u);
  assert.match(prime.headless_fallback.projection, /reducer JSON/u);
  assert.match(piCore.headless_fallback.projection, /status --format text\/json/u);
  assert.match(piSubagents.headless_fallback.projection, /reducer JSON projection/u);
});
