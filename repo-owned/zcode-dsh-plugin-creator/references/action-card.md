# Action cards (interactive proposals in the UI)

Action cards let the MODEL propose one interactive card below its answer by calling the built-in `propose_action` tool. The card's behavior — its user-visible verbs — is implemented host-side by a registered **kind** on the `actionCards` service (`@deepseek-ai/dsh-action-cards`). This package's public types use **zod** (`import { z, type ZodType } from "zod"`), not schemastery: both the service `Config` and every kind's `details` schema are zod, so `zod` is a required dependency of any kind-owning plugin (schemastery ~3.19.0 remains the choice for ordinary plugin config elsewhere). Pinned: DSH 0.2.2-rc.1, Node >=24.9.0, `@deepseek-ai/cordis` ~4.1.0 (peer).

## The skill-gating rule (critical)

An `ActionCardKind` names a `skill` whose instructions tell the model when and how to propose the action. **A kind without its skill never fires.** The chain, exactly as the service implements it:

1. `propose_action` is declared per agent only while that agent has successfully loaded some registered kind's skill through the `skill` tool (tool declaration is conditional on that loaded set).
2. The service watches `tools/result`: a successful `skill` tool call whose `name` argument equals a registered kind's `skill` is recorded against that agent's current turn.
3. A `propose_action` call is refused with `ACTION_CARD_SKILL` ("Load skill <name> first, then call propose_action.") unless the kind's skill was loaded in the SAME turn. Root agents only, one card per turn, non-blank `title`/`brief`, and `details` must pass the kind's zod schema.

So ship two halves together: the kind (host-side `act`) and the skill content (model-side instructions naming the `action` and its `details` fields). Register the skill with `ctx.skills.register` (see ./skill-plugin.md) or ship it as a SKILL.md the filesystem provider discovers.

## Shapes (quoted from `dsh-action-cards/lib/types/`)

```ts
import { z, type ZodType } from "zod";

interface ActionCardKind<Details> {
  readonly action: string;            // value of the `action` argument
  readonly skill: string;             // skill whose instructions propose this action
  readonly invitation: string;        // model-facing closing guidance after acceptance
  readonly details: ZodType<Details>; // validates details on propose AND each action
  readonly verbs: Readonly<Record<string, ActionCardVerb>>; // besides `dismiss`
  readonly openPhases?: readonly string[];   // phases still offering the action
  readonly statusGuidance?: string;          // sentence for the status notice
  readonly statusFields?: readonly string[]; // decision fields the notice reports
  dismissal?(proposal, payload): ActionCardFields | undefined;
  reconcile?(agent, proposal): Promise<void>; // sync state outside the Session
  act(agent, proposal, verb: string, payload): Promise<ActionCardResult>;
}
interface ActionCardVerb {
  readonly global?: true;   // connection must hold global Remote access
  readonly writes?: true;   // refused while the Session sandbox is read-only
}
interface ActionCardDecision {
  readonly callId: ToolCallId;
  readonly action: string;
  readonly phase: string;                  // kind-defined; `dismissed` is shared
  readonly data?: ActionCardFields;        // kind-defined fields
}
type ActionCardResult =
  | { readonly status: "accepted" }                          // background work started
  | { readonly status: "settled"; readonly decision: ActionCardDecision }
  | { readonly status: "refused"; readonly reason: string }
  | { readonly status: "unconfirmed"; readonly reason: string }; // owner unloaded
```

`ActionCardProposal` (what `act` receives) is `{ callId, turn, action, title, brief, details: Details }` with `details` already schema-validated.

## Registration

The service lives at `ctx.actionCards`. A kind-owning plugin injects `["actionCards"]` (plus `["skills"]` when it registers the gating skill itself) and uses three methods:

```ts
ctx.actionCards.register(kind);                     // => disposer; throws on duplicate action
ctx.actionCards.record(agent, decision);            // log a decision; next request reports it
ctx.actionCards.act(agent, callId, verb, payload?); // run a user action (UI path)
// also: ctx.actionCards.view(session) => { proposals, decisions } by call id
```

`dismiss` is built in (recorded by `act` itself, also for an unstarted card whose kind unregistered); every other verb goes to the kind's `act` after the shared `global`/`writes` checks and an optional `reconcile`.

## Worked template — local fixture kind "confirm-rename"

```ts
import type { Context } from "@deepseek-ai/cordis";
import { ToolCallId } from "@deepseek-ai/dsh-llm";
import type { Agent } from "@deepseek-ai/dsh-agent";
import { z } from "zod";

const skillContent = `Propose renaming the current branch via a confirm card.
Call propose_action with action "confirm-rename", a short title, a brief saying
what the rename does, and details { "from": string, "to": string }. Propose it
only when the user asked to rename a branch.`;

export const inject = ["actionCards", "skills"];
export function apply(ctx: Context) {
  const offKind = ctx.actionCards.register({
    action: "confirm-rename",
    skill: "confirm-rename",
    invitation: "Offer the rename card so the user can approve or dismiss it.",
    details: z.object({ from: z.string(), to: z.string() }),
    verbs: { approve: {} },
    openPhases: ["proposed", "approved"],
    // act(agent, proposal, verb, payload) — no context parameter; close over ctx
    async act(agent: Agent, proposal: { callId: ReturnType<typeof ToolCallId>; details: { from: string; to: string } }, verb: string) {
      if (verb !== "approve") return { status: "refused" as const, reason: `Unknown verb ${verb}` };
      const decision = { callId: proposal.callId, action: "confirm-rename", phase: "approved",
        data: { from: proposal.details.from, to: proposal.details.to } };
      ctx.actionCards.record(agent, decision);
      return { status: "settled" as const, decision };
    },
  });
  const offSkill = ctx.skills.register({
    name: "confirm-rename", description: "Propose a branch-rename confirmation card",
    source: "bundled", content: skillContent,
  });
  ctx.effect(function* () { yield offKind; yield offSkill; });
}
```

In real kinds, `act` performs the action host-side (here a deterministic fixture: record and settle), and `reconcile` brings stale decisions up to date when a Session reopens. The accepted `propose_action` result carries `{ action, title, invitation }` and instructs the model not to restate the card.

## Verify

See ./verify.md. Register kind + skill in a temp profile, then:

1. One real model turn: the model must load the `confirm-rename` skill via the `skill` tool, after which `propose_action` is declared; its accepted call admits the card (refusals carry `ACTION_CARD_SKILL` when the skill was not loaded this turn — itself a useful negative check).
2. Service-level, over the live agent: `await ctx.actionCards.act(agent, callId, "approve")` returns `{ status: "settled", decision: { phase: "approved", data: { from, to } } }`; `ctx.actionCards.view(agent.session)` shows the recorded decision by call id, and the next model request reports it as a status notice.

Related: [../SKILL.md](../SKILL.md) · [./bundle-anatomy.md](./bundle-anatomy.md) · [./skill-plugin.md](./skill-plugin.md) · [./preset.md](./preset.md) · [./tool.md](./tool.md) · [./command.md](./command.md) · [./verify.md](./verify.md)
