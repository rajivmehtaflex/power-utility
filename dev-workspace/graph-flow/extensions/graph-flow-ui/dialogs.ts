import type { DialogUI, InputRequest, PendingApproval } from "./types.ts";

export interface PendingApprovalActions {
  approveGraph(): Promise<void>;
  approveNode(node: string, outcome: string): Promise<void>;
}

export async function answerOpenRequest(
  request: InputRequest,
  ui: DialogUI | undefined,
  respond: (requestId: string, answer: unknown) => Promise<void>,
): Promise<boolean> {
  if (!ui) return false;
  let answer: unknown;
  if (request.answer_type === "confirm") {
    answer = await ui.confirm(request.prompt, request.rationale ?? "");
  } else if (request.answer_type === "text") {
    answer = await ui.input(request.prompt, request.rationale);
  } else if (request.answer_type === "multi_select") {
    const selected: string[] = [];
    const remaining = [...(request.options ?? [])];
    let done = "Done";
    while (remaining.includes(done)) done = `_${done}`;
    while (remaining.length > 0) {
      const choice = await ui.select(request.prompt, [...remaining, done]);
      if (choice === undefined) return false;
      if (choice === done) break;
      if (Array.isArray(choice)) {
        for (const item of choice) if (remaining.includes(item)) selected.push(item);
        break;
      }
      if (!remaining.includes(choice)) return false;
      selected.push(choice);
      remaining.splice(remaining.indexOf(choice), 1);
    }
    answer = selected;
  } else {
    answer = await ui.select(request.prompt, request.options ?? []);
  }
  if (answer === undefined || answer === "" || (Array.isArray(answer) && answer.length === 0)) return false;
  await respond(request.id, answer);
  return true;
}

export async function answerPendingApproval(
  approval: PendingApproval,
  ui: DialogUI | undefined,
  actions: PendingApprovalActions,
): Promise<boolean> {
  if (!ui) return false;
  if (approval.scope === "graph") {
    if (!await ui.confirm(approval.prompt, approval.objective ?? "")) return false;
    await actions.approveGraph();
    return true;
  }
  if (!approval.node) return false;
  const outcome = await ui.select(approval.prompt, approval.allowed_outcomes);
  if (typeof outcome !== "string" || !approval.allowed_outcomes.includes(outcome)) return false;
  await actions.approveNode(approval.node, outcome);
  return true;
}
